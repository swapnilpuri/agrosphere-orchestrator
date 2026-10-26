# Milestone 1B adjudication matrix

Outcome: **REQUIRES_AUTHENTICATED_HUMAN_DECISION**. Dispositions below are recommendations, not runtime decisions. PARTIAL is not ACCEPTED.

## 1B-HIST-001

| Field | Evidence / proposed decision |
|---|---|
| assertion | Estate Service is implemented, independently buildable and container-tested. All requested acceptance checks completed locally: Java 21 build/tests, PostgreSQL startup, fresh and upgrade Flyway migrations, REST APIs, JWT authorization, atomic outbox creation, real RabbitMQ publication, Docker image and reproducible instructions. No other microservice was implemented, no central infrastructure configuration changed, no remote/commit/push/cloud deployment occurred, and Milestone 1B was not started. |
| source | agrosphere-estate-service/docs/MILESTONE_1A_REPORT.md:7 |
| support | Title: Milestone 1A completion report; line 3 dates the 1A outcome October 23, 2026, version 0.2.0; line 7 explicitly excludes next-stage work. Git blame and tracked blob verify the assertion is real. |
| counter | Spatial 1B report documents bounded delivered functionality; committed projection/store/migration and tests corroborate existence. They do not refute the earlier checkpoint. |
| independence | Original Estate artifact, separately sourced Spatial and Architecture artifacts. Same recorded Git author; not independent human attestations. |
| disposition | non-conflicting historical observation (RECOMMENDED; not applied) |
| rationale | The propositions describe different milestone checkpoints. Retain 1B not started at the 1A checkpoint; do not turn it into a timeless current-state denial. |
| authorization | Requires governed semantics and an authorized authenticated human disposition before runtime consistency changes. |
| consistency | Could remove this conflict only after approved capability and a valid scoped decision; PARTIAL and empty acceptance remain. |

## 1B-IMPL-002

| Field | Evidence / proposed decision |
|---|---|
| assertion | Spatial 1B completion report claims delivered Spatial Service 0.2.0 scope and 19+12 passing tests. |
| source | agrosphere-spatial-service/docs/MILESTONE_1B_REPORT.md:3,43-69,75-93 |
| support | Trackable blob, committed PostGIS queries, transaction-bound Estate projection, V2 migration, current matching test source. |
| counter | Test results are ignored local XML; no authenticated revision-binding or current execution; division lifecycle remains inferred and external rendering is excluded. |
| independence | Different repository and implementation artifact types; same project author and locally controlled Git. Strong existence evidence, no independent acceptance certification. |
| disposition | supports historical delivery; acceptance unresolved |
| rationale | Code existence is directly inspectable. Claimed passing tests are corroborated by result files, whose temporal/source binding remains limited. |
| authorization | No approval for read-only inspection; formal acceptance remains separately governed. |
| consistency | Supports semantic comparison only, never ACCEPTED/COMPLETED/execution eligibility. |

## 1B-TEST-003

| Field | Evidence / proposed decision |
|---|---|
| assertion | Retained JUnit: ApplicationRules 7, GeometryValidation 8, SecurityPolicy 4, SpatialServiceIT 12; zero failures/errors/skips. |
| source | agrosphere-spatial-service/target/{surefire,failsafe}-reports/TEST-*.xml |
| support | XML parsed this task; exact SHA-256 and case names captured in retained-junit-analysis.json. |
| counter | All four lack suite timestamp and are Git-ignored; no generating revision attestation. No tests rerun this task. |
| independence | Machine-readable local artifacts, different format from narrative; not an independently authenticated test runner. |
| disposition | historical corroboration with missing provenance |
| rationale | Absence of timestamp must remain explicit; a file mtime or matching case name is not execution certification. |
| authorization | A human cannot make these files current by approval; new reproducible validation would be needed for current acceptance. |
| consistency | Does not itself clear the checkpoint. |

## 1B-ARCH-004

| Field | Evidence / proposed decision |
|---|---|
| assertion | Scoped 1B local delivery is historically supported; acceptance matrix is an engineering assessment, not authenticated approval. |
| source | agrosphere-architecture/docs/roadmap/MILESTONE_1B.md; docs/adr/0009-spatial-digital-twin.md; docs/milestones/reconciliation-1a-3a/ACCEPTANCE_MATRIX.md:3,20 |
| support | Tracked and hashed roadmap/ADR/assessment; explicit limits and links to implementation/tests. |
| counter | Roadmap/ADR Git commit time precedes Estate and Spatial imports; cross-repository commit clocks are not a causal DAG. Assessment is derivative of project evidence. |
| independence | Separate architecture repository; same author; assessment is derivative, not an independent test or approval. |
| disposition | scope corroboration, not acceptance authority |
| rationale | Use explicit delivered scope and exclusions; do not rank by timestamp. |
| authorization | Existing signed-off design/acceptance must be demonstrated independently; no 1B runtime approval recovered. |
| consistency | No automatic change. |

