"""Fresh manifest-bound observation and supported append-only AEO-1B reconciliation."""
import asyncio, json
from pathlib import Path
from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from agrosphere_orchestrator.autonomous import AutonomousMilestoneController
from agrosphere_orchestrator.autonomous_models import AutonomousRequest
from agrosphere_orchestrator.autonomous_store import AutonomousRun, report
from agrosphere_orchestrator.autonomous_services import ExistingServices
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.recovery import recovery_engine, reconcile
from agrosphere_orchestrator.recovery_models import RecoverySnapshot
from agrosphere_orchestrator.persistence import RecoveryRecord
from agrosphere_orchestrator.design import design_status
OUT=Path(__file__).parent; RUN='ba0851d4-66bc-417a-851b-f08176bd8061'
def save(n,v): (OUT/n).write_text(json.dumps(v,indent=2,default=str)+'\n',encoding='utf-8')
s=Settings(); e=recovery_engine(s.database_url)
before=report(e,RUN)
with Session(e) as db:
 req=AutonomousRequest.model_validate(db.get(AutonomousRun,RUN).request)
 previous=set(db.scalars(select(RecoveryRecord.id)))
svc=ExistingServices(e,s); fresh=svc.discover(req)
assert len(fresh['snapshot']['repositories'])==12
save('authoritative-observation.json',fresh)
identity=reconcile(e,RecoverySnapshot.model_validate(fresh['snapshot']))
# RECONCILING only observes facts and returns a conflict gate before design or execution.
assert fresh['conflicts']
result=asyncio.run(svc.perform('RECONCILING',req,before,None))
save('read-only-controller-check.json',result.model_dump(mode='json'))
# No unfinished operation: supported recover is an idempotent observation of the run.
controller=AutonomousMilestoneController(e,s,svc)
recovered=asyncio.run(controller.recover(RUN))
after=report(e,RUN)
assert before==after==recovered
with Session(e) as db:
 current=set(db.scalars(select(RecoveryRecord.id)))
 assert previous<=current
remaining=controller.remaining(type('StoredRun',(),{'created_at':before['created_at'],'usage':before['usage'],'request':{'limits':before['limits']}})())
save('reconciliation-result.json',{'snapshot_id':identity,'prior_records':len(previous),'current_records':len(current),'historical_records_preserved':previous<=current,'run_id':RUN,'run_unchanged':before==after,'run_state':after['state'],'checkpoint':after['checkpoint'],'discovery_consistent':fresh['discovery_consistent'],'conflicts':fresh['conflicts'],'remaining_run_seconds':remaining,'validate':controller.validate(RUN),'milestone_2_design':design_status(e,'agrosphere:2'),'eligibility_precheck':svc.eligibility(req,fresh),'resume_executed':False,'reason':'Unresolved historical status requires human evidence adjudication; resume would also enforce retained deadline.'})
save('run-after.json',after)
print((OUT/'reconciliation-result.json').read_text())
e.dispose()
