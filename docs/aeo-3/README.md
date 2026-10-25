# AEO-3 operations and architecture

The deterministic scheduler executes the exact approved milestone DAG through the existing AEO-2 adapter. Tasks are ordered by descending priority and then ID. A prerequisite must have both a succeeded task state and persisted task.verified evidence. Independent tasks may run concurrently; failed or uncertain prerequisites block their descendants while unrelated tasks can continue.

## Source and persistence

- orchestration_models.py: strict execution plans, task options, artifact references, failure categories.
- orchestration_store.py: SQLite transaction boundary, plan revisions, controls, claims, resource leases, immutable evidence.
- orchestration.py: planning, scheduling, handoffs, recovery, JSON and Markdown reporting.
- execution.py: existing execution admission, now aware of scheduler claims and lease conflicts.
- execution_context.py: verified handoff contents enter the existing bounded, redacted, hashed context.
- Migration 0005 adds orchestration_plans, orchestration_controls, task_claims, resource_leases and orchestration_evidence. Dependencies, assignments, validations, repair results, batches, and handoffs are typed plan data or immutable evidence associated with existing milestone/task foreign keys. Project identity is inherited from the milestone.

All state changes and their audit records share a transaction. Plans and evidence have database triggers rejecting update/delete. SQLite BEGIN IMMEDIATE serializes local scheduling admission; transactions never contain model awaits. Idempotent plan proposals reuse an identical historical revision. Changing scheduling options creates a new revision requiring fresh human approval. Existing approved plan history remains intact.

## Roles and contracts

All nine roles retain ExecutionRequest input and AgentOutput output. Their permissions come from config/roles.yaml plus exact approved execution grants and native isolation. Program Manager reviews roadmap intent and final evidence; Project Manager recommends task decomposition and dependencies; Business Analyst handles requirement traceability; Solution Architect verifies approved interfaces; Developers implement specialized scoped proposals; QA validates acceptance; Security reviews policy risks; DevOps reviews automation; Technical Writer reconciles verified as-built documentation. Roles cannot approve their own work or spawn unrestricted agents.

## Operator workflow

Use an existing approved/imported milestone and its design lifecycle before planning. The planner does not authorize new scope or alter approved architecture.

~~~powershell
aeo milestone plan AGRO-M3C --options task-options.json
aeo milestone graph AGRO-M3C --plantuml
aeo milestone approve-plan AGRO-M3C
aeo milestone prepare AGRO-M3C
aeo agent status --execution EXECUTION-UUID
aeo agent approve --execution EXECUTION-UUID
aeo milestone execute AGRO-M3C
aeo milestone status AGRO-M3C
aeo milestone pause AGRO-M3C
aeo milestone resume AGRO-M3C
aeo milestone report AGRO-M3C --markdown
aeo tasks list --milestone AGRO-M3C
aeo tasks inspect TASK-UUID
aeo agents workload
~~~

Plan approval displays the exact plan and requires the configured authenticated execution approver. prepare creates bounded requests without invoking a model. Approve each exact request through the existing interactive grant workflow. execute drains eligible approved requests and stops when new grants, handoffs, or other prerequisites are needed. It never implicitly approves a request. Repeat prepare/review/grant/execute for subsequent waves.

Task options are a JSON object keyed by the exact milestone task IDs:

~~~json
{
  "implement": {
    "mode": "WORKTREE_WRITE",
    "allowed_paths": ["src"],
    "expected_outputs": ["src/generated.txt"],
    "validation_commands": ["approved-test-command"],
    "priority": 10,
    "max_repairs": 3
  }
}
~~~

Write options require literal paths and administrator-allowlisted validation command IDs. The executor verifies native isolation before model invocation, preserves proposals in private worktrees, checks changed paths, and independently runs validations. A model success claim does not verify implementation. Read-only role reviews can succeed without claiming implementation validation.

## Resource locking

