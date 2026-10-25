# Local execution durability and conservative recovery

Status: Implemented for AEO-2; no AEO-3 scheduler.

Add executions, append-only grants and append-only attempts beside existing task/run state.
An atomic unique active slot enforces one PREPARING/RUNNING execution globally. All service
state and audit writes share transactions. Model success and orchestrator-run validation
remain separate; only verified validators can accept a write task, without completing a milestone.

Own process trees with a Windows kill-on-close job; confirm exit before claiming cancellation.
Persist process creation identity, session UUID, redacted raw output, normalized result and
partial files. Reconciliation never infers success or kills by stale PID. Unknown/live identities
block replay. Explicit recovery creates a new bounded grant and retains previous worktrees;
only verified read-only sessions may request continuation. No automatic write retries.

Consequences: this is local single-writer recovery. Disk artifacts and SQLite are not one atomic
transaction; reports can be regenerated from retained results, and interrupted work stays in place.
No distributed locks, workflow scheduling, concurrent agents or automated merges are introduced.
