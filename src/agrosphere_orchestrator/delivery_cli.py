"""Delivery commands; inspection and recovery have no remote write side effects."""

import json
from pathlib import Path

import typer
from sqlalchemy.orm import Session

from . import delivery, quality
from .config.settings import Settings
from .configuration import load_yaml
from .delivery_models import DeliveryError, Manifest
from .delivery_store import DeliveryRun
from .recovery import recovery_engine

app = typer.Typer(help="Artifact-bound GitHub delivery; remote writes default off.")


def output(call):
    engine = None
    try:
        settings = Settings()
        engine = recovery_engine(settings.database_url)
        value = call(engine, settings)
        typer.echo(value if isinstance(value, str) else json.dumps(value, indent=2))
    except Exception as exc:
        code = getattr(
            exc,
            "code",
            "AUTHORIZATION_DENIED"
            if isinstance(exc, PermissionError)
            else "INVALID_INPUT"
            if isinstance(exc, ValueError)
            else "DELIVERY_FAILURE",
        )
        typer.echo(
            json.dumps(
                {
                    "error": code,
                    "message": str(exc)
                    if isinstance(exc, (DeliveryError, PermissionError))
                    else "Delivery operation failed",
                }
            ),
            err=True,
        )
        raise typer.Exit(
            3
            if code in {"AUTHORIZATION_DENIED", "APPROVAL_SCOPE", "WRITES_DISABLED"}
            else 4
            if code == "RECOVERY_REQUIRED"
            else 2
        ) from None
    finally:
        if engine:
            engine.dispose()


@app.command("plan")
def plan_command(manifest: Path):
    output(lambda e, s: {"run": delivery.plan(e, s, load_yaml(manifest, Manifest))})


@app.command("prepare")
def prepare_command(run: str, unit: str, approval: str = typer.Option(...)):
    output(lambda e, s: delivery.mutate(e, s, run, unit, "prepare", approval))


@app.command("publish")
def publish_command(
    run: str,
    unit: str,
    push_approval: str = typer.Option(...),
    pr_approval: str = typer.Option(...),
):
    def publish(e, s):
        delivery.mutate(e, s, run, unit, "push", push_approval)
        return delivery.mutate(e, s, run, unit, "create-pr", pr_approval)

    output(publish)


@app.command("status")
def status_command(run: str):
    output(lambda e, s: delivery.status(e, run))


@app.command("checks")
def checks_command(run: str, unit: str, poll: bool = False):
    output(lambda e, s: delivery.observe(e, s, run, unit, poll))


@app.command("reviews")
def reviews_command(run: str, unit: str):
    output(lambda e, s: delivery.observe(e, s, run, unit))


@app.command("reconcile")
def reconcile_command(run: str, unit: str):
    output(lambda e, s: delivery.reconcile(e, s, run, unit))


@app.command("recover")
def recover_command(run: str, unit: str, action: str | None = None, approval: str | None = None):
    """Observe by default; an explicit retry needs its exact fresh recovery grant."""

    def recover(e, s):
        if action is None and approval is None:
            return delivery.reconcile(e, s, run, unit)
        if action not in {"prepare", "push", "create-pr"} or not approval:
            raise DeliveryError(
                "APPROVAL_SCOPE", "Explicit recovery action and fresh exact approval are required"
            )
        return delivery.mutate(e, s, run, unit, "recover-" + action, approval)

    output(recover)


@app.command("report")
def report_command(run: str, markdown: bool = False):
    output(
        lambda e, s: (
            delivery.markdown(delivery.status(e, run)) if markdown else delivery.status(e, run)
        )
    )


@app.command("request-approval")
def request_command(run: str, unit: str, action: str, justification: str = typer.Option(...)):
    """Request exact one-time AEO-4 authorization; never approves a request."""

    def request(e, s):
        scope = delivery.approval_scope(e, s, run, unit, action)
        with Session(e) as session:
            record = session.get(DeliveryRun, run)
            manifest = record.manifest
        identity = quality.request_approval(
            e,
            s,
            manifest["milestone"],
            scope["category"],
            scope["action"],
            "delivery-engine",
            justification,
            project=manifest["project"],
        )
        return {"approval_request": identity, **scope, "approved": False}

    output(request)
