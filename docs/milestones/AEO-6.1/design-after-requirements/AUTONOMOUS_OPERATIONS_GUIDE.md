# Autonomous operations guide — AEO-6.1 design review

Requirements approval has been verified against persisted decision 67c78c9f-387d-426b-8e89-64092bd48fd0, scope 8367e71ff015366e5c2493c11d199f3d9f7f3ad7bde902f385d10b6a5db96138. Technical revision 4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066 is registered and validated, awaiting authenticated design approval. Implementation is not authorized. This version supersedes the preparation guide for current status only; the preparation guide is a hashed approved context reference and remains unchanged.

## Exact next action

Review [the approval package](DESIGN_APPROVAL_REQUIRED.md), [architecture](../../AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/architecture.md), [service design](../../AEO-6-ADJUDICATION/revisions/4db823e6ee59b3278a89083dccbf0198ef19b20f8a25a39b299b875b1c618066/service.md) and diagrams. From C:\Projects\agrosphere\agrosphere-orchestrator, the authorized human runs:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-design AEO-6-ADJUDICATION
~~~

Use --reject for a rejection. The command displays the exact package and asks for confirmation and local Windows credentials. Never place credentials in arguments or chat. The currently authorized design SID is sid:S-1-5-21-1295115365-4060518610-348779417-1001. No agent approval command is run by this preparation.

## Supported inspection

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone docs AEO-6-ADJUDICATION
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone design-status AEO-6-ADJUDICATION
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous status ba0851d4-66bc-417a-851b-f08176bd8061
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous report ba0851d4-66bc-417a-851b-f08176bd8061 --markdown
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous validate ba0851d4-66bc-417a-851b-f08176bd8061
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli approvals pending
~~~

Use approvals inspect <request-id> for generic governance requests. Evidence list/inspect/request/decide commands in the proposed design do not exist yet. Do not run a fabricated evidence command or repurpose a delivery/security approval category to clear 1B.

## Later internal implementation gates

After independently verifying authenticated design approval, the existing workflow supports:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone implementation-ready AEO-6-ADJUDICATION
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone plan AEO-6-ADJUDICATION
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-plan AEO-6-ADJUDICATION
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone prepare AEO-6-ADJUDICATION
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone execution-report AEO-6-ADJUDICATION
~~~

These are conditional future steps. Use the approved internal manifest only in the internal child process. Read the prepared exact execution IDs, worktree paths, policy and expiry before an authorized human uses agents approve --execution <exact-id>. Execution/plan approvers are independently configured through AEO_EXECUTION_APPROVERS; currently empty. No existing requirements or design decision supplies execution authority. milestone execute must not start until the plan and exact grants pass. The registered developer task precedes verification; do not recreate completed tasks or create an autonomous run for this change.

## Governed approver configuration procedure

Settings defines three separate JSON-list fields: AEO_DESIGN_APPROVERS, AEO_EXECUTION_APPROVERS, AEO_GOVERNANCE_APPROVERS. Governance is empty and denies every quality-policy activation and governance decision, including delivery/security/dependency decisions. It does not invalidate a separately authorized design SID. Execution is also empty, blocking authenticated plan and execution grants.

An authorized local configuration administrator must obtain the intended human Windows SID through the existing local identity procedure, verify role assignment outside the agent, and set only the reviewed roles in the existing .env or process environment using JSON arrays of canonical sid:S-... strings. Example format (replace the placeholder before use): AEO_GOVERNANCE_APPROVERS=["sid:<authorized-Windows-SID>"]. Set AEO_EXECUTION_APPROVERS separately when execution is authorized. Do not copy the design identity automatically, use usernames, wildcard identities, add agents, or expose passwords. .env changes are local administrator configuration, not an authenticated policy/decision record. No allowlist has been changed here. Restart the CLI process, inspect Settings locally without dumping unrelated secrets, and verify an unauthorized/removed SID fails in disposable tests. Existing grants must be rechecked at consumption. See quality.activate_policy, quality.decide_approval, quality.valid_approval, orchestration.approve_plan and execution.check_grant.

## Renderer setup used for this package

The JAR already exists at .aeo/tools/plantuml-1.2026.9.jar. The configured Settings value is null, but design preparation explicitly supplied that local file to LocalPlantUML. All three diagrams passed check-only and SVG generation using the existing sandbox profile. The JAR hash is recorded in evidence/design-generation.json. No software was downloaded or installed.

Supported CLI setup for future generation, limited to the review process:

~~~powershell
$env:AEO_PLANTUML_JAR = (Resolve-Path '.aeo/tools/plantuml-1.2026.9.jar').Path
.\.venv\Scripts\python.exe scripts/verify_design_tools.py
~~~

AEO_JAVA_EXECUTABLE selects an existing approved Java executable if java is not on PATH. Verify the chosen JAR/hash and Java locally before use. No permanent environment change is implied. Do not run milestone design again over this revision merely to configure rendering: the CLI template adapter differs from this content-addressed review adapter and would select a different revision requiring review. Use milestone docs now; supported export-docs can repair missing published files from the immutable stored revision.

## Same-run continuation and recovery

After adjudication capability is implemented and verified, an authorized human decision still does not restart an exited controller process. Once the conflict, roadmap/dependency, M2 product acceptance, quality/execution and expired-budget blockers are independently resolved, the existing entry is:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous resume ba0851d4-66bc-417a-851b-f08176bd8061
~~~

Do not run it now. Application discovery must use the absolute config/repositories.yaml with exactly the 12 application roots and workspace C:\Projects\agrosphere, and database URL for the original aeo.db. Never leave an internal-only manifest configured for application discovery. No autonomous start, new run, limit change or SQL edit is permitted.

For an uncertain unfinished operation inspect status/report/validate, then use autonomous recover <run> only when current evidence supports outcome reconciliation; it does not replay writes or refresh an ordinary conflict. Current operation is absent. Original deadline remains created_at + 3600 seconds, 2026-10-26T06:28:07.706005Z (October 26, 2026, 1:28:07 AM America/Chicago), already expired. Raising AEO_AUTONOMOUS_MAX_SECONDS cannot change it.

## Operator experience and remaining runtime work

The existing bounded controller discovers, designs, prepares plans, executes authorized children, validates and checkpoints subject to its actual guards. Existing status/report and human commands avoid bespoke coordination prompts. Full autonomous application delivery is not demonstrated by mocked simulation. This design supplies actionable evidence checkpoints after implementation; it does not add approval-triggered continuation. Automatic restart would require a separately governed runtime enhancement with durable decision notification, single-owner lease, idempotency, fresh guards and expired-run enforcement. No watcher or parallel scheduler is authorized by AEO-6.1. Today humans decide, then explicitly resume when eligible.

Independent packages: [operational blockers](OPERATIONAL_BLOCKERS.md), [deadline proposal](DEADLINE_EXTENSION_CHANGE_PROPOSAL.md), [roadmap review](ROADMAP_APPROVAL_PACKAGE.md), and [M2 performance package](MILESTONE_2_PERFORMANCE_REVIEW.md).

## Existing CLI summary limitation

The supported milestone docs/design-status summary reads architecture narrative keys from the frozen requirements input. Those keys were absent in the approved preparation scope, so its summary fields still show architecture_overview={} and technical_decisions/risks_and_assumptions=MISSING. The registered architecture/service artifacts contain the complete design and passed section/content validation. Review those exact artifact links and bundle; do not treat the summary placeholders as approved decisions or silently rewrite the approved requirements to fill them. No runtime change to the summary formatter was authorized or made.

## Local administrator SID/configuration checklist

1. On the intended approver's own Windows session, run whoami /user and independently confirm that account's assigned governance or execution role. Prefix the returned SID with sid: exactly; account names alone are not sufficient.
2. In the existing administrator-controlled .env, set AEO_GOVERNANCE_APPROVERS to a JSON list of the specifically authorized canonical SIDs. Set AEO_EXECUTION_APPROVERS only for separately authorized execution approvers. Keep AEO_DESIGN_APPROVERS unchanged unless its role assignment is independently changed. Review the resulting diff locally, preserving unrelated configuration and secrets.
3. Start a fresh CLI process so Settings reloads the selected values. Use approvals pending/inspect for review; configuration alone grants no decision and does not create evidence approval. Existing requests still require exact authenticated decisions and unchanged policy/context.
4. After authorized implementation, verify fail-closed empty/removed/wrong-role/self-actor behavior in disposable regression fixtures before any live evidence decision. No credentials or production approval should be used as a configuration test.

This is a procedure for an authorized administrator, not authorization to assign roles. No configuration update has been performed by the agent.

The persisted run explicitly selects milestone 2 with max_milestones=1. Existing discovery observes other milestones but does not grant automatic progression across the roadmap or authorize a different milestone. This task preserves that selection and limit. The registered internal adjudication design is prepared through the existing design service, without repurposing the expired application run as an internal implementation run.
