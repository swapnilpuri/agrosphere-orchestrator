# AEO-6 — Autonomous Milestone Execution and End-to-End Engineering Orchestration

## ROLE

Act as Principal AI Systems Architect, Autonomous Software Engineering Architect, Multi-Agent Systems Engineer, Senior Python Developer, DevOps Architect, and Software Quality Engineering Lead.

You are continuing the existing **AgroSphere AI Engineering Orchestrator (AEO)** using OpenAI Codex in VS Code.

Your task is to implement **AEO-6 — Autonomous Milestone Execution**, integrating the existing AEO-1 through AEO-5 capabilities into a reliable, policy-governed, resumable autonomous software engineering workflow.

This is an implementation milestone, not merely an architecture assessment or planning exercise.

However, all implementation must respect the existing AEO-1C documentation and design approval workflow, AEO-4 security and quality governance, and AEO-5 privileged delivery permissions.

Do not bypass approvals to accelerate development.

---

## 1. CURRENT VERIFIED BASELINE

The authoritative workspace is:

`C:\Projects\agrosphere`

The orchestrator repository is:

`C:\Projects\agrosphere\agrosphere-orchestrator`

The existing configured SQLite database is `aeo.db`, with existing environment and policy configuration.

Use actual runtime configuration to verify these locations rather than assuming they cannot change.

### AEO-5R acceptance findings

The October 25, 2026 acceptance report states:

- AEO-5 local implementation accepted.
- Full validation suite: 275 tests passed.
- All 163 original baseline test IDs preserved.
- 112 additional tests passing.
- Alembic migration 0007 added durable delivery tables.
- All 24 pre-existing database tables preserved.
- GitHub provider, branch, PR, CI, approval, recovery, evidence and CLI capabilities implemented.
- Mocked end-to-end delivery tests passed.
- No live GitHub publishing was performed.
- Remote writes remain disabled by default.
- Real AEO-5 runtime milestone remains IMPLEMENTING.
- Formal runtime delivery and publication approvals remain outstanding.

**Do not interpret local implementation acceptance as formal runtime milestone completion.**

### Critical instruction

Before building AEO-6, independently verify the AEO-5 baseline and identify any prerequisites that remain blocked.

Do not fabricate AEO-5 completion, publishing grants, CI checks, PRs, or production validation.

You may implement and locally test AEO-6 against the accepted AEO-5 interfaces while its separate runtime delivery remains pending, provided the current approval policy permits this work.

---

## 2. PRIMARY OBJECTIVE

Create an Autonomous Engineering Controller that can safely:

1. Discover current AgroSphere repositories and project state.
2. Reconcile previous milestone history and implementation evidence.
3. Identify the next eligible, approved or proposed application milestone.
4. Generate milestone business and technical explanations.
5. Generate architecture documents, diagrams and design decisions.
6. Register and validate technical design revisions.
7. Request authenticated human approval when necessary.
8. Resume automatically after the approval has been recorded.
9. Convert approved designs into structured engineering plans.
10. Assign work to the existing specialized agents.
11. Execute tasks using existing Codex adapters.
12. Schedule independent tasks concurrently.
13. Enforce repository and worktree isolation.
14. Verify task completion with independent quality gates.
15. Perform bounded, authorized remediation.
16. Coordinate validated changes through AEO-5 delivery services.
17. Monitor PRs, CI results, reviews and delivery dependencies.
18. Generate final implementation and delivery reports.
19. Persist all lifecycle transitions and artifacts.
20. Recover safely from interruptions.
21. Advance to another milestone only when the current milestone is verified complete and authorization explicitly permits advancement.

Do not implement an unbounded autonomous loop.

Do not automatically merge or deploy software.

---

## 3. NON-NEGOTIABLE ARCHITECTURAL PRINCIPLES

