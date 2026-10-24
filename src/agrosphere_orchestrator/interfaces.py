from typing import Protocol

from .models import TaskSpec


class AgentExecutor(Protocol):
    """AEO-2 adapter seam for OpenAI Agents SDK; never called in AEO-1."""

    def execute(self, task: TaskSpec) -> str: ...


class CodexWorkspace(Protocol):
    """Future isolated Codex workspace adapter. No concrete implementation in AEO-1."""

    def prepare(self, repository_id: str, run_id: str) -> str: ...
