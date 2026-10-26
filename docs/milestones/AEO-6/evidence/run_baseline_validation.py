"""Run the required validator on a disposable SQLite backup; retain all command evidence."""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from sqlalchemy.engine import make_url
from agrosphere_orchestrator.config.settings import Settings

root = Path.cwd()
out = root / "docs/milestones/AEO-6/evidence/baseline-validation"
out.mkdir(parents=True, exist_ok=True)
for relative in ("docs/validation/commands.json", "docs/validation/pytest.xml"):
    source = root / relative
    if source.is_file():
        archived = out / ("prior-" + source.name)
        if not archived.exists():
            shutil.copyfile(source, archived)
settings = Settings()
original = Path(make_url(settings.database_url).database).resolve()
with tempfile.TemporaryDirectory(prefix="aeo6-baseline-") as directory:
    backup = Path(directory) / "validation.db"
    with sqlite3.connect(original.as_uri() + "?mode=ro", uri=True) as source, sqlite3.connect(backup) as target:
        source.backup(target)
    source.close()
    target.close()
    env = os.environ.copy()
    env["AEO_DATABASE_URL"] = "sqlite:///" + backup.as_posix()
    env["AEO_PLANTUML_JAR"] = str(root / ".aeo/tools/plantuml-1.2026.9.jar")
    fixture_root = Path(tempfile.gettempdir()) / ("a6-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    if fixture_root.exists():
        raise RuntimeError("Fresh test fixture directory required")
    env["PYTEST_ADDOPTS"] = env.get("PYTEST_ADDOPTS", "") + " --basetemp=" + fixture_root.as_posix()
    argv = [sys.executable, "scripts/validate.py"]
    completed = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, timeout=2400)
    result = {"executed_at": datetime.now(UTC).isoformat(), "argv": argv, "fixture_root": str(fixture_root), "cwd": str(root), "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "database": "Disposable SQLite backup; authoritative database not migrated or modified by validation."}
    (out / "runner.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for name in ("commands.json", "pytest.xml"):
        source = root / "docs/validation" / name
        if source.exists():
            shutil.copyfile(source, out / name)
    print(json.dumps(result, indent=2))
    raise SystemExit(completed.returncode)
