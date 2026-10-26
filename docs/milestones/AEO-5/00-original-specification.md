# AEO-5 — GitHub Integration, Pull Request Automation, Durable Recovery & Delivery Evidence

## ROLE

Act as a Principal AI Systems Architect, Senior Python Engineer, DevOps Architect, GitHub Integration Specialist, and Multi-Agent Systems Engineer.

You are continuing development of the existing **AgroSphere AI Engineering Orchestrator (AEO)**.

The previous milestones AEO-1, AEO-1B, AEO-1C, AEO-2, AEO-3, and AEO-4 have been completed.

Your task is to implement **AEO-5 — GitHub Integration, Pull Request Automation, Durable Recovery & Delivery Evidence**.

This is an incremental implementation. Do not regenerate the project, overwrite existing functionality, or rebuild completed capabilities.

## 1. NON-NEGOTIABLE INSTRUCTIONS

1. Inspect the existing workspace and orchestrator implementation before modifying anything.
2. Treat actual repository code, persistence migrations, configuration, and tests as the source of truth.
3. Preserve all existing milestones, architecture decisions, tests, and documentation.
4. Reuse existing persistence, policies, execution records, agents, logging, and state machines wherever practical.
5. Maintain clean architecture and modular Python code.
6. Use Python 3.12+, Pydantic v2, SQLAlchemy 2.x, Alembic, Typer, pytest and Ruff where already established.
7. Do not introduce additional infrastructure without demonstrated need.
8. Do not introduce generic multi-project orchestration.
9. Continue supporting the existing independent Git repositories.
10. Generate milestone documentation and diagrams before implementation.
11. Do not bypass AEO-4 quality, security, approval, or evidence requirements.
12. All remote operations must be explicitly authorized and fail closed.
13. Do not merge pull requests or deploy applications.
14. Do not automatically begin AEO-6.
15. Do not assume tests have passed without executing them.
16. Prefer reasonable documented defaults rather than repeatedly asking implementation questions.
17. Never delete or overwrite existing user work.
18. Do not commit changes or push branches as a side effect of inspection or validation.

Use the official GitHub documentation and installed CLI capabilities to verify implementation details rather than relying on unverified command flags or API behavior.

## 2. PRE-IMPLEMENTATION DISCOVERY

Before writing code, inspect:

- Existing orchestrator package structure
- Existing Typer CLI commands
- Persistence models and Alembic migrations
- AEO-2 Codex execution adapters
- AEO-3 task scheduler and recovery mechanisms
- AEO-4 quality gates, approval records, security policies, and evidence models
- Repository discovery and worktree handling
- Existing Git helper functions
- GitHub Actions configurations
- Architecture documentation and architectural decisions
- Existing test patterns
- Environment and configuration management

Discover actual repositories from the workspace; do not assume names beyond those found.

Determine which AEO-5 capabilities are partially implemented already.

Generate:

`docs/milestones/AEO-5/01-existing-capability-assessment.md`

The assessment must include existing functionality, reusable interfaces, missing capabilities, architectural conflicts, risks, and the intended modification plan.

Identify the applicable baseline commits and working-tree changes. Do not overwrite or clean uncommitted modifications.

If a prerequisite is missing, implement only the smallest compatible extension needed, and document the deviation.

## 3. DOCUMENTATION-FIRST DESIGN

Before implementation, generate:

`docs/milestones/AEO-5/02-architecture.md`

`docs/milestones/AEO-5/03-workflows.md`

`docs/milestones/AEO-5/04-security-and-approvals.md`

`docs/milestones/AEO-5/05-implementation-plan.md`

`docs/milestones/AEO-5/06-acceptance-criteria.md`

`docs/milestones/AEO-5/diagrams/`

Include PlantUML diagrams for:

1. AEO-5 component architecture
2. GitHub delivery sequence
3. Multi-repository PR coordination
4. Delivery state machine
5. Durable recovery workflow
6. Approval and quality-gate enforcement

Use C4-PlantUML where appropriate.

Respect existing documentation ownership rules:

