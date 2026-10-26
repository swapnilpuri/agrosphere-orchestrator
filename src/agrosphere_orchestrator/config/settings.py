from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AEO_", env_file=".env", extra="ignore")
    database_url: str = "sqlite:///aeo.db"
    repository_manifest: Path = Path("config/repositories.yaml")
    role_registry: Path = Path("config/roles.yaml")
    approval_policy: Path = Path("config/approvals.yaml")
    log_level: str = "INFO"
    workspace_root: Path = Path("..")
    recovery_directory: Path = Path("project")
    design_approvers: list[str] = []
    plantuml_jar: Path | None = None
    java_executable: str = "java"
    codex_executable: str = "codex"
    codex_startup_arguments: list[str] = []
    codex_transport: Literal["auto", "exec", "mcp"] = "auto"
    codex_model: str | None = None
    execution_root: Path = Path(".aeo/executions")
    execution_policy: Path = Path("config/execution.yaml")
    execution_approvers: list[str] = []

    scheduler_max_concurrency: int = Field(default=2, ge=1, le=32)
    scheduler_per_agent: int = Field(default=2, ge=1, le=32)
    scheduler_per_repository: int = Field(default=1, ge=1, le=32)
    scheduler_max_repairs: int = Field(default=3, ge=0, le=3)

    quality_policy: Path = Path("config/quality.yaml")
    governance_approvers: list[str] = []

    github_executable: str = "gh"
    github_timeout_seconds: int = Field(default=30, ge=1, le=120)
    github_max_response_bytes: int = Field(default=2000000, ge=1000, le=10000000)
    github_read_retries: int = Field(default=1, ge=0, le=3)
    github_max_pages: int = Field(default=20, ge=1, le=100)
    github_poll_seconds: int = Field(default=5, ge=1, le=30)
    github_poll_budget_seconds: int = Field(default=60, ge=0, le=300)
    github_remote_writes: bool = False
    github_repositories: list[str] = []
    github_base_branches: list[str] = ["main", "master"]
    delivery_root: Path = Path("../.aeo-delivery")

    autonomous_max_tasks: int = Field(default=20, ge=1, le=1000)
    autonomous_max_concurrency: int = Field(default=2, ge=1, le=32)
    autonomous_max_invocations: int = Field(default=30, ge=1, le=10000)
    autonomous_max_attempts: int = Field(default=30, ge=1, le=10000)
    autonomous_max_repairs: int = Field(default=3, ge=0, le=3)
    autonomous_max_seconds: int = Field(default=3600, ge=1, le=86400)
    autonomous_max_poll_seconds: int = Field(default=60, ge=0, le=300)
    autonomous_max_steps: int = Field(default=50, ge=1, le=1000)
    autonomous_max_model_cost: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    autonomous_report_root: Path = Path(".aeo/autonomous")
    autonomous_roadmap: Path | None = None
