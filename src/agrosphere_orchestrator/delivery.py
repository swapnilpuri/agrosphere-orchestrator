"""Transactional delivery coordination. External I/O never holds a SQLite write transaction."""

import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import quality
from .delivery_models import DeliveryError, Manifest, Observation, PullRequest
from .delivery_store import DeliveryEvent, DeliveryOperation, DeliveryRun, DeliveryUnit
from .execution_workspace import create_worktree, git, tree_fingerprints
from .github_provider import GitHubCliAdapter, check_remote
from .orchestration import milestone_record
from .orchestration_store import acquire, release, transaction
from .persistence import Task, audit
from .quality_store import GovernanceRecord, blob, digest, read_blob


def validate_unit(settings, unit):
    repos = quality.repositories(settings)
    if (
        unit.remote.slug.lower() not in {r.lower() for r in settings.github_repositories}
        or unit.base not in settings.github_base_branches
        or unit.repository not in repos
        or repos[unit.repository].path.resolve() != unit.root
    ):
        raise DeliveryError(
            "REPOSITORY_POLICY", "Repository root, remote or base is not allowlisted"
        )
    if (
        git(unit.root, "rev-parse", "--show-toplevel").replace("\\", "/").lower()
        != unit.root.as_posix().lower()
    ):
        raise DeliveryError(
            "REPOSITORY_POLICY", "Delivery root must be the exact Git repository root"
        )
    check_remote(unit)
    git(unit.root, "check-ref-format", "--branch", unit.branch)
    git(unit.root, "check-ref-format", "--branch", unit.base)
    for sha in (unit.base_sha, unit.head_sha):
        if git(unit.root, "cat-file", "-t", sha) != "commit":
            raise DeliveryError("COMMIT_IDENTITY", "Base and head must name local commits")
    git(unit.root, "merge-base", "--is-ancestor", unit.base_sha, unit.head_sha)


def plan(engine, settings, manifest):
    manifest = Manifest.model_validate(manifest.model_dump())
    for unit in manifest.units:
        validate_unit(settings, unit)
    identity = digest(manifest.model_dump(mode="json"))
    with transaction(engine) as session:
        milestone = milestone_record(session, manifest.milestone, manifest.project)
        quality.design_context(session, milestone)
        prior = session.scalar(select(DeliveryRun).where(DeliveryRun.milestone_id == milestone.id))
        if prior:
            if prior.id != identity:
                raise DeliveryError(
                    "MANIFEST_CONFLICT", "A milestone delivery manifest is immutable"
                )
            return prior.id
        session.add(
            DeliveryRun(
                id=identity, milestone_id=milestone.id, manifest=manifest.model_dump(mode="json")
            )
        )
        session.flush()
        for spec in manifest.units:
            task = session.get(Task, spec.task)
            if (
                not task
                or task.milestone_id != milestone.id
                or task.spec["repository"] != spec.repository
            ):
                raise DeliveryError(
                    "TASK_SCOPE",
                    "Delivery unit does not reference an existing milestone repository task",
                )
            session.add(
                DeliveryUnit(
                    id=digest([identity, spec.id]),
                    run_id=identity,
                    task_id=task.id,
                    external_id=spec.id,
                    state="PLANNED",
                )
            )
        audit(session, identity, "delivery.planned", "delivery-engine", {"manifest": identity})
    return identity


def load(session, run_id, unit_id):
    run = session.get(DeliveryRun, run_id)
    if run is None:
        raise DeliveryError("UNKNOWN_RUN", "Unknown delivery run")
    manifest = Manifest.model_validate(run.manifest)
    unit = session.scalar(
        select(DeliveryUnit).where(
            DeliveryUnit.run_id == run_id, DeliveryUnit.external_id == unit_id
        )
    )
    if unit is None:
        raise DeliveryError("UNKNOWN_UNIT", "Unknown delivery unit")
    spec = next(u for u in manifest.units if u.id == unit_id)
    return run, unit, spec


