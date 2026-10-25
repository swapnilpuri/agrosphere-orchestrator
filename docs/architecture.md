# Architecture

AEO-1 uses a modular Python application with synchronous, single-writer services.
Typer is the local operator entry point. Pydantic v2 validates YAML plans and role,
repository and approval configuration. Settings centralize environment and .env loading.
SQLAlchemy 2-style mappings and sessions own SQLite persistence; Alembic owns schema
changes. JSON logs go to stderr; CLI results go to stdout as JSON.

Dependencies point inward: CLI -> planning/configuration/repository inspection;
state services -> typed models and persistence. Future AgentExecutor and CodexWorkspace
protocols isolate SDK/process details. No concrete executor, model call or scheduling
loop exists. The execution seam is intentionally minimal; result/evidence envelopes
and cancellation protocols are AEO-2 decisions.

## Data and invariants

Project -> milestone -> task -> run/approval uses enforced SQLite foreign keys.
Project IDs are global; external milestone IDs are project-scoped; external task IDs
are milestone-scoped. UUIDs identify persisted child records. Milestone content is
immutable through the import service. A repeated exact import returns existing IDs;
changed content conflicts rather than silently altering a plan. Full plan import and
its creation events commit atomically. Each legal state change updates run bookkeeping
and appends its audit event in the same transaction. Audit table UPDATE/DELETE triggers
protect history from accidental SQL/ORM edits. Audit events are ordered by integer ID.

Pydantic graph validation checks uniqueness, missing dependencies, self cycles and
multi-node cycles. JSON Schema describes structure; graph invariants additionally require
Pydantic validation. Planning checks roles, operations and currently available confirmed
repositories. Lower-level persistence is a trusted service API; it is not a public sandbox.

## Trust and boundaries

Local configuration, human actor strings and the database owner are trusted. Approval
allowlists validate asserted identity; AEO-1 has no authentication provider. Direct SQL
can bypass state policies, and a database owner can remove audit triggers. History is
append-only within the application boundary, not cryptographically tamper-evident.
Git subprocess arguments are fixed and passed as arrays without a shell. Inspection
uses no remote commands and disables optional index locks and filesystem monitors.
The legacy inspector discovers immediate children; AEO-1B recursively discovers roots. Linked-worktree markers are supported
by the inspector but the bootstrap evidence script targets ordinary Git directories.

Configuration is source-checkout based and paths are CWD-relative except repository
paths, which are manifest-relative. This is not a standalone bundled wheel distribution
of configuration. There is no parallel scheduling, distributed locking or remote storage.
Python 3.12 is the minimum; validation evidence identifies the interpreter actually used.

## C4 views

PlantUML sources in diagrams/ use native PlantUML shapes and C4 semantic levels, without
network includes. Context describes operator/system boundaries; container describes CLI,
configuration, SQLite and local Git; component describes internal dependencies.
Diagram sources were reviewed as text; rendering is not claimed.

## Recovery observations (AEO-1B)

CLI -> discovery -> existing inspector and typed evidence. Recovery -> existing persistence
and audit service -> additive recovery_snapshots/recovery_heads tables. Approved plan/task/
approval tables retain their semantics. Snapshot identity excludes scan time. Observations,
head changes and audit events share a transaction. Reports use per-file atomic replacement
with export-only repair. Human text outside generated regions is preserved. Unmarked reports
fail closed. Application builds/tests, Git writes, agent execution and AEO-2 remain outside scope.

## Documentation-first lifecycle (AEO-1C)

Design scopes, immutable revisions/manifests, deterministic validations and authenticated
human decisions are separate from imported plans and recovery classifications. Migration
0003 adds five tables with append-only history guards and mutable case pointers. Serial
BA/architect/writer adapters and an independent review seam do not call live agents.
Repository-owned revision paths hold canonical documents; SQLite retains archival bytes.
The original state.transition entry point enforces exact scope, approval, validation and
artifact hashes before any implementation operation can start. See [workflow](design-workflow.md).

## AEO-2 controlled executor

The explicitly authorized AEO-2 implementation adds a transport-neutral execution service,
version-bound context, authenticated execution grants, isolated worktrees, native permission
canaries, process/session management and normalized evidence. Migration 0004 adds execution
records and an atomic single-active slot beside existing state. CLI, SDK and transport health
are probed; this installed CLI uses exec because mcp-server is unavailable. Existing artifact,
design, task-operation and delivery approvals remain independent. See [AEO-2 docs](aeo-2/README.md).


AEO-3 scheduling, handoffs, resource leases, and operator commands are described in [the orchestration guide](aeo-3/README.md).
