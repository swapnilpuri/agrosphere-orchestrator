"""Register the corrected scope and use the ordinary CLI; never supplies human approval."""
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.configuration import load_yaml
from agrosphere_orchestrator.design import canonical, design_status, register_requirements
from agrosphere_orchestrator.design_agents import ROLES, TemplateDocumentationAgents
from agrosphere_orchestrator.design_artifacts import LocalPlantUML, digest
from agrosphere_orchestrator.design_models import DesignInput, DocumentationTask
from agrosphere_orchestrator.design_validation import expected_owners, verify_context
from agrosphere_orchestrator.recovery import recovery_engine

root = Path.cwd()
base = root / "docs/milestones/AEO-5"
settings = Settings()
manifest = base / "design-repositories-internal.json"
source = base / "requirements-input-internal.json"
inputs = load_yaml(source, DesignInput)
repositories = verify_context(inputs, manifest, settings.role_registry)
scope = digest(canonical({"input": inputs.model_dump(mode="json"), "repositories": repositories}))
preview = base / "approval-preview" / scope
preview.mkdir(parents=True, exist_ok=True)
jar = root / ".aeo/tools/plantuml-1.2026.9.jar"
renderer = LocalPlantUML(jar, settings.java_executable)
records, findings = [], []
for role in ROLES:
    output = TemplateDocumentationAgents().generate(DocumentationTask(role=role, phase="design", milestone="AEO-5", scope_digest=scope), inputs)
    findings.extend(f.model_dump() for f in output.findings)
    for artifact in output.artifacts:
        if artifact.repository not in expected_owners(artifact.type, inputs):
            raise ValueError("Invalid preview artifact owner")
        target = preview / artifact.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(artifact.content.encode("utf-8"))
        records.append({"type": artifact.type, "file": str(target.relative_to(root)), "sha256": artifact.sha256})
        if artifact.type.startswith("diagram:"):
            svg, problems = renderer.render(artifact.content)
            findings.extend(f.model_dump() for f in problems)
            if svg is not None:
                rendered = target.with_suffix(".svg")
                rendered.write_bytes(svg.encode("utf-8"))
                records.append({"type": artifact.type.replace("diagram:", "render:"), "file": str(rendered.relative_to(root)), "sha256": digest(svg)})
if any(f["severity"] == "error" for f in findings):
    raise ValueError(json.dumps(findings))
engine = recovery_engine(settings.database_url)
registered = register_requirements(engine, inputs, manifest, settings.role_registry)
assert registered == scope
engine.dispose()
env = os.environ.copy()
env["AEO_PLANTUML_JAR"] = str(jar)
commands = []
for operation in ("design", "validate-design"):
    argv = [sys.executable, "-m", "agrosphere_orchestrator.cli", "milestone", operation, "AEO-5", "--project", "agrosphere"]
    completed = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, timeout=180)
    commands.append({"argv": argv, "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
engine = recovery_engine(settings.database_url, readonly=True)
status = design_status(engine, "agrosphere:AEO-5")
engine.dispose()
result = {"executed_at": datetime.now(UTC).isoformat(), "scope_id": scope, "requirements_file": str(source), "manifest": str(manifest), "preflight": {"passed": True, "formal_design_validation": False, "reused_narratives": True, "reused_diagram_count": len(inputs.diagrams), "artifacts": records, "findings": findings, "renderer_jar": str(jar), "renderer_sha256": hashlib.sha256(jar.read_bytes()).hexdigest()}, "commands": commands, "status": status, "approval_granted_by_this_script": False}
(base / "evidence/internal-design-workflow.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"scope_id": scope, "preview_artifact_count": len(records), "state": status["state"], "revision_id": status["revision_id"], "commands": [{"operation": c["argv"][4], "exit_code": c["exit_code"], "stderr": c["stderr"]} for c in commands]}, indent=2))
