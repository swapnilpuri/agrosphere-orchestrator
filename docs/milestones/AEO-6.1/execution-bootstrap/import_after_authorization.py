"""Conditional existing-service DAG import. NOT authorization; never approve or execute.
Default is read-only. --register may be used only AFTER independent administrator authorization.
"""
import argparse, json
from pathlib import Path
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.configuration import RepositoryManifest, RoleRegistry, load_yaml
from agrosphere_orchestrator.design import artifacts_of, require_approval
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator.design_validation import verify_stored_context, check_files
from agrosphere_orchestrator.execution_models import ExecutionPolicy
from agrosphere_orchestrator.persistence import DesignCase, DesignRevision, import_plan
from agrosphere_orchestrator.planning import validate_plan
from agrosphere_orchestrator.recovery import recovery_engine
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--register',action='store_true');a=p.parse_args()
O=Path(__file__).resolve().parent;s=Settings()
assert s.execution_approvers and all(v.startswith('sid:S-') for v in s.execution_approvers), 'Administrator must independently assign verified execution SID(s)'
for active,proposed,model in [(s.repository_manifest,O/'repositories.internal.proposed.json',RepositoryManifest),(s.role_registry,O/'roles.internal.proposed.json',RoleRegistry),(s.execution_policy,O/'execution.internal.proposed.json',ExecutionPolicy)]:
    assert load_yaml(active,model)==load_yaml(proposed,model), 'Effective process configuration differs from reviewed draft; review changed content before import'
spec=validate_plan(O/'approved-plan.json',s.repository_manifest,s.role_registry)
roles=load_yaml(s.role_registry,RoleRegistry).by_id()
assert all(t.repository in roles[t.role].allowed_repositories for t in spec.tasks)
e=recovery_engine(s.database_url,readonly=not a.register)
try:
    with Session(e) as db:
        c=db.get(DesignCase,'agrosphere:AEO-6-ADJUDICATION');rev=db.get(DesignRevision,c.revision_id)
        inputs=DesignInput.model_validate(rev.payload['input']);assert spec==inputs.plan
        assert require_approval(db,c,c.scope_id,'requirements').id=='67c78c9f-387d-426b-8e89-64092bd48fd0'
        assert require_approval(db,c,rev.payload['bundle_digest'],'design').id=='59196472-83fa-4d48-86ca-307559a1d00c'
        verify_stored_context(inputs,rev.payload['repositories']);assert not check_files(artifacts_of(rev),rev.payload['repositories'])
    if a.register:
        ids=import_plan(e,spec)
        print(json.dumps({'imported_task_ids':ids,'milestone_external_id':spec.id,'approved':False,'executed':False}))
    else:
        print(json.dumps({'read_only_preflight_passed':True,'imported':False,'approved':False}))
finally:e.dispose()
