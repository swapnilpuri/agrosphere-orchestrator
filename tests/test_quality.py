"""Governance tests use temporary Git repositories, dummy findings and mocked validators."""

import asyncio
import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_design import ACTOR, HumanFixture, approve
from test_design import design_workspace as design_workspace
from test_orchestration import orchestration_fixture as orchestration_fixture
from typer.testing import CliRunner

from agrosphere_orchestrator.cli import app
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.orchestration_store import transaction
from agrosphere_orchestrator.persistence import Task
from agrosphere_orchestrator.quality import (
    activate_policy,
    assert_delivery,
    consume_approval,
    decide_approval,
    history,
    prepare_remediation,
    readiness,
    request_approval,
    validate,
)
from agrosphere_orchestrator.quality_adapters import interpret
from agrosphere_orchestrator.quality_models import Gate, QualityPolicy
from agrosphere_orchestrator.quality_store import record


class Validator:
    def __init__(self, failure=None, findings=None, version="fixture-v1"):
        self.failure, self.findings, self.version = failure, findings or [], version

    async def evaluate(self, gate, repository, command):
        raw = {"exit_code": 1 if gate.id == self.failure else 0, "stdout": "fixture", "stderr": ""}
        if gate.format == "json":
            raw["stdout"] = json.dumps(
                {
                    "validator_version": self.version,
                    "findings": self.findings if gate.type == "security" else [],
                    "test_cases": {
                        "business.test": "failed" if gate.id == self.failure else "passed"
                    },
                }
            )
        return raw


@pytest.fixture
def quality_fixture(engine, design_workspace, tmp_path):
    f = design_workspace
    approve(engine, f)
    with Session(engine) as session, session.begin():
        task = session.scalar(select(Task))
        task.state = "succeeded"
        f.task_id, f.milestone_id = task.id, task.milestone_id
    gates = []
    for kind in ["build", "test", "security", "architecture", "contract", "documentation"]:
        gates.append(
            {
                "id": kind,
                "type": kind,
                "repository": "estate",
                "command": kind,
                "validator_version": "fixture-v1",
                "format": "json" if kind in {"security", "test"} else "exit",
                "retry_eligible": kind in {"build", "test"},
                "tasks": ["implement"],
            }
        )
    f.policy = QualityPolicy.model_validate(
        {
            "id": "fixture",
            "version": 1,
            "gates": gates,
            "required_review_roles": [],
            "criteria": [
                {
                    "requirement_id": "REQ-1",
                    "criterion_id": "AC-1",
                    "criterion_text": f.inputs.requirements[0].acceptance_criteria[0],
                    "task": "implement",
                    "gate": "test",
                    "test_case": "business.test",
                }
            ],
        }
    )
    policy_path = tmp_path / "quality.json"
    policy_path.write_text(f.policy.model_dump_json())
    commands = tmp_path / "commands.json"
    commands.write_text(
        json.dumps(
            {
                "validation_commands": [
                    {"id": g.id, "argv": ["fixture-validator", g.id]} for g in f.policy.gates
                ]
            }
        )
    )
    f.settings = Settings(
        _env_file=None,
        quality_policy=policy_path,
        execution_policy=commands,
        governance_approvers=[ACTOR],
        repository_manifest=f.manifest,
    )
    activate_policy(engine, f.settings, "FIXTURE-1", HumanFixture(), "fixture")
    return f


def run_validation(engine, f, validator=None):
    return asyncio.run(
        validate(engine, f.settings, "FIXTURE-1", "fixture", validator or Validator())
    )


def request(
    engine, f, category="DELIVERY_APPROVAL", action="delivery", agent="developer", expiry=900
):
    return request_approval(
        engine,
        f.settings,
        "FIXTURE-1",
        category,
        action,
        agent,
        "Fixture review",
        expiry,
        "fixture",
    )