## 1B-OTHER-005

| Field | Evidence / proposed decision |
|---|---|
| assertion | # Recommended Milestone 1B prompt (not executed); no renderer/client/terrain engine implemented; Compose shared services not started. |
| source | Architecture NEXT_CODEX_PROMPT.md:1; Spatial MILESTONE_1B_REPORT.md:50,89 |
| support | Exact records retained in prior 924-row matrix and fresh evidence. |
| counter | These concern planning, an excluded rendering component, and a validation action. |
| independence | Original planning/report sources; copied exports add no independent evidence. |
| disposition | out-of-scope for milestone-wide denial (already classified) |
| rationale | The existing scoped classifier preserves them without treating them as current delivery contradictions. |
| authorization | No new disposition applied here. |
| consistency | Already conflict-free for these sources. |

## 1B-CONTAM-006

| Field | Evidence / proposed decision |
|---|---|
| assertion | Quoted reports and nested fixture assertions appeared in the earlier two-root observation. |
| source | Prior contaminated-observation-records.json; autonomous event 2c95ea01-84bd-46c5-a331-59221e65be92 |
| support | Persisted observation identifies Orchestrator+Architecture and embedded source paths. |
| counter | Fresh exact-12-root discovery sources the Estate assertion directly; it remains even with fixture exclusion. |
| independence | Quotations are derivative; test fixtures are not application repositories. |
| disposition | out-of-scope (preserved prior audit evidence) |
| rationale | Do not confuse the original real assertion with contaminated copies. |
| authorization | No deletion or history editing permitted. |
| consistency | Cannot resolve the remaining direct-source 1B question. |

## Immutable artifact provenance

Full hashes, blob IDs, current HEADs, file-origin commits and XML case names are in [source-artifacts.json](source-artifacts.json) and [retained-junit-analysis.json](retained-junit-analysis.json).