- Cross-service AgroSphere architecture belongs in `agrosphere-architecture`.
- Shared API and event contracts belong in `agrosphere-contracts`.
- Microservice implementation documentation belongs in its respective repository.
- AEO-specific architecture, delivery state, and evidence belong in `agrosphere-orchestrator`.

Do not change unrelated application repositories simply to document the orchestrator milestone.

Use the existing AEO-1C documentation approval workflow. Before requesting approval, generate and validate the documentation and diagrams. Do not proceed to implementation if a required approval is pending or denied.

## 4. GITHUB INTEGRATION ARCHITECTURE

Create a modular GitHub integration using ports and adapters.

Suggested conceptual components:

- `GitHubProvider`
- `GitHubCliAdapter`
- `RepositoryDiscoveryService`
- `BranchManagementService`
- `PullRequestService`
- `GitHubChecksService`
- `ReviewVerificationService`
- `DeliveryCoordinator`
- `DeliveryRecoveryService`
- `DeliveryEvidenceService`
- `DeliveryReportService`

Names and files are illustrative. Adapt them to the actual existing architecture.

### GitHubProvider

Define an interface supporting:

- Get repository metadata
- Discover remote branches
- Identify default branch
- Inspect current authenticated principal and relevant permissions
- Find matching pull requests
- Create a pull request
- Retrieve pull request details
- Retrieve review decisions
- Retrieve CI checks
- Retrieve branch restrictions and ruleset information when accessible
- Retrieve commits and relevant GitHub metadata

Prefer a `GitHubCliAdapter` for the initial implementation if the existing environment supports authenticated GitHub CLI access.

Use controlled subprocess argument arrays, explicit working directories, bounded timeouts, and structured JSON responses.

Never construct arbitrary shell commands from LLM-generated strings.

Define typed request and response models so the orchestration engine is not dependent on raw CLI output.

Do not add an HTTP GitHub adapter unless required by an existing capability or a demonstrated unsupported CLI operation.

### Authentication

Support existing local GitHub authentication mechanisms without storing credentials in the SQLite database.

Validate authentication and required capabilities before any remote write.

Do not print credentials, tokens, authorization headers, or sensitive environment values.

Require least-privilege permissions.

Do not automatically create personal access tokens, GitHub Apps, or new credentials.

If a capability or permission cannot be verified, report a blocked state rather than attempting unrestricted access.

## 5. REPOSITORY AND BRANCH MANAGEMENT

Support independent Git repositories discovered through the existing workspace inventory.

Each delivery unit must refer to exactly one Git repository.

A milestone can include multiple delivery units.

Use existing Git worktree and repository locking mechanisms introduced in AEO-2 and AEO-3.

Implement safe branch preparation:

1. Identify the correct repository.
2. Inspect its Git state.
3. Verify the expected baseline commit.
4. Confirm the intended target branch.
5. Validate branch naming and allowed operations.
6. Reuse a matching existing AEO branch where safe.
7. Create a branch only when necessary.
8. Record branch identity and commit evidence.

Suggested naming convention:

`aeo/<milestone-id>/<task-id>`

Adapt the convention to existing branch policies and Git naming restrictions.

Never reset, force-push, rebase, delete, or overwrite branches automatically.

Never modify an unrelated user working tree.

Commit preparation and branch publishing are controlled mutating operations, not read-only checks. Require the existing AEO authorization policy before performing them.

Publishing must be an explicitly invoked delivery action or part of an already authorized delivery workflow.

## 6. PULL REQUEST AUTOMATION

Implement pull request preparation and creation.

A PR must contain a structured description including:

- Milestone ID
- Task ID
- Repository
- Purpose and implementation summary
- Architecture or design references
- Acceptance criteria addressed
- Tests executed and results
- Quality-gate summary
- Security verification status
- Documentation references
- Related PRs in other repositories
- Known limitations and risks
- Evidence references

Generate descriptions from verified execution records, not invented agent claims.

Support draft PRs for work that is explicitly permitted to be published before final readiness.

Fail closed if required AEO-4 pre-publication approval or security checks are missing.

### Idempotency

Prevent duplicate pull requests during retries and recovery.

Before creating a PR:

