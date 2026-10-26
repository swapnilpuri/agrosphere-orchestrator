"""Validate actual candidate artifacts in temporary storage. Not a formal persisted validation."""
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from agrosphere_orchestrator.configuration import load_yaml
from agrosphere_orchestrator.design_agents import ROLES, RuleBasedArchitectureReviewer, TemplateDocumentationAgents
from agrosphere_orchestrator.design_artifacts import digest, write_artifacts
from agrosphere_orchestrator.design_models import Artifact, DesignInput, DocumentationTask
from agrosphere_orchestrator.design_validation import deterministic_findings

base = Path("docs/milestones/AEO-5")
workflow = json.loads((base / "evidence/internal-design-workflow.json").read_text())
scope = workflow["scope_id"]
inputs = load_yaml(base / "requirements-input-internal.json", DesignInput)
revision = digest(scope + ":preview-only-not-persisted")
artifacts = []
for role in ROLES:
    result = TemplateDocumentationAgents().generate(DocumentationTask(role=role, phase="design", milestone="AEO-5", scope_digest=scope), inputs)
    assert not result.findings
    artifacts.extend(result.artifacts)
for a in list(artifacts):
    if a.type.startswith("diagram:"):
        svg = (base / "approval-preview" / scope / a.path).with_suffix(".svg").read_text(encoding="utf-8")
        artifacts.append(Artifact(type=a.type.replace("diagram:", "render:"), repository=a.repository, path=a.path.removesuffix(".puml") + ".svg", content=svg, sha256=digest(svg), requirement_ids=a.requirement_ids, agent=a.agent))
for a in artifacts:
    a.path = f"docs/milestones/AEO-5/revisions/{revision}/" + a.path
with tempfile.TemporaryDirectory(prefix="aeo5-candidate-preflight-") as directory:
    repositories = {"agrosphere-orchestrator": directory}
    write_artifacts(artifacts, repositories)
    findings = deterministic_findings(inputs, artifacts, repositories, "design", scope, revision)
    findings += RuleBasedArchitectureReviewer().review(inputs, artifacts)
result = {"executed_at": datetime.now(UTC).isoformat(), "scope_id": scope, "formal_design_validation": False, "persisted_validation_id": None, "storage": "Temporary preview artifact storage; no database revision, validation or approval written", "passed": not any(f.severity == "error" for f in findings), "artifact_count": len(artifacts), "findings": [f.model_dump() for f in findings]}
(base / "evidence/candidate-preflight.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(not result["passed"])
