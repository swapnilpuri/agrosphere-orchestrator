# Authenticated governance bootstrap — design proposal

Status: PROPOSED; NOT APPROVED, IMPLEMENTED, PROVISIONED OR ACTIVE. Prepared October 27, 2026 (America/Chicago). Documentation-only work authorized by the attached request. No administrator SID is selected. Examples describe future commands and have not been invoked.

## Review package and authorization boundary

Read this proposal with [Threat model](SECURITY_THREAT_MODEL.md), [Acceptance criteria](ACCEPTANCE_CRITERIA.md), and [Implementation and governance](IMPLEMENTATION_GOVERNANCE.md). REVIEW_MANIFEST.json hashes this new review package; it is not a decision or authorization token.

The independent organizational configuration/change authority must authorize this capability and designate its external trust-root custodian. Neither that authority nor a provisioning record has been independently identified in accessible evidence. Authority cannot be derived from the current Windows account, the design SID, execution/governance membership, the legacy local-user actor, a Markdown declaration, or an agent's request.

This is a new capability/change scope, not an extension implicitly authorized by AEO-6-ADJUDICATION approvals. Its approved architecture ADR61-4 and AEO61-COMPAT prohibit migrations; AEO61-AUTH concerns evidence dispositions, and AEO61-AUDIT reuses milestone-bound governance. This proposal introduces external administrative authorization, protected configuration loading, and an additive migration. Obtain new authenticated requirements/design approval for a separate bootstrap change (or an explicitly amended scope), and independent configuration-authority approval, before implementation. Do not alter the registered adjudication artifacts or reuse their approved DAG to conceal these changes.

## Established evidence reused

The latest diagnostic is [CONTINUATION_OUTCOME.md](../execution-bootstrap/CONTINUATION_OUTCOME.md), backed by CONTINUATION_BOUNDARY_EVIDENCE.json. It reports no independently verifiable administrator decision, no imported adjudication milestone or orchestration plan, empty execution/governance allowlists in file configuration, live_enabled=false, and no execution grants. Runtime environment overrides were not verified. Those findings are reused as historical observations, not a new live database audit.

Also reviewed: ADMIN_DECISION_REQUIRED.md, READINESS_REPORT.md and REVIEW_MANIFEST.json in execution-bootstrap; approved revision 4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066 architecture/service; current authentication, configuration, CLI, state, persistence, governance storage, execution, orchestration and security tests. Earlier 54-test success remains historical. No authentication, test, CLI, migration or implementation command ran in this design pass. Shell process launch failed before execution with Access denied; no elevation or alternate process launcher was attempted.

Existing configuration review-manifest byte SHA-256: 434c652c236d2bca7128f054f5d64e2a58b81a1ffc344c1f19d4af94fdfd61d7. Its draft artifacts remain inactive. They are review inputs, not evidence of authorization or certification of validator isolation.

## Minimal architecture

Extend the existing Python/Typer CLI with a local administrative command group and narrow services. Reuse strict Pydantic validation, safe YAML loading, WindowsConsoleHumanVerifier/LogonUserW identity verification, SQLAlchemy, SQLite BEGIN IMMEDIATE serialization, persistence.audit, EvidenceBlob and its digest verification. Introduce no web service, background worker, automatic continuation or new password store.

Five cooperating pieces are required:

1. An externally deployed authority verifier reads a signed administrator-authority document and a separately pinned organizational verification key from an OS-protected location outside the workspace. It never reads administrator authority from AEO_* variables or project configuration.
2. A typed, immutable change envelope binds one deployment/profile, exact baseline, proposed configuration, restricted semantic diff and all review artifacts.
3. The existing interactive Windows verifier authenticates an operator against the exact decision-envelope digest; the authority verifier separately authorizes that returned canonical SID.
4. A local activation service seals an immutable configuration bundle on disk, then atomically commits its authoritative selection, decision consumption and audit evidence in SQLite.
5. A governed settings resolver loads that selected bundle once into a verified immutable snapshot and checks its generation at privileged action boundaries. Protected settings cannot be replaced by environment values, mutable draft paths or old long-lived Settings objects.

