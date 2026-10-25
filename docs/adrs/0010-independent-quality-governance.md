# ADR 0010: Independent artifact-bound quality governance

Status: Proposed implementation; existing approved architectural records remain unchanged.

Reuse AEO-1C human identity and DesignDecision authority, AEO-2 sandbox/command boundaries and AEO-3 transaction/repair/scheduling primitives. Add immutable quality evidence and an additive task quality lifecycle. Require explicit human activation of versioned policies and revalidate all artifact-bound approvals at use.

Decision: objective validation and complete requirement mappings determine readiness; LLM recommendations never approve delivery. Persist canonical content-addressed evidence and append-only records in existing SQLite. Reports are derived and can be invalidated; history remains immutable. Maintain compatibility for legacy milestones until explicit adoption.

Consequences: no new workflow engine, frontend or privileged execution mechanism. Local administrators remain trusted. Read-only native gates may require separately granted isolated build validation. Unsupported/missing validators block. Organization-wide enforcement requires migration of all delivery milestones to activated policies.
