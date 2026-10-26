# Approval required before AEO-5 implementation

Current registered scope: **56d8808b4578f16347616e27876d2c53ca772156bf4fb4d9ba5a6376a338537a**.

Status: requirements registered, unapproved; state DISCOVERED; no design revision and no authenticated decisions. All six draft diagrams render locally, and the DesignInput/context checks pass. These checks are not formal AEO-1C design validation or approval.

The original AEO-5 specification section 3 requires the existing AEO-1C documentation approval workflow and says not to proceed with pending/denied approval. AEO-5R section 4 preserves that requirement. Actual design.generate_design rejects this scope with Authorized human requirements approval is required. Settings.design_approvers is empty, and design.decide rejects an empty allowlist. This is a project/user-request gate, not an automatic sandbox approval rejection.

## Review and record the first required decision

Review [the architecture](02-architecture.md), [security/approvals](04-security-and-approvals.md), [implementation plan](05-implementation-plan.md), [acceptance matrix](06-acceptance-criteria.md), [recovery findings](IMPLEMENTATION_RECOVERY.md), the preserved user specifications, and diagrams/. REVIEW_PACKAGE.json identifies review files by SHA-256.

From an interactive Windows terminal in the orchestrator root:

~~~powershell
# A trusted administrator must first configure AEO_DESIGN_APPROVERS with
# the actual authorized canonical Windows SID identities. Existing policy
# deliberately does not choose or enroll an approver automatically.
# whoami /user can identify your SID; that alone is not enrollment/approval.
$env:AEO_REPOSITORY_MANIFEST = (Resolve-Path 'docs/milestones/AEO-5/design-repositories.json').Path
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone docs AEO-5
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-requirements AEO-5
~~~

The CLI asks for exact subject confirmation and Windows authentication locally. Do not send passwords or credentials through chat. A requirements approval is not a publishing authorization and does not enable GitHub writes.

## Remaining design-stage prerequisite

Before using the normal generator, the internal-orchestrator ownership extension described in IMPLEMENTATION_RECOVERY.md and 02-architecture.md must be implemented and tested under the reviewed prerequisite scope. The existing generic generator would direct architecture documents into the sibling architecture repository, which is prohibited by this milestone. Do not run it as a workaround. A subsequent formal design revision must pass validation and receive authenticated approve-design before the delivery implementation begins. Any material scope change requires a fresh digest review.

Independent work completed while waiting: recovery inspection/evidence, twelve-capability inventory, draft technical/security/workflow designs, six editable and locally rendered diagrams, hash-bound requirements/context registration, test matrix, and an established regression/quality validator run with preserved prior evidence. No delivery production code, migration, CLI feature or GitHub mutation was made. AEO-5 remains NOT ACCEPTED.
