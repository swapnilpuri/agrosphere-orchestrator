"""Read-only final runtime gate/state observations; no approvals or delivery writes."""
import json
from datetime import UTC,datetime
from pathlib import Path
from sqlalchemy import select,text
from sqlalchemy.orm import Session
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.persistence import Milestone,Task,DesignCase
from agrosphere_orchestrator.quality_store import GovernanceRecord
from agrosphere_orchestrator.recovery import recovery_engine

settings=Settings()
engine=recovery_engine(settings.database_url,readonly=True)
with Session(engine) as session:
    milestone=session.scalar(select(Milestone).where(Milestone.project_id=="agrosphere",Milestone.external_id=="AEO-5"))
    tasks=list(session.scalars(select(Task).where(Task.milestone_id==milestone.id)))
    records=list(session.scalars(select(GovernanceRecord).where(GovernanceRecord.milestone_id==milestone.id)))
    result={"observed_at":datetime.now(UTC).isoformat(),"database_access":"read-only","schema":session.execute(text("select version_num from alembic_version")).scalar(),"state":session.get(DesignCase,"agrosphere:AEO-5").state,"runtime_task_states":{t.external_id:t.state for t in tasks},"remote_writes_enabled":settings.github_remote_writes,"repository_allowlist":settings.github_repositories,"activated_aeo4_policy_count":sum(r.kind=="policy.activated" for r in records),"publishing_approval_request_count":sum(r.kind=="approval.request" and r.payload.get("action","").startswith("delivery:") for r in records),"real_delivery_run_count":session.execute(text("select count(*) from delivery_runs where milestone_id=:m"),{"m":milestone.id}).scalar(),"remote_mutations_performed":False,"merge_or_deployment_performed":False,"aeo6_started":False}
engine.dispose()
Path("docs/milestones/AEO-5/evidence/runtime-boundary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
