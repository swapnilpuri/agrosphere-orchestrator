"""Deterministic design gates, independent of generation and conceptual review."""

import hashlib
import re
from pathlib import Path, PurePosixPath

import yaml

from .configuration import Repository, RepositoryManifest, RoleRegistry, load_yaml
from .design_agents import ROLES, SECTIONS
from .design_artifacts import check_files, digest, source_findings
from .design_models import Artifact, DesignInput, Finding
from .repositories import inspect_repository


def verify_context(inputs: DesignInput, manifest_path: Path, registry_path: Path) -> dict[str, str]:
    roles = load_yaml(registry_path, RoleRegistry).by_id()
    if not set(ROLES) <= roles.keys():
        raise ValueError("Required documentation roles are absent")
    if (
        any("document" not in roles[role].allowed_operations for role in ROLES)
        or "review-design" not in roles["solution-architect"].allowed_operations
    ):
        raise ValueError("Documentation/review operations are not authorized by the role registry")
    declared = {
        r.id: r for r in load_yaml(manifest_path, RepositoryManifest).resolve(manifest_path)
    }
    needed = {t.repository for t in inputs.plan.tasks} | {c.repository for c in inputs.context}
    needed |= {"agrosphere-architecture"} | {d.repository for d in inputs.diagrams}
    if inputs.contract_impact or inputs.contracts:
        needed.add("agrosphere-contracts")
    repositories = {}
    heads = {}
    for name in sorted(needed):
        if name not in declared or declared[name].status != "confirmed":
            raise ValueError(f"Unknown/unconfirmed repository: {name}")
        inspected = inspect_repository(declared[name])
        if inspected.error or not inspected.is_git:
            raise ValueError(f"Unavailable repository: {name}: {inspected.error}")
        repositories[name] = inspected.path
        heads[name] = inspected.head
    for context in inputs.context:
        relative = PurePosixPath(context.path)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "\\" in context.path
            or ":" in context.path
        ):
            raise ValueError("Unsafe context reference path")
        root = Path(repositories[context.repository]).resolve()
        target = root.joinpath(*relative.parts)
        if not target.resolve().is_relative_to(root) or target.is_symlink():
            raise ValueError("Context escapes repository or uses symlink")
        if target.suffix.lower() not in {
            ".md",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".java",
            ".py",
            ".ts",
            ".sql",
            ".proto",
            ".puml",
        }:
            raise ValueError("Unsupported context document type")
        if target.stat().st_size > 2_000_000:
            raise ValueError("Context document exceeds 2 MB")
        if hashlib.sha256(target.read_bytes()).hexdigest() != context.sha256:
            raise ValueError("Context content does not match verified hash")
        if context.head != heads[context.repository]:
            raise ValueError("Context HEAD does not match current repository")
    return repositories


def expected_owners(kind: str, inputs: DesignInput) -> set[str]:
    services = {t.repository for t in inputs.plan.tasks} - {
        "agrosphere-architecture",
        "agrosphere-contracts",
        "agrosphere-orchestrator",
    }
    if kind in {"business", "architecture", "overview", "as-built"}:
        return {"agrosphere-architecture"}
    if kind == "contracts" or kind.startswith("proposal:"):
        return {"agrosphere-contracts"}
    if kind == "service":
        return services
    if kind.startswith("diagram:"):
        diagram = kind.split(":", 1)[1]
        if diagram in {"context", "container", "data-flow", "deployment", "activity"}:
            return {"agrosphere-architecture"}
        if diagram in {"component", "domain", "state"}:
            return services
        return services | {"agrosphere-architecture"}
    if kind.startswith("render:"):
        return expected_owners("diagram:" + kind.split(":", 1)[1], inputs)
    return set()


