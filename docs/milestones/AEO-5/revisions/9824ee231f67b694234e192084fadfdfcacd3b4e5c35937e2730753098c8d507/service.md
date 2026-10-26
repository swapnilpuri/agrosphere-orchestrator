# AEO-5: service (design)

Scope: 22e7ab696621e4f7b779cf49ac2cd04bbfe5eeb58864ca9a372d69df755b0edd
Requirements: AEO5-AUTH, AEO5-BRANCH, AEO5-PR, AEO5-COORD, AEO5-CI, AEO5-REVIEW, AEO5-APPROVAL, AEO5-DURABLE, AEO5-RECOVERY, AEO5-EVIDENCE, AEO5-CLI, AEO5-BOUNDARY

## Technical design

# AEO-5 architecture proposal

This is a reviewable design, not an implementation claim. The user specifications in 00-original-specification.md and 00-recovery-request.md are authoritative scope inputs. Only agrosphere-orchestrator changes. Shared service APIs/events and application runtime behavior are unaffected.

## Ports and configuration

Proposed github_models.py holds strict Pydantic repository identity, principal, branch, PR, check, review, policy and error models. github_provider.py defines a typed protocol and GitHubCliAdapter with an injected subprocess runner for tests. Commands use fixed argument arrays, explicit cwd, explicit API method, bounded timeouts, bounded response size and sanitized errors. Validate github.com remote owner/name, IDs, SHA lengths and Git refs before use. Reject URL userinfo, arbitrary hosts, option-like branch names, traversal and untrusted executable selection. Confirm fetch and push remote identity agree with the configured allowlist.

Settings gains centralized provider, gh executable, operation timeout, bounded read retries/poll interval/duration, repository/base allowlists, branch prefix, redaction and remote writes disabled by default. Credentials remain with existing gh authentication. User/API identity and access are observed before writes; authentication never grants publishing approval. No merge/deploy/write-workflow capability is present in the port.

## Delivery domain

Proposed delivery_models.py defines a milestone manifest with uniquely named units, one repository/task per unit, DAG dependencies, expected base and head SHA, target/head branches and remote identity. Planned units reference existing milestone/task records. Validate duplicate IDs, cycles, missing tasks, repository mismatches and allowed target branches before persistence. Unit policy/CI/review snapshots evolve independently from operational state.

Proposed delivery_store.py adds DeliveryRun, DeliveryUnit and DeliveryOperation projections with stable IDs and uniqueness constraints on milestone/unit and operation reconciliation identity. Append immutable snapshots/events and raw result hashes through quality_store rather than retaining mutable-only audit evidence. Event/state updates and audit records share orchestration_store.transaction. Alembic 0007 adds tables/triggers/indexes without dropping old tables. Reject destructive downgrade. Existing DesignDecision and governance authority remain authoritative.

Proposed delivery.py coordinates branch preparation, publishing, observation, readiness and reports. Reuse execution_workspace's isolated worktree/preservation checks and orchestration_store resource leases for repository write exclusion. Each unit holds the same repository:<id> write resource as execution scheduling. No remote network call holds a SQLite write transaction. In-progress operation and ownership persist before releasing the transaction for I/O; uncertain completion retains a reconciliation block rather than freeing a conflicting write.

## Mutation protocol

Recheck exact source revision, baseline, remote, policy, authorization and AEO-4 quality before each step. Persist operation intent and preconditions transactionally before local branch preparation, push or PR creation. Use a stable key bound to unit, action, remote, branches and head SHA. After I/O reconcile observed external identity and persist append-only evidence/outcome. A process restart cannot infer completion from attempted intent. Do not create commits automatically; prepared commits require separate existing authorization. Push only an explicitly approved isolated branch without force or protected-target writes.

PR creation uses a structured body built from stored actual validation/quality/security/design references; include milestone/task IDs, design, purpose, tests, limitations and related PRs. Before creation inspect persisted identity and all relevant remote PR states for exact owner/head/base/remote identity. Multiple matches or closed/merged outcomes block for a human decision. A timeout after creation triggers lookup, never another blind create. Serialize lookups and creates with the repository lease and durable operation state. External actors may race: detect and block duplicates after observation; do not promise a GitHub cross-process atomic PR transaction.

