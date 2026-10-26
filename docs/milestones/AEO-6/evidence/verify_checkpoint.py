"""Observe registered scope and verify its immutable preparation inputs without approving."""
import hashlib
import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.configuration import load_yaml
from agrosphere_orchestrator.design import canonical, design_status, generate_design
from agrosphere_orchestrator.design_agents import TemplateDocumentationAgents
from agrosphere_orchestrator.design_artifacts import LocalPlantUML, digest, source_findings
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator.design_validation import verify_context
from agrosphere_orchestrator.persistence import DesignDecision
from agrosphere_orchestrator.recovery import recovery_engine
root = Path.cwd()
out = root / "docs/milestones/AEO-6"
s = Settings(repository_manifest=out / "design-repositories.json")
inputs = load_yaml(out / "requirements-input.json", DesignInput)
repositories = verify_context(inputs, s.repository_manifest, s.role_registry)
expected = digest(canonical({"input": inputs.model_dump(mode="json"), "repositories": repositories}))
engine = recovery_engine(s.database_url, readonly=True)
status = design_status(engine, "agrosphere:AEO-6")
assert status["scope_id"] == expected
assert status.get("revision_id") is None
with Session(engine) as session:
    assert not list(session.scalars(select(DesignDecision).where(DesignDecision.case_id == "agrosphere:AEO-6")))
try:
    generate_design(engine, "agrosphere:AEO-6", TemplateDocumentationAgents(), LocalPlantUML(None), "not-invoked")
except PermissionError as exc:
    guard = str(exc)
else:
    raise AssertionError("Missing requirements approval did not block generation")
assert all(not source_findings(d.approved_source) for d in inputs.diagrams)
(out / "REVIEW_PACKAGE.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
result = {"scope_id": expected, "state": status["state"], "checkpoint": "AWAITING_REQUIREMENTS_APPROVAL", "requirements": len(inputs.requirements), "proposed_tasks": len(inputs.plan.tasks), "context_hashes_verified": len(inputs.context), "diagram_sources_checked": len(inputs.diagrams), "design_revision": None, "approval_decisions": 0, "generation_guard": guard, "source_implementation_started": False, "repositories": repositories}
(out / "evidence/checkpoint-verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
engine.dispose()
