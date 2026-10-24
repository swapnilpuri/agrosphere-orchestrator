import os
import subprocess
from pathlib import Path

from .configuration import Repository
from .models import StrictModel


class Inspection(StrictModel):
    id: str
    path: str
    declared_status: str
    exists: bool
    is_git: bool
    branch: str | None = None
    head: str | None = None
    status: str | None = None
    error: str | None = None


def inspect_repository(repo: Repository) -> Inspection:
    path = repo.path.resolve()
    result = Inspection(
        id=repo.id, path=str(path), declared_status=repo.status, exists=path.is_dir(), is_git=False
    )
    if not result.exists:
        result.error = "missing repository path"
        return result
    if not (path / ".git").exists():
        result.error = "no Git marker at configured repository root"
        return result
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}

    def git(*args: str) -> str:
        completed = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(path), *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
            env=env,
        )
        return completed.stdout.strip()

    try:
        git("rev-parse", "--git-dir")
        result.is_git = True
        # Unborn repositories have no HEAD; preserve the rest of the inspection.
        try:
            result.head = git("rev-parse", "--verify", "HEAD")
        except subprocess.CalledProcessError:
            result.head = None
        result.branch = (
            git("symbolic-ref", "--quiet", "--short", "HEAD")
            if result.head is None
            else git("rev-parse", "--abbrev-ref", "HEAD")
        )
        result.status = git(
            "-c",
            "core.fsmonitor=false",
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
            "--ignore-submodules=all",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        result.error = str(exc)
    return result


def discover(root: Path) -> list[Inspection]:
    return [
        inspect_repository(Repository(id=child.name, path=child, status="unverified"))
        for child in sorted(root.iterdir())
        if child.is_dir() and (child / ".git").exists()
    ]
