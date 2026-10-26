"""Upgrade every existing 0007 table without modifying its records or audit history."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from agrosphere_orchestrator.persistence import import_plan, make_engine


def test_0008_preserves_all_0007_tables_and_records(tmp_path, monkeypatch, plan):
    root = Path(__file__).resolve().parents[1]
    database = "sqlite:///" + (tmp_path / "upgrade.db").as_posix()
    monkeypatch.setenv("AEO_DATABASE_URL", database)
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    command.upgrade(config, "0007")
    engine = make_engine(database)
    try:
        import_plan(engine, plan)
        tables = set(inspect(engine).get_table_names())
        assert len(tables) == 29

        def snapshot():
            with engine.connect() as connection:
                return {
                    name: list(connection.execute(text('SELECT * FROM "' + name + '"')))
                    for name in tables
                    if name != "alembic_version"
                }

        before = snapshot()
        command.upgrade(config, "head")
        assert snapshot() == before
        assert set(inspect(engine).get_table_names()) - tables == {
            "autonomous_runs",
            "autonomous_operations",
            "autonomous_events",
        }
        command.check(config)
        with pytest.raises(RuntimeError, match="retained"):
            command.downgrade(config, "0007")
    finally:
        engine.dispose()
