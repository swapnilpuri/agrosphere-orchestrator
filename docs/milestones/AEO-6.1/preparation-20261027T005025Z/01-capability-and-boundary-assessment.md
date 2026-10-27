# Existing capabilities and approval boundary

AEO-6.1 is a preparation label for the pending internal change case AEO-6-ADJUDICATION; no new autonomous run is created. Existing AEO-6 remains IMPLEMENTING with its immutable approved scope/revision. The old adjudication proposal was never registered. Current registration is explicitly authorized by the attached request; requirements/design approval is not.

| Obligation | Existing implementation / limitation |
|---|---|
| Durable workflow / restart | autonomous.py and autonomous_store.py preserve operation intent, run identity, history and budgets |
| Fresh collection | ExistingServices.discover directly inspects confirmed manifest roots; recover_milestones retains historical-unresolved 1B |
| Authenticated identity | WindowsConsoleHumanVerifier confirms subject and uses LogonUserW/canonical SID; no credentials stored |
| Requirements/design approval | design.register_requirements, require_approval, generate_design, decide and assert_design_gate; generation requires requirements approval before work |
| Generic governance | quality.request_approval/decide_approval/valid_approval with DesignDecision and GovernanceRecord, scope/expiry/actor checks and transactional audit |
| Missing evidence semantics | ApprovalCategory lacks evidence disposition; no exact original/supporting evidence subject, disposition CLI or classifier consumer. Descriptive adjudications are not authenticated authority |
| Acceptance protection | Recovery PARTIAL and empty verified criteria remain independent of formal completion, roadmap/dependency checks and exact grants |
| Operations | Existing autonomous resume loops eligible work until a checkpoint; no background approval watcher or new service needed for current manual CLI continuation |
| Same-run limit | One-hour immutable deadline is expired; this scope will surface it and will not modify or extend it |

Current configured design SID is sid:S-1-5-21-1295115365-4060518610-348779417-1001. Governance SID allowlist is empty. The role registry is metadata, not an evidence-adjudicator authorization. Local SQLite/config/code administrators remain the established trust boundary; hash-bound subjects plus interactive Windows authentication are not externally signed tamper-proof audit attestations.

## Proposed implementation direction, pending design approval

Extend the existing governance service and decision/audit storage using category-specific evidence context validation. Define explicit approve/reject/unresolved outcomes, original and supporting immutable provenance, affected milestone scope, rationale, policy/version, duplicate handling and current authority checks. Retain old snapshots and assertions. Consume only a valid exact relationship decision in fresh collection; do not erase other conflicts, grant acceptance or change execution authority. Do not add a parallel approval API, database migration, scheduler, provider launcher, watcher or UI.

The twelve clauses in requirements-input.json are the reviewable proposed requirements. Diagrams and narratives inside that input are proposed material, not generated/validated approved technical design. Existing generate_design calls require_approval before generation. This preparation stops at the authenticated requirements boundary; it does not claim Phase 3 or later implementation was authorized.

Milestone 2 preparation is an unregistered draft in MILESTONE_2_PREPARATION_DRAFT.md. Original product scope, frame/time acceptance statistics, reference device and dataset/provider budgets require explicit decisions. Runtime source files, application files and prior evidence stay unchanged.
