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


milestone_app = typer.Typer(help="Mandatory documentation-first milestone lifecycle.")
app.add_typer(milestone_app, name="milestone")


def design_engine(readonly: bool = False):
    from .recovery import recovery_engine

    return recovery_engine(Settings().database_url, readonly=readonly)


@milestone_app.command("design")
def milestone_design(
    milestone: str, requirements: Path | None = None, project: str = "agrosphere"
) -> None:
    """Register an input scope or generate from authenticated, approved requirements."""
    from .design import generate_design, register_requirements
    from .design_agents import TemplateDocumentationAgents
    from .design_artifacts import LocalPlantUML, digest
    from .design_models import DesignInput, case_key

    engine = None
    try:
        settings = Settings()
        key = case_key(project, milestone)
        engine = design_engine()
        if requirements is not None:
            inputs = load_yaml(requirements, DesignInput)
            if inputs.plan.id != milestone or inputs.plan.project != project:
                raise ValueError("Requirement plan does not match requested milestone/project")
            scope = register_requirements(
                engine, inputs, settings.repository_manifest, settings.role_registry
            )
            typer.echo(
                json.dumps(
                    {
                        "scope_id": scope,
                        "approval_granted": False,
                        "next": "Review scope using docs, then run approve-requirements interactively before generation.",
                    }
                )
            )
            return
        renderer = LocalPlantUML(settings.plantuml_jar, settings.java_executable)
        tool = (
            digest(settings.plantuml_jar.read_bytes().hex())
            if settings.plantuml_jar and settings.plantuml_jar.is_file()
            else "plantuml-unavailable"
        )
        identity = generate_design(engine, key, TemplateDocumentationAgents(), renderer, tool)
        typer.echo(json.dumps({"revision_id": identity, "approval_granted": False}))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@milestone_app.command("docs")
@milestone_app.command("design-status")
def milestone_docs(milestone: str, project: str = "agrosphere") -> None:
    """Present the complete review package, exact artifact links and approval history."""
    from .design import design_status
    from .design_models import case_key

    engine = None
    try:
        engine = design_engine(readonly=True)
        typer.echo(json.dumps(design_status(engine, case_key(project, milestone)), indent=2))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@milestone_app.command("validate-design")
def milestone_validate_design(milestone: str, project: str = "agrosphere") -> None:
    from .design import validate_design
    from .design_agents import RuleBasedArchitectureReviewer
    from .design_models import case_key

    engine = None
    try:
        engine = design_engine()
        result = validate_design(
            engine, case_key(project, milestone), RuleBasedArchitectureReviewer()
        )
        typer.echo(json.dumps(result, indent=2))
        if not result["passed"]:
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


def human_design_decision(milestone: str, project: str, kind: str, reject: bool):
    from .design import decide, design_status
    from .design_models import case_key
    from .human_approval import WindowsConsoleHumanVerifier

    engine = None
    try:
        key = case_key(project, milestone)
        engine = design_engine()
        typer.echo(json.dumps(design_status(engine, key), indent=2))
        decision = decide(
            engine,
            key,
            kind,
            not reject,
            WindowsConsoleHumanVerifier(),
            Settings().design_approvers,
        )
        typer.echo(
            json.dumps({"decision_id": decision, "decision": "rejected" if reject else "approved"})
        )
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@milestone_app.command("approve-requirements")
def milestone_approve_requirements(
    milestone: str, project: str = "agrosphere", reject: bool = False
):
    """Authenticate a human decision tied to exact requirement scope. No agent actor flag."""
    human_design_decision(milestone, project, "requirements", reject)


@milestone_app.command("approve-design")
def milestone_approve_design(milestone: str, project: str = "agrosphere", reject: bool = False):
    """Review exact validated artifacts; --reject returns the design for revision."""
    human_design_decision(milestone, project, "design", reject)


@milestone_app.command("approve-delivery")
def milestone_approve_delivery(milestone: str, project: str = "agrosphere", reject: bool = False):
    human_design_decision(milestone, project, "delivery", reject)


