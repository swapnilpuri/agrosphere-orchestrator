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
