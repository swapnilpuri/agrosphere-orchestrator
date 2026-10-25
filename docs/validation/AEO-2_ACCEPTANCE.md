# AEO-2 acceptance check

9 of 10 verified (90%), including deterministic fixture checks. Live integration remains pending.

Executed: 2026-10-25T04:27:30.344864+00:00. Full suite: 116 passed in 132.693 seconds. All 16 validation commands returned exit 0.

| Check | Status | Evidence |
| --- | --- | --- |
| Codex runtime health check succeeds | verified | Native CLI 0.164.0, authenticated, exec supported; codex-runtime.json |
| All nine agent roles resolve correctly | verified | All nine actual CLI describe calls returned the expected role and schemas; aeo2-roles.json |
| A test agent executes a permitted task | verified_fixture | test_orchestrator_allowlisted_validation_marks_task_accepted; simulated Codex transport with temporary Git worktree |
| Execution result is saved in persistent storage | verified_fixture | test_success_persists_session_but_model_claim_is_not_validation; SQLite backup reopened independently |
| Repository and worktree restrictions are enforced | verified | Native canaries for three modes; temporary Git worktree/source-preservation tests |
| Unauthorized operations are rejected | verified | Grant bypass, protected scope, unauthorized repository, expiry, disabled policy and validator allowlist tests |
| An interrupted execution can be reconciled | verified_fixture | test_recovery_marks_orphan_interrupted_without_success_or_replay; persisted INTERRUPTED record and new unapproved recovery request |
| Existing AEO-1/1B/1C regression tests pass | verified | Full suite: 116 tests, zero failures/errors; all 16 validation commands exit 0 |
| Architecture and execution diagrams are generated | verified | Five PlantUML SVGs rendered and XML-validated, plus design lifecycle SVG; immutable sources/hashes preserved |
| Optional live smoke test is run and verified | blocked | Not run: interactive Windows credential verification required; configured execution approver count is zero |

Fixture checks use a simulated Codex transport and authenticated-human test double; they do not prove a live model execution or actual Windows credential authentication. SQLite fixture backups are retained under `.aeo/acceptance-evidence`, separate from the application database.

The native sandbox probes use the actual standalone CLI and confirm denied network access, outside reads/writes, out-of-scope writes and the correct in-scope behavior in all three execution modes.

Diagram output: [render evidence](aeo2-docs.json). PlantUML 1.2026.9 was downloaded from the [official distribution](https://plantuml.com/en/download) into ignored local tooling; no immutable documentation revision was changed and no design approval was granted.

Live smoke prerequisite: [AGENTS.md](../../AGENTS.md) requires "Live model smoke tests require explicit opt-in and human authentication". This request supplies opt-in. No execution approvers are configured, and an interactive human must authenticate using their Windows password locally; do not submit that password in chat. No live invocation or quota use occurred.

Run the live script from the orchestrator directory after an authorized execution approver SID has been configured:

```powershell
$env:AEO_CODEX_EXECUTABLE = "$env:LOCALAPPDATA\Programs\OpenAI\Codexin\codex.exe"
.\.venv\Scripts\python.exe scripts\codex_live_smoke.py --live
```

This is a transport-only temporary-fixture smoke. It does not grant application design approval or enable production execution. Its generated `live-result.json` must be checked before marking the final item verified.
