"""Execute validations and retain exact argv, exit codes and complete output."""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from agrosphere_orchestrator.design_models import AsBuiltInput, DesignInput
from agrosphere_orchestrator.execution_models import (
    AgentOutput,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionResult,
)
from agrosphere_orchestrator.models import MilestoneSpec, TaskSpec

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    evidence_dir = ROOT / "docs/validation"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    schema_dir = ROOT / "docs/schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    for name, model in (
        ("milestone", MilestoneSpec),
        ("task", TaskSpec),
        ("design-input", DesignInput),
        ("as-built-input", AsBuiltInput),
        ("execution-request", ExecutionRequest),
        ("execution-result", ExecutionResult),
        ("agent-output", AgentOutput),
        ("execution-policy", ExecutionPolicy),
    ):
        (schema_dir / f"{name}.schema.json").write_text(
            json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8"
        )
    commands = [
        [sys.executable, "-m", "pytest", "-v", "--junitxml=docs/validation/pytest.xml"],
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "ruff", "format", "--check", "."],
        [sys.executable, "-m", "pip", "check"],
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        [sys.executable, "-m", "alembic", "check"],
        [sys.executable, "-m", "agrosphere_orchestrator.cli", "project-status"],
        [sys.executable, "-m", "agrosphere_orchestrator.cli", "repository-inspect"],
        [
            sys.executable,
            "-m",
            "agrosphere_orchestrator.cli",
            "milestone-validate",
            "examples/aeo-1.yaml",
        ],
        [
            sys.executable,
            "-m",
            "agrosphere_orchestrator.cli",
            "milestone",
            "design-status",
            "AEO-1C",
        ],
        [sys.executable, "scripts/verify_design_tools.py"],
        [sys.executable, "-m", "agrosphere_orchestrator.cli", "agents", "list"],
        [sys.executable, "-m", "agrosphere_orchestrator.cli", "agents", "describe", "developer"],
        [sys.executable, "scripts/verify_aeo2_docs.py"],
        [sys.executable, "scripts/codex_live_smoke.py"],
        [sys.executable, "-m", "pip", "freeze"],
    ]
    results = []
    for argv in commands:
        completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=300)
        result = {
            "argv": argv,
            "cwd": str(ROOT),
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        results.append(result)
        print(f"exit={completed.returncode}: {' '.join(argv)}")
        if completed.returncode:
            print(completed.stdout, completed.stderr)
    output = {
        "executed_at": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "commands": results,
    }
    (evidence_dir / "commands.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    return int(any(result["exit_code"] for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
