# AEO-6 persistent discovery conflict recovery report

Run: ba0851d4-66bc-417a-851b-f08176bd8061. Outcome: false scope conflicts corrected; explicit 1B historical evidence review remains. No application implementation, publication, model invocation, new run or history reset occurred.

## Root cause and previous implementation

Two distinct defects caused the observed block. The latest committed observation used only Orchestrator and Architecture, ingested nested test fixtures and exported reports, and reported conflicts in 1A/1B/1C/2/3B. Its event ID is 2c95ea01-84bd-46c5-a331-59221e65be92 (2026-10-26T05:39:49.240559+00:00). The preceding operation used all 12 application repositories and reported only 1B/1C/2. Current configuration resolves the correct 12 roots. The exact historical environment override and imported module version cannot be reconstructed because that operation did not persist a manifest path/hash or classifier fingerprint. We do not claim a specific unrecorded override file caused it.

The previous manifest-bound root integration and claim_text sentence scoping exist. The historical adjudication enhancement did not exist: global negative/positive phrase booleans ignored evidence scope, temporal provenance and legitimate supersession. Current fresh discovery invokes this same recovery_discovery module through autonomous_cli.resume_command -> controller.resume -> run/advance -> ExistingServices.perform(RECONCILING) -> discover -> collect_repository -> recover_milestones. Resume re-observes repository files; status/report present persisted observations. No stale RecoveryRecord is used as classifier input. A changed invocation configuration can nevertheless change discovery roots because repository manifest identity is not frozen in the run request. Explicitly pin the application manifest in operator commands.

## Changes and design control

Existing AEO-6 immutable scope/revision, exact registered plan, 22 approved artifacts, authorized requirements decision c003c8e6-7477-4c5d-a226-194a5995539e and design decision 506b66d5-2e8c-423e-9cf6-814cef4aadb5 passed the established implementation checkpoint verifier before and after changes. This bounded correction preserves discovery as observation and leaves all authorization/acceptance gates intact. No immutable requirements/design artifacts or imported plans were edited.

Modified source: src/agrosphere_orchestrator/recovery_discovery.py (conservative scoped adjudication); src/agrosphere_orchestrator/recovery_models.py (additive adjudications metadata). Added tests/test_discovery_adjudication.py. Each mapped claim retains its file/line/hash/mtime/observed HEAD and disposition. Narrow recommendation headings and the identified component/validation statements no longer contradict milestone delivery. Ambiguous negatives, explicit current denials, unknown timestamps and revision uncertainty remain blocking when implementation/completion claims coexist. Historical predecessor claims are identified, but no record is automatically superseded. No newest-record rule, automatic COMPLETED classification or verified acceptance is introduced.

Inspected source and exact SHA-256 values: [source-inspection.json](source-inspection.json). Inspection includes autonomous CLI/controller/services/store, recovery collection/models/reconciliation, settings, configuration, repository manifest, existing recovery/security tests and validator. Application implementation anchors were inspected read-only; their paths and evidence limits are in the matrix.

## Evidence matrix and classifications

[Readable evidence matrix](EVIDENCE_CONFLICT_MATRIX.md); [all 924 application evidence rows](conflict-evidence-matrix.json); [all 1,411 contaminated historical rows](contaminated-observation-records.json). The latter are audit context, not application repositories. Every application record contains timestamps, available revisions, status claim/scope, observed implementation, available tests, retained test results, acceptance, disposition and unresolved contradiction. Full inventories and source fingerprints are in [authoritative-observation.json](authoritative-observation.json).

| Milestone | Classification | Current conflict / interpretation |
|---|---|---|
| 1A | PARTIAL | None. Historical local Estate delivery supported; full/current authenticated acceptance absent. Earlier conflict came from Orchestrator fixtures/quoted reports. |
| 1B | PARTIAL | Estate 1A report line 7 denies 1B at that checkpoint; Spatial implementation/report/tests corroborate later delivery. Historical supersession provenance remains unadjudicated. Renderer exclusion, unstarted Compose services and recommended prompt are separate scopes. |
| 1C | PARTIAL | None. Predecessor report's recommended integration tasks are planning evidence. Local historical platform validation exists; current formal acceptance absent. |
| 2 | PARTIAL | None. Predecessor report's recommended next sequence is planning evidence. Functional delivery claims do not satisfy the open rendering/performance exit gate. |
| 3B | UNVERIFIED | None. 3A COMPLETE belongs to 3A; 3B not-started claims have no matching implementation/completion claim. No 3B implementation authorized. |

No simultaneous current application contradiction has been established. The remaining conservative checkpoint represents unproven historical supersession. Filesystem mtime, observed HEAD, commit subjects and unrelated cross-repository commit dates cannot establish it. The per-file last commit is included separately and is not a signed claim-origin/test attestation.

## Recovery performed