def test_quality_human_approval_and_one_time_consumption(engine, quality_fixture):
    f = quality_fixture
    report = run_validation(engine, f)
    assert report["decision"] == "READY_FOR_APPROVAL"
    assert report["acceptance_criteria"][0]["result"] == "VERIFIED"
    assert report["evidence"] and report["report_hash"]
    identity = request(engine, f)
    decide_approval(
        engine, f.settings, identity, HumanFixture(), "approved", "Reviewed exact fixture evidence"
    )
    assert (
        readiness(engine, f.settings, "FIXTURE-1", "fixture")["decision"] == "APPROVED_FOR_DELIVERY"
    )
    consume_approval(engine, f.settings, identity, "DELIVERY_APPROVAL", "delivery")
    with pytest.raises(PermissionError):
        consume_approval(engine, f.settings, identity, "DELIVERY_APPROVAL", "delivery")


@pytest.mark.parametrize("failure", ["build", "test", "architecture", "contract", "documentation"])
def test_failed_gate_blocks_and_retains_evidence(engine, quality_fixture, failure):
    f = quality_fixture
    report = run_validation(engine, f, Validator(failure))
    assert report["decision"] == "NOT_READY"
    assert report["evidence"]
    with pytest.raises(PermissionError):
        request(engine, f)
    if failure in {"architecture", "contract"}:
        with Session(engine) as session:
            assert history(session, f.milestone_id, "architecture.review")


def test_missing_validator_is_blocked(engine, quality_fixture):
    f = quality_fixture
    f.settings.execution_policy.write_text('{"validation_commands": []}')
    report = run_validation(engine, f)
    assert report["decision"] == "BLOCKED"
    assert all(g["state"] == "BLOCKED" for g in report["gate_results"])


def test_invalid_test_evidence_is_error(engine, quality_fixture):
    class Invalid(Validator):
        async def evaluate(self, gate, repository, command):
            raw = await super().evaluate(gate, repository, command)
            if gate.id == "test":
                raw["stdout"] = (
                    '{"validator_version": "fixture-v1", "findings": [], "test_cases": {"business.test": "trust me"}}'
                )
            return raw

    report = run_validation(engine, quality_fixture, Invalid())
    assert report["decision"] == "BLOCKED"
    assert report["acceptance_criteria"][0]["result"] == "NOT_EVALUATED"


def test_changed_artifact_invalidates_evidence_and_approval(engine, quality_fixture):
    f = quality_fixture
    run_validation(engine, f)
    identity = request(engine, f)
    decide_approval(engine, f.settings, identity, HumanFixture(), "approved", "Reviewed")
    (f.repos["estate"] / "new.py").write_text("# Changed after validation")
    report = readiness(engine, f.settings, "FIXTURE-1", "fixture")
    assert report["decision"] == "BLOCKED"
    with pytest.raises(PermissionError):
        consume_approval(engine, f.settings, identity, "DELIVERY_APPROVAL", "delivery")


def test_expired_validation(engine, quality_fixture):
    f = quality_fixture
    run_validation(engine, f)
    with transaction(engine) as session:
        last = history(session, f.milestone_id, "validation.completed")[-1]
        payload = {**last.payload, "ended_at": (datetime.now(UTC) - timedelta(days=5)).isoformat()}
        record(session, f.milestone_id, "validation.completed", payload)
    assert "expired" in str(
        readiness(engine, f.settings, "FIXTURE-1", "fixture")["outstanding_blockers"]
    )


@pytest.mark.parametrize("name", ["synthetic-secret", "dependency-CVE-fixture"])
def test_security_exception_is_human_scoped_and_expiring(engine, quality_fixture, name):
    f = quality_fixture
    findings = [
        {
            "id": name,
            "message": "Dummy credential or vulnerable fixture dependency",
            "severity": "CRITICAL",
        }
    ]
    assert run_validation(engine, f, Validator(findings=findings))["decision"] == "NOT_READY"
    identity = request(engine, f, "SECURITY_EXCEPTION", "security:" + name)
    with pytest.raises(PermissionError):
        decide_approval(
            engine, f.settings, identity, HumanFixture("agent"), "approved", "Not authorized"
        )
    decide_approval(
        engine, f.settings, identity, HumanFixture(), "approved", "Fixture exception only"
    )
    report = readiness(engine, f.settings, "FIXTURE-1", "fixture")
    assert report["decision"] == "READY_FOR_APPROVAL"
    assert report["security_findings"] and report["exceptions_and_waivers"]


