# AEO-1 completion and validation report

Completed scope: Foundation only. AEO-2 has not started.

## Delivered structure and architecture

The independent project lives at C:/Projects/agrosphere/agrosphere-orchestrator.
Source is in src/agrosphere_orchestrator; registries in config; Alembic in migrations;
tests in tests; sample YAML in examples; reproducible evidence tooling in scripts;
architecture, five ADRs, three PlantUML C4 sources, policies, role documentation,
JSON Schemas and future milestones in docs. README.md contains CLI instructions.

The design uses Python 3.12+, Pydantic v2 and pydantic-settings, safe YAML, synchronous
SQLAlchemy transactional services, SQLite, Alembic, Typer, Pytest and Ruff. SDK and Codex
execution exist only as Protocol interfaces. This avoids installing or invoking live
agent dependencies before the execution boundary is approved. See docs/adrs for decisions.

Implemented: manifest-driven loading and discovery; actual Git existence checks; typed
milestone/tasks; duplicate/missing dependency and cycle rejection; project/milestone/task/
run/approval persistence; explicit task transitions and dependency gates; fail-closed
approval policy; append-only transactional audit; idempotent exact imports with content
conflict rejection; read-only status/inspection and milestone-validation CLI; JSON logs.
Nine organizational roles include developer Java/Python/Angular specializations and
responsibilities, named contracts, allowlists, boundaries and handoffs.

## Final executed validation

Executed with the project's Python 3.14.2 virtual environment. Full exact argv, working
directory, exit code, stdout and stderr for each command are in [commands.json](commands.json).
The installed dependency versions are retained by the pip freeze command in that file.

| Command (project virtual-environment Python) | Exit | Result |
|---|---:|---|
| -m pytest -v --junitxml=docs/validation/pytest.xml | 0 | 30 passed, no skips |
| -m ruff check . | 0 | All checks passed |
| -m ruff format --check . | 0 | All Python files formatted |
| -m pip check | 0 | No broken requirements |
| -m alembic upgrade head | 0 | Initial migration applied |
| -m alembic check | 0 | No schema drift |
| -m agrosphere_orchestrator.cli project-status | 0 | Existing database read successfully |
| -m agrosphere_orchestrator.cli repository-inspect | 0 | 12 confirmed repositories inspected |
| -m agrosphere_orchestrator.cli milestone-validate examples/aeo-1.yaml | 0 | Valid milestone, 2 tasks |
| -m pip freeze | 0 | Actual installed versions recorded |

The outer command .\.venv\Scripts\python.exe scripts/validate.py returned exit 0.
JUnit evidence: [pytest.xml](pytest.xml).

## Required acceptance evidence

| Requirement | Executed evidence |
|---|---|
| Invalid definitions rejected | Seven parametrized invalid-definition tests: missing title, extra field, duplicate task, cycle, unknown dependency, empty tasks, duplicate dependencies |
| Missing paths detected | Missing/non-Git inspection test and CLI missing-path rejection |
| Circular dependencies rejected | Cycle fixture introduces first -> second -> first and raises Pydantic ValidationError |
| Unauthorized transitions rejected | pending -> succeeded and succeeded -> ready fail; unfinished dependencies block ready |
| Duplicate creation idempotent | Same plan imported twice yields same task UUIDs, two task rows, four creation events |
| Audit preserves history | Transition history ordered by audit ID; raw UPDATE and DELETE rejected by SQLite triggers |
| Read-only Git inspection | Live repository integration test and 12-repository bootstrap verification hash all Git metadata files before and after |
| Approval policies enforced | Unknown operation defaults to approval; non-allowlisted actor rejected; latest denial blocks start; approved start records run |
| Persistent run lifecycle | running creates a run; terminal transition finishes it with timestamp |

[scripts/verify_repositories.py](../../scripts/verify_repositories.py) was executed with
exit 0: Verified 12 repositories; all Git metadata unchanged. Per-repository paths,
HEADs, porcelain status, file counts and before/after digests are in
[repositories.json](repositories.json). Only the orchestrator manifest was updated.
The live inspection test uses an existing repository without creating test branches or
commits. Registry confirmation records observation, and planning rechecks availability.

## Bootstrap command history and corrected findings

Initial ordinary process-launch attempts failed before a process was created (access
denied; no process exit code). The filesystem fallback was read-only; its subprocess
launcher also failed with EPERM. Reviewed execution subsequently worked.

