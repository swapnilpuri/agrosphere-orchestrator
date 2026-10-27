import json,sqlite3,hashlib,subprocess,sys
from pathlib import Path
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.recovery import recovery_engine
from agrosphere_orchestrator.design import design_status,require_approval,artifacts_of
from agrosphere_orchestrator.design_artifacts import check_files
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator.design_validation import verify_stored_context
from agrosphere_orchestrator.persistence import DesignCase,DesignRevision,DesignValidation
from agrosphere_orchestrator.autonomous_store import report,AutonomousRun
from agrosphere_orchestrator.autonomous_models import AutonomousRequest
from agrosphere_orchestrator.autonomous_services import ExistingServices
R=Path.cwd();O=R/'docs/milestones/AEO-6.1/design-after-requirements';E=O/'evidence';RUN='ba0851d4-66bc-417a-851b-f08176bd8061'
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=str)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=Settings();e=recovery_engine(s.database_url,readonly=True)
with Session(e) as db:
 c=db.get(DesignCase,'agrosphere:AEO-6-ADJUDICATION');revision=db.get(DesignRevision,c.revision_id);validation=db.get(DesignValidation,c.validation_id)
 d=require_approval(db,c,c.scope_id,'requirements');assert d.id=='67c78c9f-387d-426b-8e89-64092bd48fd0'
 assert c.state=='AWAITING_DESIGN_APPROVAL' and validation.payload['passed']
 assert not check_files(artifacts_of(revision),revision.payload['repositories'])
 verify_stored_context(DesignInput.model_validate(revision.payload['input']),revision.payload['repositories'])
 try:require_approval(db,c,revision.payload['bundle_digest'],'design')
 except PermissionError as exc:gate=str(exc)
 else:raise AssertionError('Unexpected design approval; re-audit before work')
 request=AutonomousRequest.model_validate(db.get(AutonomousRun,RUN).request)
 save('registered-validation.json',{'id':validation.id,**validation.payload})
 status=design_status(e,c.id);save('design-after.json',status)
 artifacts=[{'path':a.path,'type':a.type,'sha256':a.sha256} for a in artifacts_of(revision)]
 assert len([a for a in artifacts if a['type'].startswith('render:')])==3
run=report(e,RUN);assert run==json.loads((E/'run-before.json').read_text());save('run-after.json',run)
fresh=ExistingServices(e,s).discover(request);save('discovery-after.json',fresh)
assert len(fresh['snapshot']['repositories'])==12 and fresh['conflicts']==['1B']
files=json.loads((E/'source-baseline.json').read_text());assert all(sha(R/p)==h for p,h in files.items())
apps=0
for repo in json.loads((E/'discovery-before.json').read_text())['snapshot']['repositories']:
 for rel,h in repo['file_fingerprints'].items():
  assert sha(Path(repo['path'])/rel)==h,(repo['id'],rel)
  apps+=1
baseline=json.loads((E/'database-baseline.json').read_text())
with sqlite3.connect((R/'aeo.db').as_uri()+'?mode=ro',uri=True) as db:
 current={n:[hashlib.sha256(json.dumps(list(r),sort_keys=True,default=str).encode()).hexdigest() for r in db.execute('SELECT * FROM "'+n+'"')] for n in baseline}
 changes={n:{'before':len(old),'after':len(current[n]),'original_rows_retained':len(set(old)&set(current[n]))} for n,old in baseline.items() if sorted(old)!=sorted(current[n])}
 assert set(changes)<= {'design_cases','design_revisions','design_validations','audit_events'},changes
 for n,old in baseline.items():
  if n!='design_cases':assert set(old)<=set(current[n]),n
 assert len(current['design_cases'])==len(baseline['design_cases'])
 assert len(set(baseline['design_cases'])-set(current['design_cases']))==1
save('database-changes.json',changes)
for args,name in [(['milestone','docs','AEO-6-ADJUDICATION'],'docs-command'),(['autonomous','validate',RUN],'run-validate-command')]:
 p=subprocess.run([sys.executable,'-m','agrosphere_orchestrator.cli',*args],capture_output=True,text=True)
 save(name+'.json',{'argv':[sys.executable,'-m','agrosphere_orchestrator.cli',*args],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0
roadmaps=[]
for name in ['MILESTONES.md','IMPLEMENTATION_BACKLOG.md','MILESTONE_1A.md','MILESTONE_1B.md','MILESTONE_1C.md']:
 p=R.parent/'agrosphere-architecture/docs/roadmap'/name
 if p.is_file():roadmaps.append({'path':str(p),'sha256':sha(p)})
save('roadmap-sources.json',roadmaps)
summary={'requirements_verified':True,'decision_id':d.id,'scope_id':c.scope_id,'revision_id':c.revision_id,'bundle_digest':revision.payload['bundle_digest'],'validation_id':validation.id,'validation_passed':True,'state':c.state,'design_gate':gate,'design_approved':False,'implementation_authorized':False,'run_unchanged':True,'original_deadline_unchanged':True,'all_original_decisions_snapshots_runs_operations_events_and_migrations_preserved':True,'runtime_tests_config_migrations_unchanged':True,'application_fingerprints_preserved':apps,'application_repositories':12,'conflicts':fresh['conflicts'],'milestone_1b':next(m['classification'] for m in fresh['snapshot']['milestones'] if m['id']=='1B'),'artifacts':artifacts,'database_changes':changes,'approval_commands_executed':False,'resume_executed':False,'full_regression':(json.loads((E/'regression/runner.json').read_text())['exit_code'] if (E/'regression/runner.json').exists() else 'running')}
save('completion-verification.json',summary);print(json.dumps({k:v for k,v in summary.items() if k not in ('artifacts','database_changes')},indent=2));e.dispose()
