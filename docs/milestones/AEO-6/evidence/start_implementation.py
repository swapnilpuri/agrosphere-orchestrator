"""Enter the approved manual implementation lifecycle through existing services."""
import json
from pathlib import Path
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design import implementation_ready, move, require_approval
from agrosphere_orchestrator.design_models import DesignInput, MilestoneState
from agrosphere_orchestrator.persistence import DesignCase, DesignRevision, import_plan
from agrosphere_orchestrator.recovery import recovery_engine
engine = recovery_engine(Settings().database_url)
with Session(engine) as session:
    case = session.get(DesignCase, 'agrosphere:AEO-6')
    revision = session.get(DesignRevision, case.revision_id)
    decision = require_approval(session, case, revision.payload['bundle_digest'], 'design')
    inputs = DesignInput.model_validate(revision.payload['input'])
    state = case.state
if state == MilestoneState.DESIGN_APPROVED:
    import_plan(engine, inputs.plan)
    implementation_ready(engine, 'agrosphere:AEO-6')
with Session(engine) as session, session.begin():
    case = session.get(DesignCase, 'agrosphere:AEO-6')
    if case.state == MilestoneState.IMPLEMENTATION_READY:
        move(session, case, MilestoneState.IMPLEMENTING, 'codex-manual-implementation')
    assert case.state == MilestoneState.IMPLEMENTING
    result = {'state':case.state,'revision_id':case.revision_id,'design_decision_id':decision.id,'task_execution_evidence_fabricated':False,'implementation_mode':'User-authorized manual repository implementation; no autonomous application execution.'}
Path('docs/milestones/AEO-6/evidence/implementation-start.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
engine.dispose()
