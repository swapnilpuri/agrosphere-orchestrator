"""Consolidate actual pre-approval evidence without changing approvals or runtime state."""
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
root = Path.cwd()
base = root / "docs/milestones/AEO-6"
validation = base / "evidence/baseline-validation"
runner = json.loads((validation / "runner.json").read_text(encoding="utf-8"))
commands = json.loads((validation / "commands.json").read_text(encoding="utf-8"))
def cases(p):
    tree = ET.parse(p).getroot()
    return tree.find("testsuite"), {(c.attrib.get("classname"), c.attrib["name"]) for c in tree.iter("testcase")}
suite, current = cases(validation / "pytest.xml")
_, accepted = cases(root / "docs/milestones/AEO-5/evidence/aeo5r-accepted-validation/pytest.xml")
_, original = cases(root / "docs/milestones/AEO-5/evidence/current-regression.xml")
summary = {"generated_at": datetime.now(UTC).isoformat(), "phase": "AEO-6A", "aeo6_locally_accepted": False, "checkpoint": "AWAITING_REQUIREMENTS_APPROVAL", "scope_id": "48fd59274969f5abf0623159f5d15dba1c00111a80a67a654184ee58be6a2143", "validation_exit_code": runner["exit_code"], "pytest": suite.attrib, "original_baseline_count": len(original), "original_ids_preserved": original <= current, "accepted_aeo5_count": len(accepted), "accepted_aeo5_ids_preserved": accepted <= current, "missing_test_ids": sorted(accepted-current), "command_count": len(commands["commands"]), "failed_commands": [{"argv": c["argv"], "exit_code": c["exit_code"]} for c in commands["commands"] if c["exit_code"]], "diagram_count": 9, "context_hashes_verified": 28, "source_modules_changed_for_aeo6": [], "new_aeo6_tests": 0, "aeo6_controller_implemented": False, "real_codex_execution": False, "aeo6_simulated_end_to_end": False, "live_github_verified": False, "formal_completion": False}
(base / "evidence/preparation-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
results = "\n".join("| " + " ".join(c["argv"][1:]) + " | " + str(c["exit_code"]) + " |" for c in commands["commands"])
(base / "10-test-results.md").write_text(f"# Actual AEO-6A baseline verification\n\nPytest: {suite.attrib['tests']} tests, {suite.attrib['failures']} failures, {suite.attrib['errors']} errors, {suite.attrib['skipped']} skipped, {suite.attrib['time']} seconds. All {len(accepted)} accepted AEO-5 IDs preserved: {accepted <= current}. Original {len(original)} IDs preserved: {original <= current}. No new AEO-6 controller tests exist before approval.\n\nValidator exit: {runner['exit_code']}. Tests and migrations used a disposable SQLite backup and temporary Git repositories. Exact stdout/stderr and argv are retained in evidence/baseline-validation/commands.json; runner.json and pytest.xml accompany it.\n\n| Executed command arguments | Exit code |\n|---|---|\n{results}\n\nNine draft diagrams passed existing LocalPlantUML safety, syntax and rendering checks. Initial missing jar configuration and default internal-manifest mismatch were resolved with process-local overrides; failed attempts remain in evidence/preparation-attempts.json. Checkpoint verification confirms 28 context hashes, zero AEO-6 decisions and an enforced requirements approval gate. Formal design validation cannot run until requirements approval permits revision generation. No application test/build, real Codex, AEO-6 end-to-end simulation or live GitHub validation was executed.\n", encoding="utf-8")
report = fr"""# AEO-6 acceptance report — pre-implementation checkpoint

Status: **NOT LOCALLY ACCEPTED — AWAITING AUTHENTICATED REQUIREMENTS APPROVAL**.
This is the AEO-6A progress/acceptance boundary report, not a completed implementation acceptance claim.

## Verified baseline and work completed

Actual Settings resolve C:/Projects/agrosphere, agrosphere-orchestrator and its existing aeo.db. Runtime schema is 0007, with 29 existing tables including Alembic bookkeeping. AEO-5 remains IMPLEMENTING; its local acceptance does not complete runtime delivery. All 20 files in its accepted source inventory match their recorded SHA-256 values. There are no runtime delivery runs/operations or execution grants/governance records, and remote writes are disabled.

Prepared capability matrix, architecture, lifecycle, durable recovery, governance, implementation and acceptance documents; nine PlantUML sources and SVGs; exact operator/approval guides; complete immutable requirements input and runtime review export. Registered 12 requirements, six proposed tasks and 28 context hashes under scope 48fd59274969f5abf0623159f5d15dba1c00111a80a67a654184ee58be6a2143. No approval was fabricated.

## Required delivery inventory

| Requested item | Actual status at this checkpoint |
|---|---|
| Code modules created/modified | No AEO-6 production source changes. Evidence helpers only under docs/milestones/AEO-6/evidence. Existing dirty AEO-5 work preserved. |
| Existing modules reused | recovery/discovery, configuration/Settings, design registration/context/hash/render/status/approval guard; complete future interface matrix in 01-existing-capability-assessment.md. |
| Database schema changes | None. Existing CLI added AEO-6 DesignCase/DesignScope and transactional registration audit only; validator migration uses disposable backup. |
| Registered design approval evidence | Requirements scope registered; zero AEO-6 decisions, no formal design revision yet. Existing guard rejects generation without authenticated requirements approval. |
| New CLI commands | None before design approval. Existing exact commands in 08-cli-operation-guide.md. |
| New tests/counts | Zero AEO-6 implementation tests; nine diagrams rendered and 28 context hashes verified. |
| Existing regression | {suite.attrib['tests']} tests, {suite.attrib['failures']} failures, {suite.attrib['errors']} errors, {suite.attrib['skipped']} skipped; {len(commands['commands'])} standard checks; validator exit {runner['exit_code']}. Original {len(original)} and accepted {len(accepted)} test IDs preserved: {original <= current and accepted <= current}. |
| End-to-end outcomes | Existing AEO-5 regression includes mocked delivery tests; AEO-6 end-to-end NOT RUN. |
| Actual Codex execution | NOT RUN; no model quota consumed by preparation. |
| Approval/security | Requirements approval gate verified; no approval decision inserted or authentication simulated against runtime. Publication remains separately gated and disabled. |
| Durable recovery | Existing recovery discovered read-only; future AEO-6 16-case fault-injection contract documented, NOT TESTED. |
| Repo/Git safety | 12 confirmed application roots inspected clean; read-only discovery; no application writes, commits, pushes, PRs, merges or deployments. |
| Local acceptance recommendation | Do not accept AEO-6 yet; implement and verify 6B–6G after valid requirements and technical-design approval. |
| Remaining live/runtime checks | Formal design generation/validation/approval; controller implementation/tests/simulation; separately authorized real local Codex proof and any live publishing. |
| Next operator action | Review this scope and run existing interactive approve-requirements command below. |

## Recovered application milestone summary

Manifest-bound discovery finds 1A/1B/1C/2/3A PARTIAL, medium confidence; 3B UNVERIFIED with no recovered implementation/test evidence. Operations 3A has 30 source files and five test paths, with architecture history claiming 3A completion documents; those claims do not prove current acceptance. All verified acceptance-criteria lists are empty. Existing recovery suggests 1A acceptance reconciliation and 3B as a development review candidate, not an eligible authorized execution. No real application work starts.

Raw recursive discovery included nested orchestrator test fixtures. This is recorded as an integration defect/risk. Use evidence/application-discovery.json and application-summary.json, which bind the 12 confirmed manifest application roots. Raw evidence/fresh-discovery.json is diagnostic only and was not reconciled into the authoritative runtime recovery head.

## Approval boundary and exact next action

The user's specification section 5 requires stopping at authenticated requirements/design checkpoints. Existing design.generate_design calls require_approval for the exact requirements scope before generation. Verification returned: Authorized human requirements approval is required. The configured human approver must authenticate in an interactive Windows terminal; chat permission is not a formal decision.

~~~powershell
Set-Location C:\Projects\agrosphere\agrosphere-orchestrator
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-requirements AEO-6
~~~

After the authenticated decision, resume from the existing persisted scope; generate/validate the formal revision with the installed renderer and internal manifest, then obtain the separate exact design approval. See 08-cli-operation-guide.md and 09-approval-and-recovery-guide.md. No working autonomous dry-run/simulation/local command exists yet; those command patterns must be implemented and verified after design approval.

Evidence: preparation-summary.json, checkpoint-verification.json, aeo5-source-verification.json, baseline-state.json, application-summary.json and diagram-validation.json under evidence; complete standard command results under evidence/baseline-validation. Unit/integration regression was executed; AEO-6 simulation, real Codex, live GitHub and formal completion are pending, not claimed.
"""
(base / "AEO-6_ACCEPTANCE_REPORT.md").write_text(report, encoding="utf-8")
(base / "END_TO_END_STATUS.md").write_text("# AEO-6 end-to-end status\n\nNOT RUN. Requirements and technical-design approval are prerequisites to controller implementation. Existing AEO-5 mocked tests cannot establish AEO-6 execution or readiness. Planned isolated three-repository scenario and all 16 recovery cases are specified in 07-acceptance-criteria.md and 04-state-and-recovery-model.md. No real Codex, application execution or live GitHub operation occurred.\n", encoding="utf-8")
(base / "IMPLEMENTATION_INVENTORY.json").write_text(json.dumps({"phase": "AEO-6A", "production_modules_created": [], "production_modules_modified": [], "schema_changes": [], "new_cli_commands": [], "new_controller_tests": [], "proposed_modules": ["autonomous.py", "autonomous_models.py", "autonomous_store.py", "autonomous_cli.py"], "implemented": False}, indent=2), encoding="utf-8")
manifest = []
for p in sorted(base.rglob("*")):
    if p.is_file() and p.name != "ARTIFACT_MANIFEST.json":
        manifest.append({"repository": "agrosphere-orchestrator", "path": p.relative_to(root).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
(base / "ARTIFACT_MANIFEST.json").write_text(json.dumps({"artifacts": manifest}, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
