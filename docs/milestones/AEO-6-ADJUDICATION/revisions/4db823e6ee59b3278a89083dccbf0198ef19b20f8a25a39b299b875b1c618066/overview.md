# AEO-6-ADJUDICATION: overview (design)

Scope: 8367e71ff015366e5c2493c11d199f3d9f7f3ad7bde902f385d10b6a5db96138
Requirements: AEO61-DISPOSITION, AEO61-PROVENANCE, AEO61-AUTH, AEO61-AUDIT, AEO61-NEGATIVE, AEO61-IDEMPOTENT, AEO61-DISCOVERY, AEO61-CONTROLLER, AEO61-BOUNDARIES, AEO61-COMPAT, AEO61-OPERATIONS, AEO61-VERIFICATION

## Milestone overview

This is a proposed technical design under approved requirements scope 8367e71ff015366e5c2493c11d199f3d9f7f3ad7bde902f385d10b6a5db96138. It grants no implementation, evidence disposition, milestone acceptance or execution authority.

## What will be built

Versioned evidence-disposition subjects and category-specific existing-governance validation, exact human CLI review, recovery relationship integration and actionable controller checkpoints.

## Why it is needed

The original evidence remains valid historical context but currently blocks discovery without an authenticated way to establish its exact relationship.

## Platform fit

AEO-1 through AEO-6 services, durable run and registered task DAG remain the orchestration system. No new run, scheduler, approval framework or watcher.

## Component responsibilities

Governance owns authenticated decisions; discovery owns observed provenance; classifier owns conservative relationships; controller owns bounded continuation; humans retain product and approval decisions.

## Implementation sequence

Requirements approval verified. Generate and validate this revision, then stop for authenticated design approval. Later implementation-ready/plan/exact execution grants must independently pass; the developer task precedes the QA task.

## Expected outcomes

Approved dispositions can remove only their exact relationship conflicts. Milestone 1B remains PARTIAL without fresh acceptance. Milestone 2 product/performance gates, roadmap and expiry remain independent.

## User-facing documentation

The versioned AUTONOMOUS_OPERATIONS_GUIDE.md in this review package lists available CLI commands and distinguishes proposed evidence commands. Operator approval is followed by explicit autonomous resume only once every independent blocker is resolved. No automatic restart currently exists.

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
