import json
from pathlib import Path

from typer.testing import CliRunner

from agrosphere_orchestrator.cli import app
from agrosphere_orchestrator.persistence import import_plan

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def configure(tmp_path, monkeypatch, status="confirmed", exists=True):
    repo = ROOT.parent / "agrosphere-architecture" if exists else tmp_path / "missing"
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        json.dumps(
            {
                "repositories": [
                    {"id": "agrosphere-architecture", "path": str(repo), "status": status}
                ]
            }
        )
    )
    monkeypatch.setenv("AEO_REPOSITORY_MANIFEST", str(manifest))
    monkeypatch.setenv("AEO_ROLE_REGISTRY", str(ROOT / "config/roles.yaml"))


def test_validation_and_inspection(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    result = runner.invoke(app, ["milestone-validate", str(ROOT / "examples/aeo-1.yaml")])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["tasks"] == 2
    result = runner.invoke(app, ["repository-inspect"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)[0]["is_git"]


def test_unverified_and_missing_rejected(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch, status="unverified")
    result = runner.invoke(app, ["milestone-validate", str(ROOT / "examples/aeo-1.yaml")])
    assert result.exit_code == 1 and "unverified" in result.output
    configure(tmp_path, monkeypatch, exists=False)
    result = runner.invoke(app, ["repository-inspect"])
    assert result.exit_code == 1 and "missing" in result.stdout


def test_status_missing_does_not_create_db(tmp_path, monkeypatch):
    db = tmp_path / "absent.db"
    monkeypatch.setenv("AEO_DATABASE_URL", "sqlite:///" + db.as_posix())
    result = runner.invoke(app, ["project-status"])
    assert result.exit_code == 1
    assert not db.exists()


def test_status_existing(engine, plan):
    import_plan(engine, plan)
    result = runner.invoke(app, ["project-status"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["records"]["tasks"] == 2


def test_unknown_role_and_operation(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    source = (ROOT / "examples/aeo-1.yaml").read_text()
    path = tmp_path / "plan.yaml"
    path.write_text(source.replace("solution-architect", "unknown-role"))
    assert runner.invoke(app, ["milestone-validate", str(path)]).exit_code == 1
    path.write_text(source.replace("operation: inspect", "operation: deploy"))
    assert runner.invoke(app, ["milestone-validate", str(path)]).exit_code == 1
