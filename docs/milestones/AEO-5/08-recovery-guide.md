# AEO-5R durable delivery recovery

Run aeo delivery recover RUN_ID UNIT_ID or delivery reconcile. Both are read-only with respect to GitHub and branch creation. Never replay push/create after a lost response.

## Persistence and ownership

Every mutation stores a stable artifact-bound DeliveryOperation, consumes its exact AEO-4 one-time grant, acquires the existing repository:<id> write lease and appends intent/audit evidence in one serialized SQLite transaction. No network operation holds the write transaction. The external result is observed and recorded in another transaction. A network/process/transaction exception after intent retains the operation and write lease as RECOVERY_REQUIRED.

Intents and outcome events are append-only; immutable content-addressed evidence retains historical snapshots. Unit/PR identities cannot be silently replaced. Leases do not become stealable merely because their timestamp expires. AEO-2/AEO-3 scheduling and delivery share the same repository resource namespace.

## Decisions

| Observed situation | Recovery behavior |
| --- | --- |
| Exact isolated branch/head/common repository exists | Verify clean isolated identity; record observed preparation completion |
| Push response lost, exact remote branch head exists | Record reconciled completion; release only that operation's lease |
| PR response lost, exactly one exact matching open PR exists | Retain immutable PR identity; record completion; no second create |
| No provable result after intent | Retain lease and unresolved-intent blocker; no blind mutation retry |
| Multiple PR matches, foreign repository, wrong head/base, disappeared persisted PR | Block for human investigation; no create/reopen/replacement |
| Closed/merged PR observed | Record terminal blocker; never reopen or replace it |
| Authentication/rate-limit/network/policy unavailable | Append unavailable observation and blocker; never interpret it as success |
| Changed source/head/base/policy or revoked approval | Block/invalidate readiness and authorization; retain previous snapshots |
| Dependency PR open | Downstream content unavailable |
| Exact dependency PR merged and merge commit reachable from target | Content available; other unit guards still apply |
| Partial multi-repository completion | Reconcile units independently; incomplete aggregate remains blocked |

An unresolved intent with no provable external result is never automatically reset or retried. After read-only reconciliation has recorded actual available remote evidence, an operator may request a fresh action recover-prepare, recover-push or recover-create-pr through delivery request-approval, authenticate it through the existing AEO-4 approvals interface, and invoke delivery recover --action prepare|push|create-pr --approval REQUEST_ID. The new grant binds the previous immutable operation IDs, exact reconciled observation hash, current source/remote/policy and isolated target. An ordinary prior grant cannot authorize recovery. Unavailable or changed remote evidence blocks the request.

The coordinator consumes the fresh grant, appends superseded events for prior intents, releases only their leases and acquires the replacement operation lease in one serialized transaction. A competing scheduler lease rolls back all of that work. Old intents, decisions and evidence remain immutable. Another interrupted attempt requires another observation and fresh human grant. This is an explicit reviewed retry, not a default replay or lease-steal command. Do not edit/delete intent/audit rows or disable guards as a workaround.

## Evidence

JSON reports contain the manifest, unit state, immutable PR ID/number/URL, exact head/base, policy/CI/review snapshots, required-check/application identities, authenticated principal, quality/security/approval references, prior state, blocker codes, observation time and complete event/evidence hashes. Markdown reports expose actual values and unknown fields. Stored readiness expires after 60 seconds and never executes a merge.

The mocked end-to-end/restart/failure-injection tests exercise response loss, local outcome transaction failure after remote success, independent multi-repository recovery, existing resource conflicts, duplicate/terminal PRs, immutable history and unchanged source worktrees. See the acceptance report for actual executed results. These tests do not establish live GitHub credentials, token scope or production write success.
