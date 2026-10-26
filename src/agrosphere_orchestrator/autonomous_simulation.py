"""Opt-in disposable three-repository simulation. Never uses real model/provider ports."""

import asyncio
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import delivery, design, quality
from .autonomous import AutonomousMilestoneController
from .autonomous_models import AutonomousRequest, RunLimits
from .autonomous_services import ExistingServices
from .autonomous_store import markdown
from .config.settings import Settings
from .delivery_models import Manifest, Observation, Policy, PullRequest, Remote, Unit
from .design_agents import SECTIONS
from .design_models import DesignInput
from .execution import approve_execution
from .execution_models import AgentOutput
from .execution_process import ProcessOutcome
from .execution_workspace import git
from .orchestration import TaskScheduler, approve_plan
from .persistence import Task, make_engine
from .quality_models import QualityPolicy

ACTOR = "sid:aeo-isolated-simulation-human"


class IsolatedVerifier:
    def __init__(self, directory, settings):
        self.directory, self.settings = directory.resolve(), settings

    def verify(self, subject, decision):
        if (
            not (self.directory / "SIMULATION_ONLY").is_file()
            or self.settings.database_url != "sqlite:///" + (self.directory / "state.db").as_posix()
        ):
            raise PermissionError(
                "Fixture authentication is restricted to the isolated simulation database"
            )
        return ACTOR


class SimulatedRenderer:
    def render(self, source):
        return (
            '<svg xmlns="http://www.w3.org/2000/svg"><text>Simulated renderer, not PlantUML evidence</text></svg>',
            [],
        )


class SimulatedTransport:
    name = "simulation-no-live-codex"
    calls = 0

    async def execute(self, request, prompt, directory, **callbacks):
        self.calls += 1
        callbacks["started"](os.getpid())
        changed = []
        if request.mode == "WORKTREE_WRITE":
            target = Path(request.worktree_path) / "src/simulation.txt"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("Simulated implementation output\n", encoding="utf-8")
            changed = ["src/simulation.txt"]
        value = AgentOutput(
            summary="Simulated independent task output",
            work_performed=["Read-only fixture task"],
            files_changed=changed,
            artifacts_created=[],
            commands_executed=[],
            validation_evidence=[],
            errors=[],
            warnings=["SIMULATION"],
            unresolved_issues=[],
            suggested_next_actions=[],
        )
        stream = [
            {"type": "thread.started", "thread_id": str(uuid4())},
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": value.model_dump_json()},
            },
            {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}},
        ]
        return ProcessOutcome(0, "\n".join(json.dumps(v) for v in stream), "")


class SimulatedValidator:
    def __init__(self):
        self.failed_once = False

    async def evaluate(self, gate, repository, command):
        failed = gate.type == "test" and not self.failed_once
        if failed:
            self.failed_once = True
        data = {
            "validator_version": "simulation-v1",
            "findings": [],
            "test_cases": {"simulation.acceptance": "failed" if failed else "passed"},
        }
        return {"exit_code": 1 if failed else 0, "stdout": json.dumps(data), "stderr": ""}


