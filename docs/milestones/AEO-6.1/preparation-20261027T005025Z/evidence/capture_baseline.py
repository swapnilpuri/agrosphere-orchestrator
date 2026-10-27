"""Capture read-only baseline before authorized requirements registration."""
import hashlib,json,sqlite3,subprocess
from datetime import UTC,datetime
from pathlib import Path
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.recovery import recovery_engine
from agrosphere_orchestrator.autonomous_store import report,AutonomousRun
from agrosphere_orchestrator.autonomous_models import AutonomousRequest
from agrosphere_orchestrator.autonomous_services import ExistingServices
from agrosphere_orchestrator.autonomous import AutonomousMilestoneController
from agrosphere_orchestrator.persistence import DesignCase
from agrosphere_orchestrator.design import design_status
ROOT=Path('C:/Projects/agrosphere'); ORCH=ROOT/'agrosphere-orchestrator'; OUT=Path(__file__).resolve().parents[1]
RUN='ba0851d4-66bc-417a-851b-f08176bd8061'; CHANGE='AEO-6-ADJUDICATION'
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x): (OUT/'evidence'/n).write_text(json.dumps(x,indent=2,default=str)+'\n',encoding='utf-8')
s=Settings(); s=s.model_copy(update={'database_url':'sqlite:///C:/Projects/agrosphere/agrosphere-orchestrator/aeo.db','repository_manifest':ORCH/'config/repositories.yaml','workspace_root':ROOT})
engine=recovery_engine(s.database_url,readonly=True)
run=report(engine,RUN); save('run-before.json',run)
with Session(engine) as session:
 request=AutonomousRequest.model_validate(session.get(AutonomousRun,RUN).request)
 case=session.get(DesignCase,'agrosphere:'+CHANGE)
 target_case=None if case is None else {k:getattr(case,k) for k in ('id','state','scope_id','revision_id','validation_id')}
svc=ExistingServices(engine,s); fresh=svc.discover(request);save('application-discovery-before.json',fresh)
ctrl=AutonomousMilestoneController(engine,s,svc)
class RunView:
 created_at=run['created_at'];usage=run['usage'];request={'limits':run['limits']}
remaining=ctrl.remaining(RunView())
with sqlite3.connect((ORCH/'aeo.db').as_uri()+'?mode=ro',uri=True) as db:
 tables=[x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
 baseline={}
 for name in tables:
  rows=[list(r) for r in db.execute('SELECT * FROM "'+name+'"')]
  baseline[name]={'count':len(rows),'row_hashes':sorted(hashlib.sha256(canon(r).encode()).hexdigest() for r in rows)}
save('database-baseline.json',baseline)
paths=[]
for folder in ('src','tests','migrations'):
 paths += [p for p in (ORCH/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.sql') and '__pycache__' not in p.parts]
save('runtime-hashes-before.json',{p.relative_to(ORCH).as_posix():sha(p) for p in paths})
prior=ORCH/'docs/milestones/AEO-6/evidence/discovery-reconciliation'
save('prior-artifact-hashes.json',{p.relative_to(ORCH).as_posix():sha(p) for p in prior.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
status={'observed_at':datetime.now(UTC).isoformat(),'change_case':target_case,'change_design_status':design_status(engine,'agrosphere:'+CHANGE),'aeo6_status':{k:v for k,v in design_status(engine,'agrosphere:AEO-6').items() if k in ('milestone','state','scope_id','revision_id')},'milestone_2':design_status(engine,'agrosphere:2'),'run_state':run['state'],'run_checkpoint':run['checkpoint'],'run_valid':ctrl.validate(RUN),'remaining_run_seconds':remaining,'run_deadline_expired':remaining<=0,'application_repository_ids':[r['id'] for r in fresh['snapshot']['repositories']],'application_manifest_sha256':sha(s.repository_manifest),'discovery_consistent':fresh['discovery_consistent'],'conflicts':fresh['conflicts'],'design_approver_sids':s.design_approvers,'governance_approver_sids':s.governance_approvers,'autonomous_roadmap':str(s.autonomous_roadmap) if s.autonomous_roadmap else None,'plantuml_jar_configured':bool(s.plantuml_jar and s.plantuml_jar.is_file())}
save('baseline-status.json',status);engine.dispose();print(json.dumps(status,indent=2))