@pytest.mark.parametrize("decision", ["rejected", "revoked"])
def test_rejection_and_revocation_cannot_be_bypassed(engine, quality_fixture, decision):
    f = quality_fixture
    run_validation(engine, f)
    identity = request(engine, f)
    if decision == "revoked":
        decide_approval(engine, f.settings, identity, HumanFixture(), "approved", "Reviewed")
    decide_approval(engine, f.settings, identity, HumanFixture(), decision, "Stop")
    with pytest.raises(PermissionError):
        consume_approval(engine, f.settings, identity, "DELIVERY_APPROVAL", "delivery")
    with pytest.raises(PermissionError):
        request(engine, f)
    with pytest.raises(PermissionError):
        decide_approval(engine, f.settings, identity, HumanFixture(), "approved", "Retry")


def test_self_approval_and_wrong_action_rejected(engine, quality_fixture):
    f = quality_fixture
    run_validation(engine, f)
    identity = request(engine, f, "PRIVILEGED_EXECUTION", "self-test", agent=ACTOR)
    with pytest.raises(PermissionError):
        decide_approval(engine, f.settings, identity, HumanFixture(), "approved", "Self")
    with pytest.raises(PermissionError):
        consume_approval(engine, f.settings, identity, "DEPLOYMENT_APPROVAL", "other-repo")


def test_unauthorized_policy_change_rejected(engine, quality_fixture):
    f = quality_fixture
    altered = f.policy.model_dump(mode="json")
    altered["medium_security_blocks"] = False
    f.settings.quality_policy.write_text(json.dumps(altered))
    with pytest.raises(PermissionError, match="Unauthorized policy"):
        run_validation(engine, f)
    with pytest.raises(PermissionError, match="increasing version"):
        activate_policy(engine, f.settings, "FIXTURE-1", HumanFixture(), "fixture")


def test_append_only_evidence_and_audit(engine, quality_fixture):
    run_validation(engine, quality_fixture)
    for table in ["governance_records", "validation_evidence", "audit_events"]:
        for verb in ["UPDATE", "DELETE"]:
            with pytest.raises(IntegrityError):
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            f"{verb} {table} SET id=id"
                            if verb == "UPDATE"
                            else f"DELETE FROM {table}"
                        )
                    )


def test_remediation_bounded_and_revalidation(engine, quality_fixture):
    f = quality_fixture
    run_validation(engine, f, Validator("build"))
    assert prepare_remediation(engine, f.settings, "FIXTURE-1", "fixture") == [f.task_id]
    assert prepare_remediation(engine, f.settings, "FIXTURE-1", "fixture") == []
    with Session(engine) as session, session.begin():
        session.get(Task, f.task_id).state = "succeeded"
    assert run_validation(engine, f)["decision"] == "READY_FOR_APPROVAL"
    with Session(engine) as session:
        assert history(session, f.milestone_id, "remediation.revalidated")


def test_existing_delivery_guard_cannot_bypass_missing_evidence(engine, quality_fixture):
    f = quality_fixture
    with transaction(engine) as session:
        from agrosphere_orchestrator.persistence import Milestone

        with pytest.raises(PermissionError, match="AEO-4"):
            assert_delivery(session, f.settings, session.get(Milestone, f.milestone_id))


def test_default_policy_missing_and_review_roles_fail_closed(engine, quality_fixture):
    f = quality_fixture
    policy = f.policy.model_dump(mode="json")
    policy["version"] = 2
    policy["required_review_roles"] = [
        "qa-engineer",
        "security-engineer",
        "solution-architect",
        "technical-writer",
    ]
    f.settings.quality_policy.write_text(json.dumps(policy))
    activate_policy(engine, f.settings, "FIXTURE-1", HumanFixture(), "fixture")
    report = run_validation(engine, f)
    assert report["decision"] == "BLOCKED"
    assert sum("review role" in b for b in report["outstanding_blockers"]) == 4