1. Check persisted delivery records.
2. Verify repository, head branch, base branch, and remote identity.
3. Query GitHub for matching open PRs.
4. Reconcile previously created, closed, and merged PR states.
5. Reuse a matching PR where policy permits.
6. Create a new PR only after confirming that no conflicting matching PR exists.

Persist remote PR number, immutable ID when available, URL, branch identities, head SHA, and milestone/task linkage.

If a network timeout occurs during PR creation, do not blindly retry. Query GitHub first and reconcile the outcome.

If the matching PR is closed or merged, do not silently reopen it or create a replacement.

Use documented recovery decisions requiring appropriate authorization.

Do not modify unrelated PRs.

## 7. MULTI-REPOSITORY DELIVERY COORDINATION

Implement a milestone-level delivery manifest.

Each milestone can have several repository-specific delivery units.

Model:

- Milestone identity
- Delivery unit identity
- Repository identity
- Task identity
- Dependency relationships
- Associated PR
- Target and head commits
- Validation evidence
- Approval state
- CI state
- Delivery readiness
- Blocking reasons

Example conceptual manifest:

```yaml
milestone_id: M3B
delivery_units:
  - id: contract-change
    repository: discovered-contract-repository
    dependencies: []
  - id: service-change
    repository: discovered-service-repository
    dependencies:
      - contract-change
```

This example is illustrative. Do not assume that these repository names exist.

The delivery coordinator must:

1. Track dependencies across repositories.
2. Permit independent preparation where safe.
3. Preserve one active conflicting write operation per repository.
4. Reconcile delivery unit status independently.
5. Detect missing or blocked dependency PRs.
6. Prevent false milestone-level readiness when dependencies remain unresolved.
7. Generate one aggregated delivery report.

PR creation does not imply that a dependency has been merged or made available to downstream repositories.

Represent the distinction explicitly.

Do not implement unsupported atomic commits or pretend that GitHub provides a cross-repository transaction.

## 8. CI/CD CHECK MONITORING

Integrate GitHub Actions and available GitHub check results.

Support:

- Pending
- Queued
- Running
- Successful
- Failed
- Cancelled
- Skipped
- Timed out
- Unavailable
- Unknown

Map provider-specific states into a typed internal representation without discarding original values.

Associate CI evidence with the exact commit SHA tested.

A successful check from an older commit must not validate a newer head commit.

Distinguish:

1. Required checks
2. Optional checks
3. Local AEO-4 quality gates
4. Missing or not-yet-reported checks

Respect branch protection and applicable rulesets.

Where policy requirements cannot be read, fail closed for automated readiness rather than interpreting missing information as unrestricted access.

Use bounded polling with configurable intervals, timeouts and rate-limit handling.

Do not create a continuously running background service.

Do not dispatch, cancel, rerun or modify GitHub Actions workflows automatically unless that capability already has explicit authorization in the existing policy model.

## 9. REVIEW AND APPROVAL VERIFICATION

Integrate with existing AEO-4 governance.

Verify:

- Design approval
- Required security approval
- Required quality gates
- Authorized publishing permission
- GitHub required reviews
- Required CI checks
- Applicable branch restrictions
- Head commit identity
- Cross-repository dependencies

AI agent review is not equivalent to required human review.

AEO cannot create or infer human approval from model-generated text.

Do not implement self-approval through agent identities.

Do not bypass CODEOWNERS, GitHub branch protection, or repository rulesets.

If external review state changes or a new commit invalidates previous readiness, recompute readiness.

The coordinator must provide a machine-readable explanation of every unmet requirement.

AEO-5 may declare a delivery ready for authorized merging, but must not perform the merge.

## 10. DURABLE DELIVERY STATE

Extend existing SQLAlchemy and Alembic persistence structures.

Reuse existing milestone, task, execution, approval, and evidence entities where possible.

Add only the entities required for durable delivery.

Possible domain concepts:

- DeliveryRun
- DeliveryUnit
- RemoteRepository
- BranchReference
- PullRequestReference
- CheckSnapshot
- ReviewSnapshot
- DeliveryOperation
- DeliveryEvidence
- DeliveryRecoveryRecord

