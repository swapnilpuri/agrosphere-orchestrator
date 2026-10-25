# Session persistence design — as built

Migration 0004 adds executions, immutable execution_grants and immutable execution_attempts.
The current execution row stores request/context/result/session/cancellation state. Grants
bind exact request digests, verified human identity and expiry. Attempt transitions, task/run
changes and audit evidence share transactions. Original foundation, design and recovery tables
are retained. Attempt history is append-only. A global active-slot uniqueness constraint keeps
the AEO-2 single-execution contract atomic.

CodexProcessManager owns a Windows kill-on-close job before sending prompt stdin. Timeouts,
output budgets and cancellation stop the owned tree and wait for process exit. Pending
cancellation can be confirmed immediately; active cancellation is a request until the worker
confirms actual termination. Raw evidence is bounded and redacted separately from normalized
results. Per-execution Markdown/JSON reports and archives remain in private ignored storage.

Reconciliation compares persisted owner/child PID creation identities. Matching live identities
block replay. Unknown identities remain unresolved; absence/mismatch never implies success.
An interrupted task is failed for existing lifecycle bookkeeping and partial work stays in place.
No process is killed merely by a stale PID. Crash recovery is local and conservative, not distributed.

Resume creates a new bounded execution with the previous evidence/context and explicit recovery
instructions. It needs a new human grant. Completed, active and cancelled tasks are not blindly
reopened. Write sessions are not continued automatically; their old worktrees remain preserved.
Only verified read-only session UUIDs can request codex exec resume with the same bounded policy.
Those continuation calls are implemented but not live verified. SQLite/file report publication is
not one distributed transaction; persistent DB evidence survives a report-write interruption.