1. Preserve the entire AEO-1 through AEO-5 codebase.
2. Reuse existing domain models, adapters, persistence, state machines and CLI conventions.
3. Avoid duplicate implementations of existing capabilities.
4. Keep the orchestration engine deterministic.
5. Use LLM agents for reasoning, generation and implementation, not governance authorization.
6. Enforce approved design revisions before implementation.
7. Enforce AEO-4 independent quality and security gates.
8. Enforce AEO-5 privileged execution approval for remote writes.
9. Preserve independent Git repositories and worktree isolation.
10. Prevent concurrent conflicting writes.
11. Persist durable intent and execution state.
12. Do not invent task completion or evidence.
13. Do not allow unbounded retries or uncontrolled iteration.
14. Never bypass failed or missing approvals.
15. Keep all settings centralized.
16. Support Windows PowerShell and the established Python environment.
17. Do not introduce additional databases, queues, distributed services or web applications without a demonstrated need.
18. Do not generalize AEO into a multi-project platform.
19. Do not create the future Orchestrator Control Center UI.
20. Do not automatically start new AgroSphere application work during AEO-6 implementation or validation.

Use the existing application architecture as the source of truth where it differs from this prompt.

---

## 4. PRE-IMPLEMENTATION DISCOVERY

Inspect the actual orchestrator codebase.

Discover and document the relevant interfaces for:

- AEO-1 milestone and state models
- AEO-1B repository and roadmap recovery
- AEO-1C requirements, design generation, validation and approval
- AEO-2 Codex execution and agent context
- AEO-3 task DAG, scheduler, locks and recovery
- AEO-4 policy, validation, security, approval and remediation
- AEO-5 delivery coordinator, GitHub provider, persistence and evidence
- Existing CLI and configuration mechanisms
- Existing tests, fixtures and sample milestone definitions

Inspect actual application repository history to determine how far AgroSphere development progressed through Milestone 3.

Do not assume an application milestone was completed merely because a document or source directory exists.

Generate:

`docs/milestones/AEO-6/01-existing-capability-assessment.md`

Include a traceability matrix showing:

- Existing component
- Existing interface
- Reuse strategy
- Missing integration
- Required modification
- Associated tests
- Risks and dependencies

Identify which capabilities can be connected without substantial new implementation.

---

## 5. DOCUMENTATION-FIRST DEVELOPMENT

Follow the established AEO-1C workflow.

Prepare these AEO-6 documents:

`docs/milestones/AEO-6/02-architecture.md`

`docs/milestones/AEO-6/03-autonomous-lifecycle.md`

`docs/milestones/AEO-6/04-state-and-recovery-model.md`

`docs/milestones/AEO-6/05-governance-and-authorization.md`

`docs/milestones/AEO-6/06-implementation-plan.md`

`docs/milestones/AEO-6/07-acceptance-criteria.md`

`docs/milestones/AEO-6/diagrams/`

Include PlantUML diagrams for:

1. C4 component architecture
2. Autonomous milestone lifecycle
3. Multi-agent orchestration sequence
4. Human approval and resumption
5. Durable state machine
6. Interruption recovery
7. Repository execution and delivery boundaries
8. End-to-end milestone execution
9. Cross-repository dependencies

Reuse existing design narratives and diagrams where applicable.

Register the AEO-6 requirements through the existing supported workflow.

Complete all permitted preparation and validation automatically.

If authenticated requirements or design approval is required, stop at that precise approval checkpoint.

Provide the exact PowerShell command supported by the current CLI.

Do not pretend approval exists.

Do not insert approval records directly into the database.

After the user records approval, verify the exact approved scope and resume from the persisted state.

Do not repeatedly ask for an approval that is already valid for the current immutable scope.

---

## 6. AUTONOMOUS ENGINEERING CONTROLLER

Implement an orchestration application service provisionally called:

`AutonomousMilestoneController`

Use the existing package conventions to determine its actual name and location.

Its responsibilities are:

- Load persistent milestone state
- Reconcile current repository facts
- Evaluate milestone eligibility
- Select the next permitted workflow transition
- Dispatch an existing application service
- Persist operation intent
- Observe and validate operation results
- Record artifacts and evidence
- Enforce safety and authorization
- Pause at required checkpoints
- Resume after verified state changes
- Produce status and outcome reports

The controller must not directly duplicate:

- GitHub API calls
- Codex process management
- Agent task scheduling
- Quality validation logic
- Approval policy evaluation
- Git worktree management