Defaults: two global executions, two per role, one per repository, three repair attempts. AEO_SCHEDULER_MAX_CONCURRENCY, AEO_SCHEDULER_PER_AGENT, AEO_SCHEDULER_PER_REPOSITORY and AEO_SCHEDULER_MAX_REPAIRS configure limits. A repository writer is exclusive even if a higher repository concurrency limit is configured. Read leases can coexist when the per-repository limit permits. Shared contract, migration, build, or test environments must be declared as stable resources in task options. Resource names are acquired in sorted order within one transaction; acquisition is all-or-nothing. Separate worktrees do not remove repository or shared-resource conflicts.

Leases include ownership and expiry. Expiry records uncertainty and does not allow another writer to steal the resource. Confirmed execution results release resources. Cancellation that has not established process termination retains claims and leases for reconciliation. SQLite coordination is single-host; there is no distributed locking or exactly-once guarantee. Trusted administrators must not bypass the scheduler or edit control tables while it runs.

## Handoff protocol

ArtifactReference includes repository, literal relative path, SHA-256, source commit revision, and optional producer task. Producers must be declared task dependencies with matching expected outputs. A produced artifact resolves to the producer's verified preserved execution worktree, never a sibling working tree. Its source commit, bytes, producer state, and validation evidence are checked before use. External inputs must match the current confirmed repository HEAD and content hash.

Successful producers automatically publish approved expected handoffs. Persisted handoff evidence identifies both tasks and roles, milestone, summary, artifacts and hashes, source commits, criteria, validation evidence, known issues and status. Receiving claims acknowledge the exact references. The executor adds their bounded content and hashes to its prompt/context digest. Modified or missing bytes invalidate downstream use. Unexpected output hashes remain blocked and require a reviewed plan revision. Handoff records can also be submitted with milestone handoff; no natural-language message substitutes for them.

## Failures and recovery

Structured failures distinguish runtime, validation, contract, security, approval, resource, dependency, output, timeout and unknown categories. Read-only transient/validation/output/timeout failures are eligible for at most three repairs after the original attempt. Every attempt preserves the original result and uses a newly prepared exact execution grant. Security violations and missing approvals are never automatically retried. Write recovery requires explicit human review and a new grant; no uncertain write is blindly replayed. The current implementation deliberately does not preauthorize future repair executions.

pause persists a scheduling stop before requesting cancellation of claimed executions. resume first invokes the existing process/session reconciler. Live or unverifiable process identities retain ownership. A terminal persisted result can reconcile a claim; an uncertain result enters reconciliation_required and retains its resource leases. Human operators must inspect preserved worktrees, process identities, validation evidence and possible side effects before resolving an uncertain claim. Never delete an expired lease merely to make progress. There is no automated acceptance of uncertain output.

Design changes invalidate the gate on every scheduling wave and in the executor before and after execution. A design deviation must be recorded through the existing design revision/approval lifecycle; affected work cannot proceed until the approved design and plan agree. report cannot mark a milestone complete with missing verification or incomplete required tasks.

## Troubleshooting and limits

- Missing design or plan approval: complete the existing design lifecycle, review the exact plan, then approve it interactively.
- Waiting for a grant: use prepare, agent status, and agent approve. Grants expire and do not carry over to repair executions.
- Artifact mismatch: inspect the preserved producing worktree and approved hash. Revise and reapprove the plan if the intended output changed.
- Resource conflict: inspect workload and persisted claims. Reconcile interrupted executions before releasing ownership.
- Partial success: inspect task.result, handoff.failed, reconciliation.required and execution reports. Unrelated tasks can still proceed.

The main fixture is deterministic and mocked. It demonstrates scheduler concurrency, not live Codex concurrency. Real native sandbox and live model behavior remain covered only by separate explicit opt-in smoke workflows. There are no automatic merges, pushes, deployments, business repository writes during testing, or distributed queue services.

Run the separate live transport smoke only by explicit opt-in: `.venv\Scripts\python.exe scripts/codex_multi_role_smoke.py --live`. It authenticates each role request, uses temporary fixture worktrees, and records results separately. It does not claim live scheduler concurrency.
