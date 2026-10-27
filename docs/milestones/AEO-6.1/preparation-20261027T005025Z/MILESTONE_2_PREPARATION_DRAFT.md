# Milestone 2 preparation draft — no approval or execution authority

Status: draft only; not registered as Milestone 2 requirements, not a generated/validated technical design, and not acceptance evidence. Product-owner choices below must be resolved before an exact DesignInput can be registered. No application source, build, browser benchmark or model was executed.

## Recovered requirements and acceptance matrix

| Requirement / gate | Authoritative source | Current evidence | Missing acceptance |
|---|---|---|---|
| Canonical estate navigation, block selection and authoritative details | Architecture docs/requirements/FUNCTIONAL_REQUIREMENTS.md FR-03; docs/roadmap/MILESTONES.md row 2 | Web docs/MILESTONE_2_REPORT.md describes Angular/Cesium implementation, API adapters, lifecycle/picking and functional items 1–17 | Fresh reproducible checks bound to current web/backend/contracts revisions and approved scope |
| Provenance and source attribution | FR-12; M2 roadmap; Web report and attribution configuration | Historical report/source only | Current configuration, data/asset provenance and permitted provider notices verified |
| Reference-device frame budget | Architecture docs/requirements/NONFUNCTIONAL_REQUIREMENTS.md:9 proposes 30 fps minimum on a named desktop | Web report: no reference-device FPS claim; software-rendered fixture navigation is not this gate | Approved reference hardware, representative dataset/assets/provider configuration, metric definition, sample plan and actual evidence |
| Initial useful estate view | Web docs/MILESTONE_2_REPORT.md:72,115; docs/ARCHITECTURE.md:29 | No measured reference-device target; report mentions 10 seconds but does not claim it | Original authoritative approved threshold or explicit product decision; agreed start/end timing and actual samples |
| Dependencies, security and quality | Existing AEO design/roadmap/task/quality policies | No registered M2 scope; no approved autonomous roadmap configured | Exact registered requirements/design/plan, formal dependency evidence, current policy/gates and authenticated execution grants |

The 30 fps statement is explicitly a proposed NFR, not an authenticated M2 threshold approval. The 10-second figure is a historical report reference with no recovered original approved numbered specification. Neither is silently adopted by this draft. The broad parent FR backlog is not proof that implemented increments are absent; do not restart their completed functional work.

## Proposed technical validation design (unapproved)

Reuse existing Web viewer/store/API adapters and tests; do not replace the application. After scope/design authorization, add only the approved bounded measurement/validation instrumentation and scripts if existing tests cannot supply evidence. Keep browser rendering evidence distinct from mock functional tests, live Gateway integration, build success and hosted CI.

A frame benchmark should capture rendered-frame timing during agreed active Cesium navigation, selection and layer-toggle scenarios. Browser requestAnimationFrame cadence alone is not proof of rendered frames, especially with request-render mode, tab throttling or software WebGL. Retain the chosen frame metric, interval, raw samples and all failures. Agree the acceptance statistic before collecting data; average FPS cannot silently stand for a minimum.

Define initial useful view explicitly: agree whether timing starts at navigation after authenticated login or includes login/startup; end only when the agreed canonical geometry has rendered and the authoritative details panel is usable. Separate cold/warm resource cache conditions and backend readiness. Never substitute total Playwright test duration or the existing fixture navigation/remount timer.

Record exact hardware model/CPU/GPU/RAM, OS, GPU driver, browser/version, viewport/resolution/device-pixel ratio, power mode, acceleration/GL renderer and any browser flags. Record source/configuration commits and raw hashes, dataset canonical IDs and feature/vertex counts, asset/LOD/terrain budgets and provider/licensing/network/cache conditions. Agree repetitions, warm-up and exclusions before running; preserve failed or outlier samples. No device or result is selected or measured in this draft.

## Precise product-owner decisions

| ID | Options | Recommendation / impact |
|---|---|---|
| M2-PO-DEVICE | A: name a hardware-accelerated desktop already intended for local demonstration; B: name a minimum supported user device | A is the narrowest continuation of the existing proposed desktop gate; B broadens the compatibility claim. Supply exact device/driver/browser specification either way. |
| M2-PO-FRAMES | A: confirm the proposed 30 fps target and define the minimum measurement/statistic/window; B: provide an authoritative revised requirement | Prefer confirming/recovering the intended requirement. Both require an explicit statistic, active workload, sample plan and asset budget. No target is approved here. |
| M2-PO-TIMING | A: recover the original approved initial-view budget; B: explicitly adopt a new budget including whether the historical 10-second reference is intended | Prefer A. B is a new product requirement and must be registered/approved. Define cold/warm conditions and start/end events. |
| M2-PO-DATA | A: agree a representative SIMULATED local estate and permitted local/fallback assets; B: agree licensed network terrain/imagery and representative operating data | A supports reproducibility without inventing provider availability; B needs license/provider/network and data-provenance decisions. Agree geometry/asset/LOD budgets. |

These are pending decisions in a draft, not requests to weaken gates or approve the application by conversation.

## Existing-run restrictions

Run ba0851d4-66bc-417a-851b-f08176bd8061 remains BLOCKED/discovery-conflict for 1B and has an expired immutable one-hour deadline. M2 is DISCOVERED/missing-requirements. No autonomous roadmap is configured and no formal dependency completions were established. Resolving 1B would not change M2 acceptance, execution eligibility or that deadline. No supported budget-extension command exists; a future extension policy would require its own governed scope. No new run or budget reset is proposed here.

## Next established AEO steps

First finish the pending internal adjudication requirements/design approval workflow. Separately resolve the product decisions, then prepare an exact M2 DesignInput with recovered context hashes, test plan and roadmap dependency evidence. Register through milestone design 2 --requirements <validated-input>, obtain interactive approve-requirements 2, generate/render/validate the technical design, then obtain approve-design 2 and the existing implementation/plan/execution/quality gates. These are future conditional steps, not commands executed by this task. Do not mark M2 accepted or eligible from this draft.
