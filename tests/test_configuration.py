import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.configuration import (
    ApprovalPolicy,
    RepositoryManifest,
    RoleRegistry,
    load_yaml,
)

ROOT = Path(__file__).resolve().parents[1]


def test_settings_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("AEO_DATABASE_URL", "sqlite:///custom.db")
    monkeypatch.setenv("AEO_REPOSITORY_MANIFEST", str(tmp_path / "repos.yaml"))
    settings = Settings(_env_file=None)
    assert settings.database_url == "sqlite:///custom.db"
    assert settings.repository_manifest == tmp_path / "repos.yaml"


def test_registry_and_policy():
    roles = load_yaml(ROOT / "config/roles.yaml", RoleRegistry).by_id()
    assert len(roles) == 9
    assert roles["developer"].specializations == [
        "java",
        "python",
        "angular",
        "data-postgis",
        "integration",
    ]
    policy = load_yaml(ROOT / "config/approvals.yaml", ApprovalPolicy)
    assert policy.requires("deploy") and policy.requires("unknown")


def test_manifest_relative_resolution(tmp_path):
    path = tmp_path / "manifest.yaml"
    path.write_text(json.dumps({"repositories": [{"id": "repo", "path": "../repo"}]}))
    manifest = load_yaml(path, RepositoryManifest)
    assert manifest.resolve(path)[0].path == (tmp_path / "../repo").resolve()
    manifest.repositories.append(manifest.repositories[0])
    with pytest.raises(ValueError, match="duplicate"):
        manifest.resolve(path)


def test_bad_yaml_and_extra_fields(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("repositories: []\nexecute: true\n")
    with pytest.raises(ValidationError):
        load_yaml(path, RepositoryManifest)


def test_unknown_handoff():
    roles = load_yaml(ROOT / "config/roles.yaml", RoleRegistry)
    roles.roles[0].handoffs = ["missing"]
    with pytest.raises(ValueError, match="handoff"):
        roles.by_id()
