# AEO-6 local implementation acceptance

Status: **LOCALLY ACCEPTED WITH EXPLICIT LIVE VALIDATION LIMITS**. Runtime AEO-6 remains **IMPLEMENTING**; formal milestone completion is false. No real application milestone was launched.

## Actual implementation inventory

Six new modules implement strict run/request/roadmap contracts, durable intent/event persistence, deterministic bounded control, existing-service adapters, the autonomous CLI and isolated simulation. Additive migration 0008 creates autonomous_runs, autonomous_operations and autonomous_events. Narrow existing-service changes add atomic scheduler dispatch reservations/batch caps and per-task AEO-4 repair reservations. Settings, CLI registration, Alembic metadata and standard schema exports are updated. Eight new test modules cover unit, integration, scheduler, security, CLI, quality, recovery and upgrade behavior. Exact 22-file inventory and SHA-256 values are in IMPLEMENTATION_INVENTORY.json and evidence/implementation-source-manifest.json. Existing uncommitted AEO-5 work was retained.

The controller reuses AEO-1 domain/plan persistence; AEO-1B repository collection, recovered milestones and snapshot reconciliation; AEO-1C scope, immutable generation/export/validation and exact approval guards; AEO-2 context/execution/grants/worktree isolation; AEO-3 plan/DAG/claims/leases/handoffs; AEO-4 independent policy/readiness/validation/remediation; AEO-5 immutable delivery planning, publication guards and provider reconciliation. It introduces no alternate model launcher, scheduler, GitHub adapter, queue, service or UI.

## Registered approval and runtime state

Requirements scope: 48fd59274969f5abf0623159f5d15dba1c00111a80a67a654184ee58be6a2143

Requirements decision: c003c8e6-7477-4c5d-a226-194a5995539e

Design revision: e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe

Design bundle: 0f55432b8e4c4508b27795a92a45537ea63b6e8ae94a001a39250adf2d6d4126

Design validation: e3c6d54b3da94cbd8c5a2805838e5915e4128050bb7021017a7c393d62879bab

Authenticated design decision: 506b66d5-2e8c-423e-9cf6-814cef4aadb5

Current authorized identity, transactional human-decision audit, all 22 immutable approved artifacts and exact imported six-task plan were independently verified. Requirements input is unchanged. Approved context was checked before entering IMPLEMENTING; authorized implementation source edits are recorded separately, following the existing design guard. The requirements and approved design were not silently rewritten.

Runtime schema upgraded 0007 -> 0008 only after the full validator passed. A backup is retained under .aeo/backups; evidence/runtime-migration-0008.json identifies it. All records in every pre-existing table were compared before/after and preserved. Table count increased 29 -> 32. No runtime autonomous run/operation/event records were fabricated. The six manually implemented plan tasks were not falsely marked as executed by Codex. AEO-5 remains IMPLEMENTING and its outstanding runtime delivery is separate.

## Actual validation results

Standard validator: **exit 0; 18/18 checks passed**. Pytest: **354 tests; zero failures, errors or skips**, 677.405 seconds. All 275 accepted AEO-5 IDs and all 293 design-checkpoint IDs are preserved; 61 new cases were added after the design checkpoint. The original 163 IDs remain preserved through that accepted baseline. Tests/migration checks ran on a disposable runtime backup and independent temporary Git repositories.

Evidence: evidence/implementation-validation/commands.json, pytest.xml and runner.json. Final source hashes match the inventory captured at the start of that run. The earlier interrupted full run is explicitly recorded in implementation-validation-interrupted.json and is not claimed as passing.

Safety checks include atomic dispatch rollback and concurrency caps through the real scheduler, per-task repair transaction rollback through AEO-4, immutable run/history and report integrity, duplicate-start serialization, retained elapsed/attempt/resource counters, unknown-cost fail-closed behavior, exact timeout bounds, manifest-root isolation, approved-roadmap dependencies, fixture authentication refusing runtime DBs, read-only CLI defaults and additive upgrade preservation.

Recovery tests retain ownership and require independently verified adoption for all 16 documented categories; additional injection covers after-intent, before-dispatch, after-observation, before-commit and after-commit faults. Existing AEO-2–AEO-5 tests verify child process/session, worktree, publication response loss, CI/SHA/review changes and authorization failures. The parent delegates child recovery; no blind write replay is introduced. See IMPLEMENTATION_NOTES.md for evidence scope.

## End-to-end simulated result

The supported simulation CLI exited 0 and exported evidence/simulation-final/simulation-report.json and .md. Three independent temporary Git repositories and a temporary SQLite DB exercised real requirements/design/plan/grant lifecycle services, the real scheduler, an isolated write worktree, all mandatory quality/security gate types for every impacted repository, one failed QA result, one bounded read-only remediation, revalidation, separate fixture-authenticated delivery approval and action grants, three mocked pushes/PRs and controller reconstruction across checkpoints. The run ended REPORTED with formal completion false. Four simulated model calls, one repair and three simulated PRs were observed. Long Windows path cleanup was exercised and fixed without relaxing existing worktree safeguards.

Model, scanner, PlantUML renderer and GitHub ports are explicitly mocked in this simulation. Actual AEO-6 design PlantUML sources/SVGs were rendered and validated separately at the approved design checkpoint. Simulation evidence is not live model/scanner/provider evidence.

## Repository safety and recovered application progress

The actual supported dry-run exited 0 and inspected exactly 12 confirmed application roots. HEAD, Git status and file fingerprints match the prior checkpoint for all 12 roots. No application commits, pushes, PRs, merges or deployments occurred. Remote writes remain disabled in runtime.

1A, 1B, 1C, 2 and 3A are PARTIAL with medium confidence and no verified acceptance criteria. 3B is UNVERIFIED with low confidence. Conflicting completion/not-started historical claims occur for 1B, 1C and 2. Recovery recommends 1A acceptance reconciliation; 3B is only a development review candidate, not an eligible authorized execution. The controller blocks conflicting/unknown dependencies and requires a roadmap bound to approved context before application execution.

## New commands and exact next actions

Commands: autonomous plan/start/status/pause/resume/recover/report/validate/simulate. Run from C:/Projects/agrosphere/agrosphere-orchestrator:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous plan --milestone 3B
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous simulate --output-directory docs/milestones/AEO-6/evidence/operator-simulation
~~~

Supported future local-execution pattern, requiring a separate explicit application-run instruction and all exact existing grants:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous start --milestone <approved-milestone> --mode local --request <reviewed-request.json>
~~~

See 08-cli-operation-guide.md for request schemas, persisted run inspection, explicit continuation, atomic report export and authenticated checkpoint commands; see 09-approval-and-recovery-guide.md for recovery and current approval verification.

## Remaining live/runtime validation

Actual Codex smoke/proof-of-concept execution: **NOT RUN; separate explicit opt-in and authentication required**. Live GitHub publication/CI/review checks: **NOT RUN; separately scoped grants and configuration required**. Real application autonomous execution: **NOT RUN; separate explicit instruction after this acceptance required**. No automated merge, deployment or application advancement is implemented. Formal completion and AEO-5 runtime delivery remain pending their actual existing workflow evidence and approvals.

Local acceptance covers implemented unit/integration/simulated behavior. It does not claim production readiness or formal runtime delivery. No additional requirements/design approval is requested for the unchanged AEO-6 scope.
