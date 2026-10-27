import json,sqlite3,hashlib,subprocess
from pathlib import Path
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.recovery import recovery_engine
from agrosphere_orchestrator.design import require_approval,design_status,canonical
from agrosphere_orchestrator.persistence import DesignCase,DesignDecision
from agrosphere_orchestrator.autonomous_store import report,AutonomousRun
from agrosphere_orchestrator.autonomous_models import AutonomousRequest
from agrosphere_orchestrator.autonomous_services import ExistingServices
from agrosphere_orchestrator.autonomous import AutonomousMilestoneController
R=Path.cwd(); O=R/'docs/milestones/AEO-6.1/design-after-requirements/evidence'; RUN='ba0851d4-66bc-417a-851b-f08176bd8061'
def save(n,x):(O/n).write_text(json.dumps(x,indent=2,default=str)+'\n',encoding='utf-8')
s=Settings(); e=recovery_engine(s.database_url,readonly=True)
with Session(e) as db:
 c=db.get(DesignCase,'agrosphere:AEO-6-ADJUDICATION'); d=require_approval(db,c,c.scope_id,'requirements')
 assert c.scope_id=='8367e71ff015366e5c2493c11d199f3d9f7f3ad7bde902f385d10b6a5db96138'
 assert d.id=='67c78c9f-387d-426b-8e89-64092bd48fd0' and d.decision=='approved'
 save('authenticated-requirements.json',{k:getattr(d,k) for k in ('id','case_id','subject','kind','actor','decision','payload','created_at')})
 request=AutonomousRequest.model_validate(db.get(AutonomousRun,RUN).request)
save('design-before.json',design_status(e,c.id));save('run-before.json',report(e,RUN))
save('configuration.json',{'design_approvers':s.design_approvers,'execution_approvers':s.execution_approvers,'governance_approvers':s.governance_approvers,'autonomous_roadmap':s.autonomous_roadmap,'plantuml_jar':s.plantuml_jar,'repository_manifest':str(s.repository_manifest),'workspace_root':str(s.workspace_root)})
svc=ExistingServices(e,s);fresh=svc.discover(request);save('discovery-before.json',fresh)
save('run-validation.json',AutonomousMilestoneController(e,s,svc).validate(RUN))
with sqlite3.connect((R/'aeo.db').as_uri()+'?mode=ro',uri=True) as db:
 names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
 baseline={n:[hashlib.sha256(json.dumps(list(r),sort_keys=True,default=str).encode()).hexdigest() for r in db.execute('SELECT * FROM "'+n+'"')] for n in names}
save('database-baseline.json',baseline)
files={}
for folder in ('src','tests','migrations','config'):
 for p in (R/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:files[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
save('source-baseline.json',files)
p=subprocess.run(['git','--no-optional-locks','status','--short'],capture_output=True,text=True);save('git-before.json',{'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
print(json.dumps({'requirements_verified':True,'actor':d.actor,'design':design_status(e,c.id),'run_state':report(e,RUN),'conflicts':fresh['conflicts'],'repositories':len(fresh['snapshot']['repositories'])},default=str,indent=2))
