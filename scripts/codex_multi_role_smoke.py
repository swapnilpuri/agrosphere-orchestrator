"""Explicit opt-in transport smoke for developer, QA and security roles; not a scheduler proof."""

import argparse
import asyncio
import json
import tempfile
from pathlib import Path

from codex_live_smoke import run

from agrosphere_orchestrator.codex_runtime import (
    CodexExecutor,
    executable,
    parse_output,
    permission_arguments,
)
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.execution_models import ExecutionRequest
from agrosphere_orchestrator.execution_workspace import git, probe_isolation
from agrosphere_orchestrator.human_approval import WindowsConsoleHumanVerifier


async def smoke(settings, directory):
    developer = await run(settings, directory)
    worktree = directory / "worktree"
    reviews = []
    for role in ("qa-engineer", "security-engineer"):
        request = ExecutionRequest(
            project_id="fixture",
            milestone_id="MULTI-ROLE-SMOKE",
            task_id=role,
            agent_role=role,
            repository="temporary-fixture",
            worktree_path=str(worktree),
            allowed_file_scopes=["."],
            instructions="Read generated/hello.txt and report whether it contains hello plus newline. Return AgentOutput JSON. Do not modify files.",
            acceptance_criteria=["Read-only review of temporary generated artifact"],
            source_head=git(worktree, "rev-parse", "HEAD"),
            context_digest="transport-smoke-only",
            design_revision="transport-fixture-only",
        )
        actor = WindowsConsoleHumanVerifier().verify(
            "Multi-role smoke billing/permissions:" + request.model_dump_json(), "approved"
        )
        if actor not in settings.execution_approvers:
            raise PermissionError("Authenticated execution approver required")
        role_directory = directory / role
        role_directory.mkdir()
        probe_isolation(
            executable(settings), request, permission_arguments(request), role_directory
        )
        outcome = await CodexExecutor(settings).execute(
            request, request.instructions, role_directory
        )
        if outcome.exit_code or outcome.timed_out or outcome.cancelled:
            raise RuntimeError("Live review failed; no success inferred")
        output, session, usage = parse_output(outcome.stdout)
        reviews.append(
            {"role": role, "output": output.model_dump(), "session_id": session, "usage": usage}
        )
    result = {
        "transport_only": True,
        "scheduler_verified_live": False,
        "live_concurrency_verified": False,
        "developer": developer,
        "reviews": reviews,
    }
    (directory / "multi-role-result.json").write_text(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        print("SKIPPED: explicit --live and authenticated human grants required")
        return 0
    settings = Settings()
    settings.execution_root.mkdir(parents=True, exist_ok=True)
    directory = Path(
        tempfile.mkdtemp(prefix="multi-role-smoke-", dir=settings.execution_root.resolve())
    )
    print(json.dumps(asyncio.run(smoke(settings, directory)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
