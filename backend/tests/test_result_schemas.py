from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas import ParameterDefinitionCreate, ResultSaveInput, ResultValueInput


def test_result_parameter_ids_must_be_unique() -> None:
    with pytest.raises(ValidationError, match="can only appear once"):
        ResultSaveInput(
            values=[
                ResultValueInput(parameter_definition_id="parameter-id", value_text="first"),
                ResultValueInput(parameter_definition_id="parameter-id", value_text="second"),
            ]
        )


def test_result_observed_at_requires_timezone() -> None:
    with pytest.raises(ValidationError, match="timezone offset"):
        ResultValueInput(
            parameter_definition_id="parameter-id",
            value_text="value",
            observed_at=datetime.now(),
        )


def test_result_draft_can_be_empty() -> None:
    payload = ResultSaveInput(values=[], ready_for_validation=False)
    assert payload.values == []
    assert payload.ready_for_validation is False


def test_select_parameter_accepts_code_label_options() -> None:
    parameter = ParameterDefinitionCreate(
        code="CULTURE_RESULT",
        name="Resultado del cultivo",
        value_type="SELECT",
        options_schema=[
            {"code": "NEGATIVO", "label": "NEGATIVO A UROPATOGENOS"},
            {"code": "DESARROLLO", "label": "DESARROLLO"},
        ],
    )
    assert parameter.options_schema[0]["code"] == "NEGATIVO"
