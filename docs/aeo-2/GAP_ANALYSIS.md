# AEO-2 inspection and gap analysis

The user explicitly authorized AEO-2 on 2026-10-24. Earlier AEO-1 scope restrictions remain
historical; no application task or optional billed live test is authorized by default.

Reuse the existing typed plans/tasks, manifest/role registry, Settings, human verifier,
design gate, SQLite/Alembic/audit transaction service and Typer CLI. Preserve dirty AEO-1C
changes observed at task start; no commits or resets are performed.

Actual discrepancies: there is no executor, session or execution approval model. AEO-1 task
approval asserts an actor string and is insufficient for live execution. AEO-1C defaults to
approved-input templates and a rule reviewer, requires a configured PlantUML JAR, and has no
approved application design in the live database. Recovery classifications are not approvals.
The SDK packages were initially absent. Codex 0.164.0-alpha.11.1 is installed/authenticated;
its help rejects mcp-server, despite the older official MCP cookbook describing that transport.
The current CLI exposes non-interactive JSON/schema output. SDK 0.24.0 MCP signatures were
inspected locally after installing the project dependency. Live model execution has not run.

Implementation plan: add typed execution envelopes and a separate immutable human execution
grant; reuse the registry with typed execution metadata; build targeted, hashed context from
approved design and manifest references; require isolated worktrees for writes; enforce OS
sandbox policy and fail closed if not verifiable. Prefer SDK MCP only on a compatible probed
runtime; use verified CLI exec otherwise. Separate transport success from orchestrator validation.
Persist all attempts, session/error/partial evidence and audit atomically. Explicit resume never
replays writes automatically. No scheduler, concurrent delegation, PR, push, merge or deployment.