Delegate these operations to existing AEO services.

### Deterministic execution

The controller must select transitions according to explicit state and policy rules.

LLM-generated text must not determine whether a permission or approval requirement can be skipped.

Unknown state, conflicting records, or unverified identity must result in a blocked or recovery-required outcome.

### Execution limits

Support configurable limits for:

- Maximum milestones per run
- Maximum tasks per run
- Maximum concurrent agents
- Maximum repair attempts
- Maximum elapsed execution time
- Maximum estimated resource or model budget
- Maximum delivery polling duration

Where accurate cost estimation is unavailable, explicitly mark it unknown and enforce available hard limits.

Initial autonomous application execution should default to a single authorized milestone.

Do not create an infinite milestone advancement loop.

---

## 7. MILESTONE SELECTION AND RECOVERY

Integrate existing AEO-1B project discovery.

Determine milestone eligibility based on:

- Actual repository state
- Recovered application milestone history
- Approved roadmap
- Dependency completion
- Existing task progress
- Requirements status
- Design status
- Existing execution records
- Delivery state
- Human authorization
- Security and policy constraints

Support:

- Proposed milestone
- Approved milestone
- Partially implemented milestone
- Blocked milestone
- Completed milestone
- Interrupted milestone
- Milestone with pending delivery

Do not restart completed tasks.

Do not mistake a locally accepted implementation for a formally completed delivered milestone.

### Reconciliation first

Before selecting new work:

1. Read persistent state.
2. Discover actual Git repository and worktree state.
3. Locate existing related execution records.
4. Reconcile task and delivery outcomes.
5. Identify unresolved operations.
6. Require safe recovery before continuing conflicting work.

If the next milestone cannot be determined reliably, produce a clear blocked report with supporting evidence.

Do not invent a milestone or assume a numeric sequence is authoritative.

---

## 8. AUTOMATIC MILESTONE EXPLANATIONS AND DIAGRAMS

This is a mandatory feature.

In the previous manual development workflow, ChatGPT explained each milestone and generated diagrams before producing implementation prompts.

AEO-6 must preserve that experience automatically.

For every selected application milestone, generate and persist a readable milestone explanation containing:

- Business context
- Objectives
- Scope
- Major features
- Functional requirements
- Nonfunctional requirements
- Existing architectural dependencies
- Proposed components
- Cross-service interactions
- Database impact
- API/event contract impact
- Security considerations
- Testing strategy
- Implementation phases
- Risks and assumptions
- Acceptance criteria

Generate appropriate C4 and PlantUML diagrams.

Store artifacts in their correct repositories:

- Cross-service design: `agrosphere-architecture`
- API/event contracts: `agrosphere-contracts`
- Service-specific designs: relevant service repository
- Orchestration state and manifests: `agrosphere-orchestrator`

Repository names must be confirmed through discovery.

Design drafts must not overwrite approved designs.

Use revisions and content hashes.

If artifacts are changed after approval, apply the existing invalidation and reapproval policies.

No source implementation may begin until the required design gate passes.

---

## 9. APPROVAL-AWARE AUTOMATIC CONTINUATION

Implement a workflow checkpoint system that distinguishes:

- Automatically executable work
- Work requiring design approval
- Work requiring security approval
- Work requiring privileged GitHub execution approval
- Work requiring a human recovery decision
- Work blocked by invalid or conflicting state

### Expected behavior

If the workflow reaches an approval boundary:

1. Complete all authorized preparatory steps.
2. Validate and persist the work requiring approval.
3. Generate the review package.
4. Report exactly which decision is required.
5. Provide the precise existing CLI approval command.
6. Persist the blocked/awaiting-approval checkpoint.
7. Stop unauthorized execution.
8. Resume only when the approval is recorded and verified.

Resumption may occur through an explicit CLI continuation or an already established authorized scheduling mechanism.

Do not require a new infrastructure service to poll continuously for approvals.

Do not equate a user's chat message with a formal authenticated approval decision.

### Important correction from AEO-5 experience