## Policy and readiness

Read active branch rules and classic protection. A failed/ambiguous policy lookup does not mean no restrictions. Preserve provider values when mapping queued/pending/running/success/failed/cancelled/skipped/timed-out/unavailable/unknown. Query checks and statuses for the exact PR head; reject evidence for any older SHA. Keep required and optional checks distinct. Successful optional checks cannot satisfy missing required ones. Poll within configured budgets and classify authentication, rate-limit and network failures without printing secrets.

Review state must combine current GitHub merge/review decision, applicable required counts, changes-requested/dismissals, CODEOWNERS and current head. Agent/bot review never counts as human approval. If requirements cannot be proved by available metadata, block instead of approximating them from a review count. Recompute on every changed head/base/policy/review state. Existing AEO-4 activated policy, quality/security readiness and exact publishing authorization are mandatory for every delivery milestone, including legacy milestones.

Milestone readiness requires all unit guards and dependencies. A dependency PR existing is distinct from its changes being available to downstream units; unmerged/unavailable dependency content blocks the latter condition. AEO-5 may declare READY_FOR_AUTHORIZED_MERGE but never performs the merge.

## Evidence and reports

Persist unit and operation identity, authenticated principal, preconditions, policy/approval references, base/head SHA, branches, immutable PR ID/number/URL, exact-head CI and review snapshots, quality and security evidence hashes, documentation hashes, dependency state, recovery observations and blocker codes. Preserve prior observations when state changes. Report JSON and Markdown read stored evidence and display unavailable fields as unknown. Content hashes and SQLite append-only guards do not establish tamper-resistant remote audit storage.

## Documentation ownership prerequisite

The existing AEO-1C generator assumes cross-service architecture ownership. Introduce an explicit typed internal-orchestrator scope only after requirements approval; bind it into the scope digest. Restrict it to the single orchestrator task/context root and orchestrator-owned docs. Preserve current application ownership defaults and negative tests. Never silently remap an existing approved revision. This compatibility change is part of the review scope and is not already implemented.

## Official provider references

