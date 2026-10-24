from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$", max_length=128)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaskState(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskSpec(StrictModel):
    id: Identifier
    title: str = Field(min_length=1)
    repository: Identifier
    role: Identifier
    operation: Identifier = "plan"
    depends_on: list[Identifier] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(min_length=1)


class MilestoneSpec(StrictModel):
    id: Identifier
    project: Identifier
    title: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    tasks: list[TaskSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        graph = {task.id: task.depends_on for task in self.tasks}
        if len(graph) != len(self.tasks):
            raise ValueError("duplicate task IDs")
        visiting, visited = set(), set()

        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError(f"circular dependency at {node}")
            if node in visited:
                return
            visiting.add(node)
            deps = graph[node]
            if len(deps) != len(set(deps)):
                raise ValueError(f"duplicate dependencies at {node}")
            for dependency in deps:
                if dependency not in graph:
                    raise ValueError(f"unknown dependency: {dependency}")
                visit(dependency)
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)
        return self
