# Evidence conflict matrix

Application scope: exactly 12 confirmed manifest-bound repositories. Nested fixtures and Orchestrator are excluded. All 924 mapped records, not just negative triggers, are in [conflict-evidence-matrix.json](conflict-evidence-matrix.json). Each record includes file/line, excerpt, SHA-256, filesystem timestamp, observation HEAD, per-file last commit, scope/adjudication, implementation inventory, available tests, retained outcomes, acceptance and unresolved contradiction. SHA-256 identifies bytes; observation HEAD and filesystem mtime do not authenticate authored time or test revision. No record is declared legitimately superseded.

The 1,411 records behind the contaminated two-root observation are preserved in [contaminated-observation-records.json](contaminated-observation-records.json), excluded from the application matrix. That event has 53 broad negative phrase matches across the five milestones.

| Milestone | Current classification | Current conflict | Actual observed implementation | Available tests | Verified acceptance |
|---|---|---|---|---|---|
| 1A | PARTIAL | none | agrosphere-estate-service: 41 source files observed; see inventory | 12 files; historical execution only | 0 criteria |
| 1B | PARTIAL | Both completion/implementation and not-started claims occur; inspect dates and scope. | agrosphere-spatial-service: 33 source files observed; see inventory | 6 files; historical execution only | 0 criteria |
| 1C | PARTIAL | none | agrosphere-api-gateway: 9 source files observed; see inventory | 14 files; historical execution only | 0 criteria |
| 2 | PARTIAL | none | agrosphere-web: 37 source files observed; see inventory | 17 files; historical execution only | 0 criteria |
| 3B | UNVERIFIED | none | none linked | 0 files; historical execution only | 0 criteria |

## Exact negative-trigger rows

| Milestone | Source and line | Timestamp (filesystem UTC) | Last file commit | Claim / scope | Adjudication | Unresolved contradiction |
|---|---|---|---|---|---|---|
| 1B | agrosphere-architecture/docs/roadmap/NEXT_CODEX_PROMPT.md:1 | 2026-10-24T04:12:39.102992+00:00 | 11cc09cfc1e576cba4e89bfc2a6909def9dc4fb5	2026-10-24T00:57:35-05:00	feat: Add initial documentation and requirements for AgroSphere project | # Recommended Milestone 1B prompt (not executed) | planning-only | none |
| 1B | agrosphere-estate-service/docs/MILESTONE_1A_REPORT.md:7 | 2026-10-24T04:16:32.259642+00:00 | ca992841bc9694a4a9df0e504ade8e42c35acf01	2026-10-24T01:06:33-05:00	Add JSON schema definitions for estate and plantation block events (v2) | No other microservice was implemented, no central infrastructure configuration changed, no remote/commit/push/cloud deployment occurred, and Milestone 1B was not started. | historical-unresolved | Both completion/implementation and not-started claims occur; inspect dates and scope. |
| 1B | agrosphere-spatial-service/docs/MILESTONE_1B_REPORT.md:50 | 2026-10-24T05:17:40.994104+00:00 | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	feat(database): add initial database migrations for messaging and spatial features | GeoJSON import is a bounded JSON FeatureCollection wrapper, atomically validated/persisted in the calling request with a durable job/report No partial features/events survive failed imports Export preserves feature/reference identifiers, geometry versions, provenance, bbox, centroid and calculated hectares 3D Tiles metadata is supported through layers no renderer, client or terrain engine is implemented. | component-or-validation-scope | none |
| 1B | agrosphere-spatial-service/docs/MILESTONE_1B_REPORT.md:89 | 2026-10-24T05:17:40.994104+00:00 | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	feat(database): add initial database migrations for messaging and spatial features | \| Compose overlay config --quiet \| PASS using placeholder configuration shared services were not started \| | component-or-validation-scope | none |
| 1C | agrosphere-spatial-service/docs/MILESTONE_1B_REPORT.md:126 | 2026-10-24T05:17:40.994104+00:00 | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	feat(database): add initial database migrations for messaging and spatial features | Recommended Milestone 1C integration tasks (not started) | planning-only | none |
| 2 | agrosphere-infrastructure/docs/MILESTONE_1C_REPORT.md:200 | 2026-10-24T06:14:46.021627+00:00 | 0caac03f5ebc4b5fe05f70cdca534e5850c19d99	2026-10-24T01:22:45-05:00	Update comments for clarity on localhost cookie policy behavior in dev_identity.py | Recommended Milestone 2 sequence (not started) | planning-only | none |
| 3B | agrosphere-architecture/docs/milestones/milestone-3a-completion.md:3 | 2026-10-24T19:41:04.786455+00:00 | ab6289d42dcc0ba4a956c39ed55b34c2f0c49746	2026-10-24T15:47:35-05:00	feat: Update version to 0.5.0, add Milestone 3A diagrams, and enhance documentation with completion and development reports | Milestone 3B was not started. | historical-unresolved | none |
| 3B | agrosphere-architecture/docs/milestones/milestone-3a-completion.md:111 | 2026-10-24T19:41:04.786455+00:00 | ab6289d42dcc0ba4a956c39ed55b34c2f0c49746	2026-10-24T15:47:35-05:00	feat: Update version to 0.5.0, add Milestone 3A diagrams, and enhance documentation with completion and development reports | No Milestone 3B feature was implemented. | historical-unresolved | none |