Production installation, authority, database, bundle storage and receipt key must be protected from agent writes. The CLI used for administration must run a trusted installed build, not editable source from an agent worktree. An agent may propose documents and inspect redacted evidence but cannot execute a protected writer under an administrative token. Interactive TTY checks alone do not establish this isolation.

## External administrator trust root

The organizational security/configuration owner designates a custodian through its existing change process. That custodian provisions a machine/deployment descriptor, pinned public-key fingerprint, signed authority document, and least-privilege ACLs outside the repository. A location such as ProgramData/AgroSphere/AEO is illustrative only; no directory, account, key or SID is provisioned here. The descriptor fixes deployment ID, canonical DB identity, managed internal-profile ID, authority location and bundle root. Caller-supplied paths cannot substitute these anchors.

Authority document version 1 contains issuer, deployment ID, monotonically increasing authority epoch, issued/not-before/expiry UTC times, approved administrator canonical Windows SIDs and permitted administrative scope, revocations, authorized receipt-key identity and external provisioning/change reference. No wildcards, role inheritance, automatic Windows Administrators-group inference, current-account enrollment or enrollment CLI. The custodian independently verifies identity ownership and assigns scope. Design/execution/governance lists are never inputs to this decision.

Verify the issuer signature against the independently pinned key, deployment binding, schema, time bounds, current epoch and ACL/owner/reparse-point integrity before prompting, before recording a decision, before activation commit and at protected admission. Track the highest accepted epoch in protected host state; reinstallation/restore needs a custodian-provided external epoch checkpoint. Missing, expired, unreadable, malformed, rolled-back or unverifiable authority fails closed. No fallback to local-user or another approver list.

The custodian alone adds/removes administrators, rotates keys and publishes revocations through the external process. The deployment must coordinate authority publication with a host-wide authority read/write lock: decisions/activation/admission hold a shared authority lock through their authorization linearization point, and the trusted publisher takes its exclusive side. Lock order is authority lock, profile lock, SQLite writer lock; no authentication prompt holds these locks. A publisher that cannot honor this protocol requires quiesced administrative/admission processes during publication. Receipt of a remote revocation is bounded by the approved freshness window; it cannot be treated as instant local publication. Root rotation requires the currently trusted issuer's authorization plus independently verified deployment approval; root loss/compromise uses external recovery with operators quiesced, new independently verified pin and documented supersession. AEO cannot bootstrap its own root, recover by enrolling its operator, or use an old root after revocation. Offline authority is usable only until its approved short validity window ends; immediate offline revocation is not promised. Host policy must define refresh/expiry and emergency shutdown before deployment.

OS/organization controls supply administrator identity lifecycle, key custody, machine clock, executable trust, ACL enforcement, process-token separation, deployment ownership, trusted backups and external change evidence. These are prerequisites, not protections AEO can infer or create for itself. See the threat model for residual limits.

## Exact change envelope and decision contract

Use quality_store.canonical/digest conventions: versioned strict JSON, sorted object keys, compact separators, ensure_ascii=true, SHA-256 over UTF-8. Reject duplicate keys and nonfinite numbers before parsing/canonicalizing; preserve list order when meaningful. No unspecified serialization. Byte SHA-256 is separately recorded for every external file, including each review manifest and each file it lists. Pin original manifest-relative bases; copying files must not change relative path meaning.

The immutable proposal includes deployment/database identity, profile ID, schema version, request ID/nonce, requester identity class, baseline generation, baseline full effective-configuration digest, proposed full effective-configuration digest, raw file digests, canonical resolved repository ID/root mapping, tool/runtime versions and exact semantic diff. Include protected guard values outside the allowed diff so changes to limits, operations, approval policy or network denial are detected. Bind explicit applicability to internal adjudication preparation; never apply this profile to the original application run.

A decision is an immutable typed envelope stored as an EvidenceBlob and referenced by a namespaced audit event. Fields:

| Field | Contract |
|---|---|
| schema_version, decision_id, request_id, nonce | Unique server-generated identity; one terminal decision per request |
| deployment_id, database_identity, profile_id | Fixed external deployment binding; no cross-profile/database use |
| authenticated_admin_sid | Only from successful Windows authentication; canonical SID, never a claimed actor flag |
| authentication evidence | Method, authentication time, exact challenge digest, trusted build identity; no password/token/hash |
| authority evidence | Issuer/key fingerprint, authority document digest, epoch, permitted scope and provisioning reference |
| decision_type and scope | APPROVE_CONFIG, REJECT_CONFIG or REVOKE_DECISION; exact allowed field paths, old/new values, repository and command bounds |
| baseline/proposed digests | Full effective snapshots, baseline generation and immutable file/root-mapping digests |
| review evidence | Original configuration-review-manifest digest, this capability-review manifest digest, and all transitive artifact digests |
| rationale and restrictions | Required text plus typed enforceable conditions; unsupported conditions block activation |
| external authorization | Verifiable change ID, issuer, authorized scope, evidence digest and expiry; an unchecked ticket string is insufficient |
| time metadata | created_at, not_before, expires_at in UTC; proposed maximum 900 seconds, bounded 1..3600 subject to independent approval |
| immutable audit linkage | EvidenceBlob digest, linked audit event ID, prior admin-event hash, protected writer receipt/key identity |
| activation outcome | Derived from linked append-only activation/result events; never edit the original decision |

Bind decision type, scope, rationale, restrictions, expiry, external reference, authority epoch, baseline/proposal and manifest digests into the human confirmation subject. Show the complete diff and review evidence before requiring an exact phrase such as APPROVED config-admin:<deployment>:<envelope-sha256>. Authenticate only after confirmation, then reconstruct and revalidate the exact envelope inside the serialized write transaction. The nonce is fixed before the prompt; authentication is not a reusable permission to approve arbitrary later content.

The protected writer signs a receipt over the decision-envelope digest, authenticated SID and audit-chain predecessor with an OS-protected installation key using an organization-approved algorithm. This receipt attests the trusted local verifier's result; it is not a personal administrator digital signature or independent organizational change authorization. Key fingerprint/algorithm and verifier build are deployment evidence. No mock verifier or caller-supplied SID may reach production writers.

Reject is terminal for that request. Revocation appends a new authenticated event referencing the old decision; no historical deletion. Expiration is derived from immutable time bounds and cannot be renewed in place. A rejected/revoked/expired proposal needs a new explicitly reviewed change reference and new authentication; changing a timestamp alone cannot override a rejection. Revocation of the deciding administrator before consumption invalidates the decision. Revocation after activation blocks further admission under that selection pending independently authorized reassessment; it does not erase history or silently restore permissions.

## Allowed configuration surface

| Supported change | Enforced boundary |
|---|---|
| Execution approver allowlist | Exact independently selected canonical SID list; no wildcard, agent identity, design/governance inheritance or administrative-authority change |
| Developer/QA repository permissions | Only allowed_repositories for developer and qa-engineer; all other role fields and all other roles identical to baseline |
| Repository manifest selection | Exact reviewed immutable manifest bytes plus resolved roots; initial profile limited to agrosphere-orchestrator; no application manifest rewrite |
| Validation command allowlist | Exact command IDs, full argv, executable identity/digest, bounded timeout and canonical read roots; no interpolation, shells or implicit PATH resolution |
| Execution policy selection | Exact reviewed immutable policy; only the explicitly approved command diff; live_enabled must remain false; preserve resource, tracing and pricing settings |

No arbitrary settings setter. Approval policy, administrative membership, DB URL, workspace root, transport, model, remote-write settings, role operations/instructions, network/process capabilities, live opt-in and run budgets are outside scope. Compare complete typed baseline/proposed configurations; reject extra keys, duplicate IDs, alias/reparse/path escapes, ambiguous roots and all undeclared changes. A request to widen another boundary requires a separately governed design. Command allowlisting alone cannot certify executable behavior; script, interpreter and relevant dependency identities must be bound, and known unsafe regression semantics remain blocked.

## Decision and activation lifecycle