These are conceptual entities, not mandatory separate tables.

Avoid parallel or competing state machines when existing models can be extended.

Persist:

- Stable operation identity
- Idempotency or reconciliation identity
- Milestone and task IDs
- Repository ID
- Operation type
- Intended remote mutation
- Attempt and outcome
- Remote resource identity
- Commit SHA
- Timestamps
- Policy decision and approval references
- Evidence references
- Recoverability status
- Sanitized error information

Use transactional persistence.

Create backward-compatible Alembic migrations.

Do not drop or rewrite existing execution records.

### Delivery state model

Design a deterministic state machine representing at least:

- Planned
- Awaiting approval
- Authorized
- Branch prepared
- Awaiting publication
- PR published
- Checks pending
- Review pending
- Blocked
- Ready for authorized merge
- Failed
- Recovery required

Separate operational state from independently evolving CI, review, and policy state as appropriate.

Define valid transitions, invalid transitions, and terminal or recoverable conditions.

Do not mark delivery successful merely because a PR exists.

An existing PR may still be blocked by CI failures, missing approvals, conflicts or unmet dependencies.

## 11. CRASH RECOVERY AND RECONCILIATION

Implement deterministic recovery of interrupted delivery operations.

Before each remote mutation:

1. Verify authorization.
2. Persist the intended operation.
3. Associate it with a stable operation identity.
4. Record relevant preconditions.
5. Mark the operation as in progress.
6. Perform the authorized remote action.
7. Reconcile the observed remote result.
8. Persist outcome and evidence.

For ambiguous outcomes, prioritize observation and reconciliation over retry.

Recovery must handle:

- Crash before branch creation
- Crash after branch creation
- Crash before push
- Push completed but response lost
- Crash before PR creation
- PR created but response lost
- CI status temporarily unavailable
- Rate limiting
- Expired authentication
- GitHub network failures
- Head commit changed
- Base branch changed
- PR closed externally
- PR merged externally
- Required checks changed
- Required reviews dismissed
- Interrupted multi-repository delivery

Do not silently retry non-idempotent actions.

Use bounded retries only for safe, classified, recoverable conditions.

Provide reconciliation reports identifying:

- Local persisted state
- Actual GitHub state
- Discrepancies
- Safe recovery actions
- Operations requiring human approval

Do not rely on LLM agents to decide whether a risky remote mutation is safe.

Use deterministic application logic and established policies.

## 12. DELIVERY EVIDENCE AND AUDITABILITY

Create a delivery evidence system compatible with AEO-4.

Capture:

- Milestone/task IDs
- Execution run IDs
- Agent handoffs
- Source repository
- Base and head commit SHAs
- Branch and PR references
- Quality gate results
- Security check results
- Approval references
- CI check conclusions
- Review decisions
- Relevant documentation artifacts
- Artifact content hashes
- Operation history
- Recovery history

Use immutable or append-only records where appropriate.

If a previously recorded result changes, preserve the prior evidence and record the updated observation.

Link evidence to the exact source revision.

Redact credentials and sensitive content.

Do not copy large logs or secrets into GitHub PR descriptions.

Do not claim cryptographic or audit immutability beyond guarantees actually provided by the implementation.

## 13. CLI INTEGRATION

Extend the existing Typer CLI.

Follow established command naming and help conventions.

Provide operations equivalent to:

```text
aeo delivery plan <milestone>
aeo delivery prepare <milestone>
aeo delivery publish <milestone>
aeo delivery status <milestone>
aeo delivery checks <milestone>
aeo delivery reviews <milestone>
aeo delivery reconcile <milestone>
aeo delivery recover <milestone>
aeo delivery report <milestone>
```

These commands are proposed interfaces, not mandatory exact syntax.

Prefer compatibility with the current CLI architecture.

### CLI safety

`plan`, `status`, `checks`, `reviews`, `reconcile`, and `report` must be read-only with respect to GitHub and Git repositories, apart from authorized local recording of observations.

`prepare` may create local branches/worktrees only when authorized.

`publish` must require the corresponding remote-write permission.

