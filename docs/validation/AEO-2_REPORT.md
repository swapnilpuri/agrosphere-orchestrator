# AEO-2 implementation and validation report

Software validation completed at 2026-10-25T03:51:16.455674+00:00: **116 passed in 125.92s (0:02:05)**.
All 16 required commands in scripts/validate.py returned exit 0.
Native sandbox boundaries were verified independently. **Live model integration is not verified:**
the optional billed smoke was not run. No AEO-3 scheduler or application milestone was started.

## 1. Summary of implementation

The existing orchestrator now supports one explicit, approved task through a modular Codex
execution adapter. It discovers runtime capabilities, resolves registered roles, assembles
version-bound context, obtains authenticated execution approval, prepares an isolated worktree,
checks native permissions, captures typed output, runs approved validators and persists results.
Timeouts, cancellation, startup/auth/output errors, interrupted-session reconciliation and
preserved proposals have deterministic handling. Defaults remain offline and fail closed.

This is a production-oriented local framework with explicit operating limits, not a claim of
production certification or a successful live model run. Mock execution proves service behavior;
the native canary proves the tested OS boundaries. Neither substitutes for a live smoke.

## 2. Existing components reused

MilestoneSpec and TaskSpec remain the plan/task source of truth. The existing repository manifest,
read-only inspector, role registry, Settings, strict models, safe YAML, human authentication adapter,
AEO-1C artifact/design gate, operation-approval/state services, SQLAlchemy/Alembic/audit service,
Typer CLI and fixture conventions are extended. The original 82 tests remain operational.
Legacy AgentExecutor/CodexWorkspace protocol interfaces are preserved. The new async transport
protocol separates raw process results from the service's normalized ExecutionResult.

AEO-1B recovery evidence remains distinct from approved requirements. AEO-1C's template author,
rule review, required render evidence and authenticated design/delivery decisions remain intact.
There are no approved application plans invented by this implementation.

## 3. New components and interfaces

- execution_models: typed request/result/error/mode/state, validation policy, retry metadata and AgentOutput.
- CodingAgentExecutor: transport protocol; CodexExecutor/CodexExecAdapter implement the selected exec path.
- CodexMCPAdapter: actual SDK connection/tool-discovery interface, with execution refused when uncertified.
- CodexProcessManager: shell-free launch, bounded capture, secret redaction, Windows job lifetime and confirmed termination.
- execution_context: approved artifact/version selection, role resolution, dependency context and context integrity.
- execution_workspace: trusted Git worktrees, disabled hooks/filters, native canaries, scoped changes and preservation/cleanup.
- CodexSessionManager: persisted PID creation identity, conservative interruption and explicit recovery.
- execution: immutable human grants, single-task orchestration, task acceptance, telemetry and Markdown/JSON reports.

All nine roles have instructions, schemas, repository/operation policy, required context,
validation/approval requirements and advisory handoff contracts. Developer specializes in Java,
Python, Angular, Data/PostGIS and Integration. No handoff starts another agent.

## 4. Updated project structure

~~~text
config/execution.yaml
src/agrosphere_orchestrator/
  codex_runtime.py
  execution.py
  execution_context.py
  execution_models.py
  execution_process.py
  execution_sessions.py
  execution_workspace.py
  interfaces.py              existing protocols plus async transport contract
migrations/versions/0004_execution.py
tests/test_execution.py
scripts/verify_codex_runtime.py
scripts/verify_execution_upgrade.py
scripts/verify_aeo2_docs.py
scripts/codex_live_smoke.py
docs/aeo-2/                  gap analysis and current-bundle pointer
docs/milestones/AEO-2/revisions/<content-hash>/
  nine architecture/operations documents
  five PlantUML diagrams
  SCOPE_BASELINE.md
  ARTIFACT_MANIFEST.json
docs/adrs/0006-*, 0007-*, 0008-*
docs/schemas/               execution request/result/policy/output schemas
.aeo/executions/            private ignored worktrees, reports and evidence
~~~

The immutable documentation bundle contains 15 artifact references. Hash/ownership
validation passed and references were persisted through the existing append-only audit service
as documentation.bundle.observed. Approval remains pending review; no authenticated design
approval was fabricated. Current bundle: ecc485aed3038aaa7a2c78e87de1c49df28644b19b5a5a0980ef2cd632872b6d.

## 5. Selected Codex integration and rationale

Official OpenAI documentation and the installed executable/SDK were inspected before implementing
the adapter. Actual installed runtime: codex-cli 0.164.0-alpha.11.1; exec/schema/JSON support
is present, login status reports ready, and help mcp-server returns exit 2 (unrecognized command).
The preferred MCP route therefore does not satisfy installed-runtime compatibility.

