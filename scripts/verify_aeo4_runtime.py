"""No model/network/install: probe the actual read-only native quality adapter on a fixture."""

import asyncio
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.execution_models import ValidationCommand
from agrosphere_orchestrator.persistence import now
from agrosphere_orchestrator.quality_adapters import SandboxedValidator
from agrosphere_orchestrator.quality_models import Gate

ROOT = Path(__file__).resolve().parents[1]


async def main():
    settings = Settings()
    settings.execution_root = ROOT / ".aeo/quality-runtime-probe"
    settings.execution_root.mkdir(parents=True, exist_ok=True)
    result = {"executed_at": now(), "model_invoked": False, "scanner_invoked": False}
    with tempfile.TemporaryDirectory(dir=settings.execution_root, prefix="fixture-") as folder:
        repository = Path(folder)
        (repository / "fixture.txt").write_text("quality adapter fixture only")
        gate = Gate(
            id="native-fixture",
            type="test",
            repository="fixture",
            command="fixture",
            validator_version="python-" + sys.version.split()[0],
        )
        command = ValidationCommand(
            id="fixture",
            read_paths=[str(Path(sys.executable).parent.parent), sys.base_prefix],
            argv=[
                sys.executable,
                "-c",
                "from pathlib import Path; assert Path('fixture.txt').read_text() == 'quality adapter fixture only'; print('native fixture passed')",
            ],
        )
        result["argv"] = command.argv
        result["runtime_reads"] = command.read_paths
        try:
            outcome = await SandboxedValidator(settings).evaluate(gate, repository, command)
            result.update(
                state="PASSED"
                if outcome["exit_code"] == 0 and not outcome.get("timed_out")
                else "FAILED",
                outcome=outcome,
            )
        except Exception as exc:
            result.update(state="BLOCKED", error=str(exc))
    raw = json.dumps(result, sort_keys=True, indent=2) + "\n"
    history = ROOT / "docs/validation/aeo4-runtime-history"
    history.mkdir(parents=True, exist_ok=True)
    target = history / (hashlib.sha256(raw.encode()).hexdigest() + ".json")
    if not target.exists():
        target.write_text(raw)
    (ROOT / "docs/validation/aeo4-runtime.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return int(result["state"] != "PASSED")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
