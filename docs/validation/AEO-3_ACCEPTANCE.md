# AEO-3 acceptance checklist

| Acceptance item | Evidence | Result |
| --- | --- | --- |
| Existing AEO regression tests pass | Full suite: 132 passed, including 116 existing tests | Verified |
| Planner produces a valid dependency graph | Plan idempotence, strict task options, cycle/missing/duplicate checks and PlantUML graph tests | Verified |
| Independent tasks execute concurrently | End-to-end mock transport measures peak active executions of 2 for developer tasks in separate temporary repositories | Verified with mocks |
| Conflicting repository writes are blocked | Exclusive write leases, scheduler admission, expired lease protection, retained legacy single-slot guard | Verified |
| Handoffs preserve artifact references | Generated developer artifact handoff, hash/commit checks, persisted publication and acknowledgment, hashed receiving context | Verified with mocks |
| Unapproved designs block implementation | Missing approval, changed approved artifact, missing plan approval and missing exact execution grant tests | Verified |
| Failing tasks follow bounded retries | Original plus at most three read-only repairs; authentication failures never retry; each attempt receives a new exact grant | Verified with mock human grants |
| Interrupted execution can be reconciled | Confirmed-result recovery without duplicate execution; uncertain outcomes retain leases and block resume | Verified |
| Multi-agent fixture completes end to end | Ten tasks across all nine roles; concurrent developers and reviews; verified artifact handoff; final COMPLETED report | Verified with mocks |
| Documentation and PlantUML diagrams updated | Assessment, operator guide, ADR 0009 and seven successfully rendered editable PlantUML diagrams | Verified |

Detailed command exit codes are in commands.json, individual test results in pytest.xml, and diagram evidence in aeo3-docs.json. [Implementation report](AEO-3_REPORT.md) explains scope, contracts and limitations.

No live Codex concurrency claim is made. The opt-in multi-role live smoke was checked only in its SKIPPED mode. Repair executions preserve the existing human-grant boundary. Uncertain writes require operator reconciliation rather than automatic replay. No AgroSphere business repository was modified by the acceptance fixtures.
