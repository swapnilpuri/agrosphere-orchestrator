# AEO-6: architecture (design)

Scope: 48fd59274969f5abf0623159f5d15dba1c00111a80a67a654184ee58be6a2143
Requirements: AEO6-DISCOVERY, AEO6-CONTROLLER, AEO6-DESIGN, AEO6-APPROVAL, AEO6-DAG, AEO6-QUALITY, AEO6-DELIVERY, AEO6-DURABLE, AEO6-BUDGET, AEO6-CLI, AEO6-EVIDENCE, AEO6-SAFETY

## Architecture overview

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

## Impacted microservices

Only agrosphere-orchestrator source/schema/CLI changes; application repositories remain read-only during AEO-6 development.

## DDD boundaries

Run coordination references existing design/task/quality/delivery domains without duplicating their authority.

## APIs and event interactions

Internal Python application services and Typer commands. No new application API/event contract.

## Database changes

# Durable state and recovery model proposal

Run projection: ID, milestone, mode, workflow step, state, approved scope/revision, current operation, checkpoint subject/category, limits and reservations, usage, child execution/plan/delivery IDs, repository/base/head identities, artifact hashes, quality references, retries, failure classification, next permitted transition and timestamps. Append an immutable event and audit record for every projection mutation in the same transaction.

Run states: PLANNED -> RECONCILING -> PREPARING_DESIGN -> AWAITING_APPROVAL -> PLANNING_TASKS -> EXECUTING -> VERIFYING -> PREPARING_DELIVERY -> OBSERVING_DELIVERY -> REPORTED. PAUSED, BLOCKED and RECOVERY_REQUIRED are explicit resumable branches. REPORTED is an outcome, not formal milestone completion. Checkpoints name requirements/design/plan/execution/security/publication/recovery authority separately.

Operation states: INTENDED -> DISPATCHED -> OBSERVED -> COMMITTED; an interrupted DISPATCHED becomes UNCERTAIN pending child reconciliation. Atomically reserve maximum Codex invocations/attempts/task slots before dispatch, including concurrent batches and remediation. No post-hoc counter may permit an overrun. Keep reserved capacity for ambiguous operations until reconciled. A paused run retains cumulative counts; resume cannot reset its budget. Monotonic runtime enforcement plus persisted UTC elapsed accounting bounds execution across restarts. Child subprocess deadlines must fit the remaining run deadline; delivery polling is separately capped.

| Crash or restart boundary | Required reconciliation before continuation |
|---|---|
| Discovery | Repeat read-only observation; retain prior snapshot |
| Documentation generated | Compare immutable artifacts and stored child generation outcome; preserve partial files |
| Before design approval | Re-present exact stored subject without starting tasks |
| After approval | Verify latest decision, authorized identity and unchanged scope before adopting |
| Task decomposition | Adopt exact PlanRevision if it exists; otherwise resolve uncertain operation |
| During agent execution | Existing scheduler/execution recovery owns task claims; do not relaunch |
| Agent finished before parent persistence | Inspect durable child result, independently verify artifacts and adopt once |
| Parallel scheduling | Reconcile each claim/lease and reservation; block uncertain writers |
| Quality checks | Reconcile existing evidence; rerun only bounded read-only validation if safe |
| Remediation | Preserve attempt count, changed artifacts, design gate and exact write authority |
| Before publication | Revalidate all AEO-5 preconditions; no remote write without grant |
| Remote operation succeeded, response lost | delivery.reconcile observes exact PR/branch; no blind retry |
| PR/CI changed externally | Observe exact current SHA/policy/reviews; invalidate stale readiness |
| Approved artifacts modified | Existing design gate blocks; create revision and reapprove |
| Approval expired/revoked | Block the exact affected action; retain completed history |
| Repository/worktree conflict | Existing locks/isolation reject dispatch; require safe recovery decision |

Use atomic file writing for reports and retain content-addressed historical reports. Never overwrite partial approved designs or release uncertain writer ownership merely because a lease expired.

## Security considerations

# Governance and authorization proposal

The user explicitly requires AEO-1C requirements and technical-design approval. Existing design.generate_design calls require_approval for the exact scope before generation. design.decide uses WindowsConsoleHumanVerifier; chat instructions cannot substitute for its authenticated decision. Therefore the first checkpoint for this request is requirements approval. Draft documentation, diagram preparation, registration and baseline tests are allowed before that checkpoint. Production controller implementation and schema changes wait for design approval.

Maintain separate authorities: registered requirements; validated immutable technical design; scheduling plan; exact local execution requests; activated AEO-4 quality/security policy and decisions; action-specific AEO-5 publication grants; human recovery decisions; explicit milestone advancement. An approval for AEO-5 is never approval for AEO-6. A selected mode, model response or role label grants nothing.

At every boundary finish authorized preparation, persist its exact review subject, produce the existing CLI decision command, and stop only dependent execution. Resume re-evaluates existing decisions, allowlists and artifact hashes. Do not repeatedly ask when the latest decision is valid for the same scope. Changed artifacts/context or rejected/revoked/expired authority fail closed. Never insert decisions directly into SQLite, add an approver automatically, emulate a human verifier against runtime, or consume an unrelated grant.

No automatic remote-write enablement, protected branch modification, force push, duplicate PR, merge, deployment or application milestone launch. Original dirty worktrees remain untouched. Simulated approvals exist only in fixture databases using established authenticated fixture mechanisms. Do not log passwords, tokens, environment files or credential material. Ordinary plans/status never mutate application repositories.

## Technology decisions

Python 3.12+, existing Pydantic v2, SQLAlchemy/Alembic, SQLite and Typer; safe local PlantUML; existing injected adapters.

## Architectural trade-offs

Additional small durable projections in the existing database; narrow scheduler budget hook if needed; no second scheduler or continuous daemon.

## Risks and assumptions

Raw recursive discovery includes test fixtures; confirmed manifest identities and roots must constrain selection. Unknown model cost cannot establish monetary affordability. AEO-5 runtime delivery remains pending.

## Architectural decisions

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

## Integration design

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

- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/business.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/architecture.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/service.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/01-components.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/01-components.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/02-lifecycle.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/02-lifecycle.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/03-multi-agent-sequence.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/03-multi-agent-sequence.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/04-human-approval.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/04-human-approval.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/05-durable-state.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/05-durable-state.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/06-interruption-recovery.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/06-interruption-recovery.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/07-repository-boundaries.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/07-repository-boundaries.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/08-end-to-end.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/08-end-to-end.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/09-cross-repository-dependencies.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/diagrams/09-cross-repository-dependencies.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6/revisions/9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88/overview.md)
