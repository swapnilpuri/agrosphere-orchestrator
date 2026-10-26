"""Export a portable review archive and verify standard validation and boundary evidence."""
import difflib
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from sqlalchemy import inspect, text
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design import design_status
from agrosphere_orchestrator.recovery import recovery_engine

root = Path.cwd()
out = root / 'docs/milestones/AEO-6'
evidence = out / 'evidence'
validation = evidence / 'design-preparation-validation'
runner = json.loads((validation/'runner.json').read_text(encoding='utf-8'))
commands = json.loads((validation/'commands.json').read_text(encoding='utf-8'))
assert runner['exit_code'] == 0
assert len(commands['commands']) == 18
assert all(c['exit_code'] == 0 for c in commands['commands'])

def cases(file):
    return {(c.get('classname'),c.get('name')) for c in ET.parse(file).iter('testcase')}

current = cases(validation/'pytest.xml')
baseline = cases(evidence/'baseline-validation/pytest.xml')
assert baseline <= current
suite = next(ET.parse(validation/'pytest.xml').iter('testsuite'))
assert int(suite.get('failures')) == int(suite.get('errors')) == int(suite.get('skipped')) == 0
settings = Settings()
engine = recovery_engine(settings.database_url, readonly=True)
with engine.connect() as connection:
    tables = inspect(engine).get_table_names()
    counts = {name:connection.execute(text('SELECT COUNT(*) FROM "'+name+'"')).scalar_one() for name in tables}
    migration = connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one()
assert migration == '0007'
assert len(tables) == 29
for name in ['execution_attempts','execution_grants','executions','governance_records','orchestration_controls','orchestration_evidence','orchestration_plans','resource_leases','runs','task_claims','task_quality_states','validation_evidence','delivery_events','delivery_operations','delivery_runs','delivery_units']:
    assert counts[name] == 0, name
assert counts['tasks'] == 7 and counts['milestones'] == 1
assert settings.github_remote_writes is False
assert design_status(engine,'agrosphere:AEO-5')['state'] == 'IMPLEMENTING'
state = design_status(engine,'agrosphere:AEO-6')
assert state['state'] == 'AWAITING_DESIGN_APPROVAL'
assert not any(d['kind'] == 'design' for d in state['decisions'])
engine.dispose()
summary = {'checkpoint':state['state'], 'validator_exit_code':runner['exit_code'], 'standard_checks':len(commands['commands']), 'tests':dict(suite.attrib), 'baseline_275_test_ids_preserved':baseline <= current, 'baseline_test_count':len(baseline), 'added_design_regression_cases':len(current-baseline), 'runtime_migration':migration, 'runtime_table_counts':counts, 'aeo5_state':'IMPLEMENTING', 'remote_writes_enabled':False, 'aeo6_implementation_started':False, 'human_design_approval_recorded':False}
(evidence/'design-preparation-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
for name in ['design_agents','test_design']:
    before = (evidence/(name+'.before.py.txt')).read_text(encoding='utf-8')
    relative = 'src/agrosphere_orchestrator/design_agents.py' if name == 'design_agents' else 'tests/test_design.py'
    after = (root/relative).read_text(encoding='utf-8')
    patch = ''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='before/'+relative,tofile='after/'+relative))
    (evidence/(name+'.design-preparation.patch')).write_text(patch,encoding='utf-8')
line = f"Standard validator: exit 0; all 18 commands passed. Pytest: {suite.get('tests')} tests, 0 failures/errors/skips. All {len(baseline)} accepted baseline test IDs preserved; {len(current-baseline)} added cases cover existing AEO-1C preparation defects. Tests/migrations used a disposable SQLite backup and temporary Git repositories. Runtime remains schema 0007, AEO-5 IMPLEMENTING, no AEO-6 executable plan/tasks or execution/delivery activity."
(out/'10-test-results.md').write_text('# AEO-6A formal design preparation verification\n\n'+line+'\n\nFormal design validation passed with zero errors and one mandatory human conceptual-review warning. The focused design suite also passed: 65 tests in 67.57 seconds. See evidence/design-preparation-validation/commands.json, pytest.xml, runner.json and design-preparation-summary.json. The prior 275-test checkpoint report is archived in evidence/10-test-results.md.requirements-checkpoint.txt.\n',encoding='utf-8')
with (out/'TECHNICAL_DESIGN_APPROVAL_PACKAGE.md').open('a',encoding='utf-8') as report:
    report.write('\n## Standard validation and implementation boundary\n\n'+line+'\n')
package = json.loads((out/'TECHNICAL_DESIGN_APPROVAL_PACKAGE.json').read_text(encoding='utf-8'))
package['standard_validation_and_boundary_evidence'] = summary
(out/'TECHNICAL_DESIGN_APPROVAL_PACKAGE.json').write_text(json.dumps(package,indent=2)+'\n',encoding='utf-8')
files = {}
for artifact in package['revision_payload']['artifacts']:
    source = Path(package['revision_payload']['repositories'][artifact['repository']])/artifact['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == artifact['sha256']
    files['revision/'+source.relative_to(out/'revisions'/package['revision_id']).as_posix()] = source
for name in ['TECHNICAL_DESIGN_APPROVAL_PACKAGE.json','TECHNICAL_DESIGN_APPROVAL_PACKAGE.md','REGISTERED_IMPLEMENTATION_PLAN.json','REVIEW_PACKAGE.json','requirements-input.json','AEO-6_ACCEPTANCE_REPORT.md','08-cli-operation-guide.md','09-approval-and-recovery-guide.md','10-test-results.md']:
    files[name] = out/name
for ref in package['revision_payload']['input']['context']:
    if ref['path'].startswith('docs/milestones/AEO-6/'):
        files['approved-context/'+ref['path'].removeprefix('docs/milestones/AEO-6/')] = root/ref['path']
for name in ['requirements-approval-verification.json','design-checkpoint-verification.json','design-preparation-command-results.json','design-preparation-summary.json','verify_requirements_approval.py','verify_design_checkpoint.py','design_agents.design-preparation.patch','test_design.design-preparation.patch']:
    files['evidence/'+name] = evidence/name
for name in ['commands.json','runner.json','pytest.xml']:
    files['evidence/standard-validation/'+name] = validation/name
archive = out/('AEO-6-design-'+package['revision_id']+'.zip')
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
    for destination,source in sorted(files.items()):
        bundle.write(source,destination)
    bundle.writestr('EXPORT_MANIFEST.json',json.dumps({'revision_id':package['revision_id'],'bundle_digest':package['bundle_digest'],'files':{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in sorted(files.items())}},indent=2)+'\n')
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    manifest = json.loads(bundle.read('EXPORT_MANIFEST.json'))
    assert all(hashlib.sha256(bundle.read(n)).hexdigest() == h for n,h in manifest['files'].items())
result = {'archive':str(archive),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'exported_files':len(files),**summary}
(evidence/'design-export-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
