# Exact execution grants and native repository isolation

Status: Implemented for authorized AEO-2; operational decisions remain human-controlled.

Reuse authenticated Windows human verification for expiring grants bound to exact task,
context, repository HEAD, role, runtime binary/model, allowed scopes and validator argv.
Preserve the separate original operation approval and AEO-1C design approval. New worktree
and branch creation is an explicit grant side effect; no application commit/push is provided.

Require Windows MXC and a named literal-path permission profile with root reads denied,
minimal/target reads, scoped writes and networking disabled. Disable connectors, web, MCP,
hooks and delegation. Probe native file/network boundaries before any model. Unknown or
unsupported isolation fails closed. Runtime/model authorization does not grant unrestricted
Git or tool access. No weaker native fallback is silently selected.

Consequences: only native Windows is certified here. Protected files/approved revisions are
not writable. Directory scopes are required by the current non-destructive canary. Large
artifact budgets and inaccessible process identities can block execution/cleanup for review.
