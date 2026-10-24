from pathlib import Path

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