AEO must not repeatedly ask the user to perform steps that the orchestration application is already authorized to perform.

For example, a missing design revision should cause the controller to execute the existing design preparation and validation workflow, not immediately ask the user whether the design exists in another database.

Only genuine approval, authorization, unresolved ambiguity or unsafe recovery conditions should require human intervention.

---

## 10. MULTI-AGENT IMPLEMENTATION

Integrate the existing AEO-3 multi-agent organization.

Preserve existing agent roles:

- Program Manager
- Project Manager
- Business Analyst
- Solution Architect
- Developer
- QA Engineer
- Security Engineer
- DevOps Engineer
- Technical Writer

Use the existing developer specializations as appropriate.

### Agent responsibilities

The Program Manager coordinates milestones and escalation.

The Project Manager converts approved plans into dependency-aware tasks.

The Business Analyst verifies requirements.

The Solution Architect verifies architecture and contracts.

Developers implement code and unit tests.

QA performs independent validation.

Security verifies relevant controls.

DevOps handles authorized infrastructure and delivery tasks.

Technical Writer maintains documents and diagrams.

### Execution requirements

Reuse the existing:

- Agent registry
- Task contracts
- DAG scheduler
- Codex execution adapter
- Execution context assembly
- Worktree manager
- Repository locks
- Handoff records
- Persistence
- Retry and remediation logic

Do not create a second independent scheduler.

Do not permit agents to self-authorize privileged operations.

Independent tasks may execute concurrently only when existing locks and dependencies allow it.

### Agent handoffs

Every agent output must be structured and reference evidence.

Require:

- Task ID
- Agent role
- Repository
- Inputs and prerequisite references
- Actions performed
- Output artifacts
- File or commit references
- Test results, when applicable
- Remaining blockers
- Recommended next action

Validate agent outputs before allowing state transitions.

---

## 11. QUALITY ENGINEERING AND REMEDIATION

After task execution, invoke existing AEO-4 quality and governance components.

Include:

- Unit tests
- Integration tests
- Acceptance-criteria verification
- Architecture compliance
- API and event contract validation
- Documentation validation
- Security policies
- Dependency and vulnerability checks, when available
- Cross-repository compatibility

A developer's success message is not sufficient evidence.

Independent quality checks must confirm completion.

### Automatic repair

When a task fails:

1. Classify the failure.
2. Determine whether remediation is permitted.
3. Record failure evidence.
4. Assign repair work to an appropriate existing agent.
5. Limit retries using configured policies.
6. Re-run required verification.
7. Stop and escalate when retry limits or policy boundaries are reached.

Preserve the previous default limit of three automatic repairs unless current configuration specifies otherwise.

Do not automatically modify quality policy merely to pass validation.

Do not allow remediation to invalidate an approved design without triggering the appropriate reapproval workflow.

---

## 12. CONTROLLED GITHUB DELIVERY

Reuse AEO-5.

After implementation and required local validations:

1. Construct the milestone delivery manifest.
2. Map changes to independent repositories.
3. Verify branch and source identities.
4. Determine applicable publication policies.
5. Verify required AEO-4 quality/security evidence.
6. Request separate privileged publication authorization when required.
7. Prepare approved branches and PRs only if authorized.
8. Monitor CI and required human reviews.
9. Reconcile remote state.
10. Produce milestone delivery reports.

### Critical boundaries

- Do not automatically enable remote writes.
- Do not assume successful mocked GitHub tests authorize live writes.
- Do not create duplicate PRs.
- Do not force-push.
- Do not merge PRs.
- Do not deploy applications.
- Do not bypass branch protection or CODEOWNERS.
- Do not invent CI successes or reviews.
- Do not mark a milestone formally delivered merely because PRs exist.

If the requested delivery action is outside granted permissions, stop at the existing authorization gate.

### Completion semantics

Distinguish at least:

- Implementation complete
- Local quality accepted
- Ready for authorized publication
- PR published
- Awaiting CI/review
- Ready for authorized merge
- Externally merged/accepted, if verified
- Formally completed, if supported by policy
- Blocked

AEO-6 must not weaken the existing AEO-5 delivery state model.

