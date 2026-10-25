# AEO-4 implementation and validation report

## 1. Implementation summary

Extended the existing orchestrator with independent quality/security governance. A versioned authenticated policy drives deterministic gates and explicit acceptance mappings. Immutable evidence, current artifacts and human authorization determine delivery eligibility; agent assertions cannot grant it. Application repositories are not edited, merged or deployed.

## 2. Existing components reused

AEO-1C approved requirements/design artifacts, DesignDecision persistence, HumanVerifier and WindowsConsoleHumanVerifier; AEO-2 command allowlists, native permission profiles, isolation probes, bounded process runner, worktree fingerprints and execution grants; AEO-3 dependency scheduling, registered QA/security/architect/writer roles, transaction primitive, audit and repair evidence. No separate workflow engine or identity authority was introduced.

## 3. New components and interfaces

quality_models.py defines policies, gates, findings, criteria, approval categories and results. quality_adapters.py exposes GateValidator plus sandboxed deterministic adapters. quality.py owns policy activation, validation, freshness/integrity checks, readiness, scoped decisions and remediation provenance. quality_store.py provides content-addressed evidence and append-only governance events.

## 4. Policies and validators

Commands resolve through Repository.validators into the existing ExecutionPolicy allowlist. Technology-independent adapters support Java/Spring, Python/FastAPI, Angular/TypeScript, Docker/infrastructure, database and contract toolchains through configured commands. Parsers support exit status, named JUnit cases, coverage.py-compatible JSON, strict scanner JSON and SARIF. Native document and explicit architecture rules are also available. The supplied policy is an intentionally incomplete template; unconfigured scanners block readiness. AEO-2 validation can be reused only with unchanged final worktree hashes and exact argv. Administrator-owned read_paths admits narrowly scoped runtime dependencies without granting those reads to the model.

## 5. Security controls

High/Critical findings block; Medium treatment is policy-defined; Low findings remain visible. SARIF in-source suppressions are not honored automatically. Exceptions require an existing deterministic finding, matching finding content, human authorization, justification, exact context and expiration. Scanner errors/missing evidence cannot be waived. Security findings do not automatically enter repair. The security configuration guide covers Keycloak, JWT/OIDC, gateway authorization, service identity, MQTT, RabbitMQ, database credentials and public exposure; mature configured scanners are required for actual security assessment.

## 6. Approval enforcement

Existing DesignDecision records hold new governance categories. Decisions use verified authorized SID identities, exact review subjects and transaction-time rechecks. Agents cannot self-approve or pass an arbitrary CLI actor. Wrong action/category, changed artifacts, expired/revoked decisions and consumed one-time authorization fail closed. Rejected decisions cannot be retried under unchanged scope. A successful validation creates a mandatory delivery-review request; READY_FOR_APPROVAL is distinct from approval. Existing AEO-1C delivery invokes the same guard after policy adoption and consumes delivery authorization atomically.

## 7. State-machine integration

Task.quality_state is an additive projection: IMPLEMENTED → VALIDATING → QUALITY_REVIEW → SECURITY_REVIEW → READY_FOR_DELIVERY_REVIEW → AWAITING_DELIVERY_APPROVAL → DELIVERY_APPROVED. Legacy succeeded retains implementation/dependency semantics. Changed evidence resets awaiting/approved quality state. Eligible failures can enter bounded remediation through existing AEO-3 evidence. Write repair remains an explicitly scoped new request with a fresh grant; the successful original worktree/result is retained. Revalidation events link original failures, retry counts, changed files, new execution IDs and final evidence.

## 8. Persistence

Alembic 0006 creates task_quality_states, governance_records and validation_evidence without changing the historical task-table mapper. This preserves operation against earlier schemas in upgrade tests. Governance records/evidence have append-only triggers and evidence content hashes are checked on retrieval. All state and audit writes share transactions. Destructive downgrade is rejected. Policies, definitions, outputs, findings, waivers, requests, decisions, readiness reports and artifact contexts are retained rather than overwritten. The validation runner also retains content-addressed run histories.

