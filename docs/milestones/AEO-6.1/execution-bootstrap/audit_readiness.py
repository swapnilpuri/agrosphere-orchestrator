"""Read-only persisted-state and inactive-draft audit; never approves/imports/executes."""
import hashlib
import inspect
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.configuration import RepositoryManifest, RoleRegistry, load_yaml
from agrosphere_orchestrator.design import require_approval, artifacts_of
from agrosphere_orchestrator.design_validation import verify_stored_context, check_files
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator.execution_models import ExecutionPolicy
from agrosphere_orchestrator.orchestration import milestone_record
from agrosphere_orchestrator.orchestration_models import TaskOptions, ExecutionPlan
from agrosphere_orchestrator.persistence import DesignCase, DesignRevision, DesignValidation, Milestone
from agrosphere_orchestrator.recovery import recovery_engine
from agrosphere_orchestrator.autonomous_store import report
from agrosphere_orchestrator.planning import validate_plan
from sqlalchemy.engine import make_url
ROOT=Path.cwd(); OUT=Path(__file__).resolve().parent
RUN='ba0851d4-66bc-417a-851b-f08176bd8061'; KEY='agrosphere:AEO-6-ADJUDICATION'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),default=str)
s=Settings(); dbpath=Path(make_url(s.database_url).database).resolve()
def snapshot():
    with sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True) as db:
        names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        tables={}
        for name in names:
            quoted='"'+name.replace('"','""')+'"'
            rows=sorted(canonical(list(row)) for row in db.execute('SELECT * FROM '+quoted))
            tables[name]={'rows':len(rows),'sha256':sha(canonical(rows).encode())}
    return {'file_sha256':sha(dbpath.read_bytes()),'tables':tables}
def protected_hashes():
    files=[ROOT/'.env',*sorted((ROOT/'config').glob('*')),*sorted((ROOT/'src').rglob('*.py'))]
    return {p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in files if p.is_file()}
before=snapshot(); config_before=protected_hashes(); e=recovery_engine(s.database_url,readonly=True)
results={'executed_at':datetime.now(UTC).isoformat(),'argv':sys.argv,'database_mode':'read-only','database_before':before,'protected_before':config_before,'approvals':[]}
with Session(e) as db:
    c=db.get(DesignCase,KEY); rev=db.get(DesignRevision,c.revision_id); inputs=DesignInput.model_validate(rev.payload['input'])
    results.update(case_state=c.state,scope_id=c.scope_id,revision_id=c.revision_id,bundle_digest=rev.payload['bundle_digest'])
    for kind,subject,expected in [('requirements',c.scope_id,'67c78c9f-387d-426b-8e89-64092bd48fd0'),('design',rev.payload['bundle_digest'],'59196472-83fa-4d48-86ca-307559a1d00c')]:
        d=require_approval(db,c,subject,kind); assert d.id==expected
        results['approvals'].append({'kind':kind,'id':d.id,'subject':d.subject,'actor':d.actor,'created_at':d.created_at,'current_guard_passed':True})
    verify_stored_context(inputs,rev.payload['repositories']); assert not check_files(artifacts_of(rev),rev.payload['repositories'])
    v=db.get(DesignValidation,c.validation_id); assert v.payload['passed']; results['validation_id']=v.id
    results['context_and_artifacts_verified']=True
    exported=json.loads((OUT/'approved-plan.json').read_text()); assert exported==inputs.plan.model_dump(mode='json')
    results['dag_matches_approved_design']=True
    results['approved_dag_sha256']=sha((OUT/'approved-plan.json').read_bytes())
    results['task_order']=[t.id for t in inputs.plan.tasks]
    results['task_dependencies']={t.id:t.depends_on for t in inputs.plan.tasks}
    try:
        m=milestone_record(db,inputs.plan.id); results['imported_milestone_id']=m.id
    except ValueError as exc:
        results['imported_milestone_id']=None; results['readonly_resolution_error']=str(exc)
    results['run_before']=report(e,RUN)
    results['execution_approvers']=s.execution_approvers
    results['design_approvers']=s.design_approvers
    results['governance_approvers']=s.governance_approvers
    manifest=load_yaml(s.repository_manifest,RepositoryManifest).resolve(s.repository_manifest)
    results['application_manifest']=[{'id':r.id,'path':str(r.path)} for r in manifest]; assert len(manifest)==12
    roles=load_yaml(s.role_registry,RoleRegistry).by_id()
    results['role_blocks']=[{'task':t.id,'role':t.role,'repository':t.repository} for t in inputs.plan.tasks if t.repository not in roles[t.role].allowed_repositories]
    results['active_execution_policy']=load_yaml(s.execution_policy,ExecutionPolicy).model_dump(mode='json')
    draft_roles=load_yaml(OUT/'roles.internal.proposed.json',RoleRegistry).by_id()
    draft_policy=load_yaml(OUT/'execution.internal.proposed.json',ExecutionPolicy)
    draft_manifest=load_yaml(OUT/'repositories.internal.proposed.json',RepositoryManifest)
    spec=validate_plan(OUT/'approved-plan.json',OUT/'repositories.internal.proposed.json',OUT/'roles.internal.proposed.json')
    assert all(t.repository in draft_roles[t.role].allowed_repositories for t in spec.tasks)
    options={k:TaskOptions.model_validate(v) for k,v in json.loads((OUT/'task-options.proposed.json').read_text()).items()}
    candidate=ExecutionPlan(milestone=spec,design_revision=rev.id,tasks=options)
    assert all(set(o.validation_commands)<={v.id for v in draft_policy.validation_commands} for o in options.values())
    assert all(Path(v.argv[0]).is_file() and all(Path(p).is_dir() for p in v.read_paths) for v in draft_policy.validation_commands)
    assert draft_policy.live_enabled is False
    results['inactive_drafts_schema_and_assignments_passed']=True
    results['draft_runtime_read_paths_exist']=True
    results['draft_plan_is_not_registered_or_execution_ready']=True
    results['runtime_identity']={'python':sys.executable,'base_prefix':sys.base_prefix}
    results['plan_id']=None; results['execution_ids']=[]
    results['run_after']=report(e,RUN)
    assert results['run_before']==results['run_after']
e.dispose()
results['database_after']=snapshot(); results['protected_after']=protected_hashes()
assert results['database_before']==results['database_after']; assert results['protected_before']==results['protected_after']
results['database_unchanged']=True;results['protected_configuration_and_source_unchanged']=True;results['original_run_unchanged']=True
results['human_authentication_invoked']=False;results['model_invoked']=False;results['source_changes']=False
(OUT/'verification.json').write_text(json.dumps(results,indent=2,default=str)+'\n',encoding='utf8')
print(json.dumps({'approvals_verified':len(results['approvals']),'dag_matches_design':True,'read_only_resolution':results.get('readonly_resolution_error'),'inactive_drafts_valid':True,'database_unchanged':True,'original_run_unchanged':True,'exit_code':0}))
