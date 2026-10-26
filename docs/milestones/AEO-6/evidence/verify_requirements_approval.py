"""Read-only verification of the exact authenticated AEO-6 requirements checkpoint."""
import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.configuration import load_yaml
from agrosphere_orchestrator.design import canonical, require_approval
from agrosphere_orchestrator.design_artifacts import digest
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator.design_validation import verify_context, verify_stored_context
from agrosphere_orchestrator.persistence import AuditEvent, DesignCase, DesignDecision, DesignScope
from agrosphere_orchestrator.recovery import recovery_engine

out = Path('docs/milestones/AEO-6')
s = Settings(repository_manifest=out / 'design-repositories.json')
inputs = load_yaml(out / 'requirements-input.json', DesignInput)
repositories = verify_context(inputs, s.repository_manifest, s.role_registry)
expected = '48fd59274969f5abf0623159f5d15dba1c00111a80a67a654184ee58be6a2143'
engine = recovery_engine(s.database_url, readonly=True)
with Session(engine) as session:
    case = session.get(DesignCase, 'agrosphere:AEO-6')
    assert case.scope_id == expected
    scope = session.get(DesignScope, expected)
    assert digest(canonical(scope.payload)) == expected
    assert scope.payload == {'input': inputs.model_dump(mode='json'), 'repositories': repositories}
    verify_stored_context(inputs, repositories)
    decision = require_approval(session, case, expected, 'requirements')
    assert decision.id == 'c003c8e6-7477-4c5d-a226-194a5995539e'
    assert decision.payload['scope_id'] == expected
    events = list(session.scalars(select(AuditEvent).where(AuditEvent.entity_id == case.id, AuditEvent.kind == 'design.human-decision')))
    matches = [e for e in events if e.payload.get('decision_id') == decision.id]
    assert len(matches) == 1
    event = matches[0]
    assert event.actor == decision.actor
    assert event.payload == {'decision_id': decision.id, 'kind': 'requirements', 'subject': expected, 'decision': 'approved'}
    result = {'milestone': case.id, 'scope_id': expected, 'decision_id': decision.id, 'decision': decision.decision, 'actor': decision.actor, 'created_at': decision.created_at, 'authorized_currently': decision.actor in s.design_approvers, 'authentication_evidence': 'Persisted authorized SID decision and matching transactional design.human-decision audit event; existing CLI uses WindowsConsoleHumanVerifier/LogonUserW before decide persists. No credential or independent cryptographic authentication receipt is stored by this workflow.', 'audit_event_id': event.id, 'registered_scope_digest_verified': True, 'requirements_input_matches_persisted_scope': True, 'context_hashes_verified': len(inputs.context), 'diagram_sources': len(inputs.diagrams), 'requirements': len(inputs.requirements), 'implementation_tasks': len(inputs.plan.tasks), 'state': case.state}
(out / 'evidence/requirements-approval-verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
engine.dispose()
