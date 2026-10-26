"""Verify immutable approved design and exact implementation plan during implementation."""
import hashlib
import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design import artifacts_of, assert_design_gate, canonical, design_status, require_approval
from agrosphere_orchestrator.design_artifacts import check_files,digest
from agrosphere_orchestrator.persistence import AuditEvent, DesignCase, DesignRevision, DesignScope, Milestone
from agrosphere_orchestrator.recovery import recovery_engine

out=Path('docs/milestones/AEO-6')
scope_id='48fd59274969f5abf0623159f5d15dba1c00111a80a67a654184ee58be6a2143'
revision_id='e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe'
engine=recovery_engine(Settings().database_url,readonly=True)
with Session(engine) as session:
    case=session.get(DesignCase,'agrosphere:AEO-6')
    assert case.scope_id==scope_id and case.revision_id==revision_id
    milestone=session.scalar(select(Milestone).where(Milestone.project_id=='agrosphere',Milestone.external_id=='AEO-6'))
    assert_design_gate(session,milestone)
    scope=session.get(DesignScope,scope_id)
    revision=session.get(DesignRevision,revision_id)
    assert digest(canonical(scope.payload))==scope_id
    assert revision.payload['input']==scope.payload['input']
    assert milestone.spec==scope.payload['input']['plan']
    assert not check_files(artifacts_of(revision),revision.payload['repositories'])
    requirements=require_approval(session,case,scope_id,'requirements')
    design=require_approval(session,case,revision.payload['bundle_digest'],'design')
    assert requirements.id=='c003c8e6-7477-4c5d-a226-194a5995539e'
    assert design.id=='506b66d5-2e8c-423e-9cf6-814cef4aadb5'
    assert design.payload['revision_id']==revision_id and design.payload['validation_id']==case.validation_id
    events=list(session.scalars(select(AuditEvent).where(AuditEvent.entity_id==case.id,AuditEvent.kind=='design.human-decision')))
    assert any(e.actor==design.actor and e.payload.get('decision_id')==design.id and e.payload.get('subject')==design.subject and e.payload.get('decision')=='approved' for e in events)
    current_input=json.loads((out/'requirements-input.json').read_text(encoding='utf-8'))
    from agrosphere_orchestrator.design_models import DesignInput
    assert DesignInput.model_validate(current_input).model_dump(mode='json')==scope.payload['input']
    context=[]
    for ref in scope.payload['input']['context']:
        target=Path(scope.payload['repositories'][ref['repository']])/ref['path']
        current=hashlib.sha256(target.read_bytes()).hexdigest()
        context.append({'path':ref['path'],'approved_sha256':ref['sha256'],'current_sha256':current,'unchanged':current==ref['sha256']})
    result={'state':case.state,'scope_id':scope_id,'revision_id':revision_id,'bundle_digest':revision.payload['bundle_digest'],'validation_id':case.validation_id,'requirements_decision_id':requirements.id,'design_decision_id':design.id,'design_approver_authorized':True,'approved_artifacts_verified':len(revision.payload['artifacts']),'requirements_input_unchanged':True,'registered_plan_unchanged':True,'context':context,'context_policy':'Approved pre-implementation context was verified before entering IMPLEMENTING. Implementation changes source files; the existing design guard now checks immutable approved artifacts, scope, plan and current authorized decisions.','aeo5_state':design_status(engine,'agrosphere:AEO-5')['state']}
(out/'evidence/implementation-approval-linkage.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='context'},indent=2))
engine.dispose()
