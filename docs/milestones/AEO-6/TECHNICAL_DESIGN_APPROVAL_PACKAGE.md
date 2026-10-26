# AEO-6 formal technical design approval checkpoint

Status: **AWAITING_DESIGN_APPROVAL**. Formal design preparation and validation passed. Human design approval is pending. AEO-6B through AEO-6G have not begun.

| Identity | Persisted value |
|---|---|
| Milestone | agrosphere:AEO-6 |
| Approved requirements scope | 48fd59274969f5abf0623159f5d15dba1c00111a80a67a654184ee58be6a2143 |
| Requirements decision | c003c8e6-7477-4c5d-a226-194a5995539e |
| Formal design revision | e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe |
| Design bundle SHA-256 / human approval subject | 0f55432b8e4c4508b27795a92a45537ea63b6e8ae94a001a39250adf2d6d4126 |
| Formal validation ID | e3c6d54b3da94cbd8c5a2805838e5915e4128050bb7021017a7c393d62879bab |
| Validation | Passed; zero errors, one review-limit warning |
| Registered implementation plan SHA-256 | 8ce9d6bd96ef5554bab0ce5d1f7cb0654671fa1eac7cf5f29f5593bdce8e3685 |

## Requirements approval verification

The exact requirements decision is persisted with the exact registered scope, a matching transactional design.human-decision audit event (38), and a Windows SID that remains in the configured approver allowlist. The existing CLI uses WindowsConsoleHumanVerifier and LogonUserW before recording decisions. This workflow stores the authenticated SID and audit event; it does not retain credentials or an independently verifiable authentication receipt. See evidence/requirements-approval-verification.json.

Recomputed scope digest matches; the current requirements-input.json equals the persisted approved input. All 28 context file hashes and repository HEAD references match. The approved requirements, architecture documents, lifecycle, implementation plan and nine diagram sources were preserved.

## Formal validation and repairs

The initial revision 9320bceed9a65e79e7ff3232c61b5e297869938908d397ad31777d5e103edf88 failed validation a9a2b1ff61fd1bf17dd4766764f8b18fc84934e475ece227af69eb7fa8aa3ad5. Both remain in durable history and the exported package. Two existing AEO-1C adapter defects were corrected in src/agrosphere_orchestrator/design_agents.py:

- Internal scope now reads the approved generic service narrative when a repository-specific narrative is absent. An explicitly supplied repository narrative takes precedence; missing sections still fail. Application scope still requires repository-specific narratives.
- Independent review inspects labelled interactions in the authoritative approved PlantUML source when present. Empty diagrams, comments, notes and blank messages still fail, even when unused edge metadata is populated.

The generator and reviewer versions were advanced. These are design preparation fixes; no autonomous controller, runtime migration, scheduler or AEO-6B–6G feature was implemented. Regression tests were added in tests/test_design.py. The focused design suite passed: 65 tests, exit 0. The original source is archived in evidence/design_agents.before.py.txt. Approved context does not include design_agents.py or test_design.py; every approved context hash was rechecked after these edits.

Formal validation covers required document sections and completeness, source/content and on-disk hashes, repository ownership and generating roles, exact revision paths and cross-references, approved diagram source identity and SVG presence, acceptance criteria narratives and requirements references, and independent declared-scope/interaction review. All 22 artifacts passed. The independent reviewer is rule based, not a model or a human approval; the review-limit warning is retained for authenticated human conceptual review.

## Registered implementation plan

REGISTERED_IMPLEMENTATION_PLAN.json exports the exact plan held in the approved DesignScope and the linked DesignRevision. Tasks: controller -> lifecycle -> agents -> quality-delivery -> cli-report -> verification. All belong to agrosphere-orchestrator. The plan has not been imported as executable runtime tasks. No implementation-ready transition or execution authorization was performed.

## Review package and next action

TECHNICAL_DESIGN_APPROVAL_PACKAGE.json contains the persisted revision payload, complete artifact contents and hashes, requirements linkage, implementation plan, review status and validation history. REVIEW_PACKAGE.json is the current CLI-compatible status export. The existing milestone export-docs workflow successfully exported the revision under revisions/e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe/.

Review business.md, architecture.md, service.md, overview.md and diagrams in that revision, plus the linked registered plan. Authenticate in an interactive Windows PowerShell terminal:

~~~powershell
Set-Location C:\Projects\agrosphere\agrosphere-orchestrator
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-design AEO-6
~~~

The exact phrase displayed by the CLI should be:

~~~text
APPROVED agrosphere:AEO-6:design:0f55432b8e4c4508b27795a92a45537ea63b6e8ae94a001a39250adf2d6d4126
~~~

After completing human approval, verify its persisted exact revision, validation, bundle, currently authorized identity and matching audit event with this read-only command:

~~~powershell
Set-Location C:\Projects\agrosphere\agrosphere-orchestrator
.\.venv\Scripts\python.exe docs\milestones\AEO-6\evidence\verify_design_checkpoint.py --require-approval
~~~

Success exits 0 and reports design_approval_persisted: true with the decision ID. Missing approval, changed context/artifacts or mismatched revision fails closed. The existing status command also displays persisted decisions:

~~~powershell
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone design-status AEO-6
~~~

No approval command was run by the agent. No decision was inserted directly. No application repository writes, model calls, remote publication, PRs, merge or deployment occurred. AEO-5 remains separately unfinished. AEO-6 simulation, live Codex and live GitHub evidence remain NOT RUN.

## Verification command guard

Before human approval, verify_design_checkpoint.py --require-approval was executed and exited 1 with PermissionError: Authorized human design approval is required. This confirms the verifier does not treat successful validation as human approval. A supplemental traceability check verified all 12 approved acceptance criteria appear verbatim in business.md and map to at least one registered implementation task; the complete matrix is included in the JSON package.

## Standard validation and implementation boundary

Standard validator: exit 0; all 18 commands passed. Pytest: 293 tests, 0 failures/errors/skips. All 275 accepted baseline test IDs preserved; 18 added cases cover existing AEO-1C preparation defects. Tests/migrations used a disposable SQLite backup and temporary Git repositories. Runtime remains schema 0007, AEO-5 IMPLEMENTING, no AEO-6 executable plan/tasks or execution/delivery activity.
