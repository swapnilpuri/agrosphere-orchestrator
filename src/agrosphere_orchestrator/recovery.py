"""Atomic recovery transactions and repeatable projections of durable observations."""

import hashlib
import json
import os
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from .persistence import Milestone, RecoveryHead, RecoveryRecord, audit
from .recovery_models import RecoverySnapshot

BEGIN = "<!-- BEGIN AEO RECOVERY -->"
END = "<!-- END AEO RECOVERY -->"
YAML_BEGIN = "# BEGIN AEO RECOVERY"
YAML_END = "# END AEO RECOVERY"


def recovery_engine(url: str, readonly: bool = False) -> Engine:
    from .persistence import make_engine

    parsed = make_url(url)
    if parsed.drivername != "sqlite" or not parsed.database or parsed.database == ":memory:":
        raise ValueError("recovery requires an existing migrated SQLite file")
    path = Path(parsed.database).resolve()
    if not path.is_file():
        raise ValueError("state database missing; run alembic upgrade head first")
    return make_engine("sqlite:///" + path.as_uri() + "?mode=ro&uri=true" if readonly else url)


def fingerprint(snapshot: RecoverySnapshot) -> str:
    payload = snapshot.model_dump(mode="json", exclude={"observed_at"})
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def reconcile(engine: Engine, snapshot: RecoverySnapshot) -> str:
    """Observations, head and audit commit together; imported specs/approvals are untouched."""
    snapshot = RecoverySnapshot.model_validate(snapshot.model_dump())
    identity = fingerprint(snapshot)
    with Session(engine) as session, session.begin():
        record = session.get(RecoveryRecord, identity)
        if record is None:
            record = RecoveryRecord(
                id=identity,
                workspace=snapshot.workspace,
                observed_at=snapshot.observed_at,
                payload=snapshot.model_dump(mode="json"),
            )
            session.add(record)
            session.flush()
            audit(
                session,
                identity,
                "recovery.observed",
                "local-user",
                {"workspace": snapshot.workspace},
            )
        head = session.get(RecoveryHead, snapshot.workspace)
        if head is None:
            session.add(RecoveryHead(workspace=snapshot.workspace, snapshot_id=identity))
        elif head.snapshot_id == identity:
            return identity
        else:
            head.snapshot_id = identity
        audit(
            session,
            identity,
            "recovery.reconciled",
            "local-user",
            {"workspace": snapshot.workspace},
        )
    return identity


def current_snapshot(engine: Engine, workspace: Path) -> tuple[str, RecoverySnapshot]:
    with Session(engine) as session:
        head = session.get(RecoveryHead, str(workspace.resolve()))
        if head is None:
            raise ValueError("no recovery state for workspace; run project reconcile")
        record = session.get(RecoveryRecord, head.snapshot_id)
        return record.id, RecoverySnapshot.model_validate(record.payload)


def next_milestone(snapshot: RecoverySnapshot) -> dict:
    chain = ("1A", "1B", "1C", "2", "3A", "3B")
    by_id = {m.id: m for m in snapshot.milestones}
    pending = next(
        (by_id[mid] for mid in chain if mid in by_id and by_id[mid].classification != "COMPLETED"),
        None,
    )
    return {
        "milestone": pending.id if pending else None,
        "action": "Verify and reconcile acceptance criteria before authorizing application development.",
        "development_candidate": "3B" if "3A" in by_id and by_id["3A"].implementation else None,
        "approval_granted": False,
        "aeo_2_started": False,
    }


