# AgroSphere AEO-6.1 — Execution Bootstrap, Governance Configuration and Plan Registration

## ROLE

Act as Principal Autonomous Engineering Architect, Runtime Integration Engineer, Security Engineer, DevOps Engineer and Engineering Program Manager.

Our goal is to complete the transition from approved design to governed implementation execution using the existing AEO orchestrator.

Avoid another cycle of individual troubleshooting prompts. Diagnose and prepare all prerequisites in one coordinated pass.

## WORKSPACE

- Workspace: `C:\Projects\agrosphere`
- Orchestrator: `C:\Projects\agrosphere\agrosphere-orchestrator`
- Milestone: `AEO-6-ADJUDICATION`
- Existing application run: `ba0851d4-66bc-417a-851b-f08176bd8061`

## CONFIRMED APPROVALS

Requirements:
`67c78c9f-387d-426b-8e89-64092bd48fd0`

Technical design:
`59196472-83fa-4d48-86ca-307559a1d00c`

Verify their persistence and scope.

Do not repeat either approval.

## CURRENT ERROR

The operator attempted:

`python -m agrosphere_orchestrator.cli milestone approve-plan AEO-6-ADJUDICATION`

CLI returned:

`Unknown imported milestone`

Previous Codex investigation identified:

1. Missing execution approver configuration.
2. Missing Developer/QA permissions for the orchestrator repository.
3. Missing allowlisted validation commands.
4. Missing implementation DAG import.
5. Missing generated execution plan.

Implementation has not started.

## PRIMARY OBJECTIVE

Make AEO-6-ADJUDICATION ready for the legitimate authenticated implementation-plan approval.

Complete all safely authorized preparation, register the implementation DAG and plan, and stop at any required administrative authorization or authenticated human approval.

Do not approve decisions on behalf of the operator.

## PHASE 1 — END-TO-END EXECUTION READINESS AUDIT

Inspect the actual implementation of:

- Repository manifest discovery.
- Milestone registration and import.
- Task DAG persistence.
- Execution plan generation.
- Agent permissions.
- Repository access policies.
- Execution approver configuration.
- Command allowlists.
- Authenticated plan approval.
- Orchestrator execution adapters.
- Approval-aware autonomous continuation.

Read:

`docs/milestones/AEO-6.1/after-design-approval/IMPLEMENTATION_APPROVAL_REQUIRED.md`

Identify the source of the `Unknown imported milestone` error.

Determine the exact command dispatch, registry lookup, and persistence conditions responsible.

Do not assume documentation milestone registration automatically creates an imported execution milestone.

## PHASE 2 — RESOLVE EXECUTION CONFIGURATION

Inspect the current configuration and examples before proposing changes.

Prepare the minimum necessary configuration for AEO-6-ADJUDICATION.

Address:

### Execution approvers

Identify the existing authorized administrator and execution-approver configuration mechanism.

Reuse the established authentication and authorization model.

Do not invent identities, add wildcard approvers, or grant yourself authorization.

If administrative approval is required, produce a precise decision package and stop before making the protected change.

### Developer and QA permissions

Identify the registered Developer and QA agent roles.

Determine the exact repository permissions necessary to implement and validate the approved design.

Use least-privilege access.

Limit permissions to explicitly required repositories, paths, operations and commands.

Do not enable unrestricted workspace access.

### Validation commands

Discover the actual validation commands from existing repository configuration and prior verified execution scripts.

Prepare an explicit allowlist with exact executable and argument restrictions supported by the existing policy.

Do not broadly allow arbitrary PowerShell, Python, shell execution or unrestricted command arguments.

### Configuration integrity

Preserve existing security restrictions and unrelated configuration.

Before changing any active configuration, classify the change as either permitted routine configuration or a governed change requiring authorization.

Do not treat this Codex prompt as permission to modify protected governance configuration.

## PHASE 3 — IMPORT THE IMPLEMENTATION MILESTONE

Inspect the approved AEO-6-ADJUDICATION requirements and technical design.

Find the existing approved task model.

Verify task roles and repository mappings.

Import or register the implementation DAG using the supported execution subsystem.

