# Repository isolation design — as built

Repositories resolve only through the existing confirmed manifest and per-role allowlists.
Write tasks require an explicit code-write/document operation and literal non-root scopes.
The original user worktree is never reset, cleaned, overlaid or checked out. A dedicated
branch/worktree starts from the approved HEAD; original uncommitted changes remain untouched
and are not silently copied into the new worktree. Context that depends on dirty approved
inputs remains visible and must match the reviewed version.

Native Windows MXC is required, without falling back to weaker isolation. The named filesystem
profile denies root reads, grants minimal runtime reads and target-repository reads, and grants
writes only to approved literal paths. Git metadata, agent/configuration controls, approved
milestone artifacts and authoritative contract roots are protected. Child environment values
are limited to essential Windows variables; production credentials are excluded. Command
networking, connectors/apps, MCP servers, web search, hooks and delegation are disabled.
[Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox)

Before a model call, fixed temporary canaries verify outside reads/writes are denied, inside
writes match the mode, sibling writes are denied and a controlled loopback connection fails.
No system sandbox setup, firewall mutation or PowerShell execution-policy bypass is performed.
Failure prevents model invocation. A future non-Windows/alternative isolation adapter must be
certified before use; there is no unrestricted fallback.

After exit, changed-file hashes and bounded archives preserve partial work, including ignored
outputs. Known secrets prevent automatic preservation/cleanup. Symlinks/junctions and artifact
budget overruns fail closed. Cleanup requires a terminal owned worktree, exact preserved file
hashes and a verified archive hash; it never removes the original tree or unrelated worktrees,
and branch refs are retained. Whole-worktree fingerprint budgets can block very large repos.
