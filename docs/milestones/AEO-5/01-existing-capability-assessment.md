# Existing capability assessment

Status: proposed design; implementation blocked on authenticated requirements/design approval. References are relative to the orchestrator root unless linked.

| Capability | Existing code / proposed addition | Existing tests / required new tests | Status |
| --- | --- | --- | --- |
| GitHub provider | No provider; propose github_models.py and github_provider.py | No provider tests; auth, parse, permissions, timeout and redaction fixtures needed | Missing |
| Branch management | execution_workspace.py isolates execution worktrees; delivery branch service absent | test_execution.py preservation/hook fixtures; branch names, exact base, clean isolated head, reuse/conflict tests needed | Missing |
| PR automation | No PR service; propose delivery.py | PR payload/publication tests needed | Missing |
| Duplicate prevention | No PR lookup or identity persistence | Duplicate-open, closed/merged, conflicting identity, ambiguous-timeout and lock-contention tests needed | Missing |
| Multi-repository coordination | orchestration_store.py ResourceLease/acquire/release reusable; delivery manifest absent | test_orchestration.py claims/leases; delivery DAG and partial-completion tests needed | Missing |
| CI monitoring | Local quality validators in quality_adapters.py; no remote CI reader | Required/optional checks, exact-SHA freshness and unavailable policy tests needed | Missing |
| GitHub review verification | No GitHub review integration | Human/bot/self/dismissed/stale/CODEOWNERS tests needed | Missing |
| Approval enforcement | quality.py assert_delivery, readiness, request_approval, consume_approval and HumanVerifier reusable | test_quality.py authenticated approval, tamper/revocation/expiry fixtures exist; exact publish context tests needed | Missing for AEO-5 |
| Durable state | Existing execution/task/governance entities; no delivery entities or operations | Existing persistence tests; upgrade-preservation and restart tests needed | Missing for AEO-5 |
| Remote recovery | Local execution and scheduler reconciliation reusable | Existing interrupted local execution tests; push/PR ambiguity and remote reconciliation tests needed | Missing |
| Delivery evidence | quality_store.py append-only blobs/events reusable; no delivery aggregate | Existing hash-integrity tests; PR/check/review/Git/report binding tests needed | Missing |
| CLI commands | cli.py groups through AEO-4; no delivery group | Existing CLI tests; all nine delivery commands and no-write assertions needed | Missing |

All twelve capabilities remain incomplete. A reusable foundation is not a complete delivery capability. The previous full suite passed 163 tests; a fresh established-validator run is recorded separately for this recovery turn. No AEO-5 behavioral tests have run because production implementation has not been authorized through the required design gate.

## Risks and intended changes

Preserve existing immutable history, imported plans and task semantics. Add delivery data through Alembic 0007 without rewriting task tables. Reuse BEGIN IMMEDIATE transactions and the existing repository resource lease keys; do not introduce independent locks. Remote outcomes cannot share a SQLite transaction, so ambiguous operations retain intent and require observation before any replay. Changing head/base/remote/policy revokes readiness and publishing authorization. Fail closed on unavailable GitHub requirements and unsupported rules. Extend internal documentation ownership narrowly after requirements review; never publish orchestrator design into sibling repositories.
