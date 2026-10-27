# Implementation authorization boundary — AEO-6-ADJUDICATION

Status: BLOCKED BEFORE IMPLEMENTATION. This review package grants no authority and changes no active policy.

Both supplied authenticated approvals passed the existing require_approval guard against the current design SID allowlist. Requirements decision 67c78c9f-387d-426b-8e89-64092bd48fd0 binds scope 8367e71ff015366e5c2493c11d199f3d9f7f3ad7bde902f385d10b6a5db96138. Design decision 59196472-83fa-4d48-86ca-307559a1d00c binds bundle 989c1335f933a2505d60391360d96bf9a725a1cd008c284959d3f355bccdb8bf, revision 4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066 and passed validation 7e5e7154abeb1a70d63705b5b8d19b905eb385daf34f3ee8aef640f0253eb329. Current approved context and artifact integrity checks passed. Case remains DESIGN_APPROVED.

## Exact implementation scope for review

Use the unmodified approved-plan.json exported from the registered revision. Tasks: adjudication-integration (developer/code-write), followed by verification (qa-engineer/validate). Implement only the registered evidence adjudication design using existing GovernanceRecord, DesignDecision, audit, HumanVerifier, discovery and controller seams. Preserve historical evidence and original autonomous-run data. No application source changes, migrations, automatic human decisions, new controller, automatic resume, provider/model invocation or deployment is authorized by this package.

Architecture/service review documents remain under ../../AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/. This package does not revise that approved design.

## Prerequisites requiring authorized administrator review

1. Assign independently authorized canonical Windows SID(s) to AEO_EXECUTION_APPROVERS. Current list is empty. The design approver must not be copied automatically. No SID assignment has been made.
2. Approve an internal-only role-registry variant permitting developer and qa-engineer to target agrosphere-orchestrator. Both current roles exclude it. Preserve application role configuration and restrict this variant to the internal CLI process.
3. Approve an internal execution-policy variant with bounded validation commands for focused adjudication pytest coverage and the existing scripts/validate.py regression. Current validation_commands is empty, and write planning cannot proceed without explicit allowlisted commands. live_enabled=false is a separate live execution blocker; enabling a model adapter requires explicit opt-in, not implicit design approval. Do not silently enable it.
4. Retain config/repositories.yaml unchanged with exactly 12 application repositories. For internal plan preparation only, the existing preparation-20261027T005025Z/design-repositories.json confirms the orchestrator root. Do not use it for application discovery or the original autonomous run.

The exact execution-plan digest and execution IDs DO NOT EXIST yet. They cannot truthfully be supplied until the above policy selections have been authorized and the existing plan service has generated them. No fabricated approval request or parallel approval mechanism was created.

## Supported preparation and authenticated commands

After the administrator authorizes the prerequisites, preparation can continue autonomously: import the exact exported approved DAG through the existing import_plan service; use milestone implementation-ready; propose milestone plan with explicit TaskOptions and approved command IDs. Do not re-register requirements, regenerate design or bypass context checks. Import is missing today; implementation-ready would fail before it.

The supported human plan-approval command from C:/Projects/agrosphere/agrosphere-orchestrator is:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-plan AEO-6-ADJUDICATION
~~~

This command is CONDITIONAL and currently blocked: no imported milestone/validated execution plan exists, and no execution approver is configured. It displays the plan and authenticates via WindowsConsoleHumanVerifier, binding <generated-plan-id>:approve-plan. There is no supported standalone approve-implementation command. After approval, milestone prepare produces exact execution requests; agents approve --execution <generated-id> requires separate authenticated, bounded grants. Never substitute the design digest for a plan digest or invent an execution ID.

## Verification performed

verify_readiness.py executed with the project virtual environment, exit 0. Real local checks used existing approval guards, current allowlists, stored-context HEAD/hash verification, artifact-integrity verification, current passed validation and typed manifest/policy/role inspection. Application manifest has exactly 12 roots. This is not a regression test or a live Windows credential authentication: authentication was previously recorded and was not repeated. No verifier mocks, application builds, models or providers were invoked. Prior full validation was not rerun: no implementation changes were authorized or made.

## Milestone 1B and autonomous run

No new evidence decision was requested or approved. 1B remains unresolved/PARTIAL in retained discovery. Estate's earlier checkpoint and later Spatial delivery may be compatible, but authenticated historical test provenance remains incomplete. After authorized implementation and validation, propose only the scoped historical-reference disposition under the approved policy; do not grant milestone acceptance or claim historical test authentication.

Run ba0851d4-66bc-417a-851b-f08176bd8061 remains BLOCKED/RECONCILING, discovery-conflict, current_operation=null. Request hash ea68398c024774bf986a784d1e481e88545e2229162e029c078bd351cdcd6672, original limits/checkpoint/history unchanged. Deadline expired October 26, 2026, 1:28:07 AM America/Chicago. No run was started or resumed.

Independent remaining blockers: evidence capability/decision, governance approvers, approved roadmap/dependency completion, M2 requirements/performance acceptance, execution and quality/security gates, and separately governed deadline-extension policy. Existing packages remain in ../design-after-requirements/ (OPERATIONAL_BLOCKERS.md, ROADMAP_APPROVAL_PACKAGE.md, MILESTONE_2_PERFORMANCE_REVIEW.md, DEADLINE_EXTENSION_CHANGE_PROPOSAL.md).

The runtime requires explicit autonomous resume after decisions and all applicable gates. No approval-triggered restart is implemented. Original application run cannot be repurposed to implement this internal milestone.

## One next operator action

An authorized configuration administrator must review and authorize the execution prerequisites above, including the actual execution approver SID assignment. Open this exact package from the orchestrator root:

~~~powershell
notepad.exe docs\milestones\AEO-6.1\after-design-approval\IMPLEMENTATION_APPROVAL_REQUIRED.md
~~~

This is an administrative configuration boundary before the authenticated approve-plan gate, not a request to repeat requirements/design approval. Supplying approve-plan as an immediately usable next command would fail under current persisted state. Once the prerequisites are assigned, the remaining plan preparation is agent work; do not ask the operator to manufacture plans or execution IDs.