def event(session, unit, kind, payload, operation=None):
    identity = blob(session, payload)
    session.add(
        DeliveryEvent(unit_id=unit.id, operation_id=operation, kind=kind, evidence=identity)
    )
    audit(
        session,
        unit.id,
        "delivery." + kind,
        "delivery-engine",
        {"operation": operation, "evidence": identity},
    )
    return identity


def matching_pr(unit, observation, persisted=None):
    prs = observation.prs
    if len(prs) > 1:
        raise DeliveryError("DUPLICATE_PR", "Multiple matching PRs require human reconciliation")
    if not prs:
        if persisted:
            raise DeliveryError("PR_DISAPPEARED", "Previously recorded PR is unavailable")
        return None
    pr = prs[0]
    if (
        pr.repository_id != unit.remote.id
        or pr.head_repository_id != unit.remote.id
        or pr.base != unit.base
        or pr.branch != unit.branch
        or pr.head_sha != unit.head_sha
        or pr.base_sha != unit.base_sha
        or (persisted is not None and pr.id != persisted)
    ):
        raise DeliveryError(
            "PR_IDENTITY", "PR immutable identity, base or head differs from approved scope"
        )
    if pr.state != "open":
        raise DeliveryError(
            "PR_TERMINAL", "Closed or merged PR cannot be replaced or reopened automatically"
        )
    return pr


def blockers(unit, observation):
    result = []
    if observation.remote != unit.remote or observation.base_sha != unit.base_sha:
        result.append("REMOTE_OR_BASE_CHANGED")
    if observation.branch_sha != unit.head_sha:
        result.append("REMOTE_HEAD_MISSING_OR_CHANGED")
    policy = observation.policy
    if not policy.known:
        result.append("POLICY_UNAVAILABLE")
    result.extend("UNSUPPORTED_POLICY:" + value for value in policy.unsupported)
    try:
        pr = matching_pr(unit, observation)
    except DeliveryError as exc:
        result.append(exc.code)
        return result
    if pr is None:
        return result + ["PR_MISSING"]
    if pr.draft:
        result.append("DRAFT_PR")
    if policy.strict and observation.base_in_head is not True:
        result.append("BASE_NOT_IN_HEAD")
    if pr.review_decision == "CHANGES_REQUESTED":
        result.append("GITHUB_CHANGES_REQUESTED")
    if pr.mergeable is not True:
        result.append("MERGEABILITY_UNKNOWN_OR_CONFLICTING")
    for required in policy.checks:
        checks = [
            c
            for c in observation.checks
            if c.name == required.name
            and c.sha == unit.head_sha
            and (required.app_id in {None, -1} or required.app_id == c.app_id)
        ]
        if not checks or any(c.state != "success" for c in checks):
            result.append("REQUIRED_CHECK:" + required.name)
    latest = {}
    for review in sorted(observation.reviews, key=lambda r: (r.submitted_at, r.id)):
        if review.state != "COMMENTED":
            latest[review.actor.casefold()] = review
    humans = [
        r
        for r in latest.values()
        if r.actor_type == "User"
        and not r.actor.casefold().endswith("[bot]")
        and r.actor.casefold() != pr.author.casefold()
    ]
    if any(r.state == "CHANGES_REQUESTED" for r in humans):
        result.append("CHANGES_REQUESTED")
    approvals = {
        r.actor.casefold() for r in humans if r.state == "APPROVED" and r.sha == unit.head_sha
    }
    if len(approvals) < policy.approvals:
        result.append("HUMAN_REVIEW_REQUIRED")
    if policy.codeowners:
        result.append("CODEOWNER_HUMAN_APPROVAL_UNPROVEN")
    if (policy.approvals or policy.codeowners) and pr.review_decision != "APPROVED":
        result.append("GITHUB_REVIEW_REQUIREMENTS_UNPROVEN")
    return result


