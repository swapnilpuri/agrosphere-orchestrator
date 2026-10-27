"""Validate and register only proposed requirements through the existing CLI; never decide or resume."""
import hashlib,json,os,sqlite3,subprocess,sys
from pathlib import Path
from sqlalchemy.orm import Session
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator.design_validation import verify_context
from agrosphere_orchestrator.design import canonical,design_status,require_approval
from agrosphere_orchestrator.design_artifacts import digest
from agrosphere_orchestrator.persistence import DesignCase
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.recovery import recovery_engine
from agrosphere_orchestrator.autonomous_store import report
from agrosphere_orchestrator.autonomous import AutonomousMilestoneController
from agrosphere_orchestrator.autonomous_models import AutonomousRequest
from agrosphere_orchestrator.autonomous_services import ExistingServices
ROOT=Path('C:/Projects/agrosphere'); ORCH=ROOT/'agrosphere-orchestrator'; OUT=Path(__file__).resolve().parents[1]; EV=OUT/'evidence'
RUN='ba0851d4-66bc-417a-851b-f08176bd8061'; KEY='agrosphere:AEO-6-ADJUDICATION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(EV/n).write_text(json.dumps(x,indent=2,default=str)+'\n',encoding='utf-8')
source_before=json.loads((EV/'runtime-hashes-before.json').read_text())
prior_before=json.loads((EV/'prior-artifact-hashes.json').read_text())
assert all(sha(ORCH/p)==h for p,h in source_before.items())
assert all(sha(ORCH/p)==h for p,h in prior_before.items())
head=subprocess.run(['git','--no-optional-locks','-C',str(ORCH),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
p=OUT/'requirements-input.json'; value=json.loads(p.read_text(encoding='utf-8'))
for ref in value['context']:
 assert sha(ORCH/ref['path'])==ref['sha256'],ref['path']
 ref['head']=head
p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
inputs=DesignInput.model_validate(value)
repos=verify_context(inputs,OUT/'design-repositories.json',ORCH/'config/roles.yaml')
expected=digest(canonical({'input':inputs.model_dump(mode='json'),'repositories':repos}))
s=Settings();s=s.model_copy(update={'database_url':'sqlite:///C:/Projects/agrosphere/agrosphere-orchestrator/aeo.db','repository_manifest':ORCH/'config/repositories.yaml','workspace_root':ROOT})
e=recovery_engine(s.database_url,readonly=True)
with Session(e) as session:
 assert session.get(DesignCase,KEY) is None,'Target case changed externally; do not overwrite a registered scope.'
assert report(e,RUN)==json.loads((EV/'run-before.json').read_text())
e.dispose()
env={**os.environ,'AEO_DATABASE_URL':s.database_url,'AEO_REPOSITORY_MANIFEST':str(OUT/'design-repositories.json'),'AEO_WORKSPACE_ROOT':str(ROOT)}
argv=[sys.executable,'-m','agrosphere_orchestrator.cli','milestone','design','AEO-6-ADJUDICATION','--requirements',str(p)]
completed=subprocess.run(argv,cwd=ORCH,env=env,capture_output=True,text=True,check=False)
save('requirements-registration-command.json',{'argv':argv,'environment_overrides':{k:env[k] for k in ('AEO_DATABASE_URL','AEO_REPOSITORY_MANIFEST','AEO_WORKSPACE_ROOT')},'exit_code':completed.returncode,'stdout':completed.stdout,'stderr':completed.stderr})
assert completed.returncode==0,completed.stderr
assert json.loads(completed.stdout)['scope_id']==expected
# Supported package presentation. No decision command is invoked.
argv2=[sys.executable,'-m','agrosphere_orchestrator.cli','milestone','docs','AEO-6-ADJUDICATION']
shown=subprocess.run(argv2,cwd=ORCH,env=env,capture_output=True,text=True,check=False)
save('requirements-review-command.json',{'argv':argv2,'exit_code':shown.returncode,'stdout':shown.stdout,'stderr':shown.stderr})
assert shown.returncode==0
review=json.loads(shown.stdout);save('registered-requirements-review.json',review)
e=recovery_engine(s.database_url,readonly=True)
with Session(e) as session:
 case=session.get(DesignCase,KEY)
 assert case.scope_id==expected and case.revision_id is None
 try: require_approval(session,case,expected,'requirements')
 except PermissionError as exc: gate=str(exc)
 else: raise AssertionError('Unexpected approval; stop and re-audit')
run_after=report(e,RUN);save('run-after.json',run_after)
assert run_after==json.loads((EV/'run-before.json').read_text())
svc=ExistingServices(e,s)
from agrosphere_orchestrator.autonomous_store import AutonomousRun
with Session(e) as session: request=AutonomousRequest.model_validate(session.get(AutonomousRun,RUN).request)
fresh=svc.discover(request);save('application-discovery-after.json',fresh)
assert len(fresh['snapshot']['repositories'])==12 and fresh['conflicts']==['1B']
# Every original DB row must remain byte-for-byte the same; registration is additive only.
baseline=json.loads((EV/'database-baseline.json').read_text())
with sqlite3.connect((ORCH/'aeo.db').as_uri()+'?mode=ro',uri=True) as db:
 current={}
 for name in baseline:
  rows=[list(r) for r in db.execute('SELECT * FROM "'+name+'"')]
  current[name]={'count':len(rows),'row_hashes':sorted(hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest() for r in rows)}
 assert all(set(old['row_hashes'])<=set(current[n]['row_hashes']) for n,old in baseline.items())
 changes={n:{'before':old['count'],'after':current[n]['count']} for n,old in baseline.items() if old!=current[n]}
 assert set(changes)<={'design_cases','design_scopes','audit_events'},changes
 for name in ('design_decisions','recovery_snapshots','autonomous_runs','autonomous_operations','autonomous_events','alembic_version'):
  assert current[name]==baseline[name],name
assert all(sha(ORCH/p)==h for p,h in source_before.items())
assert all(sha(ORCH/p)==h for p,h in prior_before.items())
before_snapshot=json.loads((EV/'application-discovery-before.json').read_text())['snapshot']
application_files=0
for repo in before_snapshot['repositories']:
 for rel,h in repo['file_fingerprints'].items():
  assert sha(Path(repo['path'])/rel)==h,(repo['id'],rel)
  application_files+=1
result={'requirements_schema_valid':True,'context_hash_head_role_guards_valid':True,'requirement_count':len(inputs.requirements),'context_references':len(inputs.context),'scope_id':expected,'case_id':KEY,'requirements_registered':True,'requirements_approved':False,'requirements_gate':gate,'state':review['state'],'technical_revision_generated':False,'technical_design_validated':False,'implementation_authorized':False,'approval_commands_executed':False,'resume_executed':False,'run_id':RUN,'run_unchanged':True,'run_validation':AutonomousMilestoneController(e,s,svc).validate(RUN),'discovery_consistent':fresh['discovery_consistent'],'conflicts':fresh['conflicts'],'application_repository_count':len(fresh['snapshot']['repositories']),'application_fingerprints_preserved':application_files,'runtime_and_migration_files_unchanged':True,'prior_evidence_unchanged':True,'all_original_database_rows_preserved':True,'all_decisions_snapshots_run_history_migrations_unchanged':True,'additive_registration_tables':changes,'design_approver_sids':s.design_approvers,'governance_approver_sids':s.governance_approvers,'next_command':'.\\.venv\\Scripts\\python.exe -m agrosphere_orchestrator.cli milestone approve-requirements AEO-6-ADJUDICATION','exact_confirmation_phrase':'APPROVED '+KEY+':requirements:'+expected,'tests_executed':[]}
save('preparation-verification.json',result);e.dispose();print(json.dumps(result,indent=2))