Use the documented non-interactive exec transport with stdin prompts, JSONL events and final
JSON Schema. The service validates final output with Pydantic; it does not assume prose is JSON.
[Official non-interactive interface](https://learn.chatgpt.com/docs/non-interactive-mode)

The official MCP cookbook was evaluated, and installed SDK signatures were inspected. SDK 0.24.0
MCP discovery/tracing is modular; MCP execution/continuation stays refused until its schema and
native process/isolation semantics are certified. No old CLI was silently installed. No extra
planner model or outer Runner call is needed for this deterministic single-task transport.
[Official MCP/SDK cookbook](https://developers.openai.com/cookbook/examples/codex/codex_mcp_agents_sdk/building_consistent_workflows_codex_cli_agents_sdk)

Evidence: [runtime probes](codex-runtime.json), [SDK interfaces](codex-sdk.json), and the pinned
versions in [commands.json](commands.json). Authentication readiness does not prove a model call.

## 6. Agent execution examples

A developer task can prepare a Java/Python/Angular/PostGIS/integration proposal in literal
service-owned directories and then run administrator-allowlisted validators. Architect, analyst,
writer, manager, security, DevOps and QA roles can execute their permitted inspection/planning/
documentation operations against an approved milestone. New architecture/contract changes are
proposals rather than automatic replacement of approved source-of-truth documents.

A QA validation task can use VALIDATION_ONLY to execute exact approved command vectors without
calling a model. That mode cannot be substituted for validating a write proposal in a fresh
baseline worktree. Write-task validators run against the same proposed worktree after the model.

Model claims about commands/tests remain separate from observed orchestrator validation. A runtime
SUCCEEDED proposal without validators has implementation_verified=false and does not accept a
write task. That boolean means configured validator commands passed, not that every milestone
criterion or delivery approval has been independently established.

## 7. CLI commands and usage

~~~powershell
aeo codex doctor
aeo agents list
aeo agents describe solution-architect
aeo agent run --task TASK-UUID --mode WORKTREE_WRITE --scope src --scope tests --validate approved-test-id
aeo agent status --execution EXECUTION-ID
aeo agent approve --execution EXECUTION-ID
aeo agent run --execution EXECUTION-ID
aeo agent logs --execution EXECUTION-ID
aeo agent cancel --execution EXECUTION-ID
aeo agent reconcile
aeo agent resume --execution FAILED-ID --instructions "Review preserved evidence and propose this bounded recovery"
aeo agent cleanup --execution TERMINAL-ID
~~~

run --task prepares a reviewable pending request. It never implicitly starts a model. Review the
expanded validation argv, scope, hashes, role and runtime; authenticate exact execution approval;
then explicitly run --execution. Existing task-operation approval must already be recorded through
the foundation service where required. The imported plan and authenticated AEO-1C design must match.
The full configuration/operator guide is in the immutable [documentation bundle](../aeo-2/README.md).

## 8. Persistence changes and migrations

Migration 0004 adds executions, execution_grants and execution_attempts. Grants and attempt
history are append-only. State, related task/run outcomes and audit writes share transactions.
The unique nullable active slot atomically prevents two PREPARING/RUNNING executions globally.
No concurrent/distributed scheduling framework is introduced.

The live upgrade preservation check returned exit 0 and preserved all 13 pre-existing tables'
row counts and SHA256 digests. [Upgrade evidence](execution-upgrade.json) records before/after.
The final read-only live database audit found executions=0, execution_grants=0,
execution_attempts=0 and one observed documentation bundle. Thus no live task or human grant
was fabricated as validation evidence. Existing recovery snapshots and design history remain.

## 9. Security controls implemented

Execution grants bind exact task/project/milestone, role/specialization, repository/base commit,
worktree path, literal file scopes, artifact/context hashes, binary/version/model settings,
validator commands, correlation identity and bounded expiry. Interactive Windows authentication
returns an authorized SID; a claimed actor or boolean cannot approve. Design, operation,
execution and delivery authorizations remain separate. Expiry is rechecked while the process
runs and before each follow-up validation action; expired grants cannot launch validators.

Native Windows MXC enforces the generated named profile. Root reads are denied, minimal/target
reads allowed, writes limited to literal approved paths and networking disabled. Protected
metadata/approved artifacts stay inaccessible; connector apps, web, MCP, hooks and delegation
are disabled. Registry instructions use the documented developer-priority input. Unreviewed
runtime configuration and uncertified MCP/platform paths fail closed.
[Official permissions reference](https://learn.chatgpt.com/docs/permissions)

Actual native canaries passed for READ_ONLY, WORKTREE_WRITE and VALIDATION_ONLY: outside reads,
outside writes, out-of-scope writes and the controlled loopback connection were denied; inside
writes matched the mode. [Native evidence](codex-runtime.json) records these results. No admin
sandbox provisioning, firewall edits, execution-policy bypass or model call was performed.
[Official Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox)

Trusted Git worktree creation disables hooks and configured filters and receives no Codex API
credential. User worktrees are never reset/cleaned/overlaid. Windows kill-on-close jobs own process
trees before prompt stdin. Cancellation is confirmed only after termination; unknown PID identities
block recovery. Partial work is bounded and retained. Cleanup requires a verified preserved archive
and unchanged workspace hashes, and it preserves task branch refs. No source branch is committed,
pushed, merged, deployed or connected to production infrastructure.

Prompts/logs redact known secret values and common credential patterns; child environments exclude
production/cloud/database credentials. Raw evidence is stored separately from normalized results.
SDK tracing is metadata-only and opt-in; cost estimates require explicit configured rates.

## 10. Unit and integration test results

Final scripts/validate.py: exit 0. Pytest: 116 passed in 125.92s (0:02:05). All 16 retained commands returned 0,
including Ruff lint/format, pip check, Alembic upgrade/check, legacy inspection/plan/design CLI,
role CLI, artifact-manifest validation, offline smoke entry and dependency inventory.
Full argv, stdout, stderr and timestamps: [commands.json](commands.json). Cases: [pytest.xml](pytest.xml).

New tests cover successful normalized execution, original dirty-worktree preservation, literal
scope violations, startup/auth/parse failures, timeout and cancellation, missing/expired grants,
context/role drift, independent validator success/failure, no-model validation-only runs,
conservative recovery, unsafe cleanup refusal, immutable grants/attempts, unknown process identity,
MCP incompatibility, blocked hooks, atomic single-active enforcement, duplicate command settings,
normal-language-safe redaction and grant expiry before follow-up actions. Integration uses mocked
Codex/MCP behavior and temporary Git repositories. Real harmless process timeout/cancellation and
separate native canaries also ran. No application repository was modified for generated test outputs.

Intermediate findings were corrected: required CLI selectors initially used positional parameters;
formatter changes to a fenced example were caught by immutable hashes, the exact scope baseline
was restored and immutable revisions excluded from formatting; native configuration serialization,
Windows core environment and protected nested-path handling were corrected before the canaries
passed. A broad secret regex was narrowed and regression-tested. A redundant validation run was
interrupted while the expiry guard was finalized; the final complete run above supersedes it.
A read-only audit command quoting error was replaced with a structured script. No unresolved
unit, integration, static-analysis, dependency or migration failure remains.

## 11. Live smoke test status

**NOT RUN / NOT VERIFIED.** No model quota or API billing was intentionally consumed. The normal
smoke entrypoint returned SKIPPED, and ordinary validation never invokes a model. The separate
script requires --live and an authorized interactive human decision. It creates a temporary fixture
Git source/worktree, uses the restricted sandbox, asks for a harmless generated file, verifies that
file and checks original repository state, then retains output/evidence. It is a transport smoke,
not a fabricated application-design approval or full delivery test.

~~~powershell
python scripts/codex_live_smoke.py --live
~~~

No permission to run that optional billed action is inferred from this implementation request.

## 12. Known limitations

- Live Codex task execution and live session continuation are implemented but remain unverified
  until an explicit successful model test. Login/health and native canaries are narrower evidence.
- Installed Codex cannot expose MCP server tools; SDK MCP execution is intentionally unavailable.
- Native Windows MXC is the certified isolation target. Other platforms and weaker fallbacks refuse execution.
- Current non-destructive canaries require a directory write scope. Literal whole-root writes,
  protected controls, approved revisions and authoritative contract roots are not writable.
- All role execution uses already approved design context. AEO-1C's default template author and rule
  reviewer are not silently replaced by live design agents; pre-approval live authoring needs a
  separately reviewed integration. Proposed documentation can be produced in approved proposal scopes.
- The local administrator, installed runtime and trusted configuration/database owner remain trusted.
  This is not multi-tenant authentication or distributed orchestration.
- Context/whole-worktree artifact budgets deliberately block oversized inputs or large worktrees;
  symlinks/junctions and known-secret outputs can require manual review.
- Reports are available after process exit; a crash preserves DB history/worktree state but disk
  report publication is not one atomic transaction with SQLite.
- Recovery creates a new bounded scope using prior result/evidence metadata and explicit operator
  instructions. It retains old worktrees and does not automatically transplant partial patches or
  replay writes. Cancelled tasks remain terminal under the existing lifecycle. There are no automatic retries.
- PlantUML rendering is unavailable until a trusted JAR is configured. All five source structures and
  hashes were checked, but no actual syntax/render pass or SVG is claimed. Findings are retained.

## 13. Remaining operating dependencies

Configure an approved application plan/design, source manifests, canonical human SID allowlists,
original operation approvals, exact validation argv and live_enabled deliberately. Install the
project codex extra for SDK features; the inspected versions are openai-agents 0.24.0, MCP 2.3.0
and OpenAI Python 3.37.0. Codex needs supported login or secure CODEX_API_KEY and native Git/MXC.
Select a model explicitly when required through Settings. A trusted PlantUML JAR is still needed
for rendered diagrams and AEO-1C design approval. Live Windows authentication itself was not
exercised unattended; tests used explicit fake identities.

## 14. Recommended AEO-3 scope

Start with separately approved workflow/dependency scheduling, typed role handoff consumption,
reviewed proposal/patch context transfer, durable leases/recovery and budget enforcement. Retain
the single-active boundary until a concurrency design and isolation tests are explicitly approved.
Do not automatically add milestone selection, multi-repository PRs, merge, production deployment
or agent delegation. No AEO-3 work is started by this release.