def authority(session, settings, run):
    milestone = milestone_record(session, run.manifest["milestone"], run.manifest["project"])
    policy = quality.active_policy(session, settings, milestone)
    report = quality.evaluate(session, settings, milestone)
    if report["decision"] not in {"READY_FOR_APPROVAL", "APPROVED_FOR_DELIVERY"}:
        raise DeliveryError(
            "QUALITY_BLOCKED", "Current AEO-4 quality/security readiness is required"
        )
    current = quality.context(session, settings, milestone, policy)
    return milestone, current, report


def scope_for(run, spec, action, observation, current, report, settings, recovery=None):
    source = current["repositories"].get(spec.repository)
    if not source or source["head"] != spec.head_sha:
        raise DeliveryError(
            "QUALITY_HEAD", "Validated artifact HEAD differs from the publishing commit"
        )
    return {
        "run": run.id,
        "manifest": digest(run.manifest),
        "worktree": str(worktree(settings, run.id, spec.id)),
        "delivery_policy": {
            "repositories": settings.github_repositories,
            "bases": settings.github_base_branches,
            "remote_writes": settings.github_remote_writes,
        },
        "unit": spec.model_dump(mode="json"),
        "action": action,
        "recovery": recovery,
        "remote_policy": observation.policy.model_dump(mode="json"),
        "principal": observation.principal,
        "context": current,
        "quality_validation": report.get("validation"),
        "quality_evidence": report.get("evidence", []),
    }


def assert_preconditions(settings, spec, observation, action):
    validate_unit(settings, spec)
    if not observation.can_push or not observation.principal:
        raise DeliveryError(
            "PERMISSION_DENIED", "Authenticated repository push permission is required"
        )
    if observation.remote != spec.remote or observation.base_sha != spec.base_sha:
        raise DeliveryError("STALE_SCOPE", "Remote identity or target base changed")
    if not observation.policy.known or observation.policy.unsupported:
        raise DeliveryError(
            "POLICY_BLOCKED", "Current repository policy is unavailable or unsupported"
        )
    if observation.branch_sha not in {None, spec.head_sha}:
        raise DeliveryError("REMOTE_BRANCH_CONFLICT", "Remote branch contains a different head")
    if action.removeprefix("recover-") != "prepare" and not settings.github_remote_writes:
        raise DeliveryError("WRITES_DISABLED", "Remote writes are disabled")


def recovery_context(session, unit, action, observation):
    if not action.startswith("recover-"):
        return None
    if not unit.observation:
        raise DeliveryError(
            "RECOVERY_OBSERVATION_REQUIRED",
            "Reconcile the previous intent before requesting recovery authority",
        )
    previous = read_blob(session, unit.observation).get("observation")
    if previous is None:
        raise DeliveryError(
            "RECOVERY_OBSERVATION_REQUIRED", "Unavailable remote evidence cannot authorize replay"
        )
    old = Observation.model_validate(previous)
    if (
        old.remote != observation.remote
        or old.branch_sha != observation.branch_sha
        or old.base_sha != observation.base_sha
        or [p.model_dump() for p in old.prs] != [p.model_dump() for p in observation.prs]
    ):
        raise DeliveryError(
            "RECOVERY_OBSERVATION_CHANGED",
            "Current remote identity differs from the reconciled observation",
        )
    operations = list(
        session.scalars(
            select(DeliveryOperation).where(
                DeliveryOperation.unit_id == unit.id,
                DeliveryOperation.action == action.removeprefix("recover-"),
            )
        )
    )
    if not operations:
        raise DeliveryError("RECOVERY_INTENT_REQUIRED", "No prior operation exists to recover")
    return {"operations": sorted(op.id for op in operations), "observation": unit.observation}


