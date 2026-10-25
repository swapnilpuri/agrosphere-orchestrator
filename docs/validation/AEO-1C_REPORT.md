# AEO-1C completion and validation report

Delivered: mandatory documentation-first lifecycle and deterministic offline integration seams.
Executed validation: 2026-10-24T23:36:54.014513+00:00. All 12 required validation commands returned exit 0.
No application milestone requirements/design were invented, approved or implemented. No sibling
application repository was modified, and no Git commit, push, live model or AEO-2 adapter ran.

## 1. Existing components reused

- MilestoneSpec/TaskSpec for the exact proposed implementation scope and acceptance criteria.
- Settings, strict Pydantic models, safe YAML, repository manifest and confirmed Git inspection.
- Existing role registry: BA, solution architect and writer; separate architect review task.
- SQLAlchemy sessions, Alembic, transactional audit and append-only history conventions.
- Typer JSON-output/error patterns; existing plan, task-approval and recovery services.
- Existing validation runner and temporary-database/Git-repository fixtures.

No orchestration project was recreated. No imported plan is rewritten or automatically approved.

## 2. New components implemented

Design input/requirement/context/diagram contracts; immutable artifact revisions/manifests;
repository-owned publication; serial documentation adapters; separate architecture-review
interface/task; deterministic quality gates; authenticated requirement/design/delivery decisions;
implementation gates; as-built reconciliation; CLI review packages and publication recovery.

Migration 0003 adds design_cases, design_scopes, design_revisions, design_validations and
design_decisions. Scope/revision/validation/decision UPDATE and DELETE operations are rejected
by SQLite triggers. Cases hold mutable current pointers; all state/audit writes share transactions.
A current validation pointer handles pass/fail/revalidation without duplicating historical rows.

## 3. Updated project structure

~~~text
src/agrosphere_orchestrator/
  design_models.py       typed input, artifact and lifecycle contracts
  design_agents.py       approved-input templates and independent review seam
  design_artifacts.py    safe immutable paths and PlantUML/SVG adapter
  design_validation.py   deterministic quality and repository-context gates
  design.py              persistence, lifecycle, review package and task-start guards
  human_approval.py      interactive Windows authentication boundary
  cli.py                milestone group; original commands preserved
migrations/versions/0003_design.py
scripts/verify_design_upgrade.py
scripts/verify_design_tools.py
tests/test_design.py
docs/design-workflow.md
docs/diagrams/design-lifecycle.puml
docs/schemas/design-input.schema.json
docs/schemas/as-built-input.schema.json
docs/validation/design-tools.json
docs/validation/design-upgrade.json
~~~

Existing configuration/policy/readme/state documentation is extended. Role operations add only
document and review-design to the relevant documentation roles; no application code-write grant
or agent concurrency is introduced.

## 4. New state transitions

DISCOVERED -> DESIGN_IN_PROGRESS -> DESIGN_VALIDATING -> AWAITING_DESIGN_APPROVAL ->
DESIGN_APPROVED -> IMPLEMENTATION_READY -> IMPLEMENTING -> IMPLEMENTATION_VALIDATING ->
AWAITING_DELIVERY_APPROVAL -> COMPLETED.

Design validation failures and human rejection return to DESIGN_IN_PROGRESS. New scope/tool/
generator versions cannot inherit approval. Delivery rejection returns to
IMPLEMENTATION_VALIDATING. Original task states remain intact; the central transition service
adds the design gate before new implementation starts. Existing read-only tasks remain usable.
Existing records without a design case are DISCOVERED and cannot start new implementation.

## 5. Documentation templates

Templates require business context/problem/objectives/stories/requirements/criteria; architecture,
services, boundaries, APIs/events, data, security, decisions, trade-offs, integration and risks;
writer overview, rationale, platform fit, responsibilities, sequence, outcomes and user docs;
service-specific technical/domain/interface/persistence/security/developer design; contract
proposals/compatibility; and separate as-built notes/ADRs/limitations/validation evidence.

Default adapters render approved narrative input verbatim. Missing material is explicitly
flagged and blocks validation. Structured scope references are checked against actual confirmed
Git repositories, current file hashes and HEADs. Requirement registration alone grants no approval.
No current application milestone input was supplied; live design case count after migration is
0. AEO-1B reports are evidence, not approved requirements.

## 6. Diagram generation support

Nine selectable PlantUML families: C4 system context, container, component; sequence; domain/class;
activity; state; data flow; deployment. Explicit scope/rationale selects useful diagrams instead
of generating every family. Activity support is currently linear. C4 uses bundled standard-library
includes; no network includes or downloads occur.

The local adapter performs syntax checking and SVG rendering with bounded subprocess calls.
Source and successful SVG files have exact manifest hashes. Tool availability was actually checked
at 2026-10-24T23:36:53.670693+00:00: Java is available, but AEO_PLANTUML_JAR is not configured.
No SVG render or real PlantUML grammar pass is claimed. The recorded plantuml-unavailable error
blocks design approval. The availability probe exits 0 because it successfully records the missing
tool; that exit code does not mean rendering passed. Configured renderer failures return nonzero.

## 7. Validation and approval workflow

