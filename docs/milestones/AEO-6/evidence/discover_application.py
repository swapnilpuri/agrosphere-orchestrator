"""Use confirmed application roots only; exclude nested orchestrator test fixtures."""
import json
from pathlib import Path
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.configuration import RepositoryManifest, load_yaml
from agrosphere_orchestrator.recovery_discovery import collect_repository, recover_milestones
from agrosphere_orchestrator.recovery_models import RecoverySnapshot
from agrosphere_orchestrator.recovery import next_milestone
s = Settings()
repositories, evidence = [], []
for repo in load_yaml(s.repository_manifest, RepositoryManifest).resolve(s.repository_manifest):
    if repo.id == "agrosphere-orchestrator" or repo.status != "confirmed":
        continue
    inventory, found = collect_repository(repo.path)
    repositories.append(inventory)
    evidence.extend(found)
snapshot = RecoverySnapshot(workspace=str(s.workspace_root.resolve()), repositories=repositories, milestones=recover_milestones(repositories, evidence), limitations=["Confirmed application manifest roots only; nested test fixture repositories excluded.", "Historical tests and completion documents do not establish current acceptance.", "Application builds/tests were not executed; Git subject history is bounded to 200 commits."])
out = Path("docs/milestones/AEO-6/evidence")
(out / "application-discovery.json").write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
summary = {"repositories": [{"id": r["id"], "path": r["path"], "head": r["head"], "dirty": r["dirty"]} for r in repositories], "milestones": [{"id": m.id, "classification": m.classification, "confidence": m.confidence, "implementation": m.implementation, "tests_observed": len(m.tests), "verified_criteria": m.verified_acceptance_criteria} for m in snapshot.milestones], "candidate": next_milestone(snapshot)}
(out / "application-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
