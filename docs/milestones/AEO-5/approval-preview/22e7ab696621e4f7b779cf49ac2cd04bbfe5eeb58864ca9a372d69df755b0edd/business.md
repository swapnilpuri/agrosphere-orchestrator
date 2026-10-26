# AEO-5: business (design)

Scope: 22e7ab696621e4f7b779cf49ac2cd04bbfe5eeb58864ca9a372d69df755b0edd
Requirements: AEO5-AUTH, AEO5-BRANCH, AEO5-PR, AEO5-COORD, AEO5-CI, AEO5-REVIEW, AEO5-APPROVAL, AEO5-DURABLE, AEO5-RECOVERY, AEO5-EVIDENCE, AEO5-CLI, AEO5-BOUNDARY

## Business context

Complete the internal AgroSphere engineering orchestrator delivery milestone, preserving AEO-1 through AEO-4.

## Problem statement

The actual checkout has no AEO-5 delivery implementation; existing tests and local quality gates do not prove GitHub delivery.

## Objectives

Typed GitHub access, safe idempotent publication, exact-head CI and human reviews, restart-safe reconciliation and evidence-based reporting.

## User stories

An authorized operator prepares and publishes independent repository units, inspects blockers and recovers ambiguous operations without duplicate PRs.

## Functional requirements

- AEO5-AUTH: GitHub authentication and typed repository discovery
- AEO5-BRANCH: Safe branch preparation and publication
- AEO5-PR: Verified PR creation and idempotent reconciliation
- AEO5-COORD: Multi-repository manifest coordination
- AEO5-CI: Exact-head required CI and repository policy
- AEO5-REVIEW: Required human GitHub review
- AEO5-APPROVAL: Existing AEO-4 approvals remain mandatory
- AEO5-DURABLE: Transactional durable delivery state
- AEO5-RECOVERY: Observe ambiguous remote outcomes before retry
- AEO5-EVIDENCE: Actual delivery evidence and reports
- AEO5-CLI: Safe discoverable delivery CLI
- AEO5-BOUNDARY: Preserve regression and scope boundaries

## Nonfunctional requirements

Fail closed; bounded subprocess arrays; no secret logging; existing SQLite/leases/approval authority; additive migrations; temporary mocked tests.

## Acceptance criteria

- AEO5-AUTH: GitHub authentication and typed repository discovery — Authentication/permission failures block writes; repository and branch identities are validated.
- AEO5-BRANCH: Safe branch preparation and publication — Isolated branch creation/reuse preserves dirty source; exact authorized push never force-pushes.
- AEO5-PR: Verified PR creation and idempotent reconciliation — Repeated or ambiguous publication reuses an exact matching PR; duplicates and closed/merged matches block.
- AEO5-COORD: Multi-repository manifest coordination — Existing tasks and resource leases bind each unit; unavailable dependencies block milestone readiness.
- AEO5-CI: Exact-head required CI and repository policy — Required checks are current-SHA bound; missing, stale and unavailable policy/checks block.
- AEO5-REVIEW: Required human GitHub review — Human review, CODEOWNERS and dismissals are respected; agents do not self-approve.
- AEO5-APPROVAL: Existing AEO-4 approvals remain mandatory — Fresh activated quality/security and exact human publishing approval are required before mutation.
- AEO5-DURABLE: Transactional durable delivery state — Intent survives restart and migrations preserve existing records; evidence/audit are append-only.
- AEO5-RECOVERY: Observe ambiguous remote outcomes before retry — Lost push/PR responses, provider failures and partial completion reconcile without blind replay.
- AEO5-EVIDENCE: Actual delivery evidence and reports — Reports include actual SHA, PR, CI, reviews, approval/quality hashes, blockers and recovery history.
- AEO5-CLI: Safe discoverable delivery CLI — All nine commands expose structured output; observation and default recovery never write remotely.
- AEO5-BOUNDARY: Preserve regression and scope boundaries — All 163 baseline and new tests pass; no unauthorized remote writes, merges, deployment or AEO-6.

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
