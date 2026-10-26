"""Verify the exact AEO-6 design checkpoint; optionally require persisted human approval.

Uses a read-only database connection and never records decisions or imports tasks.
"""
import argparse
import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design import artifacts_of, canonical, design_status, require_approval
from agrosphere_orchestrator.design_artifacts import check_files, digest
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator.design_validation import deterministic_findings, verify_stored_context
from agrosphere_orchestrator.design_agents import RuleBasedArchitectureReviewer
from agrosphere_orchestrator.persistence import AuditEvent, DesignCase, DesignRevision, DesignScope, DesignValidation
from agrosphere_orchestrator.recovery import recovery_engine

parser = argparse.ArgumentParser()
parser.add_argument('--require-approval', action='store_true')
parser.add_argument('--export-package', action='store_true')
args = parser.parse_args()
expected_scope = '48fd59274969f5abf0623159f5d15dba1c00111a80a67a654184ee58be6a2143'
expected_revision = 'e93d7e7f28163d47d871faed1a5f4ad16d99662a1cf0955400a2a87b163535fe'
out = Path('docs/milestones/AEO-6')
engine = recovery_engine(Settings().database_url, readonly=True)
with Session(engine) as session:
    case = session.get(DesignCase, 'agrosphere:AEO-6')
    assert case.scope_id == expected_scope and case.revision_id == expected_revision
    scope = session.get(DesignScope, case.scope_id)
    assert digest(canonical(scope.payload)) == expected_scope
    revision = session.get(DesignRevision, case.revision_id)
    assert revision.scope_id == expected_scope and revision.phase == 'design'
    assert revision.payload['input'] == scope.payload['input']
    inputs = DesignInput.model_validate(revision.payload['input'])
    verify_stored_context(inputs, revision.payload['repositories'])
    artifacts = artifacts_of(revision)
    assert not check_files(artifacts, revision.payload['repositories'])
    errors = deterministic_findings(inputs, artifacts, revision.payload['repositories'], revision.phase, revision.scope_id, revision.id)
    errors += RuleBasedArchitectureReviewer().review(inputs, artifacts)
    assert not [f for f in errors if f.severity == 'error']
    expected_bundle = digest(canonical({'scope_id': expected_scope, 'artifacts': [{k:a[k] for k in ('type','repository','path','sha256','requirement_ids','agent')} for a in revision.payload['artifacts']]}))
    assert expected_bundle == revision.payload['bundle_digest']
    validation = session.get(DesignValidation, case.validation_id)
    assert validation.revision_id == revision.id and validation.payload['passed']
    requirements = require_approval(session, case, expected_scope, 'requirements')
    assert requirements.id == 'c003c8e6-7477-4c5d-a226-194a5995539e'
    traceability = []
    business = next(a for a in artifacts if a.type == 'business')
    for requirement in inputs.requirements:
        criteria = []
        for criterion in requirement.acceptance_criteria:
            tasks = [t.id for t in inputs.plan.tasks if criterion in t.acceptance_criteria]
            assert tasks, f'Unplanned acceptance criterion: {requirement.id}'
            assert criterion in business.content
            criteria.append({'criterion': criterion, 'implementation_tasks': tasks})
        linked = [a.path for a in artifacts if requirement.id in a.requirement_ids]
        assert linked
        traceability.append({'requirement_id': requirement.id, 'acceptance_criteria': criteria, 'artifacts': linked})
    design_decision = None
    if args.require_approval:
        design_decision = require_approval(session, case, expected_bundle, 'design')
        assert design_decision.payload == {'scope_id': expected_scope, 'revision_id': expected_revision, 'validation_id': validation.id}
        events = list(session.scalars(select(AuditEvent).where(AuditEvent.entity_id == case.id, AuditEvent.kind == 'design.human-decision')))
        assert any(e.actor == design_decision.actor and e.payload == {'decision_id': design_decision.id, 'kind': 'design', 'subject': expected_bundle, 'decision': 'approved'} for e in events)
    result = {'milestone':case.id, 'state':case.state, 'revision_id':revision.id, 'scope_id':revision.scope_id, 'requirements_decision_id':requirements.id, 'bundle_digest':expected_bundle, 'validation_id':validation.id, 'validation':validation.payload, 'context_hashes_verified':len(inputs.context), 'artifacts_verified':len(artifacts), 'acceptance_criteria_verified':sum(len(r.acceptance_criteria) for r in inputs.requirements), 'diagram_sources_verified':sum(a.type.startswith('diagram:') for a in artifacts), 'diagram_renders_verified':sum(a.type.startswith('render:') for a in artifacts), 'implementation_plan_sha256':digest(canonical(inputs.plan.model_dump(mode='json'))), 'registered_implementation_tasks':[t.id for t in inputs.plan.tasks], 'implementation_plan_status':'Registered in approved DesignScope and linked DesignRevision; not imported for execution.', 'design_approval_persisted':design_decision is not None, 'design_decision_id':design_decision.id if design_decision else None}
    if args.export_package:
        assert not args.require_approval
        assert case.state == 'AWAITING_DESIGN_APPROVAL'
        package = {**result, 'approval_status':'PENDING_AUTHENTICATED_HUMAN_DESIGN_APPROVAL', 'requirements_approval':json.loads((out/'evidence/requirements-approval-verification.json').read_text(encoding='utf-8')), 'registered_implementation_plan':inputs.plan.model_dump(mode='json'), 'acceptance_criteria_traceability':traceability, 'review_package':design_status(engine, case.id), 'revision_payload':revision.payload, 'validation_history':[{'validation_id':v.id, 'revision_id':v.revision_id, **v.payload} for v in session.scalars(select(DesignValidation).join(DesignRevision, DesignRevision.id == DesignValidation.revision_id).where(DesignRevision.case_id == case.id))]}
        (out/'TECHNICAL_DESIGN_APPROVAL_PACKAGE.json').write_text(json.dumps(package,indent=2)+'\n',encoding='utf-8')
        (out/'REGISTERED_IMPLEMENTATION_PLAN.json').write_text(json.dumps(inputs.plan.model_dump(mode='json'),indent=2)+'\n',encoding='utf-8')
        (out/'REVIEW_PACKAGE.json').write_text(json.dumps(package['review_package'],indent=2)+'\n',encoding='utf-8')
        (out/'evidence/design-checkpoint-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
engine.dispose()
