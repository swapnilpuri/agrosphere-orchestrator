# AEO-6 approval and durable recovery guide

The exact registered requirements and technical design approvals have been verified. AEO-6 is IMPLEMENTING; repeat requirements/design approval is unnecessary for this unchanged scope. Existing workflow semantics allow source implementation to evolve after approved context was verified at entry. Approved requirements, immutable revision artifacts and the imported implementation plan remain unchanged and are rechecked by the existing gate.

Current linkage verification:

~~~powershell
Set-Location C:\Projects\agrosphere\agrosphere-orchestrator
.\.venv\Scripts\python.exe docs\milestones\AEO-6\evidence\verify_implementation_checkpoint.py
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone design-status AEO-6
~~~

The earlier verify_design_checkpoint.py intentionally verifies pre-implementation source hashes and is historical design-preparation evidence. Use the implementation verifier after authorized source edits. Neither verifier creates decisions.

## Durable continuation

Each operation has an immutable intent before dispatch and a transactional committed outcome. The current operation remains owned until an independently observed result can be adopted. Parent counters and child claims survive interruptions. Concurrent resume cannot acquire a second operation or steal a stale writer lease.

- RECONCILING: repeat manifest-bound read-only facts; conflicts and unknown dependencies block.
- PREPARING_DESIGN: reuse exact stored revisions and repair incomplete exports through existing immutable publication. Recheck requirements/design identity and authorized approvers. Changed requirements are presented as a scope-change blocker.
- PLANNING_TASKS: adopt an exact persisted plan and its actual approval; otherwise retain uncertainty. Never duplicate uncertain execution preparation.
- EXECUTING: existing scheduler/session reconciliation owns child results and leases. Adopt verified completed outcomes; incomplete or uncertain children remain RECOVERY_REQUIRED. A fresh write recovery still needs existing authority.
- VERIFYING: reuse valid independent quality evidence and existing decisions. Repairs reserve each affected task in AEO-4's mutation transaction and require new exact execution grants. No policy is weakened.
- PREPARING_DELIVERY: adopt the exact persisted immutable delivery manifest; no arbitrary replacement.
- OBSERVING_DELIVERY: existing AEO-5 reconciliation observes branch/PR/current-SHA/CI/review outcomes, including response loss. Recovery never republishes blindly. Grant scope, actor, policy and expiry remain authoritative.

Use autonomous recover for observation/adoption, then autonomous resume after the reported blocker or approval has actually been resolved. Pause retains in-flight ownership and the operator reason even if a child outcome arrives. Budget pause retains all counts; resume never resets or silently increases the immutable run limits.

All 16 documented recovery categories have controller ownership/adoption tests; fault injection also covers intent, dispatch, observation and commit boundaries. Child-specific AEO-2–AEO-5 recovery/security regressions remain part of the full standard validator. Actual live model/provider recovery remains untested until separately authorized.

No application milestone is automatically advanced. Current discovery requires acceptance reconciliation and reports conflicting historical claims. AEO-5 remains IMPLEMENTING with its separate delivery/publication requirements. Actual autonomous application execution requires a separate explicit instruction after AEO-6 local acceptance.
