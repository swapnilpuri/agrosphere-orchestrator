# AEO-5 architecture proposal

This is a reviewable design, not an implementation claim. The user specifications in 00-original-specification.md and 00-recovery-request.md are authoritative scope inputs. Only agrosphere-orchestrator changes. Shared service APIs/events and application runtime behavior are unaffected.

## Ports and configuration

Proposed github_models.py holds strict Pydantic repository identity, principal, branch, PR, check, review, policy and error models. github_provider.py defines a typed protocol and GitHubCliAdapter with an injected subprocess runner for tests. Commands use fixed argument arrays, explicit cwd, explicit API method, bounded timeouts, bounded response size and sanitized errors. Validate github.com remote owner/name, IDs, SHA lengths and Git refs before use. Reject URL userinfo, arbitrary hosts, option-like branch names, traversal and untrusted executable selection. Confirm fetch and push remote identity agree with the configured allowlist.

Settings gains centralized provider, gh executable, operation timeout, bounded read retries/poll interval/duration, repository/base allowlists, branch prefix, redaction and remote writes disabled by default. Credentials remain with existing gh authentication. User/API identity and access are observed before writes; authentication never grants publishing approval. No merge/deploy/write-workflow capability is present in the port.

## Delivery domain

Proposed delivery_models.py defines a milestone manifest with uniquely named units, one repository/task per unit, DAG dependencies, expected base and head SHA, target/head branches and remote identity. Planned units reference existing milestone/task records. Validate duplicate IDs, cycles, missing tasks, repository mismatches and allowed target branches before persistence. Unit policy/CI/review snapshots evolve independently from operational state.

Proposed delivery_store.py adds DeliveryRun, DeliveryUnit and DeliveryOperation projections with stable IDs and uniqueness constraints on milestone/unit and operation reconciliation identity. Append immutable snapshots/events and raw result hashes through quality_store rather than retaining mutable-only audit evidence. Event/state updates and audit records share orchestration_store.transaction. Alembic 0007 adds tables/triggers/indexes without dropping old tables. Reject destructive downgrade. Existing DesignDecision and governance authority remain authoritative.

Proposed delivery.py coordinates branch preparation, publishing, observation, readiness and reports. Reuse execution_workspace's isolated worktree/preservation checks and orchestration_store resource leases for repository write exclusion. Each unit holds the same repository:<id> write resource as execution scheduling. No remote network call holds a SQLite write transaction. In-progress operation and ownership persist before releasing the transaction for I/O; uncertain completion retains a reconciliation block rather than freeing a conflicting write.

## Mutation protocol

Recheck exact source revision, baseline, remote, policy, authorization and AEO-4 quality before each step. Persist operation intent and preconditions transactionally before local branch preparation, push or PR creation. Use a stable key bound to unit, action, remote, branches and head SHA. After I/O reconcile observed external identity and persist append-only evidence/outcome. A process restart cannot infer completion from attempted intent. Do not create commits automatically; prepared commits require separate existing authorization. Push only an explicitly approved isolated branch without force or protected-target writes.

PR creation uses a structured body built from stored actual validation/quality/security/design references; include milestone/task IDs, design, purpose, tests, limitations and related PRs. Before creation inspect persisted identity and all relevant remote PR states for exact owner/head/base/remote identity. Multiple matches or closed/merged outcomes block for a human decision. A timeout after creation triggers lookup, never another blind create. Serialize lookups and creates with the repository lease and durable operation state. External actors may race: detect and block duplicates after observation; do not promise a GitHub cross-process atomic PR transaction.

## Policy and readiness

Read active branch rules and classic protection. A failed/ambiguous policy lookup does not mean no restrictions. Preserve provider values when mapping queued/pending/running/success/failed/cancelled/skipped/timed-out/unavailable/unknown. Query checks and statuses for the exact PR head; reject evidence for any older SHA. Keep required and optional checks distinct. Successful optional checks cannot satisfy missing required ones. Poll within configured budgets and classify authentication, rate-limit and network failures without printing secrets.

Review state must combine current GitHub merge/review decision, applicable required counts, changes-requested/dismissals, CODEOWNERS and current head. Agent/bot review never counts as human approval. If requirements cannot be proved by available metadata, block instead of approximating them from a review count. Recompute on every changed head/base/policy/review state. Existing AEO-4 activated policy, quality/security readiness and exact publishing authorization are mandatory for every delivery milestone, including legacy milestones.

Milestone readiness requires all unit guards and dependencies. A dependency PR existing is distinct from its changes being available to downstream units; unmerged/unavailable dependency content blocks the latter condition. AEO-5 may declare READY_FOR_AUTHORIZED_MERGE but never performs the merge.

## Evidence and reports

Persist unit and operation identity, authenticated principal, preconditions, policy/approval references, base/head SHA, branches, immutable PR ID/number/URL, exact-head CI and review snapshots, quality and security evidence hashes, documentation hashes, dependency state, recovery observations and blocker codes. Preserve prior observations when state changes. Report JSON and Markdown read stored evidence and display unavailable fields as unknown. Content hashes and SQLite append-only guards do not establish tamper-resistant remote audit storage.

## Documentation ownership prerequisite

The existing AEO-1C generator assumes cross-service architecture ownership. Introduce an explicit typed internal-orchestrator scope only after requirements approval; bind it into the scope digest. Restrict it to the single orchestrator task/context root and orchestrator-owned docs. Preserve current application ownership defaults and negative tests. Never silently remap an existing approved revision. This compatibility change is part of the review scope and is not already implemented.

## Official provider references

Request construction: [GitHub CLI API manual](https://cli.github.com/manual/gh_api). Policy reads: [classic protection](https://docs.github.com/en/rest/branches/branch-protection) and [active branch rules](https://docs.github.com/en/rest/repos/rules). Review data: [pull request reviews](https://docs.github.com/en/rest/pulls/reviews). These references inform the proposed adapter; they do not prove a live integration was implemented or tested.