class SimulatedProvider:
    def __init__(self, units):
        self.values = {
            u.id: Observation(
                remote=u.remote,
                principal="simulation-publisher",
                can_push=True,
                base_sha=u.base_sha,
                policy=Policy(known=True),
            )
            for u in units
        }
        self.pushes = self.creates = 0

    def observe(self, unit):
        return self.values[unit.id].model_copy(deep=True)

    def push(self, unit, worktree):
        self.pushes += 1
        self.values[unit.id].branch_sha = unit.head_sha

    def create_pr(self, unit, title, body):
        self.creates += 1
        pr = PullRequest(
            id=unit.remote.id * 10,
            number=1,
            url=f"https://github.com/simulation/{unit.repository}/pull/1",
            repository_id=unit.remote.id,
            head_repository_id=unit.remote.id,
            base=unit.base,
            branch=unit.branch,
            base_sha=unit.base_sha,
            head_sha=unit.head_sha,
            state="open",
            author="simulation-author",
            mergeable=True,
        )
        self.values[unit.id].prs = [pr]
        return pr

    def dependency_available(self, unit, observation):
        return False


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def fixture(directory, source_settings):
    package = Path(__file__).resolve().parents[2]
    (directory / "SIMULATION_ONLY").write_text(
        "Disposable fixtures; no live authority", encoding="utf-8"
    )
    repositories, context = [], []
    names = ("estate", "agrosphere-architecture", "agrosphere-contracts")
    for name in names:
        root = directory / name
        root.mkdir()
        git(root, "init", "-b", "main")
        git(root, "config", "core.autocrlf", "false")
        (root / "README.md").write_text("Isolated simulation fixture\n", encoding="utf-8")
        if name == "estate":
            write_json(root / "roadmap.json", {"milestones": [{"id": "AEO-SIM", "depends_on": []}]})
        git(root, "add", ".")
        git(
            root,
            "-c",
            "user.name=Simulation",
            "-c",
            "user.email=simulation@example.invalid",
            "commit",
            "-m",
            "Isolated simulation",
        )
        git(root, "remote", "add", "origin", "https://github.com/simulation/" + name + ".git")
        repositories.append({"id": name, "path": str(root), "status": "confirmed"})
        for path in (
            [root / "README.md", root / "roadmap.json"]
            if name == "estate"
            else [root / "README.md"]
        ):
            context.append(
                {
                    "repository": name,
                    "path": path.name,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "head": git(root, "rev-parse", "HEAD"),
                }
            )
    manifest = directory / "repositories.json"
    write_json(manifest, {"repositories": repositories})
    roles = json.loads((package / "config/roles.yaml").read_text(encoding="utf-8"))
    for role in roles["roles"]:
        role["allowed_repositories"] = list(names)
    write_json(directory / "roles.json", roles)
    write_json(
        directory / "execution.json",
        {
            "live_enabled": True,
            "validation_commands": [
                {"id": kind, "argv": [sys.executable, "-c", "print('simulation')"]}
                for kind in [
                    "build",
                    "test",
                    "security",
                    "architecture",
                    "contract",
                    "documentation",
                ]
            ],
        },
    )
    write_json(
        directory / "approvals.json",
        {
            "required_operations": ["code-write"],
            "approvers": [ACTOR],
            "exempt_operations": ["inspect", "validate"],
        },
    )
    settings = Settings(
        _env_file=None,
        database_url="sqlite:///" + (directory / "state.db").as_posix(),
        workspace_root=directory,
        repository_manifest=manifest,
        role_registry=directory / "roles.json",
        execution_policy=directory / "execution.json",
        approval_policy=directory / "approvals.json",
        quality_policy=directory / "quality.json",
        execution_root=directory / "x",
        design_approvers=[ACTOR],
        execution_approvers=[ACTOR],
        governance_approvers=[ACTOR],
        github_remote_writes=True,
        github_repositories=["simulation/" + name for name in names],
        delivery_root=directory / "d",
        autonomous_roadmap=directory / "estate/roadmap.json",
        github_timeout_seconds=1,
        autonomous_max_steps=100,
        autonomous_max_poll_seconds=300,
        autonomous_max_seconds=3600,
    )
    requirements = DesignInput.model_validate(
        {
            "plan": {
                "id": "AEO-SIM",
                "project": "agrosphere",
                "title": "Isolated simulation",
                "tasks": [
                    {
                        "id": "task-" + str(i),
                        "title": "Simulated read-only work " + name,
                        "repository": name,
                        "role": "developer",
                        "operation": "code-write" if i == 1 else "inspect",
                        "depends_on": [] if i < 2 else ["task-0", "task-1"],
                        "acceptance_criteria": ["Fixture accepted"],
                    }
                    for i, name in enumerate(names)
                ],
            },
            "requirements": [
                {
                    "id": "SIM-REQ",
                    "text": "Simulated acceptance contract",
                    "acceptance_criteria": ["Fixture accepted"],
                }
            ],
            "context": context,
            "narratives": {
                key: {
                    section: "Explicit simulated approved fixture narrative for " + section
                    for section in sections
                }
                for key, sections in SECTIONS.items()
            },
            "diagrams": [
                {
                    "id": "simulation-sequence",
                    "kind": "sequence",
                    "repository": "estate",
                    "requirement_ids": ["SIM-REQ"],
                    "nodes": [{"id": "A", "label": "Operator"}, {"id": "B", "label": "Controller"}],
                    "edges": [{"source": "A", "target": "B", "label": "Run bounded workflow"}],
                    "rationale": "Fixture interactions",
                }
            ],
        }
    )
    requirements.contract_impact = True
    from .design_models import ContractProposal

    requirements.contracts = [
        ContractProposal(
            id="simulation-api",
            kind="openapi",
            version="1.0.0",
            requirement_ids=["SIM-REQ"],
            content="openapi: 3.0.0\ninfo: {title: Simulation, version: 1.0.0}\npaths: {}\n",
        )
    ]
    requirements.narratives["service:estate"] = requirements.narratives["service"].copy()
    quality_policy = QualityPolicy.model_validate(
        {
            "id": "simulation",
            "version": 1,
            "required_review_roles": [],
            "gates": [
                {
                    "id": kind,
                    "type": kind,
                    "repository": "estate",
                    "command": kind,
                    "format": "json" if kind in {"test", "security"} else "exit",
                    "validator_version": "simulation-v1",
                    "retry_eligible": kind in {"build", "test"},
                    "tasks": ["task-0"],
                }
                for kind in [
                    "build",
                    "test",
                    "security",
                    "architecture",
                    "contract",
                    "documentation",
                ]
            ],
            "criteria": [
                {
                    "requirement_id": "SIM-REQ",
                    "criterion_id": "AC-1",
                    "criterion_text": "Fixture accepted",
                    "task": "task-0",
                    "gate": "test",
                    "test_case": "simulation.acceptance",
                }
            ],
        }
    )
    # Every impacted repository must retain the complete required gate set.
    original_gates = quality_policy.gates
    gates = []
    for i, name in enumerate(names):
        for gate in original_gates:
            gates.append(
                gate.model_copy(
                    update={
                        "id": name + "-" + gate.type,
                        "repository": name,
                        "tasks": ["task-" + str(i)],
                    }
                )
            )
    quality_policy.gates = gates
    quality_policy.criteria[0].gate = "estate-test"
    write_json(settings.quality_policy, quality_policy.model_dump(mode="json"))
    return settings, requirements