def test_junit_coverage_and_sarif_adapters():
    test_gate = Gate(
        id="test",
        type="test",
        repository="repo",
        command="test",
        format="junit",
        validator_version="v1",
    )
    raw = {
        "exit_code": 0,
        "stdout": '<testsuite><testcase classname="orders" name="accept"/><testcase name="bad"><failure/></testcase></testsuite>',
    }
    assert interpret(test_gate, raw)["state"] == "FAILED"
    assert interpret(test_gate, raw)["test_cases"]["orders.accept"] == "passed"
    for stdout in ["trust me", "<testsuite/>", "<!DOCTYPE x><testsuite/>"]:
        with pytest.raises(ValueError):
            interpret(test_gate, {"exit_code": 0, "stdout": stdout})
    coverage = Gate(
        id="coverage",
        type="coverage",
        repository="repo",
        command="coverage",
        format="coverage",
        minimum_coverage=80,
        validator_version="v1",
    )
    assert (
        interpret(coverage, {"exit_code": 0, "stdout": '{"totals": {"percent_covered": 79.9}}'})[
            "state"
        ]
        == "FAILED"
    )
    scanner = Gate(
        id="scanner",
        type="security",
        repository="repo",
        command="scanner",
        format="sarif",
        validator_version="v1",
    )
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"version": "v1"}},
                "results": [
                    {
                        "ruleId": "fixture",
                        "message": {"text": "Dummy secret"},
                        "suppressions": [{"kind": "inSource"}],
                        "properties": {"security-severity": "9.8"},
                    }
                ],
            }
        ],
    }
    assert (
        interpret(scanner, {"exit_code": 0, "stdout": json.dumps(sarif)})["findings"][0]["severity"]
        == "CRITICAL"
    )


def test_skip_requires_explicit_policy():
    with pytest.raises(ValueError):
        Gate(
            id="bad",
            type="test",
            repository="repo",
            command="test",
            validator_version="v1",
            skip=True,
        )


def test_cli_governance_commands(monkeypatch, quality_fixture):
    f = quality_fixture
    monkeypatch.setenv("AEO_QUALITY_POLICY", str(f.settings.quality_policy))
    monkeypatch.setenv("AEO_GOVERNANCE_APPROVERS", json.dumps([ACTOR]))
    monkeypatch.setenv("AEO_EXECUTION_POLICY", str(f.settings.execution_policy))
    runner = CliRunner()
    assert runner.invoke(app, ["quality", "policies"]).exit_code == 0
    for args in [["quality", "report"], ["security", "report"], ["milestone", "readiness"]]:
        result = runner.invoke(app, [*args, "--milestone", "FIXTURE-1", "--project", "fixture"])
        assert result.exit_code == 0, result.output
        assert json.loads(result.output)["decision"] == "BLOCKED"
    assert runner.invoke(app, ["approvals", "pending"]).exit_code == 0


def test_native_documentation_and_architecture_checks(tmp_path):
    from agrosphere_orchestrator.quality_adapters import architecture, documentation

    docs = Gate(
        id="docs",
        type="documentation",
        repository="repo",
        evaluator="files",
        required_files=["design.puml"],
        validator_version="v1",
    )
    assert documentation(docs, tmp_path)["state"] == "FAILED"
    (tmp_path / "design.puml").write_text("@startuml\nA -> B\n@enduml")
    assert documentation(docs, tmp_path)["state"] == "PASSED"
    arch = Gate(
        id="arch",
        type="architecture",
        repository="repo",
        evaluator="architecture",
        validator_version="v1",
        architecture_rules=[
            {
                "id": "ownership",
                "repository": "repo",
                "path": "design.puml",
                "kind": "database-owner",
                "value": "another-service",
            },
            {
                "id": "dependency",
                "repository": "repo",
                "path": "design.puml",
                "kind": "prohibited-token",
                "value": "A -> B",
            },
        ],
    )
    assert len(architecture(arch, tmp_path)["findings"]) == 2
    with pytest.raises(PermissionError):
        documentation(docs.model_copy(update={"required_files": ["../outside"]}), tmp_path)


