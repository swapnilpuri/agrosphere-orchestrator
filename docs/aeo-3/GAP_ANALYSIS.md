# AEO-3 assessment

| Requirement | Reused foundation | AEO-3 extension |
| --- | --- | --- |
| Approved milestone | MilestoneSpec, import_plan, AEO-1C design cases | Exact approved spec projection; immutable scheduling revisions |
| Task graph | MilestoneSpec duplicate/missing/cycle checks | Artifact producer edges, deterministic priority order, verified completion |
| Nine roles | RoleRegistry, ExecutionRequest, AgentOutput | Registered role/repository checks and persisted handoff contracts |
| Codex execution | queue_execution, grants, run_execution, CodexExecutor | Scheduler claims admit bounded concurrency; same adapter and canary |
| State | SQLAlchemy, SQLite, Alembic, append-only audit | Migration 0005: five additive orchestration tables |
| Isolation | Native permissions and isolated Git worktrees | Repository read/write leases and shared resource identifiers |
| Approval | Requirements/design decisions and exact execution grants | Human plan approval bound to immutable plan digest |
| Failure | Structured ExecutionResult, preserved worktrees | Failure classification and bounded repair eligibility |
| Recovery | CodexSessionManager process identity checks | Conservative claim reconciliation; uncertain leases retained |
| CLI/reporting | Existing Typer groups, structured execution reports | Plan/graph/prepare/execute/status/pause/resume/report and workload |
| Validation | Existing temporary repository fixtures | Nine-role deterministic fixture and negative boundary tests |

The old executor explicitly allowed one execution. Its admission transaction now admits multiple executions only when matching scheduler claims exist; direct single-task use retains its conservative limit. Design generation and human approval remain separate. No model SDK or transport was replaced.

Planning deliberately projects tasks already enumerated in the approved milestone. New decomposition or changed scope must pass the existing design lifecycle first; an agent recommendation alone cannot add executable work. Program and Project Manager metadata identify review responsibilities, not authenticated approval. Their runtime outputs use the existing typed AgentOutput contract.
