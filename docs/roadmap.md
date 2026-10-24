# Proposed milestones (not implemented)

## AEO-2 — Controlled single-task execution

Proposed exact scope: choose and pin OpenAI Agents SDK/Codex adapter versions; define
typed execution requests, artifact/evidence results, cancellation and error contracts;
implement one serial, operator-invoked task executor behind the existing protocols;
add authenticated human approval integration and immutable task/operation/repository
scope binding; define isolated workspace lifecycle with an explicit repository allowlist;
add per-run budget, timeout and credential-redaction controls; persist adapter results
and failure events. Use deterministic fake adapters for unit tests and opt-in live
contract tests only after separate authorization. No autonomous queue, concurrency,
GitHub writes, merge, deployment or multi-repository write coordination.

Acceptance: a single explicitly approved task runs through one adapter in isolation;
refusal, timeout, cancellation and restart evidence is durable; defaults remain offline;
no execution can escape its approved repository/operation scope. Decisions needed:
SDK vs Codex process transport, identity provider, workspace location, credential source,
model/budget policy and approval expiry/retry semantics. AEO-2 begins only on approval.

## AEO-3 — Serial workflow and recovery

Build durable scheduling, verified dependency completion, retry policy, interrupted-run
reconciliation and artifact provenance. Demonstrate deterministic replay with fake
executors. Retain serial execution until a separate concurrency design is approved.

## AEO-4 — Reviewed multi-repository changes

Define cross-repository contract versioning and compensating plans. Add opt-in isolated
Git worktrees and reviewable patch proposals per repository. Any branch/PR write requires
explicit policy and approval; preserve independent repositories and never consolidate.

## AEO-5 — Governed parallel organization

Design leases, idempotency under concurrent writers, capacity/budget scheduling,
role handoff validation and hardened authentication. Evaluate PostgreSQL before multi-host
coordination. Prove contention handling, cancellation and audit ordering under load.

## AEO-6 — Production governance and operations

Add observability, retention/backup/restore, signed provenance, operational dashboards
and separately approved delivery integrations. Security review and failure exercises
precede production or deployment automation. None of these phases is automatically enabled.
