<!-- BEGIN AEO RECOVERY -->
Snapshot: 49cdf041630e91d3ba8d4d06610285aefe7945058dbb4d42b0acacd384eff113

Observed at: 2026-10-26T04:59:08.394116+00:00
Workspace: C:\Projects\agrosphere

| Milestone | Observed state | Confidence |
|---|---|---|
| 0 | UNVERIFIED | low |
| 1 | UNVERIFIED | low |
| 1A | PARTIAL | medium |
| 1B | PARTIAL | medium |
| 1C | PARTIAL | medium |
| 2 | PARTIAL | medium |
| 3 | UNVERIFIED | low |
| 3A | PARTIAL | medium |
| 3B | UNVERIFIED | low |
| 4 | UNVERIFIED | low |
| 5 | UNVERIFIED | low |

Reused: repository inspector, Settings, Pydantic strict models, SQLAlchemy sessions, Alembic migrations, audit service and Typer conventions.

Added: recursive read-only inventory, evidence mapping, historical XML outcomes, content-addressed recovery snapshots, transactional current pointer, repeatable report export, project/milestones CLI groups and recovery tests.

Discovered application repositories:

- agrosphere-ai-service: C:\Projects\agrosphere\agrosphere-ai-service (branch main; HEAD cc92974049a50d64e6a5c1fb06868f01aa7f5def; dirty=False; error=None)
- agrosphere-analytics-service: C:\Projects\agrosphere\agrosphere-analytics-service (branch main; HEAD 38725317675493237b2769ed38e1840b3991d69e; dirty=False; error=None)
- agrosphere-api-gateway: C:\Projects\agrosphere\agrosphere-api-gateway (branch main; HEAD fcf7daf66fa0d9efaf2d1aa72f8cc88c600ab6c0; dirty=False; error=None)
- agrosphere-architecture: C:\Projects\agrosphere\agrosphere-architecture (branch main; HEAD ab6289d42dcc0ba4a956c39ed55b34c2f0c49746; dirty=True; error=None)
- agrosphere-contracts: C:\Projects\agrosphere\agrosphere-contracts (branch main; HEAD 7e962552421f15ad5d1492276817db1e1692b104; dirty=False; error=None)
- agrosphere-estate-service: C:\Projects\agrosphere\agrosphere-estate-service (branch main; HEAD 7fdd691431a6962f5ac71fb08e9e3e09380bae00; dirty=False; error=None)
- agrosphere-immersive: C:\Projects\agrosphere\agrosphere-immersive (branch main; HEAD 2bf7663e412f86956dbdb831184f2d0ab1a03c70; dirty=False; error=None)
- agrosphere-infrastructure: C:\Projects\agrosphere\agrosphere-infrastructure (branch main; HEAD 3268651e1d48a38f858351c105ab54b4103c3ded; dirty=False; error=None)
- agrosphere-operations-service: C:\Projects\agrosphere\agrosphere-operations-service (branch main; HEAD fbfda7e87dc0f650f013e6082d1f886df888b6c9; dirty=False; error=None)
- agrosphere-spatial-service: C:\Projects\agrosphere\agrosphere-spatial-service (branch main; HEAD 2a7dbda842141fca041510ca79481ea0454eaaf8; dirty=False; error=None)
- agrosphere-telemetry-service: C:\Projects\agrosphere\agrosphere-telemetry-service (branch main; HEAD 8a3c888dea3e1f3c7a94baf5c55a61285b5bcb7a; dirty=False; error=None)
- agrosphere-web: C:\Projects\agrosphere\agrosphere-web (branch main; HEAD 2a56f819cc653425e4c58bd6306872e352ee5c7a; dirty=False; error=None)

Missing manifest entries: none

Latest verified completed milestone: none established

Partial milestones: 1A, 1B, 1C, 2, 3A

Recommended next application work: review 3B scope against the 3A report only after verifying the earlier acceptance chain; no development is authorized by this report. The machine recommendation identifies the earliest verification gap.

AEO-2 readiness: foundation extended for durable discovery; application acceptance and historical conflicts still need review. Separate AEO-2 authorization is required.

Automated orchestrator validation: see docs/validation/commands.json and pytest.xml for actual commands, exit codes and timestamps. Application tests were not rerun.

Unresolved information and limits:

- Manifest-bound read-only observation; claims are not acceptance or execution authority.



- 1B: Both completion/implementation and not-started claims occur; inspect dates and scope.
- 1C: Both completion/implementation and not-started claims occur; inspect dates and scope.
- 2: Both completion/implementation and not-started claims occur; inspect dates and scope.





<!-- END AEO RECOVERY -->

## Final AEO-1B executed results

Recorded at 2026-10-24T20:50:33.839976+00:00. The required scripts/validate.py returned exit 0.
Pytest: 45 passed, no skips. Ruff lint/format, pip check, Alembic upgrade/check,
legacy CLI checks and dependency inventory all returned exit 0. The real-workspace
verification at 2026-10-24T20:50:23.432574+00:00 returned exit 0: 12 application repositories,
no missing manifest entries, unchanged application Git metadata/evidence fingerprints,
and identical snapshot/counts on repeated reconciliation. Snapshot: a0baa294d218243bba423d085bc1ad8e89ea4a4e538d9b0db1b849edd13912c4.
