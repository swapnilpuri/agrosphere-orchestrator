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