def projections(identity: str, snapshot: RecoverySnapshot, plans: list[dict]) -> dict[str, str]:
    header = f"Snapshot: {identity}\n\nObserved at: {snapshot.observed_at}\nWorkspace: {snapshot.workspace}\n"
    table = "| Milestone | Observed state | Confidence |\n|---|---|---|\n" + "".join(
        f"| {m.id} | {m.classification} | {m.confidence} |\n" for m in snapshot.milestones
    )
    completed = [m.id for m in snapshot.milestones if m.classification == "COMPLETED"]
    current = (
        header
        + "\n"
        + table
        + "\nLatest verified completed milestone: "
        + (completed[-1] if completed else "none established")
    )
    current += "\n\n" + "\n".join(f"- {s}" for s in snapshot.limitations)
    history = header
    for m in snapshot.milestones:
        history += f"\n## Milestone {m.id}: {m.classification} ({m.confidence})\n"
        for label, entries in (
            ("Documented objectives / claims", m.objectives),
            ("Observed implementation", m.implementation),
            ("Available tests", m.tests),
            ("Verified acceptance criteria", m.verified_acceptance_criteria),
            ("Outstanding work", m.outstanding),
            ("Missing documentation", m.missing_documentation),
            ("Conflicting claims", m.conflicts),
        ):
            history += (
                f"\n### {label}\n\n"
                + ("\n".join(f"- {x}" for x in entries) or "- None established.")
                + "\n"
            )
        history += "\n### Supporting evidence\n\n"
        for e in m.evidence:
            history += (
                f"- {e.repository}/{e.path}:{e.line or 0}; kind={e.kind}; HEAD={e.head}; "
                f"sha256={e.sha256}; modified={e.modified_at}; outcome={e.outcome or 'claim only'}\n"
            )
    inventory = {
        "snapshot_id": identity,
        "observed_at": snapshot.observed_at,
        "repositories": snapshot.repositories,
        "missing_repositories": snapshot.missing_repositories,
    }
    roadmap = {
        "snapshot_id": identity,
        "observations": [m.model_dump(mode="json") for m in snapshot.milestones],
        "imported_plans": plans,
        "recommendation": next_milestone(snapshot),
        "approval_policy": "Recovery grants no approval. Imported plans are shown separately and remain unchanged.",
    }
    report = header + "\n" + table
    report += (
        "\nReused: repository inspector, Settings, Pydantic strict models, SQLAlchemy sessions, "
        "Alembic migrations, audit service and Typer conventions.\n\n"
        "Added: recursive read-only inventory, evidence mapping, historical XML outcomes, "
        "content-addressed recovery snapshots, transactional current pointer, repeatable report export, "
        "project/milestones CLI groups and recovery tests.\n\n"
    )
    report += "Discovered application repositories:\n\n" + "\n".join(
        f"- {r['id']}: {r['path']} (branch {r['branch']}; HEAD {r['head']}; dirty={r['dirty']}; error={r['error']})"
        for r in snapshot.repositories
    )
    report += "\n\nMissing manifest entries: " + (
        ", ".join(snapshot.missing_repositories) or "none"
    )
    report += "\n\nLatest verified completed milestone: " + (
        completed[-1] if completed else "none established"
    )
    report += "\n\nPartial milestones: " + (
        ", ".join(m.id for m in snapshot.milestones if m.classification == "PARTIAL") or "none"
    )
    report += (
        "\n\nRecommended next application work: review 3B scope against the 3A report only after "
        "verifying the earlier acceptance chain; no development is authorized by this report. "
        "The machine recommendation identifies the earliest verification gap.\n\n"
        "AEO-2 readiness: foundation extended for durable discovery; application acceptance and "
        "historical conflicts still need review. Separate AEO-2 authorization is required.\n\n"
        "Automated orchestrator validation: see docs/validation/commands.json and pytest.xml for actual "
        "commands, exit codes and timestamps. Application tests were not rerun.\n\n"
        "Unresolved information and limits:\n\n"
    )
    report += "\n".join(f"- {s}" for s in snapshot.limitations)
    for m in snapshot.milestones:
        report += "\n" + "\n".join(f"- {m.id}: {s}" for s in m.conflicts + m.missing_documentation)
    return {
        "CURRENT_STATE.md": current + "\n",
        "MILESTONE_HISTORY.md": history,
        "REPOSITORY_INVENTORY.yaml": yaml.safe_dump(
            {"recovered_observations": inventory}, sort_keys=False
        ),
        "ROADMAP.yaml": yaml.safe_dump({"recovered_observations": roadmap}, sort_keys=False),
        "RECOVERY_REPORT.md": report + "\n",
    }


def export_reports(engine: Engine, workspace: Path, destination: Path) -> str:
    """SQLite is authoritative. Retry this after interruption to repair all projections.

    Only delimited generated regions are replaced. Unmarked existing files fail closed;
    operator text/approved YAML outside these regions is preserved byte for byte.
    Each file uses atomic replacement; all five carry the same durable snapshot ID.
    """
    identity, snapshot = current_snapshot(engine, workspace)
    with Session(engine) as session:
        plans = [
            {"project": m.project_id, "id": m.external_id, "spec": m.spec}
            for m in session.scalars(select(Milestone).order_by(Milestone.id))
        ]
    rendered = projections(identity, snapshot, plans)
    destination.mkdir(parents=True, exist_ok=True)
    prepared = {}
    for name, body in rendered.items():
        target = destination / name
        if target.is_symlink():
            raise ValueError(f"refusing symlink report: {target}")
        begin, end = (YAML_BEGIN, YAML_END) if name.endswith(".yaml") else (BEGIN, END)
        region = begin + "\n" + body + end
        if target.exists():
            old = target.read_bytes().decode("utf-8")
            if old.count(begin) != 1 or old.count(end) != 1 or old.index(begin) > old.index(end):
                raise ValueError(f"unmanaged or malformed report preserved: {target}")
            start, stop = old.index(begin), old.index(end) + len(end)
            content = old[:start] + region + old[stop:]
        else:
            content = region + "\n"
        if name.endswith(".yaml"):
            # Safe-load and reject duplicate top-level keys, including manual/generated collisions.
            parsed = yaml.compose(content, Loader=yaml.SafeLoader)
            if not isinstance(parsed, yaml.MappingNode):
                raise ValueError(f"report must be a YAML mapping: {target}")
            keys = [key.value for key, _ in parsed.value]
            if len(keys) != len(set(keys)):
                raise ValueError(f"duplicate YAML keys in report: {target}")
            yaml.safe_load(content)
        prepared[target] = content
    for target, content in prepared.items():
        temporary = target.with_name(target.name + ".recovery-tmp")
        if temporary.is_symlink():
            raise ValueError(f"refusing symlink temporary report: {temporary}")
        try:
            with temporary.open("w", encoding="utf-8", newline="") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return identity
