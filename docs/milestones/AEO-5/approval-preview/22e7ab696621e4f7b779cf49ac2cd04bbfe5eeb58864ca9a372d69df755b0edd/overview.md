# AEO-5: overview (design)

Scope: 22e7ab696621e4f7b779cf49ac2cd04bbfe5eeb58864ca9a372d69df755b0edd
Requirements: AEO5-AUTH, AEO5-BRANCH, AEO5-PR, AEO5-COORD, AEO5-CI, AEO5-REVIEW, AEO5-APPROVAL, AEO5-DURABLE, AEO5-RECOVERY, AEO5-EVIDENCE, AEO5-CLI, AEO5-BOUNDARY

## Milestone overview

Recover and complete the missing AEO-5 implementation after existing human approvals.

## What will be built

GitHub authentication and typed repository discovery; Safe branch preparation and publication; Verified PR creation and idempotent reconciliation; Multi-repository manifest coordination; Exact-head required CI and repository policy; Required human GitHub review; Existing AEO-4 approvals remain mandatory; Transactional durable delivery state; Observe ambiguous remote outcomes before retry; Actual delivery evidence and reports; Safe discoverable delivery CLI; Preserve regression and scope boundaries

## Why it is needed

AEO-5 acceptance failed due to absent production capabilities.

## Platform fit

Extends the internal orchestrator without new infrastructure or unrelated service edits.

## Component responsibilities

Provider observes GitHub; coordinator enforces units/leases; AEO-4 authorizes; persistence retains intent; reports expose evidence/blockers.

## Implementation sequence

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

## Expected outcomes

All baseline and new mocked tests pass; exact-source readiness and durable recovery are demonstrated.

## User-facing documentation

CLI help, operational/recovery guides and evidence-based acceptance report, with live capabilities labeled separately.

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
