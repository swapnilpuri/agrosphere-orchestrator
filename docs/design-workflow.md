# AEO-1C documentation-first workflow

AEO-1C extends the synchronous, single-writer foundation. No model, Codex adapter,
application implementation, automatic Git write, network include or deployment is invoked.
Existing imported plans, task states, task approvals and recovery observations retain their
schema and semantics. Migration 0003 adds design state alongside those records. A legacy
milestone without a design case is DISCOVERED with a missing-requirements finding; it is
never grandfathered into design approval. Existing running tasks can finish; new implementation
task starts require the new gate in addition to the original operation approval.

## Operator workflow

Run from the orchestrator root with its virtual environment and migrate first:

~~~powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\aeo.exe milestone design AGRO-M3C --requirements reviewed-input.yaml
.\.venv\Scripts\aeo.exe milestone docs AGRO-M3C
.\.venv\Scripts\aeo.exe milestone approve-requirements AGRO-M3C
.\.venv\Scripts\aeo.exe milestone design AGRO-M3C
.\.venv\Scripts\aeo.exe milestone validate-design AGRO-M3C
.\.venv\Scripts\aeo.exe milestone design-status AGRO-M3C
.\.venv\Scripts\aeo.exe milestone approve-design AGRO-M3C
.\.venv\Scripts\aeo.exe milestone implementation-ready AGRO-M3C
~~~

AGRO-M3C is only an example identifier. No requirements for it are supplied or invented by
this release. The first command registers a proposed input scope without approving it or
creating an application plan. Generation without human-approved requirements fails closed.
The existing import_plan service must import the exact approved MilestoneSpec before readiness;
content conflicts retain the foundation rejection behavior. Readiness and task RUNNING are
bookkeeping only. AEO-2 must implement a separately approved execution adapter.

The --project option defaults to agrosphere and scopes every command. Status/docs are read-only
and show the summary, requirements and acceptance criteria, architecture, decisions, risks,
affected repositories, proposed tasks, document/diagram paths, manifests, validation findings,
exact bundle digest, review decisions and revision history. All CLI results are JSON.
Use approve-design --reject to return a validated design to DESIGN_IN_PROGRESS.
A rejection is append-only history. New input or generator/tool revisions require new review;
regeneration never erases a decision or marks anything approved.

After all implementation tasks have succeeded, run:

~~~powershell
.\.venv\Scripts\aeo.exe milestone implementation-complete AGRO-M3C
.\.venv\Scripts\aeo.exe milestone reconcile-docs AGRO-M3C --as-built actual-results.yaml
.\.venv\Scripts\aeo.exe milestone validate-design AGRO-M3C
.\.venv\Scripts\aeo.exe milestone approve-delivery AGRO-M3C
~~~

A separate as-built revision requires architect and writer outputs, current hashed context,
as-built diagrams, service documentation, contracts when affected, implementation notes,
relevant ADRs, known limitations and validation evidence. It cannot replace the original
approved design. Delivery rejection returns to IMPLEMENTATION_VALIDATING. Only authenticated
delivery approval advances to COMPLETED. Task success is the existing bookkeeping state;
AEO-1C does not execute or independently attest application tests.

## Inputs and templates

Generated schemas are docs/schemas/design-input.schema.json and as-built-input.schema.json.
Inputs are safely loaded YAML and reject unknown fields. DesignInput contains an existing
MilestoneSpec, uniquely identified requirements with acceptance criteria, verified repository
context references (repository, relative path, raw file SHA256 and current Git HEAD), approved
narratives, explicit diagram specifications/rationales and optional versioned contract proposals.
A YAML approved flag or a claimed actor name is not accepted as requirements approval.

Narrative keys are business, architecture, overview, service:<repository>, contracts and
as-built. The required section templates live in design_agents.SECTIONS:

- Business: context, problem, objectives, stories, functional/nonfunctional requirements and criteria.
- Architecture: overview, services, DDD boundaries, API/events, database changes, security,
  technologies, trade-offs, risks, decisions and integration design.
- Overview: what/why, platform fit, component responsibilities, sequence, outcomes and user docs.
- Service: technical design, domain model, interfaces, persistence, security and developer docs.
- Contracts: proposed APIs/events and compatibility analysis.
- As-built: actual architecture, APIs/events, technical design, ADRs, notes, limits and evidence.

The default adapters render approved inputs verbatim. They do not infer business scope from
file names or recovered milestone completion reports. Missing narratives remain MISSING
placeholders with error findings; no generic prose is inserted to make a gate pass. Context
must belong to actual confirmed Git roots with matching hashes/HEADs, and is rechecked before
generation and initial implementation readiness/start. Once implementation begins, legitimate
source changes do not rewrite the historical approved context. Artifact integrity remains enforced.

## Repository ownership and immutable artifacts

Canonical files use docs/milestones/<milestone>/revisions/<revision-id>/ inside their owner:

| Owner | Documents |
|---|---|
| agrosphere-architecture | Business requirements, overview, architecture/ADR/integration/implementation-plan sections, cross-service diagrams and as-built architecture |
| agrosphere-contracts | Compatibility design and versioned proposed OpenAPI/event schemas |
| Scoped service repository | Technical design, domain models, service diagrams and developer docs |
| agrosphere-orchestrator | Lifecycle/task state, manifests, validation, audit and human decisions |

