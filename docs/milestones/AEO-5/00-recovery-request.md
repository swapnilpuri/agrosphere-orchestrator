# AEO-5R — Implementation Recovery, Completion and Acceptance

## Role

Act as Principal Python Engineer, AI Orchestration Architect, GitHub Integration Engineer and Software Quality Lead.

You are working in the existing `agrosphere-orchestrator` project.

AEO-1 through AEO-4 are implemented and validated.

The AEO-5 acceptance report found:

- AEO-1–4 regression tests: 163 passed.
- Lint, formatting, dependencies, and disposable database migrations passed.
- GitHub authentication and access work.
- AEO-5 GitHub delivery integration is missing.
- Branch and PR management are missing.
- Duplicate PR prevention is missing.
- GitHub CI and review enforcement are missing.
- Remote recovery is missing.
- Delivery evidence reporting is missing.
- No unauthorized pushes, merges or deployments occurred.

**AEO-5 is NOT accepted.**

Your responsibility is to recover and complete AEO-5, not merely validate the existing codebase.

## 1. First: Investigate Missing Implementation

Inspect the workspace and determine whether AEO-5 implementation exists in:

- Another local Git branch
- Another Git worktree
- Uncommitted local files
- A different orchestrator checkout
- Existing commits not currently checked out
- Other accessible repository references

Use non-destructive Git inspection.

Do not reset, clean, delete, overwrite or force-checkout any repository.

If AEO-5 code exists elsewhere, determine whether it can be safely integrated without overwriting existing work.

Do not merge automatically when conflicts or unclear ownership exist.

Document findings in:

`docs/milestones/AEO-5/IMPLEMENTATION_RECOVERY.md`

State whether the original implementation was:

1. Found and recoverable
2. Partially found
3. Not found

## 2. Verify Actual AEO-5 Implementation

Create a capability inventory showing:

| Capability | Existing code | Tests | Status |
|---|---|---|---|
| GitHub provider | File/class reference | Test reference | Complete/Missing |
| Branch management | File/class reference | Test reference | Complete/Missing |
| PR automation | File/class reference | Test reference | Complete/Missing |
| Duplicate prevention | File/class reference | Test reference | Complete/Missing |
| Multi-repository coordination | File/class reference | Test reference | Complete/Missing |
| CI monitoring | File/class reference | Test reference | Complete/Missing |
| GitHub review verification | File/class reference | Test reference | Complete/Missing |
| Approval enforcement | File/class reference | Test reference | Complete/Missing |
| Durable state | File/class reference | Test reference | Complete/Missing |
| Remote recovery | File/class reference | Test reference | Complete/Missing |
| Delivery evidence | File/class reference | Test reference | Complete/Missing |
| CLI commands | File/class reference | Test reference | Complete/Missing |

Do not mark a capability complete merely because documentation, a stub, or an interface exists.

## 3. Implement Missing AEO-5 Capabilities

Complete all outstanding functionality from the original AEO-5 specification.

### A. GitHub integration

Implement a typed GitHub provider interface and CLI adapter that supports repository discovery, remote branch discovery, PR lookup, PR creation, CI checks, review inspection, and required repository policies.

Use validated subprocess arguments, bounded timeouts, sanitized errors and centralized configuration.

### B. Branch and PR workflows

Implement:

- Safe branch preparation
- Repository and worktree isolation
- Permission checks
- Authorized branch publishing
- PR creation
- PR metadata persistence
- Duplicate PR prevention
- Existing PR reconciliation

Do not allow automatic force-push, merges or deployments.

### C. Multi-repository coordination

Maintain milestone-level delivery units for independent repositories.

Track dependencies, PR identities, commit SHAs and readiness.

Use existing AEO-3 scheduling and locking rather than creating competing mechanisms.

### D. CI and approval enforcement

Read GitHub check results and review requirements.

Bind check evidence to the exact PR head SHA.

Respect GitHub branch protection, rulesets, required reviews and AEO-4 approval policies.

If mandatory requirements cannot be verified, mark delivery blocked.

### E. Durable recovery

Extend the existing persistence layer.

