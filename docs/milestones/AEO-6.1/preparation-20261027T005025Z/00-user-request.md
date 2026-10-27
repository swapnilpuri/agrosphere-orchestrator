# AgroSphere AEO-6.1 — Autonomous Recovery and Approval-Driven Engineering

## ROLE

Act as Principal Autonomous Engineering Architect, Orchestrator Runtime Engineer, Governance Architect, QA Lead, and Engineering Program Manager.

We are developing AgroSphere using the existing AEO-1 through AEO-6 autonomous engineering orchestrator.

**Primary objective:** Move from repeated ChatGPT-to-Codex manual coordination to approval-driven autonomous engineering, using the existing orchestrator and governance framework.

This is a targeted stabilization and operationalization task, not a new orchestrator project.

## WORKSPACE

- Workspace: `C:\Projects\agrosphere`
- Orchestrator: `C:\Projects\agrosphere\agrosphere-orchestrator`
- Architecture: `C:\Projects\agrosphere\agrosphere-architecture`
- Existing autonomous run: `ba0851d4-66bc-417a-851b-f08176bd8061`

Discover the 12 application repositories from the authoritative manifest.

## CURRENT STATE

AEO-1 through AEO-6 are implemented.

The real autonomous run is BLOCKED at `discovery-conflict`.

Only Milestone 1B has an unresolved historical evidence relationship.

The latest forensic analysis established:

- Estate's 1A completion report states that 1B had not started at the 1A checkpoint.
- Separately committed Spatial implementation and tests support later 1B delivery.
- The assertions are semantically compatible.
- Authenticated provenance is insufficient for automatic historical supersession.
- The existing AEO approval framework lacks an evidence-disposition workflow.
- A governed AEO-6-ADJUDICATION change proposal was prepared but not registered or approved.
- No source changes were made in the latest investigation.

Milestone 2 separately lacks approved requirements and documented performance acceptance.

## PHASE 1 — DISCOVER THE EXISTING GOVERNANCE IMPLEMENTATION

Read the existing AEO design, requirements, policies, schemas, authenticated approvals, CLI, autonomous controller, recovery classification, and audit mechanisms.

Read:

- `MILESTONE_1B_FORENSIC_REPORT.md`
- `MILESTONE_1B_ADJUDICATION_MATRIX.md`
- `MILESTONE_1B_DECISION_PACKAGE.json`
- `MILESTONE_1B_RECOVERY_VERIFICATION.md`

These reside under:

`docs/milestones/AEO-6/evidence/discovery-reconciliation/`

Find the AEO-6-ADJUDICATION proposal and determine its registration and approval status.

Do not recreate capabilities already implemented.

## PHASE 2 — COMPLETE THE GOVERNED ADJUDICATION DESIGN

Use existing AEO documentation-first workflows to register and validate the pending evidence-adjudication requirements and design.

The design must provide:

1. Explicit evidence-disposition records.
2. Original evidence preservation.
3. Cryptographically verifiable or otherwise authenticated decision provenance consistent with existing AEO policy.
4. Human actor identity and authorized role.
5. Recorded rationale and supporting evidence references.
6. Decision scope and affected milestones.
7. Immutable audit history.
8. Rejection, unresolved, and approved dispositions.
9. Idempotent recovery and duplicate-decision protection.
10. Integration with fresh discovery and autonomous resume.
11. Protection against converting evidence adjudication into milestone acceptance.
12. Version compatibility and migration safety.

Use the established design approval workflow.

**STOP at any required authenticated human approval.**

Do not interpret this prompt as approval.

Report the exact existing approval command or supported workflow, required identity, and artifact to review. Never fabricate credentials or approvals.

If implementation approval is separately required, enforce that boundary as well.

## PHASE 3 — IMPLEMENT THE CAPABILITY AFTER AUTHORIZATION

After the applicable authenticated approvals have been granted through existing AEO mechanisms, implement the smallest necessary extension.

Prefer reusing:

- Existing approval entities and services.
- Existing authentication and authorization.
- Existing audit infrastructure.
- Existing CLI conventions.
- Existing recovery persistence.
- Existing autonomous controller checkpoints.

Avoid creating another independent governance subsystem.

Provide a CLI-based human decision workflow. A UI is not required.

Ensure the mechanism supports an approval, rejection, or request-for-more-evidence disposition without directly manipulating SQLite.

## PHASE 4 — APPLY TO MILESTONE 1B

Generate a human-reviewable recommendation for the existing 1B conflict.