def test_evidence_integrity_and_command_policy_change(engine, quality_fixture):
    f = quality_fixture
    run_validation(engine, f)
    commands = json.loads(f.settings.execution_policy.read_text())
    commands["validation_commands"][0]["argv"] = ["different-validator"]
    f.settings.execution_policy.write_text(json.dumps(commands))
    report = readiness(engine, f.settings, "FIXTURE-1", "fixture")
    assert report["decision"] == "BLOCKED"
    from agrosphere_orchestrator.quality_store import read_blob

    with Session(engine) as session:
        with pytest.raises(PermissionError):
            read_blob(session, "a" * 64)


def test_expired_approval_and_exception_rejected(engine, quality_fixture, monkeypatch):
    import agrosphere_orchestrator.quality as quality_module

    f = quality_fixture
    run_validation(engine, f)
    identity = request(engine, f, "PRIVILEGED_EXECUTION", "expiry-test", expiry=1)
    decide_approval(engine, f.settings, identity, HumanFixture(), "approved", "Fixture only")
    real_datetime = datetime

    class FutureClock(real_datetime):
        @classmethod
        def now(cls, tz=None):
            return real_datetime.now(tz) + timedelta(seconds=2)

    monkeypatch.setattr(quality_module, "datetime", FutureClock)
    with pytest.raises(PermissionError, match="expired"):
        consume_approval(engine, f.settings, identity, "PRIVILEGED_EXECUTION", "expiry-test")
    run_validation(
        engine,
        f,
        Validator(findings=[{"id": "fixture", "message": "Dummy expiry risk", "severity": "HIGH"}]),
    )
    identity = request(engine, f, "SECURITY_EXCEPTION", "security:fixture", expiry=1)
    # The future clock advances request expiry as well; verify expired absolute request separately.
    monkeypatch.setattr(quality_module, "datetime", real_datetime)
    decide_approval(engine, f.settings, identity, HumanFixture(), "approved", "Fixture exception")

    class LaterClock(real_datetime):
        @classmethod
        def now(cls, tz=None):
            return real_datetime.now(tz) + timedelta(seconds=10)

    monkeypatch.setattr(quality_module, "datetime", LaterClock)
    with pytest.raises(PermissionError, match="expired"):
        consume_approval(engine, f.settings, identity, "SECURITY_EXCEPTION", "security:fixture")


def test_execution_evidence_requires_matching_validated_snapshot(engine, quality_fixture):
    f = quality_fixture
    policy = f.policy.model_dump(mode="json")
    policy["version"] = 2
    policy["gates"][0]["evaluator"] = "execution"
    f.settings.quality_policy.write_text(json.dumps(policy))
    activate_policy(engine, f.settings, "FIXTURE-1", HumanFixture(), "fixture")
    report = run_validation(engine, f)
    assert report["gate_results"][0]["state"] == "BLOCKED"