`recover` may perform read-only reconciliation by default; mutating recovery actions must be separately authorized.

Never implicitly push or create PRs during a status command.

Provide useful structured output and clear error codes.

Support noninteractive automation without suppressing mandatory human approvals.

## 14. IMPLEMENTATION PHASES

Execute AEO-5 in the following order.

### Phase 5A — Discovery and architecture

- Assess existing implementation.
- Identify reusable modules.
- Generate milestone documentation.
- Generate PlantUML diagrams.
- Validate document completeness.
- Obtain required design approval.

### Phase 5B — GitHub adapter

- Implement provider interface.
- Implement CLI-backed adapter.
- Add authentication and capability validation.
- Add typed schemas and errors.
- Add unit tests with mocked subprocess responses.

### Phase 5C — Branch and PR management

- Extend existing Git/worktree integration.
- Implement branch safety policies.
- Implement PR preparation and publication.
- Implement PR reconciliation and duplicate prevention.
- Add tests.

### Phase 5D — Delivery coordination

- Add cross-repository delivery manifests.
- Track dependency readiness.
- Implement deterministic coordination.
- Reuse existing locking and scheduling.
- Add tests.

### Phase 5E — CI and approval integration

- Implement check monitoring.
- Implement review verification.
- Integrate AEO-4 governance.
- Detect stale evidence after head SHA changes.
- Add tests.

### Phase 5F — Persistence and recovery

- Extend persistence.
- Add migrations.
- Implement durable operation tracking.
- Implement external-state reconciliation.
- Implement crash recovery.
- Add failure-injection tests.

### Phase 5G — CLI, reporting and integration tests

- Integrate Typer commands.
- Generate delivery reports.
- Add end-to-end mocked workflows.
- Add optional authorized GitHub sandbox smoke tests.
- Update documentation and examples.
- Generate final milestone completion report.

Within each phase, follow the existing project workflow and approvals.

Do not bypass the approval process merely because phases are contained in a single implementation prompt.

Do not automatically create GitHub PRs or push repository changes as part of the AEO-5 installation.

## 15. TESTING REQUIREMENTS

Tests must not depend on live GitHub access by default.

### Unit tests

Cover:

- Repository discovery
- GitHub response parsing
- CLI command construction
- Authentication failures
- Branch-name validation
- Branch conflict detection
- PR payload generation
- Existing PR reconciliation
- Duplicate PR prevention
- CI result normalization
- Review status interpretation
- Approval policy enforcement
- Artifact hashing
- Delivery state transitions

### Integration tests

Cover:

- SQLAlchemy persistence
- Alembic upgrades
- Existing milestone/task linkage
- Existing AEO-4 approvals
- Delivery state recovery
- CLI command execution
- Cross-repository manifests
- Concurrent delivery coordination

### Failure injection

Simulate:

1. GitHub unavailable
2. Missing credentials
3. Insufficient permissions
4. PR creation timeout after remote success
5. Duplicate matching PRs
6. Failed required check
7. Missing required review
8. New commit after successful CI
9. Process crash after push
10. Process crash after PR creation
11. Local database transaction failure
12. Multi-repository partial completion
13. GitHub rate limit
14. Branch policy mismatch
15. Working-tree changes that must be preserved

Verify fail-closed behavior.

### Regression tests

Run existing AEO-1 through AEO-4 tests.

Verify:

- Existing Codex execution works.
- Existing multi-agent scheduling works.
- Existing repository locking works.
- Existing approval policies work.
- Existing quality gates work.
- Existing recovery state is preserved.
- Existing CLI commands remain compatible.

### Optional live testing

Live tests are opt-in and require an explicitly identified, authorized test repository.

Never use production repositories for destructive integration tests.

Do not automatically create branches, push commits, or open PRs in real repositories during ordinary test execution.

## 16. SECURITY REQUIREMENTS

Enforce the following:

- Least-privilege authentication
- No secret logging
- No hardcoded GitHub credentials
- No unrestricted shell commands
- No trust in unvalidated agent output
- No automatic privilege escalation
- No self-approved restricted operations
- No branch-protection bypass
- No automatic force push
- No automatic merge
- No automatic deployment
- No silent modification of external repositories
- No modification of protected branches
- No reuse of stale authorization decisions after material changes
- No misleading success reports

