import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from agrosphere_orchestrator.cli import app
from agrosphere_orchestrator.persistence import (
    Approval,
    AuditEvent,
    Milestone,
    RecoveryRecord,
    import_plan,
)
from agrosphere_orchestrator.recovery import (
    current_snapshot,
    export_reports,
    fingerprint,
    reconcile,
)
from agrosphere_orchestrator.recovery_discovery import discover_project, recover_milestones
from agrosphere_orchestrator.recovery_models import Evidence
from agrosphere_orchestrator.state import record_approval


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "workspace"
    repo = root / "nested" / "estate"
    repo.mkdir(parents=True)

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
        )

    git("init", "-b", "main")
    (repo / "README.md").write_text("Milestone 1A implements estate metadata.\n")
    (repo / "pom.xml").write_text("<project>spring-boot</project>")
    (repo / "src/main/java").mkdir(parents=True)
    (repo / "src/main/java/Estate.java").write_text("class Estate {}")
    (repo / "src/test/java").mkdir(parents=True)
    (repo / "src/test/java/EstateTest.java").write_text("class EstateTest {}")
    git("add", ".")
    git(
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-m",
        "Milestone 1A implementation",
    )
    (repo / "docs").mkdir()
    (repo / "docs/MILESTONE_1A_REPORT.md").write_text(
        "# Milestone 1A complete\nAll tests passed.\nMilestone 1B not started.\n"
    )
    (repo / "target/surefire-reports").mkdir(parents=True)
    (repo / "target/surefire-reports/TEST-estate.xml").write_text(
        '<testsuite tests="2" failures="0" errors="0" skipped="0"/>'
    )
    manifest = tmp_path / "repositories.yaml"
    manifest.write_text(
        json.dumps(
            {
                "repositories": [
                    {"id": "estate", "path": str(repo)},
                    {"id": "missing", "path": str(root / "missing")},
                ]
            }
        )
    )
    return root, repo, manifest


def snapshot(workspace):
    root, _, manifest = workspace
    return discover_project(root, manifest, root / "orchestrator")


def digest_tree(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_discovery_nested_dirty_missing_and_readonly(workspace):
    root, repo, _ = workspace
    before = digest_tree(root)
    found = snapshot(workspace)
    assert before == digest_tree(root)
    assert found.missing_repositories == ["missing"]
    assert len(found.repositories) == 1
    observed = found.repositories[0]
    assert observed["dirty"] and observed["branch"] == "main" and observed["head"]
    assert observed["main_language"] == "Java"
    assert observed["test_commands"] == ["./mvnw verify"]
    assert observed["test_results"][0]["outcome"] == "historical-pass"
    assert observed["recent_commits"][0]["subject"] == "Milestone 1A implementation"
    assert str(repo) == observed["path"]


def test_evidence_never_implies_verified_completion(workspace):
    found = snapshot(workspace)
    milestones = {m.id: m for m in found.milestones}
    assert milestones["1A"].classification == "PARTIAL"
    assert milestones["1A"].evidence and milestones["1A"].tests
    assert not milestones["1A"].verified_acceptance_criteria
    assert milestones["3B"].classification == "UNVERIFIED"
    assert milestones["3B"].missing_documentation
    assert all(m.classification != "COMPLETED" for m in found.milestones)


def test_missing_workspace(workspace):
    root, _, manifest = workspace
    with pytest.raises(ValueError, match="workspace"):
        discover_project(root / "absent", manifest, root / "aeo")


def test_conflicting_claims_and_no_inferred_implementation():
    ev = [
        Evidence(
            repository="r",
            path="README.md",
            kind="document",
            sha256="a",
            excerpt="Milestone 3B complete",
        ),
        Evidence(
            repository="r",
            path="NEXT.md",
            kind="document",
            sha256="b",
            excerpt="Milestone 3B not started",
        ),
    ]
    m = next(m for m in recover_milestones([], ev) if m.id == "3B")
    assert m.classification == "UNVERIFIED" and m.conflicts


def test_idempotence_preserves_plan_and_approval(engine, plan, policy, workspace):
    task = import_plan(engine, plan)[0]
    record_approval(engine, task, "inspect", "human", True, policy)
    found = snapshot(workspace)
    identity = reconcile(engine, found)
    with Session(engine) as session:
        before = session.scalar(select(func.count()).select_from(AuditEvent))
        spec = session.scalar(select(Milestone)).spec
    found.observed_at = "later"
    assert reconcile(engine, found) == identity
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(RecoveryRecord)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == before
        assert session.scalar(select(Milestone)).spec == spec
        assert session.scalar(select(Approval)).decision == "approved"
    assert current_snapshot(engine, Path(found.workspace))[0] == identity


def test_transaction_rollback(engine, workspace, monkeypatch):
    import agrosphere_orchestrator.recovery as recovery

    def fail(*args, **kwargs):
        raise RuntimeError("interrupted transaction")

    found = snapshot(workspace)
    with monkeypatch.context() as patch:
        patch.setattr(recovery, "audit", fail)
        with pytest.raises(RuntimeError):
            reconcile(engine, found)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(RecoveryRecord)) == 0
    assert reconcile(engine, found) == fingerprint(found)


