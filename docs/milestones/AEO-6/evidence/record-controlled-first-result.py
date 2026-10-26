"""Summarize existing controller evidence; no execution or approval mutations."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


root = Path(__file__).resolve().parent


def read(name):
    return json.loads((root / name).read_text(encoding="utf-8-sig"))


run = read("controlled-first-start.json")
status = read("controlled-first-status.json")
assert run["run_id"] == status["run_id"]
assert run["state"] == status["state"] == "BLOCKED"
assert run["checkpoint"]["category"] == "discovery-conflict"
assert run["usage"]["invocations"] == 0
found = next(
    e["payload"]["evidence"]
    for e in run["events"]
    if e["kind"] == "operation.committed"
)
before = read("controlled-first-plan.json")["discovery"]["snapshot"]
preservation = []
for repo in found["snapshot"]["repositories"]:
    prior = next(r for r in before["repositories"] if r["id"] == repo["id"])
    preservation.append(
        {
            "repository": repo["id"],
            "head_unchanged": prior["head"] == repo["head"],
            "status_unchanged": prior["status"] == repo["status"],
            "inventoried_fingerprints_unchanged": prior["file_fingerprints"]
            == repo["file_fingerprints"],
        }
    )
assert len(preservation) == 12
assert all(
    r["head_unchanged"]
    and r["status_unchanged"]
    and r["inventoried_fingerprints_unchanged"]
    for r in preservation
)
preflight = read("controlled-first-preflight.json")
native_hash = "7c52f3743063ffefaa36d65fd819c1613b755bdb84681b8e8e4d1077fd7e71db"
native_root = (
    Path(".aeo/autonomous")
    / "0c22b4cd3076c5b5c21a5fc53f088199ea03725a201d7cea3df7a08fd48cae92"
)
native_files = [str((native_root / (native_hash + ext)).resolve()) for ext in (".json", ".md")]
assert all(Path(p).is_file() for p in native_files)
summary = {
    "observed_at": datetime.now(UTC).isoformat(),
    "timezone": "America/Chicago",
    "command": ".\\.venv\\Scripts\\python.exe -m agrosphere_orchestrator.cli autonomous start --milestone 2 --mode local",
    "exit_code": 0,
    "run_id": run["run_id"],
    "mode": run["mode"],
    "milestone": run["milestone"],
    "state_transitions": ["PLANNED", "RECONCILING", "BLOCKED"],
    "events": [e["kind"] for e in run["events"]],
    "checkpoint": run["checkpoint"],
    "authorization": {
        "operator_start_authorization": "Explicit user authorization for exactly one bounded local Milestone 2 controller attempt verified from this request.",
        "separate_authenticated_start_decision": "Not required or exposed by the installed start/reconciliation implementation.",
        "aeo6_requirements_design_approval_verifier_exit": 0,
        "privileged_application_execution_grant_verified": False,
        "privileged_application_execution_grant_required_for_work_performed": False,
        "privileged_execution_performed": False,
        "application_requirements_design_plan_approvals": "Absent; not bypassed. Later-stage prerequisites, not authority to dispatch.",
    },
    "preflight": preflight,
    "limits": run["limits"],
    "usage": run["usage"],
    "completed_operations": [
        "Fresh AEO-6 approval linkage and source hash verification",
        "Current database, exact manifest roots, persisted recovery and budget inspection",
        "One real local start and one read-only RECONCILING operation",
        "Native persisted run validation (valid true, exit 0)",
        "Native immutable JSON/Markdown report export (exit 0)",
        "Read-only diagnosis of exact historical conflicts",
    ],
    "tasks_dispatched": [],
    "agents_invoked": [],
    "fresh_tests": "No unit/integration suite rerun in this turn. Fresh runtime preflight, supported start, status and native validate commands executed successfully. Earlier 36 readiness tests are prior-operation evidence.",
    "fresh_performance_measurements": [],
    "milestone_2_acceptance": "PARTIAL; functional evidence remains historical, reference-device FPS and initial useful estate view unverified; no formal acceptance.",
    "performance_criteria": {
        "fps": "30 FPS is proposed in NONFUNCTIONAL_REQUIREMENTS; an approved named reference device/workload/method was not recovered.",
        "initial_view": "Approved numeric threshold not recovered; do not treat the report's disclaimed 10-second reference as an approved requirement.",
        "benchmarks": "No performance npm script; graphics/live projects use SwiftShader and the graphics test logs combined navigation/remount duration, not an acceptance benchmark.",
    },
    "conflicts": read("controlled-first-conflict-diagnosis.json"),
    "remaining_prerequisites": [
        "Resolve chronological/scope conflicts for 1B, 1C and 2; the current CLI has no authenticated conflict-adjudication command or override.",
        "Prepare authoritative application scope and approved context-bound roadmap before later-stage eligibility.",
        "Exact requirements/design/plan and privileged task grants remain required before their protected operations.",
        "Execution/governance approvers are unconfigured, live execution disabled, and application quality criteria/validators absent.",
        "M2 approved reference device, timing criterion and measurement protocol remain unresolved.",
    ],
    "next_operator_action": "Review the exact historical claims in controlled-first-conflict-diagnosis.json and resolve the evidence-adjudication limitation through a separately reviewed documentation or orchestrator change. Do not alter approvals or delete historical evidence merely to clear the heuristic. Keep this run BLOCKED until the actual checkpoint is resolved.",
    "checkpoint_approval_command": None,
    "checkpoint_approval_explanation": "The real controller emitted command:null for discovery-conflict. This is an evidence/eligibility checkpoint, not a human approval request; no valid approval command can be supplied to clear it.",
    "read_only_operator_command": ".\\.venv\\Scripts\\python.exe -m agrosphere_orchestrator.cli autonomous report " + run["run_id"] + " --markdown",
    "conditional_continuation_command": ".\\.venv\\Scripts\\python.exe -m agrosphere_orchestrator.cli autonomous resume " + run["run_id"],
    "continuation_conditions": "Not executed or currently ready. Only after the discovery checkpoint is genuinely resolved and the unchanged run budget/authorization still permits continuation. Do not start a second run or reset budgets.",
    "local_autonomy": "Real controller orchestration, persistence, fail-closed checkpoint and reporting functioned for the one reconciliation step. Agent execution and performance acceptance were not reached or validated.",
    "repository_preservation": preservation,
    "previous_recovery_head": "49cdf041630e91d3ba8d4d06610285aefe7945058dbb4d42b0acacd384eff113",
    "recovery_note": "Fresh discovery persisted in the committed autonomous operation. Existing AEO-1B recovery head retained: conflict stops the controller before its recovery.reconcile call.",
    "native_report_hash": native_hash,
    "native_report_files": native_files,
    "policy_changes": [],
    "source_edits": [],
    "publication": "None; remote writes remain disabled. No PR, merge or deployment.",
    "milestone_3B": "No run started, scope registered, design generated or implementation performed. No M2 GPU prerequisite for backend-only planning recovered, but exact 3B scope and approved roadmap dependencies remain unresolved.",
}
report_path = root / "operator-activation-report.json"
previous = json.loads(report_path.read_text(encoding="utf-8"))
previous["status"] = "BLOCKED_DISCOVERY_CONFLICT"
previous["autonomous_run_id"] = run["run_id"]
previous["execution_mode"] = "local"
previous["latest_controlled_run"] = summary
previous["historical_blockers_before_explicit_start_authorization"] = previous.pop("blockers")
previous["blockers"] = summary["remaining_prerequisites"]
previous["historical_next_action_before_explicit_start_authorization"] = previous.pop("next_authorized_action")
previous["next_authorized_action"] = summary["next_operator_action"]
previous["historical_start_authorization_request"] = previous.pop("requested_operator_authorization")
previous["approval_commands"] = {
    "current_checkpoint": None,
    "reason": summary["checkpoint_approval_explanation"],
    "read_only_report": summary["read_only_operator_command"],
}
report_path.write_text(json.dumps(previous, indent=2) + "\n", encoding="utf-8")
(root / "controlled-first-result.json").write_text(
    json.dumps(summary, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps({
    "run_id": run["run_id"],
    "state": run["state"],
    "repository_preservation_checks": len(preservation),
    "native_report_files_exist": True,
    "summary_sha256": hashlib.sha256((root / "controlled-first-result.json").read_bytes()).hexdigest(),
}, indent=2))
