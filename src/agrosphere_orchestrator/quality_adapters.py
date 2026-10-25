"""Deterministic adapters; no model output is accepted as validation evidence."""

import asyncio
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol

from .codex_runtime import executable, permission_arguments, reject_local_configuration
from .execution_context import safe_relative
from .execution_models import ExecutionMode
from .execution_process import CodexProcessManager, Redactor
from .execution_workspace import probe_isolation
from .quality_models import Finding, GateState, Severity


class GateValidator(Protocol):
    async def evaluate(self, gate, repository: Path, command) -> dict: ...


class SandboxedValidator:
    """Read-only native sandbox. Builds needing writes use separately granted AEO-2 worktrees."""

    def __init__(self, settings):
        self.settings = settings

    async def evaluate(self, gate, repository, command):
        reject_local_configuration(repository)
        request = SimpleNamespace(
            worktree_path=str(repository),
            mode=ExecutionMode.READ_ONLY,
            allowed_file_scopes=["."],
            context_digest=gate.id,
            role_instructions="",
        )
        permissions = permission_arguments(
            request,
            [
                *[safe_relative(repository, p) for p in gate.inputs],
                *[Path(p) for p in command.read_paths],
            ],
        )
        name = next(
            p.split("=", 1)[1].strip('"')
            for p in permissions
            if p.startswith("default_permissions=")
        )
        self.settings.execution_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            dir=self.settings.execution_root, prefix="quality-"
        ) as folder:
            isolation = await asyncio.to_thread(
                probe_isolation, executable(self.settings), request, permissions, Path(folder)
            )
            outcome = await CodexProcessManager().run(
                [
                    executable(self.settings),
                    *permissions,
                    "sandbox",
                    "--permission-profile",
                    name,
                    "--cd",
                    str(repository),
                    "--",
                    *command.argv,
                ],
                repository,
                "",
                min(command.timeout_seconds, gate.timeout_seconds),
            )
        return {
            "exit_code": outcome.exit_code,
            "stdout": Redactor().clean(outcome.stdout),
            "stderr": Redactor().clean(outcome.stderr),
            "timed_out": outcome.timed_out,
            "truncated": outcome.truncated,
            "cancelled": outcome.cancelled,
            "isolation": isolation,
            "runtime_reads": command.read_paths,
        }


def interpret(gate, raw):
    """Only deterministic runner output enters here. Strict parsing fails closed."""
    result = {"state": GateState.PASSED, "findings": [], "test_cases": {}, "coverage": None}
    if raw.get("timed_out") or raw.get("cancelled") or raw.get("truncated"):
        raise ValueError("Incomplete validator output")
    if raw.get("exit_code") != gate.expected_exit:
        result["state"] = GateState.FAILED
    output = raw.get("stdout", "")
    if gate.format in {"json", "coverage"}:
        data = json.loads(output)
        if not isinstance(data, dict):
            raise ValueError("Validator report must be an object")
        if gate.format == "json":
            if data.get("validator_version") != gate.validator_version or not isinstance(
                data.get("findings"), list
            ):
                raise ValueError("Scanner version/findings evidence is missing")
            result["findings"] = [
                Finding.model_validate(f).model_dump(mode="json") for f in data["findings"]
            ]
            cases = data.get("test_cases", {})
            if not isinstance(cases, dict) or any(
                v not in {"passed", "failed", "skipped"} for v in cases.values()
            ):
                raise ValueError("Invalid test case evidence")
            result["test_cases"] = cases
        else:
            # coverage.py JSON; numeric percentages without tool output are not proof.
            percent = data["totals"]["percent_covered"]
            if (
                isinstance(percent, bool)
                or not isinstance(percent, (float, int))
                or not 0 <= percent <= 100
            ):
                raise ValueError("Invalid coverage evidence")
            result["coverage"] = percent
            if percent < gate.minimum_coverage:
                result["state"] = GateState.FAILED
    elif gate.format == "junit":
        if "<!DOCTYPE" in output.upper() or "<!ENTITY" in output.upper():
            raise ValueError("Unsafe XML evidence")
        try:
            xml = ET.fromstring(output)
        except ET.ParseError as exc:
            raise ValueError("Malformed JUnit evidence") from exc
        if xml.tag not in {"testsuite", "testsuites"}:
            raise ValueError("Not a JUnit report")
        cases = list(xml.iter("testcase"))
        if not cases:
            raise ValueError("JUnit has no evaluated tests")
        for case in cases:
            name = (case.get("classname", "") + "." + case.attrib["name"]).lstrip(".")
            if name in result["test_cases"]:
                raise ValueError("Duplicate test case identifier")
            status = (
                "failed"
                if case.find("failure") is not None or case.find("error") is not None
                else "skipped"
                if case.find("skipped") is not None
                else "passed"
            )
            result["test_cases"][name] = status
        if any(v == "failed" for v in result["test_cases"].values()) or list(xml.iter("error")):
            result["state"] = GateState.FAILED
    elif gate.format == "sarif":
        data = json.loads(output)
        if data.get("version") != "2.1.0" or not data.get("runs"):
            raise ValueError("Invalid SARIF evidence")
        levels = {
            "error": Severity.HIGH,
            "warning": Severity.MEDIUM,
            "note": Severity.LOW,
            "none": Severity.INFORMATIONAL,
        }
        for run in data["runs"]:
            driver = run["tool"]["driver"]
            if (
                driver.get("semanticVersion", driver.get("version")) != gate.validator_version
                or "results" not in run
            ):
                raise ValueError("Missing scanner version or SARIF results")
            rules = {r["id"]: r for r in driver.get("rules", [])}
            for index, item in enumerate(run["results"]):
                rule = rules.get(item.get("ruleId"), {})
                score = item.get("properties", {}).get(
                    "security-severity", rule.get("properties", {}).get("security-severity")
                )
                severity = levels[item.get("level", "warning")]
                if score is not None:
                    score = float(score)
                    if not 0 <= score <= 10:
                        raise ValueError("Invalid security severity")
                    severity = (
                        Severity.CRITICAL
                        if score >= 9
                        else Severity.HIGH
                        if score >= 7
                        else Severity.MEDIUM
                        if score >= 4
                        else Severity.LOW
                    )
                # SARIF suppressions are retained in raw evidence, never honored automatically.
                result["findings"].append(
                    Finding(
                        id="sarif-" + str(index) + "-" + str(len(result["findings"])),
                        message=item["message"]["text"],
                        severity=severity,
                    ).model_dump(mode="json")
                )
    return result


