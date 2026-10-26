"""The additive delivery migration preserves AEO-1 through AEO-4 evidence."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from agrosphere_orchestrator.persistence import AuditEvent, Task, import_plan, make_engine
from agrosphere_orchestrator.quality_store import blob, read_blob, record


def test_0007_preserves_0006_records_and_rejects_destructive_downgrade(tmp_path, monkeypatch, plan):
    root = Path(__file__).resolve().parents[1]
    url = "sqlite:///" + (tmp_path / "upgrade.db").as_posix()
    monkeypatch.setenv("AEO_DATABASE_URL", url)
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    command.upgrade(config, "0006")
    engine = make_engine(url)
    try:
        task = import_plan(engine, plan)[0]
        with Session(engine) as session, session.begin():
            milestone = session.get(Task, task).milestone_id
            identity = blob(session, {"preserved": "quality fixture"})
            record(session, milestone, "fixture", {"evidence": identity})
        with Session(engine) as session:
            before = [(a.id, a.kind, a.payload) for a in session.scalars(select(AuditEvent))]
        command.upgrade(config, "0007")
        with Session(engine) as session:
            assert [
                (a.id, a.kind, a.payload) for a in session.scalars(select(AuditEvent))
            ] == before
            assert read_blob(session, identity) == {"preserved": "quality fixture"}
            assert session.get(Task, task).state == "pending"
            assert (
                session.execute(text("select version_num from alembic_version")).scalar() == "0007"
            )
        command.upgrade(config, "head")
        command.check(config)
        with pytest.raises(RuntimeError, match="retained"):
            command.downgrade(config, "0006")
    finally:
        engine.dispose()
