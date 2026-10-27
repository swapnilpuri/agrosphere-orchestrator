# Autonomous operations guide

This guide uses the existing AEO CLI and durable run ba0851d4-66bc-417a-851b-f08176bd8061. It creates no new orchestrator, UI, service, watcher or autonomous run. Current evidence-disposition capability is unimplemented and awaiting requirements approval. Historical AEO-6 simulation was mocked; it is not proof of live autonomous delivery.

## Safe inspection entry point today

From C:\Projects\agrosphere\agrosphere-orchestrator:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous status ba0851d4-66bc-417a-851b-f08176bd8061
~~~

This reads the persisted run and does not resume it. Before any application continuation, ensure AEO_DATABASE_URL targets the existing aeo.db, AEO_WORKSPACE_ROOT is C:\Projects\agrosphere and AEO_REPOSITORY_MANIFEST is the absolute config/repositories.yaml for the 12 application repositories. Never leave an internal design manifest in the environment for application discovery. Do not use autonomous start to replace this run.

## Progress, results and pending decisions

Use autonomous report <run> (optionally --markdown), autonomous validate <run> and milestone design-status <milestone>. Existing autonomous reports are persisted observations; fresh discovery happens on continuation and must use the correct manifest. Use approvals pending and approvals inspect <request-id> for existing governance requests. These do not replace milestone docs <milestone> for requirements/design decisions. Documentation and evidence are under docs/milestones; the current AEO-6.1 preparation package is docs/milestones/AEO-6.1/preparation-20261027T005025Z. Older discovery/forensic artifacts remain under AEO-6/evidence/discovery-reconciliation.

Current 1B evidence recommendation is non-conflicting historical observation; it is not an approval or acceptance. No evidence request/decision CLI exists yet, so do not invent a category/action or write a SQLite record to clear the conflict.

## Immediate authenticated requirements gate

The pending change uses milestone ID AEO-6-ADJUDICATION. Review its requirements-input.json, the source proposal lineage, all twelve requirement/acceptance clauses, the 1B forensic package and milestone docs output. After registration, the supported command is:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-requirements AEO-6-ADJUDICATION
~~~

The configured design identity is sid:S-1-5-21-1295115365-4060518610-348779417-1001. The interactive verifier requires the exact displayed subject phrase and Windows username/domain/password and resolves the canonical SID. Passwords are entered locally, never in CLI arguments, scripts or chat; no agent --actor bypass exists. Use the same command with --reject to reject. Approval authorizes technical-design preparation only, not source changes, evidence disposition or application execution. This prompt and these documentation artifacts are not approvals.

## Subsequent design and implementation gates

After authenticated requirements approval, use the existing internal-scoped milestone design AEO-6-ADJUDICATION workflow, configured renderer, milestone validate-design and milestone docs to review the immutable generated revision, diagrams and validation evidence. Then an authorized human uses milestone approve-design AEO-6-ADJUDICATION (or --reject). Only after the existing implementation-ready gate, approved plan and exact execution authority may implementation begin. The internal manifest belongs to that workflow alone; scope environment overrides to the process and restore the application manifest afterward.

Existing generic governance decisions use approvals decide <request-id> --decision approved|rejected|revoked --reason <rationale>, with current authenticated governance-SID authorization and bound artifact/context/expiry checks. There are currently no configured governance approver SIDs. Do not repurpose design approval as evidence approval or configure identities automatically. Evidence approve/reject/request-more-evidence commands are a design obligation pending approval and implementation; they are not available today.

## Single continuation entry point after all blockers are resolved

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous resume ba0851d4-66bc-417a-851b-f08176bd8061
~~~

This is the existing single continuation command, not a grant and not safe to run merely because a report looks complete. The controller runs the bounded eligible workflow until another checkpoint; approved unchanged child artifacts/grants are reused subject to their actual guards. Human approval remains a separate authenticated CLI action; after the decision, invoke the same resume entry point. There is no implemented background watcher or automatic approval listener, and no claim that a human decision automatically restarts an exited process. No new wrapper is required to select a command already implemented; actionable evidence-disposition integration still requires the governed extension.

Do not execute resume now. Fresh 1B conflict persists, M2 requirements and performance acceptance are missing, and the original immutable run deadline has expired. Raising AEO_AUTONOMOUS_MAX_SECONDS does not change the persisted request budget. No deadline extension command exists; no reset, manual run edit or new run is permitted by this task. A separate governed policy is needed if same-run continuation beyond its original deadline is required.

## Failure and restart recovery

Inspect status/report/validate first. For an unfinished operation, use the documented autonomous recover <run> and child-specific recovery only when the reported evidence supports them; they adopt independently observed outcomes and never blindly replay uncertain writes. With no current operation, autonomous recover returns the current report and does not refresh or clear a conflict. Resume cannot take ownership of an unfinished operation. Pause retains owned child work and budgets. Do not clear checkpoints, leases, approvals or counters in SQLite.

A missing/rejected/stale approval, unknown evidence, security policy, dependency, quality failure, missing requirements, budget exhaustion or uncertain external outcome requires the appropriate existing gate. Independent ready tasks can proceed only within the existing approved DAG and resource/security constraints; a global discovery conflict cannot be bypassed by choosing another task. AEO does not authorize PR merge/deploy from local completion or historical tests.

## Actual readiness and remaining gaps

Current run is BLOCKED; discovery_consistent=false with 1B only. M2 is DISCOVERED with no registered approved requirements. The evidence-disposition category/subject/CLI/consumer and authenticated unresolved/rejection flow remain unimplemented. AEO-6.1 requirements approval, technical-design generation/validation/approval, implementation authorization and regressions remain ahead. Governance SID policy, renderer, approved roadmap/dependencies, M2 product/performance decisions, exact execution grants and expired-budget policy remain independent blockers. Existing service capabilities are reused; none of these gaps is silently treated as satisfied.