@milestone_app.command("implementation-ready")
def milestone_ready(milestone: str, project: str = "agrosphere"):
    from .design import implementation_ready
    from .design_models import case_key

    engine = None
    try:
        engine = design_engine()
        implementation_ready(engine, case_key(project, milestone))
        typer.echo(json.dumps({"state": "IMPLEMENTATION_READY", "execution_started": False}))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@milestone_app.command("implementation-complete")
def milestone_implementation_complete(milestone: str, project: str = "agrosphere"):
    from .design import implementation_complete
    from .design_models import case_key

    engine = None
    try:
        engine = design_engine()
        implementation_complete(engine, case_key(project, milestone))
        typer.echo(json.dumps({"state": "IMPLEMENTATION_VALIDATING", "as_built_required": True}))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@milestone_app.command("reconcile-docs")
def milestone_reconcile_docs(milestone: str, as_built: Path, project: str = "agrosphere"):
    from .design import generate_design
    from .design_agents import TemplateDocumentationAgents
    from .design_artifacts import LocalPlantUML, digest
    from .design_models import AsBuiltInput, case_key

    engine = None
    try:
        settings = Settings()
        engine = design_engine()
        report = load_yaml(as_built, AsBuiltInput)
        tool = (
            digest(settings.plantuml_jar.read_bytes().hex())
            if settings.plantuml_jar and settings.plantuml_jar.is_file()
            else "plantuml-unavailable"
        )
        identity = generate_design(
            engine,
            case_key(project, milestone),
            TemplateDocumentationAgents(),
            LocalPlantUML(settings.plantuml_jar, settings.java_executable),
            tool,
            as_built=report,
        )
        typer.echo(json.dumps({"as_built_revision": identity, "delivery_approved": False}))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@milestone_app.command("export-docs")
def milestone_export_docs(milestone: str, project: str = "agrosphere"):
    from .design import design_status, export_revision
    from .design_models import case_key

    engine = None
    try:
        engine = design_engine(readonly=True)
        state = design_status(engine, case_key(project, milestone))
        if not state.get("revision_id"):
            raise ValueError("No durable revision to export")
        export_revision(engine, state["revision_id"])
        typer.echo(json.dumps({"exported_revision": state["revision_id"]}))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


codex_app = typer.Typer(help="Codex runtime discovery; doctor never invokes a model.")
agents_app = typer.Typer(help="Existing role registry and specialized execution contracts.")
agent_app = typer.Typer(help="Explicit single-task execution; no scheduler.")
app.add_typer(codex_app, name="codex")
app.add_typer(agents_app, name="agents")
app.add_typer(agent_app, name="agent")


