import pytest
from pydantic import ValidationError

from app.schemas import ParameterDefinitionCreate


def test_select_parameter_requires_options() -> None:
    with pytest.raises(ValidationError, match="options_schema is required"):
        ParameterDefinitionCreate(code="RESULT", name="Result", value_type="SELECT")


def test_non_select_parameter_rejects_options() -> None:
    with pytest.raises(ValidationError, match="options_schema is only valid"):
        ParameterDefinitionCreate(code="NOTE", name="Note", value_type="TEXT", options_schema=["A", "B"])


def test_parameter_reference_range_is_ordered() -> None:
    with pytest.raises(ValidationError, match="reference_low cannot be greater"):
        ParameterDefinitionCreate(
            code="COUNT",
            name="Count",
            value_type="TEXT",
            reference_low=10,
            reference_high=5,
        )


def test_valid_select_parameter() -> None:
    parameter = ParameterDefinitionCreate(
        code="CULTURE",
        name="Culture",
        value_type="SELECT",
        options_schema=["NEGATIVE", "POSITIVE"],
    )
    assert parameter.options_schema == ["NEGATIVE", "POSITIVE"]
