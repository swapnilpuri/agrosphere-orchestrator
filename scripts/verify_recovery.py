"""Read-only workspace verification; write evidence only inside the orchestrator."""

import hashlib
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.persistence import AuditEvent, RecoveryRecord, now
from agrosphere_orchestrator.recovery import export_reports, reconcile, recovery_engine
from agrosphere_orchestrator.recovery_discovery import discover_project, repository_roots

ROOT = Path(__file__).resolve().parents[1]


def git_metadata(workspace):
    result = {}
    for repo in repository_roots(workspace):
        if repo.resolve() == ROOT:
            continue
        marker = repo / ".git"
        files = marker.rglob("*") if marker.is_dir() else [marker]
        result[str(repo)] = {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()
        }
    return result


def counts(engine):
    with Session(engine) as session:
        return {
            model.__tablename__: session.scalar(select(func.count()).select_from(model))
            for model in (RecoveryRecord, AuditEvent)
        }


def main():
    settings = Settings()
    before = git_metadata(settings.workspace_root)
    observed = discover_project(settings.workspace_root, settings.repository_manifest, ROOT)
    engine = recovery_engine(settings.database_url)
    try:
        identity = reconcile(engine, observed)
        export_reports(engine, settings.workspace_root, settings.recovery_directory)
        first = counts(engine)
        repeated = discover_project(settings.workspace_root, settings.repository_manifest, ROOT)
        repeated_id = reconcile(engine, repeated)
        export_reports(engine, settings.workspace_root, settings.recovery_directory)
        after = counts(engine)
        assert identity == repeated_id and first == after, "reconciliation was not idempotent"
        assert before == git_metadata(settings.workspace_root), "application Git metadata changed"
        assert [r["file_fingerprints"] for r in observed.repositories] == [
            r["file_fingerprints"] for r in repeated.repositories
        ], "application evidence files changed"
        output = {
            "executed_at": now(),
            "snapshot_id": identity,
            "application_repositories": len(observed.repositories),
            "missing_repositories": observed.missing_repositories,
            "git_metadata_unchanged": True,
            "evidence_files_unchanged": True,
            "idempotent_reconciliation": True,
            "record_counts": after,
            "milestones": {m.id: m.classification for m in observed.milestones},
        }
        (ROOT / "docs/validation/recovery.json").write_text(
            json.dumps(output, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(output, indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
