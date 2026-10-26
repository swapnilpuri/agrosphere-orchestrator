"""End-to-end fixture uses real design, grants, scheduler, quality and delivery services."""

from agrosphere_orchestrator.autonomous_simulation import simulate
from agrosphere_orchestrator.config.settings import Settings


def test_three_repository_restart_repair_and_mock_delivery(tmp_path, monkeypatch):
    original = Settings().database_url
    result = simulate(Settings(), tmp_path / "evidence")
    assert Settings().database_url == original
    assert result["repositories"] == 3
    assert result["run"]["state"] == "REPORTED"
    assert result["validation"]["valid"]
    assert result["failed_quality_then_repaired"]
    assert result["mock_transport_calls"] == 4
    assert result["provider_pushes"] == result["provider_prs"] == 3
    assert (
        not result["real_codex"] and not result["live_github"] and not result["formal_completion"]
    )
    categories = {
        i["checkpoint"]["category"] for i in result["restart_checkpoints"] if i["checkpoint"]
    }
    assert {
        "requirements",
        "design",
        "plan",
        "execution",
        "security-policy",
        "delivery-approval",
        "publication",
    } <= categories
    assert (tmp_path / "evidence/simulation-report.json").is_file()
