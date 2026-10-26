"""Read-only verification of the existing AEO-1C AEO-5 gate."""
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design import assert_design_gate, canonical, design_status, require_approval
from agrosphere_orchestrator.design_artifacts import digest
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator.design_validation import verify_stored_context
from agrosphere_orchestrator.persistence import AuditEvent, DesignCase, DesignDecision, DesignRevision, DesignScope, DesignValidation, Milestone
from agrosphere_orchestrator.recovery import recovery_engine

settings = Settings()
engine = recovery_engine(settings.database_url, readonly=True)
key = "agrosphere:AEO-5"
status = design_status(engine, key)
result = {"verified_at": datetime.now(UTC).isoformat(), "database_path": str(Path(make_url(settings.database_url).database).resolve()), "database_access": "SQLite mode=ro", "milestone": key, "state": status["state"], "scope_id": status.get("scope_id"), "revision_id": status.get("revision_id"), "validation": status.get("validation"), "implementation_authorized": status.get("implementation_authorized", False), "revision_history": status.get("revision_history", []), "decisions": status.get("decisions", [])}
with Session(engine) as session:
    case = session.get(DesignCase, key)
    scope = session.get(DesignScope, case.scope_id)
    result["stored_scope_hash_matches"] = digest(canonical(scope.payload)) == scope.id
    try:
        verify_stored_context(DesignInput.model_validate(scope.payload["input"]), scope.payload["repositories"])
        result["stored_context_valid"] = True
    except (OSError, ValueError) as exc:
        result["stored_context_valid"] = False
        result["context_error"] = str(exc)
    try:
        decision = require_approval(session, case, case.scope_id, "requirements")
        result["requirements_approval_currently_authorized"] = True
        result["requirements_decision_id"] = decision.id
    except PermissionError as exc:
        result["requirements_approval_currently_authorized"] = False
        result["requirements_error"] = str(exc)
    revisions = list(session.scalars(select(DesignRevision).where(DesignRevision.case_id == key)))
    decisions = list(session.scalars(select(DesignDecision).where(DesignDecision.case_id == key)))
    result["design_revision_count"] = len(revisions)
    result["design_decision_count"] = sum(d.kind == "design" for d in decisions)
    result["validation_id"] = case.validation_id
    result["decision_audit_matches"] = [{"decision_id": d.id, "kind": d.kind, "actor_currently_authorized": d.actor in settings.design_approvers, "audit_event_ids": [a.id for a in session.scalars(select(AuditEvent).where(AuditEvent.entity_id == key, AuditEvent.kind == "design.human-decision")) if a.payload.get("decision_id") == d.id and a.actor == d.actor and a.payload.get("subject") == d.subject and a.payload.get("decision") == d.decision]} for d in decisions]
    milestone = session.scalar(select(Milestone).where(Milestone.project_id == "agrosphere", Milestone.external_id == "AEO-5"))
    result["implementation_plan_imported"] = milestone is not None
    try:
        assert_design_gate(session, milestone or SimpleNamespace(project_id="agrosphere", external_id="AEO-5"))
        result["existing_state_machine_gate_passed"] = True
    except (PermissionError, ValueError, OSError) as exc:
        result["existing_state_machine_gate_passed"] = False
        result["gate_error"] = str(exc)
result["acceptance"] = "NOT_ASSESSED_BY_GATE_VERIFIER"
result["production_implementation_started"] = status["state"] in {"IMPLEMENTING", "IMPLEMENTATION_VALIDATING", "AWAITING_DELIVERY_APPROVAL", "COMPLETED"}
if result["production_implementation_started"] and not result["stored_context_valid"]:
    result["context_change_note"] = "Initial source context changed during authorized implementation; AEO-1C intentionally checks immutable approved design artifacts rather than freezing implementation source after entering IMPLEMENTING."
result["remote_mutations_performed"] = False
result["aeo6_started"] = False
result["assurance"] = "Existing authenticated decision handler and matching persisted audit events checked; historical authentication cannot be independently re-performed by this read-only verifier."
out = Path(__file__).parent / ("implementation-gate-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".json")
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"evidence": str(out), **result}, indent=2))