@contextmanager
def isolated_directory():
    parent = Path(tempfile.gettempdir()).resolve()
    root = Path(tempfile.mkdtemp(prefix="a6s-", dir=parent)).resolve()
    try:
        yield root
    finally:
        # Only delete this exact freshly allocated child. Extended Windows paths
        # allow cleanup of nested immutable revision bundles beyond MAX_PATH.
        if (
            root.parent != parent
            or not root.name.startswith("a6s-")
            or root == parent
            or root.is_symlink()
        ):
            raise RuntimeError("Unsafe simulation cleanup target")
        target = "\\\\?\\" + str(root) if os.name == "nt" else str(root)

        def writable(function, path, error):
            if not isinstance(error, PermissionError):
                raise error
            os.chmod(path, stat.S_IWRITE)
            function(path)

        shutil.rmtree(target, onexc=writable)


def simulate(source_settings, output_directory=None):
    # Source settings are read for reporting only. Every side-effect target below is newly created.
    with isolated_directory() as name:
        directory = Path(name).resolve()
        settings, requirements = fixture(directory, source_settings)
        env = {
            "AEO_DATABASE_URL": settings.database_url,
            "AEO_DESIGN_APPROVERS": json.dumps([ACTOR]),
        }
        package = Path(__file__).resolve().parents[2]
        config = Config(str(package / "alembic.ini"))
        config.set_main_option("script_location", str(package / "migrations"))
        with (
            patch.dict(os.environ, env),
            patch(
                "agrosphere_orchestrator.execution.executable", return_value="simulation-no-process"
            ),
            patch(
                "agrosphere_orchestrator.execution_context.runtime_identity",
                return_value={
                    "path": "simulation",
                    "version": "simulation",
                    "sha256": "simulation",
                },
            ),
        ):

            class FixtureCommandManager:
                def __init__(self, *args):
                    pass

                async def run(self, *args, **kwargs):
                    return ProcessOutcome(0, "Explicit simulated validation", "")

            command.upgrade(config, "head")
            engine = make_engine(settings.database_url)
            try:
                verifier = IsolatedVerifier(directory, settings)
                transport, validator = SimulatedTransport(), SimulatedValidator()
                scheduler = TaskScheduler(
                    engine,
                    settings,
                    adapter=transport,
                    isolation_probe=lambda *a: {"simulation": True},
                )
                services = ExistingServices(
                    engine,
                    settings,
                    scheduler=scheduler,
                    validator=validator,
                    renderer=SimulatedRenderer(),
                )
                from .execution_models import ExecutionMode
                from .orchestration_models import TaskOptions

                controller = AutonomousMilestoneController(engine, settings, services)
                # Register proposed scope first; every subsequent approval is in this isolated DB.
                design.register_requirements(
                    engine, requirements, settings.repository_manifest, settings.role_registry
                )
                request = AutonomousRequest(
                    milestone="AEO-SIM",
                    mode="controlled-delivery",
                    requirements=requirements,
                    limits=RunLimits(max_steps=100, max_poll_seconds=300),
                    task_options={
                        task.id: TaskOptions(
                            mode=ExecutionMode.WORKTREE_WRITE,
                            allowed_paths=["src"],
                            expected_outputs=["src/simulation.txt"],
                            validation_commands=["test"],
                        )
                        if task.id == "task-1"
                        else TaskOptions()
                        for task in requirements.plan.tasks
                    },
                )
                initial = controller.start(request)
                history, approved_design, quality_active, committed = [], False, False, False

                async def workflow():
                    nonlocal controller, approved_design, quality_active, committed
                    value = await controller.run(initial["run_id"])
                    for _ in range(40):
                        history.append(
                            {
                                "state": value["state"],
                                "step": value["step"],
                                "checkpoint": value["checkpoint"],
                            }
                        )
                        if value["state"] == "REPORTED":
                            return value
                        if value["state"] not in {"AWAITING_APPROVAL", "BLOCKED"}:
                            raise RuntimeError(
                                "Simulation blocked: " + json.dumps(value["checkpoint"])
                            )
                        category = value["checkpoint"]["category"]
                        grants, manifest = None, None
                        if category in {"requirements", "design"}:
                            design.decide(
                                engine, "agrosphere:AEO-SIM", category, True, verifier, [ACTOR]
                            )
                            approved_design = category == "design" or approved_design
                        elif category == "plan":
                            approve_plan(engine, settings, "AEO-SIM", verifier)
                            from .configuration import ApprovalPolicy, load_yaml
                            from .state import record_approval

                            with Session(engine) as session:
                                base_tasks = list(session.scalars(select(Task)))
                            for task in base_tasks:
                                if task.spec["operation"] == "code-write":
                                    record_approval(
                                        engine,
                                        task.id,
                                        "code-write",
                                        verifier.verify(task.id, "approved"),
                                        True,
                                        load_yaml(settings.approval_policy, ApprovalPolicy),
                                    )
                        elif category == "execution":
                            last = value["events"][-1]["payload"]["evidence"]
                            for identity in last["pending_executions"]:
                                approve_execution(engine, settings, identity, verifier)
                        elif category == "security-policy":
                            # Commit generated documentation only in the three temporary roots.
                            if not committed:
                                for root in [
                                    directory / n
                                    for n in (
                                        "estate",
                                        "agrosphere-architecture",
                                        "agrosphere-contracts",
                                    )
                                ]:
                                    from .persistence import Execution

                                    with Session(engine) as session:
                                        execution = session.scalars(
                                            select(Execution).where(Execution.state == "SUCCEEDED")
                                        ).all()
                                        write = next(
                                            (
                                                e
                                                for e in execution
                                                if e.request["repository"] == root.name
                                                and e.request["mode"] == "WORKTREE_WRITE"
                                            ),
                                            None,
                                        )
                                    if write:
                                        root = Path(write.request["worktree_path"])
                                    git(root, "add", ".")
                                    if git(root, "status", "--porcelain"):
                                        git(
                                            root,
                                            "-c",
                                            "user.name=Simulation",
                                            "-c",
                                            "user.email=simulation@example.invalid",
                                            "commit",
                                            "-m",
                                            "Simulated design artifacts",
                                        )
                                committed = True
                            quality.activate_policy(engine, settings, "AEO-SIM", verifier)
                            quality_active = True
                        elif category == "delivery-approval":
                            identity = quality.request_approval(
                                engine,
                                settings,
                                "AEO-SIM",
                                "DELIVERY_APPROVAL",
                                "delivery",
                                "simulation-reviewer",
                                "Explicit isolated fixture review",
                            )
                            quality.decide_approval(
                                engine,
                                settings,
                                identity,
                                verifier,
                                "approved",
                                "Isolated simulated human evidence review",
                            )
                        elif category == "delivery-manifest":
                            with Session(engine) as session:
                                tasks = list(session.scalars(select(Task)))
                            units = []
                            for i, task in enumerate(sorted(tasks, key=lambda t: t.external_id)):
                                root = directory / task.spec["repository"]
                                sha = git(root, "rev-parse", "HEAD")
                                from .persistence import Execution

                                with Session(engine) as session:
                                    executions = list(
                                        session.scalars(
                                            select(Execution).where(
                                                Execution.task_id == task.id,
                                                Execution.state == "SUCCEEDED",
                                            )
                                        )
                                    )
                                write = next(
                                    (
                                        e
                                        for e in executions
                                        if e.request["mode"] == "WORKTREE_WRITE"
                                    ),
                                    None,
                                )
                                head = (
                                    git(Path(write.request["worktree_path"]), "rev-parse", "HEAD")
                                    if write
                                    else sha
                                )
                                units.append(
                                    Unit(
                                        id=task.external_id,
                                        task=task.id,
                                        repository=task.spec["repository"],
                                        root=root,
                                        remote=Remote(
                                            id=i + 1,
                                            owner="simulation",
                                            name=task.spec["repository"],
                                        ),
                                        base="main",
                                        branch="aeo/simulation-" + str(i),
                                        base_sha=sha,
                                        head_sha=head,
                                    )
                                )
                            manifest = Manifest(milestone="AEO-SIM", units=units)
                            services.provider = SimulatedProvider(units)
                        elif category == "publication":
                            last = value["events"][-1]["payload"]["evidence"]["delivery"]
                            grants = {}
                            for unit in last["manifest"]["units"]:
                                spec = Unit.model_validate(unit)
                                observation = services.provider.observe(spec)
                                action = (
                                    "prepare"
                                    if not delivery.worktree(
                                        settings, last["run"], spec.id
                                    ).exists()
                                    else "push"
                                    if observation.branch_sha != spec.head_sha
                                    else "create-pr"
                                    if not observation.prs
                                    else None
                                )
                                if action:
                                    scoped = delivery.approval_scope(
                                        engine,
                                        settings,
                                        last["run"],
                                        spec.id,
                                        action,
                                        services.provider,
                                    )
                                    identity = quality.request_approval(
                                        engine,
                                        settings,
                                        "AEO-SIM",
                                        scoped["category"],
                                        scoped["action"],
                                        "simulation-publisher",
                                        "Explicit fixture publication",
                                    )
                                    quality.decide_approval(
                                        engine,
                                        settings,
                                        identity,
                                        verifier,
                                        "approved",
                                        "Isolated fixture publication only",
                                    )
                                    grants[spec.id + ":" + action] = identity
                                    break
                        else:
                            detail = value["events"][-1]["payload"].get("evidence", {})
                            raise RuntimeError(
                                "Unhandled simulation checkpoint: "
                                + category
                                + " "
                                + json.dumps(
                                    detail.get("quality", {}).get("outstanding_blockers", detail)
                                )
                            )
                        # Reconstruct the controller to prove continuation uses persisted state.
                        controller = AutonomousMilestoneController(engine, settings, services)
                        value = await controller.resume(initial["run_id"], grants, manifest)
                    raise RuntimeError("Bounded simulation driver exhausted")

                with patch(
                    "agrosphere_orchestrator.execution.CodexProcessManager", FixtureCommandManager
                ):
                    value = asyncio.run(workflow())
                validation = controller.validate(initial["run_id"])
                result = {
                    "simulation": True,
                    "repositories": 3,
                    "database": "Disposable SQLite, removed after export",
                    "real_codex": False,
                    "live_github": False,
                    "formal_completion": False,
                    "mock_transport_calls": transport.calls,
                    "failed_quality_then_repaired": validator.failed_once
                    and value["usage"]["repairs"] == 1,
                    "design_fixture_approved": approved_design,
                    "quality_fixture_activated": quality_active,
                    "restart_checkpoints": history,
                    "run": value,
                    "validation": validation,
                    "provider_pushes": services.provider.pushes,
                    "provider_prs": services.provider.creates,
                    "renderer": "Explicitly mocked; real AEO-6 diagram rendering is separate evidence",
                }
                if output_directory:
                    output_directory.mkdir(parents=True, exist_ok=True)
                    write_json(output_directory / "simulation-report.json", result)
                    (output_directory / "simulation-report.md").write_text(
                        markdown(value), encoding="utf-8"
                    )
                return result
            finally:
                engine.dispose()
