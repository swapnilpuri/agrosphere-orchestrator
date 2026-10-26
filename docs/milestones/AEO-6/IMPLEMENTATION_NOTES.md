# AEO-6 implementation notes

The original 00–07 requirements/design documents and nine diagram sources remain the approved design baseline. Implementation details below supplement that baseline without replacing it.

## Implemented components

- autonomous_models.py: strict single-milestone request, run limits, result states, approved-roadmap DAG validation and documented recovery categories.
- autonomous_store.py: durable AutonomousRun, immutable AutonomousOperation/AutonomousEvent, transactional audit, complete JSON/Markdown presentation and atomic content-addressed report export.
- autonomous.py: bounded intent/dispatch/observation/commit coordination, serial run ownership, exact-once outcome adoption, explicit pause/resume/recover, conservative elapsed accounting, request integrity, counters and independently observed child usage.
- autonomous_services.py: manifest-bound AEO-1B discovery; AEO-1C scope/generation/validation/export and exact approval checks; existing plan import and scheduler planning; authenticated execution checkpoints; independent AEO-4 quality and bounded remediation; existing AEO-5 planning/observation/publication guards.
- autonomous_cli.py: plan/start/status/pause/resume/recover/report/validate/simulate. Default start is read-only even if the request file says local; the CLI requires an explicit mode.
- autonomous_simulation.py: isolated three-repository fixture with real lifecycle services, fixture-only authentication, injected model/scanner/provider/renderer ports, one isolated write worktree, failed quality plus one bounded repair, restart reconstruction and mock delivery. Fixture authentication cannot target the runtime DB.
- 0008_autonomous.py: three additive tables; append-only operation/event history; immutable run request/identity; destructive downgrade refused.

Existing TaskScheduler.execute_ready_tasks gained optional dispatch_guard and max_batch_size arguments. Reservations share its claim/lease transaction, so rejection rolls back both claims and budgets before model dispatch. Existing quality.prepare_remediation gained an optional per-task reservation_guard in its own mutation transaction. Default existing callers retain their behavior. Settings remain centralized; standard validation exports the new request/limit schemas.

## Important operational semantics

Application execution requires a configured roadmap whose bytes are bound to the selected requirements context. Unknown, cyclic, duplicate or unverified dependencies block. An explicit milestone, mode or model response supplies no authority. Numeric recovery suggestions are displayed as review recommendations only.

A run is immutable and bounded to one milestone. Resume retains cumulative counters, reservations and elapsed history. Configured limits cap requested limits. Unknown monetary cost prevents dispatch when a monetary cap is requested. Model invocations and attempts are reserved before dispatch, unique tasks are capped, scheduler concurrency is capped, repairs reserve each affected task, approved child/validator timeouts must fit the remaining deadline, and observation calls consume retained polling reservations. Existing provider/process/worktree implementations keep their own safeguards.

BLOCKED identifies missing configuration, invalid design, failed quality or dependencies; AWAITING_APPROVAL identifies genuine human authorization checkpoints; RECOVERY_REQUIRED retains uncertain child ownership; PAUSED retains operator/budget state. REPORTED is a run outcome and never asserts formal milestone completion. No automatic merge/deploy/next-milestone operation exists.

Planning, design preparation and observation complete authorized preparation before presenting human decisions. Resume rechecks the current authorized identity, exact scope, design artifacts, scheduling plan, quality and child grants. Changed approved requirements are not silently registered by the controller. Later delivery manifest/grant references may be bound through explicit resume; the manifest becomes immutable and all actual grants are verified by AEO-5.

The controller never calls a human verifier or records human decisions. Only the opt-in isolated simulation invokes its fixture verifier against its disposable database. Live proof-of-concept/model execution and real application runs still require the separate explicit authorization specified in the original design.

## Recovery evidence scope

The test suite covers conservative ownership/adoption behavior for all 16 documented recovery categories, plus injected faults after intent, before dispatch, after observation, before commit and after commit. Specific integration tests exercise actual scheduler rollback/concurrency, AEO-4 repair transaction rollback, roadmap integrity, approved artifact/identity enforcement through existing regression tests, additive migration preservation, and end-to-end restart/repair/delivery. Existing AEO-5 response-loss, external SHA/CI/review and worktree tests remain authoritative for child recovery; the controller delegates to them and never implements publication replay.

## Evidence limitations

The isolated simulation uses mock Codex, validation, GitHub and renderer ports. It is not live model, scanner, GitHub or production acceptance evidence. Actual AEO-6 design diagrams were rendered and validated separately at the approved design checkpoint. Runtime AEO-6 remains IMPLEMENTING unless actual existing lifecycle services verify subsequent tasks and delivery; manual development does not fabricate those records. AEO-5 remains separate.
