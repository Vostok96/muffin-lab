"""Unit tests for microbiology advanced schemas."""

import pytest
from pydantic import ValidationError

from app.schemas import (
    AntimicrobialResultInput,
    AntimicrobialResultUpdate,
    AstPanelAntibioticInput,
    IsolateCreate,
)


def test_isolate_requires_organism() -> None:
    with pytest.raises(ValidationError, match="organism_id"):
        IsolateCreate()


def test_isolate_optional_fields_can_be_null() -> None:
    isolate = IsolateCreate(
        organism_id="org-id",
        colony_count_option_id=None,
        phenotype=None,
        comment=None,
        ast_panel_id=None,
    )
    assert isolate.organism_id == "org-id"
    assert isolate.colony_count_option_id is None


def test_isotate_rejects_long_phenotype() -> None:
    with pytest.raises(ValidationError, match="at most 500"):
        IsolateCreate(organism_id="org-id", phenotype="X" * 501)


def test_antimicrobial_result_valid() -> None:
    ar = AntimicrobialResultInput(
        antibiotic_id="abx-id",
        interpretation="S",
        mic_value="<=2",
        method="Microdilution",
    )
    assert ar.interpretation == "S"
    assert ar.mic_value == "<=2"


def test_antimicrobial_result_invalid_interpretation() -> None:
    with pytest.raises(ValidationError, match="interpretation"):
        AntimicrobialResultInput(
            antibiotic_id="abx-id",
            interpretation="INVALID",
        )


def test_antimicrobial_result_mic_optional() -> None:
    ar = AntimicrobialResultInput(
        antibiotic_id="abx-id",
        interpretation="NA",
    )
    assert ar.mic_value is None


def test_antimicrobial_result_update_partial() -> None:
    update = AntimicrobialResultUpdate(mic_value=">=8")
    assert update.mic_value == ">=8"
    assert update.interpretation is None


def test_panel_antibiotic_defaults_to_susceptible() -> None:
    relation = AstPanelAntibioticInput(display_order=5, default_method="CMI")
    assert relation.default_interpretation == "S"


def test_defined_comment_code_pattern() -> None:
    with pytest.raises(ValidationError, match="pattern"):
        from app.schemas import DefinedCommentCreate
        DefinedCommentCreate(code="invalid code!", text="Some comment")