---

## 13. DURABLE EXECUTION AND INTERRUPTION RECOVERY

Build on AEO-3 and AEO-5 persistent recovery.

Do not introduce conflicting recovery mechanisms.

Persist enough information to safely resume:

- Autonomous run ID
- Milestone ID
- Active workflow step
- Task and agent execution IDs
- Approval checkpoint
- Approved design revision
- Task and dependency state
- Relevant repository and commit identity
- Artifact manifest and hashes
- Quality gate state
- Delivery operation references
- Retry counts
- Failure classification
- Authorized next transition

### Required recovery scenarios

Test:

1. Crash during milestone discovery
2. Crash after documentation generation
3. Crash before design approval
4. Restart after design approval
5. Crash during task decomposition
6. Crash during an agent execution
7. Crash after an agent finishes but before persistence
8. Crash during parallel scheduling
9. Crash during quality checks
10. Crash during remediation
11. Crash before GitHub publication
12. Crash after a remote operation succeeded
13. Restart when PR or CI status changed externally
14. Restart with modified approved design artifacts
15. Restart when approval has expired or been revoked
16. Restart with repository/worktree conflicts

Recovery must reconcile actual state before replaying operations.

Do not blindly relaunch Codex tasks when previous outcomes are uncertain.

Do not discard or overwrite partial artifacts.

Retain previous execution history.

---

## 14. AUTONOMOUS EXECUTION CLI

Extend the existing Typer CLI.

Follow current command conventions and use existing services.

Provide operations conceptually equivalent to:

```text
aeo autonomous plan
aeo autonomous start
aeo autonomous status
aeo autonomous pause
aeo autonomous resume
aeo autonomous recover
aeo autonomous report
aeo autonomous validate
```

Exact commands and parameters must be determined from the current implementation.

### Recommended modes

#### Dry-run

No Codex source modification, branch publication or remote mutation.

Produce the proposed milestone, execution DAG, approval requirements and expected operations.

#### Simulation

Use mocked agents, GitHub providers and temporary repositories/databases.

Execute the complete orchestration workflow without affecting real application repositories.

#### Local execution

Permit explicitly authorized local Codex execution with existing worktree isolation.

Do not infer permission from the selected mode alone.

#### Controlled delivery

Permit remote publishing only when all existing policies, approvals and privileged grants are satisfied.

Never merge or deploy.

### Required controls

Support:

- Explicit milestone selection
- Automatic next-eligible milestone selection
- Maximum milestone count
- Maximum task count
- Concurrent-agent limit
- Retry limit
- Run budget
- Stop-on-gate behavior
- Resume by persisted run ID
- Read-only status inspection
- JSON and Markdown reports

Default to the safest non-mutating mode.

Do not cause an ordinary status or plan command to modify application repositories.

---

## 15. RESOURCE AND EXECUTION BUDGETS

Implement configurable execution limits using existing settings.

At minimum:

- Maximum Codex invocations
- Maximum execution attempts
- Maximum active tasks
- Maximum total run duration
- Maximum milestones per run
- Maximum agent concurrency

Record available token and cost usage when exposed by existing provider interfaces.

Do not fabricate usage measurements.

If budget limits are reached, persist a resumable paused state and provide a clear explanation.

The controller must never silently exceed established limits.

---

## 16. OBSERVABILITY, LOGGING AND REPORTING

Reuse existing structured JSON logging, traces and evidence facilities.

Every autonomous run must provide:

- Run ID
- Milestone ID
- Selected workflow
- Current state
- Completed stages
- Active agents
- Pending dependencies
- Blocked approvals
- Generated documentation
- Diagrams
- Code artifacts
- Validation results
- Repository and commit identities
- GitHub delivery status
- Recoverability status
- Resource usage, when available
- Next permitted action

Maintain artifact manifests referencing the authoritative repositories and files.

Do not duplicate large generated artifacts in SQLite unless required by existing design.

AEO should make it possible to reconstruct why any particular action was executed or blocked.

### Milestone completion report

Generate a final report including:

