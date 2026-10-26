# AEO-6: overview (design)

Scope: 48fd59274969f5abf0623159f5d15dba1c00111a80a67a654184ee58be6a2143
Requirements: AEO6-DISCOVERY, AEO6-CONTROLLER, AEO6-DESIGN, AEO6-APPROVAL, AEO6-DAG, AEO6-QUALITY, AEO6-DELIVERY, AEO6-DURABLE, AEO6-BUDGET, AEO6-CLI, AEO6-EVIDENCE, AEO6-SAFETY

## Milestone overview

AEO-6 Autonomous Milestone Execution; internal development only.

## What will be built

# AEO-6 architecture proposal

## Business context and objective

AgroSphere engineering currently requires an operator to connect recovery, approved designs, execution, independent quality and delivery. The controller will connect those services in bounded, auditable runs while retaining the readable milestone explanations and diagrams used during manual development. Implementation is internal to agrosphere-orchestrator. No application capability, external API, event schema, UI or infrastructure service is added.

## Components and dependency direction

AutonomousMilestoneController is an application service in proposed autonomous.py. autonomous_models.py contains strict run modes, transition/checkpoint models, operation identities and limits; autonomous_store.py contains durable projections and append-only events. autonomous_cli.py exposes the Typer group. Names are proposed until approved. The controller depends on existing recovery, design, orchestration, quality and delivery services; those services do not depend on controller decisions for authorization. Use injected service boundaries for tests; production uses the existing Codex/GitHub implementations.

Selection is a deterministic function of approved roadmap/dependencies, recovered evidence and persisted task/design/delivery state. The existing recovery.next_milestone numeric heuristic may suggest a review candidate; it cannot authorize work. Unknown or conflicting evidence blocks. Explicit milestone selection does not bypass eligibility.

## Operation protocol

Before external I/O, atomically claim a run operation, reserve hard budgets, persist exact input identities and append audit evidence. Release the database transaction for service calls. Persist result and evidence references in another transaction only after independent observation. Unique run/step/scope operation identities prevent duplicate dispatch. Concurrent resume calls serialize through the existing transaction/lease mechanism. Source services retain their existing task and delivery intent records.

A completed child operation with an interrupted parent result write is adopted only after verifying child identity and actual outcomes. Missing or uncertain outcomes enter RECOVERY_REQUIRED; they are never silently replayed. No network or Codex process runs while holding a SQLite write transaction.

## Data and artifact ownership

Proposed additive migration 0008 adds AutonomousRun, AutonomousOperation and AutonomousEvent; reuse existing Base/engine and audit in the configured database. A run references existing milestone/design/task/execution/quality/delivery identifiers. Store small manifests, hashes, limits, reservations, usage and transition evidence; large artifacts remain on disk. Preserve existing tables, audit history and independent service records. Upgrade tests populate 0007 and prove preservation.

Internal AEO-6 design uses the existing internal-orchestrator scope with only orchestrator-owned artifacts. Future application cross-service narratives/diagrams belong in discovered agrosphere-architecture, contracts in agrosphere-contracts, and service designs in the relevant service repository according to existing design_policy. Revisions include hashes and never overwrite approved artifacts.

## Milestone explanation generation

Build complete business context, objectives, scope/features, functional/nonfunctional requirements, architectural dependencies, proposed components/interactions, database and API/event impact, security, testing, phases, risks/assumptions and acceptance criteria into typed approved narratives. Persist C4 and PlantUML sources/rendered outputs with requirement links. Missing authoritative requirements cause a proposed review scope, never invented business acceptance. Use the existing documentation-role adapter, renderer and reviewer. No source implementation before requirements and validated design gates pass.

## Architectural decisions

ADR-6-01: one deterministic application controller; existing scheduler remains sole task dispatcher.
ADR-6-02: same SQLite database, additive projections, transactional audit and durable child references; no queue/daemon/web application.
ADR-6-03: explicit CLI continuation after approvals; no continuous polling infrastructure.
ADR-6-04: default dry-run, one milestone, fail-closed governance; local mode alone grants nothing.
ADR-6-05: simulated services run in temporary independent repositories/databases; never promote simulations to live evidence.

## Risks and trade-offs

Existing interfaces cover most services but not an atomic run-wide budget across scheduler batches. Add a narrow reservation seam under the approved design, retaining scheduler semantics and tests. Exact model cost may be unknown; unknown usage is reported and a configured monetary cap that cannot be enforced blocks execution. Local administrators remain trusted; hash manifests are integrity evidence, not tamper-proof remote storage.

