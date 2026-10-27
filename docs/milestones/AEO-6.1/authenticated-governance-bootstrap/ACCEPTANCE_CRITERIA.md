# Acceptance criteria and security test plan

Status: SPECIFIED, NOT EXECUTED. All future mutation tests use disposable SQLite databases, temporary repositories/bundles and test-only authority/identity keys. Mock verifier results are labeled; they cannot establish real Windows authentication or OS isolation. Production database/configuration/run history must never be test fixtures.

## Required invariants

- AC-1: External authority is independently provisioned, pinned, fresh and deployment bound. No SID is inferred or self-enrolled. Authority absence or failed integrity verification denies all administrative writes and protected admissions.
- AC-2: Successful identity authentication, current administrator authorization and external exact-scope change authorization are each necessary. The challenge binds all decision fields; no generic approval, supplied actor or test adapter authorizes production.
- AC-3: Only the five documented surfaces can change. Whole-configuration comparison preserves all other permissions and live_enabled=false. A valid schema alone never certifies command safety or QA/regression readiness.
- AC-4: Rejected, revoked, expired, replayed, stale or manifest-mismatched decisions cannot activate. Immutable history survives every negative outcome.
- AC-5: A consumer sees one complete committed generation or is denied. Bundle durability/sealing precedes head selection; selection, consumption and audit share one SQLite transaction.
- AC-6: Concurrent activation, crash and retry cause at most one head transition per decision. Unknown acknowledgement is resolved from durable identity, not repeated side effects.
- AC-7: Settings/env/path/DB redirection, stale process snapshots and alternate CLI/service entry points cannot bypass governed-mode admission.
- AC-8: Decision, activation and audit evidence are immutable/digest verified, with externally retained receipts under documented custody. Claims distinguish ordinary append-only protection from privileged host tamper resistance.
- AC-9: No milestone import, source change, application mutation, model/provider use, resumed run, live opt-in, code-write approval synthesis or deadline change follows from administrative approval or activation.

## Negative, concurrency and failure tests