@codex_app.command("doctor")
def codex_doctor(output: Path | None = None):
    from .codex_runtime import doctor

    result = doctor(Settings())
    typer.echo(result.model_dump_json(indent=2))
    if output is not None:
        root = Path(__file__).resolve().parents[2]
        target = output.resolve()
        if not target.is_relative_to(root):
            fail(ValueError("Doctor evidence output must be inside the orchestrator"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    if not result.exec_supported:
        raise typer.Exit(1)


@agents_app.command("list")
def agents_list():
    from .configuration import RoleRegistry

    typer.echo(
        json.dumps(
            [
                {
                    "id": r.id,
                    "specializations": r.specializations,
                    "allowed_operations": r.allowed_operations,
                }
                for r in load_yaml(Settings().role_registry, RoleRegistry).roles
            ],
            indent=2,
        )
    )


@agents_app.command("describe")
def agents_describe(role: str):
    from .configuration import RoleRegistry

    value = load_yaml(Settings().role_registry, RoleRegistry).by_id().get(role)
    if value is None:
        fail(ValueError("Unknown registered role"))
    typer.echo(value.model_dump_json(indent=2))


@agent_app.command("run")
def agent_run(
    task: str | None = None,
    execution: str | None = None,
    mode: str = "READ_ONLY",
    scope: list[str] = typer.Option(None),
    validate: list[str] = typer.Option(None),
    specialization: str | None = None,
    timeout: int = 300,
):
    """--task prepares a reviewable scope; --execution starts its exact approved request."""
    import asyncio

    from .execution import queue_execution, run_execution

    engine = None
    try:
        settings = Settings()
        engine = design_engine()
        if bool(task) == bool(execution):
            raise ValueError(
                "Provide exactly one of --task (prepare) or --execution (execute approved scope)"
            )
        if task:
            identity = queue_execution(
                engine,
                settings,
                task,
                mode=mode,
                scopes=scope,
                command_ids=validate,
                specialization=specialization,
                timeout=timeout,
            )
            typer.echo(
                json.dumps(
                    {
                        "execution_id": identity,
                        "state": "AWAITING_APPROVAL",
                        "next": "Review agent status, then approve this exact execution interactively.",
                    },
                    indent=2,
                )
            )
        else:
            result = asyncio.run(run_execution(engine, settings, execution))
            typer.echo(result.model_dump_json(indent=2))
            if result.status != "SUCCEEDED":
                raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@agent_app.command("approve")
def agent_approve(execution: str = typer.Option(...), expiry_seconds: int = 900):
    from .execution import approve_execution, execution_status
    from .human_approval import WindowsConsoleHumanVerifier

    engine = None
    try:
        engine = design_engine()
        typer.echo(json.dumps(execution_status(engine, execution), indent=2))
        grant = approve_execution(
            engine, Settings(), execution, WindowsConsoleHumanVerifier(), expiry_seconds
        )
        typer.echo(json.dumps({"execution_id": execution, "grant_id": grant, "approved": True}))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@agent_app.command("status")
def agent_status(execution: str = typer.Option(...)):
    from .execution import execution_status

    engine = None
    try:
        engine = design_engine(readonly=True)
        typer.echo(json.dumps(execution_status(engine, execution), indent=2))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@agent_app.command("logs")
def agent_logs(execution: str = typer.Option(...)):
    from .execution import execution_status
    from .execution_process import Redactor

    engine = None
    try:
        engine = design_engine(readonly=True)
        status = execution_status(engine, execution)
        root = Settings().execution_root.resolve()
        for value in (status["result"] or {}).get("logs", []):
            p = Path(value).resolve()
            if not p.is_relative_to(root):
                raise PermissionError("Persisted log path is outside private execution storage")
            typer.echo(Redactor().clean(p.read_text(encoding="utf-8")))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@agent_app.command("cancel")
def agent_cancel(execution: str = typer.Option(...)):
    from .execution import cancel_execution

    engine = None
    try:
        engine = design_engine()
        state = cancel_execution(engine, execution)
        typer.echo(
            json.dumps(
                {
                    "execution_id": execution,
                    "state": state,
                    "cancellation_confirmed": state == "CANCELLED",
                }
            )
        )
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@agent_app.command("reconcile")
def agent_reconcile():
    from .execution_sessions import CodexSessionManager

    engine = None
    try:
        engine = design_engine()
        typer.echo(json.dumps(CodexSessionManager(engine).reconcile(), indent=2))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@agent_app.command("resume")
def agent_resume(
    execution: str = typer.Option(...),
    instructions: str = typer.Option(...),
    continue_session: bool = False,
):
    """Prepare a new bounded recovery scope; always requires a new human grant."""
    from .execution import execution_status, queue_execution
    from .execution_sessions import CodexSessionManager

    engine = None
    try:
        engine = design_engine()
        CodexSessionManager(engine).reconcile()
        parent = execution_status(engine, execution)
        if parent["state"] not in {"FAILED", "TIMED_OUT", "INTERRUPTED"}:
            raise PermissionError(
                "Only failed/interrupted work can recover; completed/active/cancelled work is not replayed"
            )
        request = parent["request"]
        if continue_session and (request["mode"] != "READ_ONLY" or not parent["session_id"]):
            raise PermissionError("Only a verified read-only session UUID can be continued")
        identity = queue_execution(
            engine,
            Settings(),
            parent["task_id"],
            mode=request["mode"],
            scopes=request["allowed_file_scopes"],
            specialization=request.get("specialization"),
            command_ids=request["validation_commands"],
            timeout=request["timeout_seconds"],
            parent=execution,
            instructions=instructions,
            continuation=parent["session_id"] if continue_session else None,
        )
        typer.echo(
            json.dumps(
                {
                    "recovery_execution_id": identity,
                    "state": "AWAITING_APPROVAL",
                    "original_worktree_preserved": True,
                }
            )
        )
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@agent_app.command("cleanup")
def agent_cleanup(execution: str = typer.Option(...)):
    from .execution import execution_directory, execution_status
    from .execution_workspace import cleanup_worktree

    engine = None
    try:
        engine = design_engine(readonly=True)
        settings = Settings()
        status = execution_status(engine, execution)
        if (
            status["state"] not in {"SUCCEEDED", "FAILED", "TIMED_OUT", "CANCELLED", "INTERRUPTED"}
            or status["request"]["mode"] == "READ_ONLY"
        ):
            raise PermissionError("Only terminal, preserved isolated worktrees can be cleaned")
        directory = execution_directory(settings, execution)
        workspace = json.loads((directory / "workspace.json").read_text(encoding="utf-8"))
        cleanup_worktree(
            Path(workspace["source"]), Path(workspace["path"]), settings.execution_root, directory
        )
        typer.echo(
            json.dumps(
                {"execution_id": execution, "worktree_removed": True, "branch_preserved": True}
            )
        )
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


# AEO-3 commands retain the existing milestone/agent naming conventions.
@milestone_app.command("plan")
def milestone_plan(milestone: str, options: Path | None = None, project: str = "agrosphere"):
    from .orchestration import propose_plan
    from .orchestration_models import TaskOptions

    try:
        settings = Settings()
        engine = design_engine()
        data = (
            None
            if options is None
            else {
                k: TaskOptions.model_validate(v) for k, v in json.loads(options.read_text()).items()
            }
        )
        identity = propose_plan(engine, settings, milestone, data, project)
        typer.echo(json.dumps({"plan_id": identity, "approved": False}))
    except Exception as exc:
        fail(exc)


@milestone_app.command("approve-plan")
def milestone_approve_plan(milestone: str, project: str = "agrosphere"):
    from .human_approval import WindowsConsoleHumanVerifier
    from .orchestration import approve_plan, milestone_report

    try:
        engine = design_engine()
        typer.echo(json.dumps(milestone_report(engine, milestone, project), indent=2))
        approve_plan(engine, Settings(), milestone, WindowsConsoleHumanVerifier(), project)
        typer.echo(json.dumps({"approved": True}))
    except Exception as exc:
        fail(exc)


def scheduler_action(action, milestone, project):
    import asyncio

    from .orchestration import TaskScheduler

    engine = None
    try:
        engine = design_engine()
        scheduler = TaskScheduler(engine, Settings())
        result = asyncio.run(getattr(scheduler, action)(milestone, project))
        typer.echo(json.dumps(result, indent=2))
    except Exception as exc:
        fail(exc)
    finally:
        if engine is not None:
            engine.dispose()


@milestone_app.command("prepare")
def milestone_prepare(milestone: str, project: str = "agrosphere"):
    """Prepare READY requests for review with agent approve --execution ID."""
    scheduler_action("prepare", milestone, project)


@milestone_app.command("execute")
def milestone_execute(milestone: str, project: str = "agrosphere"):
    scheduler_action("execute", milestone, project)


@milestone_app.command("pause")
def milestone_pause(milestone: str, project: str = "agrosphere"):
    scheduler_action("pause", milestone, project)


@milestone_app.command("resume")
def milestone_resume(milestone: str, project: str = "agrosphere"):
    scheduler_action("resume", milestone, project)


@milestone_app.command("status")
@milestone_app.command("report")
def milestone_execution_report(milestone: str, project: str = "agrosphere", markdown: bool = False):
    from .orchestration import markdown_report, milestone_report

    try:
        engine = design_engine(readonly=True)
        report = milestone_report(engine, milestone, project)
        typer.echo(markdown_report(report) if markdown else json.dumps(report, indent=2))
    except Exception as exc:
        fail(exc)


@milestone_app.command("graph")
def milestone_graph(milestone: str, project: str = "agrosphere", plantuml: bool = False):
    from .orchestration import load_plan, milestone_record

    try:
        engine = design_engine(readonly=True)
        with Session(engine) as session:
            plan, _, _ = load_plan(session, milestone_record(session, milestone, project))
            typer.echo(plan.plantuml() if plantuml else plan.model_dump_json(indent=2))
    except Exception as exc:
        fail(exc)


tasks_app = typer.Typer(help="Persisted task execution state.")
app.add_typer(tasks_app, name="tasks")


@tasks_app.command("list")
def tasks_list(milestone: str = typer.Option(...), project: str = "agrosphere"):
    from .orchestration import milestone_report

    try:
        typer.echo(
            json.dumps(
                milestone_report(design_engine(readonly=True), milestone, project)["tasks"],
                indent=2,
            )
        )
    except Exception as exc:
        fail(exc)


@tasks_app.command("inspect")
def tasks_inspect(task: str):
    try:
        with Session(design_engine(readonly=True)) as session:
            record = session.get(Task, task)
            if record is None:
                raise ValueError("Unknown persistent task UUID")
            typer.echo(
                json.dumps({"id": record.id, "state": record.state, "spec": record.spec}, indent=2)
            )
    except Exception as exc:
        fail(exc)


@agents_app.command("workload")
def agents_workload():
    from .orchestration_store import TaskClaim

    try:
        with Session(design_engine(readonly=True)) as session:
            rows = session.execute(
                select(Task.spec, TaskClaim.execution_id, TaskClaim.reconciliation_required).join(
                    TaskClaim
                )
            ).all()
            typer.echo(
                json.dumps(
                    [
                        {
                            "role": r[0]["role"],
                            "execution_id": r[1],
                            "reconciliation_required": r[2],
                        }
                        for r in rows
                    ],
                    indent=2,
                )
            )
    except Exception as exc:
        fail(exc)


@milestone_app.command("reconcile")
def milestone_reconcile_execution(milestone: str, project: str = "agrosphere"):
    from .orchestration import TaskScheduler

    try:
        engine = design_engine()
        typer.echo(
            json.dumps(TaskScheduler(engine, Settings()).reconcile(milestone, project), indent=2)
        )
    except Exception as exc:
        fail(exc)


@milestone_app.command("handoff")
def milestone_handoff(
    milestone: str,
    source: str,
    destination: str,
    artifacts: Path,
    summary: str = "Structured artifact handoff",
    project: str = "agrosphere",
):
    from .orchestration import publish_handoff

    try:
        engine = design_engine()
        identity = publish_handoff(
            engine,
            Settings(),
            milestone,
            source,
            destination,
            json.loads(artifacts.read_text()),
            summary,
            project,
        )
        typer.echo(json.dumps({"handoff_id": identity}))
    except Exception as exc:
        fail(exc)


@milestone_app.command("deviation")
def milestone_deviation(milestone: str, description: str, impact: str, project: str = "agrosphere"):
    import asyncio

    from .orchestration import propose_deviation

    try:
        identity = asyncio.run(
            propose_deviation(design_engine(), Settings(), milestone, description, impact, project)
        )
        typer.echo(json.dumps({"deviation_id": identity, "approval_required": True}))
    except Exception as exc:
        fail(exc)


quality_app = typer.Typer(help="Independent deterministic quality governance.")
security_app = typer.Typer(help="Security findings and exception evidence.")
approvals_app = typer.Typer(help="Artifact-bound authenticated human decisions.")
app.add_typer(quality_app, name="quality")
app.add_typer(security_app, name="security")
app.add_typer(approvals_app, name="approvals")


@quality_app.command("policies")
def quality_policies():
    from .quality_models import QualityPolicy

    try:
        typer.echo(load_yaml(Settings().quality_policy, QualityPolicy).model_dump_json(indent=2))
    except Exception as exc:
        fail(exc)


@quality_app.command("activate")
def quality_activate(milestone: str = typer.Option(...), project: str = "agrosphere"):
    from .human_approval import WindowsConsoleHumanVerifier
    from .quality import activate_policy
    from .quality_models import QualityPolicy

    try:
        typer.echo(load_yaml(Settings().quality_policy, QualityPolicy).model_dump_json(indent=2))
        typer.echo(
            json.dumps(
                {
                    "policy_hash": activate_policy(
                        design_engine(),
                        Settings(),
                        milestone,
                        WindowsConsoleHumanVerifier(),
                        project,
                    )
                }
            )
        )
    except Exception as exc:
        fail(exc)


@quality_app.command("validate")
def quality_validate(
    milestone: str = typer.Option(...), project: str = "agrosphere", markdown: bool = False
):
    import asyncio

    from .quality import markdown_report, validate

    try:
        report = asyncio.run(validate(design_engine(), Settings(), milestone, project))
        typer.echo(markdown_report(report) if markdown else json.dumps(report, indent=2))
        if report["decision"] not in {"READY_FOR_APPROVAL", "APPROVED_FOR_DELIVERY"}:
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as exc:
        fail(exc)


@quality_app.command("report")
@security_app.command("report")
@milestone_app.command("readiness")
def quality_report(
    milestone: str = typer.Option(...), project: str = "agrosphere", markdown: bool = False
):
    from .quality import markdown_report, readiness

    try:
        report = readiness(design_engine(), Settings(), milestone, project)
        typer.echo(markdown_report(report) if markdown else json.dumps(report, indent=2))
    except Exception as exc:
        fail(exc)


@quality_app.command("remediate")
def quality_remediate(milestone: str = typer.Option(...), project: str = "agrosphere"):
    from .quality import prepare_remediation

    try:
        typer.echo(
            json.dumps(
                {
                    "tasks": prepare_remediation(design_engine(), Settings(), milestone, project),
                    "fresh_write_grant_required": True,
                }
            )
        )
    except Exception as exc:
        fail(exc)


@approvals_app.command("pending")
def approvals_pending():
    from .quality import decisions
    from .quality_store import GovernanceRecord

    try:
        with Session(design_engine(readonly=True)) as session:
            typer.echo(
                json.dumps(
                    [
                        {"id": r.id, **r.payload}
                        for r in session.scalars(
                            select(GovernanceRecord).where(
                                GovernanceRecord.kind == "approval.request"
                            )
                        )
                        if not decisions(session, r)
                    ],
                    indent=2,
                )
            )
    except Exception as exc:
        fail(exc)


@approvals_app.command("inspect")
def approvals_inspect(approval: str):
    from .quality import inspect_approval

    try:
        typer.echo(json.dumps(inspect_approval(design_engine(readonly=True), approval), indent=2))
    except Exception as exc:
        fail(exc)


@approvals_app.command("request")
def approvals_request(
    milestone: str = typer.Option(...),
    category: str = "DELIVERY_APPROVAL",
    action: str = "delivery",
    reason: str = typer.Option(...),
    expires_seconds: int = 900,
):
    from .quality import request_approval

    try:
        identity = request_approval(
            design_engine(),
            Settings(),
            milestone,
            category,
            action,
            "orchestrator",
            reason,
            expires_seconds,
        )
        typer.echo(json.dumps({"approval_id": identity, "approved": False}))
    except Exception as exc:
        fail(exc)


@approvals_app.command("decide")
def approvals_decide(approval: str, decision: str = "approved", reason: str = typer.Option(...)):
    from .human_approval import WindowsConsoleHumanVerifier
    from .quality import decide_approval, inspect_approval

    try:
        engine = design_engine()
        typer.echo(json.dumps(inspect_approval(engine, approval), indent=2))
        identity = decide_approval(
            engine, Settings(), approval, WindowsConsoleHumanVerifier(), decision, reason
        )
        typer.echo(json.dumps({"decision_id": identity, "decision": decision}))
    except Exception as exc:
        fail(exc)


if __name__ == "__main__":
    app()
