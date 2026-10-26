"""Read-only AEO-6 discovery; no application or approval mutations."""
import json
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from sqlalchemy.engine import make_url
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design import design_status
from agrosphere_orchestrator.recovery import recovery_engine, current_snapshot, next_milestone
from agrosphere_orchestrator.recovery_discovery import discover_project
s = Settings()
out = Path("docs/milestones/AEO-6/evidence")
engine = recovery_engine(s.database_url, readonly=True)
workspace = s.workspace_root.resolve()
db = Path(make_url(s.database_url).database).resolve()
with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as c:
    tables = [r[0] for r in c.execute("select name from sqlite_master where type='table' order by name")]
    version = list(c.execute("select version_num from alembic_version"))
    counts = {t: c.execute('select count(*) from "' + t + '"').fetchone()[0] for t in tables}
status = {mid: design_status(engine, "agrosphere:" + mid) for mid in ("AEO-5", "AEO-6")}
for mid, data in status.items():
    (out / (mid + "-design-status-before.json")).write_text(json.dumps(data, indent=2), encoding="utf-8")
identity, prior = current_snapshot(engine, workspace)
fresh = discover_project(workspace, s.repository_manifest, s.recovery_directory)
(out / "fresh-discovery.json").write_text(fresh.model_dump_json(indent=2), encoding="utf-8")
summary = {"observed_at": datetime.now(UTC).isoformat(), "workspace": str(workspace), "repository": str(Path.cwd()), "database": str(db), "migration": version, "table_counts": counts, "remote_writes": s.github_remote_writes, "design_approvers_configured": len(s.design_approvers), "previous_recovery": identity, "previous_candidate": next_milestone(prior), "fresh_candidate": next_milestone(fresh), "milestones": [{"id": m.id, "classification": m.classification, "confidence": m.confidence, "implementation_evidence_count": len(m.implementation), "test_evidence_count": len(m.tests)} for m in fresh.milestones], "aeo5_state": status["AEO-5"].get("state"), "aeo6_state": status["AEO-6"].get("state")}
(out / "baseline-state.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
engine.dispose()