The milestone CLI provides design, docs, validate-design, design-status and approve-design;
additional commands approve-requirements, implementation-ready, implementation-complete,
reconcile-docs, approve-delivery and export-docs complete the guarded workflow.

Required document/section presence, unresolved placeholders, requirement/milestone/scope tracing,
diagram source/SVG, owner/role consistency, links, version/path/hash consistency and approval state
are deterministic gates. Proposed contracts receive structural checks; full contract semantic
validation is not claimed. Independent rule review checks declared scope/interactions and records
its conceptual limits. Human architectural judgment remains required.

The review package includes summary, scope/criteria, architecture, document/diagram paths,
technical decisions, risks, affected repositories, proposed tasks and exact revisions. Human
approval requires an interactive terminal, exact digest confirmation, Windows password login
and a configured canonical SID allowlist. A claimed --actor, YAML approved flag or noninteractive
agent invocation cannot approve. Default allowlist is empty. Live credential authentication is
not exercised unattended; tests inject explicitly marked fake verifiers.

Approval binds exact scope, revision/bundle digest and validation outcome. Context is rechecked
during generation, validation, human artifact decision and initial implementation start; changes
during review block approval. Current SID authorization is rechecked before implementation.
The original task-operation approval remains required. Approved documents and scopes are immutable
versions; changes require a new revision/review. Local administrators/code/database owners remain
trusted, as in AEO-1. Other operating systems/PIN-only identities need an additional auth adapter.

Canonical documents live under docs/milestones/<id>/revisions/<revision> in architecture, contracts
or the relevant service owner. The orchestrator stores archival bytes, manifests, task/review state,
validation and approval history. Publication never replaces released documents/contracts or
business code. Per-file atomic hard-link publication prevents partial files and requires local
filesystem hard-link support. Durable export can repair missing outputs after interruption, while
refusing to overwrite changed existing versions.

As-built documentation uses a separate revision after all implementation tasks succeed. Architect
and writer reconciliation, deterministic validation and authenticated delivery approval are required
before COMPLETED. The original approved design and all decisions remain preserved. Task success
still represents foundation bookkeeping; no application tests or implementation are run here.

## 8. Executed validation and preservation evidence

The project virtual environment uses Python 3.14.2. Required scripts/validate.py returned exit 0:

| Check | Exit | Actual result |
|---|---:|---|
| Pytest/JUnit | 0 | 82 passed, no skips |
| Ruff lint | 0 | All checks passed |
| Ruff formatting | 0 | All 56 Python files formatted |
| pip check | 0 | No broken requirements |
| Alembic upgrade/check | 0 | Revision 0003, no schema drift |
| Legacy status/inspection/plan CLI | 0 | AEO-1 functionality operational |
| Design-status CLI | 0 | Missing requirements reported as DISCOVERED; no case/approval created |
| Diagram availability probe | 0 | Missing renderer recorded as an approval-blocking error |
| Dependency inventory | 0 | Installed versions recorded |

Full per-command argv/stdout/stderr/exit codes are in [commands.json](commands.json), and
case results are in [pytest.xml](pytest.xml). Coverage includes correct ownership, missing docs,
invalid PlantUML, missing/stale requirements, source changes during review, both implementation
gates, rejection, approved-version preservation, modified files, idempotence, proposal ownership,
independent review failure, scope mismatch, interruption repair, atomic publication, revalidation,
and foundation/recovery regression behavior. All design integration tests use temporary Git roots
and mocked agent/renderer/identity outputs. No application repository is used for generated test docs.

The live migration preservation probe returned exit 0 at 2026-10-24T23:33:34.800327+00:00. All existing
foundation/recovery table counts and SHA256 digests matched before/after migration; see
[design-upgrade.json](design-upgrade.json). Populated legacy data preservation is separately tested
with temporary databases. No design approvals were added to the live database.

Intermediate checks found one legacy test expecting operation approval to bypass design approval,
and missing imports in newly added tests. Those were corrected, with retry/rollback behavior now
covered under the new gate. A formatting check caught final additions; formatting and the entire
required validation script were rerun successfully. An initial exploratory Git/tool command was
interrupted (exit 1); subsequent Git inspection disabled fsmonitor and completed. No unresolved
test/static-analysis failure remains. Renderer unavailability is an explicit operational finding.

## 9. Remaining live Codex integration work

DocumentationAgents, ArchitectureReviewer, DiagramRenderer and HumanVerifier are modular seams.
The default author is an approved-input template adapter and the independent review adapter is
rule-based, not a live LLM. AEO-2 still needs protected identity/configuration, isolated workspaces,
trusted renderer provisioning, typed live execution/results, budget/cancellation/redaction rules,
authenticated task approval and opt-in live integration tests. Existing AgentExecutor and
CodexWorkspace protocols remain unimplemented. No credentials/model packages were added.

## 10. Impact on upcoming AEO milestones

The documentation lifecycle and implementation gate are ready for approved input and configured
rendering/identity. Real application milestones remain blocked until their requirements are
reviewed, documentation is generated/validated, and the exact design is approved by an authorized
human. Configure a trusted PlantUML JAR and SID allowlist before attempting live design approval.
No autonomous application work, delivery approval or AEO-2 work is implied by this release.

See [operator workflow](../design-workflow.md) for exact input contracts, commands and limits.
