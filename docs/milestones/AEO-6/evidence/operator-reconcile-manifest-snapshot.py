"""Persist only the controller's manifest-bound observed snapshot using AEO-1B."""
import json
from pathlib import Path
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.recovery import recovery_engine, reconcile, export_reports
from agrosphere_orchestrator.recovery_models import RecoverySnapshot
s=Settings()
p=Path('docs/milestones/AEO-6/evidence/operator-milestone-2-dry-run.json')
v=json.loads(p.read_text(encoding='utf-8-sig'))
snapshot=RecoverySnapshot.model_validate(v['discovery']['snapshot'])
e=recovery_engine(s.database_url)
try:
    identity=reconcile(e,snapshot)
    exported=export_reports(e,s.workspace_root,s.recovery_directory)
    print(json.dumps({'snapshot_id':identity,'exported_snapshot_id':exported,'repositories':len(snapshot.repositories),'source':str(p),'approval_granted':False}))
finally:
    e.dispose()