## Why it is needed

Preserve milestone explanations and diagrams while making existing approved engineering workflows resumable and auditable.

## Platform fit

Single AgroSphere project using existing adapters, state, policies and infrastructure.

## Component responsibilities

# Autonomous lifecycle proposal

1. Load run or construct a read-only plan. Discover actual repositories and reconcile child task/delivery operations before new work.
2. Select an eligible milestone from approved scope and dependencies; support proposed, partial, blocked, completed, interrupted and pending-delivery states. Completed tasks are adopted only with verified evidence, never restarted.
3. Prepare requirement narratives and diagrams in correct repository ownership. Register exact requirements; pause for authenticated requirements decision when missing.
4. Generate immutable design revision using existing design services; validate hashes, repository context, completeness and independent architecture review. Persist design checkpoint and stop until approved.
5. Produce DAG using orchestration.propose_plan and existing roles. Preserve plan approval, activated quality policy, exact per-execution grants and worktree isolation; missing gates are separate checkpoints.
6. Dispatch independent tasks only through TaskScheduler. Concurrency is the minimum of run limits and existing repository/agent scheduler limits. Every structured output references task, role, repository, inputs, actions, artifacts, file/commit identities, tests, blockers and next action; validate before transition.
7. Independently verify through AEO-4. Classify failures and prepare only policy-permitted remediation. Reserve repair budget first; default at most three repairs. Any changed design or write scope returns to its proper approval gate.
8. Build AEO-5 manifest from verified task outputs and exact repository identities. Prepare publication review scope. Require quality/security evidence and separate privileged approval; remote-write configuration remains off unless separately authorized.
9. Observe CI, required reviews, dependencies and external acceptance with bounded delivery polling. Retain implementation complete, local quality accepted, ready for publication, PR published, awaiting CI/review, ready for authorized merge, externally accepted and formal completion as distinct facts. Never merge or deploy.
10. Generate evidence-backed JSON/Markdown report. Advance only after formally verified completion and an explicit advance authorization within remaining milestone budget. Default one milestone; ambiguity blocks.

LLM outputs are untrusted reasoning/artifacts, never governance decisions. Stop-on-gate is mandatory for missing authority. Resume rechecks immutable scope, current allowlists, decisions, expiry/revocation, policy, artifacts and repository facts; valid unchanged approvals are reused.

## Implementation sequence

# AEO-6 implementation plan awaiting approval

| Phase | Proposed implementation | Dependencies and verification |
|---|---|---|
| 6A | Existing interface inventory, fresh recovery, baseline validation, draft narratives and nine diagrams, requirement registration | Stop at requirements approval; then existing generate/validate/design approval |
| 6B | autonomous_models.py, autonomous_store.py, additive 0008, autonomous.py deterministic lifecycle | Unit tests for selection, transitions, idempotency, transaction rollback and migration preservation |
| 6C | Existing discovery/design preparation adapters and checkpoint continuation | Complete narratives/ownership, scope invalidation, repeated approval reuse, restart tests |
| 6D | Existing DAG/Codex integration; narrow scheduler budget reservation seam; structured handoffs | Existing worktree/lease guards, concurrency budget races, no duplicate/replayed execution |
| 6E | Existing independent QA/security/remediation and AEO-5 manifest/observation adapter | Missing/failing gates block; exact publication authority; bounded repairs/polling |
| 6F | autonomous_cli.py and realistic three-repository simulation; fault injection at all 16 boundaries | Authenticated fixture approval, failed gate/repair/revalidation, delivery response loss/restart, external CI changes |
| 6G | Safe isolated proof of concept and acceptance package | Actual Codex requires separate explicit operator authorization; no live PR without separate grant |

Central Settings additions will cap milestones (default 1), tasks, active tasks, concurrency, Codex invocations, attempts, repairs (default 3 bounded by current policy), duration, estimated resource/model budget and delivery polling. All must be positive/finite where applicable. Missing cost telemetry is unknown, never zero; monetary enforcement unavailable means block a monetary-capped execution. Parent pre-dispatch reservations cover scheduler batches and concurrent resumes.

