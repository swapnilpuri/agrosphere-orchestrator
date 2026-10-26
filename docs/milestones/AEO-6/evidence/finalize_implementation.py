"""Build acceptance exclusively from persisted approval, actual validation and simulation evidence."""
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

root=Path.cwd()
out=root/'docs/milestones/AEO-6'
evidence=out/'evidence'
validation=evidence/'implementation-validation'
runner=json.loads((validation/'runner.json').read_text(encoding='utf-8'))
commands=json.loads((validation/'commands.json').read_text(encoding='utf-8'))
assert runner['exit_code']==0
assert len(commands['commands'])==18 and all(c['exit_code']==0 for c in commands['commands'])
def ids(file):
    return {(c.get('classname'),c.get('name')) for c in ET.parse(file).iter('testcase')}
current=ids(validation/'pytest.xml')
baseline=ids(evidence/'baseline-validation/pytest.xml')
design_baseline=ids(evidence/'design-preparation-validation/pytest.xml')
assert baseline<=current and design_baseline<=current
suite=next(ET.parse(validation/'pytest.xml').iter('testsuite'))
assert all(int(suite.get(key))==0 for key in ('failures','errors','skipped'))
inventory=json.loads((evidence/'implementation-source-manifest.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((root/f['path']).read_bytes()).hexdigest()==f['sha256'] for f in inventory['files'])
simulation=json.loads((evidence/'simulation-final/simulation-report.json').read_text(encoding='utf-8'))
assert simulation['run']['state']=='REPORTED' and simulation['failed_quality_then_repaired']
assert simulation['provider_prs']==simulation['provider_pushes']==3
assert not simulation['real_codex'] and not simulation['live_github'] and not simulation['formal_completion']
linkage=json.loads((evidence/'implementation-approval-linkage.json').read_text(encoding='utf-8'))
assert linkage['requirements_input_unchanged'] and linkage['registered_plan_unchanged'] and linkage['design_approver_authorized']
migration=json.loads((evidence/'runtime-migration-0008.json').read_text(encoding='utf-8'))
assert migration['after_migration']=='0008' and migration['all_preexisting_table_records_preserved']
dry=json.loads((evidence/'autonomous-dry-run.json').read_text(encoding='utf-8-sig'))
prior=json.loads((evidence/'application-discovery.json').read_text(encoding='utf-8'))
old={r['id']:r for r in prior['repositories']}
boundaries=[]
for repo in dry['discovery']['snapshot']['repositories']:
    before=old[repo['id']]
    boundaries.append({'repository':repo['id'],'head_unchanged':before['head']==repo['head'],'git_status_unchanged':before['status']==repo['status'],'file_fingerprints_unchanged':before['file_fingerprints']==repo['file_fingerprints']})
assert len(boundaries)==12 and all(all(r[k] for k in ('head_unchanged','git_status_unchanged','file_fingerprints_unchanged')) for r in boundaries)
summary={'local_acceptance':'ACCEPTED_WITH_EXPLICIT_LIVE_VALIDATION_LIMITS','runtime_state':'IMPLEMENTING','formal_completion':False,'validator_exit_code':0,'standard_checks':18,'pytest':dict(suite.attrib),'accepted_275_test_ids_preserved':True,'design_checkpoint_293_test_ids_preserved':True,'added_since_design_checkpoint':len(current-design_baseline),'source_inventory_verified':True,'source_inventory':inventory['files'],'approval_linkage':{k:v for k,v in linkage.items() if k!='context'},'migration':migration,'simulation':{k:v for k,v in simulation.items() if k not in ('run','restart_checkpoints')},'application_repository_boundaries':boundaries,'application_recommendation':dry['discovery']['recovered_recommendation'],'application_conflicts':dry['discovery']['conflicts'],'actual_codex':'NOT RUN - separate explicit opt-in required','live_github':'NOT RUN - remote writes remain disabled in runtime','automatic_application_run_started':False}
(evidence/'implementation-acceptance-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
(out/'IMPLEMENTATION_INVENTORY.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
count=suite.get('tests')
report=f'''# AEO-6 local implementation acceptance

Status: **LOCALLY ACCEPTED WITH EXPLICIT LIVE VALIDATION LIMITS**. Runtime AEO-6 remains **IMPLEMENTING**; formal milestone completion is false. No real application milestone was launched.

## Actual implementation inventory

Six new modules implement strict run/request/roadmap contracts, durable intent/event persistence, deterministic bounded control, existing-service adapters, the autonomous CLI and isolated simulation. Additive migration 0008 creates autonomous_runs, autonomous_operations and autonomous_events. Narrow existing-service changes add atomic scheduler dispatch reservations/batch caps and per-task AEO-4 repair reservations. Settings, CLI registration, Alembic metadata and standard schema exports are updated. Eight new test modules cover unit, integration, scheduler, security, CLI, quality, recovery and upgrade behavior. Exact 22-file inventory and SHA-256 values are in IMPLEMENTATION_INVENTORY.json and evidence/implementation-source-manifest.json. Existing uncommitted AEO-5 work was retained.

The controller reuses AEO-1 domain/plan persistence; AEO-1B repository collection, recovered milestones and snapshot reconciliation; AEO-1C scope, immutable generation/export/validation and exact approval guards; AEO-2 context/execution/grants/worktree isolation; AEO-3 plan/DAG/claims/leases/handoffs; AEO-4 independent policy/readiness/validation/remediation; AEO-5 immutable delivery planning, publication guards and provider reconciliation. It introduces no alternate model launcher, scheduler, GitHub adapter, queue, service or UI.

## Registered approval and runtime state

Requirements scope: {linkage['scope_id']}

Requirements decision: {linkage['requirements_decision_id']}

Design revision: {linkage['revision_id']}

Design bundle: {linkage['bundle_digest']}

Design validation: {linkage['validation_id']}

Authenticated design decision: {linkage['design_decision_id']}

Current authorized identity, transactional human-decision audit, all 22 immutable approved artifacts and exact imported six-task plan were independently verified. Requirements input is unchanged. Approved context was checked before entering IMPLEMENTING; authorized implementation source edits are recorded separately, following the existing design guard. The requirements and approved design were not silently rewritten.

Runtime schema upgraded 0007 -> 0008 only after the full validator passed. A backup is retained under .aeo/backups; evidence/runtime-migration-0008.json identifies it. All records in every pre-existing table were compared before/after and preserved. Table count increased 29 -> 32. No runtime autonomous run/operation/event records were fabricated. The six manually implemented plan tasks were not falsely marked as executed by Codex. AEO-5 remains IMPLEMENTING and its outstanding runtime delivery is separate.

## Actual validation results

Standard validator: **exit 0; 18/18 checks passed**. Pytest: **{count} tests; zero failures, errors or skips**, {suite.get('time')} seconds. All 275 accepted AEO-5 IDs and all 293 design-checkpoint IDs are preserved; {len(current-design_baseline)} new cases were added after the design checkpoint. The original 163 IDs remain preserved through that accepted baseline. Tests/migration checks ran on a disposable runtime backup and independent temporary Git repositories.

Evidence: evidence/implementation-validation/commands.json, pytest.xml and runner.json. Final source hashes match the inventory captured at the start of that run. The earlier interrupted full run is explicitly recorded in implementation-validation-interrupted.json and is not claimed as passing.

Safety checks include atomic dispatch rollback and concurrency caps through the real scheduler, per-task repair transaction rollback through AEO-4, immutable run/history and report integrity, duplicate-start serialization, retained elapsed/attempt/resource counters, unknown-cost fail-closed behavior, exact timeout bounds, manifest-root isolation, approved-roadmap dependencies, fixture authentication refusing runtime DBs, read-only CLI defaults and additive upgrade preservation.

Recovery tests retain ownership and require independently verified adoption for all 16 documented categories; additional injection covers after-intent, before-dispatch, after-observation, before-commit and after-commit faults. Existing AEO-2–AEO-5 tests verify child process/session, worktree, publication response loss, CI/SHA/review changes and authorization failures. The parent delegates child recovery; no blind write replay is introduced. See IMPLEMENTATION_NOTES.md for evidence scope.

## End-to-end simulated result

The supported simulation CLI exited 0 and exported evidence/simulation-final/simulation-report.json and .md. Three independent temporary Git repositories and a temporary SQLite DB exercised real requirements/design/plan/grant lifecycle services, the real scheduler, an isolated write worktree, all mandatory quality/security gate types for every impacted repository, one failed QA result, one bounded read-only remediation, revalidation, separate fixture-authenticated delivery approval and action grants, three mocked pushes/PRs and controller reconstruction across checkpoints. The run ended REPORTED with formal completion false. Four simulated model calls, one repair and three simulated PRs were observed. Long Windows path cleanup was exercised and fixed without relaxing existing worktree safeguards.

Model, scanner, PlantUML renderer and GitHub ports are explicitly mocked in this simulation. Actual AEO-6 design PlantUML sources/SVGs were rendered and validated separately at the approved design checkpoint. Simulation evidence is not live model/scanner/provider evidence.

## Repository safety and recovered application progress

The actual supported dry-run exited 0 and inspected exactly 12 confirmed application roots. HEAD, Git status and file fingerprints match the prior checkpoint for all 12 roots. No application commits, pushes, PRs, merges or deployments occurred. Remote writes remain disabled in runtime.

1A, 1B, 1C, 2 and 3A are PARTIAL with medium confidence and no verified acceptance criteria. 3B is UNVERIFIED with low confidence. Conflicting completion/not-started historical claims occur for 1B, 1C and 2. Recovery recommends 1A acceptance reconciliation; 3B is only a development review candidate, not an eligible authorized execution. The controller blocks conflicting/unknown dependencies and requires a roadmap bound to approved context before application execution.

## New commands and exact next actions

Commands: autonomous plan/start/status/pause/resume/recover/report/validate/simulate. Run from C:/Projects/agrosphere/agrosphere-orchestrator:

~~~powershell
.\\.venv\\Scripts\\python.exe -m agrosphere_orchestrator.cli autonomous plan --milestone 3B
.\\.venv\\Scripts\\python.exe -m agrosphere_orchestrator.cli autonomous simulate --output-directory docs/milestones/AEO-6/evidence/operator-simulation
~~~

Supported future local-execution pattern, requiring a separate explicit application-run instruction and all exact existing grants:

~~~powershell
.\\.venv\\Scripts\\python.exe -m agrosphere_orchestrator.cli autonomous start --milestone <approved-milestone> --mode local --request <reviewed-request.json>
~~~

See 08-cli-operation-guide.md for request schemas, persisted run inspection, explicit continuation, atomic report export and authenticated checkpoint commands; see 09-approval-and-recovery-guide.md for recovery and current approval verification.

## Remaining live/runtime validation

Actual Codex smoke/proof-of-concept execution: **NOT RUN; separate explicit opt-in and authentication required**. Live GitHub publication/CI/review checks: **NOT RUN; separately scoped grants and configuration required**. Real application autonomous execution: **NOT RUN; separate explicit instruction after this acceptance required**. No automated merge, deployment or application advancement is implemented. Formal completion and AEO-5 runtime delivery remain pending their actual existing workflow evidence and approvals.

Local acceptance covers implemented unit/integration/simulated behavior. It does not claim production readiness or formal runtime delivery. No additional requirements/design approval is requested for the unchanged AEO-6 scope.
'''
(out/'AEO-6_ACCEPTANCE_REPORT.md').write_text(report,encoding='utf-8')
(out/'10-test-results.md').write_text(f'# AEO-6 final verification\n\n{count} tests passed; 0 failures/errors/skips. All 18 standard checks returned exit 0. All 275 accepted baseline and 293 design-checkpoint IDs were preserved; {len(current-design_baseline)} new cases.\n\nFull command/stdout/stderr/XML evidence is under evidence/implementation-validation. Source inventory hashes match the final tested implementation. End-to-end CLI simulation and migration preservation evidence are in evidence/simulation-final and evidence/runtime-migration-0008.json.\n',encoding='utf-8')
(out/'END_TO_END_STATUS.md').write_text('# AEO-6 end-to-end status\n\nSIMULATED END-TO-END PASSED through real lifecycle services with explicit fixture model/scanner/renderer/provider ports, three repositories, independent quality failure/repair, restart reconstruction and three mock PRs. Run: REPORTED. Formal completion: false. Runtime AEO-6/AEO-5: IMPLEMENTING.\n\nLive Codex, live GitHub and real application autonomous execution: NOT RUN / separately authorized. See evidence/simulation-final/simulation-report.json and AEO-6_ACCEPTANCE_REPORT.md.\n',encoding='utf-8')
files={}
for item in inventory['files']:
    files[item['path']]=root/item['path']
for name in ['AEO-6_ACCEPTANCE_REPORT.md','IMPLEMENTATION_NOTES.md','IMPLEMENTATION_INVENTORY.json','08-cli-operation-guide.md','09-approval-and-recovery-guide.md','10-test-results.md','END_TO_END_STATUS.md','REGISTERED_IMPLEMENTATION_PLAN.json']:
    files['docs/'+name]=out/name
for name in ['implementation-acceptance-summary.json','implementation-source-manifest.json','implementation-approval-linkage.json','runtime-migration-0008.json','autonomous-dry-run.json','implementation-validation-interrupted.json']:
    files['evidence/'+name]=evidence/name
for directory,names in [('implementation-validation',['commands.json','runner.json','pytest.xml']),('simulation-final',['simulation-report.json','simulation-report.md'])]:
    for name in names:
        files['evidence/'+directory+'/'+name]=evidence/directory/name
manifest={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in sorted(files.items())}
(out/'ARTIFACT_MANIFEST.json').write_text(json.dumps({'scope_id':linkage['scope_id'],'revision_id':linkage['revision_id'],'design_bundle_digest':linkage['bundle_digest'],'implementation_files':manifest},indent=2)+'\n',encoding='utf-8')
archive=out/'AEO-6_IMPLEMENTATION_REVIEW.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as output:
    for name,path in sorted(files.items()):
        output.write(path,name)
    output.write(out/'ARTIFACT_MANIFEST.json','ARTIFACT_MANIFEST.json')
with zipfile.ZipFile(archive) as output:
    assert output.testzip() is None
    assert all(hashlib.sha256(output.read(name)).hexdigest()==sha for name,sha in manifest.items())
print(json.dumps({'local_acceptance':summary['local_acceptance'],'tests':count,'new_cases_since_design':len(current-design_baseline),'standard_checks':18,'archive':str(archive),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'application_roots_unchanged':12,'runtime_state':'IMPLEMENTING','formal_completion':False},indent=2))
