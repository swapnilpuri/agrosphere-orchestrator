from pathlib import Path
from typing import Literal, TypeVar

import yaml
from pydantic import Field

from .models import Identifier, StrictModel

T = TypeVar("T", bound=StrictModel)


def load_yaml(path: Path, model: type[T]) -> T:
    return model.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


class Repository(StrictModel):
    id: Identifier
    path: Path
    status: Literal["confirmed", "unverified"] = "unverified"
    validators: dict[str, Identifier] = Field(default_factory=dict)


class RepositoryManifest(StrictModel):
    repositories: list[Repository]

    def resolve(self, manifest_path: Path) -> list[Repository]:
        ids = [repo.id for repo in self.repositories]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate repository IDs")
        return [
            repo.model_copy(update={"path": (manifest_path.parent / repo.path).resolve()})
            for repo in self.repositories
        ]


class Role(StrictModel):
    id: Identifier
    responsibilities: list[str] = Field(min_length=1)
    inputs: list[str] = Field(min_length=1)
    outputs: list[str] = Field(min_length=1)
    allowed_operations: list[str]
    handoffs: list[str]
    boundaries: list[str] = Field(min_length=1)
    specializations: list[str] = Field(default_factory=list)
    system_instructions: str = ""
    input_schema: str = "ExecutionRequest"
    output_schema: str = "AgentOutput"
    allowed_repositories: list[str] = Field(default_factory=list)
    required_context: list[str] = Field(default_factory=list)
    validation_expectations: list[str] = Field(default_factory=list)
    approval_requirements: list[str] = Field(default_factory=list)
    handoff_contract: dict[str, str] = Field(default_factory=dict)
    specialization_instructions: dict[str, str] = Field(default_factory=dict)


class RoleRegistry(StrictModel):
    roles: list[Role]

    def by_id(self) -> dict[str, Role]:
        result = {role.id: role for role in self.roles}
        if len(result) != len(self.roles):
            raise ValueError("duplicate role IDs")
        for role in self.roles:
            if not set(role.handoffs) <= result.keys():
                raise ValueError("unknown handoff role")
        return result


class ApprovalPolicy(StrictModel):
    required_operations: list[str]
    approvers: list[str] = Field(min_length=1)
    default_require_approval: bool = True
    exempt_operations: list[str] = Field(default_factory=list)

    def requires(self, operation: str) -> bool:
        if operation in self.required_operations:
            return True
        if operation in self.exempt_operations:
            return False
        return self.default_require_approval
