"""Explicit opt-in transport-only smoke. Never run by the normal validation suite."""

import argparse
import asyncio
import hashlib
import json
import tempfile
from pathlib import Path
from uuid import uuid4

from agrosphere_orchestrator.codex_runtime import (
    CodexExecutor,
    executable,
    parse_output,
    permission_arguments,
)
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.configuration import RepositoryManifest, load_yaml
from agrosphere_orchestrator.execution_models import ExecutionRequest
from agrosphere_orchestrator.execution_process import Redactor
from agrosphere_orchestrator.execution_workspace import create_worktree, git, probe_isolation
from agrosphere_orchestrator.human_approval import WindowsConsoleHumanVerifier
from agrosphere_orchestrator.persistence import now
from agrosphere_orchestrator.repositories import inspect_repository


def application_state(settings):
    result = {}
    for repo in load_yaml(settings.repository_manifest, RepositoryManifest).resolve(
        settings.repository_manifest
    ):
        inspection = inspect_repository(repo)
        result[repo.id] = {
            "head": inspection.head,
            "status": inspection.status,
            "error": inspection.error,
        }
    return result


async def run(settings, directory):
    before = application_state(settings)
    source = directory / "fixture-source"
    source.mkdir()
    git(source, "init", "-b", "main")
    (source / "README.md").write_text("Temporary Codex smoke fixture only.\n", encoding="utf-8")
    git(source, "add", "README.md")
    git(
        source,
        "-c",
        "user.name=AEO Smoke Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-m",
        "temporary fixture",
    )
    head = git(source, "rev-parse", "HEAD")
    identity = str(uuid4())
    worktree = directory / "worktree"
    request = ExecutionRequest(
        project_id="fixture",
        milestone_id="SMOKE",
        task_id="smoke-only",
        agent_role="developer",
        repository="temporary-fixture",
        worktree_path=str(worktree),
        allowed_file_scopes=["generated"],
        instructions="Create generated/hello.txt containing exactly hello and a newline. Return only AgentOutput JSON.",
        acceptance_criteria=["generated/hello.txt equals hello plus newline"],
        mode="WORKTREE_WRITE",
        timeout_seconds=120,
        source_head=head,
        context_digest=hashlib.sha256(b"temporary smoke context").hexdigest(),
        design_revision="transport-fixture-not-an-application-design",
    )
    subject = (
        "AEO temporary-fixture smoke/billing:"
        + hashlib.sha256(request.model_dump_json().encode()).hexdigest()
    )
    actor = WindowsConsoleHumanVerifier().verify(subject, "approved")
    if actor not in settings.execution_approvers:
        raise PermissionError("Smoke requires an authorized human execution approver")
    create_worktree(source, worktree, identity, head)
    probe_isolation(executable(settings), request, permission_arguments(request), directory)
    outcome = await CodexExecutor(settings).execute(request, request.instructions, directory)
    (directory / "raw-output.jsonl").write_text(Redactor().clean(outcome.stdout), encoding="utf-8")
    (directory / "stderr.log").write_text(Redactor().clean(outcome.stderr), encoding="utf-8")
    if outcome.exit_code or outcome.timed_out or outcome.cancelled:
        raise RuntimeError("Live runtime did not complete; inspect preserved evidence")
    normalized, session_id, usage = parse_output(outcome.stdout)
    assert (worktree / "generated/hello.txt").read_bytes() == b"hello\n"
    assert not (source / "generated/hello.txt").exists()
    assert before == application_state(settings), "Original AgroSphere repository state changed"
    result = {
        "executed_at": now(),
        "transport_only": True,
        "live_integration_verified": True,
        "application_design_approval_exercised": False,
        "session_id": session_id,
        "usage": usage,
        "output": normalized.model_dump(),
        "expected_file_verified": True,
        "original_application_repositories_unchanged": True,
    }
    (directory / "live-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly opt in to credentials/quota use; interactive human authentication is still required",
    )
    args = parser.parse_args()
    if not args.live:
        print("SKIPPED: opt-in --live required; no credentials, model calls or quota used")
        return 0
    settings = Settings()
    settings.execution_root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="live-smoke-", dir=settings.execution_root.resolve()))
    try:
        result = asyncio.run(run(settings, directory))
        print(json.dumps({"evidence_directory": str(directory), **result}, indent=2))
        return 0
    except Exception as exc:
        (directory / "failure.json").write_text(
            json.dumps(
                {
                    "error": Redactor().clean(str(exc)),
                    "executed_at": now(),
                    "live_integration_verified": False,
                }
            ),
            encoding="utf-8",
        )
        print("FAILED; partial fixture/evidence preserved: " + str(directory))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
