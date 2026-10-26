import json

from typer.testing import CliRunner

from agrosphere_orchestrator.autonomous import AutonomousMilestoneController
from agrosphere_orchestrator.cli import app


def test_default_start_is_read_only_even_when_input_says_local(tmp_path, monkeypatch, engine):
    source = tmp_path / "request.json"
    source.write_text(json.dumps({"milestone": "fixture", "mode": "local"}))

    def plan(self, request):
        assert request.mode == "dry-run"
        return {"mutations": False, "mode": "dry-run"}

    monkeypatch.setattr(AutonomousMilestoneController, "plan", plan)
    result = CliRunner().invoke(
        app, ["autonomous", "start", "--milestone", "fixture", "--request", str(source)]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["mutations"] is False


def test_cli_rejects_scope_mismatch_and_unknown_mode(tmp_path, engine):
    source = tmp_path / "request.json"
    source.write_text(json.dumps({"milestone": "different"}))
    result = CliRunner().invoke(
        app, ["autonomous", "start", "--milestone", "fixture", "--request", str(source)]
    )
    assert result.exit_code != 0
    result = CliRunner().invoke(
        app, ["autonomous", "start", "--milestone", "fixture", "--mode", "unrestricted"]
    )
    assert result.exit_code != 0


def test_autonomous_help_has_all_lifecycle_commands():
    result = CliRunner().invoke(app, ["autonomous", "--help"])
    assert result.exit_code == 0
    for command in [
        "plan",
        "start",
        "status",
        "pause",
        "resume",
        "recover",
        "report",
        "validate",
        "simulate",
    ]:
        assert command in result.stdout
