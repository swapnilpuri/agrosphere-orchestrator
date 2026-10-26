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
