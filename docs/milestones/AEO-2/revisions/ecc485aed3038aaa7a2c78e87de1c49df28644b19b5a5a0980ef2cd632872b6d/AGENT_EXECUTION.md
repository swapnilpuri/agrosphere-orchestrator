# Agent execution model — as built

The existing nine-role registry now supplies developer-priority instructions, responsibility,
input/output schema names, repository/operation allowlists, required context, validation
expectations, approval requirements and a non-executing handoff contract. Developer profiles
cover Java, Python, Angular, Data/PostGIS and Integration. Roles are not permission grants.

ExecutionRequest includes project/milestone/task, role/specialization, repository/worktree,
literal scopes, versioned input artifacts, instructions, acceptance criteria, mode, grant,
timeout, retry policy, correlation ID, source HEAD, context digest and design revision.
ExecutionResult captures timestamps/duration, session, status, actual changed files, model
artifacts, logs, exit/error, usage, orchestrator validation and evidence references. AgentOutput
normalizes work, files, artifacts, claimed commands/evidence, warnings/errors, unresolved issues
and suggested next actions. Model output never authorizes a second agent.

QUEUED -> AWAITING_APPROVAL -> PREPARING -> RUNNING -> SUCCEEDED/FAILED/TIMED_OUT/CANCELLED.
Lost workers become INTERRUPTED only after process reconciliation. A unique nullable active
slot in SQLite prevents two executions entering PREPARING/RUNNING concurrently, even if two
operators invoke the CLI. This guard is not a scheduler.

Task lifecycle and execution lifecycle remain separate. A successful model proposal without
orchestrator validators is recorded as runtime SUCCEEDED with implementation_verified=false;
the write task remains failed for acceptance bookkeeping. Only approved validator commands
run by the orchestrator can establish that verification flag. It does not complete a milestone
or bypass AEO-1C as-built/delivery approval. Validation-only requires an explicit validation
operation and cannot mark a fresh baseline copy as validation of a write proposal.
