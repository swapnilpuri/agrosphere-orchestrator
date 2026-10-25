# AgroSphere AI Engineering Orchestrator

AEO-1 is a local, single-process Python foundation for a future engineering organization.
It validates plans and inspects repositories. It does not run agents or call models.

## Run locally (PowerShell, Python 3.12+)

Run from this directory; configuration paths are relative to the current working directory.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\aeo.exe project-status
.\.venv\Scripts\aeo.exe repository-inspect
.\.venv\Scripts\aeo.exe repository-inspect --discover-root ..
.\.venv\Scripts\aeo.exe milestone-validate examples/aeo-1.yaml
.\.venv\Scripts\python.exe scripts/validate.py
```

No API keys are needed. Environment variables override .env and defaults in
[src/agrosphere_orchestrator/config/settings.py](src/agrosphere_orchestrator/config/settings.py).
Inspection and validation never import plans or initialize state. Status opens an existing
SQLite database with mode=ro. Alembic explicitly creates/migrates only the orchestrator database.

## Project structure

- src/agrosphere_orchestrator/: configuration, models, planning, persistence, state,
  read-only repository inspection, JSON logging, CLI and future adapter protocols.
- config/: repository manifest, nine-role registry and approval policy.
- migrations/: Alembic schema and SQLite append-only audit triggers.
- tests/: fixtures and core module, CLI and integration verification.
- examples/: YAML milestone plan.
- scripts/: reproducible validation and local repository verification.
- docs/: architecture, PlantUML C4 diagrams, ADRs, policy/state specifications,
  generated JSON Schemas, roadmap and executed validation evidence.

## Core usage

The Python service API exposes import_plan(engine, MilestoneSpec) for atomic, idempotent
project/milestone/task creation, record_approval(...) for authorized decisions, and
transition(...) for explicit task/run lifecycle changes. These are bookkeeping APIs;
marking a task running never invokes an agent. Initialize with Alembic before using them.
A duplicate project/milestone ID with different content is rejected. Task identity is
scoped to a milestone; duplicate imports produce no extra tasks or audit events.
Use planning.validate_plan before import when repository and role validation is required.
The lower-level import API enforces the milestone model, not workspace permissions.

## Repository safety

Manifest confirmation records a successful local Git inspection at bootstrap time.
Paths are relative to the manifest file; existence and Git validity are checked again
when validating plans. Discovered repositories remain unverified until explicitly reviewed.
Missing entries are reported, never synthesized. No remote URLs are read or contacted.
Git commands are restricted to rev-parse, symbolic-ref, status and bounded local log reads with optional locks and fsmonitor
integration disabled. No branch, commit, merge, fetch or PR operations exist.

## Design and scope

See [architecture](docs/architecture.md), [roles](docs/agent-roles.md),
[state machine](docs/state-machine.md), [approvals](docs/approval-policy.md),
[validation report](docs/validation/REPORT.md) and [future milestones](docs/roadmap.md).
OpenAI Agents SDK and Codex are represented only by protocols; SDK dependencies and
credentials are deliberately deferred until approved AEO-2 adapter work.

This directory is an independent Git repository with no commits, branch refs or remote.
No existing microservice repository is consolidated or modified. AEO-2 requires a
separate approval and is not started by any AEO-1 command.

## AEO-1B project discovery and recovery

Run from this directory after upgrading the existing database:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\aeo.exe project discover
.\.venv\Scripts\aeo.exe project reconcile
.\.venv\Scripts\aeo.exe project status
.\.venv\Scripts\aeo.exe milestones history
.\.venv\Scripts\aeo.exe milestones next
.\.venv\Scripts\aeo.exe project reconcile --export-only
```

Settings AEO_WORKSPACE_ROOT (default ..) and AEO_RECOVERY_DIRECTORY (default project)
follow existing CWD-relative conventions. Report output must resolve inside this orchestrator.
Discovery prints JSON without database or file writes. Reconcile writes local bookkeeping,
never plans, approvals, builds or agent invocations. Status/history/next open SQLite read-only
and fail if missing. The original flat CLI commands remain available.

Recovery recursively discovers actual Git roots, including nested roots and linked-worktree
markers. Missing manifest entries are reported; roadmap names never create repositories.
The orchestrator itself is excluded from application recovery to avoid feedback into its
snapshots. Generated dependencies and symlinks are skipped. Branch/HEAD, dirty status, inferred
build/test commands, documentation, contracts, source/test inventories and historical XML
outcomes are retained. Commands are listed, never executed. Local history reads at most 200
subjects per repository. Evidence records hashes, line references, modification times and
observed HEAD. Observed HEAD does not prove that an uncommitted artifact was produced there.

Automatic evidence matching is conservative: implementation claims corroborated by source
inventories yield PARTIAL; unsupported claims and missing history yield UNVERIFIED. No report,
commit subject or source file alone establishes COMPLETED, NOT_STARTED, verified acceptance
or approval. Those classifications remain representable for future reviewed verification.
Historical test passes do not prove full acceptance against a dirty worktree. Additional
milestones are recorded even when their requirements are unavailable. The next command
identifies the earliest verification gap in the requested 1A-through-3B chain and separately
reports a conditional 3B candidate when 3A implementation is observed. Generic roadmap parents
(1 or 3) do not displace that chain.

Reconciliation stores content-addressed snapshots, a workspace current pointer and audit events
in one transaction. Unchanged evidence (ignoring scan time) creates no duplicate records or
audit events. Returning to an older observation changes the pointer with an audit event.
Imported milestone specs, tasks and approval records are never modified.

The five project/ reports are projections of SQLite observations. Every report contains its
snapshot ID. Each file is replaced atomically; interruption can leave different generations.
Run project reconcile --export-only to repair all five from committed state without rescanning.
Export preflights all reports before replacing any. Existing unmarked files fail closed. Put
manual approvals and notes OUTSIDE the AEO RECOVERY markers; generated regions belong to the
exporter. YAML reserves recovered_observations and preserves other top-level keys; duplicate
top-level keys fail closed. Single-process/single-writer operation remains supported.

See [recovery report](project/RECOVERY_REPORT.md), [history](project/MILESTONE_HISTORY.md),
[inventory](project/REPOSITORY_INVENTORY.yaml), [state](project/CURRENT_STATE.md) and
[roadmap](project/ROADMAP.yaml). AEO-2 requires separate authorization.

For executed workspace safety/idempotence evidence, run .\.venv\Scripts\python.exe scripts/verify_recovery.py. It compares application Git metadata and evidence-file fingerprints before/after repeat discovery and records docs/validation/recovery.json.

## AEO-1C documentation-first design

Milestone design generation, deterministic validation, immutable artifact manifests and
authenticated human approval now gate future implementation task starts. See the complete
[design workflow](docs/design-workflow.md) and [AEO-1C report](docs/validation/AEO-1C_REPORT.md).
The milestone CLI group adds design, docs, validate-design, design-status and approve-design,
plus requirements approval, readiness, as-built reconciliation and delivery approval.
No future application design or implementation is created by installing this capability.