Persist operation intent before remote mutations.

Reconcile external GitHub state after failures, especially when a remote operation might have succeeded but the local process did not receive confirmation.

Avoid duplicate PRs and unsafe retries.

Use Alembic migrations without losing historical records.

### F. Delivery evidence and reporting

Generate milestone-level delivery reports containing:

- Repository
- Branch
- Commit SHA
- PR number and URL
- CI checks
- Review requirements
- AEO-4 approvals
- Quality evidence
- Dependency status
- Recovery history
- Blocking reasons

Do not invent successful tests, approvals or remote operations.

### G. CLI commands

Integrate with the existing Typer CLI.

Support the equivalent of:

```text
aeo delivery plan
aeo delivery prepare
aeo delivery publish
aeo delivery status
aeo delivery checks
aeo delivery reviews
aeo delivery reconcile
aeo delivery recover
aeo delivery report
```

Provide discoverable help, stable exit codes and structured output.

Read-only commands must not silently publish branches or PRs.

## 4. Implementation Execution Rules

This is an implementation task, not a planning-only task.

After discovery and any required design approval:

1. Implement the missing production code.
2. Add persistence models and migrations.
3. Add CLI functionality.
4. Add unit tests.
5. Add mocked GitHub integration tests.
6. Add fault-injection and recovery tests.
7. Update technical documentation.
8. Run regression tests.
9. Generate an evidence-based completion report.

Do not stop after producing a proposal, architecture assessment or implementation plan.

If a required approval is pending, stop only the activities blocked by that approval and clearly identify the approval needed. Continue independent authorized work.

Do not interpret this prompt as authorization for live remote writes.

## 5. Testing Requirements

Preserve the 163 previously passing tests.

Add tests covering at least:

1. GitHub authentication failure
2. Repository lookup
3. Branch naming and creation safety
4. Existing branch reuse
5. PR creation
6. PR lookup and reconciliation
7. Duplicate PR prevention
8. CI success and failure
9. Missing required reviews
10. AEO-4 approval integration
11. Stale CI results after new commits
12. Cross-repository dependency blocking
13. Crash after remote branch publication
14. Crash after remote PR creation
15. Network timeout after successful remote operation
16. SQLite persistence recovery
17. Unauthorized remote-write rejection
18. No automatic merges or deployments

Mocked GitHub tests must not mutate actual remote repositories.

Live GitHub smoke testing is optional and requires separate explicit authorization and an approved test repository.

## 6. Acceptance Verification

AEO-5R can be accepted only when:

- Actual implementation files exist.
- New tests exercise the AEO-5 capabilities.
- All 163 baseline tests continue passing, unless the baseline test inventory is explicitly reconciled.
- New AEO-5 tests pass.
- Migrations succeed.
- CLI commands execute.
- Remote operation recovery is validated.
- Duplicate PR prevention is validated.
- CI and human-review policies are enforced.
- Delivery reports can be generated from actual stored evidence.
- No unauthorized remote mutations occur.
- No unsupported success claims appear in the report.

A documentation-only implementation is not acceptable.

## 7. Required Final Report

Generate:

`docs/milestones/AEO-5/AEO-5R_ACCEPTANCE_REPORT.md`

Include:

1. Recovery investigation findings
2. Implementation inventory
3. Files created and modified
4. Database migrations
5. CLI commands implemented
6. Actual tests executed
7. Number of baseline tests passing
8. Number of new AEO-5 tests passing
9. Failure-injection results
10. Evidence of duplicate PR prevention
11. Evidence of approval enforcement
12. Evidence of durable recovery
13. Any unverified live GitHub capabilities
14. Known limitations and remaining blockers
15. Final acceptance recommendation

For each capability, provide references to implementation files, test files and actual test results.

Do not mark AEO-5 complete if required capabilities remain missing.

## 8. Completion Boundary

After implementation, testing, documentation and acceptance reporting:

**STOP.**

Do not start AEO-6.

Do not automatically resume AgroSphere application development.

Do not automatically push, merge or deploy anything.

Begin with the recovery investigation, then implement and validate the missing AEO-5 functionality.