Preserve dependency order.

Required activities should include:

1. Evidence disposition persistence.
2. Authenticated decision CLI.
3. Recovery/discovery integration.
4. Autonomous controller integration where approved.
5. QA, security and regression verification.

Reuse approved task definitions where available.

Do not duplicate existing milestone records.

If the import requires protected configuration or authorization not yet available, prepare the exact import package and command, then stop.

## PHASE 4 — GENERATE THE EXECUTION PLAN

Once prerequisites permit:

1. Generate the execution plan using existing AEO facilities.
2. Validate dependencies and agent assignments.
3. Verify repository permissions.
4. Verify command allowlists.
5. Verify the approved requirements and design digests.
6. Confirm source and artifact integrity.
7. Record the execution-plan digest and execution identity.
8. Validate plan readiness.

Do not directly manufacture execution records or approval decisions in SQLite.

Use existing supported APIs and CLI commands.

## PHASE 5 — EXPLAIN AND VALIDATE APPROVAL

Once the plan exists, verify that:

`milestone approve-plan AEO-6-ADJUDICATION`

resolves to the correct imported milestone.

Use read-only validation of command resolution; do not invoke an interactive authenticated approval on behalf of the operator.

If the command remains invalid, identify and fix the actual cause only if source changes are independently authorized.

If a source change requires additional design/change approval, stop at that boundary.

Do not attempt alternate approval mechanisms to bypass enforcement.

## PHASE 6 — PREPARE OPERATOR AUTONOMY

We do not want to keep manually coordinating every phase through ChatGPT.

Inspect whether the existing orchestrator can automatically transition between eligible tasks after human approval.

Create a concrete operational plan that provides:

- One supported controller entry point.
- Persistent task and milestone state.
- Automatic progression through eligible tasks.
- Explicit pending-human-decision reporting.
- Authenticated approval/rejection commands.
- Safe continuation after approval.
- Failure recovery without creating duplicate runs.
- Auditable artifacts and execution status.

Prefer existing functionality.

Do not introduce an unnecessary UI, generic orchestration framework or separate runtime.

Any missing approval-triggered continuation capability must be explicitly identified, designed, and governed before implementation.

## PHASE 7 — VALIDATE

Perform all authorized read-only validation and applicable safe tests.

If implementation changes are authorized and made, run focused and regression suites.

Record:

- Exact commands executed.
- Test pass/fail results.
- Configuration changes.
- Milestone import status.
- Plan generation status.
- Security validation.
- Approval readiness.
- Existing application-run preservation.

Distinguish actual results from proposed future actions.

## EXECUTION RESTRICTIONS

Do not:

- Restart the existing application run.
- Create a new application run.
- Implement adjudication before plan authorization.
- Modify approval decisions directly.
- Change the expired deadline.
- Invent an administrator or grant permissions without authority.
- Disable security gates.
- Modify unrelated application repositories.
- Force a milestone into the imported registry.
- Fabricate execution-plan identifiers.
- Start Milestone 3B.
- Begin generic orchestrator or HRMS development.

Continue automatically through all already authorized preparation.

At an authorization boundary, persist the current preparation and provide one precise human action.

## FINAL RESPONSE

Provide a compact readiness matrix:

| Prerequisite | Status | Evidence | Action |
|---|---|---|---|
| Requirements approval | | | |
| Design approval | | | |
| Execution approver | | | |
| Developer/QA permissions | | | |
| Command allowlist | | | |
| Implementation DAG import | | | |
| Execution plan | | | |
| Plan approval readiness | | | |

Also provide:

1. Exact root cause of `Unknown imported milestone`.
2. Configuration changes actually made.
3. Administrative approvals still required.
4. Registered milestone and execution-plan identity, if available.
5. Validation results.
6. Confirmation that the original application run remains preserved.
7. One exact next operator action.
8. Whether implementation can proceed after the next approval.

Do not finish by merely repeating the original five blockers. Perform all authorized preparation first.

**Success criterion: the approved AEO-6-ADJUDICATION design has a properly imported and validated implementation plan, ready for authenticated approval without bypassing governance.**