"""Apply the additive migration and retain before/after preservation evidence."""

import hashlib
import json
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.persistence import now
from agrosphere_orchestrator.recovery import recovery_engine

ROOT = Path(__file__).resolve().parents[1]
TABLES = (
    "projects",
    "milestones",
    "tasks",
    "runs",
    "approvals",
    "audit_events",
    "recovery_snapshots",
    "recovery_heads",
)


def snapshot(engine):
    with engine.connect() as connection:
        output = {}
        for table in TABLES:
            rows = [
                list(row) for row in connection.execute(text(f"SELECT * FROM {table} ORDER BY 1"))
            ]
            output[table] = {
                "rows": len(rows),
                "sha256": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            }
        return output


def main():
    engine = recovery_engine(Settings().database_url)
    try:
        before = snapshot(engine)
        config = Config(str(ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(ROOT / "migrations"))
        command.upgrade(config, "head")
        after = snapshot(engine)
        assert before == after, "Migration changed existing foundation/recovery records"
        with engine.connect() as connection:
            designs = connection.scalar(text("SELECT count(*) FROM design_cases"))
        output = {
            "executed_at": now(),
            "before": before,
            "after": after,
            "existing_records_unchanged": True,
            "design_case_count": designs,
        }
        (ROOT / "docs/validation/design-upgrade.json").write_text(
            json.dumps(output, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(output, indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
