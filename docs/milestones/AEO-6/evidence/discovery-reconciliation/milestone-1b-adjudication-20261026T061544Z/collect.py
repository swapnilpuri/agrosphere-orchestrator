"""Forensic collection only: RO SQLite, local Git reads, no recovery mutation or approvals."""
import hashlib, json, subprocess, sqlite3, inspect
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.recovery import recovery_engine, fingerprint
from agrosphere_orchestrator.autonomous_store import report, AutonomousRun
from agrosphere_orchestrator.autonomous_models import AutonomousRequest
from agrosphere_orchestrator.autonomous_services import ExistingServices
from agrosphere_orchestrator.autonomous import AutonomousMilestoneController
from agrosphere_orchestrator.design import design_status
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator import recovery_discovery, recovery_models
from agrosphere_orchestrator.quality_models import ApprovalCategory
ROOT=Path('C:/Projects/agrosphere'); ORCH=ROOT/'agrosphere-orchestrator'
V=Path(__file__).resolve().parent; BASE=V.parent
RUN='ba0851d4-66bc-417a-851b-f08176bd8061'
COMMANDS=[]
def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':'),default=str)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(n,v): (V/n).write_text(json.dumps(v,indent=2,default=str)+'\n',encoding='utf-8')
def cmd(repo,*args):
 argv=['git','--no-optional-locks','-C',str(repo),'-c','core.fsmonitor=false',*args]
 p=subprocess.run(argv,capture_output=True,check=False)
 COMMANDS.append({'argv':argv,'exit_code':p.returncode,'stdout_sha256':sha(p.stdout),'stderr':p.stderr.decode('utf-8',errors='replace')})
 return p.stdout

def artifact(repo,rel):
 p=repo/rel; raw=p.read_bytes()
 head=cmd(repo,'rev-parse','HEAD').decode().strip()
 blob=cmd(repo,'rev-parse','--verify','HEAD:'+rel).decode().strip()
 working_blob=cmd(repo,'hash-object','--path='+rel,str(p)).decode().strip()
 committed=cmd(repo,'show','HEAD:'+rel) if blob else b''
 last=cmd(repo,'log','-1','--format=%H%x09%aI%x09%cI%x09%an%x09%s','--',rel).decode().strip()
 return {'repository':repo.name,'path':rel,'absolute_path':str(p),'sha256':sha(raw),'bytes':len(raw),'filesystem_mtime':datetime.fromtimestamp(p.stat().st_mtime,UTC).isoformat(),'observed_head':head,'head_blob':blob or None,'working_git_blob':working_blob,'matches_head_under_git_filters':blob==working_blob if blob else None,'committed_blob_sha256':sha(committed) if blob else None,'last_file_commit':last or None,'ignored':bool(cmd(repo,'check-ignore','--',rel).strip())}

s=Settings(_env_file=None,database_url='sqlite:///'+str(ORCH/'aeo.db').replace('\\','/'),repository_manifest=ORCH/'config/repositories.yaml',workspace_root=ROOT)
dbpath=ORCH/'aeo.db'
def db_state():
 with sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True) as db:
  names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
  values={n:[list(r) for r in db.execute('SELECT * FROM "'+n.replace('"','""')+'"')] for n in names}
  return {'file_sha256':sha(dbpath.read_bytes()),'tables':{n:{'count':len(rows),'content_sha256':sha(canon(sorted(rows,key=canon)).encode())} for n,rows in values.items()}}
