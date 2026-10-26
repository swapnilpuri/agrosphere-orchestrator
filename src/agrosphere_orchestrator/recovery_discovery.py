"""Bounded local evidence collection. Never runs builds, tests, hooks or remote Git."""

import hashlib
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from .configuration import Repository, RepositoryManifest, load_yaml
from .recovery_models import Evidence, RecoveredMilestone, RecoverySnapshot
from .repositories import inspect_repository

SKIP = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".angular",
    ".idea",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "project",
}
MILESTONE = re.compile(r"(?<![A-Za-z0-9])(?:milestone[ _-]*|M)([0-9]+[A-Z]?)(?![A-Za-z0-9])", re.I)
TARGETS = ("1A", "1B", "1C", "2", "3A", "3B")


def paths(root: Path):
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(
            d for d in dirs if d not in SKIP and not (Path(directory) / d).is_symlink()
        )
        for name in sorted(names):
            p = Path(directory) / name
            if not p.is_symlink():
                yield p


def git_history(root: Path) -> tuple[list[dict], str | None]:
    try:
        result = subprocess.run(
            [
                "git",
                "--no-optional-locks",
                "-C",
                str(root),
                "-c",
                "core.fsmonitor=false",
                "log",
                "-200",
                "--format=%H%x09%cI%x09%s",
                "--no-show-signature",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
        )
        commits = []
        for line in result.stdout.splitlines():
            fields = line.split("\t", 2)
            if len(fields) == 3:
                commits.append(dict(zip(("commit", "date", "subject"), fields, strict=True)))
        return commits, None
    except (OSError, subprocess.SubprocessError) as exc:
        return [], f"history unavailable: {exc}"


def repository_roots(root: Path):
    """Find independent and nested roots, including linked worktree markers."""
    if not root.is_dir():
        raise ValueError(f"workspace does not exist: {root}")
    for directory, dirs, names in os.walk(root, followlinks=False):
        if ".git" in dirs or ".git" in names:
            yield Path(directory)
        dirs[:] = sorted(
            d for d in dirs if d not in SKIP and not (Path(directory) / d).is_symlink()
        )


def collect_repository(root: Path) -> tuple[dict, list[Evidence]]:
    inspection = inspect_repository(Repository(id=root.name, path=root))
    files = list(paths(root))
    relative = [p.relative_to(root).as_posix() for p in files]
    by_name = {p.name: p for p in files if p.parent == root}
    tests = [s for s in relative if re.search(r"(^|/)(tests?|src/test|e2e)/|[.](spec|test)[.]", s)]
    source = [
        s
        for s in relative
        if s.startswith("src/")
        and "/test/" not in s
        and s.endswith((".java", ".py", ".ts", ".cpp", ".cs"))
    ]
    fingerprints = {}
    for p, rel in zip(files, relative, strict=True):
        if not rel.startswith(("target/", "test-results/", ".vscode/")) and p.suffix.lower() in {
            ".java",
            ".py",
            ".ts",
            ".cpp",
            ".cs",
            ".json",
            ".yaml",
            ".yml",
            ".proto",
            ".sql",
            ".toml",
            ".md",
        }:
            if p.stat().st_size <= 2_000_000:
                fingerprints[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    builds, commands, languages, frameworks = [], [], [], []
    if "pom.xml" in by_name:
        builds.append("Maven")
        commands.append("./mvnw verify")
        languages.append("Java")
        if "spring-boot" in by_name["pom.xml"].read_text(encoding="utf-8", errors="replace"):
            frameworks.append("Spring Boot")
    if (root / "pyproject.toml").is_file() or (root / "requirements-dev.txt").is_file():
        languages.append("Python")
        builds.append("Python packaging")
        if any(s.startswith("tests/") for s in tests):
            commands.append("python -m pytest")
    if (root / "package.json").is_file():
        try:
            package = json.loads((root / "package.json").read_text(encoding="utf-8"))
            languages.append("TypeScript/JavaScript")
            builds.append("npm")
            commands.extend(f"npm run {key}" for key in package.get("scripts", {}) if "test" in key)
            deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
            frameworks.extend(name for name in ("@angular/core", "cesium", "react") if name in deps)
        except (ValueError, OSError):
            pass
    if (root / "scripts/validate.py").is_file():
        commands.append("python scripts/validate.py")
    documents, results, evidence = [], [], []
    warnings = []
    for p, rel in zip(files, relative, strict=True):
        if p.suffix.lower() not in {".md", ".xml"}:
            continue
        if p.stat().st_size > 2_000_000:
            warnings.append(f"oversized evidence skipped: {rel}")
            continue
        if p.suffix == ".xml" and not (p.name.startswith("TEST-") or "junit" in rel):
            continue
        if p.suffix == ".md" and (rel.startswith("target/") or rel.startswith(".vscode/")):
            continue
        raw = p.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        timestamp = datetime.fromtimestamp(p.stat().st_mtime, UTC).isoformat()
        if p.suffix == ".md":
            text = raw.decode("utf-8", errors="replace")
            documents.append(rel)
            for number, line in enumerate(text.splitlines(), 1):
                if MILESTONE.search(line) or MILESTONE.search(p.stem):
                    evidence.append(
                        Evidence(
                            repository=root.name,
                            path=rel,
                            kind="document",
                            sha256=digest,
                            head=inspection.head,
                            modified_at=timestamp,
                            line=number,
                            excerpt=line[:1000],
                        )
                    )
        else:
            try:
                tree = ElementTree.fromstring(raw)
                suites = [tree] if tree.tag == "testsuite" else list(tree.iter("testsuite"))
                counts = {
                    k: sum(int(s.get(k, 0)) for s in suites)
                    for k in ("tests", "failures", "errors", "skipped")
                }
                outcome = (
                    "historical-pass"
                    if (
                        counts["tests"] > counts["skipped"]
                        and not counts["failures"]
                        and not counts["errors"]
                    )
                    else "historical-incomplete-or-fail"
                )
                results.append({"path": rel, **counts, "outcome": outcome})
                evidence.append(
                    Evidence(
                        repository=root.name,
                        path=rel,
                        kind="test-result",
                        sha256=digest,
                        head=inspection.head,
                        modified_at=timestamp,
                        outcome=outcome,
                        excerpt=json.dumps(counts),
                    )
                )
            except (ElementTree.ParseError, ValueError):
                warnings.append(f"invalid test result: {rel}")
    commits, history_error = git_history(root) if inspection.head else ([], None)
    for c in commits:
        if MILESTONE.search(c["subject"]):
            evidence.append(
                Evidence(
                    repository=root.name,
                    path=c["commit"],
                    kind="commit",
                    sha256=hashlib.sha256(c["subject"].encode()).hexdigest(),
                    head=c["commit"],
                    modified_at=c["date"],
                    excerpt=c["subject"],
                )
            )
    inventory = {
        **inspection.model_dump(),
        "dirty": bool(inspection.status),
        "main_language": languages[0] if languages else "unknown/documentation/configuration",
        "languages": languages,
        "frameworks": frameworks,
        "build_systems": builds,
        "test_commands": commands,
        "commands_executed": False,
        "readmes": [s for s in relative if Path(s).name.lower() == "readme.md"],
        "agent_guidance": [s for s in relative if Path(s).name == "AGENTS.md"],
        "architecture_documents": [s for s in documents if s.startswith("docs/")],
        "contracts": [
            s
            for s in relative
            if any(k in s.lower() for k in ("openapi/", "events/", "contracts/", "schemas/"))
            and s.endswith((".json", ".yaml", ".yml", ".proto"))
        ],
        "milestone_artifacts": sorted({e.path for e in evidence if e.kind == "document"}),
        "source_files": source,
        "file_fingerprints": fingerprints,
        "test_files": tests,
        "test_results": results,
        "recent_commits": commits,
        "warnings": warnings + ([history_error] if history_error else []),
    }
    return inventory, evidence


def discover_project(workspace: Path, manifest_path: Path, exclude: Path) -> RecoverySnapshot:
    workspace, exclude = workspace.resolve(), exclude.resolve()
    repositories, evidence = [], []
    for root in sorted(repository_roots(workspace)):
        if root.resolve() == exclude:
            continue
        inventory, found = collect_repository(root)
        repositories.append(inventory)
        evidence.extend(found)
    manifest = load_yaml(manifest_path, RepositoryManifest).resolve(manifest_path)
    actual = {str(Path(r["path"]).resolve()) for r in repositories}
    missing = [
        r.id
        for r in manifest
        if str(r.path.resolve()) not in actual and r.path.resolve() != exclude
    ]
    milestones = recover_milestones(repositories, evidence)
    return RecoverySnapshot(
        workspace=str(workspace),
        repositories=repositories,
        missing_repositories=missing,
        milestones=milestones,
        limitations=[
            "Read-only observation; application tests/builds were not executed.",
            "Historical test artifacts have no proven binding to current worktree or full acceptance criteria.",
            "Git history limited to 200 recent subjects per repository; documents limited to 2 MB each.",
            "Milestone references and completion reports are claims, never verified acceptance or approval.",
            "Repository file inventories exclude generated dependencies and symlinks.",
        ],
    )


def claim_text(mid: str, evidence: Evidence) -> str:
    """Keep a next-milestone recommendation from becoming a claim about its parent report."""
    path_ids = {m.group(1).upper() for m in MILESTONE.finditer(Path(evidence.path).stem)}
    relevant = []
    for sentence in re.split(r"[.;]\s+", evidence.excerpt):
        mentioned = {m.group(1).upper() for m in MILESTONE.finditer(sentence)}
        if mid in mentioned or (not mentioned and mid in path_ids):
            relevant.append(sentence)
    return " ".join(relevant)


def adjudicate_claim(mid: str, evidence: Evidence) -> dict:
    """Separate planning/component claims; uncertainty never establishes supersession."""
    text = claim_text(mid, evidence)
    negative = bool(
        re.search(r"not started|not implemented|no .*implemented|not executed", text, re.I)
    )
    result = {
        "repository": evidence.repository,
        "path": evidence.path,
        "line": evidence.line,
        "sha256": evidence.sha256,
        "observed_head": evidence.head,
        "modified_at": evidence.modified_at,
        "claim_text": text,
        "disposition": "claim-only",
        "blocks": False,
        "superseded": False,
        "reason": "Claims do not establish acceptance.",
    }
    if not negative:
        return result
    # A prompt/sequence recommendation says what the old plan proposed, not what
    # the current delivery contains. Preserve it, but do not compare it as status.
    if re.fullmatch(
        rf"\s*#*\s*Recommended Milestone {re.escape(mid)} "
        r"(?:prompt|sequence|integration tasks) \(not (?:started|executed)\)\s*",
        text,
        re.I,
    ):
        result.update(
            disposition="planning-only", reason="Recommended prompt/sequence, not delivery status."
        )
        return result
    subject = rf"(?:milestone[ _-]*|M){re.escape(mid)}(?![A-Za-z0-9])"
    explicit = re.search(
        subject
        + r"\s+(?:(?:was|is|has|had|been|yet)\s+)*(?:not started|not implemented|not executed)",
        text,
        re.I,
    ) or re.search(
        r"no\s+" + subject + r"\s+(?:feature\s+)?(?:was\s+|is\s+)?implemented", text, re.I
    )
    # Short status-only lines in a milestone-specific document remain status.
    status_only = re.fullmatch(
        r"[\s#*|:-]*(?:status[\s:*-]+)?not (?:started|implemented|executed)[\s.*|]*", text, re.I
    )
    bounded_component = re.search(
        r"no renderer, client or terrain engine is implemented[.]?$", text, re.I
    ) or re.fullmatch(
        r"\s*\| Compose overlay config --quiet \| PASS .*shared services were not started \|\s*",
        text,
        re.I,
    )
    if not explicit and not status_only and bounded_component:
        result.update(
            disposition="component-or-validation-scope",
            reason="Negative phrase concerns a component or validation action, not milestone delivery.",
        )
        return result
    path_ids = {m.group(1).upper() for m in MILESTONE.finditer(Path(evidence.path).stem)}
    historical = bool(
        path_ids and mid not in path_ids and re.search(r"report|completion", evidence.path, re.I)
    )
    result.update(
        disposition="historical-unresolved" if historical else "status-negative",
        blocks=True,
        reason=(
            "Predecessor report status requires explicit provenance-backed supersession review."
            if historical
            else "Explicit negative milestone status requires comparison with implementation/completion claims."
        ),
    )
    if not evidence.modified_at:
        result["reason"] += " Missing timestamp; temporal ordering is unknown."
    result["reason"] += (
        " Observation HEAD and filesystem mtime do not establish claim origin or Git ancestry."
    )
    return result


def recover_milestones(
    repositories: list[dict], evidence: list[Evidence]
) -> list[RecoveredMilestone]:
    ids = set(TARGETS)
    for e in evidence:
        ids.update(
            m.group(1).upper() for m in MILESTONE.finditer(e.excerpt + " " + Path(e.path).stem)
        )
    recovered = []
    for mid in sorted(ids, key=lambda v: (int(re.match(r"[0-9]+", v)[0]), v)):
        mapped = [
            e
            for e in evidence
            if mid
            in {m.group(1).upper() for m in MILESTONE.finditer(e.excerpt + " " + Path(e.path).stem)}
        ]
        # Only milestone-specific documents or affirmative README implementation statements
        # connect code/test inventories. A recommendation mentioning the next milestone does not.
        implemented_repos = set()
        for e in mapped:
            path_ids = {m.group(1).upper() for m in MILESTONE.finditer(Path(e.path).stem)}
            affirmative = re.search(
                r"implements|is implemented|implementation resides|^milestone.*(service|release|version|angular)",
                claim_text(mid, e),
                re.I,
            )
            if (
                mid in path_ids and re.search(r"report|completion|development", e.path, re.I)
            ) or affirmative:
                if not re.search(
                    r"not (?:started|implemented)|no .*implemented|recommended|prompt",
                    claim_text(mid, e),
                    re.I,
                ):
                    implemented_repos.add(e.repository)
        related = [r for r in repositories if r["id"] in implemented_repos]
        implementation = [
            f"{r['id']}: {len(r['source_files'])} source files observed; see inventory"
            for r in related
            if r["source_files"]
        ]
        has_implementation = bool(implementation)
        docs = [
            f"{e.repository}/{e.path}:{e.line}: {e.excerpt}"
            for e in mapped
            if e.kind == "document"
            and e.excerpt.strip()
            and re.search(r"objective|scope|implement|acceptance|^- |^\|", e.excerpt, re.I)
        ]
        result_evidence = [
            e for e in evidence if e.kind == "test-result" and e.repository in implemented_repos
        ]
        claims_complete = any(
            re.search(r"complete|verified|all .*pass", claim_text(mid, e), re.I) for e in mapped
        )
        adjudications = [adjudicate_claim(mid, e) for e in mapped]
        claims_unstarted = any(a["blocks"] for a in adjudications)
        validation_conflicts = (
            [
                "Historical test artifacts include failed, skipped-only or empty suites; current acceptance remains unverified."
            ]
            if any(e.outcome != "historical-pass" for e in result_evidence)
            else []
        )
        recovered.append(
            RecoveredMilestone(
                id=mid,
                classification="PARTIAL" if has_implementation else "UNVERIFIED",
                confidence="medium" if has_implementation else "low",
                objectives=docs[:30],
                implementation=implementation,
                repositories=sorted({e.repository for e in mapped}),
                tests=[f"{r['id']}/{t}" for r in related for t in r["test_files"]],
                evidence=mapped + result_evidence,
                outstanding=[
                    "Map authoritative acceptance criteria to reproducible validation at the current worktree.",
                    "Review historical claims and obtain human approval separately.",
                ],
                missing_documentation=[]
                if docs
                else ["Authoritative milestone specification/acceptance criteria not recovered."],
                adjudications=adjudications,
                conflicts=validation_conflicts
                + (
                    [
                        "Both completion/implementation and not-started claims occur; inspect dates and scope."
                    ]
                    if claims_unstarted and (claims_complete or has_implementation)
                    else []
                ),
            )
        )
    return recovered
