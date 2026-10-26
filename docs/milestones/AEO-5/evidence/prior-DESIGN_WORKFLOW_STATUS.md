# AEO-5 formal design workflow status

The existing CLI workflow was executed against approved scope 56d8808b4578f16347616e27876d2c53ca772156bf4fb4d9ba5a6376a338537a, after verifying the requirements decision, current approver authorization, stored scope hash and all stored context hashes.

## Actual outcome

- Design generation: exit 1. Exact error: Activity adapter supports explicit linear workflows only; branching needs a reviewed adapter.
- Design validation: exit 1. Exact error: No design artifacts; approved requirements and generation are required.
- Current state: DESIGN_IN_PROGRESS. A generation-start and failed documentation-task audit are legitimate workflow progress; they are not a completed design revision.
- Design revision ID: none. Validation ID/status: none/not performed. No formal review package exists to approve.
- Requirements scope remains unchanged and approved. No design decision was inserted and no AEO-5 delivery implementation began.

The commands were the existing module CLI: milestone design AEO-5 followed by milestone validate-design AEO-5, with the existing local PlantUML JAR configured for the subprocess. Exact argv, exit codes, output and resulting state are in evidence/formal-design-workflow-attempt-1.json.

## Concrete compatibility gaps

1. design_artifacts.plantuml rejects non-linear activity edges. The approved specifications 05-durable-recovery and 06-approval-quality contain branching edges, so solution-architect generation raises before a DesignRevision is persisted. All six manually authored .puml sources referenced by the approved scope render successfully with the existing trusted LocalPlantUML adapter. Their rendering is not the same as generation/validation of a formal revision.
2. TemplateDocumentationAgents hardcodes business/architecture/overview/as-built into agrosphere-architecture and excludes agrosphere-orchestrator from service technical-design output. This cannot satisfy the explicit internal-orchestrator documentation boundary or create its technical-design document.
3. design_validation.expected_owners excludes the orchestrator from every declared diagram's allowed owners, and deterministic_findings hardcodes required architecture/business/overview owners to the architecture sibling. Removing the activity exception alone would expose these ownership failures; it would not produce a valid design.

The individual diagram/function probes, allowed owners and actual local rendering results are recorded in evidence/formal-design-preflight.json. No ownership rule, required-document check, render requirement, source hash or authenticated approval guard was bypassed.

## Smallest compatible correction

Introduce one narrow internal-orchestrator ownership policy for scopes whose tasks and verified context are exclusively owned by agrosphere-orchestrator, with no contract proposals/impact. Have generation and deterministic required-document/owner validation use the same policy; preserve all existing application-scope defaults. Include the orchestrator's supplied service narrative in technical-design generation. Keep the scope declaration and rejection rules explicit so mixed application scopes cannot redirect cross-service architecture or contracts into the orchestrator.

Use a reviewed DocumentationAgents adapter to consume the six existing scope-hashed approved PlantUML sources, or extend the DiagramSpec activity renderer to faithfully represent its declared branching edges. Do not delete branching edges, relabel activities as a linear flow, remove required diagrams, or skip ownership/render checks to obtain a pass. Bind the selected adapter version into the existing design revision identity, as generate_design already does.

Add tests for internal-only ownership, required technical documents, unchanged application ownership, mixed-scope rejection, branching-diagram fidelity, unchanged requirement authentication, and real rendering. Continue using generate_design/export_revision/validate_design/decide with ordinary immutable revision and decision records; no second approval mechanism or raw SQL record insertion is needed.

The approved context explicitly hashes design_agents.py and design_validation.py (as well as design.py). Editing those files would invalidate this currently approved context. Therefore the correction cannot be silently applied while claiming the same requirements approval remains fresh. Implementing that prerequisite must be accompanied by refreshed context registration and authenticated review of the resulting scope before generation can proceed under the corrected workflow. Existing scope/approval history must be preserved. No production code or approved input was changed in this attempt.

## Authenticated design approval command after successful validation

Run from the orchestrator root only after a genuine revision has passed the existing validation:

    .\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-design AEO-5 --project agrosphere

That command is supported now, but cannot approve the present state because no validated revision exists. The current requirements hash is not a design bundle digest. Once generated, milestone docs AEO-5 presents the actual revision, bundle digest, artifacts and findings for human review. No human credentials or approvals were fabricated, and no remote push, PR, merge, deployment or AEO-6 work occurred.