def deterministic_findings(
    inputs: DesignInput,
    artifacts: list[Artifact],
    repositories: dict[str, str],
    phase: str,
    scope_id: str,
    revision_id: str,
) -> list[Finding]:
    findings = check_files(artifacts, repositories)
    requirement_ids = {r.id for r in inputs.requirements}
    if not requirement_ids:
        findings.append(Finding(code="requirements", message="Approved requirements are missing"))
    required = (
        [
            ("architecture", "agrosphere-architecture"),
            ("business", "agrosphere-architecture"),
            ("overview", "agrosphere-architecture"),
        ]
        if phase == "design"
        else [("as-built", "agrosphere-architecture"), ("overview", "agrosphere-architecture")]
    )
    required += [("service", repo) for repo in expected_owners("service", inputs)]
    if inputs.contract_impact:
        required.append(("contracts", "agrosphere-contracts"))
        if not inputs.contracts:
            findings.append(
                Finding(
                    code="contracts", message="Contract impact declared without versioned proposals"
                )
            )
    for kind, owner in required:
        if not any(a.type == kind and a.repository == owner for a in artifacts):
            findings.append(Finding(code="required-document", message=f"Missing {owner}/{kind}"))
    if not inputs.diagrams or not any(a.type.startswith("diagram:") for a in artifacts):
        findings.append(
            Finding(
                code="diagram-presence", message="At least one scope-relevant diagram is required"
            )
        )
    paths = {(a.repository, a.path) for a in artifacts}
    if len(paths) != len(artifacts):
        findings.append(Finding(code="duplicate-artifact", message="Duplicate artifact paths"))
    for artifact in artifacts:

        def problem(code, message):
            findings.append(Finding(code=code, message=message, artifact=artifact.path))

        expected_role = (
            "business-analyst"
            if artifact.type == "business"
            else ("technical-writer" if artifact.type == "overview" else "solution-architect")
        )
        if artifact.agent != expected_role:
            problem("generating-agent", "Artifact generated by the wrong documentation role")
        if artifact.repository not in expected_owners(artifact.type, inputs):
            problem("ownership", "Artifact assigned to the wrong repository")
        if not artifact.requirement_ids or not set(artifact.requirement_ids) <= requirement_ids:
            problem("traceability", "Missing or unknown source requirements")
        prefix = f"docs/milestones/{inputs.plan.id}/revisions/{revision_id}/"
        if not artifact.path.startswith(prefix):
            problem("revision-consistency", "Artifact path does not match exact revision")
        if artifact.sha256 != digest(artifact.content):
            problem("content-hash", "Manifest content hash mismatch")
        if artifact.type in SECTIONS:
            for section in SECTIONS[artifact.type]:
                if not re.search(r"^## " + re.escape(section) + r"\s*$", artifact.content, re.M):
                    problem("required-section", f"Missing section: {section}")
                else:
                    body = re.search(
                        r"^## " + re.escape(section) + r"\s*\n(.*?)(?=^## |\Z)",
                        artifact.content,
                        re.M | re.S,
                    )
                    if body is None or not body.group(1).strip():
                        problem("required-section", f"Empty section: {section}")
            if re.search(r"MISSING:|\bTODO\b|\bTBD\b", artifact.content, re.I):
                problem("missing-information", "Unresolved documentation placeholder")
            if (
                f"Scope: {scope_id}" not in artifact.content
                or inputs.plan.id not in artifact.content
            ):
                problem("scope-traceability", "Document does not identify exact milestone/scope")
            if not all(rid in artifact.content for rid in artifact.requirement_ids):
                problem("requirement-traceability", "Document requirement references are absent")
        if artifact.type.startswith("diagram:"):
            findings.extend(source_findings(artifact.content))
            if not any(
                a.path == artifact.path.removesuffix(".puml") + ".svg"
                and a.repository == artifact.repository
                for a in artifacts
            ):
                problem("diagram-render", "Validated SVG rendering is missing")
        if artifact.type.startswith("proposal:"):
            try:
                value = yaml.safe_load(artifact.content)
                if not isinstance(value, dict):
                    raise ValueError("Proposal must be a mapping")
                if artifact.type == "proposal:openapi" and not all(
                    k in value for k in ("openapi", "info", "paths")
                ):
                    raise ValueError("OpenAPI proposal lacks openapi/info/paths")
                if artifact.type == "proposal:event-schema" and not all(
                    k in value for k in ("$schema", "$id", "type")
                ):
                    raise ValueError("Event schema lacks versioned identity/type")
            except (yaml.YAMLError, ValueError) as exc:
                problem("contract-structure", str(exc))
        for owner, linked in re.findall(r"aeo://([A-Za-z0-9_.-]+)/([^\s)]+)", artifact.content):
            if (owner, linked) not in paths:
                problem("cross-reference", f"Broken cross-document reference: {owner}/{linked}")
    for spec in inputs.diagrams:
        if not any(
            a.path.endswith(f"/diagrams/{spec.id}.puml")
            and a.repository == spec.repository
            and a.type == "diagram:" + spec.kind
            for a in artifacts
        ):
            findings.append(
                Finding(code="diagram-presence", message=f"Declared diagram missing: {spec.id}")
            )
    return findings


def verify_stored_context(inputs: DesignInput, repositories: dict[str, str]) -> None:
    """Recheck approved evidence before generation; stale approval cannot invent context."""
    for ref in inputs.context:
        root = Path(repositories[ref.repository]).resolve()
        inspection = inspect_repository(
            Repository(id=ref.repository, path=root, status="confirmed")
        )
        target = root / ref.path
        if inspection.error or not inspection.is_git or inspection.head != ref.head:
            raise ValueError("Approved context repository HEAD changed or is unavailable")
        if not target.resolve().is_relative_to(root) or target.is_symlink():
            raise ValueError("Approved context path escaped repository")
        if hashlib.sha256(target.read_bytes()).hexdigest() != ref.sha256:
            raise ValueError(
                "Approved context file changed; revised requirements need human approval"
            )
