# AEO-6-ADJUDICATION: service (design)

Scope: 8367e71ff015366e5c2493c11d199f3d9f7f3ad7bde902f385d10b6a5db96138
Requirements: AEO61-DISPOSITION, AEO61-PROVENANCE, AEO61-AUTH, AEO61-AUDIT, AEO61-NEGATIVE, AEO61-IDEMPOTENT, AEO61-DISCOVERY, AEO61-CONTROLLER, AEO61-BOUNDARIES, AEO61-COMPAT, AEO61-OPERATIONS, AEO61-VERIFICATION

## Technical design

The subject schema is EvidenceDispositionSubjectV1: version=1; project; exact sorted affected_milestones; relationship_type=historical-reference; source and referenced observations; original and supporting references; proposed_effect=non-blocking-historical-observation; manifest byte SHA-256 plus canonical resolved root/id mapping digest; classifier_version; disposition_policy_version/digest; stable observation_digest. Each evidence reference contains repository ID, repo-relative path, whole-file SHA-256, line start/end, excerpt hash, observed HEAD, origin commit when independently known or explicit null with reason, and evidence kind (original/report quotation/fixture). Record captured_at in the request envelope, outside identity, so repeated identical collection is idempotent. A missing origin commit may be explicitly known-missing without inventing it; missing current file/hash/line, uncertain source relationship or ambiguous origin mapping makes approval inapplicable. Preserve captured content in the existing immutable blob so history remains inspectable after files change.

Applicability requires exact manifest/root mapping, evidence bytes/lines, observation identity, policy/version, current authorized SID, unexpired request and latest eligible decision. No record is authoritative merely because it includes disposition fields. An approved historical-reference allows only the named relationship to stop contributing a conflict; it does not suppress all claims in a document, other milestone evidence, or acceptance checks. Changed evidence invalidates that applicability; old records remain visible.

## Domain model

Request identity = SHA-256(canonical(subject)); use action evidence-disposition:<subject digest>. Store requesting actor separately from authorized deciding SID. A decision contains request ID, subject digest, disposition, rationale, supporting-reference digests, authenticated actor SID, timestamp, manifest/policy/classifier versions and correlation/run IDs for audit only. The same evidence relationship is reusable across reports; the run ID is not a substitute for evidence identity.

Decision state: pending -> approved | rejected | unresolved. Proposed CLI unresolved maps to an explicit immutable decision value scoped to governance.EVIDENCE_DISPOSITION only. Reject and unresolved both retain the checkpoint; unresolved means request more evidence, not approval. A terminal identical decision returns its existing ID only when every authenticated field matches; conflicting repeat is denied. Rejection/unresolved cannot be superseded by renewing expiry or changing only rationale/timestamp/requester. New substantive provenance/evidence or policy version is necessary for a revised subject. Approved -> revoked appends a revocation; revocation is sticky for that subject. Revocation is permitted after request expiry to preserve audit intent, but no expired request can grant authority. Every evaluation checks current authority and expiry.

## Interfaces

Proposed commands (unavailable until implementation): evidence list --run <run>; evidence inspect <request-id>; evidence request --run <run> --milestone 1B --subject <reviewed-subject.json> --reason <text> --expires-seconds <bounded>; evidence decide <request-id> --disposition approved|rejected|unresolved|revoked --reason <text>. Listing/inspection are read-only; requesting creates no authority and cannot decide. Derive the request subject from fresh exact-root discovery and validate any submitted file matches it; never trust arbitrary JSON to assert provenance. Reuse existing 1..86400 second request bounds, default 900, without extending decision validity. Print the precise confirmation subject including request/subject/disposition/rationale digest and full review details before Windows authentication. No actor flag, password argument or noninteractive approval mode.

Extend approvals inspect/pending so this category is visible. Existing approvals decide routes this category through the same validator and cannot bypass exact rationale/disposition confirmation; other categories remain compatible. Proposed interfaces are design commitments only; no command is claimed operational.

## Persistence

Reuse GovernanceRecord append-only request/decision/revocation/application-reference events and existing blob() integrity checks. Reuse DesignDecision(kind=governance.EVIDENCE_DISPOSITION,subject=request.id), not design requirements/design decisions. Record decision and audit in one transaction; no parallel evidence store. Before insertion acquire the established serialized writer transaction, requery identical requests/final decisions and check fresh context. Concurrent identical requests converge to one request; competing final decisions allow one and reject the other. On rollback neither decision nor audit persists. Verify SQLite transaction behavior in concurrency tests; do not assume an ordinary deferred read transaction serializes duplicate checks.

Restart reconstructs state from immutable records, recomputes evidence applicability and recollects exactly the 12 application roots. Original report, snapshot, run request/limits, counters and prior approvals are never changed. Snapshot disposition metadata is explanatory, not independently trusted. Legacy snapshots lacking versioned metadata retain conservative classification. No Alembic change; migration version and existing rows must remain identical.

## Security