## Implementation, test and acceptance anchors

### 2

Web EstateStore, typed API clients and Cesium viewer lifecycle/picking; unit/UI/graphics/live test source and retained embedded Playwright result. Functional completion claims are bounded by the explicit unverified reference-device rendering/frame and useful-view timing gate.

Inventory-linked test paths:

- agrosphere-web/tsconfig.spec.json
- agrosphere-web/e2e/fixtures.ts
- agrosphere-web/e2e/graphics.spec.ts
- agrosphere-web/e2e/live.spec.ts
- agrosphere-web/e2e/ui.spec.ts
- agrosphere-web/src/app/app.component.spec.ts
- agrosphere-web/src/app/api/clients.spec.ts
- agrosphere-web/src/app/core/errors.spec.ts
- agrosphere-web/src/app/core/auth/auth.guard.spec.ts
- agrosphere-web/src/app/core/auth/auth.service.spec.ts
- agrosphere-web/src/app/core/interceptors/gateway.interceptor.spec.ts
- agrosphere-web/src/app/features/blocks/block-detail.component.spec.ts
- agrosphere-web/src/app/features/dashboard/dashboard.component.spec.ts
- agrosphere-web/src/app/features/digital-twin/cesium-viewer.component.spec.ts
- agrosphere-web/src/app/features/estates/estate.store.spec.ts
- agrosphere-web/src/app/features/spatial-layers/layer-manager.component.spec.ts
- agrosphere-web/src/app/shared/models.spec.ts

Retained results for agrosphere-web: []. These are historical and are not bound to current source acceptance.

### 1A

EstateApplicationService.java, JwtEstateAccess.java, OutboxDispatcher.java; EstateServiceIT.java and retained Estate JUnit XML. Architecture acceptance matrix supports historical local estate scope, not broad FR-01 company management.

Inventory-linked test paths:

- agrosphere-estate-service/src/test/java/com/agrosphere/estate/ApplicationServiceTest.java
- agrosphere-estate-service/src/test/java/com/agrosphere/estate/DomainRulesTest.java
- agrosphere-estate-service/src/test/java/com/agrosphere/estate/EstateAuthorizationTest.java
- agrosphere-estate-service/src/test/java/com/agrosphere/estate/EstateServiceIT.java
- agrosphere-estate-service/src/test/java/com/agrosphere/estate/OutboxDispatcherTest.java
- agrosphere-estate-service/src/test/java/com/agrosphere/estate/SecurityPolicyTest.java
- agrosphere-estate-service/src/test/resources/contracts/README.md
- agrosphere-estate-service/src/test/resources/contracts/estate-service.openapi.json
- agrosphere-estate-service/src/test/resources/contracts/events/v2/EstateCreated.schema.json
- agrosphere-estate-service/src/test/resources/contracts/events/v2/EstateUpdated.schema.json
- agrosphere-estate-service/src/test/resources/contracts/events/v2/PlantationBlockCreated.schema.json
- agrosphere-estate-service/src/test/resources/contracts/events/v2/PlantationBlockUpdated.schema.json

Retained results for agrosphere-estate-service: [{"path":"target/failsafe-reports/TEST-com.agrosphere.estate.EstateServiceIT.xml","tests":9,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"},{"path":"target/surefire-reports/TEST-com.agrosphere.estate.ApplicationServiceTest.xml","tests":9,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"},{"path":"target/surefire-reports/TEST-com.agrosphere.estate.DomainRulesTest.xml","tests":10,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"},{"path":"target/surefire-reports/TEST-com.agrosphere.estate.EstateAuthorizationTest.xml","tests":9,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"},{"path":"target/surefire-reports/TEST-com.agrosphere.estate.OutboxDispatcherTest.xml","tests":7,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"},{"path":"target/surefire-reports/TEST-com.agrosphere.estate.SecurityPolicyTest.xml","tests":4,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"}]. These are historical and are not bound to current source acceptance.

