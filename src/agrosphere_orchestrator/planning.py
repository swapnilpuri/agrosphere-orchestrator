from pathlib import Path

from .configuration import RepositoryManifest, RoleRegistry, load_yaml
from .models import MilestoneSpec
from .repositories import inspect_repository


def validate_plan(path: Path, manifest_path: Path, registry_path: Path) -> MilestoneSpec:
    spec = load_yaml(path, MilestoneSpec)
    repositories = {
        repo.id: repo
        for repo in load_yaml(manifest_path, RepositoryManifest).resolve(manifest_path)
    }
    roles = load_yaml(registry_path, RoleRegistry).by_id()
    for task in spec.tasks:
        if task.repository not in repositories:
            raise ValueError(f"unknown repository: {task.repository}")
        repo = repositories[task.repository]
        if repo.status != "confirmed":
            raise ValueError(f"unverified repository: {repo.id}")
        inspection = inspect_repository(repo)
        if not inspection.is_git or inspection.error:
            raise ValueError(f"unavailable repository: {repo.id}: {inspection.error}")
        if task.role not in roles:
            raise ValueError(f"unknown role: {task.role}")
        if task.operation not in roles[task.role].allowed_operations:
            raise ValueError(f"role {task.role} cannot perform {task.operation}")
    return spec
