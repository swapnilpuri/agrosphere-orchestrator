# Milestone 1B recovery verification

Outcome: **REQUIRES_AUTHENTICATED_HUMAN_DECISION**. This task performed read-only runtime verification and created review artifacts only.

| Check actually executed | Result |
|---|---|
| Fresh manifest-bound discovery, twice | Exactly 12 application roots; identical content fingerprint excluding observation time |
| Discovery consistency | false; conflicts=[1B] |
| 1B state | PARTIAL; verified_acceptance_criteria=[] |
| Existing autonomous.validate | valid=true; BLOCKED; discovery-conflict |
| Before/after complete run report | Identical |
| Before/after SQLite file hash and every table content/count | Identical; includes snapshots, approvals, events and run state |
| Tracked report/source/test Git blob comparison | All inspected tracked files match HEAD under Git filters |
| Retained Spatial JUnit parsing | 31 historical tests, zero failure/error/skip; no suite timestamps or authenticated source revision binding |
| Source modifications | None |
| Test suites executed this task | None; prior 367 full-suite/15 focused passes were not rerun |
| Resume / recover / reconcile / approval mutation | None executed |

Exact observations, source hashes, DB/table fingerprints, imported module paths and full repository IDs: [read-only-verification.json](read-only-verification.json). Local Git command exit codes (including expected nonzero probes for ignored/untracked files) are in [git-command-results.json](git-command-results.json). Initial failed collection query and its correction are recorded in collection-attempts.json. Source unchanged means regression implementation tests are deferred until the proposed capability is authorized.

## Decision boundary

Recommended disposition is non-conflicting historical observation: the 1A checkpoint did not start 1B; separately scoped 1B implementation exists. No authenticated evidence-decision workflow currently represents this relationship. Neither generic architecture-change approval nor a descriptive adjudications dictionary authorizes a recovery conflict override. No evidence-disposition decision was recorded; no current acceptance was asserted.

The authorized role for this new disposition is not currently defined. A governed change must define it using the existing verified governance SID allowlist and authenticated verifier. Exact requirements/design change approval belongs to the existing configured design-approver SID; the role registry alone grants no authority. The agent cannot supply that identity or create a decision.

## Concrete next operator action

Review the forensic report, matrix and decision package, then the separate internal change requirements draft. This draft is PROPOSED, UNREGISTERED and UNAPPROVED. Existing AEO-6 scope is immutable while IMPLEMENTING, so register the separate proposed change milestone only if the operator accepts the review scope. This is a design case, not another autonomous run. The following are existing CLI operations, provided for future operator use and not executed here:

~~~powershell
Set-Location C:\Projects\agrosphere\agrosphere-orchestrator
$env:AEO_DATABASE_URL = 'sqlite:///C:/Projects/agrosphere/agrosphere-orchestrator/aeo.db'
$env:AEO_WORKSPACE_ROOT = 'C:\Projects\agrosphere'
try {
$env:AEO_REPOSITORY_MANIFEST = 'C:\Projects\agrosphere\agrosphere-orchestrator\docs\milestones\AEO-6\evidence\discovery-reconciliation\milestone-1b-adjudication-20261026T061544Z\design-repositories-proposed.json'
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone design AEO-6-ADJUDICATION --requirements 'docs/milestones/AEO-6/evidence/discovery-reconciliation/AEO-6-ADJUDICATION.requirements-proposed.json'
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone docs AEO-6-ADJUDICATION
# After exact scope review, an authorized human uses the interactive verifier:
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-requirements AEO-6-ADJUDICATION
} finally {
    $env:AEO_REPOSITORY_MANIFEST = 'C:\Projects\agrosphere\agrosphere-orchestrator\config\repositories.yaml'
}
~~~

Requirements approval would authorize technical-design preparation, not evidence adjudication or implementation. Generate/validate/render the exact design, then obtain authenticated approve-design and satisfy implementation-ready before any source change. Configure a verified PlantUML renderer for that future workflow. The proposed adjudication request/decision CLI does not exist and no hypothetical command is presented as executable. After a capability is approved and implemented, its actual approved path would record the specific evidence decision. Do not reuse the internal manifest for application discovery; use config/repositories.yaml for the exact 12 application roots. Do not resume the autonomous run as part of this review.

## Planned tests after authorization (not executed)

1. Proven checkpoint progression can affect only its bound conflict after a valid authenticated decision.
2. Genuine unresolved current contradictions remain blocking.
3. Original versus quoted/fixture/out-of-scope evidence is distinguished and preserved.
4. Missing commit/blob/timestamp or ambiguous scope fails closed.
5. Newer but lower-authority history cannot override a scoped authoritative assertion.
6. Adjudication never marks acceptance/completion, satisfies dependencies, or grants execution.
7. Repeated decision/recovery is idempotent; every required audit event is transactional.
8. Existing run ID/request/counters/history/approvals and old snapshots remain unchanged.
9. Discovery remains bound to exactly the approved 12 application roots; manifest digest changes invalidate the subject.
10. Wrong SID, agent self-approval, stale subject, rejection, revocation, expiry and decision replay all fail closed.

Run the applicable focused suites and scripts/validate.py only after authorized source implementation. The present repeated read-only observation check is not a test of a missing decision capability.

## Independent Milestone 2 blockers

Fresh design-status is DISCOVERED/missing-requirements: no approved Milestone 2 scope. The existing request carries no requirements/task options. Approved requirements, exact design, plan/dependencies bound to an approved roadmap, execution grants and independent quality/acceptance evidence remain prerequisites. The architecture assessment leaves named-device rendering/frame and reproducible useful-estate-view timing unverified; no performance work was performed. Historical functional delivery is not current acceptance. The immutable run deadline/counters remain unchanged and may independently pause future continuation; no extension or new run was created. 3B remains outside scope. AEO-6's earlier simulation was mocked and supplies no live-execution proof.

## Proposed requirements verification

The proposed separate internal change input passed DesignInput schema validation and existing verify_context repository/role/hash/HEAD guards (exit 0). No design case was registered and no approval was created. See proposal-validation.json. This is a read-only proposal check, not the regression suite or human authorization.

## Final preservation check

Final verification passed: runtime source hashes unchanged; all prior package hashes unchanged; SQLite file and every table unchanged; 454 application fingerprints across exactly 12 repositories matched. All four required artifacts exist and report links resolve. See final-preservation.json. The operator command block restores the application manifest after the internal-scope review workflow. No commands in that block were executed.