## 9. CLI examples

    aeo quality policies
    aeo quality activate --milestone AGRO-M3C
    aeo quality validate --milestone AGRO-M3C
    aeo quality report --milestone AGRO-M3C --markdown
    aeo security report --milestone AGRO-M3C
    aeo quality remediate --milestone AGRO-M3C
    aeo approvals pending
    aeo approvals inspect APPROVAL-ID
    aeo approvals decide APPROVAL-ID --decision approved --reason "Reviewed exact evidence"
    aeo milestone readiness --milestone AGRO-M3C

See the troubleshooting guide for approval requests, revocation and explicit write-repair preparation.

## 10. Automated tests

Focused AEO-4 run: **31 passed**. Final complete-project validation: **163 passed**, including all 132 pre-existing tests. All **18 validation commands returned exit code 0**. Exact output and command exit codes are recorded in commands.json and pytest.xml; content-addressed histories preserve earlier failed runs. Tests cover passing/failing gates, missing validators, invalid JUnit/scanner evidence, coverage threshold parsing, expiration, artifact changes, immutable history, critical findings, exact scoped/expired waivers, policy tampering, unauthorized/self approval, rejection/revocation, wrong scope and replay. A mocked multi-role AEO-3 workflow reaches independent validation and authenticated fixture approval. Build evidence in that workflow comes from hash-bound mocked AEO-2 execution results.

The assessment runs found and corrected an old-schema migration compatibility issue, JUnit parse normalization, runtime dependency reads, original-checkout/worktree selection and exception fingerprint binding. Intermediate failed runs are not represented as passes. Full command histories retain actual exit codes.

## 11. Real tool validation versus mocks

Real: project Python/pytest, Ruff lint/format, dependency consistency, Alembic upgrades/check, Git fixture operations, CLI execution, local PlantUML rendering and a native sandbox read-only Python validator. The final native probe passed with exit 0 and recorded outside-read/write, out-of-scope-write and network denial. Its first attempt failed with Python exit 106 because pyvenv.cfg was inaccessible; explicit administrator-owned runtime reads resolved it. Both attempts remain in aeo4-runtime-history.

Mocked: Codex agent output, scanner vulnerability/secret reports, business acceptance fixtures and human identity verification inside tests. No real dependency/secret/SAST/container scanner or live model was run. Interactive Windows human authentication was not exercised with real user credentials.

## 12. Architecture documentation and diagrams

The docs/aeo-4 directory contains the gap analysis, quality/security/approval designs, evidence model, readiness workflow, configuration and troubleshooting guides. ADR 0010 records the decision without modifying approved ADRs. Six editable sources cover the C4 component boundary, validation/review, human approval, failure/remediation, quality lifecycle and approval invalidation. All six rendered locally with no findings; SVGs and aeo4-docs.json retain results.

## 13. Remaining risks and limitations

- Adoption is explicit. Legacy milestones without activated policies retain AEO-1C delivery behavior; migrate every delivery milestone before treating AEO-4 as an organization-wide mandatory gate.
- Trusted local code/config/database administrators remain outside the adversarial boundary. SQLite/content hashes do not provide remote tamper-resistant storage.
- Windows password/SID verification is a local development mechanism; no production SSO/MFA identity claim is made. Test verifier injection is trusted code.
- Actual scanner, semantic OpenAPI/event/schema compatibility, business tests and application-specific security configuration checks require installed authorized tools and repository-specific policies. Lexical architecture checks prove only declared rules.
- Standalone native gates are read-only. Write-capable builds require separately granted isolated AEO-2 validation; multiple independent write worktrees must be reconciled before milestone-wide readiness. Original repair artifacts are preserved but not silently restored into a new write request.
- Command/JUnit validator versions are administrator declarations; structured scanner report versions are checked against metadata. Configure trusted wrappers and independently managed tools.
- Filesystem content may change between checks outside orchestrator-controlled operations. No production atomic deployment/merge or isolation certification is claimed. Neither is implemented here.

## 14. AEO-5 readiness

The governance foundation is implemented for review and local development. AEO-5 planning can use these contracts after reviewing policy adoption, real scanner/compatibility integrations and the identity/storage threat model. This work does not start AEO-5 or authorize delivery, deployment or merging.

See AEO-4_ACCEPTANCE.md for requirement-to-test mapping and docs/aeo-4/README.md for operator documentation.
