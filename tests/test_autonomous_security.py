"""Fail-closed discovery, roadmap and permission tests on isolated repositories."""

import hashlib
import json
from types import SimpleNamespace

import pytest
from test_design import design_workspace as design_workspace

from agrosphere_orchestrator.autonomous_models import AutonomousRequest
from agrosphere_orchestrator.autonomous_services import ExistingServices
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design import register_requirements
from agrosphere_orchestrator.design_models import ContextReference


@pytest.fixture
def services(engine, design_workspace):
    f = design_workspace
    f.settings = Settings(
        _env_file=None,
        repository_manifest=f.manifest,
        role_registry=f.registry,
        workspace_root=f.manifest.parent,
    )
    f.services = ExistingServices(engine, f.settings)
    return f


def test_manifest_bound_discovery_excludes_nested_fixture_repositories(services):
    f = services
    nested = f.repos["estate"] / ".aeo/fixtures/fake/.git"
    nested.mkdir(parents=True)
    found = f.services.discover(AutonomousRequest(milestone="FIXTURE-1"))
    assert len(found["snapshot"]["repositories"]) == 3
    assert not any("fake" in r["path"] for r in found["snapshot"]["repositories"])
    assert found["numeric_advancement_authorized"] is False


@pytest.mark.parametrize("kind", ["duplicate-id", "duplicate-path", "unconfirmed", "outside"])
def test_ambiguous_or_unavailable_confirmed_roots_fail_closed(services, kind, tmp_path):
    f = services
    value = json.loads(f.manifest.read_text())
    if kind == "duplicate-id":
        value["repositories"].append(value["repositories"][0])
    elif kind == "duplicate-path":
        value["repositories"][1]["path"] = value["repositories"][0]["path"]
    elif kind == "unconfirmed":
        for item in value["repositories"]:
            item["status"] = "unverified"
    else:
        f.settings.workspace_root = tmp_path / "narrow-workspace"
    f.manifest.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        f.services.discover(AutonomousRequest(milestone="FIXTURE-1"))


def prepare_roadmap(engine, f, dependencies=None):
    f.inputs.plan.project = "agrosphere"
    path = f.repos["estate"] / "roadmap.json"
    value = {"milestones": [{"id": "FIXTURE-1", "depends_on": dependencies or []}]}
    if dependencies:
        value["milestones"].append({"id": dependencies[0]})
    path.write_text(json.dumps(value))
    head = next(c.head for c in f.inputs.context if c.repository == "estate")
    f.inputs.context.append(
        ContextReference(
            repository="estate",
            path=path.name,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            head=head,
        )
    )
    register_requirements(engine, f.inputs, f.manifest, f.registry)
    f.settings.autonomous_roadmap = path
    request = AutonomousRequest(milestone="FIXTURE-1")
    return path, request, f.services.discover(request)


def test_application_requires_roadmap_bound_to_exact_registered_context(engine, services):
    f = services
    path, request, found = prepare_roadmap(engine, f)
    assert f.services.eligibility(request, found) is None
    path.write_text('{"milestones": [{"id":"FIXTURE-1","depends_on":[]}]} changed')
    assert "exact requirements" in f.services.eligibility(request, found)


def test_unverified_dependency_and_missing_roadmap_block_even_explicit_selection(engine, services):
    f = services
    path, request, found = prepare_roadmap(engine, f, ["earlier"])
    assert "formal completion" in f.services.eligibility(request, found)
    f.settings.autonomous_roadmap = None
    assert "No approved roadmap" in f.services.eligibility(request, found)


def test_missing_design_cannot_reach_scheduler(engine, services):
    f = services
    with pytest.raises((PermissionError, ValueError)):
        f.services.planning(AutonomousRequest(milestone="FIXTURE-1"))


def test_real_backend_recovery_of_uncertain_task_planning_never_replays(engine, services):
    import asyncio

    f = services
    assert (
        asyncio.run(
            f.services.recover("PLANNING_TASKS", AutonomousRequest(milestone="FIXTURE-1"), {})
        )
        is None
    )


def test_simulated_authenticator_refuses_real_database(tmp_path):
    from agrosphere_orchestrator.autonomous_simulation import IsolatedVerifier

    (tmp_path / "SIMULATION_ONLY").write_text("fixture")
    verifier = IsolatedVerifier(tmp_path, SimpleNamespace(database_url="sqlite:///aeo.db"))
    with pytest.raises(PermissionError, match="isolated"):
        verifier.verify("subject", "approved")
