"""Trusted Git worktree operations, artifact preservation and bounded sandbox validation."""

import hashlib
import json
import os
import socket
import subprocess
import tarfile
import tempfile
from pathlib import Path

from .execution_models import ExecutionMode
from .execution_process import runtime_environment


def git(repository: Path, *args: str) -> str:
    # A checkout must not run repository hooks or configured clean/smudge programs.
    with tempfile.TemporaryDirectory(prefix="aeo-git-policy-") as temporary:
        folder = Path(temporary)
        hooks = folder / "hooks"
        hooks.mkdir()
        global_config = folder / "gitconfig"
        global_config.write_text("", encoding="utf-8")
        env = {k: v for k, v in runtime_environment().items() if k != "CODEX_API_KEY"}
        env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(global_config)})
        prefix = [
            "git",
            "--no-optional-locks",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.longpaths=true",
            "-c",
            f"core.hooksPath={hooks}",
            "-C",
            str(repository),
        ]
        configured = subprocess.run(
            [
                *prefix,
                "config",
                "--name-only",
                "--get-regexp",
                r"^filter\..*\.(clean|smudge|process|required)$",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            env=env,
        )
        if configured.returncode not in {0, 1}:
            raise PermissionError("Cannot establish safe Git filter configuration")
        overrides = []
        for key in configured.stdout.splitlines():
            overrides.extend(["-c", key + ("=false" if key.endswith(".required") else "=")])
        result = subprocess.run(
            [*prefix, *overrides, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=30,
            env=env,
        )
        return result.stdout.strip()


def create_worktree(
    repository: Path,
    target: Path,
    execution_id: str,
    source_head: str,
    expected_source_head: str | None = None,
):
    if target.exists():
        raise PermissionError("Worktree path already exists; explicit recovery is required")
    target.parent.mkdir(parents=True, exist_ok=True)
    if git(repository, "rev-parse", "HEAD") != (expected_source_head or source_head):
        raise PermissionError("Source HEAD changed after execution approval")
    branch = "aeo/" + execution_id
    git(repository, "worktree", "add", "-b", branch, str(target), source_head)
    if git(target, "rev-parse", "HEAD") != source_head:
        raise RuntimeError("Isolated worktree HEAD does not match approved base")
    return branch


def tree_fingerprints(root: Path, max_bytes: int) -> dict[str, str]:
    # Git can create Windows paths longer than MAX_PATH. Traverse the same complete
    # tree using the extended path namespace; never silently skip unreadable directories.
    traversal_root = root.resolve()
    if os.name == "nt" and not str(traversal_root).startswith("\\\\?\\"):
        name = str(traversal_root)
        traversal_root = Path(
            "\\\\?\\UNC\\" + name[2:] if name.startswith("\\\\") else "\\\\?\\" + name
        )

    def traversal_error(error):
        raise error

    hashes = {}
    total = 0
    for directory, dirs, files in os.walk(
        traversal_root, followlinks=False, onerror=traversal_error
    ):
        for name in dirs:
            p = Path(directory) / name
            if p.is_symlink() or p.is_junction():
                raise PermissionError("Worktree symlinks/junctions are not allowed")
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for name in sorted(files):
            p = Path(directory) / name
            if name == ".git":
                continue
            if p.is_symlink() or any((Path(directory) / d).is_symlink() for d in dirs):
                raise PermissionError(
                    "Worktree symlinks/reparse links require a separately isolated adapter"
                )
            raw = p.read_bytes()
            total += len(raw)
            if total > max_bytes:
                raise ValueError(
                    "Artifact preservation budget exceeded; workspace retained, cleanup refused"
                )
            hashes[p.relative_to(traversal_root).as_posix()] = hashlib.sha256(raw).hexdigest()
    return hashes


def changed_files(before: dict, after: dict) -> list[str]:
    return sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))


def check_changes(paths: list[str], scopes: list[str]):
    for relative in paths:
        if any(
            p in {".git", ".codex", ".agents", ".github", "AGENTS.md"} or p.startswith(".env")
            for p in Path(relative).parts
        ):
            raise PermissionError("Runtime changed a protected control file")
        if not any(
            relative == scope or relative.startswith(scope.rstrip("/") + "/") for scope in scopes
        ):
            raise PermissionError(
                f"Runtime changed a file outside literal approved scopes: {relative}"
            )


