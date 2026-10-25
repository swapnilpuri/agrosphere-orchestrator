# Task state machine

| Source | Allowed targets |
|---|---|
| pending | ready, cancelled |
| ready | running, cancelled |
| running | succeeded, failed, cancelled |
| failed | ready, cancelled |
| succeeded | none |
| cancelled | none |

A transition to ready or running requires every declared dependency in the same milestone
to be succeeded. Starting an operation requiring approval uses the most recent persisted
approval decision and checks its actor against the current allowlist. Invalid edges,
missing dependencies and missing/denied approvals roll back without an audit mutation.
Starting creates a bookkeeping run. Leaving running finishes that run. Failed -> ready
allows a retry; approval remains task/operation-scoped across retries in AEO-1.
No actual process or agent starts. Transition actor is an asserted local identity;
role permissions are enforced in plan validation, not a runtime RBAC identity system.

## Milestone design lifecycle

The task state machine above is preserved. New implementation starts additionally require
a design case in IMPLEMENTATION_READY or IMPLEMENTING, current authenticated scope/design
approvals, a matching imported plan, passing validation and unchanged artifact hashes.
Read-only plan/inspect/validate task operations retain their existing behavior.
See [documentation lifecycle](design-workflow.md) and diagrams/design-lifecycle.puml for
DISCOVERED through COMPLETED, including revision/rejection and delivery guards.

## Execution states (AEO-2)

QUEUED -> AWAITING_APPROVAL -> PREPARING -> RUNNING -> SUCCEEDED/FAILED/TIMED_OUT/CANCELLED.
Lost owners become INTERRUPTED after process-identity reconciliation. Execution success and
task acceptance are separate. An unvalidated write proposal cannot mark a task accepted or
complete a milestone. The DB enforces one active execution; no scheduler is added.
