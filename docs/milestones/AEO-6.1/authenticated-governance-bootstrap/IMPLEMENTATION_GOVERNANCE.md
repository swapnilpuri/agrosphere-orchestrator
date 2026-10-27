# Implementation scope, prerequisites and governance gates

Status: PLANNING ONLY. Task IDs below are review labels, not registered/imported AEO tasks. No implementation or administrative permission is granted by this breakdown.

## Independent authority and missing provisioning evidence

The accountable organizational configuration/change authority, independent of AEO role membership and the requesting agent, must approve the administrator capability and its exact deployment boundary. The security/identity custodian provisions the external root and independently verified administrator SIDs. Authorized requirements/design reviewers approve the new technical scope. The same person may hold multiple organizational roles only if independently evidenced; no current SID is assigned any such role by this proposal.

Missing evidence:

- Identity and mandate of that configuration authority and root custodian, plus authentic scope/change reference for the new capability.
- Actual administrator SID/account ownership verification, administrative scope and explicit exclusion of agent/service identities. No initial SID is invented or prefilled.
- Provisioned issuer public-key pin, signed authority document, receipt-key identity, monotonic epoch checkpoint and root ownership/ACL integrity.
- Documented revocation freshness, key rotation, expired/unavailable-root handling and independent recovery ceremony.
- Trusted installed build, protected import path/launch environment, distinct process tokens, protected DB/bundle/key paths and denied-access evidence for agents.
- Approved deployment/profile/database binding and a tested local filesystem durability/quiescence protocol; external audit custody/retention and restore checkpoints.

No AEO command may provision these on its own authority. The first root must be supplied through the external process; an in-app approval cannot solve that initial trust dependency.

## Artifacts that can be reused

| Existing artifact/component | Reuse and limitation |
|---|---|
| Requirements decision 67c78c9f-387d-426b-8e89-64092bd48fd0, scope 8367e71ff015366e5c2493c11d199f3d9f7f3ad7bde902f385d10b6a5db96138 | Existing adjudication requirements only; not administrative authorization |
| Design decision 59196472-83fa-4d48-86ca-307559a1d00c, revision 4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066, bundle 989c1335f933a2505d60391360d96bf9a725a1cd008c284959d3f355bccdb8bf | Existing evidence-disposition design only; immutable reference, not permission for this capability |
| execution-bootstrap/REVIEW_MANIFEST.json and its six hashed files | Bounded inactive configuration/DAG/options/helper review inputs; missing admin selection/QA/validator controls remain missing |
| ADMIN_DECISION_REQUIRED.md, READINESS_REPORT.md, CONTINUATION_OUTCOME.md and CONTINUATION_BOUNDARY_EVIDENCE.json | Established stop, preservation evidence and exact runtime gaps; no repeated database rediscovery or claimed fresh authentication |
| HumanVerifier/WindowsConsoleHumanVerifier | Credential verification and exact challenge; external admin membership and OS separation must be added |
| StrictModel, Settings, load_yaml, RepositoryManifest, RoleRegistry, ExecutionPolicy | Typed validation and existing architecture; env resolution and mutable path reopening need governed-mode protection |
| AuditEvent, EvidenceBlob/canonical/digest/read_blob and orchestration_store.transaction | Existing audit/evidence and serialized transaction mechanisms, with explicit new administrative schema and guards |
| Existing negative/security tests | Fixtures and gate preservation, not proof that the new design works |

GovernanceRecord.milestone_id is a mandatory foreign key to milestones, and DesignDecision.case_id is tied to design_cases. There is no imported adjudication milestone. Do not create a placeholder milestone/case or relax those foreign keys to store global configuration authority. Reuse the existing AuditEvent ledger with typed administrative event envelopes and existing EvidenceBlob storage; do not route administrative decisions through quality.valid_approval, whose authority is governance_approvers. This preserves one audit/evidence system without pretending milestone governance authorizes administrator actions.

## Proposed data changes

One additive migration (provisional revision 0009; rebase the number if the repository changes) creates two deployment/profile-scoped operational tables and guards. It does not update legacy approvals or registered design/application records:

- ConfigurationHead: primary key deployment_id/profile_id; current bundle digest, generation, last activation ID and original-baseline digest. This is a mutable projection changed only with same-transaction audit evidence and compare-and-swap.
- ConfigActivation: immutable activation ID, deployment/profile, unique decision ID, unique deployment/idempotency key, from/to generation and digests, committed audit-event linkage and created_at. One row represents a committed selection, not an attempted partial filesystem operation. Update/delete triggers reject history mutation. Failed attempts are append-only events and never consume the decision.