before_db=db_state(); e=recovery_engine(s.database_url,readonly=True)
before_run=report(e,RUN); save('run-before.json',before_run)
with Session(e) as session: request=AutonomousRequest.model_validate(session.get(AutonomousRun,RUN).request)
svc=ExistingServices(e,s); fresh=svc.discover(request); again=svc.discover(request)
assert len(fresh['snapshot']['repositories'])==12
from agrosphere_orchestrator.recovery_models import RecoverySnapshot
assert fingerprint(RecoverySnapshot.model_validate(fresh['snapshot']))==fingerprint(RecoverySnapshot.model_validate(again['snapshot']))
save('fresh-discovery.json',fresh)
m=next(m for m in fresh['snapshot']['milestones'] if m['id']=='1B')
assert m['classification']=='PARTIAL' and fresh['conflicts']==['1B'] and not m['verified_acceptance_criteria']
negative=next(a for a in m['adjudications'] if a['disposition']=='historical-unresolved')
original=next(ev for ev in m['evidence'] if ev['repository']==negative['repository'] and ev['path']==negative['path'] and ev['line']==negative['line'])
locator='sha256:'+sha(canon(original).encode())
refs=[]
with sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True) as db:
 for rid,observed,payload in db.execute('SELECT id,observed_at,payload FROM recovery_snapshots'):
  snap=json.loads(payload)
  for milestone in snap.get('milestones',[]):
   if milestone['id']!='1B': continue
   for idx,ev in enumerate(milestone.get('evidence',[])):
    if ev['repository']==original['repository'] and ev['path']==original['path'] and ev.get('line')==7:
     refs.append({'recovery_record_id':rid,'snapshot_capture_time':observed,'json_pointer':'/milestones/'+str(snap['milestones'].index(milestone))+'/evidence/'+str(idx),'evidence':ev})
 for event in before_run['events']:
  if event['kind']!='operation.committed': continue
  snap=event['payload'].get('evidence',{}).get('snapshot',{})
  for milestone in snap.get('milestones',[]):
   if milestone['id']!='1B': continue
   for idx,ev in enumerate(milestone.get('evidence',[])):
    if ev['repository']==original['repository'] and ev['path']==original['path'] and ev.get('line')==7:
     refs.append({'autonomous_event_id':event['id'],'event_time':event['created_at'],'snapshot_capture_time':snap.get('observed_at'),'evidence_index':idx,'evidence':ev})
artifacts=[]
selections={
'agrosphere-estate-service':['docs/MILESTONE_1A_REPORT.md'],
'agrosphere-spatial-service':['docs/MILESTONE_1B_REPORT.md','src/main/java/com/agrosphere/spatial/adapter/in/messaging/EstateProjection.java','src/main/java/com/agrosphere/spatial/adapter/out/persistence/JdbcSpatialStore.java','src/main/resources/db/migration/V2__spatial_twin.sql','src/test/java/com/agrosphere/spatial/SpatialServiceIT.java','src/test/java/com/agrosphere/spatial/GeometryValidationTest.java','src/test/java/com/agrosphere/spatial/ApplicationRulesTest.java','src/test/java/com/agrosphere/spatial/SecurityPolicyTest.java'],
'agrosphere-architecture':['docs/roadmap/MILESTONE_1B.md','docs/adr/0009-spatial-digital-twin.md','docs/milestones/reconciliation-1a-3a/ACCEPTANCE_MATRIX.md','docs/milestones/reconciliation-1a-3a/evidence-index.json']}
for repo,rels in selections.items():
 for rel in rels:
  if (ROOT/repo/rel).is_file(): artifacts.append(artifact(ROOT/repo,rel))
  else: artifacts.append({'repository':repo,'path':rel,'missing':True})
# Resolve actual migration filename rather than infer it from the report title.
for p in (ROOT/'agrosphere-spatial-service/src/main/resources/db/migration').glob('V2*'):
 if not any(a.get('absolute_path')==str(p) for a in artifacts): artifacts.append(artifact(ROOT/'agrosphere-spatial-service',p.relative_to(ROOT/'agrosphere-spatial-service').as_posix()))
suites=[]
spatial=ROOT/'agrosphere-spatial-service'
for folder in ('target/surefire-reports','target/failsafe-reports'):
 for p in sorted((spatial/folder).glob('TEST-*.xml')):
  a=artifact(spatial,p.relative_to(spatial).as_posix()); artifacts.append(a)
  tree=ET.fromstring(p.read_bytes())
  suites.append({'path':a['path'],'sha256':a['sha256'],'timestamp':tree.get('timestamp'),'name':tree.get('name'),'tests':int(tree.get('tests',0)),'failures':int(tree.get('failures',0)),'errors':int(tree.get('errors',0)),'skipped':int(tree.get('skipped',0)),'test_cases':[t.get('name') for t in tree.findall('testcase')],'revision_binding':'Untracked/ignored result; no authenticated generating revision attestation recovered.'})
