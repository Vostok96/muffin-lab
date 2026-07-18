from app.services import derive_care_setting


def test_outpatient_origin_with_specialty_is_ambulatory() -> None:
    assert derive_care_setting("CONSULTA_EXTERNA", "CONSULTA EXTERNA", "UROLOGIA", "UROLOGIA") == "AMBULATORIO"


def test_hospital_origin_with_hospital_service_is_inpatient() -> None:
    assert (
        derive_care_setting("HOSPITALIZACION", "HOSPITALIZACION", "HOSP_MEDICINA", "HOSP. MEDICINA")
        == "INTERNADO_NO_UCI"
    )


def test_gineco_obstetricia_service_is_inpatient() -> None:
    assert (
        derive_care_setting(
            "HOSPITALIZACION",
            "HOSPITALIZACIÓN",
            "HOSP_GINECO_OBSTETRICIA",
            "HOSP. GINECO-OBSTETRICIA",
        )
        == "INTERNADO_NO_UCI"
    )


def test_icu_origin_overrides_general_inpatient_service() -> None:
    assert derive_care_setting("UCI", "UCI", "HOSP_MEDICINA", "HOSP. MEDICINA") == "UCI"


def test_conflicting_hospital_and_emergency_evidence_is_unknown() -> None:
    assert derive_care_setting("HOSPITALIZACION", "HOSPITALIZACION", "EMERGENCIA", "EMERGENCIA") == "DESCONOCIDO"


def test_ambiguous_ucin_without_origin_evidence_is_unknown() -> None:
    assert derive_care_setting("REFERIDO", "REFERIDO", "UCIN", "UCIN") == "DESCONOCIDO"