Proposed CLI group: autonomous plan/start/status/pause/resume/recover/report/validate. Plan/status read-only; dry-run is default; simulation exclusively temporary fixture roots/databases; local/controlled-delivery require existing authority. Explicit milestone and eligible selection, limits, run ID, JSON/Markdown output and stop-on-gate are supported. No command exists yet; do not present these proposals as executable commands.

Do not import this proposed task DAG for execution before the design gate. Preserve baseline test IDs and all existing work. Add meaningful unit/integration/security/recovery tests; run scripts/validate.py from .venv using a disposable runtime backup and isolated Git fixtures. Final report must separate local implementation acceptance from runtime/formal completion and list exact modules, migrations, commands, test evidence, limitations and next operator action.

## Expected outcomes

# AEO-6 acceptance criteria and test plan

This is a planned verification contract, not passed acceptance.

1. Preserve every existing AEO-1 through AEO-5 test ID (275-test accepted baseline, including original 163). Require full standard validation with actual exit codes; migration tests preserve all populated 0007 tables and audit history.
2. Demonstrate implemented deterministic controller and real repository/history reconciliation; no milestone inferred complete from directory/document existence. Recovered 3A/3B remains a review candidate until dependencies, acceptance and authority are proved.
3. Generate full readable explanations and nine appropriate design views using existing immutable revision workflow. Missing requirements/design approval blocks; valid unchanged approval resumes without new prompts; changed content/identity/policy blocks.
4. Existing scheduler and Codex adapter execute structured task outputs with existing repository/worktree isolation. Independent tasks can overlap only within DAG, agent/repository limits and exact grants. Verify conflicts, duplicate resume calls and uncertain child outcomes.
5. Independent AEO-4 QA/security/acceptance evidence gates task and delivery progress. Fail once, perform one permitted remediation, independently revalidate. Default max three repairs; write recovery still needs exact authorization; quality policy never weakened.
6. Reuse AEO-5 manifests/provider/persistence. Require disabled remote writes by default, exact publication scope, current-SHA checks and genuine human review. Tests prohibit force push, protected writes, duplicate PRs, automatic merge/deploy and agent self-approval.
7. Enforce all hard budgets before dispatch, including parallel agents, retries, polling and resumed runs. Unknown token/cost values remain unknown. Exhaustion persists a resumable paused state and clear reason.
8. Inject all 16 interruption scenarios listed in 04-state-and-recovery-model.md. Reconcile actual child/Git/provider state before replay; retain prior/partial artifacts, claims, history and counts.
9. Use at least three independent temporary Git repositories and a temporary database for full simulation: discovery -> draft -> validate -> approval checkpoint -> fixture-authenticated approval -> resume -> DAG -> mocked agents -> failed QA -> one repair -> pass -> delivery manifest -> publication gate -> mocked publication -> CI/review reconciliation -> report -> restart. Assert formally_completed remains false without separate policy-supported evidence.
10. Default plan/status and simulation preserve real application Git status, HEAD, worktrees and files. No real application milestone starts during AEO-6 verification. No live Codex, GitHub, model quota or production-readiness claim is inferred from mocks.
11. Reports expose run/milestone/state, stages, active agents, dependencies/checkpoints, artifacts/hashes, approvals, repo/commit identities, quality/security/delivery, recovery, usage/unknowns and next permitted action. Final acceptance contains all 15 requested inventory/evidence fields.
12. Check Windows paths, path-length failures, PowerShell CLI invocation and all existing error/isolation safeguards. Produce JSON and Markdown evidence with actual return codes.

Required new suites after approval: test_autonomous (transition/selection/budget), test_autonomous_integration (existing-service wiring), test_autonomous_recovery (16 interruption boundaries), test_autonomous_security (negative authority/mutation cases), test_autonomous_cli (read-only/default modes), test_autonomous_upgrade and isolated three-repository end-to-end simulation. Until run, each is NOT TESTED.

## User-facing documentation

CLI operation, autonomous lifecycle, approval/recovery guides, evidence and final acceptance. No Control Center UI.

## Verified context references

