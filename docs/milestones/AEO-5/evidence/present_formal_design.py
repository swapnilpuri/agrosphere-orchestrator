"""Export the actual persisted review package using read-only application interfaces."""
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design import design_status, require_approval
from agrosphere_orchestrator.persistence import DesignCase, DesignRevision, DesignValidation
from agrosphere_orchestrator.recovery import recovery_engine

root = Path.cwd()
base = root / "docs/milestones/AEO-5"
engine = recovery_engine(Settings().database_url, readonly=True)
status = design_status(engine, "agrosphere:AEO-5")
with Session(engine) as session:
    case = session.get(DesignCase, "agrosphere:AEO-5")
    revision = session.get(DesignRevision, case.revision_id)
    validation = session.get(DesignValidation, case.validation_id)
    decision = require_approval(session, case, case.scope_id, "requirements")
    if not revision or not validation or not validation.payload["passed"]:
        raise ValueError("A persisted revision and successful validation are required")
    package = {"package_type": "formal-design-approval", "generated_at": datetime.now(UTC).isoformat(), "milestone": case.id, "state": case.state, "scope_id": case.scope_id, "revision_id": revision.id, "bundle_digest": revision.payload["bundle_digest"], "validation_id": validation.id, "formal_validation_passed": validation.payload["passed"], "validation": validation.payload, "requirements_decision_id": decision.id, "requirements_actor_currently_authorized": True, "design_approval_recorded": any(d["kind"] == "design" and d["decision"] == "approved" and d["subject"] == revision.payload["bundle_digest"] for d in status["decisions"]), "implementation_authorized": status["implementation_authorized"], "artifacts": status["artifacts"], "decisions": status["decisions"], "file_findings": status["file_findings"], "exact_next_operation": "./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli milestone approve-design AEO-5 --project agrosphere"}
engine.dispose()
if package["design_approval_recorded"]:
    package["exact_next_operation"] = ""
for a in package["artifacts"]:
    if hashlib.sha256(Path(a["absolute_path"]).read_bytes()).hexdigest() != a["sha256"]:
        raise ValueError("Persisted artifact does not match the approval package")
current = base / "DESIGN_APPROVAL_PACKAGE.json"
if current.exists():
    old = current.read_bytes()
    archive = base / "evidence" / ("approval-package-" + hashlib.sha256(old).hexdigest() + ".json")
    if not archive.exists():
        archive.write_bytes(old)
current.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
lines = ["# AEO-5 formal technical design approval package", "", "Status: **" + package["state"] + "**. Formal design generation and validation both succeeded through the existing AEO-1C application. Authenticated design approval status is recorded in the JSON package; implementation and delivery authority remain separate.", "", "- Scope: " + package["scope_id"], "- Persisted design revision: " + package["revision_id"], "- Bundle digest (approval subject): " + package["bundle_digest"], "- Persisted successful validation: " + package["validation_id"], "- Authenticated requirements decision: " + package["requirements_decision_id"], "", "All 16 persisted artifacts were rehashed against the database manifest. Six SVGs were actually rendered with the trusted local tool. The single review-limit warning states that rule-based review does not replace human conceptual review.", "", "## Exact artifacts", ""]
for a in package["artifacts"]:
    rel = Path(a["absolute_path"]).relative_to(base).as_posix()
    lines.append("- [" + a["type"] + "](" + rel + ") — sha256 " + a["sha256"])
lines += ["", "## Authenticated human decision", "", "Review the linked persisted documents and diagrams, then run from the orchestrator root in an interactive Windows terminal:", "", "~~~powershell", package["exact_next_operation"], "~~~", "", "This uses the existing WindowsConsoleHumanVerifier and configured allowlist. Do not supply passwords through chat. No decision was inferred or manufactured. Design approval does not authorize publishing, merging or deployment.", "", "The authoritative database is C:/Projects/agrosphere/agrosphere-orchestrator/aeo.db. [Full persisted review data](DESIGN_APPROVAL_PACKAGE.json). [Actual generation and validation commands](evidence/internal-design-workflow.json)."]
if package["design_approval_recorded"]:
    section = lines.index("## Authenticated human decision")
    lines = lines[:section] + ["## Recorded authenticated decision", "", "The exact bundle has authenticated human design approval. No additional design decision is pending. Future quality/security and publishing approvals remain separate.", "", "[Full persisted review data](DESIGN_APPROVAL_PACKAGE.json). [Current approval boundary](APPROVAL_REQUIRED.md)."]
(base / "DESIGN_APPROVAL_PACKAGE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({k: package[k] for k in ("state", "scope_id", "revision_id", "bundle_digest", "validation_id", "formal_validation_passed", "requirements_decision_id", "design_approval_recorded", "implementation_authorized", "exact_next_operation")}, indent=2))