Fresh read-only collection used exactly 12 confirmed application repositories: AI, Analytics, Gateway, Architecture, Contracts, Estate, Immersive, Infrastructure, Operations, Spatial, Telemetry and Web. The supported AEO-1B reconcile service appended snapshot cc98fd3fadb2b7fa0e0e4b6035b06240807560705fd1dc1182132d0b4ac09fdb and moved the recovery head transactionally. All five prior recovery records remain; there are now six. No prior snapshot was rewritten.

Supported autonomous recover returned the same run because there is no unfinished operation. The run report before/after is identical. A read-only RECONCILING service check independently returned discovery-conflict for 1B. Run validation passed. discovery_consistent is false; discovery-conflict remains; execution_eligible and numeric_advancement_authorized remain false. Resume was withheld because the historical review remains unresolved. Evidence: [reconciliation-result.json](reconciliation-result.json), [read-only-controller-check.json](read-only-controller-check.json), [run-after.json](run-after.json).

## Independent Milestone 2 blockers

Milestone 2 is DISCOVERED with missing-requirements: no approved scope. The existing run request contains no requirements or task options. The eligibility precheck returns null only because no registered scope exists; this permits proposed requirements preparation and is not execution eligibility. Application execution still requires approved requirements, exact technical design and plan, a roadmap bound to approved context with formally completed dependencies, exact execution grants and independent quality policy/results. These have not been established for Milestone 2.

The architecture acceptance reconciliation explicitly leaves the reference-device rendering/frame target and reproducible useful-estate-view timing gate open. Select a named device/browser/dataset, confirm the authoritative timing budget (the report's 10-second figure lacks recovered original approval), and obtain reproducible evidence. Do not manufacture performance acceptance from software WebGL tests or a test's total runtime. No fresh application tests or performance benchmark were executed here.

The immutable 3,600-second run deadline remains in force. At recovery observation 2,385.58 seconds remained; that is a point-in-time value, not a renewal. Resume cannot reset counts or extend that deadline. If it expires, existing controller behavior is a budget pause; no supported budget-extension command was found, and this work does not invent one or create another run.

## Human evidence adjudication and next operator action

Review [HUMAN_ADJUDICATION_REVIEW.json](HUMAN_ADJUDICATION_REVIEW.json) and the matrix. Establish whether Estate's 1A checkpoint denial of 1B is legitimately superseded by scoped Spatial delivery, citing exact hashes/revisions and test freshness limits. Preserve the historical statement and keep milestone acceptance separate. There is currently no authenticated evidence-adjudication CLI; this report is a review package, not runtime approval. A persisted adjudication mechanism that changes authority requires an approved change-control design. Do not manually edit the run, snapshots or approvals to clear the checkpoint.

After supported adjudication and applicable gates are satisfied, the exact existing resume command is below. Pinning the application manifest prevents reusing an internal design manifest. The CLI rechecks evidence, limits and authority; this command does not grant execution or publication rights.

~~~powershell
Set-Location C:\Projects\agrosphere\agrosphere-orchestrator
$env:AEO_REPOSITORY_MANIFEST = 'C:\Projects\agrosphere\agrosphere-orchestrator\config\repositories.yaml'
$env:AEO_WORKSPACE_ROOT = 'C:\Projects\agrosphere'
$env:AEO_DATABASE_URL = 'sqlite:///C:/Projects/agrosphere/agrosphere-orchestrator/aeo.db'
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli autonomous resume ba0851d4-66bc-417a-851b-f08176bd8061
~~~

## Validation

15 new adjudication/reconciliation tests passed (exit 0); 68 existing focused recovery/controller/security tests passed (exit 0). Changed-file Ruff lint and formatting checks passed (exit 0). The AEO-6 implementation checkpoint verifier passed before/after; real existing-run validate returned valid=true. New coverage includes historical denial followed by implementation, current contradiction, partial acceptance, missing timestamp, conflicting revisions, stale persisted heads, exact 12-root scope with nested fixture exclusion, and same-run re-observation without history reset. The historical/revision cases deliberately retain the checkpoint rather than infer verified acceptance.

Established scripts/validate.py completed with exit 0. All 18 commands returned exit 0. Full pytest: 367 passed, zero failed/errors/skips, 723.83 seconds. The full suite collected the first 13 new cases; the two added later passed in the separate 15-case focused run. No production source changed after full-suite launch. Full lint/format, pip dependency check, Alembic upgrade/check, repository/CLI/docs validators also returned 0. [Exact commands/stdout/stderr](established-commands.json), [JUnit](established-pytest.xml), [summary](validation-summary.json).

The design-tool capability probe reports plantuml-unavailable despite its zero exit code; future design approval/rendering requires configured AEO_PLANTUML_JAR. This is an observed readiness finding, not a claim of renderer availability. Existing AEO-6 approved rendered artifacts passed their separate immutable-artifact verification. Retained application JUnit/Playwright results are historical evidence, not tests executed by this task.