| Case | Setup/action | Required observable result |
|---|---|---|
| Unauthorized administrator | Successful Windows-verifier fixture SID not in external root; include design/execution/governance members | No decision/selection/consumption; authorization error, no secret-bearing logs |
| Absent trust root | Missing, unreadable, empty, expired, invalid-signature or wrong-deployment authority | Fail closed before prompt/write; no fallback identity or config |
| Wrong SID | Correct display name with different token SID; malformed SID, alias or wildcard | Canonical token SID checked exactly; rejected |
| Agent self-authorization | Agent token invokes CLI and direct APIs; edits proposed members; uses TTY or claimed admin actor | OS denies protected writes/key use; service rejects agent identity; proposal never adds administrative members |
| Replayed decision | Same decision against same/different activation keys or database/profile | Same committed result only for exact retry; no second selection; cross-deployment/profile fails |
| Rejected/expired decision | Reject, then approve same request; expiry at boundary; timestamp-only replacement | Terminal rejection preserved; activation denied; new independently authorized revised request required |
| Stale configuration | Baseline head/generation or immutable guard values change while authentication is pending | Post-prompt CAS/full digest check fails; no head change |
| Changed review manifest | Change manifest whitespace/bytes, listed file, relative base or executable dependency | Byte/root/dependency mismatch; no consumption |
| Unauthorized scope expansion | Alter another role, role operation/instruction, DB URL, command argv/read path/timeout, network/process settings, live flag or application root | Exact diff validator denies; approved values cannot mask extra fields |
| Concurrent activation | Two processes/barrier at same baseline with same and competing decisions | At most one generation transition; exact retry converges; loser stale/conflict; no audit-chain fork |
| Partial filesystem failure | Inject disk-full/short write/flush/ACL/seal/publish failure for each bundle step | Old head intact; no selected partial bundle; orphan is inactive and evidence retained |
| Database commit failure | Inject constraint, disk/I/O and commit failure before/after durable acknowledgement boundary | Precommit rollback includes selection, consumption and audit; unknown result resolved by key; sealed orphan harmless |
| Crash and retry | Kill process after each file write/flush/seal, before transaction, after insert/CAS/audit and after commit before CLI output | Restart selects old or new complete generation; verifies original decision before retry; no duplicate activation |
| Reader/activation race | Hold admission lock with old snapshot; attempt activation; restart stale reader | Activation waits/fails quiescence; stale snapshot cannot perform later privileged action |
| Audit integrity | UPDATE/DELETE events/blob/activation, change receipt/chain/digest, truncate copied DB against external checkpoint | Guards or verification reject; no silent repair or rewritten history; checkpoint-limit distinction documented |
| Revocation | Remove admin/increment epoch during prompt and before activation; revoke decision; revoke after activation | Recheck denies recording/consumption or future admission as applicable; existing history unchanged; no automatic rollback |
| Root rollback/recovery | Replay old signed epoch, swap root pin/path, restore older DB/bundle pair | Protected/external high-water check denies; custodian recovery required |
| Environment bypass | Override all protected AEO_* settings, .env, working directory, SQLite path, supplied Settings and alternate entry points | Fixed production deployment binding or explicit conflict denial; no agent-controlled fallback |
| File tampering/path escape | Reparse point, case/root ambiguity, duplicate JSON/YAML keys, changed bundle after verification | Deny; consumers parse captured verified bytes, never reopened mutable drafts |
| Compensation | New authorized reverse activation; old decision reused or revocation alone | New generation+audit only with new exact authority; no hidden pointer restore |
| Legacy gate independence | Valid config decision plus plan approval/grant, but no operation approval | state.transition still denies code-write; no Approval row synthesized |
| Preservation/upgrade | Additive migration on copied populated DB with original records and deadline | All existing rows/digests/constraints and run identity preserved; no synthetic milestone; no destructive downgrade |

Tests must assert selection, consumption count, audit linkage and unchanged protected values, not just an exception string. A rejected unauthenticated attempt may leave a denial log, but no approval state; if its DB log cannot persist, the operation still fails and reports unavailable audit rather than proceeds.

## Reuse and execution plan after authorization

Inspected existing tests: test_configuration.py covers env resolution, manifest bases and extra fields; test_persistence_state.py covers append-only audit, idempotent imports and independent operation denial; test_design.py covers noninteractive rejection, modified artifacts and removed approvers; test_execution.py covers grants/replay/expiry/protected scopes/disabled policy; test_orchestration.py covers plan approval independent of execution grants and serialized coordination; test_autonomous_security.py covers real/simulated database separation. Reuse fixtures/patterns, not their simulated authentication as proof of real administrator authority.

After independently authorized implementation, execute new focused authority/decision/activation/upgrade tests and relevant existing configuration, design, persistence, execution, orchestration and autonomous security suites in disposable state. Capture actual commands, exit codes and raw results. A separate operator acceptance on a supported Windows host must prove real credential-to-SID mapping, distinct agent/operator tokens, denied ACL/key use, trusted installation resolution and local-volume flush/crash behavior. Never supply credentials to the agent.

AGENTS.md requires the project virtual environment's scripts/validate.py after changes. Here no source implementation is authorized and the validator can migrate authoritative DB/config and generate reports. Future implementation must resolve the separately governed disposable regression profile first, preserve prior reports, then run the required validator there with actual results. If process launch remains unavailable or isolation is unresolved, record the acceptance gate as blocked; do not request elevation, spawn through another route or claim tests passed. No validation command is executed in this design pass.

Release acceptance requires all AC items and failure tests passing, independent security/configuration authority review, recorded external trust-root/OS controls, and authenticated approval of the exact release and first configuration selection. Agent preparation does not certify those prerequisites.