def test_interrupted_export_and_approved_text(engine, workspace, tmp_path, monkeypatch):
    found = snapshot(workspace)
    identity = reconcile(engine, found)
    destination = tmp_path / "project"
    export_reports(engine, Path(found.workspace), destination)
    roadmap = destination / "ROADMAP.yaml"
    with roadmap.open("a") as f:
        f.write("approved_plan: {milestone: 3B, approver: human}\n")
    current = destination / "CURRENT_STATE.md"
    with current.open("a") as f:
        f.write("Human approved notes: keep these.\n")
    original = os.replace
    calls = 0

    def fail_after_first(source, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("interrupted export")
        original(source, target)

    with monkeypatch.context() as patch:
        patch.setattr(os, "replace", fail_after_first)
        with pytest.raises(OSError):
            export_reports(engine, Path(found.workspace), destination)
    assert export_reports(engine, Path(found.workspace), destination) == identity
    assert "approved_plan: {milestone: 3B, approver: human}" in roadmap.read_text()
    assert "Human approved notes: keep these." in current.read_text()
    before = digest_tree(destination)
    export_reports(engine, Path(found.workspace), destination)
    assert digest_tree(destination) == before
    assert all(identity in p.read_text() for p in destination.iterdir())


def test_unmanaged_reports_fail_closed(engine, workspace, tmp_path):
    found = snapshot(workspace)
    reconcile(engine, found)
    destination = tmp_path / "project"
    destination.mkdir()
    protected = destination / "ROADMAP.yaml"
    protected.write_text("approved: true\n")
    with pytest.raises(ValueError, match="preserved"):
        export_reports(engine, Path(found.workspace), destination)
    assert protected.read_text() == "approved: true\n"
    assert len(list(destination.iterdir())) == 1


def test_cli_readonly_commands_and_reconcile(engine, workspace, monkeypatch):
    root, _, manifest = workspace
    monkeypatch.setenv("AEO_WORKSPACE_ROOT", str(root))
    monkeypatch.setenv("AEO_REPOSITORY_MANIFEST", str(manifest))
    runner = CliRunner()
    before = digest_tree(root)
    result = runner.invoke(app, ["project", "discover"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["missing_repositories"] == ["missing"]
    assert before == digest_tree(root)
    reconcile(engine, snapshot(workspace))
    for args in (["project", "status"], ["milestones", "history"], ["milestones", "next"]):
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)


def test_reverted_snapshot_updates_current_pointer(engine, workspace):
    found = snapshot(workspace)
    original = reconcile(engine, found)
    changed = found.model_copy(deep=True)
    changed.limitations.append("new observation")
    assert reconcile(engine, changed) != original
    assert reconcile(engine, found) == original
    assert current_snapshot(engine, Path(found.workspace))[0] == original


def test_status_does_not_create_database(tmp_path, monkeypatch):
    absent = tmp_path / "absent.db"
    monkeypatch.setenv("AEO_DATABASE_URL", "sqlite:///" + absent.as_posix())
    for args in (["project", "status"], ["milestones", "history"], ["milestones", "next"]):
        assert CliRunner().invoke(app, args).exit_code == 1
    assert not absent.exists()


def test_next_milestone_reference_does_not_create_false_conflict():
    ev = [
        Evidence(
            repository="r",
            path="MILESTONE_3A_REPORT.md",
            kind="document",
            sha256="x",
            excerpt="Status: COMPLETE. Milestone 3B was not started.",
        )
    ]
    milestones = {m.id: m for m in recover_milestones([], ev)}
    assert not milestones["3A"].conflicts
    assert not milestones["3B"].conflicts
    assert milestones["3B"].classification == "UNVERIFIED"


def test_unborn_and_detached_repositories(tmp_path):
    from agrosphere_orchestrator.recovery_discovery import collect_repository

    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)

    git("init", "-b", "main")
    observed, _ = collect_repository(repo)
    assert observed["head"] is None and observed["branch"] == "main"
    (repo / "README.md").write_text("fixture")
    git("add", ".")
    git("-c", "user.name=Fixture", "-c", "user.email=f@example.invalid", "commit", "-m", "fixture")
    git("checkout", "--detach")
    observed, _ = collect_repository(repo)
    assert observed["branch"] == "HEAD" and observed["head"]


def test_cli_reconcile_and_export_only(engine, workspace, monkeypatch, tmp_path):
    import agrosphere_orchestrator.cli as cli
    from agrosphere_orchestrator.config.settings import Settings

    root, _, manifest = workspace
    settings = Settings(
        workspace_root=root, repository_manifest=manifest, recovery_directory=tmp_path / "reports"
    )
    monkeypatch.setattr(
        cli, "recovery_paths", lambda: (settings, root / "aeo", tmp_path / "reports")
    )
    runner = CliRunner()
    result = runner.invoke(app, ["project", "reconcile"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["approval_granted"] is False
    identity = json.loads(result.stdout)["snapshot_id"]
    (tmp_path / "reports/CURRENT_STATE.md").unlink()
    result = runner.invoke(app, ["project", "reconcile", "--export-only"])
    assert result.exit_code == 0, result.output
    assert identity in (tmp_path / "reports/CURRENT_STATE.md").read_text()


def test_modified_source_content_changes_snapshot_identity(workspace):
    found = snapshot(workspace)
    _, repo, _ = workspace
    source = repo / "src/main/java/Estate.java"
    source.write_text("class Estate { int version = 1; }")
    dirty = snapshot(workspace)
    source.write_text("class Estate { int version = 2; }")
    changed = snapshot(workspace)
    assert dirty.repositories[0]["status"] == changed.repositories[0]["status"]
    assert fingerprint(dirty) != fingerprint(changed) != fingerprint(found)
