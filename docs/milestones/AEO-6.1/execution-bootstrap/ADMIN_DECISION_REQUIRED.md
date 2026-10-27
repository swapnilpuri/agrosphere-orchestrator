# AEO-6.1 execution bootstrap — administrator decision package

Status: PREPARED; NOT AUTHORIZED; NO ACTIVE GOVERNANCE CHANGES. This package does not approve implementation, configure an identity, or replace the registered design. The source of this stop is the user's Phase 2 instruction: “Do not treat this Codex prompt as permission to modify protected governance configuration.”

## Required administrator decision

An independently authorized local configuration administrator must review this package and REVIEW_MANIFEST.json, explicitly authorize or reject the internal process configuration selections below, and identify the exact verified canonical Windows SID(s) permitted to approve execution. Record the decision in the organization's existing administrator/change process. There is no application-level administrator registry or supported administrator-approval CLI in this repository. Do not create a second approval store to fill that gap.

The only evidenced configured identity is design approver sid:S-1-5-21-1295115365-4060518610-348779417-1001. It authenticated the two existing decisions. This establishes design authority only; it does not establish configuration-administrator or execution-approver authority. No independently identified administrator can be inferred from that SID, the current Windows account, config/approvals.yaml's legacy local-user actor, or this prompt. The administrator must independently select the execution SID; no candidate SID is prefilled.

## Proposed configuration and classification

| Selection | Exact proposed effect | Classification / current action |
|---|---|---|
| AEO_EXECUTION_APPROVERS | JSON list of independently verified canonical sid:S-... identities; no wildcard, inherited design identity, or agent identity | Protected authorization change; NOT made |
| AEO_REPOSITORY_MANIFEST | Process-only selection of repositories.internal.proposed.json: exactly agrosphere-orchestrator at C:/Projects/agrosphere/agrosphere-orchestrator | Protected repository visibility selection; NOT made |
| AEO_ROLE_REGISTRY | Process-only selection of roles.internal.proposed.json | Protected agent access change; NOT made |
| Developer | Only allowed_repositories changes to [agrosphere-orchestrator]; existing operations, python specialization, instructions and restrictions retained | Requires administrator review; NOT made |
| QA | Only allowed_repositories changes to [agrosphere-orchestrator]; existing validate/inspect/plan operations retained | Requires administrator review; NOT made |
| AEO_EXECUTION_POLICY | Process-only selection of execution.internal.proposed.json; preserves live_enabled=false and existing resource limits; adds two exact argv arrays | Protected command authorization change; NOT made |
| Explicit TaskOptions | task-options.proposed.json restricts the five approved source seams plus tests and generated docs/validation and docs/schemas; no config, migrations, approved milestone artifacts, AGENTS.md or application writes | Inactive candidate only; QA/validator limitations below must be resolved before final plan review |
| Preparation documents / copied approved DAG / read-only evidence | Only files in this execution-bootstrap directory | Routine authorized preparation; done |

Other roles are byte-for-byte equivalent as parsed to active role definitions. Developer and QA application permissions are removed in this internal variant rather than widened. config/repositories.yaml remains the original 12-root application manifest. Do not set these overrides globally, alter .env, or use the internal manifest with application discovery or run ba0851d4-66bc-417a-851b-f08176bd8061. Existing authentication, protected scopes, network denial and grant requirements remain in force.

The two command IDs and complete executable/argument restrictions are in execution.internal.proposed.json. The policy binds whole argv arrays: it exposes no argument interpolation, wildcard, arbitrary Python -c, PowerShell, shell wrapper or command substitution. Python runtime read paths are limited to the project .venv and C:/myprograms/Python/Python314, matching the prior verified native probe in docs/validation/aeo4-runtime.json and the current interpreter. Those paths exist. They grant no additional model read access. Policy type/schema validation is not native isolation certification.

## Additional execution constraints discovered