def approval_scope(engine, settings, run_id, unit_id, action, provider=None):
    if action not in {
        "prepare",
        "push",
        "create-pr",
        "recover-prepare",
        "recover-push",
        "recover-create-pr",
    }:
        raise DeliveryError("INVALID_ACTION", "Unsupported delivery action")
    with Session(engine) as session:
        _, _, spec = load(session, run_id, unit_id)
    observed = (provider or GitHubCliAdapter(settings, spec.root)).observe(spec)
    assert_preconditions(settings, spec, observed, action)
    with transaction(engine) as session:
        run, unit, spec = load(session, run_id, unit_id)
        _, current, report = authority(session, settings, run)
        recovery = recovery_context(session, unit, action, observed)
        scope = scope_for(run, spec, action, observed, current, report, settings, recovery)
        return {
            "scope": scope,
            "action": "delivery:" + digest(scope),
            "category": "PRIVILEGED_EXECUTION",
        }


def worktree(settings, run_id, unit_id):
    base = settings.delivery_root.resolve()
    target = base / run_id / unit_id / "worktree"
    if not target.resolve().is_relative_to(base) or any(
        p.is_symlink() or p.is_junction() for p in [target, *target.parents] if p.exists()
    ):
        raise DeliveryError("WORKTREE_PATH", "Unsafe isolated worktree path")
    return target


