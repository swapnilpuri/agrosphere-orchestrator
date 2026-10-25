# CLI usage guide

Run from the orchestrator root using the project virtual environment. Install editable
.[dev,codex], migrate with python -m alembic upgrade head, and run aeo codex doctor.
SDK 0.24.0 is pinned in the codex extra. Native Codex/Git, existing supported Codex login,
Windows MXC and authorized human SIDs are prerequisites. No model is chosen automatically
by the orchestrator; AEO_CODEX_MODEL can explicitly select the user's intended model.

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
aeo agent resume --execution FAILED-ID --instructions "Review preserved work and propose this bounded repair"
aeo agent cleanup --execution TERMINAL-ID
~~~

The first run --task prepares AWAITING_APPROVAL; it never starts a model implicitly. Review
exact expanded validator argv, role, artifacts, source/runtime hashes and scope, approve
interactively, then explicitly run --execution. config/execution.yaml defaults live_enabled
false, with no validation commands. Configure that allowlist and live_enabled deliberately
before preparing/approving a request; a later policy change invalidates an earlier digest.
AEO_EXECUTION_APPROVERS is a JSON list of authorized Windows SID identities, separate from
AEO_DESIGN_APPROVERS. Existing task-operation approvals must also be present where required.

READ_ONLY inspects one approved repository. WORKTREE_WRITE produces a scoped proposal and
runs its approved validators. VALIDATION_ONLY runs fixed approved commands for a validation
task without a model. Write file scopes must be literal non-root paths; protected controls
and approved artifacts cannot be edited. Current canary support requires a directory scope.
Validation output is captured after command exit; status shows durable attempt progress.

Private data lives in AEO_EXECUTION_ROOT (default .aeo/executions), which is Git-ignored.
Native executable path, bounded startup arguments, transport and model have Settings overrides.
MCP execution is refused on this runtime; auto selects the verified exec transport.