blame=cmd(ROOT/'agrosphere-estate-service','blame','--line-porcelain','-L','7,7','--','docs/MILESTONE_1A_REPORT.md').decode()
(V/'assertion-blame.txt').write_text(blame,encoding='utf-8')
save('source-artifacts.json',artifacts); save('retained-junit-analysis.json',suites)
save('assertion-record-provenance.json',{'review_locator':locator,'locator_note':'Derived review locator, not an original Evidence.id. Evidence model has no standalone record ID. Original durable containers and pointers follow.','fresh_snapshot_capture_time':fresh['snapshot']['observed_at'],'evidence':original,'classification_reasoning':negative,'durable_containers':refs})
# Hash source and prior package artifacts without changing them.
inspected=['src/agrosphere_orchestrator/recovery_discovery.py','src/agrosphere_orchestrator/recovery_models.py','tests/test_discovery_adjudication.py','src/agrosphere_orchestrator/human_approval.py','src/agrosphere_orchestrator/design.py','src/agrosphere_orchestrator/quality.py','src/agrosphere_orchestrator/quality_models.py','src/agrosphere_orchestrator/cli.py','src/agrosphere_orchestrator/autonomous.py','src/agrosphere_orchestrator/autonomous_services.py','src/agrosphere_orchestrator/recovery.py','src/agrosphere_orchestrator/persistence.py','src/agrosphere_orchestrator/orchestration.py']
source_hashes={p:sha((ORCH/p).read_bytes()) for p in inspected}
prior_hashes={n:sha((BASE/n).read_bytes()) for n in ['RECOVERY_REPORT.md','EVIDENCE_CONFLICT_MATRIX.md','HUMAN_ADJUDICATION_REVIEW.json','authoritative-observation.json','validation-summary.json']}
after_run=report(e,RUN); after_db=db_state()
assert before_run==after_run and before_db==after_db
save('run-after.json',after_run)
validation=AutonomousMilestoneController(e,s,svc).validate(RUN)
result={'observed_at':fresh['snapshot']['observed_at'],'run_id':RUN,'run_unchanged':before_run==after_run,'database_unchanged':before_db==after_db,'database_before':before_db,'database_after':after_db,'source_hashes':source_hashes,'prior_artifact_hashes':prior_hashes,'imported_classifier_path':inspect.getfile(recovery_discovery),'imported_models_path':inspect.getfile(recovery_models),'manifest_path':str(s.repository_manifest),'manifest_sha256':sha(s.repository_manifest.read_bytes()),'repository_ids':[r['id'] for r in fresh['snapshot']['repositories']],'discovery_consistent':fresh['discovery_consistent'],'conflicts':fresh['conflicts'],'milestone_1b_classification':m['classification'],'verified_acceptance_criteria':m['verified_acceptance_criteria'],'repeated_read_only_discovery_same_fingerprint':True,'validate':validation,'milestone_2':design_status(e,'agrosphere:2'),'milestone_1b':design_status(e,'agrosphere:1B'),'approval_categories':[c.value for c in ApprovalCategory],'tests_executed':[],'checks_executed':['local Git provenance/blob/hash and status reads','two manifest-bound read-only discovery observations','existing autonomous.validate','all SQLite tables/run/source/prior-artifact preservation checks','retained JUnit XML parsing'], 'resume_executed':False,'reconcile_executed':False,'recover_executed':False,'approval_mutation_executed':False}
save('read-only-verification.json',result); save('git-command-results.json',COMMANDS)
e.dispose()
print(json.dumps({'version':str(V),'assertion_locator':locator,'durable_containers':len(refs),'fresh_conflicts':fresh['conflicts'],'run_unchanged':before_run==after_run,'database_unchanged':before_db==after_db,'suites':suites,'source_missing':[a for a in artifacts if a.get('missing')]},indent=2))
