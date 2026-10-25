from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from agrosphere_orchestrator.configuration import ApprovalPolicy
from agrosphere_orchestrator.models import MilestoneSpec
from agrosphere_orchestrator.persistence import make_engine

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def engine(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "test.db").as_posix()
    monkeypatch.setenv("AEO_DATABASE_URL", url)
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(config, "head")
    engine = make_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def plan():
    return MilestoneSpec.model_validate(
        {
            "id": "AEO-1",
            "project": "agrosphere",
            "title": "Foundation",
            "tasks": [
                {
                    "id": "first",
                    "title": "Inspect",
                    "repository": "repo",
                    "role": "developer",
                    "operation": "inspect",
                    "acceptance_criteria": ["reviewed"],
                },
                {
                    "id": "second",
                    "title": "Review",
                    "repository": "repo",
                    "role": "qa-engineer",
                    "operation": "validate",
                    "depends_on": ["first"],
                    "acceptance_criteria": ["verified"],
                },
            ],
        }
    )


@pytest.fixture
def policy():
    return ApprovalPolicy(
        required_operations=["code-write"],
        approvers=["human"],
        exempt_operations=["inspect", "validate"],
    )


@pytest.fixture(autouse=True)
def restore_logging_after_cli_tests():
    # CliRunner closes its captured stderr; keep that handler out of later migrations/tests.
    import logging

    logger = logging.getLogger()
    handlers, level = list(logger.handlers), logger.level
    yield
    logger.handlers = handlers
    logger.setLevel(level)
