"""Prove migration 0004 preserves every pre-existing table row."""

import hashlib
import json
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.persistence import now
from agrosphere_orchestrator.recovery import recovery_engine

ROOT = Path(__file__).resolve().parents[1]


def snapshot(engine, tables):
    output = {}
    with engine.connect() as connection:
        for name in tables:
            rows = [
                list(row) for row in connection.execute(text(f'SELECT * FROM "{name}" ORDER BY 1'))
            ]
            output[name] = {
                "rows": len(rows),
                "sha256": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            }
    return output


def main():
    engine = recovery_engine(Settings().database_url)
    try:
        tables = [name for name in inspect(engine).get_table_names() if name != "alembic_version"]
        before = snapshot(engine, tables)
        config = Config(str(ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(ROOT / "migrations"))
        command.upgrade(config, "head")
        after = snapshot(engine, tables)
        assert before == after, "Existing state changed during additive migration"
        output = {
            "executed_at": now(),
            "existing_records_unchanged": True,
            "before": before,
            "after": after,
        }
        (ROOT / "docs/validation/execution-upgrade.json").write_text(
            json.dumps(output, indent=2), encoding="utf-8"
        )
        print(json.dumps({"tables_preserved": len(tables), "existing_records_unchanged": True}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
