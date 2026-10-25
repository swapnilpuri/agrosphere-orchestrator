# Security and approval design — as built

Design approval, existing operation approval, execution authorization and Git worktree authority
are separate checks. The existing authenticated Windows human verifier is reused; the older
actor-string operation record alone cannot authorize a live run. Execution approvers default to
an empty SID allowlist. A grant includes exact scope/inputs/runtime/commands and expires within
one hour (default fifteen minutes). A human confirms the full execution digest and authenticates
with Windows credentials. No --actor or boolean input grants approval.

AEO-1C must approve the exact application design first. New execution approval cannot rewrite
that design or treat recovered implementation reports as requirements. Changed artifacts,
revoked approvers, stale context or source HEAD/policy drift block execution/acceptance. New
worktrees and task branch refs are the only trusted Git writes authorized by the execution
request. No commit, push, merge, PR, deployment, production infrastructure, external integration
or unrestricted installation capability is provided.

Codex uses its existing supported login or CODEX_API_KEY through the process environment.
Credentials are never put in prompts/reports; shell children do not inherit API keys or cloud/
database secrets. Metadata-only SDK tracing is explicitly opt-in and contains execution IDs,
role/task/transport only. Pricing estimates require explicit configured rates; missing pricing
never yields an invented estimate. Tracing export is an additional user-configured external action.

The user/config/database owner and installed runtime remain trusted. This is a local single-writer
service, not a hardened multi-tenant security boundary. Application test code may execute only
inside the approved native sandbox with exact administrator-allowlisted argv. Semantic/security
review and AEO-1C delivery approval remain necessary before accepting or deploying changes.