- agrosphere-orchestrator/src/agrosphere_orchestrator/design.py sha256=1330049444195c4f2ca64cc7f0f28e76a386251200ffb05104f374ddcdfe5900 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/design_models.py sha256=3adb56172c5692902c4631437fc72e1851a026595b26e91e9ac15ff441c619f4 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/design_policy.py sha256=c404512136f75955cdb8d856861bbd2299b76c053f6d1301e7d13b9b785bca91 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/orchestration.py sha256=b68cd8be78948cb6d34305d9b14f12bae43ee1fbf2a6aac6b44fde62cabb13c7 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/orchestration_store.py sha256=e7ad91941648bb7d805db0bc73b98613dfc6d410bcad09a72063ba200c5d5f06 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/quality.py sha256=0ca64bfa4952654f10904a227ccf6b5b3dc570f69bfd242528a92e2b3194dd53 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/delivery.py sha256=c8ce75a43c69ad91eb0343c78821f01d7da22e32a578ff09459d77a6c46635a2 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/recovery.py sha256=e36d107b314190a33d5a85f3f721d91c5c3efe7636b4cb51de0c2e401d2d54d2 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/recovery_discovery.py sha256=fc26cf7771581cc18a624f34fe193e75ab86ea063d1ea3a22f91263621e611b4 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/config/settings.py sha256=a0e438c4053e33eab027bf40a0548b50b830fb7a2dc898bb695bbf208f6cb7a4 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/cli.py sha256=c76fbb562242b318adf5d08535a8768d5a4b4c8e1f36569cdc314e96a46a624b HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/00-original-specification.md sha256=2d984a562d990287f9f5c1d5d4bcf9296eac6de50faa37a8be208fc32e824743 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/01-existing-capability-assessment.md sha256=002a182aee5c5d3f29c06e1488228f937e923a25b2d31f44f8b21b0fe565944d HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/02-architecture.md sha256=8e450006c5b1d77500322274d8542c614390444e702a4f57160a4b030c43028f HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/03-autonomous-lifecycle.md sha256=a622724937e81d5344f914139183af8fe2929b3fc300ade8b8a6e9e83503ff30 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/04-state-and-recovery-model.md sha256=4158e9488e88230f37926ccdd1dd3aca0b404458cfaef0883d356e80a3860687 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/05-governance-and-authorization.md sha256=09c03747c81662d39cc7cc5de3f9fb910bc5ff57fc48d601730664935c6cf58d HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/06-implementation-plan.md sha256=6ceb4a66e50f52c0a42b2f401ad0289b03df5fd258bde49d3e08e13fe14efe53 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/07-acceptance-criteria.md sha256=58833528b916e7890c25abbfa561b2b73ea0a7d4d5d034c2764ef30b824c90db HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/diagrams/01-components.puml sha256=24e0202af3c852a53064fbc46ba2bb86738ea39cbd9bbf2974a6bd02a0bb14ff HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/diagrams/02-lifecycle.puml sha256=20ef664ab5a3178385be26ac1d39699f2c2664e0712d6b4362aa3e6fa41698af HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/diagrams/03-multi-agent-sequence.puml sha256=0df808e28b50a95316c5fb6ec823056b93f20eefd227f2abf8ad82cb3a7fb72a HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/diagrams/04-human-approval.puml sha256=5097e2b138b6b135c3d597579b0af3e11a2e98eebead170c33a68db934a5e2a0 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/diagrams/05-durable-state.puml sha256=31685e6970403d09daaca79242f15f18567e16ff7c936eb93c951cf7a874aaa8 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/diagrams/06-interruption-recovery.puml sha256=0f3b7dacaab0591372c1bf452e1f1ca98c2d120cfb4181de71786dae976f5af6 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/diagrams/07-repository-boundaries.puml sha256=ec8a4c3814ef73694ba1572d47133e6312f9fa28b788859f9d1e75617e8c4292 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/diagrams/08-end-to-end.puml sha256=7e74b11d5fd2ba5e96a2bcb44b7416802040deb6258cb9a83f39987df1a4a465 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-6/diagrams/09-cross-repository-dependencies.puml sha256=6280903dfeace28172cec2508da1dfecc427783f0dfc4a25a64d2e164a5a5444 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402

## Related artifacts

- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/business.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/architecture.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/service.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/01-components.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/01-components.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/02-lifecycle.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/02-lifecycle.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/03-multi-agent-sequence.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/03-multi-agent-sequence.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/04-human-approval.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/04-human-approval.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/05-durable-state.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/05-durable-state.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/06-interruption-recovery.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/06-interruption-recovery.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/07-repository-boundaries.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/07-repository-boundaries.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/08-end-to-end.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/08-end-to-end.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/09-cross-repository-dependencies.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/diagrams/09-cross-repository-dependencies.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/overview.md)
