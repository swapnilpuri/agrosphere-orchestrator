# AEO-6 autonomous operation guide

Run from C:/Projects/agrosphere/agrosphere-orchestrator in Windows PowerShell. Requirements and technical design approvals for AEO-6 are already valid. No repeat approval is needed for that unchanged scope.

## Safe read-only dry-run

~~~powershell
Set-Location C:\Projects\agrosphere\agrosphere-orchestrator
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous plan --milestone 3B
~~~

The actual command was executed and returned exit 0. It inspects only confirmed manifest roots and reports recovered facts; it does not grant eligibility or launch application work. Start also defaults to dry-run, including when a request file says local.

## Isolated simulation

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous simulate --output-directory docs/milestones/AEO-6/evidence/operator-simulation
~~~

Simulation creates three independent temporary Git repositories and a disposable database, invokes existing lifecycle services, and injects clearly labelled fixture model/scanner/renderer/GitHub ports. All fixture approvals stay in that database. It reconstructs the controller across checkpoints, fails QA once, repairs within policy, and stops at REPORTED with formal completion false. It does not consume model quota or contact GitHub. Windows cleanup verifies the owned temporary path and handles long immutable artifact paths.

## Future approved local execution pattern

This is a supported command pattern for a later separately authorized application run. Do not substitute a real application milestone and execute it as part of AEO-6 acceptance.

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous start --milestone <approved-milestone> --mode local --request <reviewed-request.json>
~~~

The request schema is docs/schemas/autonomous-request.schema.json. It contains the milestone, optional complete DesignInput, explicit TaskOptions by task ID, optional validated delivery manifest and finite limits. The configured AEO_AUTONOMOUS_ROADMAP must identify a roadmap file included by hash in approved context for application scope. Missing roadmap, dependency evidence, explicit write paths/validators or required grants block. Existing AEO-1C, scheduler, AEO-2 and AEO-4 authentication remains required. Local mode never enables remote writes.

## Inspect and continue an existing run

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous status <run-id>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous pause <run-id>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous resume <run-id>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous recover <run-id>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous validate <run-id>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous report <run-id> --markdown
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous report <run-id> --export
~~~

Recover only observes/adopts independently verified child outcomes; it never blindly replays a write. Uncertain intent and reservations stay retained. Export publishes immutable JSON/Markdown history atomically under AEO_AUTONOMOUS_REPORT_ROOT. Status/report/validate read persisted evidence; remote freshness requires the appropriate continuation or existing AEO-5 reconciliation.

Later delivery references can be bound without rewriting the immutable run request:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous resume <run-id> --delivery-manifest <reviewed-manifest.json>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous resume <run-id> --grant "<unit>:<prepare-or-push-or-create-pr>=<authenticated-request-id>"
~~~

A bound delivery manifest cannot be replaced. The existing AEO-5 action guard validates every grant against current scope, identity, expiry, policy and remote-write settings. No merge/deploy/automatic next-milestone command is provided.

## Existing authentication checkpoints

The checkpoint report contains exact current subjects and executable existing CLI commands. Common supported commands include:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-requirements <milestone>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-design <milestone>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-plan <milestone>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli agent approve --execution <execution-id>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli quality activate --milestone <milestone>
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli approvals request --milestone <milestone> --category DELIVERY_APPROVAL --action delivery --reason "Review independent evidence"
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli approvals decide <approval-id> --reason "Reviewed exact evidence"
~~~

Do not put passwords or authentication secrets in command arguments or chat. Reuse valid unchanged decisions; failed/revoked/expired/changed-scope authority blocks. Publication action requests use existing delivery request-approval, then authenticated approvals decide, followed by explicit controlled-delivery continuation with those references.