def preserve(root: Path, directory: Path, before: dict, max_bytes: int) -> tuple[list[str], str]:
    after = tree_fingerprints(root, max_bytes)
    changes = changed_files(before, after)
    archive = directory / "preserved-worktree.tar"
    # The complete bounded worktree is retained, including untracked/ignored partial outputs.
    with tarfile.open(archive, "w") as output:
        from .execution_process import Redactor

        for relative in changes:
            if relative not in after:
                continue
            raw = (root / relative).read_bytes()
            text = raw.decode("utf-8", errors="replace")
            if Redactor().clean(text) != text:
                raise PermissionError(
                    "Sensitive output requires manual preservation; cleanup refused"
                )
            output.add(root / relative, arcname=relative, recursive=False)
    metadata = {
        "root": str(root.resolve()),
        "files": after,
        "changed_files": changes,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    }
    (directory / "preservation.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return changes, str(archive)


def cleanup_worktree(source: Path, target: Path, execution_root: Path, directory: Path):
    root, target = execution_root.resolve(), target.resolve()
    if not target.is_relative_to(root) or target == root or target == source.resolve():
        raise PermissionError("Cleanup target is outside the dedicated execution root")
    metadata = json.loads((directory / "preservation.json").read_text(encoding="utf-8"))
    if metadata["root"] != str(target) or tree_fingerprints(target, 100000000) != metadata["files"]:
        raise PermissionError("Worktree changed after preservation; cleanup refused")
    archive = directory / "preserved-worktree.tar"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != metadata["archive_sha256"]:
        raise PermissionError("Preserved archive is missing or changed")
    git(source, "worktree", "remove", "--force", str(target))
    # Keep branch refs as review evidence; never delete branches or prune unrelated worktrees.


def probe_isolation(exe: str, request, permission_args: list[str], directory: Path) -> dict:
    """No model call. Test exact native policy against bounded fixture canaries."""
    if os.name != "nt":
        raise PermissionError("Native Windows isolation is required")
    outside = directory / "denied-canary.txt"
    outside.write_text("private canary", encoding="utf-8")
    allowed = Path(request.worktree_path) / request.allowed_file_scopes[0]
    if request.mode == ExecutionMode.READ_ONLY:
        allowed = Path(request.worktree_path) / ("aeo-readonly-" + directory.name + ".tmp")
        if allowed.exists():
            raise PermissionError("Isolation canary path already exists")
    elif allowed.suffix:
        # Never probe by overwriting an approved file path; use its parent only when directory granted.
        candidates = [
            Path(request.worktree_path) / s
            for s in request.allowed_file_scopes
            if not Path(s).suffix
        ]
        if not candidates:
            raise PermissionError("Write-isolation canary requires an approved directory scope")
        allowed = candidates[0]
    if request.mode != ExecutionMode.READ_ONLY:
        allowed.mkdir(parents=True, exist_ok=True)
        allowed = allowed / "aeo-write-canary.tmp"
    denied_scope = Path(request.worktree_path) / ("aeo-denied-scope-" + directory.name + ".tmp")
    if denied_scope.exists():
        raise PermissionError("Denied-scope canary already exists")
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]
    script = directory / "isolation-probe.ps1"

    # Values are literal data escaped for PowerShell; no user-generated command text is executed.
    def quote(p):
        return "'" + str(p).replace("'", "''") + "'"

    expected = request.mode != ExecutionMode.READ_ONLY
    body = "$ErrorActionPreference='Stop'\n$outsideRead=$false\n$outsideWrite=$false\n$insideWrite=$false\n"
    body += f"try {{ [IO.File]::ReadAllText({quote(outside)}) | Out-Null; $outsideRead=$true }} catch {{}}\n"
    body += f"try {{ [IO.File]::WriteAllText({quote(outside)}, 'changed'); $outsideWrite=$true }} catch {{}}\n"
    body += f"try {{ [IO.File]::WriteAllText({quote(allowed)}, 'probe'); $insideWrite=$true }} catch {{}}\n"
    body += "$scopeWrite=$false\n$network=$false\n"
    body += f"try {{ [IO.File]::WriteAllText({quote(denied_scope)}, 'probe'); $scopeWrite=$true }} catch {{}}\n"
    body += f"try {{ $client=[Net.Sockets.TcpClient]::new(); $c=$client.ConnectAsync('127.0.0.1',{port}); if ($c.Wait(500) -and $client.Connected) {{ $network=$true }}; $client.Dispose() }} catch {{}}\n"
    body += "$expected=" + ("$true" if expected else "$false") + "\n"
    body += "if ($outsideRead -or $outsideWrite -or $scopeWrite -or $network -or ($insideWrite -ne $expected)) { exit 41 }; exit 0\n"
    script.write_text(body, encoding="utf-8")
    # Permit only the exact probe script as an additional readable file, never its parent.
    from .codex_runtime import permission_arguments

    profile = permission_arguments(request)
    name = next(
        v.split("=", 1)[1].strip('"') for v in profile if v.startswith("default_permissions=")
    )
    powershell = (
        Path(os.environ.get("SYSTEMROOT", "C:/Windows"))
        / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    args = [
        exe,
        *profile,
        "sandbox",
        "--include-managed-config",
        "--permission-profile",
        name,
        "--cd",
        request.worktree_path,
        "--",
        str(powershell),
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        body,
    ]
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=30, env=runtime_environment()
        )
    finally:
        listener.close()

    if allowed.exists() and allowed.name.startswith("aeo-"):
        allowed.unlink()
    if denied_scope.exists():
        denied_scope.unlink()
    outcome = {
        "exit_code": result.returncode,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-3000:],
        "outside_read_denied": not result.returncode,
        "outside_write_denied": not result.returncode,
        "out_of_scope_write_denied": not result.returncode,
        "network_denied": not result.returncode,
        "expected_inside_write": expected,
    }
    if result.returncode:
        raise PermissionError(
            "Native isolation probe failed; model invocation is blocked: " + result.stderr[-1000:]
        )
    return outcome
