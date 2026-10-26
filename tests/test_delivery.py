"""Delivery uses disposable repositories/databases and a stateful fake GitHub port."""

import subprocess
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_design import HumanFixture
from test_design import design_workspace as design_workspace
from test_orchestration import orchestration_fixture as orchestration_fixture
from test_quality import quality_fixture as quality_fixture
from test_quality import run_validation

from agrosphere_orchestrator import delivery, quality
from agrosphere_orchestrator.delivery_models import (
    Check,
    DeliveryError,
    Manifest,
    Observation,
    Policy,
    PullRequest,
    Remote,
    RequiredCheck,
    Review,
    Unit,
)
from agrosphere_orchestrator.delivery_store import DeliveryOperation
from agrosphere_orchestrator.execution_workspace import git
from agrosphere_orchestrator.orchestration_store import ResourceLease, acquire, transaction
from agrosphere_orchestrator.persistence import Task, make_engine
from agrosphere_orchestrator.quality_store import digest


class Provider:
    def __init__(self, unit):
        self.unit = unit
        self.value = Observation(
            remote=unit.remote,
            principal="publisher",
            can_push=True,
            base_sha=unit.base_sha,
            policy=Policy(known=True),
        )
        self.pushes = self.creates = 0
        self.crash = None
        self.body = None
        self.fail_observe = False
        self.other = {}

    def observe(self, unit):
        if self.fail_observe:
            raise DeliveryError("RATE_LIMIT", "Fixture provider unavailable")
        return self.other.get(unit.id, self.value).model_copy(deep=True)

    def push(self, unit, worktree):
        self.pushes += 1
        self.value.branch_sha = unit.head_sha
        if self.crash == "push":
            raise TimeoutError("fixture response loss")

    def create_pr(self, unit, title, body):
        self.creates += 1
        self.body = body
        pr = self.pr()
        self.value.prs = [pr]
        if self.crash == "create-pr":
            raise TimeoutError("fixture response loss")
        return pr

    def pr(self):
        u = self.unit
        return PullRequest(
            id=11,
            number=1,
            url="https://github.com/acme/estate/pull/1",
            repository_id=u.remote.id,
            head_repository_id=u.remote.id,
            base=u.base,
            branch=u.branch,
            base_sha=u.base_sha,
            head_sha=u.head_sha,
            state="open",
            author="author",
            mergeable=True,
        )

    def dependency_available(self, unit, observation):
        return bool(
            observation.prs
            and observation.prs[0].state == "merged"
            and observation.prs[0].merge_sha == observation.base_sha
        )


@pytest.fixture
def delivery_fixture(engine, quality_fixture, tmp_path):
    f = quality_fixture
    root = f.repos["estate"]
    readme = root / "README.md"
    readme.write_bytes(readme.read_bytes().replace(b"\r\n", b"\n"))
    subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=f@example.invalid",
            "commit",
            "-m",
            "fixture approved documentation",
        ],
        check=True,
        capture_output=True,
    )
    git(root, "remote", "add", "origin", "https://github.com/acme/estate.git")
    sha = git(root, "rev-parse", "HEAD")
    f.settings.github_remote_writes = True
    f.settings.github_repositories = ["acme/estate"]
    f.settings.delivery_root = tmp_path / "isolated-delivery"
    f.unit = Unit(
        id="estate",
        task=f.task_id,
        repository="estate",
        root=root,
        remote=Remote(id=10, owner="acme", name="estate"),
        base="main",
        branch="aeo/fixture-delivery",
        base_sha=sha,
        head_sha=sha,
    )
    f.manifest = Manifest(project="fixture", milestone="FIXTURE-1", units=[f.unit])
    f.run = delivery.plan(engine, f.settings, f.manifest)
    f.provider = Provider(f.unit)
    assert run_validation(engine, f)["decision"] == "READY_FOR_APPROVAL"
    return f


def grant(engine, f, action, expiry=900):
    scoped = delivery.approval_scope(engine, f.settings, f.run, f.unit.id, action, f.provider)
    request = quality.request_approval(
        engine,
        f.settings,
        "FIXTURE-1",
        "PRIVILEGED_EXECUTION",
        scoped["action"],
        "delivery-engine",
        "Fixture exact action",
        expires_seconds=expiry,
        project="fixture",
    )
    quality.decide_approval(
        engine, f.settings, request, HumanFixture(), "approved", "Fixture human approval"
    )
    return request