| Artifact | SHA-256 of observed bytes | Git blob | Last file commit |
|---|---|---|---|
| agrosphere-estate-service/docs/MILESTONE_1A_REPORT.md | de879fb392c8f2d51e27fc97461636bcd1b32a62e9a1cb4747af69ecb58ba826 | e863fe945e6f7a28002fffb507209e733bd9995a | ca992841bc9694a4a9df0e504ade8e42c35acf01	2026-10-24T01:06:33-05:00	2026-10-24T01:06:33-05:00	swapnilpuri	Add JSON schema definitions for estate and plantation block events (v2) |
| agrosphere-spatial-service/docs/MILESTONE_1B_REPORT.md | c07f7755312a53851ad3ad792a0c65f183cab43ba5f7b5f3e695b8a4b80c57ef | 5a936de3be84b3aba0f5bb079664751fe9fcd468 | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	2026-10-24T01:10:10-05:00	swapnilpuri	feat(database): add initial database migrations for messaging and spatial features |
| agrosphere-spatial-service/src/main/java/com/agrosphere/spatial/adapter/in/messaging/EstateProjection.java | 8cc0ce460e0773e691fe69f30341a05d381b5f9847938248fd9a1f4237a3dce8 | 26681fd57a30abd42612ee2f772e72871e8d7f8c | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	2026-10-24T01:10:10-05:00	swapnilpuri	feat(database): add initial database migrations for messaging and spatial features |
| agrosphere-spatial-service/src/main/java/com/agrosphere/spatial/adapter/out/persistence/JdbcSpatialStore.java | 5c528737d999ba5868fae52594acdae269982e9bf1ba23f2dcc41ab9f6165eeb | 9751583b3d26e1d6e6063d47c376994d41b70cca | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	2026-10-24T01:10:10-05:00	swapnilpuri	feat(database): add initial database migrations for messaging and spatial features |
| agrosphere-spatial-service/src/main/resources/db/migration/V2__spatial_twin.sql | a7fdcaced0c9543a4e833ca81b753ee42e7c1bfd3056a30cf6442afc31b132c6 | 6d6e4ab9eecaf145711f5079447b6cda1f8888c2 | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	2026-10-24T01:10:10-05:00	swapnilpuri	feat(database): add initial database migrations for messaging and spatial features |
| agrosphere-spatial-service/src/test/java/com/agrosphere/spatial/SpatialServiceIT.java | 354012fc3e244a6bcea26d7eb6ba47716795aa6d21d6d415739512ac01924045 | fb915ef30f726a85c0d6c3953303c5315ebe9330 | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	2026-10-24T01:10:10-05:00	swapnilpuri	feat(database): add initial database migrations for messaging and spatial features |
| agrosphere-spatial-service/src/test/java/com/agrosphere/spatial/GeometryValidationTest.java | 9cad0bcc0fe8484ec1afb2db1a1270480ba14a7838438774e7768f97c9fa1afc | 65152c8c4c311d6fc6947d6b49f6899cfba0eb50 | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	2026-10-24T01:10:10-05:00	swapnilpuri	feat(database): add initial database migrations for messaging and spatial features |
| agrosphere-spatial-service/src/test/java/com/agrosphere/spatial/ApplicationRulesTest.java | 68f74a76caab3bbadbae208839465ddb31b672e6b91081a5fc03d5aabdfe2bac | 7c6656cf250e1e0bae7d285cfd8a164b62c1bdae | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	2026-10-24T01:10:10-05:00	swapnilpuri	feat(database): add initial database migrations for messaging and spatial features |
| agrosphere-spatial-service/src/test/java/com/agrosphere/spatial/SecurityPolicyTest.java | c0814a56f85aff37475c9902d7ed36a0c9f19d59a034553d2f5f9a556c1e88c7 | 07d379e644fd572eaaeb4d7a03ca9a8e3749597d | 7bce72d595e5f76fd4a7c38b1c4b6bc5997cb1a3	2026-10-24T01:10:10-05:00	2026-10-24T01:10:10-05:00	swapnilpuri	feat(database): add initial database migrations for messaging and spatial features |
| agrosphere-architecture/docs/roadmap/MILESTONE_1B.md | cfbf5fde319526b589caca27f52b4c2c89f7e28fd67cdc1d125cafe1c203d10c | f53cb81cd93c4658be641146dfac2c15fcaf2c66 | 11cc09cfc1e576cba4e89bfc2a6909def9dc4fb5	2026-10-24T00:57:35-05:00	2026-10-24T00:57:35-05:00	swapnilpuri	feat: Add initial documentation and requirements for AgroSphere project |
| agrosphere-architecture/docs/adr/0009-spatial-digital-twin.md | dc4de257c426aeff90aac7bb039af329e8fbd3f94f9f693920c788e5291586e5 | bcf7807de305390d56ff293107266a1cb779fbbd | 11cc09cfc1e576cba4e89bfc2a6909def9dc4fb5	2026-10-24T00:57:35-05:00	2026-10-24T00:57:35-05:00	swapnilpuri	feat: Add initial documentation and requirements for AgroSphere project |
| agrosphere-architecture/docs/milestones/reconciliation-1a-3a/ACCEPTANCE_MATRIX.md | 63fe8301b01d88e6ccc5b4bfc7cb66bfd85f526c80e0182b2dc400a933d9c4fb | 08b2730ae11e8300b3e979c233e2ce03c80dadaa | edffdc19868b7d8d9139bc8272405a30ce28bb3d	2026-10-26T00:42:52-05:00	2026-10-26T00:42:52-05:00	swapnilpuri	Add evidence index for reconciliation milestone 1a-3a |
| agrosphere-architecture/docs/milestones/reconciliation-1a-3a/evidence-index.json | 33adaee27870e5446f5435d80b766cefc37aee2a4792dff23e88bda2c7b1dcb1 | d2d9c047b90ed72719aec436e4dff4756c8f1d84 | edffdc19868b7d8d9139bc8272405a30ce28bb3d	2026-10-26T00:42:52-05:00	2026-10-26T00:42:52-05:00	swapnilpuri	Add evidence index for reconciliation milestone 1a-3a |
| agrosphere-spatial-service/target/surefire-reports/TEST-com.agrosphere.spatial.ApplicationRulesTest.xml | c339cf933813b7622bdfc6cd2d93f26f5ee13262c9aef8314fa945f472c3e3d0 | not available | not available |
| agrosphere-spatial-service/target/surefire-reports/TEST-com.agrosphere.spatial.GeometryValidationTest.xml | cbd03b8bc03225337cb902ab6e110cfd5cc9f39b81041553438f591e48a841e9 | not available | not available |
| agrosphere-spatial-service/target/surefire-reports/TEST-com.agrosphere.spatial.SecurityPolicyTest.xml | 90dfc51e63f732c3eae41099e431fd54f267030db6cb17ab425ee70cea89ad5a | not available | not available |
| agrosphere-spatial-service/target/failsafe-reports/TEST-com.agrosphere.spatial.SpatialServiceIT.xml | c589073f5da914f97f0b987f0dcf0109762b63b8a889bcdb5eed241903ba77b9 | not available | not available |