1. Milestone objectives
2. Approved design and revision
3. Participating agents
4. Tasks completed
5. Repositories changed
6. Files and artifacts produced
7. Testing and quality evidence
8. Security review results
9. GitHub delivery state
10. Outstanding approvals
11. Recovery or remediation history
12. Known limitations
13. Formal completion status
14. Eligibility of the next milestone

Do not infer formal completion from local test success alone.

---

## 17. IMPLEMENTATION PHASES

Implement AEO-6 incrementally.

### AEO-6A — Discovery, architecture and approval

- Inspect AEO-1 through AEO-5.
- Verify the accepted local AEO-5 implementation.
- Record outstanding runtime delivery limitations.
- Produce AEO-6 requirements, architecture and diagrams.
- Register requirements and design revisions.
- Run existing validation.
- Obtain authenticated approvals.

Stop at required human approval checkpoints.

### AEO-6B — Autonomous controller

- Create deterministic lifecycle controller.
- Integrate existing milestone state.
- Implement eligible-transition selection.
- Add run limits, status and persistence.
- Add unit tests.

### AEO-6C — Design-first lifecycle automation

- Integrate repository discovery.
- Select milestones from recovered state.
- Generate explanations and diagrams.
- Register technical design revisions.
- Validate design.
- Implement approval-aware pausing and resuming.

### AEO-6D — Multi-agent execution

- Integrate task decomposition.
- Reuse agent registry and Codex adapter.
- Reuse DAG scheduling and worktree isolation.
- Track task and artifact completion.
- Implement bounded recovery and retry.

### AEO-6E — Quality and delivery integration

- Run AEO-4 quality/security verification.
- Integrate bounded remediation.
- Build AEO-5 delivery manifests.
- Enforce privileged publishing policy.
- Integrate delivery status and readiness reporting.

### AEO-6F — End-to-end simulation and recovery

- Execute complete simulated milestones.
- Use realistic temporary multi-repository fixtures.
- Test approvals, failures, restarts and delivery dependencies.
- Confirm no unauthorized mutations.

### AEO-6G — Controlled local proof of concept

- Validate the full local workflow against an explicitly authorized, bounded proof-of-concept scope.
- Prefer an isolated test milestone and safe working environment.
- Use actual Codex execution only when the operator has authorized local execution.
- Preserve real AgroSphere application state.
- Do not create live PRs without separate authorization.
- Generate an evidence-based acceptance report.

Do not silently promote a simulated success into a production readiness claim.

---

## 18. TESTING REQUIREMENTS

### Baseline regression

Run the standard validation suite.

All 275 previously passing tests must remain present and pass, unless a documented legitimate migration changes test organization without reducing coverage.

### Unit tests

Cover:

- Eligible milestone selection
- Invalid milestone rejection
- State transition enforcement
- Approval checkpoint detection
- Design validation requirements
- Task DAG integration
- Agent handoff validation
- Budget exhaustion
- Retry limits
- Duplicate execution prevention
- Completion eligibility

### Integration tests

Cover:

- Discovery to design generation
- Design to approval checkpoint
- Approved design to task execution
- Multi-agent dependency scheduling
- Independent QA validation
- Automatic remediation
- Delivery manifest generation
- Delivery authorization enforcement
- Final reporting

### End-to-end tests

Create a realistic isolated AgroSphere-like fixture with at least three independent repositories.

Execute a simulated lifecycle:

1. Discover incomplete milestone.
2. Generate milestone design.
3. Validate design.
4. Pause for approval.
5. Record simulated test approval through supported authenticated fixture mechanisms.
6. Resume.
7. Generate task DAG.
8. Execute mocked agents.
9. Validate outputs.
10. Simulate a failed quality gate.
11. Perform one permitted remediation.
12. Revalidate.
13. Prepare delivery manifest.
14. Verify publication approval requirements.
15. Simulate permitted GitHub publication.
16. Reconcile PR checks and reviews.
17. Generate milestone report.
18. Verify formal completion is not falsely asserted.
19. Recover successfully after restart.

All test approvals must be clearly isolated and must not contaminate the real approval database.

### Security tests

Confirm:

