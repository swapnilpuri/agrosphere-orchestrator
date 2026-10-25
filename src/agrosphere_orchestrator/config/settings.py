from pathlib import Path
from typing import Literal

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
