# Codex integration design — as built

CodingAgentExecutor separates transport from execution.run_execution, which returns a
typed ExecutionResult. The legacy AgentExecutor/CodexWorkspace protocols remain available
for compatibility. CodexExecutor/CodexExecAdapter use shell-free argument arrays, stdin
prompts, schema-constrained output and bounded JSON event capture. No model chooses tools,
permissions or retries on the orchestrator's behalf.

The preferred SDK/MCP route was evaluated against the official cookbook and local runtime.
The installed executable rejects mcp-server, so that route cannot satisfy this release's
required functionality. CodexMCPAdapter supports SDK connection/tool-schema discovery on
compatible runtimes and refuses uncertified execution/continuation. It is not advertised
as a verified MCP execution engine. The supported local transport is codex exec.
[Official MCP cookbook](https://developers.openai.com/cookbook/examples/codex/codex_mcp_agents_sdk/building_consistent_workflows_codex_cli_agents_sdk)

Exec uses the documented JSONL events and output-schema facility, then Pydantic validates
the final agent-message body. Malformed output preserves redacted raw evidence and fails.
An outer Runner is unnecessary for this deterministic single-tool path, avoiding an extra
planner model and credential requirement. The SDK 0.24.0 dependency remains optional for
MCP discovery and metadata-only tracing.
[Official non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)

Health checks invoke only version/help/login-status, never a model. Native exe paths are
configurable; .cmd/.bat/.ps1 launchers and arbitrary startup arguments are rejected. The only
startup argument allowed is --no-daemon. The runtime binary hash/version, model setting,
transport, role configuration and policy are bound into execution context.
