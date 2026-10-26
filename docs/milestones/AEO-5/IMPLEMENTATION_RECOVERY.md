# AEO-5 implementation recovery

Classification: **Not found in the inspected locations.** Date: 2026-10-25.

The baseline is e2a080f8c83339f20a3cb3e26506859da100c402 on master. Only master and origin/master exist; the live remote advertises master at the same SHA and no tags. There is one registered worktree. All eight reachable commit trees and reflogs were inspected. Six unreachable blobs were inspected for AEO-5 and delivery-class markers; none contained those markers, and no unreachable commit was reported. No AEO-5 source/test/migration was found in uncommitted files.

C:/Projects contains the current workspace and agrosphere-backup. The backup has the older apps/services/contracts layout; a candidate filename search for AEO, orchestrator and delivery returned no matches. This is a scoped search, not an assertion about inaccessible refs or every file on the computer. No recoverable AEO-5 checkout was identified. The IDE workspace lists the existing independent service repositories, not another orchestrator checkout.

Exact commands, exit codes, remote refs and object inspection summaries are in [recovery-investigation.json](evidence/recovery-investigation.json). rg exit 1 means no candidate filename matched. Candidate paths such as .github do not establish an implemented GitHub provider.

The three untracked files present at entry were the previous AEO-5 validation report, command JSON and JUnit XML. They are preserved. No reset, clean, checkout, fetch, merge, branch change or commit was used. Remote inspection used git ls-remote only.

Implementation must be newly built after mandatory approvals. Existing AEO-2 execution/worktree isolation, AEO-3 repository resource leases, AEO-4 governance/evidence, SQLAlchemy transactions, Typer and Alembic are the integration points. [Capability inventory](01-existing-capability-assessment.md) records each missing capability.

## Approval and ownership prerequisites

The explicit AEO-5 request requires the existing AEO-1C approval workflow. design.generate_design calls require_approval for requirements before generating a revision. design.decide rejects an empty design approver list. Current Settings.design_approvers is empty. No AEO-5 requirements or design decision has been manufactured.

A second compatibility gap is documented for review: design_agents.TemplateDocumentationAgents and design_validation.expected_owners hardcode business/architecture/overview ownership to agrosphere-architecture and exclude the orchestrator from service/diagram ownership. The current repository manifest also omits the orchestrator. Blindly invoking the generic generator would violate AEO-5's explicit orchestrator-only documentation ownership. The proposed smallest extension is an explicitly declared internal orchestrator design scope, with unchanged ownership behavior for existing application milestones. It must include tests rejecting cross-service ownership relaxation. No production change has been made to bypass these guards.

A review-only scoped manifest adds the actual orchestrator Git root and retains the architecture root for the existing verifier's read-only context requirement. It does not modify the central manifest, roles or approvers. Registration creates only the proposed requirements scope and audit event. It imports no executable task plan, grants no approval and performs no remote write.
