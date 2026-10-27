"""Read-only authorization inspection; never authenticate, decide, import, or execute."""
import hashlib,json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design import require_approval,artifacts_of
from agrosphere_orchestrator.design_validation import verify_stored_context,check_files
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator.persistence import DesignCase,DesignRevision,DesignValidation,Milestone,Task,DesignDecision,AuditEvent
from agrosphere_orchestrator.recovery import recovery_engine
from agrosphere_orchestrator.configuration import load_yaml,RepositoryManifest,RoleRegistry
from agrosphere_orchestrator.execution_models import ExecutionPolicy
from agrosphere_orchestrator.autonomous_store import report
R=Path.cwd(); O=Path(__file__).resolve().parent
s=Settings(); e=recovery_engine(s.database_url,readonly=True)
with Session(e) as db:
 c=db.get(DesignCase,'agrosphere:AEO-6-ADJUDICATION'); rev=db.get(DesignRevision,c.revision_id); inputs=DesignInput.model_validate(rev.payload['input'])
 results={'case_state':c.state,'scope_id':c.scope_id,'revision_id':c.revision_id,'bundle_digest':rev.payload['bundle_digest'],'approvals':[]}
 for kind,subject,expected in [('requirements',c.scope_id,'67c78c9f-387d-426b-8e89-64092bd48fd0'),('design',rev.payload['bundle_digest'],'59196472-83fa-4d48-86ca-307559a1d00c')]:
  d=require_approval(db,c,subject,kind); assert d.id==expected
  results['approvals'].append({'kind':kind,'id':d.id,'subject':d.subject,'actor':d.actor,'created_at':d.created_at,'currently_authorized':True})
 verify_stored_context(inputs,rev.payload['repositories']); assert not check_files(artifacts_of(rev),rev.payload['repositories'])
 v=db.get(DesignValidation,c.validation_id); assert v.payload['passed']; results['validation_id']=v.id
 results['approved_context_and_artifacts_verified']=True
 results['registered_dag']=inputs.plan.model_dump(mode='json')
 m=db.scalar(select(Milestone).where(Milestone.external_id==inputs.plan.id,Milestone.project_id=='agrosphere'))
 results['imported_implementation_milestone']=m is not None
 results['implementation_tasks']=[] if m is None else [{'id':t.external_id,'state':t.state} for t in db.scalars(select(Task).where(Task.milestone_id==m.id))]
 results['run']=report(e,'ba0851d4-66bc-417a-851b-f08176bd8061')
 results['run'].pop('events',None)
 results['execution_approvers']=s.execution_approvers;results['governance_approvers']=s.governance_approvers
 policy=load_yaml(s.execution_policy,ExecutionPolicy);results['execution_policy']=policy.model_dump(mode='json')
 manifest=load_yaml(s.repository_manifest,RepositoryManifest).resolve(s.repository_manifest)
 results['application_manifest']=[{'id':r.id,'path':str(r.path)} for r in manifest];assert len(manifest)==12
 roles=load_yaml(s.role_registry,RoleRegistry).by_id()
 results['role_repository_blocks']=[{'task':t.id,'role':t.role,'repository':t.repository} for t in inputs.plan.tasks if t.repository not in roles[t.role].allowed_repositories]
 results['implementation_authorized']=False
 results['database_writes']=False;results['approval_commands_executed']=False
 (O/'verification.json').write_text(json.dumps(results,indent=2,default=str)+'\n',encoding='utf8')
 (O/'approved-plan.json').write_text(json.dumps(results['registered_dag'],indent=2)+'\n',encoding='utf8')
e.dispose()
print(json.dumps({'approvals_verified':len(results['approvals']),'context_and_artifacts_verified':True,'implementation_authorized':False,'configuration_blockers':results['role_repository_blocks'],'exit_code':0}))
