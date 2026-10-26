"""AEO-4 remediation reserves each task before mutation in its existing transaction."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_design import design_workspace as design_workspace
from test_quality import Validator, run_validation
from test_quality import quality_fixture as quality_fixture

from agrosphere_orchestrator.autonomous_models import BudgetExceeded
from agrosphere_orchestrator.persistence import AuditEvent, Task, audit
from agrosphere_orchestrator.quality import history, prepare_remediation


def test_repair_budget_refusal_rolls_back_quality_changes_and_parent_audit(engine, quality_fixture):
    f = quality_fixture
    report = run_validation(engine, f, Validator(failure="test"))
    assert report["decision"] == "NOT_READY"
    with Session(engine) as session:
        before = session.get(Task, f.task_id).state
        events = list(session.scalars(select(AuditEvent.id)))

    def refuse(session, task):
        audit(
            session, "fixture-parent", "autonomous.test-reservation", "fixture", {"task": task.id}
        )
        raise BudgetExceeded("Parent repair limit exhausted")

    with pytest.raises(BudgetExceeded):
        prepare_remediation(engine, f.settings, "FIXTURE-1", "fixture", reservation_guard=refuse)
    with Session(engine) as session:
        assert session.get(Task, f.task_id).state == before
        assert list(session.scalars(select(AuditEvent.id))) == events
        assert not history(session, f.milestone_id, "remediation.prepared")
    calls = []
    affected = prepare_remediation(
        engine,
        f.settings,
        "FIXTURE-1",
        "fixture",
        reservation_guard=lambda session, task: calls.append(task.id),
    )
    assert affected == calls == [f.task_id]
