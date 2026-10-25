"""No model calls: record CLI/SDK features and a temporary native isolation canary."""

import json
from pathlib import Path
from uuid import uuid4

from agrosphere_orchestrator.codex_runtime import doctor, executable, permission_arguments
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.execution_models import ExecutionMode, ExecutionRequest
from agrosphere_orchestrator.execution_process import Redactor
from agrosphere_orchestrator.execution_workspace import probe_isolation
from agrosphere_orchestrator.persistence import now

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = Settings()
    status = doctor(settings)
    identity = "isolation-doctor-" + str(uuid4())
    directory = settings.execution_root.resolve() / identity
    workspace = directory / "fixture"
    workspace.mkdir(parents=True)
    request = ExecutionRequest(
        project_id="fixture",
        milestone_id="fixture",
        task_id="fixture",
        agent_role="developer",
        repository="fixture",
        worktree_path=str(workspace),
        allowed_file_scopes=["generated"],
        instructions="No model is invoked by this diagnostic",
        acceptance_criteria=["OS canary enforces literal scopes"],
        mode="WORKTREE_WRITE",
        source_head="fixture",
        context_digest="fixture",
        design_revision="fixture",
    )
    isolation = {"verified": False}
    try:
        result = probe_isolation(
            executable(settings), request, permission_arguments(request), directory
        )
        readonly = request.model_copy(update={"mode": ExecutionMode.READ_ONLY})
        read_result = probe_isolation(
            executable(settings), readonly, permission_arguments(readonly), directory
        )
        validation = request.model_copy(update={"mode": ExecutionMode.VALIDATION_ONLY})
        validation_result = probe_isolation(
            executable(settings), validation, permission_arguments(validation), directory
        )
        isolation = {
            "verified": True,
            **result,
            "read_only": read_result,
            "validation_only": validation_result,
        }
    except Exception as exc:
        isolation["finding"] = Redactor().clean(str(exc))
    output = {
        "executed_at": now(),
        "doctor": status.model_dump(),
        "native_isolation": isolation,
        "live_model_called": False,
        "live_integration_verified": False,
    }
    (ROOT / "docs/validation/codex-runtime.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "version": status.version,
                "exec_supported": status.exec_supported,
                "mcp_supported": status.mcp_supported,
                "authenticated": status.authenticated,
                "native_isolation": isolation,
                "live_model_called": False,
            },
            indent=2,
        )
    )
    return int(not status.exec_supported)


if __name__ == "__main__":
    raise SystemExit(main())
