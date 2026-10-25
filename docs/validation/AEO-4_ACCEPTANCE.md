# AEO-4 acceptance evidence map

This map distinguishes framework behavior from application validation. All AEO-4 scanner findings, agent transports and privileged human identities in tests are fixtures. The actual native read-only validator probe and local PlantUML rendering are recorded separately.

| Acceptance area | Implementation | Evidence |
| --- | --- | --- |
| Existing functionality preserved | Existing services extended; original task state mapping unchanged | Full scripts/validate.py regression run and pytest.xml |
| Configurable policies | Strict safe YAML, authenticated version activation, repository command mappings | test_unauthorized_policy_change_rejected; test_cli_governance_commands |
| Deterministic gates | Native sandbox, allowlisted argv, JUnit/coverage/JSON/SARIF/file/architecture adapters | Adapter tests; aeo4-runtime.json real probe |
| Persisted immutable results | Migration 0006, content-addressed blobs and append-only event triggers | test_append_only_evidence_and_audit |
| Missing/invalid evidence blocks | Complete latest validation and integrity/freshness checks | Missing validator, malformed test, expiry and integrity tests |
| QA/security scheduling | Existing registry and AEO-3 dependencies, independent read-only reviews | test_multi_role_scheduler_to_quality_delivery (mocked transports) |
| Architecture compliance | Approved revision validation, explicit lexical ownership/boundary/stack rules and external compatibility commands | Native architecture test and architecture failure fixture |
| Documentation requirements | Repository-scoped mandatory files and editable sources; separate local render validation | Native documentation test; aeo4-docs.json |
| Verified human authorization | Existing HumanVerifier/WindowsConsoleHumanVerifier/DesignDecision authority | Mocked authorized/unauthorized/self/rejection/revocation/expiry tests |
| Artifact-specific decisions | Whole-tree/Git/design/scope/policy/execution config/repository manifest hashes | Changed artifact and command-policy tests |
| No silent security suppression | Findings retained; exact-finding expiring human exceptions | Secret/dependency fixtures, SARIF suppression test, changed/expired waiver tests |
| Bounded remediation | Existing AEO-3 evidence, explicit fresh write grant, original/new validation links | test_remediation_bounded_and_revalidation |
| Verifiable readiness | JSON/Markdown reports reference immutable gate and raw evidence blobs | Human approval/consumption and end-to-end fixtures |
| CLI | quality, security, approvals and milestone readiness commands | CLI fixtures and actual quality policies invocation |
| Architecture documentation | Guides, ADR 0010 and six editable PlantUML diagrams | aeo4-docs.json, rendered SVGs |

Production scanner coverage, remote identity assurance, and application business acceptance are not established by these fixture tests. Every delivery milestone must adopt an activated quality policy; legacy milestones retain their existing behavior until adoption.
