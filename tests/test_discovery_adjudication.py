"""Fail-closed adjudication: observation is never completion or supersession."""

import pytest

from agrosphere_orchestrator.recovery_discovery import recover_milestones
from agrosphere_orchestrator.recovery_models import Evidence


def ev(text, path="docs/MILESTONE_1B_REPORT.md", **kw):
    return Evidence(repository="r", path=path, kind="document", sha256="a", excerpt=text, **kw)


def observed(negative, **kw):
    repo = {
        "id": "r",
        "source_files": ["src/Spatial.java"],
        "test_files": ["tests/SpatialTest.java"],
    }
    evidence = [
        ev(
            "Milestone 1B implements spatial features; complete",
            modified_at="2026-10-25T00:00:00Z",
            head="new",
        ),
        negative,
    ]
    return next(m for m in recover_milestones([repo], evidence) if m.id == "1B")


def test_historical_negative_with_implementation_requires_review():
    m = observed(
        ev(
            "Milestone 1B was not started.",
            path="docs/MILESTONE_1A_REPORT.md",
            modified_at="2026-10-24T00:00:00Z",
            head="old",
        )
    )
    assert m.classification == "PARTIAL" and m.conflicts
    assert any(a["disposition"] == "historical-unresolved" for a in m.adjudications)
    assert not any(a["superseded"] for a in m.adjudications)
    assert not m.verified_acceptance_criteria


@pytest.mark.parametrize(
    "text",
    [
        "Milestone 1B is not implemented",
        "Milestone 1B implementation has not started",
        "Status: not started",
    ],
)
def test_current_contradictions_block(text):
    assert observed(ev(text)).conflicts


def test_partial_acceptance_never_promotes_completion():
    m = observed(ev("Milestone 1B complete; performance acceptance remains open"))
    assert m.classification == "PARTIAL" and not m.verified_acceptance_criteria


def test_missing_timestamp_blocks_temporal_supersession():
    m = observed(ev("Milestone 1B not started"))
    assert m.conflicts
    assert any("Missing timestamp" in a["reason"] for a in m.adjudications)


def test_conflicting_revisions_are_not_newest_wins():
    m = observed(
        ev("Milestone 1B not started", modified_at="2026-10-26T00:00:00Z", head="other-branch")
    )
    assert m.conflicts and not any(a["superseded"] for a in m.adjudications)


@pytest.mark.parametrize(
    "text",
    [
        "# Recommended Milestone 1B prompt (not executed)",
        "Recommended Milestone 1B integration tasks (not started)",
        "no renderer, client or terrain engine is implemented.",
        "| Compose overlay config --quiet | PASS using placeholders shared services were not started |",
    ],
)
def test_bounded_planning_and_component_claims_preserved(text):
    m = observed(ev(text))
    assert not m.conflicts
    assert len(m.evidence) == len(m.adjudications) == 2


def test_ambiguous_negative_is_not_dropped():
    assert observed(ev("Implementation not started")).conflicts


def test_recommendation_with_current_denial_is_not_dropped():
    assert observed(
        ev("Recommended Milestone 1B prompt (not executed); Milestone 1B not implemented")
    ).conflicts


def test_exact_twelve_manifest_roots_ignore_nested_and_stale_snapshot(
    engine, tmp_path, monkeypatch
):
    import json

    from agrosphere_orchestrator import autonomous_services as module
    from agrosphere_orchestrator.autonomous_models import AutonomousRequest
    from agrosphere_orchestrator.config.settings import Settings
    from agrosphere_orchestrator.recovery import current_snapshot, reconcile
    from agrosphere_orchestrator.recovery_models import RecoveredMilestone, RecoverySnapshot

    roots = [tmp_path / f"repo-{i}" for i in range(12)]
    for root in roots:
        root.mkdir()
    (roots[0] / "fixtures/fake/.git").mkdir(parents=True)
    manifest = tmp_path / "repositories.json"
    manifest.write_text(
        json.dumps(
            {"repositories": [{"id": r.name, "path": str(r), "status": "confirmed"} for r in roots]}
        )
    )
    stale = RecoverySnapshot(
        workspace=str(tmp_path),
        repositories=[],
        milestones=[RecoveredMilestone(id="1B", conflicts=["stale"])],
    )
    stale_id = reconcile(engine, stale)
    calls = []

    def collect(root):
        calls.append(root)
        return {
            "id": root.name,
            "path": str(root),
            "is_git": True,
            "source_files": [],
            "test_files": [],
        }, []

    monkeypatch.setattr(module, "collect_repository", collect)
    svc = module.ExistingServices(
        engine, Settings(_env_file=None, workspace_root=tmp_path, repository_manifest=manifest)
    )
    fresh = svc.discover(AutonomousRequest(milestone="2"))
    assert calls == roots and len(fresh["snapshot"]["repositories"]) == 12
    assert fresh["discovery_consistent"] and not fresh["conflicts"]
    assert current_snapshot(engine, tmp_path)[0] == stale_id
    fresh_id = reconcile(engine, RecoverySnapshot.model_validate(fresh["snapshot"]))
    assert fresh_id != stale_id and current_snapshot(engine, tmp_path)[0] == fresh_id


def test_existing_run_resume_reobserves_and_keeps_conflict_checkpoint(engine, tmp_path):
    import asyncio

    from agrosphere_orchestrator.autonomous import AutonomousMilestoneController
    from agrosphere_orchestrator.autonomous_models import AutonomousRequest
    from agrosphere_orchestrator.autonomous_services import ExistingServices
    from agrosphere_orchestrator.autonomous_store import report
    from agrosphere_orchestrator.config.settings import Settings

    class Observed(ExistingServices):
        calls = 0

        def discover(self, request):
            self.calls += 1
            return {"conflicts": ["1B"], "discovery_consistent": False}

    settings = Settings(_env_file=None)
    svc = Observed(engine, settings)
    controller = AutonomousMilestoneController(engine, settings, svc)
    identity = "ba0851d4-66bc-417a-851b-f08176bd8061"
    controller.start(AutonomousRequest(milestone="2", mode="local"), identity)
    first = asyncio.run(controller.advance(identity))
    assert first["checkpoint"]["category"] == "discovery-conflict"
    second = asyncio.run(controller.resume(identity))
    assert second["run_id"] == identity and svc.calls == 2
    assert second["checkpoint"]["category"] == "discovery-conflict"
    assert len(second["events"]) > len(first["events"])
    assert second["usage"]["invocations"] == 0
    assert report(engine, identity)["request_hash"] == first["request_hash"]
