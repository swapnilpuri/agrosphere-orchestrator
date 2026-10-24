# AEO development boundaries

Scope is AEO-1 Foundation. Do not start AEO-2 without separate user approval.
Work only inside this project. Treat sibling AgroSphere repositories as read-only.
Never create branches, commits, remotes, PRs, cloud deployments or live model calls
as part of AEO-1. Preserve independent repository boundaries.

Use Python 3.12+, Pydantic v2, SQLAlchemy and Alembic. Configuration belongs in
src/agrosphere_orchestrator/config/settings.py. Keep adapters behind interfaces.
YAML must use safe loading and typed validation. Approval defaults must fail closed.
All state service writes and audit events must share one transaction. Never mutate
or delete audit history. Database-file owners remain trusted administrators.

Run python scripts/validate.py from the project virtual environment after changes.
Record actual exit codes and failures. Do not describe tests as passing unless executed.
Do not add agent concurrency, live coding, automatic Git writes or deployments here.
The role registry is organizational configuration, not authorization to spawn agents.