Use WindowsConsoleHumanVerifier for exact subject and decision; bind rationale digest into its subject as well. Before prompting and again before transactional commit, read current Settings governance SID allowlist and category policy; reject any removed actor, requesting actor or noncanonical SID. Revalidate bytes/root containment after authentication and before classification; classifier authority is computed from a single fresh captured observation set, never supplied by exported text. Record a distinct structured invalidation reason on changed input; do not mutate past decisions. Approval of this design is not an evidence decision.

## Developer documentation

Preserve the registered DAG: adjudication-integration (developer/code-write), then verification (qa-engineer/validate). Serial documentation roles are business-analyst, solution-architect, technical-writer through the existing generate_design adapter; rule architecture reviewer is a deterministic check, not a spawned agent or human approval. After design approval use milestone implementation-ready, milestone plan/approve-plan, milestone prepare and exact agent execution grants according to the existing CLI and reports; do not run them now.

Focused security/regression matrix: approve/reject/unresolved/revoke; empty/removed/unauthorized/self SID; rationale/disposition swap during prompt; changed evidence/manifest/HEAD/root and line; explicit known-missing commit versus ambiguous provenance; fixture/export quotation cross-repo identity; duplicate requests and simultaneous conflicting decisions; TTL rollover, sticky negative outcomes and unknown versions; rollback audit atomicity; restart re-collection; exact historical 1A/1B relationship with an unrelated contradiction retained; no accepted/completed promotion; same-run checkpoint recovery with original request, deadline and budgets preserved; 12-root restriction; default legacy governance behavior. Use disposable databases/Git fixtures for decision and concurrency tests, identify verifier mocks clearly. Run focused suites, then .venv/Scripts/python.exe scripts/validate.py after authorized source changes. Capture raw exits and preserve prior validation reports. No live model/provider, application benchmark or build is implied.

## Registered requirements and criteria

AEO61-DISPOSITION: Represent explicit evidence dispositions separately from milestone acceptance.
- Define immutable evidence-disposition requests and decisions with approve, reject and unresolved/request-more-evidence outcomes, exact affected milestone(s), rationale and supporting references.
- No approved disposition changes PARTIAL into ACCEPTED/COMPLETED or supplies verified acceptance criteria.
AEO61-PROVENANCE: Bind decisions to authenticated provenance and immutable original evidence.
- Canonical subject includes original repository/path/line/hash/commit-or-known-missing provenance, supporting evidence hashes, captured observation and manifest identity.
- Preserve original reports, old snapshots and their history; missing/ambiguous provenance cannot be silently filled in or overridden by newest timestamp.
AEO61-AUTH: Reuse existing verified Windows identity and authorization for evidence decisions.
- Reuse HumanVerifier/WindowsConsoleHumanVerifier and configured governance SID authorization; agent/self-approval or empty allowlist fails closed.
- Exact subject/rationale/disposition is confirmed; recheck scope and authorized identity after authentication; existing design approvals are not evidence-disposition approvals.
AEO61-AUDIT: Reuse existing approval entities/services and transactional append-only audit.
- Extend existing governance contracts and category-specific context validation; no independent approval store, authentication subsystem or direct SQLite approval changes.
- Decision and audit writes share one transaction; include actor SID, time, subject digest, scope, supporting references and policy/version identity.
AEO61-NEGATIVE: Fail closed on rejected, unresolved, revoked, expired and changed evidence.
- Rejection/request-more-evidence retains the unresolved checkpoint; no approval consumption from descriptive metadata.
- Subject mismatch, changed manifest/evidence, unauthorized actor or invalid version invalidates applicability while preserving all prior records.
AEO61-IDEMPOTENT: Prevent duplicate decisions and support restart-safe observation.
- Repeated identical request/observation is idempotent; duplicate final decisions cannot replay or supersede a rejection without a legitimate revised subject.
- Decision history remains immutable; current authority and expiry/revocation policy are rechecked on every consumption.
AEO61-DISCOVERY: Integrate valid scoped decisions into fresh manifest-bound recovery.
- Collect exactly the approved 12 application roots; bind application manifest digest; fixtures and exported quotations do not become independent implementation evidence.
- A valid decision resolves only its exact historical relationship; genuine unrelated contradictions remain blocking and all original evidence remains visible.
AEO61-CONTROLLER: Present actionable human checkpoints through the existing controller and CLI.
- Existing RECONCILING/checkpoint machinery presents the exact review package and applicable supported decision command once implemented.
- After authorized decisions and all other gates pass, the same run can be resumed using existing continuation semantics; independent work proceeds only where current dependency/security rules permit.
AEO61-BOUNDARIES: Keep adjudication, design, quality, execution and delivery authority separate.
- No application development, 3B start, execution eligibility, publication, merge or deployment follows from evidence reconciliation alone.
- Do not recreate runs, reset counters, edit original run requests/limits, alter previous approvals, or substitute historical tests for fresh acceptance.
AEO61-COMPAT: Preserve version compatibility and migration safety.
- Prefer existing GovernanceRecord/DesignDecision/audit persistence; no migrations or rewriting old snapshots/decisions in this scope.
- Legacy observations without new decision metadata remain readable and conservative; unsupported decision versions fail closed.
AEO61-OPERATIONS: Document the single existing CLI entry point and remaining operating limits.
- Use autonomous status/report/validate for read-only inspection, authenticated approval commands for humans and autonomous resume for gated continuation.
- Do not add a watchdog or parallel scheduler. Report expired immutable run budgets as blockers; extending a deadline requires separate governed policy and is not authorized by this scope.
- Current empty governance allowlist, absent approved roadmap and missing renderer are explicit prerequisites, never silently configured.
AEO61-VERIFICATION: Verify real versus simulated evidence and all applicable regressions after authorization.
- Cover approval/reject/unresolved, cross-repository provenance, original evidence preservation, duplicates, fresh discovery, restart, existing-run preservation, M2 blockers and 12-root restriction.
- Run focused suites and established scripts/validate.py after authorized source changes; identify mocks and real local checks; no model/provider live execution or application changes implied.

