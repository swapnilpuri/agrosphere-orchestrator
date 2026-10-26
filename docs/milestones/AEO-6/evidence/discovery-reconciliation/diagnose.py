"""Read-only evidence collection; never resumes or dispatches application work."""
import json, re, subprocess, hashlib
from pathlib import Path
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.recovery import recovery_engine, current_snapshot
from agrosphere_orchestrator.autonomous_store import AutonomousRun, report
from agrosphere_orchestrator.autonomous_models import AutonomousRequest
from agrosphere_orchestrator.autonomous_services import ExistingServices
from agrosphere_orchestrator.recovery_discovery import claim_text
OUT=Path(__file__).parent
RUN='ba0851d4-66bc-417a-851b-f08176bd8061'
def save(name,v): (OUT/name).write_text(json.dumps(v,indent=2,default=str)+'\n',encoding='utf-8')
s=Settings(); e=recovery_engine(s.database_url,readonly=True)
import agrosphere_orchestrator.autonomous_services as service_module
original_source=subprocess.run(['git','show','HEAD:src/agrosphere_orchestrator/recovery_discovery.py'],capture_output=True,text=True,check=True).stdout
baseline_namespace={'__name__':'agrosphere_orchestrator.baseline_discovery','__package__':'agrosphere_orchestrator'}
exec(compile(original_source,'git-HEAD:recovery_discovery.py','exec'),baseline_namespace)
current_classifier=service_module.recover_milestones
with Session(e) as db: req=AutonomousRequest.model_validate(db.get(AutonomousRun,RUN).request)
svc=ExistingServices(e,s)
service_module.recover_milestones=baseline_namespace['recover_milestones']
try: baseline=svc.discover(req)
finally: service_module.recover_milestones=current_classifier
save('baseline-reobserved.json',baseline)
found=svc.discover(req)
save('fresh-after.json',found); save('run-current.json',report(e,RUN))
try:
 identity,snap=current_snapshot(e,s.workspace_root); save('persisted-head-current.json',{'id':identity,'snapshot':snap.model_dump(mode='json')})
except ValueError as exc: save('persisted-head-before.json',{'error':str(exc)})
save('eligibility-current.json',{'reason':svc.eligibility(req,found),'request':req.model_dump(mode='json')})
repos={r['id']:r for r in found['snapshot']['repositories']}; cache={}; rows=[]
for m in found['snapshot']['milestones']:
 if m['id'] not in ('1A','1B','1C','2','3B'): continue
 for ev in m['evidence']:
  from agrosphere_orchestrator.recovery_models import Evidence
  text=claim_text(m['id'],Evidence.model_validate(ev))
  negative=bool(re.search(r'not started|not implemented|no .*implemented|not executed',text,re.I))
  positive=bool(re.search(r'complete|verified|all .*pass',text,re.I))
  key=(ev['repository'],ev['path']); repo=repos[ev['repository']]
  if key not in cache:
   git=subprocess.run(['git','--no-optional-locks','-C',repo['path'],'log','-1','--format=%H%x09%cI%x09%s','--',ev['path']],capture_output=True,text=True,check=False)
   cache[key]=git.stdout.strip() or None
  adjudication=next((a for a in m.get('adjudications',[]) if a['repository']==ev['repository'] and a['path']==ev['path'] and a['line']==ev['line']),{})
  rows.append({'milestone':m['id'],**ev,'adjudication':adjudication,'claim_text':text,'negative_trigger':negative,'positive_trigger':positive,'file_last_commit':cache[key], 'revision_caveat':'Evidence head is observed repository HEAD, not proven claim origin; modified_at is filesystem mtime, not authored date.', 'scope':adjudication.get('disposition','test-result'), 'implementation':m['implementation'],'test_files':m['tests'],'test_results':repo['test_results'],'acceptance':m['verified_acceptance_criteria'],'historical_or_current':adjudication.get('disposition','historical-test-result'), 'legitimately_superseded':False,'unresolved_contradiction':m['conflicts'] if adjudication.get('blocks') and m['conflicts'] else []})
save('conflict-evidence-matrix.json',rows)
print(json.dumps({'repositories':list(repos),'conflicts':found['conflicts'],'classifications':{m['id']:m['classification'] for m in found['snapshot']['milestones']},'rows':len(rows),'eligibility':svc.eligibility(req,found)},indent=2))
for row in rows:
 if row['negative_trigger']: print(json.dumps({k:row[k] for k in ('milestone','repository','path','line','claim_text','modified_at','file_last_commit')}))
e.dispose()