1. scripts/validate.py is the established full regression entry point, but it generates docs/schemas and docs/validation, invokes alembic upgrade head, reads configured repositories, validates examples/aeo-1.yaml, and invokes auxiliary tools. Do not run it against authoritative aeo.db for this preparation. The prior verified design-after-requirements/evidence/run_regression.py uses a disposable SQLite backup and restores generated reports. The candidate exact command is retained for administrator review, but its full isolated execution profile is NOT certified. Internal-only manifest selection also conflicts with the sample application's repository validation. The existing ValidationCommand schema has argv/read_paths/timeout only, with no per-command environment or manifest overrides. execution_process.runtime_environment also discards AEO_* settings in validator subprocesses, so process-scoped AEO_DATABASE_URL/manifest selections cannot be assumed to reach nested validation commands. An administrator-reviewed bounded wrapper/profile (and any independently required code-change approval) is needed to make full regression safe and meaningful under the internal executor. Do not broaden runtime reads to the workspace or permit arbitrary shells to solve it. The 600-second candidate timeout is the existing policy/schema maximum and is not evidence the full suite fits that budget.
2. A QA VALIDATION_ONLY request obtains a new private worktree at its own request.source_head (execution.py, queue_execution/run_execution; execution_workspace.create_worktree). It does not inherit the successful Developer worktree. The candidate QA options therefore validate schema/assignment only; they must not be represented as verification of the Developer patch. Existing producer ArtifactReference handoffs supply exact hashed input files, not automatic whole-tree materialization. A governed choice is required: bind a read-only QA review to exact producer artifacts plus Developer's independently run test evidence, or approve a bounded producer-worktree validation extension. Do not invent hashes before the artifacts exist. The latter needs design/change review before implementation; neither is activated here. Preserve the approved two-task DAG.
3. config/approvals.yaml still requires code-write operation approval and contains legacy approver local-user. Execution plan approval and the bounded agent execution grant do not write an Approval row for that operation; state.transition checks it independently. No matching task approval exists because no tasks are imported. Do not call the legacy record_approval API with a claimed actor to bridge this. Decide through the established governance/change process how authenticated execution admission will satisfy that inherited gate before live implementation. No code fix or policy exemption is authorized by this package.
4. live_enabled=false prevents run_execution even in VALIDATION_ONLY. Enabling the adapter, model/provider usage and fresh execution grants are separate explicit decisions. Leave it false during plan preparation.

## Exact conditional registration package

approved-plan.json is an exact semantic and byte copy of the prior exported registered revision DAG; audit_readiness.py checks it against the persisted approved DesignInput. Keep adjudication-integration (developer/code-write) before verification (qa-engineer/validate). The Developer task already includes evidence persistence, authenticated CLI, discovery and existing controller integration; QA includes security/regression criteria. Do not split/rewrite approved tasks to manufacture five new task IDs.

AFTER the administrator authorizes and selects the internal process configuration and assigns execution approver SID(s), agent preparation may run from the orchestrator root:

~~~powershell
.\.venv\Scripts\python.exe docs/milestones/AEO-6.1/execution-bootstrap/import_after_authorization.py
.\.venv\Scripts\python.exe docs/milestones/AEO-6.1/execution-bootstrap/import_after_authorization.py --register
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone implementation-ready AEO-6-ADJUDICATION
~~~

The first command defaults to read-only and currently fails closed on empty execution approvers; the second uses only persistence.import_plan after exact draft/effective-policy, approved digest, context, role, repository and plan checks. Import is atomic/idempotent and rejects content conflicts under an existing milestone ID. Neither command authenticates a human, approves a decision, invokes a model, starts a run, or generates a plan. The helper was prepared but not executed. It is not an administrative authorization mechanism.

After the QA/validator choices above are resolved and final TaskOptions reviewed, the existing command is:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone plan AEO-6-ADJUDICATION --options <final-reviewed-task-options.json>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone report AEO-6-ADJUDICATION
~~~

Do not substitute the candidate options as execution-ready. propose_plan generates the content-addressed PlanRevision and OrchestrationControl through existing transactional services, records plan.proposed evidence, and returns the real digest. Record it then; none exists now. Read-only milestone_record/load_plan/milestone_report must resolve the imported milestone and current PlanRevision before the human is directed to approve.

Only then the HUMAN runs the existing interactive command in the same reviewed internal configuration context:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-plan AEO-6-ADJUDICATION
~~~

WindowsConsoleHumanVerifier binds the generated plan digest plus :approve-plan to an authenticated SID; the service rechecks the current plan/design. No authentication or approval command was invoked here. Execution UUIDs arise later from milestone prepare and require separate agent approve --execution <actual UUID>; do not invent them or use the design digest in their place.

## Current result

No internal imported milestone UUID, scheduling plan digest, execution UUID, or human approval request was manufactured. Requirements/design decisions remain valid; no reapproval is requested. This is an administrator authorization boundary before the plan-approval boundary. Implementation cannot proceed after administrative approval alone, and plan approval alone does not remove the independent gates above. Review the precise artifacts and resolve the listed execution semantics before claiming execution readiness.