Request construction: [GitHub CLI API manual](https://cli.github.com/manual/gh_api). Policy reads: [classic protection](https://docs.github.com/en/rest/branches/branch-protection) and [active branch rules](https://docs.github.com/en/rest/repos/rules). Review data: [pull request reviews](https://docs.github.com/en/rest/pulls/reviews). These references inform the proposed adapter; they do not prove a live integration was implemented or tested.

## Domain model

DeliveryRun, DeliveryUnit, DeliveryOperation plus typed repository/branch/PR/check/review/policy snapshots.

## Interfaces

Nine delivery CLI operations and a typed GitHub provider; no merge/deploy capability.

## Persistence

Additive 0007 using existing SQLite transactions, audit and immutable content-addressed evidence.

## Security

# Security and approvals proposal

Remote writes default off. GitHub authentication, repository push permission, AEO design approval, activated quality/security policy and artifact-bound publishing authorization are separate checks. Required review is a human decision; neither an AI response nor an agent identity can supply it. Agent outputs and all GitHub/repository content are untrusted data.

## Mandatory existing workflow

The original AEO-5 specification section 3 says: "Use the existing AEO-1C documentation approval workflow" and "Do not proceed to implementation if a required approval is pending or denied." The AEO-5R request section 4 says: "After discovery and any required design approval" and permits stopping only approval-dependent activities while independent work continues.

The actual implementation enforces requirements approval in design.generate_design and authenticated decisions in design.decide. The current approver list is empty. No generated fixture identity, direct SQL insertion, automatic allowlist update, claimed actor or chat approval will be substituted for the configured Windows human verification. The review package is draft/unapproved; requirements registration is not approval. See APPROVAL_REQUIRED.md for the exact next action and scope digest.

## Publication authority

Bind a publishing authorization to milestone, delivery unit, existing task, action, repository ID/root, remote immutable identity, target/head branches, base/head commits, design revision, manifest/policy digest, quality evidence, expiration and approving human. Recheck scope and revocation inside the transaction immediately before intent. Persist consumption/operation identity atomically so recovery observes a previous attempt without granting a new mutation. Any changed scope needs fresh authorization. Reconciliation is read-only and does not consume a new publishing grant.

No generic legacy milestone/operation approval is treated as remote publishing authority. Every delivered milestone must adopt AEO-4. Missing/expired/stale/incomplete quality or security evidence blocks publication. Draft PR policy must be explicitly declared; it never bypasses required pre-publication security/design approval.

## Provider boundaries

Use gh with validated argv, bounded timeouts and fixed host/API methods. Do not support arbitrary shell, force push, reset, rebase, branch deletion, protected-base commits, merge, deploy, workflow dispatch/cancel/rerun, token creation or self-approval. Never log tokens, environment secrets, authentication headers or large raw PR body/log data. Redact provider errors and hash evidence. Validate JSON fields and bound output before persistence/command use. A provider permission failure does not trigger broader credentials.

Required CI policy includes active rulesets and classic protection; unreadable policy means blocked. Preserve raw status values, exact tested SHA, required/optional distinction and missing checks. Human review must satisfy current GitHub requirements including CODEOWNERS, dismissals, author/self restrictions and outstanding changes-requested. Unsupported rules and unverified review constraints block automated readiness. Recompute after any head/base/policy change.

## Test boundary

All new tests must use temporary repositories/databases and mocked gh subprocess responses. Real branch pushes and PR creation are excluded from ordinary validation. Live tests require a separately identified authorized sandbox. Local administrator control of config, Python and SQLite remains a trusted boundary; no stronger audit/storage assurance is claimed. There are no implemented AEO-5 security capabilities yet.

## Developer documentation

# Implementation plan awaiting approval

## Execution order

1. Complete recovery inventory, reviewable local design, six rendered diagrams and requirement-scope registration. Obtain authenticated requirements approval. Address the internal-documentation ownership compatibility prerequisite under that approved scope, then generate, validate and obtain authenticated design approval before AEO-5 delivery implementation.
2. Add strict models and a provider port/gh adapter. Verify installed flags and official API contracts. Mock authentication, permission, JSON, pagination, rate-limit, network and redaction cases.
3. Add additive migration 0007, durable operation identity/intent and append-only observation/evidence history. Test upgrade preservation from 0006 and prior records, transaction failure and restart.
4. Add isolated branch management and publication under existing leases and exact AEO-4 grants. Test safe naming, dirty preservation, baseline conflicts, reuse, hook isolation and disabled writes.
5. Add PR body generation, existing/open/closed/merged reconciliation and duplicate detection. Test create response loss, external competing PR and no blind retry.
6. Add manifest DAG/dependency readiness; CI/current-head policy and human-review verification. Preserve unsupported/unavailable policy as blockers. Test invalidation and independent partial completion.
7. Add recovery, reports and all nine Typer commands. Read-only commands must have spy assertions prohibiting write-port calls. Add restart/transaction/timeout failure injection, no-merge/deploy checks, report hash/provenance and full mocked end-to-end delivery.
8. Run all 163 baseline tests plus new tests; Ruff, formatting, dependency consistency, disposable database upgrade/check and established validation. Update recovery/operational guides, exact results, implementation inventory and acceptance report. Keep live capability claims separate. Stop before AEO-6.

## Planned implementation files

github_models.py, github_provider.py, delivery_models.py, delivery_store.py and delivery.py in src/agrosphere_orchestrator; additive settings/CLI integration, migration 0007_delivery.py and tests/test_github.py, test_delivery.py and test_delivery_cli.py. File decomposition may change after review; these files do not currently exist and are not reported as completed work.

## Approval boundary

Independent discovery, source assessment, draft documentation, local diagram rendering, requirements registration and existing regression checks are authorized and performed before waiting. Production delivery code, schema changes, executable delivery task import and remote publication remain gated. No live remote write is authorized by this implementation request. No user work may be cleaned or overwritten.

## Verified context references

- agrosphere-orchestrator/src/agrosphere_orchestrator/design.py sha256=1330049444195c4f2ca64cc7f0f28e76a386251200ffb05104f374ddcdfe5900 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/design_validation.py sha256=a71e64be787535a1e4721e8c1b87c21b8d4a4cf43dab29a621520f9f620bcbf5 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/design_agents.py sha256=0e02407ef3ddecd43cc3527416eaf2c1eb415a3163157f2b182f59e3ab599f8a HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/quality.py sha256=0ca64bfa4952654f10904a227ccf6b5b3dc570f69bfd242528a92e2b3194dd53 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/orchestration_store.py sha256=e7ad91941648bb7d805db0bc73b98613dfc6d410bcad09a72063ba200c5d5f06 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/execution_workspace.py sha256=8591774fa41faadb017f01c37ff473ef39816728a54eec839d74aac51da490a2 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/cli.py sha256=9e2763a447c227ff06161aa4c2ef360c1086393ea5fd24d1a30eba59f3807adc HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/config/settings.py sha256=5a19693519f0d620164ef1a5bcc0a7841a2d3156faef3d61affb840149292bd6 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/IMPLEMENTATION_RECOVERY.md sha256=df8c6041e9a3f4f4eaed25b55c17da854e107352cf08d8bda5c55d1c263b6f43 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/01-existing-capability-assessment.md sha256=01b12703723c6a099eae0439ae9766cba08b501aee67e7c414e3696f60524883 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/02-architecture.md sha256=a56f20f8a7584e0ef61ae90edb6841e0eec99d77ec72230ce4f29aa0bdeb5e9a HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/03-workflows.md sha256=1de5f9f61a0e2cec72ea23ebd568823a5510420d31e9567d985cceed5ca63db1 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/04-security-and-approvals.md sha256=03d7ae028b54850147b0cdd2ff51d0c03b57b0b6a604586e8542f1afb6fe8375 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/05-implementation-plan.md sha256=cf175d058f112d34b664926a8429b56c182cde53a3a660ac14d2ef9d9b4812b1 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/06-acceptance-criteria.md sha256=6aa4f440a99b0a43b38d815a21852434ef58e55c1ae25ab633264538d238546d HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/00-original-specification.md sha256=7aba6a8b6f3a305073544b71fb912bb719461b0e869831798dc91ad0547b490f HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/00-recovery-request.md sha256=7546988cc2ed5132b1e2e2e37a4d90127ef97488627c400614e2ba6da71ffac1 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/design-repositories.json sha256=dab365fe0c5e05b75467099d31e9a93cc155ee3b48883b99a44b7f5a6532558a HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/diagrams/01-components.puml sha256=a1803e9396bf5338c3259e2a9b028edd72022c8b53d1d4d64b7d92345da37888 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/diagrams/02-github-delivery.puml sha256=bea3f65f01eed6997110ee7b42ef81f45c08161c2ccd65bfb4c88c302f1cd83e HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/diagrams/03-multirepository.puml sha256=b42cd2978aa3c883193f1188e1e9fbfca34375d7ca030a68f3ad81d2c71cdd9a HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/diagrams/04-delivery-state.puml sha256=3033afa2c62c1c173a1361128fa14c1a3eb3f4fcc7dad165971b4b83284c0064 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/diagrams/05-durable-recovery.puml sha256=bfb903b03610299bb162d929d230dcaccbb8470e0dbb367d080d29ab763b894d HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/docs/milestones/AEO-5/diagrams/06-approval-quality.puml sha256=e70ad9d03aca75401fdc657c318d79281718e94ccd31e4a038a1882601ed6fb5 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/design_models.py sha256=3adb56172c5692902c4631437fc72e1851a026595b26e91e9ac15ff441c619f4 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402
- agrosphere-orchestrator/src/agrosphere_orchestrator/design_policy.py sha256=c404512136f75955cdb8d856861bbd2299b76c053f6d1301e7d13b9b785bca91 HEAD=e2a080f8c83339f20a3cb3e26506859da100c402

## Related artifacts

- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/business.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/architecture.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/service.md)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/01-components.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/01-components.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/02-github-delivery.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/02-github-delivery.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/03-multirepository.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/03-multirepository.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/04-delivery-state.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/04-delivery-state.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/05-durable-recovery.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/05-durable-recovery.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/06-approval-quality.svg)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/diagrams/06-approval-quality.puml)
- [Directory entry](aeo://agrosphere-orchestrator/docs/milestones/AEO-5/revisions/9824ee231f67b694234e192084fadfdfcacd3b4e5c35937e2730753098c8d507/overview.md)
