"""Verified Codex CLI transport plus a capability-gated Agents SDK MCP adapter."""

import asyncio
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from uuid import UUID

from .config.settings import Settings
from .design_artifacts import digest
from .execution_models import AgentOutput, ExecutionMode, HealthStatus
from .execution_process import CodexProcessManager, Redactor, runtime_environment


def executable(settings: Settings) -> str:
    value = shutil.which(settings.codex_executable)
    if not value or Path(value).suffix.lower() in {".cmd", ".bat", ".ps1"}:
        raise ValueError(
            "Configure a native Codex executable; shell wrapper launchers are not supported"
        )
    if any(a != "--no-daemon" for a in settings.codex_startup_arguments):
        raise ValueError("Only the bounded --no-daemon startup argument is allowed")
    return value


def runtime_identity(settings: Settings) -> dict:
    import hashlib

    path = executable(settings)
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            hasher.update(chunk)
    version = subprocess.run(
        [path, "--version"],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
        env=runtime_environment(),
    )
    return {"path": path, "sha256": hasher.hexdigest(), "version": version.stdout.strip()}


def doctor(settings: Settings) -> HealthStatus:
    health = HealthStatus()
    try:
        health.executable = executable(settings)

        def probe(args):
            result = subprocess.run(
                [health.executable, *args],
                capture_output=True,
                text=True,
                timeout=15,
                env=runtime_environment(),
                encoding="utf-8",
                errors="replace",
            )
            health.probes.append(
                {
                    "argv": args,
                    "exit_code": result.returncode,
                    "stdout": Redactor().clean(result.stdout[:18000]),
                    "stderr": Redactor().clean(result.stderr[:3000]),
                }
            )
            return result

        version = probe(["--version"])
        health.version = version.stdout.strip()
        help_result = probe(["exec", "--ignore-user-config", "--ignore-rules", "--help"])
        health.exec_supported = help_result.returncode == 0 and all(
            flag in help_result.stdout
            for flag in ("--output-schema", "--json", "--ignore-user-config", "--ignore-rules")
        )
        health.mcp_supported = probe(["help", "mcp-server"]).returncode == 0
        login = probe(["login", "status"])
        health.authenticated = login.returncode == 0
        sdk = importlib.util.find_spec("agents") is not None
        health.selected_transport = (
            "mcp" if health.mcp_supported and sdk else "exec" if health.exec_supported else None
        )
        if not health.mcp_supported:
            health.findings.append(
                "Installed CLI has no mcp-server; use the verified non-interactive exec transport."
            )
        if not sdk:
            health.findings.append(
                "Install project [codex] dependencies for Agents SDK MCP/tracing support."
            )
        if not health.authenticated:
            health.findings.append(
                "Run codex login interactively or configure CODEX_API_KEY through secure environment setup."
            )
        if os.name != "nt":
            health.findings.append(
                "This release's enforced isolation adapter targets native Windows MXC; other platforms fail closed."
            )
        health.findings.append(
            "Live execution is disabled by default; design and authenticated execution grants are independently required."
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        health.findings.append(Redactor().clean(str(exc)))
    return health


def permission_arguments(request, extra_reads: list[Path] | None = None) -> list[str]:
    if os.name != "nt":
        raise PermissionError("No certified OS isolation adapter for this platform")
    root = Path(request.worktree_path).resolve()
    access = {":root": "deny", ":minimal": "read", root.as_posix(): "read"}
    if request.mode in {ExecutionMode.WORKTREE_WRITE, ExecutionMode.VALIDATION_ONLY}:
        for scope in request.allowed_file_scopes:
            access[(root / scope).as_posix()] = "write"
    for relative in (
        ".git",
        ".codex",
        ".agents",
        ".github",
        ".env",
        "AGENTS.md",
        "docs/milestones",
        "openapi",
        "events",
        "schemas",
    ):
        if (root / relative).parent.exists():
            access[(root / relative).as_posix()] = "deny"
    access[(Path.home() / ".codex").as_posix()] = "deny"
    for readable in extra_reads or []:
        access[readable.resolve().as_posix()] = "read"
    table = "{" + ",".join(json.dumps(k) + "=" + json.dumps(v) for k, v in access.items()) + "}"
    name = "aeo_" + digest(request.context_digest + request.worktree_path)[:20]
    core = {
        k.upper(): v
        for k, v in os.environ.items()
        if k.upper() in {"PATH", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "TEMP", "TMP"}
    }
    environment_table = (
        "{"
        + ",".join(json.dumps(k) + "=" + json.dumps(v.replace("\\", "/")) for k, v in core.items())
        + "}"
    )
    return [
        "-c",
        "shell_environment_policy.set=" + environment_table,
        "-c",
        f'default_permissions="{name}"',
        "-c",
        f"permissions.{name}={{filesystem={table},network={{enabled=false}}}}",
        "-c",
        'windows.sandbox="mxc"',
        "-c",
        'approval_policy="never"',
        "-c",
        'shell_environment_policy.inherit="none"',
        "-c",
        "shell_environment_policy.ignore_default_excludes=false",
        "-c",
        'web_search="disabled"',
        "-c",
        "mcp_servers={}",
        "-c",
        "features.apps=false",
        "-c",
        "hooks={}",
        "-c",
        "plugins={}",
        "-c",
        "developer_instructions=" + json.dumps(request.role_instructions),
        "-c",
        "features.multi_agent=false",
    ]


def reject_local_configuration(directory: Path):
    for parent in (directory, *directory.parents):
        for relative in (".codex/config.toml", ".codex/hooks.json", ".mcp.json"):
            if (parent / relative).exists():
                raise PermissionError(
                    f"Unreviewed project runtime configuration blocks execution: {parent / relative}"
                )
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    if (home / "hooks.json").exists():
        raise PermissionError("User hook configuration requires a separately isolated adapter")


def parse_output(raw: str) -> tuple[AgentOutput, str | None, dict]:
    final, session, usage = None, None, {}
    for line in raw.splitlines():
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError("Codex event is not an object")
        kind = event.get("type")
        if kind == "thread.started":
            session = str(UUID(event["thread_id"]))
        elif kind in {"error", "turn.failed"}:
            raise RuntimeError("Codex reported a failed turn")
        elif kind == "turn.completed":
            usage = event.get("usage") or {}
        elif kind == "item.completed" and event.get("item", {}).get("type") == "agent_message":
            final = event["item"].get("text")
    if final is None:
        raise ValueError("No structured final agent message in Codex event stream")
    return AgentOutput.model_validate_json(final), session, usage


class CodexExecAdapter:
    name = "codex-exec"

    def __init__(self, settings: Settings, manager: CodexProcessManager | None = None):
        self.settings, self.manager = settings, manager or CodexProcessManager()

    async def health_check(self):
        return await asyncio.to_thread(doctor, self.settings)

    async def execute(self, request, prompt: str, directory: Path, **callbacks):
        reject_local_configuration(Path(request.worktree_path))
        schema = directory / "output-schema.json"
        schema.write_text(json.dumps(AgentOutput.model_json_schema()), encoding="utf-8")
        argv = [
            executable(self.settings),
            "--no-daemon",
            *self.settings.codex_startup_arguments,
            "exec",
            "--strict-config",
            "--ignore-user-config",
            "--ignore-rules",
            *permission_arguments(request),
            "--cd",
            request.worktree_path,
            "--json",
            "--output-schema",
            str(schema),
        ]
        if self.settings.codex_model:
            argv.extend(["--model", self.settings.codex_model])
        return await self.manager.run(
            [*argv, "-"], Path(request.worktree_path), prompt, request.timeout_seconds, **callbacks
        )

    async def continue_execution(self, session_id, request, prompt, directory, **callbacks):
        if request.mode != ExecutionMode.READ_ONLY:
            raise PermissionError(
                "Write sessions are not blindly continued; create an explicitly approved recovery execution"
            )
        session_id = str(UUID(session_id))
        reject_local_configuration(Path(request.worktree_path))
        schema = directory / "output-schema.json"
        schema.write_text(json.dumps(AgentOutput.model_json_schema()), encoding="utf-8")
        argv = [
            executable(self.settings),
            "--no-daemon",
            "exec",
            *permission_arguments(request),
            "resume",
            "--ignore-user-config",
            "--ignore-rules",
            "--json",
            "--output-schema",
            str(schema),
            session_id,
            "-",
        ]
        return await self.manager.run(
            argv, Path(request.worktree_path), prompt, request.timeout_seconds, **callbacks
        )


class CodexMCPAdapter:
    """SDK connection/tool discovery for compatible runtimes; no invented legacy schema."""

    name = "codex-mcp"

    def __init__(self, settings: Settings):
        self.settings = settings

    async def health_check(self):
        return await asyncio.to_thread(doctor, self.settings)

    async def tools(self):
        from agents.mcp import MCPServerStdio

        if not (await self.health_check()).mcp_supported:
            raise RuntimeError("Installed Codex CLI does not expose mcp-server")
        async with MCPServerStdio(
            name="AEO Codex",
            params={
                "command": executable(self.settings),
                "args": ["mcp-server"],
                "env": runtime_environment(),
            },
            client_session_timeout_seconds=15,
            max_retry_attempts=0,
        ) as server:
            return [tool.model_dump(mode="json") for tool in await server.list_tools()]

    async def execute(self, request, prompt, directory, **callbacks):
        # Legacy MCP has no verified per-call granular Windows profile/process identity here.
        # Discover schemas, but do not claim its broader workspace-write is equivalent.
        await self.tools()
        raise PermissionError(
            "MCP tool isolation is not certified for this runtime; select exec transport"
        )

    async def continue_execution(self, session_id, request, prompt, directory, **callbacks):
        raise PermissionError("MCP continuation requires verified schema and isolation semantics")


class CodexExecutor(CodexExecAdapter):
    """Compatible concrete executor behind CodingAgentExecutor; orchestration owns permissions."""
