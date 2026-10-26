"""Operator inspection using existing AEO services; no approval or source implementation."""
import json
from pathlib import Path
from sqlalchemy import inspect, text
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.recovery import recovery_engine, reconcile, export_reports
from agrosphere_orchestrator.recovery_models import RecoverySnapshot
from agrosphere_orchestrator.configuration import load_yaml
from agrosphere_orchestrator.execution_models import ExecutionPolicy
s=Settings()
e=recovery_engine(s.database_url, readonly=True)
with e.connect() as c:
    result={"migration": c.execute(text("select version_num from alembic_version")).scalars().all(), "tables": inspect(e).get_table_names(), "runs": [dict(r) for r in c.execute(text("select id,milestone,state,step from autonomous_runs")).mappings()], "design_cases": [dict(r) for r in c.execute(text("select id,state,scope_id,revision_id from design_cases")).mappings()]}
result["configuration"]={"github_remote_writes":s.github_remote_writes,"autonomous_roadmap":str(s.autonomous_roadmap) if s.autonomous_roadmap else None,"live_enabled":load_yaml(s.execution_policy,ExecutionPolicy).live_enabled,"design_approvers_count":len(s.design_approvers),"execution_approvers_count":len(s.execution_approvers),"governance_approvers_count":len(s.governance_approvers)}
e.dispose()
print(json.dumps(result,indent=2))
