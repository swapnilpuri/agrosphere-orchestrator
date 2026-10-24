import hashlib
import subprocess
from pathlib import Path

import pytest

from agrosphere_orchestrator.configuration import Repository
from agrosphere_orchestrator.repositories import discover, inspect_repository

ROOT = Path(__file__).resolve().parents[2]


def test_missing_and_non_git(tmp_path):
    missing = inspect_repository(Repository(id="missing", path=tmp_path / "missing"))
    assert not missing.exists and "missing" in missing.error
    ordinary = inspect_repository(Repository(id="ordinary", path=tmp_path))
    assert ordinary.exists and not ordinary.is_git
    assert discover(tmp_path) == []


def snapshot_git(path):
    # Hash every metadata file, including index, refs, logs, configuration and objects.
    return {
        str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in path.rglob("*")
        if p.is_file()
    }


def test_existing_repository_inspection_preserves_git_state():
    candidates = [p for p in ROOT.glob("agrosphere-*") if (p / ".git").is_dir()]
    if not candidates:
        pytest.skip("no existing local AgroSphere repository available")
    path = sorted(candidates)[0]
    before = snapshot_git(path / ".git")
    result = inspect_repository(Repository(id=path.name, path=path, status="confirmed"))
    after = snapshot_git(path / ".git")
    assert result.is_git and result.error is None
    assert before == after


def test_git_failure_reported(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()

    def fail(*args, **kwargs):
        raise subprocess.TimeoutExpired("git", 15)

    monkeypatch.setattr(subprocess, "run", fail)
    result = inspect_repository(Repository(id="test", path=tmp_path))
    assert result.error and not result.is_git
