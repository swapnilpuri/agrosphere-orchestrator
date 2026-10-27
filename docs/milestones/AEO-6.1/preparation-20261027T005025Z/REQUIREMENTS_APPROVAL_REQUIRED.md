# Authenticated requirements approval required

Case: **agrosphere:AEO-6-ADJUDICATION** (AEO-6.1 stabilization label). Registered state: DISCOVERED; requirements decision absent. The user request authorized preparation and registration, not approval. Existing guard: Authorized human requirements approval is required.

Registered scope SHA-256: `8367e71ff015366e5c2493c11d199f3d9f7f3ad7bde902f385d10b6a5db96138`.

## Review these artifacts

- [Exact registered requirements input](requirements-input.json): twelve obligations with acceptance clauses, nineteen source/context hashes and proposed internal narratives/diagrams.
- [Existing-capability and boundary assessment](01-capability-and-boundary-assessment.md).
- [Existing workflow review output](evidence/registered-requirements-review.json).
- [Proposal lineage](evidence/proposal-lineage.json): original unregistered proposal preserved.
- [Operations guide](AUTONOMOUS_OPERATIONS_GUIDE.md) and [Milestone 2 draft decisions](MILESTONE_2_PREPARATION_DRAFT.md). The M2 draft is unregistered and grants no product or implementation approval.
- Existing 1B forensic report, matrix, decision package and recovery verification under AEO-6/evidence/discovery-reconciliation are hash-bound context; no old record was rewritten.

The authorized Windows design SID currently configured is `sid:S-1-5-21-1295115365-4060518610-348779417-1001`. A role title or chat reply is insufficient. The existing verifier requires an interactive console, the exact displayed phrase and Windows credentials resolving to an authorized SID. Enter credentials only in that local interactive prompt; never put a password in a command, environment variable, artifact or chat. No authentication was attempted by this task.

## Exact existing operator commands

~~~powershell
Set-Location C:\Projects\agrosphere\agrosphere-orchestrator
$env:AEO_DATABASE_URL = 'sqlite:///C:/Projects/agrosphere/agrosphere-orchestrator/aeo.db'
$env:AEO_REPOSITORY_MANIFEST = 'C:\Projects\agrosphere\agrosphere-orchestrator\config\repositories.yaml'
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone docs AEO-6-ADJUDICATION
.\.venv\Scripts\python.exe -m agrosphere_orchestrator.cli milestone approve-requirements AEO-6-ADJUDICATION
~~~

Exact approval confirmation phrase expected by the current verifier:

~~~text
APPROVED agrosphere:AEO-6-ADJUDICATION:requirements:8367e71ff015366e5c2493c11d199f3d9f7f3ad7bde902f385d10b6a5db96138
~~~

To reject instead, use the same approve-requirements command with --reject; the verifier presents the corresponding REJECTED subject. No agent actor flag or direct SQLite write is supported.

After approval, technical-design generation/rendering/validation and its separate authenticated design approval remain required, followed by existing implementation authorization. This package does not claim a generated/validated technical revision. Configure the verified renderer for that future step. Evidence-decision implementation and a separately authenticated 1B disposition must follow the approved design; no current CLI can record that disposition. Governance allowlist is empty and must not be silently replaced with the design allowlist.

The original autonomous run is still BLOCKED/discovery-conflict, with an expired immutable deadline. Do not resume or recreate it. Neither requirements approval nor 1B reconciliation grants M2 eligibility or a budget extension.
