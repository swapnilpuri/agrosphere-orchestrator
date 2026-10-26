"""Shared documentation ownership policy; explicit internal scope never widens application ownership."""

from .design_models import DesignInput


def architecture_owner(inputs: DesignInput) -> str:
    return (
        "agrosphere-orchestrator"
        if inputs.documentation_scope == "internal-orchestrator"
        else "agrosphere-architecture"
    )


def service_owners(inputs: DesignInput) -> set[str]:
    if inputs.documentation_scope == "internal-orchestrator":
        return {"agrosphere-orchestrator"}
    return {t.repository for t in inputs.plan.tasks} - {
        "agrosphere-architecture",
        "agrosphere-contracts",
        "agrosphere-orchestrator",
    }
