import json
import logging
from pathlib import Path

import typer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config.settings import Settings
from .configuration import RepositoryManifest, load_yaml
from .logging import configure_logging
from .persistence import Approval, AuditEvent, Milestone, Project, Run, Task, make_engine
from .planning import validate_plan
from .repositories import discover, inspect_repository

app = typer.Typer(help="AEO-1 foundation: read-only inspection and plan validation.")


@app.callback()
def initialize() -> None:
    configure_logging(Settings().log_level)


def fail(exc: Exception) -> None:
    logging.getLogger(__name__).error(str(exc))
    raise typer.Exit(1)


@app.command("repository-inspect")
def repository_inspect(discover_root: Path | None = None) -> None:
    """Inspect manifest entries or discover local Git roots; never update the manifest."""
    try:
        if discover_root is not None:
            results = discover(discover_root)
        else:
            path = Settings().repository_manifest
            results = [
                inspect_repository(repo)
                for repo in load_yaml(path, RepositoryManifest).resolve(path)
            ]
        typer.echo(json.dumps([result.model_dump() for result in results], indent=2))
        if any(result.error for result in results):
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as exc:
        fail(exc)


@app.command("milestone-validate")
def milestone_validate(path: Path) -> None:
    """Validate schema, dependencies, confirmed repositories and role permissions."""
    try:
        settings = Settings()
        spec = validate_plan(path, settings.repository_manifest, settings.role_registry)
        typer.echo(json.dumps({"valid": True, "milestone": spec.id, "tasks": len(spec.tasks)}))
    except Exception as exc:
        fail(exc)


@app.command("project-status")
def project_status() -> None:
    """Read existing SQLite state without creating a database or applying migrations."""
    try:
        from sqlalchemy.engine import make_url

        url = make_url(Settings().database_url)
        if url.drivername != "sqlite" or not url.database or url.database == ":memory:":
            raise ValueError("project-status requires an existing SQLite file")
        path = Path(url.database).resolve()
        if not path.is_file():
            raise ValueError("state database missing; run alembic upgrade head first")
        uri = path.as_uri() + "?mode=ro&uri=true"
        engine = make_engine("sqlite:///" + uri)
        with Session(engine) as session:
            counts = {
                model.__tablename__: session.scalar(select(func.count()).select_from(model))
                for model in (Project, Milestone, Task, Run, Approval, AuditEvent)
            }
            states = dict(
                session.execute(select(Task.state, func.count()).group_by(Task.state)).all()
            )
        engine.dispose()
        typer.echo(json.dumps({"records": counts, "task_states": states}, indent=2))
    except Exception as exc:
        fail(exc)


project_app = typer.Typer(help="Read-only discovery and durable project recovery.")
milestones_app = typer.Typer(help="Observed milestone history; grants no approval.")
app.add_typer(project_app, name="project")
app.add_typer(milestones_app, name="milestones")


def recovery_paths() -> tuple[Settings, Path, Path]:
    settings = Settings()
    orchestrator = Path(__file__).resolve().parents[2]
    destination = settings.recovery_directory.resolve()
    if not destination.is_relative_to(orchestrator) or destination == orchestrator:
        raise ValueError("recovery_directory must be inside the orchestrator project")
    return settings, orchestrator, destination


@project_app.command("discover")
def project_discover() -> None:
    """Print observed workspace evidence as JSON; write no state or reports."""
    from .recovery_discovery import discover_project

    try:
        settings = Settings()
        snapshot = discover_project(
            settings.workspace_root,
            settings.repository_manifest,
            Path(__file__).resolve().parents[2],
        )
        typer.echo(snapshot.model_dump_json(indent=2))
    except Exception as exc:
        fail(exc)


@project_app.command("reconcile")
def project_reconcile(export_only: bool = False) -> None:
    """Persist observations, never approvals. --export-only repairs reports after interruption."""
    from .recovery import export_reports, reconcile, recovery_engine
    from .recovery_discovery import discover_project

    engine = None
    try:
        settings, orchestrator, destination = recovery_paths()
        engine = recovery_engine(settings.database_url)
        if not export_only:
            snapshot = discover_project(
                settings.workspace_root, settings.repository_manifest, orchestrator
            )
            reconcile(engine, snapshot)
        identity = export_reports(engine, settings.workspace_root, destination)
        typer.echo(
            json.dumps(
                {"snapshot_id": identity, "reports": str(destination), "approval_granted": False}
            )
        )
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@project_app.command("status")
def recovery_status() -> None:
    from .recovery import current_snapshot, next_milestone, recovery_engine

    engine = None
    try:
        settings = Settings()
        engine = recovery_engine(settings.database_url, readonly=True)
        identity, snapshot = current_snapshot(engine, settings.workspace_root)
        typer.echo(
            json.dumps(
                {
                    "snapshot_id": identity,
                    "observed_at": snapshot.observed_at,
                    "repositories": len(snapshot.repositories),
                    "missing_repositories": snapshot.missing_repositories,
                    "milestones": [
                        {"id": m.id, "classification": m.classification}
                        for m in snapshot.milestones
                    ],
                    "recommendation": next_milestone(snapshot),
                },
                indent=2,
            )
        )
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@milestones_app.command("history")
def milestones_history() -> None:
    from .recovery import current_snapshot, recovery_engine

    engine = None
    try:
        settings = Settings()
        engine = recovery_engine(settings.database_url, readonly=True)
        identity, snapshot = current_snapshot(engine, settings.workspace_root)
        typer.echo(
            json.dumps(
                {
                    "snapshot_id": identity,
                    "milestones": [m.model_dump(mode="json") for m in snapshot.milestones],
                },
                indent=2,
            )
        )
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@milestones_app.command("next")
def milestones_next() -> None:
    from .recovery import current_snapshot, next_milestone, recovery_engine

    engine = None
    try:
        settings = Settings()
        engine = recovery_engine(settings.database_url, readonly=True)
        _, snapshot = current_snapshot(engine, settings.workspace_root)
        typer.echo(json.dumps(next_milestone(snapshot), indent=2))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    app()
