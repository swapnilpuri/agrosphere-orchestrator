# Security and threat model

Status: PROPOSED; no security control described here has been implemented or certified by this work. Normative companion to DESIGN_PROPOSAL.md.

## Assets and trust boundaries

Protect independent administrative authority, exact configuration scope, current selection/generation, unconsumed decisions, audit history and the separation between proposal preparation and authorization. Protect credentials, receipt keys, original application state and approved design artifacts.

Trust boundaries: agent workspace -> trusted installed operator CLI; Windows credential authentication -> external administrative authorization; editable review files -> immutable captured evidence; immutable filesystem bundle -> authoritative SQLite head; current decision -> later consumption; local audit -> independently retained organizational evidence.

WindowsConsoleHumanVerifier proves successful credential authentication and returns a SID. It does not prove organizational administrative authority, intent beyond its exact prompt, an independent person's approval, hardware-backed authentication or MFA. SID allowlist membership alone does not prove the operator is independent of the requesting agent. The external custodian must attest that separation, and OS controls must enforce it. Never compare a caller-supplied agent label to a SID and claim that is sufficient.

## Required external assumptions

| Assumption/control | Owner and required evidence | Consequence if absent |
|---|---|---|
| Organization can appoint configuration authority and root custodian independently of agents | Existing authorized change/security process; verifiable record binding deployment and scope | No initial administrator or root can be accepted |
| Administrator SIDs are independently verified human accounts; agent/service tokens are distinct | Identity owner, account lifecycle/role evidence and token/ACL tests | No self-authorization guarantee; deployment blocked |
| Production CLI/build and Python import path cannot be modified by agents | Environment owner; trusted package/build digest, restricted installation, sanitized launch context | An altered verifier could invent approvals; deployment blocked |
| Root pin, authority document, epoch state, receipt key, database and bundles are inaccessible for agent writes | OS owner; ACL/ownership/reparse integrity report and denied-access tests | Authority and evidence are forgeable; deployment blocked |
| Host clock, Windows authentication subsystem and local filesystem durability are trusted | OS/storage owner; supported local-volume and recovery evidence | Time/identity/durability guarantees unavailable; deny admission |
| External change evidence and retained audit receipts have authentic issuer, scope and freshness | Change authority; signed/exported verifiable records, custody/retention policy | A typed ticket string cannot authorize changes |

This design does not make hostile local machine administrators, kernel/system compromise, stolen administrator credentials, the root custodian, or a malicious trusted installation safe. Such principals can replace binaries, disable triggers or alter storage. They remain outside AEO's protection boundary and require organizational controls, independent review, incident response and external retention. Local password memory cannot be guaranteed zeroized by assigning an empty Python string; never log or persist secrets.

## Threats and required responses

| Threat | Required response |
|---|---|
| Authenticated user lacks administrative membership; wrong SID/domain lookalike | Derive canonical SID from authenticated token; verify explicit external membership and scope; reject name-based equivalence |
| Design/execution/governance approver claims administrative authority | Lists are disjoint authority sources; no inheritance or fallback even if a SID happens to appear in multiple externally authorized lists |
| Agent edits JSON, invokes Python service directly or supplies fake verifier | Production code/keys/DB writers require separate protected identity; test injection cannot target production; fail deployment when isolation cannot be shown |
| Root substitution through workspace, env, CLI path or symlink | Protected fixed deployment anchor; signed document, key pin, ACL/reparse checks and deployment binding |
| Old signed root or revoked administrator reused | Monotonic epoch, bounded root freshness and expiry, external revocation distribution and consumption-time checks; deny when root unavailable |
| Prompt approves one change but files/rationale/restrictions change | Exact full-envelope challenge; immutable capture, post-authentication rehash and serialized stale comparison |
| Manifest lists altered files or path escape | Hash original manifest bytes and all listed files; reject traversal/reparse escapes; bind original base/root mapping and executable identities |
| Policy expands process/network/repository authority indirectly | Full typed diff with exact allowed paths; deny any guard-value change; static allowlisting does not certify command behavior |
| Generic approval replay or copying database to a different deployment | Unique decision/request nonce and activation key, deployment/DB/profile binding, one-time consumption, baseline generation and external restore checkpoint |
| Concurrent decisions/activations | Profile lock plus SQLite BEGIN IMMEDIATE and uniqueness/CAS constraints; single terminal decision and single successful consumption |
| Disk partial write/DB failure/crash after commit | Seal inactive bundle first; DB-only selection linearization; deterministic lookup by activation key; never infer success from file existence |
| Selected file altered or long-lived process keeps old permissions | Immutable storage ACLs/hash checks and generation admission lock; parse verified bytes once; no fallback or hot reload |
| Audit row edit, forged event, deletion or rollback | Existing audit update/delete guards plus new table guards; digest-verified evidence, signed receipt, hash chain and independently retained checkpoints |
| Denial of service, inaccessible root or unavailable DB | Deny new administrative/privileged admissions; preserve history; recovery belongs to external operators |

## Audit integrity contract and limits

Use the existing audit_events ledger as the single administrative event history with typed kinds config-admin.requested, decided, revoked, activation-attempt, activated, failed and recovery-required. Administrative events are deployment/profile scoped; their payload references immutable EvidenceBlob objects. Do not write a decision through an untyped legacy API or treat descriptive audit text as authority. Services validate schema, receipt, nonce, event linkage and external authorization before consumption.

Each admin-event payload binds its predecessor admin-event hash (per deployment/profile), envelope digest, generation, decision/activation ID, authority epoch and trusted build identity. Compute chain append under BEGIN IMMEDIATE so two writers cannot fork the predecessor. Each administrative event, including committed activation outcome, has a protected-writer signature over its canonical envelope hash and predecessor, using the deployment receipt key. Receipt signing is local and bounded; no network call in the transaction. Each state change and its audit event commit together. Failure to persist or sign denies the state change. Decision payloads are immutable; activation outcome is linked subsequent evidence, never an update to a signed decision.

Use existing append-only audit/EvidenceBlob guards and additive guards for activation history. Trigger/constraint tests cover ordinary application writes. A hash chain without an external anchor cannot detect a fully rewritten/truncated database by a privileged storage attacker. Signed receipts without external retention cannot establish that the newest receipt was not discarded. External custodian retention/checkpoints supply independent audit evidence and restore high-water marks. Retain the signed decision and committed activation outcome through the existing organizational process; no email/Slack delivery or new external service is implied here. Audit history is append-only within AEO; it is not physically immutable against the trusted OS/database administrator. The interval after the last external checkpoint remains a stated rollback-detection limit. If policy demands zero-window independent immutability, an external witness protocol is an additional design requirement before deployment.

Revocation blocks future consumption. For an already active selection, record any subsequent invalidation as new evidence and deny admissions until a new authorized disposition. Revocation is not an automatic compensating activation and cannot undo external effects. Root freshness imposes a bounded offline revocation delay; emergency host shutdown is external.

## Explicit exclusions

No producer-to-QA worktree inheritance, full-regression isolation redesign, live model execution activation, automatic approval-triggered continuation, application milestone recovery, deadline extension, generic multi-project orchestration, UI or HRMS work. No shell, network, deployment, merge, install or arbitrary process permission follows from this capability. No replacement autonomous run, changed original deadline or application acceptance.

No claims of live Windows authentication, native isolation certification, tests or external provisioning in this pass. Verification requirements are in ACCEPTANCE_CRITERIA.md.
