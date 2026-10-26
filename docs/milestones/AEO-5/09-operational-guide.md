# AEO-5R delivery operator guide

The implemented CLI is available under aeo delivery (or python -m agrosphere_orchestrator.cli delivery). It never merges or deploys. Remote writes default off. Ordinary tests use disposable Git repositories/databases and a stateful fake GitHub port; no live push or PR creation is part of validation.

## Configuration and migration

Use the project virtual environment and run python -m alembic upgrade head after backing up the configured SQLite database. Migration 0007 adds delivery manifests, unit projections, immutable operation intents and immutable event history, preserving existing AEO-1 through AEO-4 tables. Destructive downgrade is rejected.

Settings remain centralized in config/settings.py. Relevant environment names:

| Setting | Purpose/default |
| --- | --- |
| AEO_GITHUB_REMOTE_WRITES | false; turning it on alone grants no mutation authority |
| AEO_GITHUB_REPOSITORIES | explicit JSON allowlist of owner/name identities; empty by default |
| AEO_GITHUB_BASE_BRANCHES | JSON allowlist, default main/master |
| AEO_DELIVERY_ROOT | isolated worktree root, default ../.aeo-delivery; must be outside the source repository |
| AEO_GITHUB_EXECUTABLE | gh, gh.exe, or trusted absolute gh.exe |
| AEO_GITHUB_TIMEOUT_SECONDS | 30; bounded 1–120 |
| AEO_GITHUB_READ_RETRIES | 1; bounded 0–3; mutations are never retried |
| AEO_GITHUB_MAX_RESPONSE_BYTES | 2000000; bounded response/pagination budget |
| AEO_GITHUB_MAX_PAGES | 20; incomplete pagination blocks |
| AEO_GITHUB_POLL_SECONDS | 5; bounded polling interval |
| AEO_GITHUB_POLL_BUDGET_SECONDS | 60; bounded 0–300 |

Existing gh authentication is used. Authenticated user identity and repository permissions are observed before writing. HTTPS push uses only the fixed gh auth git-credential broker; tokens are not read into application code, command arguments or evidence. Source-repository credential helpers/custom transport commands are rejected. Trusted Git operations disable hooks, global/system config, filters and filesystem monitors. Git checkout/fingerprinting supports Windows long paths and refuses incomplete filesystem traversal.

## Manifest and grants

A delivery manifest links each unique unit to an existing persisted task UUID and repository root, immutable GitHub repository ID and owner/name, allowed base branch, distinct aeo/ branch, exact base/head commits, dependencies, and explicit draft policy. Units form a DAG. Tasks must belong to the same existing milestone and repository. Source/base objects must be commits and the approved base must be an ancestor of head. The exact repository root must match the configured confirmed repository manifest; fetch and push remotes must agree.

The generated docs/schemas/delivery-manifest.schema.json describes the JSON contract. A milestone has one immutable delivery manifest. Changed delivery scope is not silently substituted under an existing run.

~~~powershell
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli delivery plan delivery-manifest.json
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli delivery status RUN_ID
~~~

Before each mutation, activate the milestone's genuine human-reviewed AEO-4 policy and obtain fresh quality/security/acceptance evidence using the existing quality workflow. The delivery service requires active AEO-4 even for legacy milestones. It does not use assert_delivery's legacy opt-out. Missing, incomplete, stale, failed or changed evidence blocks publishing.

Request an exact one-time grant for each action (prepare, push, create-pr):

~~~powershell
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli delivery request-approval RUN_ID UNIT_ID prepare --justification 'Review the exact isolated branch preparation'
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli approvals inspect APPROVAL_REQUEST_ID
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli approvals decide APPROVAL_REQUEST_ID --reason 'Reviewed exact scope and evidence'
~~~

The existing authenticated approvals interface records the human decision; delivery never approves its own request. It uses category PRIVILEGED_EXECUTION with action delivery:<scope hash>. The scope binds manifest, task, repository/root/remote identity, base/head commits and branches, isolated target, delivery policy, current remote policy, authenticated principal, exact design/policy/artifact context, quality validation and evidence. A generic delivery approval or GitHub login is insufficient. Expired, revoked, consumed or changed-scope grants fail.

~~~powershell
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli delivery prepare RUN_ID UNIT_ID --approval PREPARE_APPROVAL
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli delivery publish RUN_ID UNIT_ID --push-approval PUSH_APPROVAL --pr-approval PR_APPROVAL
~~~

The service does not create commits. Prepared, separately authorized commits must already exist. Original dirty worktrees are preserved; a separately created/reused exact isolated worktree is required. Publication checks that its committed bytes equal the actual AEO-4 validated artifact tree. This includes line endings: Git normalization must not silently substitute different bytes. Validate the actual isolated artifact if original dirty content or checkout normalization differs.

## Observation and reports

~~~powershell
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli delivery checks RUN_ID UNIT_ID --poll
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli delivery reviews RUN_ID UNIT_ID
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli delivery reconcile RUN_ID UNIT_ID
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli delivery recover RUN_ID UNIT_ID
./.venv/Scripts/python.exe -m agrosphere_orchestrator.cli delivery report RUN_ID --markdown
~~~

Status/report read persisted evidence; checks/reviews/reconcile/recover perform observations and append evidence only. Default recovery never calls a write port. An explicit recovery retry requires --action and --approval, using a fresh authenticated request for recover-prepare, recover-push or recover-create-pr bound to the prior intent IDs and the latest reconciled observation. Ordinary publishing grants cannot authorize recovery. Stored readiness is explicitly observational and expires after 60 seconds; reconcile every unit before relying on it. READY_FOR_AUTHORIZED_MERGE is a report state, not merge authority or an executed merge.

Required checks combine classic protection and active branch rules, retaining application identity and exact tested SHA. Optional success cannot replace missing required checks. Failed, cancelled, skipped, pending, stale, unavailable and unknown required results block. Strict policy requires proof that the base is included in the head.

Current human reviews must satisfy required counts, GitHub review decision and exact head; bot/self/author reviews do not count. Latest decisions are case-insensitive by GitHub account, and dismissals/changes requested invalidate readiness. The current adapter deliberately blocks human CODEOWNER proof and unsupported rules that its metadata cannot establish, rather than treating a generic approval count as proof. Such policies require a separately reviewed richer adapter; there is no readiness override.

Dependencies require a merged exact PR and proof that its merge commit remains reachable from its target branch. An open dependency PR is not content availability. Units recover independently; partial completion is never treated as a cross-repository transaction.

CLI errors are structured JSON: exit 2 for invalid/provider/blocked input, 3 for authorization/disabled writes, 4 for uncertain mutation recovery. Provider errors are classified without printing raw tokens, bodies or credential-bearing output.