Treat GitHub API and CLI output, PR descriptions, commit messages, repository files and agent-generated content as untrusted input.

Validate fields before using them in commands, filesystem paths, persistent state or authorization decisions.

## 17. CONFIGURATION

Reuse the existing centralized configuration system.

Externalize:

- GitHub provider type
- GitHub CLI executable path if needed
- Authentication validation behavior
- Operation timeouts
- CI polling intervals
- Maximum polling duration
- Retry policy
- Repository allowlist
- Allowed base branches
- Branch naming convention
- Remote-write permissions
- PR publication policies
- Readiness rules
- Logging and redaction controls

Do not introduce scattered `os.getenv()` calls.

Provide safe local defaults.

Do not enable remote mutation merely because GitHub authentication is available.

## 18. ACCEPTANCE CRITERIA

AEO-5 is complete only when:

1. Existing AEO-1 through AEO-4 behavior is preserved.
2. Repository discovery identifies correct GitHub remotes.
3. GitHub authentication and permissions can be verified.
4. Branch preparation respects worktree and repository isolation.
5. PR descriptions contain verified milestone evidence.
6. Repeated publication attempts do not create duplicate PRs.
7. Cross-repository PRs can be correlated with a milestone.
8. CI status is associated with the correct head SHA.
9. Required GitHub reviews and checks are enforced.
10. Existing AEO-4 approvals remain mandatory.
11. Delivery state survives process restart.
12. Interrupted remote mutations can be reconciled safely.
13. Recovery never blindly repeats ambiguous GitHub operations.
14. Audit reports include Git references and evidence hashes.
15. Existing database records survive migrations.
16. Mocked integration tests pass.
17. Existing regression tests pass.
18. No unintended remote repository mutations occur during tests.
19. Documentation and diagrams are updated.
20. AEO-6 is not started.

## 19. FINAL DELIVERABLES

Produce:

### Implementation

- GitHub integration adapter
- Delivery coordinator
- Branch and PR management
- CI and review verification
- Persistence and migrations
- Recovery and reconciliation
- CLI extensions
- Automated tests

### Documentation

In `docs/milestones/AEO-5/`, produce or update:

- Existing capability assessment
- Architecture design
- Workflow design
- Security and approval model
- Implementation plan
- Acceptance criteria
- PlantUML diagrams
- Test results
- Recovery guide
- Operational guide
- Final completion report

### Final completion report

The report must include:

1. Implemented features
2. Modules added and modified
3. Database migrations
4. CLI commands
5. Architecture changes
6. Test commands and actual results
7. GitHub integration validation results
8. Security and approval verification
9. Recovery scenarios validated
10. Known limitations
11. Outstanding approvals or blocked activities
12. Deviations from the proposed design
13. Recommended validation steps before AEO-6

Distinguish mocked tests from live GitHub verification.

Do not describe a capability as validated unless supported by actual evidence.

## 20. COMPLETION BEHAVIOR

After implementing AEO-5:

1. Run all feasible required tests.
2. Run Ruff and established project quality checks.
3. Validate Alembic migrations.
4. Verify existing functionality is preserved.
5. Validate diagrams and documentation.
6. Generate the completion report.
7. Provide the exact CLI commands for a safe local demonstration.
8. Provide an example of the expected milestone-level delivery report.
9. Clearly identify any required manual approvals or live test limitations.
10. Stop.

**Do not automatically execute AEO-6.**

**Do not automatically merge PRs or deploy applications.**

**Do not automatically start a new AgroSphere application milestone.**

The next milestone, AEO-6, will be initiated through a separate instruction after AEO-5 has been reviewed and accepted.

## START NOW

Begin by inspecting the existing AgroSphere workspace and orchestrator codebase.

Generate the AEO-5 capability assessment and architecture documentation first.

Follow the established documentation approval workflow, then implement each phase incrementally.

Preserve existing work and provide evidence for every completed capability.