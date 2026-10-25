# AEO-2 overview — as built

AEO-2 adds one operator-invoked coding execution to the existing foundation. There is no
scheduler or agent-to-agent handoff execution. AEO-1 plans/tasks, AEO-1B recovery evidence
and AEO-1C design approval remain authoritative. Live execution defaults to disabled.

The operator prepares a persistent task scope, reviews exact repository/context/runtime
versions and validator commands, obtains an authenticated short-lived execution grant,
and explicitly starts the execution. A write task uses a dedicated Git worktree/branch.
Runtime events, normalized output, partial work, validation and decisions remain durable.
Model success is distinct from orchestrator validation and milestone delivery approval.

Original scope authorization is the user's AEO-2 request, whose source hash is in this
bundle manifest. These documents are observed as-built technical records; their design
approval status is pending review. No authenticated design approval is fabricated.
The original scope baseline and earlier approved versions are preserved independently.

Current evidence: Codex 0.164.0-alpha.11.1 supports exec/schema/JSON output and uses an
existing ChatGPT login. It rejects mcp-server. Native Windows MXC canaries passed for
read-only, worktree-write and validation-only. No live model smoke was invoked.