def test_multi_role_scheduler_to_quality_delivery(engine, orchestration_fixture, tmp_path):
    from test_orchestration import granted_batch, scheduler

    f = orchestration_fixture
    service = scheduler(engine, f)

    async def workflow():
        for _ in range(12):
            batch = await granted_batch(engine, f, service)
            if not batch["results"]:
                break

    asyncio.run(workflow())
    commands = json.loads(f.settings.execution_policy.read_text())
    commands["validation_commands"].append({"id": "quality-check", "argv": ["fixture-quality"]})
    f.settings.execution_policy.write_text(json.dumps(commands))
    gates = []
    for repo in ["estate", "agrosphere-architecture"]:
        for kind in ["build", "test", "security", "architecture", "contract", "documentation"]:
            gates.append(
                {
                    "id": repo + "-" + kind,
                    "type": kind,
                    "repository": repo,
                    "command": "fixture-check" if kind == "build" else "quality-check",
                    "evaluator": "execution" if kind == "build" else "command",
                    "format": "json" if kind in {"test", "security"} else "exit",
                    "validator_version": "fixture-v1",
                }
            )
    policy = QualityPolicy.model_validate(
        {
            "id": "end-to-end",
            "version": 1,
            "gates": gates,
            "criteria": [
                {
                    "requirement_id": "REQ-1",
                    "criterion_id": "AC-1",
                    "criterion_text": f.inputs.requirements[0].acceptance_criteria[0],
                    "task": "dev-a",
                    "gate": "estate-test",
                    "test_case": "business.test",
                }
            ],
        }
    )
    f.settings.quality_policy = tmp_path / "quality.json"
    f.settings.quality_policy.write_text(policy.model_dump_json())
    f.settings.governance_approvers = [ACTOR]
    activate_policy(engine, f.settings, "FIXTURE-1", HumanFixture(), "fixture")
    report = run_validation(engine, f)
    assert report["decision"] == "READY_FOR_APPROVAL", report
    identity = request(engine, f)
    decide_approval(
        engine,
        f.settings,
        identity,
        HumanFixture(),
        "approved",
        "Reviewed complete mocked multi-role evidence",
    )
    assert (
        readiness(engine, f.settings, "FIXTURE-1", "fixture")["decision"] == "APPROVED_FOR_DELIVERY"
    )


def test_expired_waiver_restores_security_blocking(engine, quality_fixture, monkeypatch):
    import agrosphere_orchestrator.quality as quality_module

    f = quality_fixture
    finding = {"id": "risk", "message": "Dummy fixture risk", "severity": "HIGH"}
    run_validation(engine, f, Validator(findings=[finding]))
    identity = request(engine, f, "SECURITY_EXCEPTION", "security:risk", expiry=1)
    decide_approval(
        engine, f.settings, identity, HumanFixture(), "approved", "Temporary fixture waiver"
    )
    assert readiness(engine, f.settings, "FIXTURE-1", "fixture")["decision"] == "READY_FOR_APPROVAL"
    real_datetime = datetime

    class FutureClock(real_datetime):
        @classmethod
        def now(cls, tz=None):
            return real_datetime.now(tz) + timedelta(seconds=5)

    monkeypatch.setattr(quality_module, "datetime", FutureClock)
    report = readiness(engine, f.settings, "FIXTURE-1", "fixture")
    assert report["decision"] == "NOT_READY"
    assert report["security_findings"] and not report["exceptions_and_waivers"]


def test_runtime_reads_cannot_grant_home_roots_or_credentials():
    from pathlib import Path

    from agrosphere_orchestrator.execution_models import ValidationCommand

    for value in [
        str(Path.home()),
        str(Path.home().anchor),
        str(Path.home() / ".aws"),
        "relative/runtime",
    ]:
        with pytest.raises(ValueError):
            ValidationCommand(id="tool", argv=["tool"], read_paths=[value])


def test_waiver_cannot_preapprove_unknown_or_changed_finding(engine, quality_fixture):
    f = quality_fixture
    run_validation(engine, f)
    with pytest.raises(PermissionError, match="existing deterministic"):
        request(engine, f, "SECURITY_EXCEPTION", "security:invented")
    run_validation(
        engine,
        f,
        Validator(findings=[{"id": "risk", "message": "Original dummy risk", "severity": "HIGH"}]),
    )
    identity = request(engine, f, "SECURITY_EXCEPTION", "security:risk")
    decide_approval(
        engine, f.settings, identity, HumanFixture(), "approved", "Exact fixture risk only"
    )
    report = run_validation(
        engine,
        f,
        Validator(
            findings=[{"id": "risk", "message": "Different dummy risk", "severity": "CRITICAL"}]
        ),
    )
    assert report["decision"] == "NOT_READY"
