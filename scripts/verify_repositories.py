"""Local bootstrap evidence; inspect siblings read-only and update only AEO manifest."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from agrosphere_orchestrator.configuration import RepositoryManifest, load_yaml
from agrosphere_orchestrator.repositories import inspect_repository

ROOT = Path(__file__).resolve().parents[1]


def snapshot(path: Path) -> dict[str, str]:
    return {
        str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in path.rglob("*")
        if p.is_file()
    }


def main():
    manifest_path = ROOT / "config/repositories.yaml"
    manifest = load_yaml(manifest_path, RepositoryManifest)
    evidence = []
    for declared, resolved in zip(
        manifest.repositories, manifest.resolve(manifest_path), strict=True
    ):
        marker = resolved.path / ".git"
        if not marker.is_dir():
            raise RuntimeError(f"bootstrap verifier expects ordinary Git directory: {marker}")
        before = snapshot(marker)
        result = inspect_repository(resolved)
        after = snapshot(marker)
        unchanged = before == after
        evidence.append(
            {
                **result.model_dump(),
                "metadata_files": len(before),
                "git_metadata_unchanged": unchanged,
                "metadata_digest_before": hashlib.sha256(
                    json.dumps(before, sort_keys=True).encode()
                ).hexdigest(),
                "metadata_digest_after": hashlib.sha256(
                    json.dumps(after, sort_keys=True).encode()
                ).hexdigest(),
            }
        )
        if result.error or not result.is_git or not unchanged:
            raise RuntimeError(f"repository verification failed: {resolved.id}")
        declared.status = "confirmed"
    # This is the new orchestrator's manifest, never an existing repository file.
    manifest_path.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    output = ROOT / "docs/validation/repositories.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {"verified_at": datetime.now(UTC).isoformat(), "repositories": evidence}, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Verified {len(evidence)} repositories; all Git metadata unchanged")


if __name__ == "__main__":
    main()
