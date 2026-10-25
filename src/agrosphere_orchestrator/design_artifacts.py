"""Immutable, repository-owned documentation files and deterministic PlantUML."""

import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Protocol

from .design_models import Artifact, DiagramSpec, Finding


def digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def owned_path(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative)
    if "\\" in relative or ":" in relative or parts.is_absolute() or ".." in parts.parts:
        raise ValueError("unsafe artifact path")
    if len(parts.parts) < 5 or parts.parts[:2] != ("docs", "milestones"):
        raise ValueError("artifact must be beneath docs/milestones/<id>/revisions/<revision>")
    base = root.resolve()
    target = base.joinpath(*parts.parts)
    cursor = target
    while cursor != base:
        if cursor.is_symlink():
            raise ValueError("artifact paths cannot traverse symlinks")
        cursor = cursor.parent
    if not target.resolve().is_relative_to(base):
        raise ValueError("artifact escapes repository")
    return target


def write_artifacts(artifacts: list[Artifact], repositories: dict[str, str]) -> None:
    # Preflight every owner and existing artifact; never overwrite a modified version.
    targets = []
    for artifact in artifacts:
        if artifact.repository not in repositories:
            raise ValueError("unknown artifact owner")
        if digest(artifact.content) != artifact.sha256:
            raise ValueError("artifact content hash mismatch")
        target = owned_path(Path(repositories[artifact.repository]), artifact.path)
        if target.exists() and target.read_bytes() != artifact.content.encode("utf-8"):
            raise ValueError(f"immutable artifact already exists with different content: {target}")
        targets.append((target, artifact.content))
    for target, content in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    newline="",
                    dir=target.parent,
                    prefix=".aeo-",
                    suffix=".tmp",
                    delete=False,
                ) as output:
                    temporary = Path(output.name)
                    output.write(content)
                    output.flush()
                    os.fsync(output.fileno())
                # A hard link publishes the complete file atomically and never replaces an existing version.
                try:
                    os.link(temporary, target)
                except FileExistsError:
                    if target.read_bytes() != content.encode("utf-8"):
                        raise ValueError(
                            f"Immutable artifact changed during publication: {target}"
                        ) from None
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)


def check_files(artifacts: list[Artifact], repositories: dict[str, str]) -> list[Finding]:
    findings = []
    for artifact in artifacts:
        try:
            path = owned_path(Path(repositories[artifact.repository]), artifact.path)
            if hashlib.sha256(path.read_bytes()).hexdigest() != artifact.sha256:
                raise ValueError("artifact changed since generation")
        except (KeyError, OSError, ValueError) as exc:
            findings.append(
                Finding(code="artifact-integrity", message=str(exc), artifact=artifact.path)
            )
    return findings


def label(value: str) -> str:
    # Reject PlantUML directives and delimiters rather than escaping executable text.
    if any(c in value for c in ('"', "\n", "\r", "@", "!", "{", "}", "\\")):
        raise ValueError("unsupported diagram label characters")
    return value


def plantuml(spec: DiagramSpec) -> str:
    if spec.kind == "activity" and spec.edges:
        expected = [(spec.nodes[i].id, spec.nodes[i + 1].id) for i in range(len(spec.nodes) - 1)]
        if [(e.source, e.target) for e in spec.edges] != expected:
            raise ValueError(
                "Activity adapter supports explicit linear workflows only; branching needs a reviewed adapter"
            )
    lines = ["@startuml", f"title {label(spec.id)}"]
    if spec.kind in {"context", "container", "component"}:
        library, macro = {
            "context": ("C4_Context", "System"),
            "container": ("C4_Container", "Container"),
            "component": ("C4_Component", "Component"),
        }[spec.kind]
        lines.append(f"!include <C4/{library}>")
        lines.extend(
            f'{macro}({n.id}, "{label(n.label)}"' + (', ""' if macro != "System" else "") + ")"
            for n in spec.nodes
        )
        lines.extend(f'Rel({e.source}, {e.target}, "{label(e.label)}")' for e in spec.edges)
    elif spec.kind == "activity":
        lines.append("start")
        lines.extend(f":{label(n.label)};" for n in spec.nodes)
        lines.append("stop")
    else:
        shape = {
            "sequence": "participant",
            "domain": "class",
            "state": "state",
            "data-flow": "rectangle",
            "deployment": "node",
        }[spec.kind]
        lines.extend(f'{shape} "{label(n.label)}" as {n.id}' for n in spec.nodes)
        arrow = "->" if spec.kind == "sequence" else "-->"
        lines.extend(f"{e.source} {arrow} {e.target} : {label(e.label)}" for e in spec.edges)
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def source_findings(source: str) -> list[Finding]:
    if source.count("@startuml") != 1 or source.count("@enduml") != 1:
        return [
            Finding(code="plantuml-source", message="exactly one @startuml/@enduml pair required")
        ]
    if not source.strip().startswith("@startuml") or not source.strip().endswith("@enduml"):
        return [Finding(code="plantuml-source", message="PlantUML delimiters out of order")]
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("!") and stripped not in {
            "!include <C4/C4_Context>",
            "!include <C4/C4_Container>",
            "!include <C4/C4_Component>",
        }:
            return [
                Finding(
                    code="plantuml-directive",
                    message="external/custom PlantUML directives forbidden",
                )
            ]
        if re.search(r"https?://|file://|%getenv|%load|%read|%invoke|%call", stripped, re.I):
            return [
                Finding(
                    code="plantuml-directive",
                    message="dynamic or external PlantUML input forbidden",
                )
            ]
    return []


class DiagramRenderer(Protocol):
    def render(self, source: str) -> tuple[str | None, list[Finding]]: ...


class LocalPlantUML:
    def __init__(self, jar: Path | None, java: str = "java"):
        self.jar, self.java = jar, java

    def render(self, source: str) -> tuple[str | None, list[Finding]]:
        problems = source_findings(source)
        if problems:
            return None, problems
        if self.jar is None or not self.jar.is_file():
            return None, [
                Finding(
                    code="plantuml-unavailable",
                    message="Configure AEO_PLANTUML_JAR; rendering is required for approval.",
                )
            ]
        try:
            with tempfile.TemporaryDirectory(prefix="aeo-plantuml-") as directory:
                p = Path(directory) / "diagram.puml"
                p.write_text(source, encoding="utf-8")
                base = [
                    self.java,
                    "-Djava.awt.headless=true",
                    "-DPLANTUML_SECURITY_PROFILE=SANDBOX",
                    "-jar",
                    str(self.jar.resolve()),
                    "-charset",
                    "UTF-8",
                ]
                for args in (["-checkonly", str(p)], ["-tsvg", "-failfast2", str(p)]):
                    result = subprocess.run(
                        [*base, *args], capture_output=True, text=True, timeout=30
                    )
                    if result.returncode:
                        return None, [
                            Finding(
                                code="plantuml-render",
                                message=f"exit={result.returncode}: {result.stderr[-1500:]}",
                            )
                        ]
                svg = p.with_suffix(".svg").read_text(encoding="utf-8")
                if "<svg" not in svg or "Syntax Error" in svg or "<script" in svg.lower():
                    raise ValueError("invalid/error SVG output")
                return svg, []
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            return None, [Finding(code="plantuml-render", message=str(exc))]
