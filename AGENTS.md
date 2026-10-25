# AEO development boundaries

Current authorized scope: AEO-2, as explicitly requested by the user on 2026-10-24.
Preserve AEO-1, AEO-1B and AEO-1C. Do not begin AEO-3 without a separate request.
Implementation edits belong inside this project. Treat sibling application worktrees as
read-only during development/testing. Automated tests use temporary Git repositories.
Live model smoke tests require explicit opt-in and human authentication; do not run them
as part of the ordinary suite. Do not make application commits, pushes, PRs or deployments.

Use Python 3.12+, Pydantic v2, SQLAlchemy and Alembic. Configuration belongs in
src/agrosphere_orchestrator/config/settings.py. Keep adapters behind interfaces.
YAML must use safe loading and typed validation. Approval defaults must fail closed.
All state writes and audit events must share a transaction. Never mutate or delete audit
history. Database/config/code administrators remain trusted local operators.

AEO-2 runtime worktree/branch creation requires an exact authenticated execution grant.
Model writes must be technically isolated in that worktree; original dirty worktrees
must be preserved. No automatic replay, broad workspace access, unrestricted shell,
concurrent task scheduling, agent delegation, push, merge, install or deployment capability.
The role registry is execution metadata, not authorization to spawn collaborating agents.

Run python scripts/validate.py from the project virtual environment after changes.
Record actual exit codes and failures. Do not claim tests/live integration passed unless
executed. Native capability probes must not invoke a model or consume quota.
