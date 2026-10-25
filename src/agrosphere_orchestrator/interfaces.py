from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .execution_models import ExecutionRequest, HealthStatus
    from .execution_process import ProcessOutcome

from .models import TaskSpec


class AgentExecutor(Protocol):
    """AEO-2 adapter seam for OpenAI Agents SDK; never called in AEO-1."""

    def execute(self, task: TaskSpec) -> str: ...


class CodexWorkspace(Protocol):
    """Future isolated Codex workspace adapter. No concrete implementation in AEO-1."""

    def prepare(self, repository_id: str, run_id: str) -> str: ...


class CodingAgentExecutor(Protocol):
    """AEO-2 async transport; execution.run_execution returns normalized ExecutionResult."""

    name: str

    async def execute(self, request: "ExecutionRequest", prompt: str, directory: Path,
                      **callbacks) -> "ProcessOutcome": ...
    async def continue_execution(self, session_id: str, request: "ExecutionRequest", prompt: str,
                                 directory: Path, **callbacks) -> "ProcessOutcome": ...
    async def health_check(self) -> "HealthStatus": ...
