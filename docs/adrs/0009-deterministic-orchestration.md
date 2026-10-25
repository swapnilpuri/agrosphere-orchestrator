# ADR 0009: Single-host deterministic orchestration

Status: Implemented for AEO-3; operational execution remains approval gated.

Reuse the approved milestone task graph, AEO-1C design validation, AEO-2 exact execution grants, native isolation, worktrees and Codex adapter. Persist scheduling plans separately as immutable revisions, with a human approval bound to their digest. Keep runtime claims and leases mutable, and store all results, handoffs and decisions as immutable evidence with atomic audit events.

Use SQLite BEGIN IMMEDIATE for task/resource admission and asyncio for independent task execution. Repository writers remain exclusive. Claims survive process interruption; lease expiry alone never proves termination. Uncertain writes require reconciliation. Automatic repair eligibility is bounded, but every new actual execution still requires an exact human grant. This preserves the stronger existing authorization boundary at the cost of interactive waves and repair approval.

No Redis, distributed queue, alternate agent execution framework, automatic scope expansion, merge, push or deployment is introduced. Future distributed coordination and preauthorized repair envelopes require a separate approved design.