def documentation(gate, repository):
    findings = []
    for value in gate.required_files:
        target = safe_relative(repository, value)
        if not target.is_file() or not target.read_bytes().strip():
            findings.append(
                Finding(
                    id="document-" + str(len(findings)),
                    message="Missing or empty documentation: " + value,
                ).model_dump(mode="json")
            )
        elif target.suffix == ".puml":
            text = target.read_text(encoding="utf-8")
            if (
                not text.strip().startswith("@startuml")
                or not text.strip().endswith("@enduml")
                or "!includeurl" in text.lower()
            ):
                findings.append(
                    Finding(
                        id="diagram-" + str(len(findings)),
                        message="Invalid editable PlantUML source: " + value,
                    ).model_dump(mode="json")
                )
    return {
        "exit_code": 1 if findings else 0,
        "stdout": "",
        "stderr": "",
        "findings": findings,
        "state": GateState.FAILED if findings else GateState.PASSED,
        "test_cases": {},
        "coverage": None,
    }


def architecture(gate, repository):
    """Explicit approved lexical boundaries, ownership and stack rules; semantic checks use tools."""
    import hashlib

    findings = []
    for rule in gate.architecture_rules:
        target = safe_relative(repository, rule.path)
        exists = target.is_file()
        failed = rule.repository != gate.repository
        if rule.kind == "required-file":
            failed = failed or not exists
        elif rule.kind == "prohibited-file":
            failed = failed or exists
        elif rule.kind == "database-owner":
            failed = failed or (exists and rule.value != gate.repository)
        elif not exists:
            failed = True
        elif rule.kind == "approved-hash":
            failed = failed or hashlib.sha256(target.read_bytes()).hexdigest() != rule.value
        else:
            found = rule.value in target.read_text(encoding="utf-8")
            failed = failed or (not found if rule.kind == "required-token" else found)
        if failed:
            findings.append(
                Finding(
                    id=rule.id,
                    message="Architecture rule violated: " + rule.kind + " at " + rule.path,
                    severity=Severity.HIGH,
                    location=rule.path,
                ).model_dump(mode="json")
            )
    return {
        "exit_code": 1 if findings else 0,
        "stdout": "",
        "stderr": "",
        "findings": findings,
        "state": GateState.FAILED if findings else GateState.PASSED,
        "test_cases": {},
        "coverage": None,
    }
