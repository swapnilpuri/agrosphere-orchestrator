# Delivery workflows proposal

All flows below are planned behavior, not currently available commands. Six locally rendered diagram sources accompany this package.

## Commands and side effects

| Command | Intended behavior | Real repository/GitHub writes |
| --- | --- | --- |
| delivery plan | Validate and persist an immutable manifest linked to existing approved tasks | None |
| delivery prepare | Validate baseline and create/reuse an isolated local branch/worktree under an exact grant | Authorized local isolated Git operations only |
| delivery publish | Recheck quality/approvals/remote identity, persist intent, push, reconcile, create/reuse PR | Explicitly authorized push/PR creation only |
| delivery status | Present persisted operational/policy state | None |
| delivery checks | Observe and optionally bounded-poll exact-head CI | None |
| delivery reviews | Observe current human-review requirements and decisions | None |
| delivery reconcile | Compare durable intent/PR/ref identities with current remote state | None |
| delivery recover | Reconcile read-only by default; separately grant any mutation | None by default |
| delivery report | Render the aggregate evidence and every blocker | None |

Local recording of observations is transactional and append-only. Status/report never invoke publication. Stable failure codes distinguish invalid input, authorization denial, blocked requirements, provider failure and ambiguous recovery; CLI errors must be structured and tested.

## Branch preparation

Inspect original and isolated worktrees, exact baseline/head and repository identity. Reject protected base writes, branch naming conflicts, unexpected source modifications, unsafe hooks and missing grants. Reuse only an exact matching safe AEO branch. Preserve dirty original worktrees. Never reset, rebase, delete branches, overwrite files or force push. Validate ref syntax through Git as well as application policy.

## Publication and duplicate prevention

Acquire the existing repository write resource. Re-evaluate activated AEO-4 evidence, design and exact publishing approval. Persist intent before each remote mutation. Inspect remote branch/head and matching open/closed/merged PRs; reconcile existing durable PR identity. Push only if separately authorized and needed. Recheck after push, then create/reuse exactly one matching PR. Unexpected competing/closed/merged matches block. Persist immutable identity, SHA, URL and complete history. No network exception causes blind create/push replay.

## Recovery decisions

| Interruption / external change | Observation and safe default |
| --- | --- |
| Before local branch creation | Inspect operation, branch and worktree; no mutation without current grant |
| Branch created before local outcome saved | Verify exact repository/branch/base and record observed result |
| Before push / push response lost | Query remote branch SHA; record completion if exact, block mismatch, do not repush blindly |
| Before PR create / PR response lost | Query all matching PR states and reconcile exact identity; no second create |
| CI unavailable / rate limit / network loss | Record unavailable evidence; bounded safe read retries, readiness blocked |
| Expired authentication / insufficient permission | Block writes; no credential provisioning or escalation |
| Head/base changed | Invalidate readiness and prior material authorization; retain old evidence |
| PR closed/merged externally | Record terminal observation; no reopen, replacement or merge action |
| Required checks changed / reviews dismissed | Recompute blockers for current policy/head |
| Partial multi-repository completion | Reconcile units independently; keep incomplete dependency/milestone blocked |
| Local transaction fails after remote success | Durable intent survives; external lookup precedes another action |

Recovery reports show previous local state, actual observed state, discrepancies, recommended safe observations and separately authorized actions. Deterministic policy controls the decisions.

## Operational state

PLANNED -> AWAITING_APPROVAL -> AUTHORIZED -> BRANCH_PREPARED -> AWAITING_PUBLICATION -> PR_PUBLISHED. From publication use CHECKS_PENDING, REVIEW_PENDING, BLOCKED or READY_FOR_AUTHORIZED_MERGE. Any ambiguous in-progress mutation enters RECOVERY_REQUIRED. Known failures enter FAILED with classification and preserved intent. Transitions are deterministic and tested; READINESS is recomputed from independent policy, CI, review and dependency snapshots. PR_PUBLISHED is not delivery success. READY_FOR_AUTHORIZED_MERGE is observational, never an executed merge.