### 1B

JdbcSpatialStore.java, EstateProjection.java, SpatialServiceIT.java; retained Spatial JUnit XML (historical 31 passing tests per architecture reconciliation). No current-revision acceptance attestation.

Inventory-linked test paths:

- agrosphere-spatial-service/src/test/java/com/agrosphere/spatial/ApplicationRulesTest.java
- agrosphere-spatial-service/src/test/java/com/agrosphere/spatial/GeometryValidationTest.java
- agrosphere-spatial-service/src/test/java/com/agrosphere/spatial/SecurityPolicyTest.java
- agrosphere-spatial-service/src/test/java/com/agrosphere/spatial/SpatialServiceIT.java
- agrosphere-spatial-service/src/test/resources/oidc-public-jwk.json
- agrosphere-spatial-service/src/test/resources/postgis.sql

Retained results for agrosphere-spatial-service: [{"path":"target/failsafe-reports/TEST-com.agrosphere.spatial.SpatialServiceIT.xml","tests":12,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"},{"path":"target/surefire-reports/TEST-com.agrosphere.spatial.ApplicationRulesTest.xml","tests":7,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"},{"path":"target/surefire-reports/TEST-com.agrosphere.spatial.GeometryValidationTest.xml","tests":8,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"},{"path":"target/surefire-reports/TEST-com.agrosphere.spatial.SecurityPolicyTest.xml","tests":4,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"}]. These are historical and are not bound to current source acceptance.

### 1C

Infrastructure scripts/smoke_platform.py, Compose/identity configuration, target/platform-smoke.json and milestone-1c-full-smoke.log (12 historical acceptance groups); Gateway implementation and retained 12-test XML. Collector only links source inventory in Gateway; Python scripts are separately visible in full repository fingerprints.

Inventory-linked test paths:

- agrosphere-api-gateway/src/test/java/com/agrosphere/gateway/GatewayIntegrationTest.java
- agrosphere-api-gateway/src/test/java/com/agrosphere/gateway/SecurityPolicyTest.java
- agrosphere-infrastructure/tests/contracts/estate.openapi.json
- agrosphere-infrastructure/tests/contracts/manifest.json
- agrosphere-infrastructure/tests/contracts/spatial.openapi.json
- agrosphere-infrastructure/tests/contracts/events/spatial/v1/DigitalTwinAssetRegistered.schema.json
- agrosphere-infrastructure/tests/contracts/events/spatial/v1/SpatialBoundaryChanged.schema.json
- agrosphere-infrastructure/tests/contracts/events/spatial/v1/SpatialFeatureCreated.schema.json
- agrosphere-infrastructure/tests/contracts/events/spatial/v1/SpatialFeatureUpdated.schema.json
- agrosphere-infrastructure/tests/contracts/events/spatial/v1/SpatialLayerCreated.schema.json
- agrosphere-infrastructure/tests/contracts/events/v2/EstateCreated.schema.json
- agrosphere-infrastructure/tests/contracts/events/v2/EstateUpdated.schema.json
- agrosphere-infrastructure/tests/contracts/events/v2/PlantationBlockCreated.schema.json
- agrosphere-infrastructure/tests/contracts/events/v2/PlantationBlockUpdated.schema.json

Retained results for agrosphere-api-gateway: [{"path":"target/surefire-reports/TEST-com.agrosphere.gateway.GatewayIntegrationTest.xml","tests":8,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"},{"path":"target/surefire-reports/TEST-com.agrosphere.gateway.SecurityPolicyTest.xml","tests":4,"failures":0,"errors":0,"skipped":0,"outcome":"historical-pass"}]. These are historical and are not bound to current source acceptance.

### 3B

3A completion report explicitly denies 3B feature implementation. No 3B implementation or acceptance is recovered. COMPLETE in that report describes 3A, not 3B.

Inventory-linked test paths:

- None linked.

## Human review question

Does Estate docs/MILESTONE_1A_REPORT.md:7 describe only the historical 1A checkpoint, with its 1B denial legitimately superseded by the scoped Spatial 1B implementation report and corroborating source/tests? Specify the historical boundary, evidence hashes and revision provenance. Do not convert the historical claims or passing artifacts into formal/current acceptance. Without that provenance, retain discovery-conflict.

No genuine simultaneous current contradiction has been established; the remaining block is unresolved historical status provenance. File modification ordering and unrelated repository commit dates alone cannot resolve it.
