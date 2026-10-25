# AEO-4 architecture assessment

The inspected AEO-1C design service owns requirements, immutable revisions, validation and Windows-authenticated DesignDecision records. AEO-2 owns execution requests, exact grants, sandbox profiles, bounded processes, worktree fingerprints and command allowlists. AEO-3 owns dependency scheduling, claims, resource locks, handoffs and bounded recovery. QA, security, architecture and writer roles already exist in the registry.

Gaps: successful commands do not establish business-criterion coverage; no versioned quality policy, independent gate evidence, severity evaluation, evidence expiry, security waiver or release readiness aggregate exists. Delivery decisions currently validate documentation rather than independently validating implementation artifacts. Existing generic task approvals are legacy operation approvals and must never authorize AEO-4 delivery.

Extend DesignDecision and HumanVerifier rather than add an approval authority. Add append-only governance evidence and content-addressed evidence blobs in the existing database, plus an additive task quality_state projection. Preserve succeeded as implementation/dependency completion for older records. Delivery remains a separate, enforced governance decision. Reuse the existing scheduler for advisory review roles and bounded repair, never grant privileges from agent output.