DRAFT -> REVIEWED/PENDING -> APPROVED | REJECTED; APPROVED -> ACTIVATED | EXPIRED | REVOKED | STALE. These are derived outcomes over immutable records. An activation attempt has a unique idempotency key and ends COMMITTED, FAILED or RECOVERY_REQUIRED. A precommit crash may leave only an inactive sealed bundle. No automatic retry may create a different authorization.

Preflight is read-only: verify external authority/change evidence, current baseline/generation, all manifests and files, strict schemas and allowed diff, enforcement of restrictions, storage/ACL capabilities, installed-build identity, quiescence and no unresolved prior activation. Resolve paths using original bases and capture bytes once; rehash files and executable dependencies again before commit. Do not execute a validation command as an administrative preflight. The current full-regression and producer-QA gaps remain separate blockers.

The decision is recorded with its audit event in one BEGIN IMMEDIATE transaction after human authentication and authority recheck. No approval can be inferred from an unfinished prompt. No interactive wait or network request occurs while holding a DB writer transaction. External change evidence must already be locally verifiable and still fresh.

### Filesystem/SQLite consistency protocol

Do not attempt a multi-file replace of active YAML followed by a database commit. There is no shared filesystem/SQLite transaction. Instead:

1. Under an exclusive, host-enforced profile lock, require no active consumers or execution claims using this internal profile. Stage the exact approved full bundle in a private same-volume temporary directory. Write and durably flush each file; validate hashes, canonical semantics and absolute-root mapping. Seal ACLs against agent/runtime modification and publish under its content digest without overwriting an existing bundle. Verify any existing bundle is byte-identical. Failure to flush, seal, publish or verify ends before selection.
2. The bundle directory is immutable storage, not an active pointer. Do not edit .env or config/*.yaml. No filesystem active symlink, current.json or process-environment pointer is authoritative. The database ConfigurationHead row is the only active selection for this internal profile.
3. In BEGIN IMMEDIATE, recheck authority epoch/revocation/time, exact decision and external change evidence, baseline generation/digest, complete proposed bytes, quiescence and unique consumption. Insert ConfigActivation with unique decision_id and idempotency_key; compare-and-swap ConfigurationHead to the sealed digest with generation+1; append activation result and audit events in the same transaction. A DB commit failure leaves the former head effective and an inactive bundle. SQLite commit is the sole selection linearization point.
4. On restart or uncertain commit acknowledgement, query the fixed deployment DB and unique activation key. If committed and matching, return that recorded outcome; do not consume again or move the head again. If absent, the old head remains active; retry only if authority, expiry, baseline and all original checks still pass. Reuse the sealed identical bundle. Conflicting identity/content fails. Never guess from files or a missing CLI response.
5. Every protected reader loads the selected generation and bundle, verifies all hashes/ACLs/authority and the linked approved decision/activation, then uses the exact parsed bytes in memory. It must not reopen mutable review paths after verification. Missing/corrupt selected files, uncertain storage durability, unsupported schema or broken audit linkage block admission; never fall back to legacy YAML or another bundle.

The initial legacy baseline is snapshotted and verified without changing it; first selection is also a decision-bound activation. A deployment descriptor must explicitly place only this internal profile into governed mode. Agents cannot disable that mode through environment or Settings constructor values in production. Reject conflicting protected AEO_* / .env values and DB/profile redirection. Existing application configuration stays separate and the governed internal profile is never admitted for application discovery or the old run.

Profile activation requires quiescence for this minimal release. All consumers take the same profile admission lock, validate the head generation immediately before privileged work, and pin one snapshot for that operation. Activation cannot race with such an operation; lock-order policy is profile lock before SQLite writer lock. A restart releases OS locks, but persisted uncertain execution/activation evidence still blocks admission until reconciliation; no lease-timeout stealing. This avoids silently keeping broader permissions through a stale Settings object. Future hot reload or distributed readers are outside scope.

No reader can observe a partly written selected bundle: selection occurs after sealing; before commit readers see the old head, after commit they see the complete new bundle or fail closed. Physical media loss after a successful durable flush remains a storage failure and causes denial. Windows flush/rename/ACL behavior must be proven by fault tests on the chosen local filesystem; no distributed filesystem guarantee is assumed.

Rollback is a new authenticated compensating activation from the current generation to an exact retained bundle, with a new scope/decision/expiry and audit evidence. No pointer restoration outside a transaction, deletion of consumption records, or automatic re-enabling of former permissions. Failed staging can be abandoned; cleanup of unreferenced bundles is a separately controlled maintenance operation and never deletes evidence or the current/prior referenced bundles. Backups restore DB and referenced bundles together under external recovery controls.

## CLI/API contract (proposed only)

Extend the existing CLI as config-admin. Illustrative syntax below is documentation, not an available or executed command; angle-bracket values are placeholders.

~~~text
python -m agrosphere_orchestrator.cli config-admin pending --profile <profile>
python -m agrosphere_orchestrator.cli config-admin inspect --proposal <proposal.json>
python -m agrosphere_orchestrator.cli config-admin verify-authority --profile <profile>
python -m agrosphere_orchestrator.cli config-admin decide --proposal <proposal.json> --decision approve --rationale <text> --change-reference <reference> --expires-seconds 900
python -m agrosphere_orchestrator.cli config-admin decide --proposal <proposal.json> --decision reject --rationale <text> --change-reference <reference>
python -m agrosphere_orchestrator.cli config-admin revoke --decision <id> --rationale <text> --change-reference <reference>
python -m agrosphere_orchestrator.cli config-admin activate --decision <id> --idempotency-key <key>
python -m agrosphere_orchestrator.cli config-admin history --profile <profile> --verify
~~~

pending/inspect/history are genuinely read-only and do not initialize a DB or append evidence. pending lists proposal envelopes from the fixed deployment proposal inbox and correlates their request IDs with existing events; presence in that inbox grants no authority. Operators may copy agent-prepared review inputs there through the external process. First decision recording captures the request and terminal decision atomically; no placeholder milestone or separate request-registration command is needed. Agents may use redacted inspection and construct inactive proposal files in permitted documentation space. verify-authority performs interactive authentication and reports current membership but grants no reusable approval token. It is operator-only, as are decide/revoke/activate. Activation reauthenticates the invoking operator against the exact decision/proposal and activation key, verifies current external administrative authority, and cannot widen the earlier decision. No --actor, password argument, supplied SID assertion, approval-by-environment or noninteractive approve mode.

Internal Python services accept trusted verifier/authority adapters behind interfaces. Production construction comes only from the protected installed entry point; test injection is confined to disposable deployment fixtures. Hiding commands is not a security boundary: OS identities/ACLs must prevent agent processes from invoking any protected writer or modifying production code/DB/keys. If the same effective Windows token can do both, this design is not deployment-ready.

## Legacy independent code-write gate

state.record_approval accepts a claimed actor checked against ApprovalPolicy; state.transition independently requires that task operation's approval. Keep that gate and config/approvals.yaml unchanged. A configuration decision, plan approval or execution grant must not synthesize an Approval row, exempt code-write, or supply local-user.

A future separately approved integration could authenticate an operation decision over exact task/spec, repository/head, file scope, plan/request digests, operation, expiry and rationale, then let the legacy gate verify that evidence plus current authority/revocation at transition. This needs its own requirements/design and migration/compatibility review if necessary. It is excluded from this bootstrap implementation and remains an execution blocker.

## Remaining blockers and one next action

Missing: independently identified configuration authority/custodian; external change authorization for this capability; actual administrator SID ownership/provisioning evidence; key pins and epoch/revocation/recovery controls; OS process/ACL and trusted-build evidence; new authenticated capability requirements/design approval; certified transactional durability/admission tests. Process launch is also unavailable for eventual implementation checks. None can be manufactured by this proposal.

The separate execution blockers remain: full-regression isolation, exact Developer-output QA verification, inherited code-write authorization, approved plan/import readiness, live opt-in and exact execution grants. The original application run remains outside scope and its expired deadline is not changed.

Exactly one recommended next action: submit this hashed review package to the independently accountable organizational configuration/change authority for a recorded scope decision and designation of the external trust-root custodian/provisioning requirements. This is the first genuine authorization boundary; implementation and provisioning stop here.