def verify_worktree(spec, target):
    if (
        not target.exists()
        or git(target, "rev-parse", "--git-common-dir") == ""
        or Path(git(target, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
        != Path(git(spec.root, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
        or git(target, "branch", "--show-current") != spec.branch
        or git(target, "rev-parse", "HEAD") != spec.head_sha
        or git(target, "status", "--porcelain", "--untracked-files=all")
    ):
        raise DeliveryError(
            "WORKTREE_CONFLICT", "Isolated worktree is missing, dirty, or has conflicting identity"
        )


def prepare_local(spec, target):
    if target.resolve().is_relative_to(spec.root):
        raise DeliveryError(
            "WORKTREE_PATH", "Delivery worktree must be outside the original repository"
        )
    before = tree_fingerprints(spec.root, 100000000)
    source_head = git(spec.root, "rev-parse", "HEAD")
    if source_head not in {spec.base_sha, spec.head_sha}:
        raise DeliveryError(
            "SOURCE_CHANGED", "Original source HEAD differs from approved base/head"
        )
    if target.exists():
        verify_worktree(spec, target)
    else:
        git(spec.root, "merge-base", "--is-ancestor", spec.base_sha, spec.head_sha)
        try:
            existing = git(spec.root, "rev-parse", "--verify", "refs/heads/" + spec.branch)
        except subprocess.CalledProcessError:
            existing = None
        if existing:
            if existing != spec.head_sha:
                raise DeliveryError("BRANCH_CONFLICT", "Existing branch has a different head")
            target.parent.mkdir(parents=True, exist_ok=True)
            git(spec.root, "worktree", "add", str(target), spec.branch)
        else:
            create_worktree(
                spec.root,
                target,
                spec.branch.removeprefix("aeo/"),
                spec.head_sha,
                expected_source_head=source_head,
            )
        verify_worktree(spec, target)
    if (
        tree_fingerprints(spec.root, 100000000) != before
        or git(spec.root, "rev-parse", "HEAD") != source_head
    ):
        raise DeliveryError(
            "SOURCE_CHANGED", "Original worktree changed during preparation; worktrees retained"
        )


def begin_operation(engine, settings, run_id, unit_id, action, approval, observation):
    with transaction(engine) as session:
        run, unit, spec = load(session, run_id, unit_id)
        assert_preconditions(settings, spec, observation, action)
        milestone, current, report = authority(session, settings, run)
        recovery = recovery_context(session, unit, action, observation)
        scope = scope_for(run, spec, action, observation, current, report, settings, recovery)
        identity = digest(scope)
        existing = list(
            session.scalars(
                select(DeliveryOperation).where(
                    DeliveryOperation.unit_id == unit.id,
                    DeliveryOperation.action == action.removeprefix("recover-"),
                )
            )
        )
        if session.get(DeliveryOperation, identity) or (existing and recovery is None):
            raise DeliveryError(
                "RECOVERY_REQUIRED", "Existing mutation intent must be reconciled; no blind replay"
            )
        request = session.scalar(
            select(GovernanceRecord).where(
                GovernanceRecord.id == approval, GovernanceRecord.kind == "approval.request"
            )
        )
        if (
            request is None
            or request.milestone_id != milestone.id
            or request.payload["category"] != "PRIVILEGED_EXECUTION"
            or request.payload["action"] != "delivery:" + identity
        ):
            raise DeliveryError(
                "APPROVAL_SCOPE",
                "Exact artifact, remote, branch, action and policy authorization required",
            )
        decision = quality.valid_approval(session, settings, request, current, consume=True)
        if recovery:
            for old in existing:
                event(
                    session,
                    unit,
                    "superseded",
                    {
                        "new_operation": identity,
                        "recovery_observation": recovery["observation"],
                        "human_decision": decision.id,
                    },
                    old.id,
                )
                release(session, old.id)
        if not acquire(
            session, unit.task_id, identity, ["repository:" + spec.repository], True, 300
        ):
            raise DeliveryError(
                "LEASE_CONFLICT", "Repository has a conflicting or unreconciled write lease"
            )
        session.add(
            DeliveryOperation(
                id=identity,
                unit_id=unit.id,
                action=action.removeprefix("recover-"),
                scope=scope,
                approval_id=approval,
                principal=observation.principal,
            )
        )
        session.flush()
        unit.state = "AUTHORIZED"
        event(
            session,
            unit,
            "intent",
            {"scope": scope, "approval": approval, "approver": decision.actor},
            identity,
        )
        return identity


def recheck_operation(engine, settings, run_id, unit_id, identity, observed):
    with transaction(engine) as session:
        run, unit, spec = load(session, run_id, unit_id)
        op = session.get(DeliveryOperation, identity)
        assert_preconditions(settings, spec, observed, op.action)
        _, current, report = authority(session, settings, run)
        if (
            scope_for(
                run,
                spec,
                op.scope["action"],
                observed,
                current,
                report,
                settings,
                op.scope.get("recovery"),
            )
            != op.scope
        ):
            raise DeliveryError(
                "STALE_AUTHORIZATION", "Artifacts, policy or identity changed after authorization"
            )
        if op.scope.get("recovery") and unit.observation != op.scope["recovery"]["observation"]:
            raise DeliveryError(
                "STALE_AUTHORIZATION", "Recovery observation changed after authentication"
            )
        request = session.scalar(
            select(GovernanceRecord).where(GovernanceRecord.id == op.approval_id)
        )
        decisions = quality.decisions(session, request)
        if (
            not decisions
            or decisions[-1].decision != "approved"
            or decisions[-1].actor not in settings.governance_approvers
            or datetime.fromisoformat(request.payload["expires_at"]) <= datetime.now(UTC)
        ):
            raise DeliveryError(
                "AUTHORIZATION_REVOKED", "Authorization expired or was revoked after intent"
            )
        return report


def pr_body(run, spec, report, related):
    return (
        f"## {run.manifest['milestone']}: {spec.id}\n\nTask: {spec.task}\nDesign: {report.get('context', {}).get('design', 'unknown')}\n"
        + f"Purpose: authorized delivery of stored milestone {run.manifest['milestone']}.\n\n"
        + "Validation and security evidence: "
        + json.dumps(report.get("evidence", []))
        + "\nQuality validation: "
        + str(report.get("validation", "unknown"))
        + "\nRelated PRs: "
        + json.dumps(related)
        + "\n\nLimitations: readiness requires current required CI, human reviews and dependency availability. No automatic merge or deployment.\n"
    )


def mutate(engine, settings, run_id, unit_id, action, approval, provider=None):
    if action not in {
        "prepare",
        "push",
        "create-pr",
        "recover-prepare",
        "recover-push",
        "recover-create-pr",
    }:
        raise DeliveryError("INVALID_ACTION", "Unsupported mutation")
    grant_action = action
    action = action.removeprefix("recover-")
    with Session(engine) as session:
        _, unit, spec = load(session, run_id, unit_id)
        persisted = unit.pr_id
    provider = provider or GitHubCliAdapter(settings, spec.root)
    observation = provider.observe(spec)
    pr = matching_pr(spec, observation, persisted)
    assert_preconditions(settings, spec, observation, action)
    if action == "push" and observation.branch_sha == spec.head_sha:
        return reconcile(engine, settings, run_id, unit_id, provider)
    if action == "create-pr" and pr is not None:
        return reconcile(engine, settings, run_id, unit_id, provider)
    if action == "create-pr" and observation.branch_sha != spec.head_sha:
        raise DeliveryError(
            "PUSH_REQUIRED", "Exact approved branch must be present before PR creation"
        )
    target = worktree(settings, run_id, unit_id)
    if action == "prepare" and target.exists():
        verify_worktree(spec, target)
        return reconcile(engine, settings, run_id, unit_id, provider)
    if action != "prepare":
        verify_worktree(spec, target)
    if action != "prepare":
        with transaction(engine) as session:
            run, _, _ = load(session, run_id, unit_id)
            _, current, _ = authority(session, settings, run)
            if current["repositories"][spec.repository]["tree"] != digest(
                tree_fingerprints(target, 100000000)
            ):
                raise DeliveryError(
                    "QUALITY_TREE", "Published worktree differs from the validated artifact tree"
                )
    identity = begin_operation(
        engine, settings, run_id, unit_id, grant_action, approval, observation
    )
    try:
        recheck_operation(engine, settings, run_id, unit_id, identity, observation)
        if action == "prepare":
            prepare_local(spec, target)
            outcome = {"worktree": str(target), "branch": spec.branch, "head_sha": spec.head_sha}
        elif action == "push":
            provider.push(spec, target)
            observed = provider.observe(spec)
            if observed.branch_sha != spec.head_sha:
                raise DeliveryError("PUSH_UNCONFIRMED", "Push completion is not proven")
            outcome = observed.model_dump(mode="json")
        elif action == "create-pr":
            # A second lookup inside the durable leased operation catches external races.
            observed = provider.observe(spec)
            found = matching_pr(spec, observed, persisted)
            recheck_operation(engine, settings, run_id, unit_id, identity, observed)
            if found is None:
                with transaction(engine) as session:
                    run, _, spec = load(session, run_id, unit_id)
                    _, _, report = authority(session, settings, run)
                    related = related_prs(session, run_id)
                    title = f"{run.manifest['milestone']}: {spec.id}"
                    body = pr_body(run, spec, report, related)
                created = provider.create_pr(spec, title, body)
                created = PullRequest.model_validate(created)
                matching_pr(spec, observed.model_copy(update={"prs": [created]}))
                if created.state != "open":
                    raise DeliveryError("PR_UNCONFIRMED", "Created PR is not open")
            observed = provider.observe(spec)
            found = matching_pr(spec, observed, persisted)
            if found is None:
                raise DeliveryError("PR_UNCONFIRMED", "PR creation outcome is unavailable")
            outcome = observed.model_dump(mode="json")
        else:
            raise DeliveryError("INVALID_ACTION", "Unsupported mutation")
        with transaction(engine) as session:
            _, unit, _ = load(session, run_id, unit_id)
            if action == "create-pr":
                unit.pr_id = found.id
            event(session, unit, "completed", outcome, identity)
            unit.state = (
                "BRANCH_PREPARED"
                if action == "prepare"
                else "PR_PUBLISHED"
                if action == "create-pr"
                else "AWAITING_PUBLICATION"
            )
            release(session, identity)
    except BaseException as exc:
        # Every exception after intent is ambiguous. Preserve ownership for observation.
        with transaction(engine) as session:
            _, unit, _ = load(session, run_id, unit_id)
            unit.state = "RECOVERY_REQUIRED"
            event(
                session,
                unit,
                "uncertain",
                {
                    "code": getattr(exc, "code", "OUTCOME_UNCERTAIN"),
                    "action": action,
                    "error_type": type(exc).__name__,
                },
                identity,
            )
        raise DeliveryError(
            "RECOVERY_REQUIRED", "Mutation outcome uncertain; use read-only reconciliation"
        ) from None
    return status(engine, run_id)


def related_prs(session, run_id):
    output = []
    for unit in session.scalars(select(DeliveryUnit).where(DeliveryUnit.run_id == run_id)):
        if unit.observation:
            data = read_blob(session, unit.observation)
            output.extend(p["url"] for p in data.get("observation", {}).get("prs", []))
    return output


def reconcile(engine, settings, run_id, unit_id, provider=None):
    with Session(engine) as session:
        _, _, spec = load(session, run_id, unit_id)
    provider = provider or GitHubCliAdapter(settings, spec.root)
    try:
        observed = provider.observe(spec)
        validate_unit(settings, spec)
        error = None
    except Exception as exc:
        observed = None
        error = getattr(exc, "code", "OBSERVATION_UNAVAILABLE")
    # Dependency content must actually be merged into its repository target branch.
    dependencies = {}
    if observed:
        with Session(engine) as session:
            _, _, spec = load(session, run_id, unit_id)
            dep_specs = [load(session, run_id, d)[2] for d in spec.depends_on]
        for dependency in dep_specs:
            try:
                dep = provider.observe(dependency)
                dependencies[dependency.id] = provider.dependency_available(dependency, dep)
            except Exception:
                dependencies[dependency.id] = False
        observed.dependencies_available = dependencies
    with transaction(engine) as session:
        run, unit, spec = load(session, run_id, unit_id)
        previous = unit.state
        unmet = [error] if error else blockers(spec, observed)
        if observed:
            try:
                pr = matching_pr(spec, observed, unit.pr_id)
                if pr:
                    unit.pr_id = pr.id
            except DeliveryError as exc:
                unmet.append(exc.code)
            for dep, available in dependencies.items():
                if not available:
                    unmet.append("DEPENDENCY_UNAVAILABLE:" + dep)
        quality_report = None
        try:
            _, _, quality_report = authority(session, settings, run)
        except Exception:
            unmet.append("QUALITY_BLOCKED")
        unresolved = False
        for op in session.scalars(
            select(DeliveryOperation).where(DeliveryOperation.unit_id == unit.id)
        ):
            completed = session.scalar(
                select(DeliveryEvent).where(
                    DeliveryEvent.operation_id == op.id,
                    DeliveryEvent.kind.in_(["completed", "reconciled", "superseded"]),
                )
            )
            if completed:
                continue
            proven = False
            if observed and observed.remote == spec.remote:
                if op.action == "push":
                    proven = observed.branch_sha == spec.head_sha
                elif op.action == "create-pr":
                    try:
                        proven = matching_pr(spec, observed, unit.pr_id) is not None
                    except DeliveryError:
                        pass
                elif op.action == "prepare":
                    try:
                        verify_worktree(spec, worktree(settings, run_id, unit_id))
                        proven = True
                    except Exception:
                        pass
            if proven:
                event(
                    session,
                    unit,
                    "reconciled",
                    {"observed_completion": True, "observation": observed.model_dump(mode="json")},
                    op.id,
                )
                release(session, op.id)
            else:
                unresolved = True
        if unresolved:
            unmet.append("UNRESOLVED_MUTATION_INTENT")
        payload = {
            "observed_at": datetime.now(UTC).isoformat(),
            "previous_state": previous,
            "observation": observed.model_dump(mode="json") if observed else None,
            "blockers": sorted(set(unmet)),
            "quality": quality_report,
        }
        unit.observation = event(session, unit, "observation", payload)
        unit.state = (
            "RECOVERY_REQUIRED"
            if unresolved
            else "BLOCKED"
            if unmet
            else "READY_FOR_AUTHORIZED_MERGE"
        )
    return status(engine, run_id)


def status(engine, run_id, max_age_seconds=60):
    with Session(engine) as session:
        run = session.get(DeliveryRun, run_id)
        if run is None:
            raise DeliveryError("UNKNOWN_RUN", "Unknown delivery run")
        units = []
        for unit in session.scalars(
            select(DeliveryUnit)
            .where(DeliveryUnit.run_id == run_id)
            .order_by(DeliveryUnit.external_id)
        ):
            events = [
                {
                    "sequence": e.sequence,
                    "operation": e.operation_id,
                    "kind": e.kind,
                    "evidence_hash": e.evidence,
                    "created_at": e.created_at,
                    "evidence": read_blob(session, e.evidence),
                }
                for e in session.scalars(
                    select(DeliveryEvent)
                    .where(DeliveryEvent.unit_id == unit.id)
                    .order_by(DeliveryEvent.sequence)
                )
            ]
            latest = read_blob(session, unit.observation) if unit.observation else None
            expired = bool(
                latest
                and (
                    datetime.now(UTC) - datetime.fromisoformat(latest["observed_at"])
                ).total_seconds()
                > max_age_seconds
            )
            units.append(
                {
                    "id": unit.external_id,
                    "state": "OBSERVATION_EXPIRED" if expired else unit.state,
                    "pr_id": unit.pr_id,
                    "latest": latest,
                    "history": events,
                }
            )
        result = {
            "run": run.id,
            "manifest": run.manifest,
            "units": units,
            "readiness": "READY_FOR_AUTHORIZED_MERGE"
            if units and all(u["state"] == "READY_FOR_AUTHORIZED_MERGE" for u in units)
            else "BLOCKED",
            "freshness": "Stored observations only; reconcile each unit before relying on readiness",
            "merge_executed": False,
        }
        result["report_hash"] = digest(result)
        return result


def observe(engine, settings, run_id, unit_id, poll=False, provider=None):
    deadline = time.monotonic() + settings.github_poll_budget_seconds
    while True:
        result = reconcile(engine, settings, run_id, unit_id, provider)
        unit = next(u for u in result["units"] if u["id"] == unit_id)
        if (
            not poll
            or unit["state"] == "READY_FOR_AUTHORIZED_MERGE"
            or time.monotonic() >= deadline
        ):
            return result
        time.sleep(min(settings.github_poll_seconds, max(0, deadline - time.monotonic())))


def markdown(report):
    lines = [
        "# Delivery " + report["manifest"]["milestone"],
        "",
        "Stored readiness: " + report["readiness"],
        "Report hash: " + report["report_hash"],
        report["freshness"],
        "",
    ]
    for unit in report["units"]:
        lines += [
            "## " + unit["id"],
            "State: " + unit["state"],
            "PR identity: " + str(unit["pr_id"] or "unknown"),
        ]
        latest = unit["latest"] or {}
        lines += ["Blockers: " + json.dumps(latest.get("blockers", ["UNOBSERVED"]))]
        observed = latest.get("observation") or {}
        lines += [
            "Head: " + str(observed.get("branch_sha") or "unknown"),
            "Pull requests: " + json.dumps(observed.get("prs", [])),
            "Checks: " + json.dumps(observed.get("checks", [])),
            "Reviews: " + json.dumps(observed.get("reviews", [])),
        ]
    return "\n".join(lines) + "\n"
