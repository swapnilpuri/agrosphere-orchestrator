"""Read-only default planning and explicit bounded local/simulated continuation."""

import asyncio
import json
from pathlib import Path

import typer

from .autonomous import AutonomousMilestoneController
from .autonomous_models import AutonomousRequest
from .autonomous_store import export_report, markdown, report
from .config.settings import Settings
from .configuration import load_yaml
from .delivery_models import Manifest
from .recovery import recovery_engine

app = typer.Typer(
    help="Bounded autonomous AgroSphere workflow; plan/start default to read-only dry-run."
)


def output(call, readonly=False):
    engine = None
    try:
        settings = Settings()
        engine = recovery_engine(settings.database_url, readonly=readonly)
        result = call(AutonomousMilestoneController(engine, settings), engine)
        typer.echo(result if isinstance(result, str) else json.dumps(result, indent=2))
    except Exception as exc:
        typer.echo(
            json.dumps(
                {
                    "error": type(exc).__name__,
                    "message": str(exc)
                    if isinstance(exc, (ValueError, PermissionError))
                    else "Operation failed; inspect durable operation and child evidence before recovery",
                }
            ),
            err=True,
        )
        raise typer.Exit(1) from None
    finally:
        if engine:
            engine.dispose()


def request_input(milestone, request, mode):
    value = (
        load_yaml(request, AutonomousRequest) if request else AutonomousRequest(milestone=milestone)
    )
    if value.milestone != milestone:
        raise ValueError("Requested milestone differs from input")
    value.mode = mode
    return value


@app.command("plan")
def plan_command(milestone: str = typer.Option(...), request: Path | None = None):
    output(lambda c, e: c.plan(request_input(milestone, request, "dry-run")), readonly=True)


@app.command("start")
def start_command(
    milestone: str = typer.Option(...),
    request: Path | None = None,
    mode: str = "dry-run",
    run_id: str | None = None,
):
    def start(c, e):
        value = request_input(milestone, request, mode)
        result = c.start(value, run_id)
        return asyncio.run(c.run(result["run_id"])) if mode != "dry-run" else result

    output(start, readonly=mode == "dry-run")


@app.command("status")
def status_command(run: str):
    output(lambda c, e: report(e, run), readonly=True)


@app.command("pause")
def pause_command(run: str):
    output(lambda c, e: c.pause(run))


@app.command("resume")
def resume_command(
    run: str, grant: list[str] = typer.Option(None), delivery_manifest: Path | None = None
):
    def resume(c, e):
        grants = {}
        for item in grant or []:
            key, identity = item.split("=", 1)
            grants[key] = identity
        manifest = load_yaml(delivery_manifest, Manifest) if delivery_manifest else None
        return asyncio.run(c.resume(run, grants, manifest))

    output(resume)


@app.command("recover")
def recover_command(run: str):
    output(lambda c, e: asyncio.run(c.recover(run)))


@app.command("report")
def report_command(
    run: str, markdown_output: bool = typer.Option(False, "--markdown"), export: bool = False
):
    def present(c, e):
        if export:
            return export_report(e, run, c.settings.autonomous_report_root)
        value = report(e, run)
        return markdown(value) if markdown_output else value

    output(present, readonly=True)


@app.command("validate")
def validate_command(run: str):
    output(lambda c, e: c.validate(run), readonly=True)


@app.command("simulate")
def simulate_command(output_directory: Path | None = None):
    from .autonomous_simulation import simulate

    try:
        typer.echo(json.dumps(simulate(Settings(), output_directory), indent=2))
    except Exception as exc:
        typer.echo(
            json.dumps(
                {
                    "error": type(exc).__name__,
                    "message": "Isolated simulation failed; no live model/provider is used",
                }
            ),
            err=True,
        )
        raise typer.Exit(1) from None