- No agent self-approval
- No unauthorized Codex execution
- No unauthorized GitHub mutation
- No approval bypass
- No protected branch modification
- No duplicate delivery PRs
- No unbounded retry
- No unsafe command execution
- No leaking secrets
- No unauthorized automatic milestone advancement

### Windows compatibility

Test important CLI, Git, worktree, persistence and artifact workflows on Windows-compatible paths.

Preserve the existing path-length protections and error behavior.

---

## 19. ACCEPTANCE CRITERIA

AEO-6 is locally accepted only when:

1. AEO-1 through AEO-5 capabilities remain functional.
2. The complete existing regression suite passes.
3. The autonomous controller is implemented, not merely documented.
4. Repository discovery identifies real persisted project progress.
5. Milestone selection respects actual dependencies and approvals.
6. Design documentation and diagrams are generated and retained.
7. Formal AEO-1C approvals are enforced.
8. Valid existing approvals are recognized without repeated prompts.
9. Multi-agent tasks execute through existing Codex and scheduler adapters.
10. Conflicting repository writes remain prevented.
11. Task handoffs and results are persisted.
12. AEO-4 quality/security verification is enforced.
13. Automatic remediation is bounded.
14. AEO-5 delivery integration is reused.
15. Publication remains separately authorized.
16. Recovery is demonstrated across lifecycle boundaries.
17. An end-to-end simulated milestone completes to the correct authorized state.
18. A complete run report with verified artifacts can be generated.
19. A failed approval or quality gate blocks further execution.
20. Resource and iteration limits are enforced.
21. Real AgroSphere repositories remain unchanged during default simulation.
22. No automatic merges or deployments occur.
23. Formal milestone completion is never fabricated.
24. No unapproved application milestone starts.
25. AEO-6 does not introduce unnecessary new infrastructure or multi-project functionality.

---

## 20. REQUIRED FINAL DELIVERABLES

Generate:

`docs/milestones/AEO-6/AEO-6_ACCEPTANCE_REPORT.md`

Also generate or update:

- Architecture documentation
- PlantUML diagrams
- Execution state-machine documentation
- CLI operation guide
- Autonomous lifecycle guide
- Approval and recovery guide
- Test results and evidence
- Implementation inventory
- End-to-end simulated run report
- Known limitations and blockers

The acceptance report must identify:

1. Actual code modules created/modified
2. Reused existing AEO modules
3. Database schema changes, if any
4. Registered design approval evidence
5. New CLI commands
6. New tests and passing counts
7. Existing regression results
8. End-to-end test outcomes
9. Actual Codex execution status
10. Approval and security verification
11. Durable recovery evidence
12. Repo and Git safety results
13. Local acceptance recommendation
14. Remaining live/runtime validation requirements
15. Exact next authorized operator actions

Clearly distinguish:

- Unit-tested
- Integration-tested
- Simulated end-to-end
- Locally executed with real Codex
- Live GitHub verified
- Not tested
- Pending authorization

---

## 21. COMPLETION BOUNDARY

After implementation and testing:

1. Generate the AEO-6 acceptance report.
2. Provide a full test summary.
3. Provide the safe dry-run CLI command.
4. Provide the simulation CLI command.
5. Provide the approved local-execution command pattern.
6. Provide the current recovered AgroSphere milestone summary.
7. Identify the next candidate application milestone with supporting evidence.
8. Explain all remaining approval requirements.
9. Stop.

Do not automatically execute a real AgroSphere application milestone.

Do not merge, deploy or publish code without required authorization.

Do not generalize the orchestrator for HRMS or other projects.

Do not build the Orchestrator Control Center UI.

The first actual autonomous AgroSphere development run will require a separate explicit instruction after AEO-6 local acceptance.

## START NOW

Start by inspecting the existing AEO codebase and persisted state.

Perform AEO-6A discovery and documentation preparation.

Use the existing AEO-1C requirements and technical design approval workflow.

Proceed through authorized implementation stages after valid approval.

Implement the complete AEO-6 controller and integration capabilities, verify them using actual tests, and produce the final acceptance report.

Do not stop at planning unless a genuine approval or security boundary requires it.