"""Validate and render draft review sources through the existing safe renderer."""
import json
from pathlib import Path
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design_artifacts import LocalPlantUML
s = Settings()
renderer = LocalPlantUML(s.plantuml_jar, s.java_executable)
root = Path("docs/milestones/AEO-6")
results = []
for source in sorted((root / "diagrams").glob("*.puml")):
    svg, findings = renderer.render(source.read_text(encoding="utf-8"))
    results.append({"path": str(source), "passed": svg is not None and not findings, "findings": [f.model_dump() for f in findings]})
    if svg:
        source.with_suffix(".svg").write_text(svg, encoding="utf-8")
(root / "evidence/diagram-validation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
raise SystemExit(int(any(not r["passed"] for r in results)))