def execute(engine, f, action):
    return delivery.mutate(
        engine, f.settings, f.run, f.unit.id, action, grant(engine, f, action), f.provider
    )


def prepare(engine, f):
    execute(engine, f, "prepare")


def publish(engine, f):
    prepare(engine, f)
    execute(engine, f, "push")
    execute(engine, f, "create-pr")


def test_end_to_end_exact_authority_and_delivery_evidence(engine, delivery_fixture):
    f = delivery_fixture
    publish(engine, f)
    result = delivery.reconcile(engine, f.settings, f.run, f.unit.id, f.provider)
    assert result["readiness"] == "READY_FOR_AUTHORIZED_MERGE"
    assert f.provider.pushes == f.provider.creates == 1
    assert f.task_id in f.provider.body and "Validation and security evidence" in f.provider.body
    assert "Design:" in f.provider.body and "Related PRs:" in f.provider.body
    observed = result["units"][0]["latest"]["observation"]
    assert observed["branch_sha"] == f.unit.head_sha
    assert observed["prs"][0]["id"] == 11
    assert result["units"][0]["history"]
    assert result["report_hash"] == digest({k: v for k, v in result.items() if k != "report_hash"})
    assert f.unit.head_sha in delivery.markdown(result)
    assert not result["merge_executed"]
    (f.unit.root.parent / "delivery-report.json").write_text(
        __import__("json").dumps(
            {
                "simulation": True,
                "provider": "stateful fake GitHub",
                "push_count": f.provider.pushes,
                "pr_create_count": f.provider.creates,
                "pr_body": f.provider.body,
                "report": result,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    # Existing exact PR is reused, even when no second mutation grant exists.
    delivery.mutate(engine, f.settings, f.run, f.unit.id, "create-pr", "unused", f.provider)
    assert f.provider.creates == 1


@pytest.mark.parametrize("action", ["push", "create-pr"])
def test_response_loss_restart_reconciles_without_replay(engine, delivery_fixture, action):
    f = delivery_fixture
    prepare(engine, f)
    if action == "create-pr":
        execute(engine, f, "push")
    approval = grant(engine, f, action)
    f.provider.crash = action
    with pytest.raises(DeliveryError, match="uncertain"):
        delivery.mutate(engine, f.settings, f.run, f.unit.id, action, approval, f.provider)
    with Session(engine) as session:
        assert list(session.scalars(select(ResourceLease)))
    fresh = make_engine(str(engine.url))
    try:
        report = delivery.reconcile(fresh, f.settings, f.run, f.unit.id, f.provider)
        assert report["units"][0]["state"] != "RECOVERY_REQUIRED"
        with Session(fresh) as session:
            assert not list(session.scalars(select(ResourceLease)))
        delivery.mutate(fresh, f.settings, f.run, f.unit.id, action, approval, f.provider)
        assert f.provider.creates <= 1 and f.provider.pushes == 1
    finally:
        fresh.dispose()


def test_uncertain_absence_retains_lease_and_blocks_blind_retry(engine, delivery_fixture):
    f = delivery_fixture
    prepare(engine, f)
    approval = grant(engine, f, "push")

    def crash(*args):
        raise TimeoutError("Before actual push")

    f.provider.push = crash
    with pytest.raises(DeliveryError):
        delivery.mutate(engine, f.settings, f.run, f.unit.id, "push", approval, f.provider)
    result = delivery.reconcile(engine, f.settings, f.run, f.unit.id, f.provider)
    assert result["units"][0]["state"] == "RECOVERY_REQUIRED"
    with pytest.raises(DeliveryError, match="reconciled"):
        delivery.mutate(engine, f.settings, f.run, f.unit.id, "push", approval, f.provider)


def test_missing_quality_policy_and_unauthorized_grant_never_write(
    engine, delivery_fixture, monkeypatch
):
    f = delivery_fixture
    with pytest.raises(DeliveryError, match="authorization"):
        delivery.mutate(engine, f.settings, f.run, f.unit.id, "prepare", "missing", f.provider)
    monkeypatch.setattr(
        quality,
        "active_policy",
        lambda *args: (_ for _ in ()).throw(PermissionError("No authenticated policy")),
    )
    with pytest.raises(PermissionError, match="policy"):
        delivery.approval_scope(engine, f.settings, f.run, f.unit.id, "push", f.provider)
    assert f.provider.pushes == f.provider.creates == 0


@pytest.mark.parametrize(
    "change", ["expired", "revoked", "base", "head", "remote", "policy", "quality", "disabled"]
)
def test_stale_or_revoked_authority_blocks_before_write(engine, delivery_fixture, change):
    f = delivery_fixture
    prepare(engine, f)
    approval = grant(engine, f, "push", expiry=1 if change == "expired" else 900)
    if change == "expired":
        # Time travel avoids mutating append-only approval history.
        import agrosphere_orchestrator.quality as q

        class Future(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.now(UTC) + timedelta(seconds=2)

        from unittest.mock import patch

        with patch.object(q, "datetime", Future), pytest.raises(PermissionError, match="expired"):
            delivery.mutate(engine, f.settings, f.run, f.unit.id, "push", approval, f.provider)
        return
    if change == "revoked":
        quality.decide_approval(
            engine, f.settings, approval, HumanFixture(), "revoked", "fixture revoke"
        )
    elif change == "base":
        f.provider.value.base_sha = "f" * 40
    elif change == "head":
        f.provider.value.branch_sha = "f" * 40
    elif change == "remote":
        f.provider.value.remote.id = 123
    elif change == "policy":
        f.provider.value.policy.approvals = 2
    elif change == "quality":
        (f.unit.root / "README.md").write_text("Unvalidated change")
    else:
        f.settings.github_remote_writes = False
    with pytest.raises((PermissionError, DeliveryError)):
        delivery.mutate(engine, f.settings, f.run, f.unit.id, "push", approval, f.provider)
    assert f.provider.pushes == 0


def test_repository_lease_conflict_rolls_back_authorization_consumption(engine, delivery_fixture):
    f = delivery_fixture
    approval = grant(engine, f, "prepare")
    with transaction(engine) as session:
        assert acquire(session, f.task_id, "scheduler", ["repository:estate"], True, 10)
    with pytest.raises(DeliveryError, match="lease"):
        delivery.mutate(engine, f.settings, f.run, f.unit.id, "prepare", approval, f.provider)
    with Session(engine) as session:
        assert not list(session.scalars(select(DeliveryOperation)))
        assert not quality.history(session, f.milestone_id, "approval.consumed")


def test_dirty_source_preserved_and_exact_worktree_reused(engine, delivery_fixture):
    f = delivery_fixture
    dirty = f.unit.root / "scratch.txt"
    dirty.write_text("Original dirty source")
    assert run_validation(engine, f)["decision"] == "READY_FOR_APPROVAL"
    prepare(engine, f)
    target = delivery.worktree(f.settings, f.run, f.unit.id)
    assert dirty.read_text() == "Original dirty source"
    assert not (target / "scratch.txt").exists()
    delivery.prepare_local(f.unit, target)
    with pytest.raises(DeliveryError, match="validated artifact tree"):
        execute(engine, f, "push")


def test_history_append_only_and_changed_observations_preserved(engine, delivery_fixture):
    f = delivery_fixture
    prepare(engine, f)
    delivery.reconcile(engine, f.settings, f.run, f.unit.id, f.provider)
    f.provider.fail_observe = True
    result = delivery.reconcile(engine, f.settings, f.run, f.unit.id, f.provider)
    assert result["units"][0]["latest"]["blockers"] == ["RATE_LIMIT"]
    assert len(result["units"][0]["history"]) == 4
    for table in ("delivery_runs", "delivery_events", "delivery_operations"):
        with pytest.raises(IntegrityError, match="append-only"):
            with engine.begin() as connection:
                connection.execute(text("DELETE FROM " + table))
    assert result["readiness"] == "BLOCKED"


@pytest.mark.parametrize("state", ["closed", "merged", "multiple", "foreign", "stale"])
def test_duplicate_terminal_and_conflicting_prs_never_create(engine, delivery_fixture, state):
    f = delivery_fixture
    pr = f.provider.pr()
    if state in {"closed", "merged"}:
        pr.state = state
    elif state == "foreign":
        pr.head_repository_id = 666
    elif state == "stale":
        pr.head_sha = "a" * 40
    f.provider.value.prs = [pr, pr.model_copy(update={"id": 22})] if state == "multiple" else [pr]
    with pytest.raises(DeliveryError):
        delivery.mutate(engine, f.settings, f.run, f.unit.id, "create-pr", "missing", f.provider)
    assert f.provider.creates == 0


def test_manifest_idempotence_and_existing_task_scope(engine, delivery_fixture):
    f = delivery_fixture
    assert delivery.plan(engine, f.settings, f.manifest) == f.run
    changed = f.manifest.model_copy(deep=True)
    changed.units[0].task = "unknown"
    with pytest.raises(DeliveryError, match="immutable"):
        delivery.plan(engine, f.settings, changed)


def ready_observation(tmp_path):
    unit = Unit(
        id="a",
        task="task",
        repository="estate",
        root=tmp_path,
        remote=Remote(id=1, owner="acme", name="estate"),
        base="main",
        branch="aeo/a",
        base_sha="a" * 40,
        head_sha="b" * 40,
    )
    pr = PullRequest(
        id=1,
        number=1,
        url="https://github.com/acme/estate/pull/1",
        repository_id=1,
        head_repository_id=1,
        base="main",
        branch="aeo/a",
        base_sha=unit.base_sha,
        head_sha=unit.head_sha,
        state="open",
        author="author",
        mergeable=True,
        review_decision="APPROVED",
    )
    observation = Observation(
        remote=unit.remote,
        principal="publisher",
        can_push=True,
        base_sha=unit.base_sha,
        branch_sha=unit.head_sha,
        prs=[pr],
        policy=Policy(known=True, checks=[RequiredCheck(name="required", app_id=10)], approvals=1),
        checks=[
            Check(
                name="required",
                sha=unit.head_sha,
                state="success",
                raw_status="completed",
                app_id=10,
            )
        ],
        reviews=[
            Review(
                id=1,
                actor="human",
                actor_type="User",
                sha=unit.head_sha,
                state="APPROVED",
                submitted_at="2026-01-01T00:00:00Z",
            )
        ],
    )
    return unit, observation


@pytest.mark.parametrize(
    "change",
    [
        "missing-check",
        "optional",
        "stale-check",
        "wrong-app",
        "failed",
        "cancelled",
        "skipped",
        "timed_out",
        "queued",
        "unknown-policy",
        "unsupported",
        "bot",
        "self",
        "dismissed",
        "stale-review",
        "changes-requested",
        "codeowners",
        "draft",
        "strict",
        "base",
    ],
)
def test_readiness_requires_exact_head_policy_ci_and_humans(tmp_path, change):
    unit, observed = ready_observation(tmp_path)
    assert delivery.blockers(unit, observed) == []
    if change == "missing-check":
        observed.checks = []
    elif change == "optional":
        observed.checks[0].name = "optional"
    elif change == "stale-check":
        observed.checks[0].sha = "f" * 40
    elif change == "wrong-app":
        observed.checks[0].app_id = 9
    elif change in {"failed", "cancelled", "skipped", "timed_out", "queued"}:
        observed.checks[0].state = change
    elif change == "unknown-policy":
        observed.policy.known = False
    elif change == "unsupported":
        observed.policy.unsupported = ["required_workflows"]
    elif change == "bot":
        observed.reviews[0].actor_type = "Bot"
    elif change == "self":
        observed.reviews[0].actor = "author"
    elif change == "dismissed":
        observed.reviews[0].state = "DISMISSED"
    elif change == "stale-review":
        observed.reviews[0].sha = "f" * 40
    elif change == "changes-requested":
        observed.reviews[0].state = "CHANGES_REQUESTED"
    elif change == "codeowners":
        observed.policy.codeowners = True
        observed.prs[0].review_decision = "REVIEW_REQUIRED"
    elif change == "draft":
        observed.prs[0].draft = True
    elif change == "strict":
        observed.policy.strict = True
    elif change == "base":
        observed.base_sha = "f" * 40
    assert delivery.blockers(unit, observed)


@pytest.mark.parametrize(
    "branch",
    ["-evil", "main..evil", "aeo/../evil", "aeo//x", "aeo/x.lock", "aeo/x@{", "aeo/x;evil"],
)
def test_branch_validation_rejects_unsafe_refs(tmp_path, branch):
    unit, _ = ready_observation(tmp_path)
    with pytest.raises(ValueError):
        Unit.model_validate({**unit.model_dump(), "branch": branch})


def test_dependency_cycles_and_missing_units_rejected(tmp_path):
    unit, _ = ready_observation(tmp_path)
    for dependencies in (["a"], ["missing"]):
        with pytest.raises(ValueError):
            Manifest(milestone="M", units=[unit.model_copy(update={"depends_on": dependencies})])
    with pytest.raises(ValueError):
        Manifest(milestone="M", units=[unit, unit])


def test_remote_success_then_local_transaction_failure_is_reconciled(
    engine, delivery_fixture, monkeypatch
):
    f = delivery_fixture
    prepare(engine, f)
    approval = grant(engine, f, "push")
    original = delivery.event

    def fail_completion(session, unit, kind, payload, operation=None):
        if kind == "completed":
            raise OSError("Fixture outcome transaction failed")
        return original(session, unit, kind, payload, operation)

    with monkeypatch.context() as patch:
        patch.setattr(delivery, "event", fail_completion)
        with pytest.raises(DeliveryError, match="uncertain"):
            delivery.mutate(engine, f.settings, f.run, f.unit.id, "push", approval, f.provider)
    assert f.provider.pushes == 1
    result = delivery.reconcile(engine, f.settings, f.run, f.unit.id, f.provider)
    assert result["units"][0]["state"] != "RECOVERY_REQUIRED"
    assert any(e["kind"] == "reconciled" for e in result["units"][0]["history"])


def test_multirepository_dependency_content_and_partial_recovery(
    engine, orchestration_fixture, monkeypatch
):
    f = orchestration_fixture
    specs = []
    with Session(engine) as session:
        tasks = {t.external_id: t.id for t in session.scalars(select(Task))}
    for key, name, task, remote_id in [
        ("a", "estate", "dev-a", 10),
        ("b", "agrosphere-architecture", "dev-b", 20),
    ]:
        root = f.repos[name]
        slug = "estate" if key == "a" else "architecture"
        git(root, "remote", "add", "origin", "https://github.com/acme/" + slug + ".git")
        sha = git(root, "rev-parse", "HEAD")
        specs.append(
            Unit(
                id=key,
                task=tasks[task],
                repository=name,
                root=root,
                remote=Remote(id=remote_id, owner="acme", name=slug),
                base="main",
                branch="aeo/" + key,
                base_sha=sha,
                head_sha=sha,
                depends_on=["a"] if key == "b" else [],
            )
        )
    f.settings.github_repositories = ["acme/estate", "acme/architecture"]
    manifest = Manifest(project="fixture", milestone="FIXTURE-1", units=specs)
    run = delivery.plan(engine, f.settings, manifest)
    provider = Provider(specs[0])
    provider.value.branch_sha = specs[0].head_sha
    provider.value.prs = [provider.pr().model_copy(update={"branch": "aeo/a"})]
    b = specs[1]
    bpr = provider.pr().model_copy(
        update={
            "id": 22,
            "number": 2,
            "url": "https://github.com/acme/architecture/pull/2",
            "repository_id": 20,
            "head_repository_id": 20,
            "branch": b.branch,
            "base_sha": b.base_sha,
            "head_sha": b.head_sha,
        }
    )
    provider.other["b"] = Observation(
        remote=b.remote,
        principal="publisher",
        can_push=True,
        base_sha=b.base_sha,
        branch_sha=b.head_sha,
        policy=Policy(known=True),
        prs=[bpr],
    )
    monkeypatch.setattr(
        delivery,
        "authority",
        lambda *a: (None, {}, {"decision": "READY_FOR_APPROVAL", "evidence": ["fixture"]}),
    )
    first = delivery.reconcile(engine, f.settings, run, "a", provider)
    second = delivery.reconcile(engine, f.settings, run, "b", provider)
    assert (
        next(u for u in first["units"] if u["id"] == "a")["state"] == "READY_FOR_AUTHORIZED_MERGE"
    )
    assert (
        "DEPENDENCY_UNAVAILABLE:a"
        in next(u for u in second["units"] if u["id"] == "b")["latest"]["blockers"]
    )
    # A merged PR plus target-branch reachability evidence releases downstream content.
    provider.value.prs[0].state = "merged"
    provider.value.prs[0].merge_sha = "f" * 40
    provider.value.base_sha = "f" * 40
    recovered = delivery.reconcile(engine, f.settings, run, "b", provider)
    assert (
        next(u for u in recovered["units"] if u["id"] == "b")["state"]
        == "READY_FOR_AUTHORIZED_MERGE"
    )
    provider.other["b"].policy.known = False
    partial = delivery.reconcile(engine, f.settings, run, "b", provider)
    assert partial["readiness"] == "BLOCKED"
    assert provider.pushes == provider.creates == 0


def test_reviews_are_case_insensitive_and_latest_human_decision_wins(tmp_path):
    unit, observed = ready_observation(tmp_path)
    observed.policy.approvals = 2
    second = observed.reviews[0].model_copy(
        update={"id": 2, "actor": "HUMAN", "submitted_at": "2026-01-02T00:00:00Z"}
    )
    observed.reviews.append(second)
    assert "HUMAN_REVIEW_REQUIRED" in delivery.blockers(unit, observed)
    observed.policy.approvals = 1
    observed.reviews[-1].state = "DISMISSED"
    assert "HUMAN_REVIEW_REQUIRED" in delivery.blockers(unit, observed)
    observed.reviews[-1].actor = "AUTHOR"
    observed.reviews[-1].state = "APPROVED"
    observed.reviews = observed.reviews[-1:]
    assert "HUMAN_REVIEW_REQUIRED" in delivery.blockers(unit, observed)


def test_absent_push_can_resume_only_with_fresh_human_recovery_grant(engine, delivery_fixture):
    f = delivery_fixture
    prepare(engine, f)
    ordinary = grant(engine, f, "push")
    real_push = f.provider.push

    def no_result(*args):
        raise TimeoutError("Fixture interrupted before push")

    f.provider.push = no_result
    with pytest.raises(DeliveryError):
        delivery.mutate(engine, f.settings, f.run, f.unit.id, "push", ordinary, f.provider)
    delivery.reconcile(engine, f.settings, f.run, f.unit.id, f.provider)
    f.provider.push = real_push
    with pytest.raises(DeliveryError):
        delivery.mutate(engine, f.settings, f.run, f.unit.id, "recover-push", ordinary, f.provider)
    assert f.provider.pushes == 0
    recovery = grant(engine, f, "recover-push")
    delivery.mutate(engine, f.settings, f.run, f.unit.id, "recover-push", recovery, f.provider)
    assert f.provider.pushes == 1
    with Session(engine) as session:
        operations = list(session.scalars(select(DeliveryOperation)))
        assert len([op for op in operations if op.action == "push"]) == 2
        assert not list(session.scalars(select(ResourceLease)))
    result = delivery.reconcile(engine, f.settings, f.run, f.unit.id, f.provider)
    assert any(e["kind"] == "superseded" for e in result["units"][0]["history"])


def test_recovery_requires_actual_prior_intent_and_remote_observation(engine, delivery_fixture):
    f = delivery_fixture
    with pytest.raises(DeliveryError, match="Reconcile"):
        grant(engine, f, "recover-push")
    f.provider.fail_observe = True
    delivery.reconcile(engine, f.settings, f.run, f.unit.id, f.provider)
    f.provider.fail_observe = False
    with pytest.raises(DeliveryError, match="Unavailable"):
        grant(engine, f, "recover-push")
    assert f.provider.pushes == f.provider.creates == 0


def test_prepare_from_separate_approved_commit_preserves_original_base(engine, delivery_fixture):
    f = delivery_fixture
    original = git(f.unit.root, "rev-parse", "HEAD")
    tree = git(f.unit.root, "rev-parse", "HEAD^{tree}")
    head = git(
        f.unit.root,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=f@example.invalid",
        "commit-tree",
        tree,
        "-p",
        original,
        "-m",
        "Fixture separately prepared commit",
    )
    assert head != original
    unit = f.unit.model_copy(update={"head_sha": head})
    target = f.unit.root.parent / "separate-commit-worktree"
    delivery.prepare_local(unit, target)
    assert git(f.unit.root, "rev-parse", "HEAD") == original
    assert git(target, "rev-parse", "HEAD") == head
