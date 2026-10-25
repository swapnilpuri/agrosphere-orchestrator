"""Render local AEO-4 diagrams without network access or model execution."""

import json
from pathlib import Path

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design_artifacts import LocalPlantUML
from agrosphere_orchestrator.persistence import now

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = Settings()
    jar = settings.plantuml_jar or ROOT / ".aeo/tools/plantuml-1.2026.9.jar"
    renderer = LocalPlantUML(jar if jar.is_file() else None, settings.java_executable)
    results = []
    for source in sorted((ROOT / "docs/aeo-4/diagrams").glob("*.puml")):
        svg, findings = renderer.render(source.read_text(encoding="utf-8"))
        target = ROOT / "docs/validation/aeo4-rendered" / (source.stem + ".svg")
        if svg:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(svg, encoding="utf-8")
        results.append(
            {
                "source": str(source.relative_to(ROOT)),
                "rendered": bool(svg),
                "findings": [f.model_dump() for f in findings],
            }
        )
    result = {"executed_at": now(), "diagrams": results, "approval_granted": False}
    (ROOT / "docs/validation/aeo4-docs.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return int(len(results) != 6 or any(not r["rendered"] for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
