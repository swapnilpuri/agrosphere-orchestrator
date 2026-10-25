# Codex transport compatibility

Status: Implemented for the explicitly authorized AEO-2 scope; documentation pending review.

The preferred Agents SDK/MCP route cannot run on installed Codex 0.164.0-alpha.11.1 because
help rejects mcp-server. Select codex exec with JSONL and a final JSON Schema, behind the
CodingAgentExecutor transport protocol. Keep an SDK MCP discovery adapter and refuse its
execution until its schema, isolation and process lifecycle are certified. Do not silently
install an older CLI or claim MCP compatibility from a cookbook example.

Consequences: the current transport works with Codex's supported login rather than an outer
planner model. Pydantic validates final output; the service, not the transport, governs approval,
context, task acceptance and validation. Optional SDK 0.24.0 supports metadata-only tracing.
See docs/validation/codex-runtime.json and the official sources listed in the AEO-2 bundle.