## Verified context references

- agrosphere-orchestrator/src/agrosphere_orchestrator/recovery_discovery.py sha256=7c7a6e4c99ba580febabded363e2a22b250e57e07af5253992675730507a8055 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/recovery_models.py sha256=2f20ebf805efc01e1df524921e49eaed0c36f0527fede1579ec617c640621cb8 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/human_approval.py sha256=edb65b1c4c53e62fd28b5b763141fb895beaf4a3b4bafe32bf49ec41a3e206d9 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/quality.py sha256=2a3fce5316bf38aacdadf2b011a70bf210f9348851b0fcb11da3e64f6fddda56 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/design.py sha256=1330049444195c4f2ca64cc7f0f28e76a386251200ffb05104f374ddcdfe5900 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/quality_models.py sha256=c41a7084b3874d0c39e51d95ae7c181519eeaa8f976aa139268a935399474ddd HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/autonomous.py sha256=dc5582c6ac16022e233b643e33187af0b51a37d0a3580dff768571a2378dab4d HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/autonomous_services.py sha256=3e8c83ae0defb452ec7caf224d7267276913baa55faaa256ad2a4909623c9e33 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/autonomous_cli.py sha256=1487b01d6e22604c3b8214141ffdc871a8e3729d0801c3775389826fc7e5ee18 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/recovery.py sha256=e36d107b314190a33d5a85f3f721d91c5c3efe7636b4cb51de0c2e401d2d54d2 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/persistence.py sha256=a35cf95d2f30ed6d5d9d67836a4b82f4eaf5a5ed27585e83ca6900429972db84 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/src/agrosphere_orchestrator/config/settings.py sha256=bc5c9faacb9acd6a543ae3dd93e276147dc04b83e5e1a6871af437dc16252b08 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/docs/milestones/AEO-6/evidence/discovery-reconciliation/MILESTONE_1B_FORENSIC_REPORT.md sha256=781e03ad22b79a37fd96e168136a48f6e25d56fd1ec881489705ef522ebc292c HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/docs/milestones/AEO-6/evidence/discovery-reconciliation/MILESTONE_1B_ADJUDICATION_MATRIX.md sha256=9993d67658c4ea6ecf65b0f047772efe33e7a261d7a7af227a4237dc4e1196c2 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/docs/milestones/AEO-6/evidence/discovery-reconciliation/MILESTONE_1B_DECISION_PACKAGE.json sha256=19b90ae4457fbb3c9d5004868bd866818c03c2840ce85d5d79fe9ee155d4fdf2 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/docs/milestones/AEO-6/evidence/discovery-reconciliation/MILESTONE_1B_RECOVERY_VERIFICATION.md sha256=9cadc5eaedecd210fdd8de7ec35adb57007bec63b4f7d0252fefd5258a63aaa8 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/docs/milestones/AEO-6.1/preparation-20261027T005025Z/00-user-request.md sha256=6b5ae12ff0f95ebc01a8c8bc0c169382e5c70143febf98fc572be5677fa01a7a HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/docs/milestones/AEO-6.1/preparation-20261027T005025Z/01-capability-and-boundary-assessment.md sha256=b1649651a11e98289558993127eb432f15278d2f4586a03ee9ca90f17e01e305 HEAD=d57d6101439b29b89fe962d78d4a131398247c75
- agrosphere-orchestrator/docs/milestones/AEO-6.1/preparation-20261027T005025Z/AUTONOMOUS_OPERATIONS_GUIDE.md sha256=e1d750409c39eedfc2005633b8c805dbbc956e9d279ffebe9003dd7f4af8f674 HEAD=d57d6101439b29b89fe962d78d4a131398247c75

## Related artifacts

- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/business.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/architecture.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/service.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/diagrams/adjudication-components.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/diagrams/adjudication-components.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/diagrams/adjudication-state.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/diagrams/adjudication-state.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/diagrams/adjudication-sequence.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/diagrams/adjudication-sequence.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/overview.md)
