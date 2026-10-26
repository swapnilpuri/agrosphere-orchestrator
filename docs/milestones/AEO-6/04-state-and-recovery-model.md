# Durable state and recovery model proposal

Run projection: ID, milestone, mode, workflow step, state, approved scope/revision, current operation, checkpoint subject/category, limits and reservations, usage, child execution/plan/delivery IDs, repository/base/head identities, artifact hashes, quality references, retries, failure classification, next permitted transition and timestamps. Append an immutable event and audit record for every projection mutation in the same transaction.

Run states: PLANNED -> RECONCILING -> PREPARING_DESIGN -> AWAITING_APPROVAL -> PLANNING_TASKS -> EXECUTING -> VERIFYING -> PREPARING_DELIVERY -> OBSERVING_DELIVERY -> REPORTED. PAUSED, BLOCKED and RECOVERY_REQUIRED are explicit resumable branches. REPORTED is an outcome, not formal milestone completion. Checkpoints name requirements/design/plan/execution/security/publication/recovery authority separately.

Operation states: INTENDED -> DISPATCHED -> OBSERVED -> COMMITTED; an interrupted DISPATCHED becomes UNCERTAIN pending child reconciliation. Atomically reserve maximum Codex invocations/attempts/task slots before dispatch, including concurrent batches and remediation. No post-hoc counter may permit an overrun. Keep reserved capacity for ambiguous operations until reconciled. A paused run retains cumulative counts; resume cannot reset its budget. Monotonic runtime enforcement plus persisted UTC elapsed accounting bounds execution across restarts. Child subprocess deadlines must fit the remaining run deadline; delivery polling is separately capped.

| Crash or restart boundary | Required reconciliation before continuation |
|---|---|
| Discovery | Repeat read-only observation; retain prior snapshot |
| Documentation generated | Compare immutable artifacts and stored child generation outcome; preserve partial files |
| Before design approval | Re-present exact stored subject without starting tasks |
| After approval | Verify latest decision, authorized identity and unchanged scope before adopting |
| Task decomposition | Adopt exact PlanRevision if it exists; otherwise resolve uncertain operation |
| During agent execution | Existing scheduler/execution recovery owns task claims; do not relaunch |
| Agent finished before parent persistence | Inspect durable child result, independently verify artifacts and adopt once |
| Parallel scheduling | Reconcile each claim/lease and reservation; block uncertain writers |
| Quality checks | Reconcile existing evidence; rerun only bounded read-only validation if safe |
| Remediation | Preserve attempt count, changed artifacts, design gate and exact write authority |
| Before publication | Revalidate all AEO-5 preconditions; no remote write without grant |
| Remote operation succeeded, response lost | delivery.reconcile observes exact PR/branch; no blind retry |
| PR/CI changed externally | Observe exact current SHA/policy/reviews; invalidate stale readiness |
| Approved artifacts modified | Existing design gate blocks; create revision and reapprove |
| Approval expired/revoked | Block the exact affected action; retain completed history |
| Repository/worktree conflict | Existing locks/isolation reject dispatch; require safe recovery decision |

Use atomic file writing for reports and retain content-addressed historical reports. Never overwrite partial approved designs or release uncertain writer ownership merely because a lease expired.