Input context and documentation ownership are verified against the existing repository manifest.
Only new immutable documentation paths can be published; business source, existing architecture
documents and released contracts are never replaced by generation. Proposed contracts remain
under the revision proposal directory, never overwrite published OpenAPI/event files, and have
structural checks rather than a claim of full OpenAPI/JSON-Schema semantic validation.

Cross-document links use aeo://<repository>/<relative-path> as logical references, resolved to
absolute local paths in the review manifest. They are reference identifiers, not installed browser
protocol handlers. The deterministic gate rejects unresolved references. The database retains
archival bytes for integrity/republication; published repository files remain the canonical
review documents. It does not create a competing live document in another repository.

Content hashes, owning repository/path, source requirements, generating role, timestamp,
validation and approval references are persisted. Approved version is the immutable revision ID;
Git commits are not required or created. Scopes, revisions, validations and decisions have SQLite
UPDATE/DELETE guards. Mutable case pointers choose the current scope/revision/validation. Each
state change and its audit events share a transaction. Unchanged generation inputs/adapters/tools
reuse a revision; changed versions create a new revision and cannot inherit design approval.

Publication persists the revision before writing files and publishes each complete file using
an atomic hard link from a temporary file in the same directory. This requires local filesystem
hard-link support (NTFS is the exercised target). Existing differing files are preserved and cause
an error. After interruption, milestone export-docs AGRO-M3C republishes missing files from the
durable revision; it refuses to overwrite a changed version. It does not delete orphaned files.

## Diagram support and deterministic quality gates

Explicit scope/rationale selects diagrams rather than generating all nine families. Supported
specifications cover C4 context/container/component, sequence, domain/class, activity, state,
data-flow and deployment. Activity generation currently supports linear workflows; branching
requires a reviewed adapter. C4 sources use bundled C4-PlantUML standard-library includes.
No network download or remote include is performed.

Set AEO_PLANTUML_JAR to a trusted local PlantUML JAR with its bundled C4 library and
AEO_JAVA_EXECUTABLE if java is not on PATH. The renderer runs fixed argument arrays, sandboxed
PlantUML, bounded subprocess timeouts, a syntax check and SVG rendering. External/custom
includes and dynamic input directives are rejected. Source .puml and successful .svg outputs
are immutable manifest entries. Missing tools, syntax errors or failed renders are error
findings that prevent approval. Basic delimiter checks alone never prove rendered validity.
The Java/PlantUML availability probe records real outcomes in docs/validation/design-tools.json.

Deterministic gates check required documents/sections, unresolved placeholders, milestone/scope
and requirement traceability, required diagram source/SVG, owner and generating role, contract
structure, reference resolution, path/revision/hash integrity and human approval state.
The separate RuleBasedArchitectureReviewer executes an independent architect-role task to check
declared scope and interactions. Its limited conceptual review is explicit; experienced human
review remains required. LLM review can later add findings but cannot suppress deterministic errors.

## Human identity and authorization

AEO_DESIGN_APPROVERS is a JSON list of authorized canonical Windows identities, for example
["sid:S-1-5-21-..."]. It defaults to [] and no approvals can occur until an administrator
configures it. A human administrator can find their Windows SID using whoami /user and must
review the allowlist themselves. This release does not automatically populate approvers.

Approval/rejection requires an interactive terminal, exact milestone/kind/digest confirmation,
and Windows username/domain/password authentication via LogonUserW. The authenticated token
SID, not an environment username or --actor, is compared with the allowlist. Passwords and
reusable authentication tokens are never persisted or logged. PIN-only/SSO-only accounts and
non-Windows platforms require a future authentication adapter; they cannot silently fall back
to a claimed actor. Automated tests inject explicit fake verifiers, never real credentials.
Live Windows credential authentication is not exercised by the unattended validation suite.

The current approver allowlist is rechecked at design gates, so removal revokes future starts.
Original task-operation approval is still required. Local code/config/database administrators
remain trusted: arbitrary Python, a malicious verifier adapter or raw SQL is outside this local
application trust boundary. Approval is protected against ordinary agent CLI invocation, not
against a compromised administrator. Configure a protected identity service in AEO-2.

## Lifecycle and integration seams

DISCOVERED -> DESIGN_IN_PROGRESS -> DESIGN_VALIDATING -> AWAITING_DESIGN_APPROVAL ->
DESIGN_APPROVED -> IMPLEMENTATION_READY -> IMPLEMENTING -> IMPLEMENTATION_VALIDATING ->
AWAITING_DELIVERY_APPROVAL -> COMPLETED. Failed design validation/rejection returns to
DESIGN_IN_PROGRESS; delivery rejection returns to IMPLEMENTATION_VALIDATING. New approved
input does not mutate old requirements, artifact content or approval history.
See diagrams/design-lifecycle.puml and design.EDGES for the exact guarded transitions.

DocumentationAgents, ArchitectureReviewer, DiagramRenderer and HumanVerifier are injectable
interfaces. Documentation tasks use the existing three role registrations; document and
review-design operations do not grant application code-write authority. Future Codex integration
needs isolated repository workspaces, typed live result/error contracts, authentication, budgets,
cancellation, redaction, trusted renderer distribution, protected config and opt-in live tests.
The existing AgentExecutor/CodexWorkspace interfaces remain unimplemented. No AEO-2 work starts.


AEO-3 scheduling, handoffs, resource leases, and operator commands are described in [the orchestration guide](aeo-3/README.md).
