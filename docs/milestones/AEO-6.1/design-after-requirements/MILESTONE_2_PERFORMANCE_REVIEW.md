# Milestone 2 performance and product review package

Status: unapproved preparation, no measurements. M2 remains DISCOVERED without approved registered requirements. Preserve the existing [detailed preparation draft](../preparation-20261027T005025Z/MILESTONE_2_PREPARATION_DRAFT.md); it remains the full source/decision matrix. Historical Web reports document implementation, not current objective acceptance.

| Owner decision | Required review input | Evidence needed after authorization |
|---|---|---|
| Product owner: reference environment | Exact supported device, CPU/GPU/RAM, OS/driver/browser, viewport/DPR, acceleration/power mode | Recorded actual environment, GPU renderer and flags |
| Product owner: frame requirement | Approve intended target, statistic/window and active workloads; proposed 30 fps remains unapproved | Raw rendered-frame samples, warm-up, agreed repetitions, outliers/failures and computed statistic |
| Product owner: initial useful view | Recover original approved budget or explicitly choose one; historical 10-second reference is unapproved | Agreed start/end events, usable canonical geometry and authoritative details; cold/warm samples |
| Product/data owner: representative workload | Canonical estate IDs, geometry/feature/vertex budget, LOD/assets, provider/license and network/cache conditions | Exact dataset/assets/configuration hashes and provenance/attribution |
| Engineering/QA: functional and integration evidence | Bind existing viewer/store/API tests to approved current revisions and quality gates | Real local build/integration/rendering results distinguished from fixtures and mocked tests |

Do not substitute requestAnimationFrame cadence for actual rendered-frame throughput in Cesium request-render mode. Do not use Playwright test duration as initial-view latency. Define repetitions, exclusions, warm/cold cache and backend readiness before collecting evidence; preserve failed trials. Current missing fields remain product decisions, not guessed target values.

After product decisions, prepare exact requirements/design/test mappings and manifest-bound roadmap context through normal requirements/design approvals, plan and execution grants. Use existing application components and preserve completed functionality; do not restart M2 implementation. No benchmark, browser/device run, application build, acceptance decision or application code change occurred in this task.
