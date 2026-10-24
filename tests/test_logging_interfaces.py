import json
import logging

from agrosphere_orchestrator.interfaces import AgentExecutor, CodexWorkspace
from agrosphere_orchestrator.logging import JsonFormatter, configure_logging


def test_structured_logging():
    record = logging.LogRecord("aeo", logging.INFO, "", 0, "task %s", ("one",), None)
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "task one" and payload["level"] == "INFO"
    configure_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING


def test_interfaces_have_no_execution_implementation():
    assert AgentExecutor._is_protocol and CodexWorkspace._is_protocol
