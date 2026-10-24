import pytest
from pydantic import ValidationError

from agrosphere_orchestrator.models import MilestoneSpec


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-title",
        "unknown-field",
        "duplicate",
        "cycle",
        "unknown-dep",
        "empty",
        "duplicate-dep",
    ],
)
def test_invalid_definitions(plan, mutation):
    data = plan.model_dump()
    if mutation == "missing-title":
        del data["title"]
    elif mutation == "unknown-field":
        data["execute"] = True
    elif mutation == "duplicate":
        data["tasks"].append(data["tasks"][0])
    elif mutation == "cycle":
        data["tasks"][0]["depends_on"] = ["second"]
    elif mutation == "unknown-dep":
        data["tasks"][0]["depends_on"] = ["missing"]
    elif mutation == "empty":
        data["tasks"] = []
    else:
        data["tasks"][1]["depends_on"] = ["first", "first"]
    with pytest.raises(ValidationError):
        MilestoneSpec.model_validate(data)


def test_schema_and_valid_plan(plan):
    assert MilestoneSpec.model_validate_json(plan.model_dump_json()) == plan
    assert "tasks" in MilestoneSpec.model_json_schema()["required"]
