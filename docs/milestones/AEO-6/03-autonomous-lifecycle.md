# Autonomous lifecycle proposal

1. Load run or construct a read-only plan. Discover actual repositories and reconcile child task/delivery operations before new work.
2. Select an eligible milestone from approved scope and dependencies; support proposed, partial, blocked, completed, interrupted and pending-delivery states. Completed tasks are adopted only with verified evidence, never restarted.
3. Prepare requirement narratives and diagrams in correct repository ownership. Register exact requirements; pause for authenticated requirements decision when missing.
4. Generate immutable design revision using existing design services; validate hashes, repository context, completeness and independent architecture review. Persist design checkpoint and stop until approved.
5. Produce DAG using orchestration.propose_plan and existing roles. Preserve plan approval, activated quality policy, exact per-execution grants and worktree isolation; missing gates are separate checkpoints.
6. Dispatch independent tasks only through TaskScheduler. Concurrency is the minimum of run limits and existing repository/agent scheduler limits. Every structured output references task, role, repository, inputs, actions, artifacts, file/commit identities, tests, blockers and next action; validate before transition.
7. Independently verify through AEO-4. Classify failures and prepare only policy-permitted remediation. Reserve repair budget first; default at most three repairs. Any changed design or write scope returns to its proper approval gate.
8. Build AEO-5 manifest from verified task outputs and exact repository identities. Prepare publication review scope. Require quality/security evidence and separate privileged approval; remote-write configuration remains off unless separately authorized.
9. Observe CI, required reviews, dependencies and external acceptance with bounded delivery polling. Retain implementation complete, local quality accepted, ready for publication, PR published, awaiting CI/review, ready for authorized merge, externally accepted and formal completion as distinct facts. Never merge or deploy.
10. Generate evidence-backed JSON/Markdown report. Advance only after formally verified completion and an explicit advance authorization within remaining milestone budget. Default one milestone; ambiguity blocks.

LLM outputs are untrusted reasoning/artifacts, never governance decisions. Stop-on-gate is mandatory for missing authority. Resume rechecks immutable scope, current allowlists, decisions, expiry/revocation, policy, artifacts and repository facts; valid unchanged approvals are reused.