Administrative requests, decisions, rejections/revocations, attempts and outcomes use existing AuditEvent plus digest-verified EvidenceBlob. Typed event schema and receipt verification are compulsory; arbitrary text in audit payloads is not authority. Each administrative request uses an unambiguous encoded deployment/profile/request identity as AuditEvent.entity_id. The migration adds partial unique indexes on that column for kind=config-admin.requested and kind=config-admin.decided, respectively: at most one request event and one terminal approve/reject event per request. Revocation uses separate append-only events; it cannot create another terminal decision. Check and append occur under BEGIN IMMEDIATE; constraints are the backstop for duplicate terminal decisions. ConfigActivation unique decision and idempotency constraints enforce one-time consumption. Existing unrelated audit kinds are untouched. Version-1 event validation and the predecessor chain described in SECURITY_THREAT_MODEL.md are mandatory; timestamp matching supplies no authority.

This is a real amendment to the earlier no-migration boundary. It requires separate authenticated technical review. Existing immutable approvals are not retroactively broadened. No migration, SQLite write or table creation is performed by this package.

## Exact proposed component/file change map

All source paths below are relative to agrosphere-orchestrator and describe future work only.

| Path | Proposed change |
|---|---|
| src/agrosphere_orchestrator/config/settings.py | Add governed immutable snapshot resolution/validation; protected production binding cannot come from env or arbitrary Settings values; preserve explicit disposable-test/legacy paths without production downgrade |
| src/agrosphere_orchestrator/configuration.py | Reuse typed loaders; add strict allowed-diff and full-baseline checks and captured-byte parsing |
| src/agrosphere_orchestrator/cli.py | Register config-admin Typer group and route protected existing command entry points through snapshot/admission checks |
| src/agrosphere_orchestrator/human_approval.py | Reuse existing verifier unchanged; new admin adapter calls it with exact envelope subject, with no test/actor injection exposed by production CLI |
| src/agrosphere_orchestrator/config_admin_models.py (new) | Strict authority/proposal/decision/event/bundle and restriction contracts |
| src/agrosphere_orchestrator/config_admin_authority.py (new) | Fixed external anchor, signature/ACL/epoch/revocation validation; operator token/identity checks and receipt signing adapter |
| src/agrosphere_orchestrator/config_admin.py (new) | Read-only inspect, authenticated terminal decisions/revocations, scoped preflight and activation orchestration |
| src/agrosphere_orchestrator/config_admin_store.py (new) | Two operational tables, typed existing audit/evidence append/query, chain verification and atomic selection/consumption |
| src/agrosphere_orchestrator/config_admin_bundle.py (new) | Immutable file staging/sealing/durable publishing, profile admission lock and restart verification |
| src/agrosphere_orchestrator/config_admin_cli.py (new) | CLI handlers, redacted inspection, exact review display, safe failures, no credential/actor flags |
| migrations/env.py | Import new metadata for authorized additive migration |
| migrations/versions/0009_config_admin.py (new, provisional) | Create only configuration-state tables/constraints and immutability guards; retain history on downgrade |
| src/agrosphere_orchestrator/execution_context.py | Use verified snapshot for role/repository/policy context and generation-bound admission |
| src/agrosphere_orchestrator/execution.py | Check governed snapshot/current generation before privileged dispatch; leave live_enabled guard and grants unchanged |
| src/agrosphere_orchestrator/orchestration.py | Bind planning/approval consumption to one governed snapshot and check generation; no new scheduler or automatic continuation |
| src/agrosphere_orchestrator/quality.py | Use selected immutable policy/repository/role inputs consistently; preserve existing governance authorities and categories |
| src/agrosphere_orchestrator/autonomous.py | Configuration/profile admission compatibility only; deny use of internal profile for application run; no lifecycle/deadline changes |
| src/agrosphere_orchestrator/autonomous_services.py | Same verified snapshot plumbing; no recovery or controller capability expansion |
| src/agrosphere_orchestrator/autonomous_simulation.py | Keep explicit disposable simulation isolated from production descriptor/root; never permit simulation to activate production state |
| tests/test_config_admin_authority.py (new) | Identity, external root, epoch, revocation, receipt and agent-isolation negatives |
| tests/test_config_admin_activation.py (new) | Exact-scope decisions, stale/replay/concurrency, filesystem/DB crash matrix, reader admission and compensation |
| tests/test_config_admin_cli.py (new) | Operator/agent separation, read-only behavior, exact prompt, no secret/actor injection |
| tests/test_config_admin_upgrade.py (new) | Additive schema upgrade and populated-state preservation |
| tests/test_configuration.py | Governed env/Settings bypass negatives while preserving allowed legacy/disposable resolution |
| tests/test_execution.py; tests/test_orchestration.py; tests/test_autonomous_security.py | Gate preservation and stale/profile isolation regression coverage |
| tests/conftest.py | Disposable deployment/root/key fixtures and new metadata only as needed; no production auth injection |
| docs/milestones/AEO-6.1/authenticated-governance-bootstrap/* | Versioned design, threat model, acceptance and implementation evidence; do not overwrite approved adjudication artifacts |

No modifications are proposed to state.py, persistence.py's legacy Approval contract, config/approvals.yaml, .env, active config YAML, approved-plan.json, the import helper, application source or old run data. Existing audit/canonical/transaction helpers are reused rather than replaced. The deployment installer/OS root provisioning is external operator work with exact paths supplied by its approved deployment record; this proposal cannot invent those external files or authorize their creation. Runtime source must be installed through that trusted deployment process before administrator use.

## Reviewable task breakdown

| ID | Deliverable | Dependency / completion evidence |
|---|---|---|
| GB-1 | Independently reviewed capability scope, trust-root ownership, deployment and external control contract | Gate G1/G2; authority and missing-evidence register resolved; no implementation |
| GB-2 | Typed canonical authority/decision/bundle contracts, exact diff rules and reviewed test vectors | Authenticated requirements/design approval; golden digests and scope-negative tests |
| GB-3 | Authority verification, protected entry point and receipt adapter | GB-2 plus operator-provisioned disposable test root; actual OS acceptance separately recorded |
| GB-4 | Additive configuration-state migration and existing audit/evidence integration | GB-2; populated-copy upgrade, immutable history and rollback/audit atomicity tests |
| GB-5 | Immutable bundle activation, admission locks, recovery and idempotency | GB-3/4; every crash window, concurrent contender and failed commit tested |
| GB-6 | Existing CLI and protected-setting consumers use one verified snapshot | GB-5; bypass, stale generation and internal/application profile separation verified |
| GB-7 | Independent security/regression review and operator deployment readiness report | All focused tests, safe required validation, actual exits, preservation evidence and real OS acceptance |

GB tasks describe only the new bootstrap capability. They are not additions to the frozen two-task adjudication DAG and cannot be imported under its earlier approval. Do not start GB-2 implementation merely because GB-1 documents exist.

## Governance gates

| Gate | Required approval/evidence | Effect |
|---|---|---|
| G0 — current work | User design-only request | Documentation/read-only inspection only; completed package grants no authority |
| G1 — independent scope decision | Existing organizational configuration/change authority reviews this package and design-boundary changes, designates custodian and provisioning requirements | First unresolved boundary; no implementation from ordinary chat approval |
| G2 — capability requirements/design | New or explicitly amended authenticated requirements and design decisions over exact bootstrap scope, migration, authority and consumer/security contracts; independent security review | Earlier adjudication approvals remain limited and unchanged |
| G3 — implementation admission | Independently authorized engineering configuration, supported import/plan readiness, actual authenticated plan approval, separate exact grants and operation gates | Enables only expressly authorized implementation; legacy code-write remains a separate blocker |
| G4 — release/deployment | Passing acceptance evidence, trusted build/package, externally provisioned root and OS separation, authorized migration/backup/rollback deployment decision | No autonomous agent enrollment or deployment |
| G5 — first configuration selection | Administrator authenticates exact decision/baseline/proposal/manifest; current external change authorization and trust root verify | Activation only of the five allowed surfaces with live_enabled=false; no task/run continuation |

A future implementation run must have its own authorization and cannot reuse or replace the original expired application run. Enabling an execution adapter, code-write integration, producer-QA validation, full-regression runtime profile and automatic continuation remain separately governed decisions. If any gate is unavailable, stop there without fabricating records, hashes of future artifacts, SIDs, grants or tests.

## Current readiness and recommended next action

Ready: reviewable documentation and design/test/task specifications. Not ready: implementation, trust-root provisioning, authenticated decisions, activation, plan import or execution. The exact missing administrative and external evidence is listed above; no actual identity is claimed.

Exactly one recommended next action: submit this package and its REVIEW_MANIFEST.json to the independently accountable organizational configuration/change authority for a recorded scope decision and designation of the external trust-root custodian/provisioning requirements. Stop before implementation or protected writes.
