"""CLI inspection, checks, reports and default recovery never invoke a write port."""

import json

import pytest
from typer.testing import CliRunner

from agrosphere_orchestrator import delivery
from agrosphere_orchestrator.cli import app


@pytest.mark.parametrize(
    "command",
    [
        "plan",
        "prepare",
        "publish",
        "status",
        "checks",
        "reviews",
        "reconcile",
        "recover",
        "report",
        "request-approval",
    ],
)
def test_delivery_commands_discoverable(command):
    result = CliRunner().invoke(app, ["delivery", command, "--help"])
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    "command", ["status", "checks", "reviews", "reconcile", "recover", "report"]
)
def test_observation_commands_never_mutate(engine, monkeypatch, command):
    def forbidden(*args, **kwargs):
        pytest.fail("Inspection attempted a mutation")

    monkeypatch.setattr(delivery, "mutate", forbidden)
    monkeypatch.setattr(
        delivery, "status", lambda *a: {"readiness": "BLOCKED", "merge_executed": False}
    )
    monkeypatch.setattr(
        delivery, "observe", lambda *a: {"readiness": "BLOCKED", "merge_executed": False}
    )
    monkeypatch.setattr(
        delivery, "reconcile", lambda *a: {"readiness": "BLOCKED", "merge_executed": False}
    )
    args = ["delivery", command, "run"] + (["unit"] if command not in {"status", "report"} else [])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert not json.loads(result.stdout)["merge_executed"]


def test_invalid_manifest_is_structured_and_does_not_disclose_input(engine, tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text('{"secret":"ghp_never_echo_this"}')
    result = CliRunner().invoke(app, ["delivery", "plan", str(path)])
    assert result.exit_code == 2
    assert "ghp_never_echo_this" not in result.output
    assert json.loads(result.stderr)["error"] == "INVALID_INPUT"


def test_publication_disabled_exit_code(engine, monkeypatch):
    from agrosphere_orchestrator.delivery_models import DeliveryError

    def deny(*args):
        raise DeliveryError("WRITES_DISABLED", "Remote writes are disabled")

    monkeypatch.setattr(delivery, "mutate", deny)
    result = CliRunner().invoke(
        app, ["delivery", "publish", "run", "unit", "--push-approval", "x", "--pr-approval", "y"]
    )
    assert result.exit_code == 3
    assert json.loads(result.stderr)["error"] == "WRITES_DISABLED"
