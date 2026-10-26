"""Strict, immutable identities for artifact-bound GitHub delivery."""

import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from .models import Identifier, StrictModel

SHA = Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
Ref = Annotated[str, Field(min_length=1, max_length=200)]


def ref(value: str) -> str:
    if (
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]*", value)
        or any(
            p in {"", ".", ".."} or p.endswith(".lock") or p.startswith(".")
            for p in value.split("/")
        )
        or ".." in value
        or value.endswith((".", "/"))
    ):
        raise ValueError("Unsafe Git branch")
    return value


class Remote(StrictModel):
    id: int = Field(gt=0)
    owner: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9-]{0,99}$")
    name: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")

    @property
    def slug(self):
        return self.owner + "/" + self.name


class Unit(StrictModel):
    id: Identifier
    task: str
    repository: Identifier
    root: Path
    remote: Remote
    base: Ref
    branch: Ref
    base_sha: SHA
    head_sha: SHA
    depends_on: list[Identifier] = Field(default_factory=list)
    draft: bool = False

    _refs = field_validator("base", "branch")(ref)

    @model_validator(mode="after")
    def safe_branch(self):
        if self.base == self.branch or not self.branch.startswith("aeo/"):
            raise ValueError("Delivery requires a separate aeo/ branch")
        if len(set(self.depends_on)) != len(self.depends_on) or self.id in self.depends_on:
            raise ValueError("Invalid dependencies")
        self.root = self.root.resolve()
        return self


class Manifest(StrictModel):
    project: Identifier = "agrosphere"
    milestone: Identifier
    units: list[Unit] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def dag(self):
        units = {u.id: u for u in self.units}
        if len(units) != len(self.units) or len({u.task for u in self.units}) != len(self.units):
            raise ValueError("Duplicate delivery unit or task")
        if len({(u.remote.id, u.branch) for u in self.units}) != len(self.units):
            raise ValueError("Conflicting publication branch")
        seen, active = set(), set()

        def visit(key):
            if key not in units or key in active:
                raise ValueError("Missing or cyclic dependency")
            if key in seen:
                return
            active.add(key)
            for dependency in units[key].depends_on:
                visit(dependency)
            active.remove(key)
            seen.add(key)

        for key in units:
            visit(key)
        return self


class PullRequest(StrictModel):
    id: int = Field(gt=0)
    number: int = Field(gt=0)
    url: str
    repository_id: int = Field(gt=0)
    head_repository_id: int = Field(gt=0)
    base: Ref
    branch: Ref
    base_sha: SHA
    head_sha: SHA
    state: Literal["open", "closed", "merged"]
    author: str
    draft: bool = False
    mergeable: bool | None = None
    review_decision: str | None = None
    merge_sha: SHA | None = None

    _refs = field_validator("base", "branch")(ref)

    @field_validator("url")
    @classmethod
    def safe_url(cls, value):
        if not re.fullmatch(
            r"https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[1-9][0-9]*", value
        ):
            raise ValueError("Invalid GitHub PR URL")
        return value


class RequiredCheck(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    app_id: int | None = None


class Policy(StrictModel):
    known: bool = False
    checks: list[RequiredCheck] = Field(default_factory=list)
    approvals: int = Field(default=0, ge=0)
    codeowners: bool = False
    strict: bool = False
    unsupported: list[str] = Field(default_factory=list)
    raw_hash: str | None = None


class Check(StrictModel):
    name: str
    sha: SHA
    state: str
    raw_status: str
    raw_conclusion: str | None = None
    app_id: int | None = None


class Review(StrictModel):
    id: int
    actor: str
    actor_type: str
    sha: SHA
    state: str
    submitted_at: str


class Observation(StrictModel):
    remote: Remote
    principal: str
    can_push: bool
    branch_sha: SHA | None = None
    base_sha: SHA
    prs: list[PullRequest] = Field(default_factory=list)
    policy: Policy
    checks: list[Check] = Field(default_factory=list)
    reviews: list[Review] = Field(default_factory=list)
    base_in_head: bool | None = None
    dependencies_available: dict[str, bool] = Field(default_factory=dict)


class DeliveryError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)
