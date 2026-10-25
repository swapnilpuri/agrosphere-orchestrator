"""Record real diagram-tool availability and outcomes without requiring tool installation."""

import json
import shutil
import subprocess
from pathlib import Path

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design_artifacts import LocalPlantUML, digest
from agrosphere_orchestrator.persistence import now

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = Settings()
    source = (ROOT / "docs/diagrams/design-lifecycle.puml").read_text(encoding="utf-8")
    java = shutil.which(settings.java_executable)
    version = None
    if java:
        result = subprocess.run([java, "-version"], capture_output=True, text=True, timeout=15)
        version = {
            "argv": [java, "-version"],
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    svg, findings = LocalPlantUML(settings.plantuml_jar, settings.java_executable).render(source)
    if svg is not None:
        (ROOT / "docs/diagrams/design-lifecycle.svg").write_text(svg, encoding="utf-8")
    output = {
        "executed_at": now(),
        "source": "docs/diagrams/design-lifecycle.puml",
        "source_sha256": digest(source),
        "java": version,
        "plantuml_jar": str(settings.plantuml_jar) if settings.plantuml_jar else None,
        "rendered": svg is not None,
        "design_approval_blocked": svg is None,
        "findings": [f.model_dump() for f in findings],
    }
    (ROOT / "docs/validation/design-tools.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output, indent=2))
    # Missing optional installation is recorded, never disguised as a successful render.
    # A configured renderer that fails is a failed validation command.
    return int(settings.plantuml_jar is not None and svg is None)


if __name__ == "__main__":
    raise SystemExit(main())