Explain why Estate's earlier 1A checkpoint statement is compatible with subsequent Spatial delivery.

Identify the evidence and its limitations.

Present the exact decision to the authenticated operator.

Do not auto-approve.

Only after the recorded authorized disposition may recovery classify the historical relationship accordingly.

Preserve 1B as PARTIAL unless independently established acceptance criteria prove otherwise.

## PHASE 5 — MAKE AUTONOMOUS RECOVERY OPERATIONAL

Verify that the existing controller can:

1. Detect a missing human decision.
2. Persist the blocked checkpoint.
3. Present the decision package.
4. Accept the resulting authenticated decision.
5. Recollect fresh evidence.
6. Resume the same run when authorized.
7. Continue other eligible tasks without requesting unnecessary operator intervention.
8. Stop only at genuine approval, security, requirements, or execution boundaries.

Where supported by the existing architecture, create reusable pause-and-resume behavior for future milestones.

Do not create a new autonomous run.

Do not resume the active run until all relevant gates are satisfied.

## PHASE 6 — PREPARE MILESTONE 2 AUTONOMOUSLY

Inspect the registered milestone roadmap and authoritative requirements.

Determine:

- Missing Milestone 2 requirements.
- Missing approved technical design.
- Required reference-device specifications.
- FPS and initial-view timing measurement methodology.
- Missing acceptance evidence.
- Required approvals.
- Any independent dependency or quality gates.

Create or update draft requirements, design, test plans and acceptance matrices through the established AEO process.

Do not invent performance targets or measurements.

If product-owner decisions are required, present precise decision options rather than asking general open-ended questions.

Do not declare Milestone 2 accepted or eligible without evidence.

## PHASE 7 — VALIDATE THE AUTONOMOUS OPERATING MODEL

Run the relevant focused and full regression suites after authorized changes.

Test:

- Evidence adjudication.
- Authenticated approval enforcement.
- Rejection and unresolved decisions.
- Cross-repository provenance.
- Immutable evidence history.
- Duplicate decision prevention.
- Fresh discovery after approval.
- Recovery after restart.
- Existing run preservation.
- Milestone 2 approval blockers.
- All 12 application repositories.
- No accidental source modification or GitHub publication.

Use mocks only for explicitly identified simulated tests.

Report simulated and real execution separately.

## PHASE 8 — PROVIDE ONE OPERATOR ENTRY POINT

The long-term operating model must be:

**Operator starts/resumes AEO → AEO plans and executes eligible tasks → AEO pauses for required human decisions → Operator approves/rejects through authenticated mechanisms → AEO continues.**

Investigate whether the existing AEO CLI and persistence can already achieve this without additional implementation.

If additional automation is needed, propose or implement it only through applicable governance gates.

Provide a single documented entry point for operating the existing autonomous run.

The entry point must not silently bypass approval or failure states.

Prepare an `AUTONOMOUS_OPERATIONS_GUIDE.md` explaining:

- How to start or resume the orchestrator.
- How to inspect current progress.
- How to review pending approvals.
- How to accept or reject decisions securely.
- How execution resumes.
- How artifacts and results are located.
- How failures are recovered.
- When human intervention is mandatory.

## SAFETY AND SCOPE

- Preserve existing AEO-1 through AEO-6.
- Preserve all 12 application repositories.
- Preserve uncommitted changes.
- Preserve database and migration history.
- Preserve the original autonomous run.
- Never manufacture approvals.
- Never edit approvals directly in SQLite.
- Never force discovery consistency.
- Never skip milestone acceptance criteria.
- Never automatically authorize PR merges or deployments.
- Never treat historical test reports as fresh validation.
- Do not create the generic orchestrator or Control Center UI.
- Do not start HRMS development.
- Do not restart completed application milestones.

Codex must not claim to have crossed an approval boundary merely because a future phase is specified in this prompt.

Execute all currently authorized work without unnecessary questions. At a genuine human approval boundary, persist progress and stop with the exact action required.

## FINAL RESPONSE

Provide:

1. Whether AEO-6.1 design and implementation were completed or are awaiting authorization.
2. Current 1B adjudication status.
3. Exact approval artifacts and supported commands.
4. Test results actually executed.
5. Current existing autonomous run state.
6. Milestone 2 readiness status.
7. The exact next operator action.
8. The proposed single-command operating model for subsequent development.
9. Remaining gaps preventing approval-driven autonomous delivery.

**Success means AEO can manage routine engineering without repeated manually written Codex prompts, while retaining authenticated human approval and auditable recovery.**