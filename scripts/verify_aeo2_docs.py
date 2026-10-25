"""Validate immutable documentation references and record render availability."""

import hashlib
import json
from pathlib import Path

from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.design import observe_documentation_bundle
from agrosphere_orchestrator.design_artifacts import LocalPlantUML, source_findings
from agrosphere_orchestrator.persistence import now
from agrosphere_orchestrator.recovery import recovery_engine

ROOT = Path(__file__).resolve().parents[1]


def main():
    pointer = json.loads((ROOT / "docs/aeo-2/CURRENT_BUNDLE.json").read_text(encoding="utf-8"))
    path = (ROOT / pointer["manifest"]).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Documentation manifest escaped project root")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    settings = Settings()
    results = []
    for item in manifest["artifacts"]:
        source = (ROOT / item["relative_file_path"]).resolve()
        if (
            not source.is_relative_to(ROOT)
            or hashlib.sha256(source.read_bytes()).hexdigest() != item["content_hash"]
        ):
            raise ValueError("Documentation content changed without a new revision")
        if source.suffix == ".puml":
            text = source.read_text(encoding="utf-8")
            if source_findings(text):
                raise ValueError("Invalid diagram structure/directives: " + str(source))
            svg, findings = LocalPlantUML(settings.plantuml_jar, settings.java_executable).render(
                text
            )
            rendered = None
            if svg is not None:
                rendered = (
                    ROOT
                    / "docs/validation/aeo2-rendered"
                    / manifest["revision_id"]
                    / (source.stem + ".svg")
                )
                rendered.parent.mkdir(parents=True, exist_ok=True)
                rendered.write_text(svg, encoding="utf-8")
            results.append(
                {
                    "source": item["relative_file_path"],
                    "rendered": str(rendered) if rendered else None,
                    "findings": [f.model_dump() for f in findings],
                }
            )
    engine = recovery_engine(settings.database_url)
    try:
        observation = observe_documentation_bundle(engine, ROOT, manifest)
    finally:
        engine.dispose()
    output = {
        "executed_at": now(),
        "revision_id": manifest["revision_id"],
        "artifact_count": len(manifest["artifacts"]),
        "hashes_and_ownership_valid": True,
        "observation_reference": observation,
        "approval_granted": False,
        "diagrams": results,
    }
    (ROOT / "docs/validation/aeo2-docs.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "artifacts": len(manifest["artifacts"]),
                "diagrams": len(results),
                "persisted_observation": observation,
                "rendered": sum(bool(r["rendered"]) for r in results),
                "approval_granted": False,
            },
            indent=2,
        )
    )
    return int(settings.plantuml_jar is not None and any(not r["rendered"] for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