Executed python --version: exit 0, Python 3.14.2. An environment-probe PowerShell group
listed Git markers and ran python -m pip --version, python -m pytest --version and
python -m ruff --version: group exit 1 because global Ruff was absent. No global packages
were installed. python -m venv .venv returned 0; .\.venv\Scripts\python.exe -m pip
install -e '.[dev]' returned 0 and installed dependencies in this new project only.

First test/lint PowerShell group (.\.venv\Scripts\python.exe -m pytest -q;
.\.venv\Scripts\python.exe -m ruff check .) exited 1: Pytest reported 15 passing
initial tests and six Alembic configuration warnings; Ruff reported one unsorted import.
Added path_separator=os, sorted imports and formatted the new files. A subsequent group
ran ruff check . --fix, ruff format . and pytest -q, returning 0 with 30 passing tests.
No unresolved failures remain. These initial results are historical tool output; final
per-process exit codes and complete output are independently retained in commands.json.

Git initialization was limited to this previously nonexistent project. The PowerShell
group git init; git for-each-ref; git remote -v; Python scripts/validate.py returned 0.
git init reported a new empty repository; ref and remote inventories were empty.
HEAD is an unborn symbolic reference; no branch ref, commit, remote connection or PR
was created. Existing repository metadata was neither initialized nor altered.

## Limitations and unresolved decisions

- Tested on Windows with Python 3.14.2; minimum Python 3.12 and other operating systems
  are declared targets but were not executed here.
- Single-process/single-writer services only; no concurrent orchestration or crash-recovery
  scheduler. SQLite state policies require trusted service use; raw SQL can bypass them.
- Approval actor strings are asserted local identities, not authenticated users. Approvals
  have no expiry, are task/operation-scoped and reusable across retries. The database owner
  can remove audit triggers; history is not cryptographically tamper-evident.
- Contracts in the role registry name artifacts. Typed agent message/result envelopes,
  credential handling, SDK version/transport and workspace isolation remain AEO-2 decisions.
- Configuration and migrations assume a source checkout and CWD-relative operator commands.
  No bundled application packaging, CI service or cloud infrastructure was added.
- PlantUML sources were reviewed as text; no rendered diagrams are claimed.
- No live models, Codex execution, autonomous coding, GitHub writes, deployments, commits,
  branch refs or multi-agent concurrency were implemented.

## Run the CLI

From the project root after dependency installation, use:

```powershell
.\.venv\Scripts\aeo.exe project-status
.\.venv\Scripts\aeo.exe repository-inspect
.\.venv\Scripts\aeo.exe milestone-validate examples/aeo-1.yaml
```

For a fresh database run .\.venv\Scripts\python.exe -m alembic upgrade head first.
The initialized local aeo.db is ignored by Git and contains schema only; test data lives
in temporary fixture databases. CLI commands do not execute the sample milestone.

## Exact AEO-2 proposal

Separate approval is required. Scope is one serial, operator-invoked, approved task
through a concrete Agents SDK/Codex adapter: typed request/result/evidence contracts,
authenticated approval scoped to immutable task/repository/operation, isolated allowed
workspace, budget/timeout/cancellation/redaction controls, durable outcomes and fake
adapter tests. Opt-in live contract tests require separate authorization. Exclude autonomous
queues, concurrent agents, GitHub writes, merges, deployments and coordinated writes to
multiple repositories. See [roadmap](../roadmap.md) for acceptance criteria and AEO-3–6.

## AEO-1B validation update

The AEO-1 sections above retain the original foundation history. The latest commands.json
and pytest.xml now describe the extended AEO-1B suite and migration 0002. The database now
contains recovery observations in addition to the unchanged foundation schema. See
[recovery report](../../project/RECOVERY_REPORT.md) and [workspace verification](recovery.json).

AEO-1B initial process creation failed with access denied; no process exit code existed.
Reviewed execution succeeded. The first expanded suite passed 41 tests; the initial Ruff
check reported import and multi-statement formatting findings. Formatting/import fixes
resolved them. Subsequent edge-case tests passed 44 tests before the final source-content
fingerprint regression was added. Final exact commands and exit codes are in commands.json.
Application tests/builds were not executed, and no application acceptance completion is claimed.
