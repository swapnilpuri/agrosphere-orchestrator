# AEO-3 implementation and acceptance report

## Implementation

The existing orchestrator now has versioned execution plans, dependency-driven asynchronous task scheduling, persisted claims and resource leases, structured artifact handoffs, bounded repair eligibility, conservative interruption reconciliation, and consolidated JSON/Markdown reports. Changes are confined to the orchestrator repository. No business repository implementation, push, merge, deployment, or live model execution was performed for this milestone.

The assessment and reuse map is [GAP_ANALYSIS](../aeo-3/GAP_ANALYSIS.md). The operator workflow, settings, contracts, failure behavior and limitations are in the [AEO-3 guide](../aeo-3/README.md).

## Reuse and source structure

Reused MilestoneSpec graph validation, import_plan, RoleRegistry and nine existing roles; AEO-1C scope/design/artifact validation and authenticated approvals; AEO-2 exact execution grants, CodexExecutor, native isolation probes, worktree creation/preservation, process/session reconciliation and structured execution results. No alternate SDK, coding framework, queue, or database was introduced.

New modules:

- src/agrosphere_orchestrator/orchestration_models.py: strict plan, task options, artifact references and failure taxonomy.
- src/agrosphere_orchestrator/orchestration_store.py: transactional coordination and immutable evidence.
- src/agrosphere_orchestrator/orchestration.py: planner, scheduler, handoffs, repair decisions, recovery and reporting.
- migrations/versions/0005_orchestration.py: additive schema and immutable history triggers.
- tests/test_orchestration.py: deterministic acceptance coverage using temporary Git repositories.
- scripts/verify_aeo3_docs.py and scripts/codex_multi_role_smoke.py: local diagram verification and explicit opt-in live transport smoke.

Existing execution.py admits concurrent work only through matching scheduler claims; direct AEO-2 execution retains the atomic single-slot guard. execution_context.py adds verified handoff contents to the existing redacted context digest. CLI and central Settings expose the new workflow and limits.

## Schema and audit

Migration 0005 adds orchestration_plans (immutable revisions), orchestration_controls (active plan and pause state), task_claims (owner/execution/expiry/reconciliation), resource_leases (resource/mode/owner/expiry), and orchestration_evidence (immutable plan decisions, batches, handoffs, results, repair decisions and scheduler events). Existing task dependencies and assignments remain in the validated plan rather than being duplicated in a second task registry. Task/milestone foreign keys retain project association. Every mutation and audit event shares a transaction; immutable evidence and revisions reject UPDATE/DELETE through SQLite triggers.

## Workflow and concurrency

A Program Manager and Project Manager review an already approved milestone through existing typed role execution contracts. Scheduling options project the exact approved task graph; changing milestone decomposition requires the established design revision lifecycle. The deterministic scheduler validates dependencies and approval references, sorts by priority and ID, and claims eligible tasks/resources using BEGIN IMMEDIATE. It executes selected independent requests using asyncio through the existing AEO-2 adapter. Only persisted verified prerequisites allow downstream tasks to run.

The fixture spans Program Manager, Project Manager, Business Analyst, Architect, two Developer tasks, QA, Security, DevOps and Technical Writer. Developer tasks operate concurrently in separate temporary repository worktrees. QA and Security reviews form another parallel wave. A generated developer artifact is hashed, persisted in a handoff, rechecked, inserted into receiving context and acknowledged. Final evidence must account for every required task before reporting COMPLETED.

Default limits are two global executions, two per agent role, one per repository and three repair attempts. Repository writes are exclusive; explicit shared resources cover contracts, migration namespaces, build outputs and test environments. Sorted all-or-nothing lease acquisition prevents partial lock ownership and deadlock. Expired leases are never automatically stolen.

## Handoffs, failures and recovery

Handoffs persist source/destination tasks and roles, milestone, context summary, artifact paths/hashes/source commits, completion criteria, validation evidence, known issues and status. Artifact producer references must be explicit dependency edges with expected outputs. Producer files resolve in preserved verified worktrees. External inputs match confirmed repository HEADs. Missing, modified, unapproved or unverified inputs block use.

Original results are preserved. Repair records correlate a new request with the prior execution and record the bounded repair budget. Security/approval failures do not retry. Eligible read-only repairs are limited to three after the original attempt; every execution still needs a fresh exact human grant. Write repairs require explicit review rather than automatic replay.

pause stops new assignments and requests cancellation. resume runs the existing process-identity reconciler first. Confirmed persisted results can release claims without repeating execution. Live or unverifiable processes retain ownership. Uncertain outcomes enter reconciliation_required and retain leases, requiring operator investigation of preserved evidence. No exactly-once or distributed-execution guarantee is claimed.

## CLI

~~~powershell
aeo milestone plan AGRO-M3C --options task-options.json
aeo milestone graph AGRO-M3C --plantuml
aeo milestone approve-plan AGRO-M3C
aeo milestone prepare AGRO-M3C
aeo agent approve --execution EXECUTION-UUID
aeo milestone execute AGRO-M3C
aeo milestone status AGRO-M3C
aeo milestone pause AGRO-M3C
aeo milestone reconcile AGRO-M3C
aeo milestone resume AGRO-M3C
aeo milestone report AGRO-M3C --markdown
aeo tasks list --milestone AGRO-M3C
aeo tasks inspect TASK-UUID
aeo agents workload
~~~

The CLI also exposes structured handoff publication and deviation reporting. Deviation reporting pauses the milestone and records impact; resumption requires a reconciled approved plan and valid approved design. No command implicitly grants approval.

## Verification

The final full suite passed **132 tests** (116 existing regressions plus 16 AEO-3 tests), with zero failures, errors or skips, in 198.950 seconds. The required scripts/validate.py runner returned exit 0; all 17 validation commands returned exit 0, including lint, formatting, pip dependency checks, Alembic upgrade/schema comparison, CLI checks and AEO-3 diagram rendering. See commands.json for exact argv, exit codes and complete command output; pytest.xml for individual tests; aeo3-docs.json for diagram rendering results.

The initial unchanged regression collection passed all 116 existing tests (exit 0). An intermediate full run exposed the direct-execution slot compatibility test; that guard was restored and its focused test passed. Active cancellation testing also exposed an expired ORM instance outside its transaction; pause now carries stable execution identifiers across the transaction boundary.

All seven new PlantUML sources have rendered successfully with the existing local PlantUML jar. Historical approved diagram revisions were preserved. ADR 0009 records the coordination decision.

## Live verification and limitations

No live Codex calls were run. The separate multi-role smoke entry point was executed without --live and returned exit 0 with an explicit SKIPPED result. The new orchestration fixture uses deterministic mock transports, mock validation commands and mock isolation probes. Its concurrency result proves scheduler orchestration, not live Codex concurrency or native sandbox effectiveness.

Planning uses tasks already enumerated in the approved milestone; it does not autonomously expand or approve scope. Repair eligibility is bounded but actual repair executions require fresh human grants. Uncertain writes remain blocked for human reconciliation; automatic acceptance or replay is intentionally unavailable. Single-host SQLite coordination and administrator-declared shared resources remain operational assumptions. Distributed scheduling, automatic delivery approval, deployment and merging remain out of scope.

AEO-4 recommendations: separately design human-approved repair authorization envelopes, richer evidence-based reconciliation tooling, and live scheduler acceptance with authenticated fixture-only execution. Do not begin AEO-4 automatically.
