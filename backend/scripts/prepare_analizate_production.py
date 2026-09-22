"""Prepare the Analizate Huaraz production dataset.

Run after Alembic migrations and the base seed. Passwords are read from
environment variables so deployment secrets are not stored in the repository.
"""

from __future__ import annotations

import os
from typing import Any

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    Clinician,
    Container,
    Destination,
    Exam,
    ExamParameter,
    ExamSpecimenType,
    LaboratoryArea,
    Origin,
    ParameterDefinition,
    Role,
    Service,
    SpecimenType,
    User,
    UserAreaPermission,
)
from app.security import hash_password
from app.services import bootstrap_security_data, normalized_catalog_key


CLIENT_USERS = (
    {
        "username": "admin-analizate",
        "given_name": "Administrador",
        "family_name": "Analizate",
        "role_codes": ("ADMIN",),
        "password_env": "ANALIZATE_ADMIN_PASSWORD",
        "password_fallback_env": "BOOTSTRAP_ADMIN_PASSWORD",
        "can_validate": True,
    },
    {
        "username": "lab-analizate",
        "given_name": "Laboratorio",
        "family_name": "Analizate",
        "role_codes": ("PROCESS_ADMIN", "PROCESSOR"),
        "password_env": "ANALIZATE_LAB_PASSWORD",
        "can_validate": True,
    },
)

AREAS = (
    ("BIOCHEMISTRY", "BIOQUIMICA", "LABORATORIO CLINICO"),
    ("MICROBIOLOGY", "MICROBIOLOGIA", "MICROBIOLOGIA"),
    ("URINALYSIS", "URIANALISIS", "LABORATORIO CLINICO"),
    ("SEMEN", "SEMEN", "LABORATORIO CLINICO"),
    ("HEMATOLOGY", "HEMATOLOGIA", "LABORATORIO CLINICO"),
    ("PREGNANCY", "EMBARAZO", "LABORATORIO CLINICO"),
    ("IMMUNOLOGY", "INMUNOLOGIA", "LABORATORIO CLINICO"),
    ("TUMOR_MARKERS", "MARCADORES TUMORALES", "LABORATORIO CLINICO"),
    ("ALLERGY", "ALERGIAS", "LABORATORIO CLINICO"),
    ("ENDOCRINOLOGY", "ENDOCRINOLOGIA", "LABORATORIO CLINICO"),
    ("PROFILES", "PERFILES", "LABORATORIO CLINICO"),
    ("PARASITOLOGY", "PARASITOLOGIA", "LABORATORIO CLINICO"),
    ("PATHOLOGY", "ANATOMIA PATOLOGICA Y CITOLOGIA", "PATOLOGIA"),
    ("GENERAL_TESTS", "EXAMENES GENERALES", "LABORATORIO CLINICO"),
    ("RECEPTION", "RECEPCION DE MUESTRAS", "LABORATORIO CLINICO"),
)

ORIGINS = (
    "PARTICULAR",
    "CONVENIO",
    "REFERIDO",
    "DOMICILIO",
    "EMPRESA",
)

SERVICES = (
    "LABORATORIO ANALIZATE",
    "TOMA DE MUESTRA",
    "ATENCION DOMICILIARIA",
    "REFERENCIA EXTERNA",
)

SPECIMENS = (
    ("SERUM", "SUERO", "TUBO"),
    ("PLASMA", "PLASMA", "TUBO"),
    ("WHOLE_BLOOD", "SANGRE TOTAL", "TUBO"),
    ("URINE", "ORINA", "FRASCO"),
    ("URINE_24H", "ORINA DE 24 HORAS", "FRASCO"),
    ("STOOL", "HECES", "FRASCO"),
    ("SEMEN", "SEMEN", "FRASCO"),
    ("SECRETION", "SECRECION", "HISOPADO"),
    ("SWAB", "HISOPADO", "HISOPADO"),
    ("SPUTUM", "ESPUTO", "FRASCO"),
    ("TISSUE", "TEJIDO", "FRASCO"),
    ("BIOLOGICAL_FLUID", "LIQUIDO BIOLOGICO", "FRASCO"),
    ("SLIDE", "LAMINA", "LAMINA"),
)

GENERIC_PARAMETERS = (
    ("GENERIC_RESULT", "RESULTADO", 1, True, "LONG_TEXT"),
    ("GENERIC_UNIT", "UNIDAD", 2, False, "TEXT"),
    ("GENERIC_REFERENCE_VALUE", "VALOR DE REFERENCIA", 3, False, "LONG_TEXT"),
    ("GENERIC_OBSERVATION", "OBSERVACIONES", 4, False, "LONG_TEXT"),
)

CULTURE_PARAMETER_CODES = (
    ("CULTURE_RESULT", 1, True),
    ("CULTURE_OBSERVATION", 2, False),
    ("CULTURE_GRAM", 3, False),
    ("CULTURE_NITRITE", 4, False),
    ("CULTURE_COLONY_COUNT", 5, False),
)

# area, exam name, specimen code, is_culture, external provider
EXAMS = (
    ("BIOCHEMISTRY", "GLICEMIA BASAL", "SERUM", False, None),
    ("BIOCHEMISTRY", "GLICEMIA AL AZAR", "SERUM", False, None),
    ("BIOCHEMISTRY", "TEST DE TOLERANCIA A LA GLUCOSA", "SERUM", False, None),
    ("BIOCHEMISTRY", "HEMOGLOBINA GLICOSILADA HBA1C", "WHOLE_BLOOD", False, None),
    ("BIOCHEMISTRY", "UREA", "SERUM", False, None),
    ("BIOCHEMISTRY", "CREATININA", "SERUM", False, None),
    ("BIOCHEMISTRY", "ACIDO URICO", "SERUM", False, None),
    ("BIOCHEMISTRY", "COLESTEROL TOTAL", "SERUM", False, None),
    ("BIOCHEMISTRY", "COLESTEROL HDL", "SERUM", False, None),
    ("BIOCHEMISTRY", "COLESTEROL LDL", "SERUM", False, None),
    ("BIOCHEMISTRY", "COLESTEROL VLDL", "SERUM", False, None),
    ("BIOCHEMISTRY", "TRIGLICERIDOS", "SERUM", False, None),
    ("BIOCHEMISTRY", "BILIRRUBINAS TOTALES Y FRACCIONADAS", "SERUM", False, None),
    ("BIOCHEMISTRY", "TGO", "SERUM", False, None),
    ("BIOCHEMISTRY", "TGP", "SERUM", False, None),
    ("BIOCHEMISTRY", "FOSFATASA ALCALINA", "SERUM", False, None),
    ("BIOCHEMISTRY", "PROTEINAS TOTALES Y FRACCIONADAS", "SERUM", False, None),
    ("BIOCHEMISTRY", "AMILASA", "SERUM", False, None),
    ("BIOCHEMISTRY", "LIPASA", "SERUM", False, None),
    ("BIOCHEMISTRY", "ELECTROLITOS SERICOS", "SERUM", False, None),
    ("BIOCHEMISTRY", "GAMMA GLUTAMIL TRANSPEPTIDASA GGT", "SERUM", False, None),
    ("MICROBIOLOGY", "UROCULTIVO Y ANTIBIOGRAMA", "URINE", True, None),
    ("MICROBIOLOGY", "COPROCULTIVO", "STOOL", True, None),
    ("MICROBIOLOGY", "CULTIVO DE SECRECIONES", "SECRETION", True, None),
    ("MICROBIOLOGY", "CULTIVO DE HONGOS", "SECRETION", True, None),
    ("MICROBIOLOGY", "EXAMEN DIRECTO DE HONGOS", "SECRETION", False, None),
    ("MICROBIOLOGY", "ESPERMOCULTIVO", "SEMEN", True, None),
    ("MICROBIOLOGY", "COLORACION GRAM", "SECRETION", False, None),
    ("MICROBIOLOGY", "BK CULTIVO", "SPUTUM", True, "SYNLAB"),
    ("MICROBIOLOGY", "BK DIRECTO", "SPUTUM", False, None),
    ("MICROBIOLOGY", "TINTA CHINA", "BIOLOGICAL_FLUID", False, None),
    ("URINALYSIS", "DEPURACION DE CREATININA", "URINE_24H", False, None),
    ("URINALYSIS", "PROTEINURIA EN ORINA DE 24 HORAS", "URINE_24H", False, None),
    ("URINALYSIS", "EXAMEN COMPLETO DE ORINA", "URINE", False, None),
    ("URINALYSIS", "SEDIMENTO URINARIO", "URINE", False, None),
    ("SEMEN", "ESPERMATOGRAMA", "SEMEN", False, None),
    ("SEMEN", "ANTICUERPOS ANTIESPERMATOZOIDES", "SEMEN", False, "SYNLAB"),
    ("HEMATOLOGY", "HEMOGRAMA COMPLETO", "WHOLE_BLOOD", False, None),
    ("HEMATOLOGY", "HEMOGLOBINA HEMATOCRITO", "WHOLE_BLOOD", False, None),
    ("HEMATOLOGY", "VELOCIDAD DE SEDIMENTACION VSG", "WHOLE_BLOOD", False, None),
    ("HEMATOLOGY", "GRUPO SANGUINEO Y FACTOR RH", "WHOLE_BLOOD", False, None),
    ("HEMATOLOGY", "RECUENTO DE RETICULOCITOS", "WHOLE_BLOOD", False, None),
    ("HEMATOLOGY", "RECUENTO DE PLAQUETAS", "WHOLE_BLOOD", False, None),
    ("HEMATOLOGY", "GOTA GRUESA HEMOPARASITOS", "WHOLE_BLOOD", False, None),
    ("HEMATOLOGY", "COOMBS DIRECTO", "WHOLE_BLOOD", False, None),
    ("HEMATOLOGY", "COOMBS INDIRECTO", "SERUM", False, None),
    ("HEMATOLOGY", "HIERRO SERICO", "SERUM", False, None),
    ("HEMATOLOGY", "TRANSFERRINA SATURACION", "SERUM", False, "SYNLAB"),
    ("HEMATOLOGY", "FERRITINA", "SERUM", False, None),
    ("HEMATOLOGY", "VITAMINA B12", "SERUM", False, "SYNLAB"),
    ("HEMATOLOGY", "ACIDO FOLICO", "SERUM", False, "SYNLAB"),
    ("HEMATOLOGY", "INR", "PLASMA", False, None),
    ("HEMATOLOGY", "TIEMPO DE PROTROMBINA TPT", "PLASMA", False, None),
    ("HEMATOLOGY", "TIEMPO DE TROMBOPLASTINA PARCIAL ACTIVADA TTPA", "PLASMA", False, None),
    ("HEMATOLOGY", "FIBRINOGENO", "PLASMA", False, None),
    ("HEMATOLOGY", "DIMERO D", "PLASMA", False, None),
    ("PREGNANCY", "TEST DE EMBARAZO", "SERUM", False, None),
    ("PREGNANCY", "BHCG CUALITATIVO", "SERUM", False, None),
    ("PREGNANCY", "BHCG CUANTITATIVO", "SERUM", False, None),
    ("IMMUNOLOGY", "RPR", "SERUM", False, None),
    ("IMMUNOLOGY", "PROTEINA C REACTIVA PCR", "SERUM", False, None),
    ("IMMUNOLOGY", "FACTOR REUMATOIDE LATEX", "SERUM", False, None),
    ("IMMUNOLOGY", "ANTIESTREPTOLISINA ASO", "SERUM", False, None),
    ("IMMUNOLOGY", "AGLUTINACIONES EN LAMINA", "SERUM", False, None),
    ("IMMUNOLOGY", "AGLUTINACIONES EN TUBO BRUCELLA", "SERUM", False, "SYNLAB"),
    ("IMMUNOLOGY", "ANTI CCP", "SERUM", False, "SYNLAB"),
    ("IMMUNOLOGY", "ANA", "SERUM", False, "SYNLAB"),
    ("IMMUNOLOGY", "ANCA", "SERUM", False, "SYNLAB"),
    ("IMMUNOLOGY", "ROSA DE BENGALA", "SERUM", False, None),
    ("IMMUNOLOGY", "HIV 1-2 ELISA", "SERUM", False, "SYNLAB"),
    ("IMMUNOLOGY", "HELICOBACTER PYLORI", "SERUM", False, None),
    ("IMMUNOLOGY", "INMUNOGLOBULINA IGE", "SERUM", False, "SYNLAB"),
    ("IMMUNOLOGY", "TORCH IGG IGM", "SERUM", False, "SYNLAB"),
    ("TUMOR_MARKERS", "PSA TOTAL", "SERUM", False, "SYNLAB"),
    ("TUMOR_MARKERS", "PSA LIBRE", "SERUM", False, "SYNLAB"),
    ("TUMOR_MARKERS", "CEA", "SERUM", False, "SYNLAB"),
    ("TUMOR_MARKERS", "AFP", "SERUM", False, "SYNLAB"),
    ("TUMOR_MARKERS", "CA 19-9", "SERUM", False, "SYNLAB"),
    ("TUMOR_MARKERS", "CA 72-4", "SERUM", False, "SYNLAB"),
    ("TUMOR_MARKERS", "CA 15-3", "SERUM", False, "SYNLAB"),
    ("TUMOR_MARKERS", "CA 125", "SERUM", False, "SYNLAB"),
    ("ALLERGY", "EOSINOFILOS RECUENTO", "WHOLE_BLOOD", False, None),
    ("ALLERGY", "IGE DOSAJE", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "FSH", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "LH", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "ESTRADIOL", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "PROGESTERONA", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "CORTISOL", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "INSULINA", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "PROLACTINA", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "T3", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "T4", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "T4 LIBRE", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "TSH", "SERUM", False, "SYNLAB"),
    ("ENDOCRINOLOGY", "TESTOSTERONA TOTAL", "SERUM", False, "SYNLAB"),
    ("PROFILES", "PERFIL RENAL", "SERUM", False, None),
    ("PROFILES", "PERFIL DE COAGULACION", "PLASMA", False, None),
    ("PROFILES", "PERFIL DE ANEMIA HEMOLITICA", "WHOLE_BLOOD", False, None),
    ("PROFILES", "PERFIL FEMENINO", "SERUM", False, "SYNLAB"),
    ("PROFILES", "PERFIL HEPATITIS", "SERUM", False, "SYNLAB"),
    ("PROFILES", "PERFIL PREOPERATORIO", "WHOLE_BLOOD", False, None),
    ("PROFILES", "PERFIL HEPATICO", "SERUM", False, None),
    ("PROFILES", "PERFIL LIPIDICO", "SERUM", False, None),
    ("PROFILES", "PERFIL TIROIDEO", "SERUM", False, "SYNLAB"),
    ("PROFILES", "PERFIL INMUNOLOGICO BASICO", "SERUM", False, None),
    ("PROFILES", "MARCADORES HEPATICOS", "SERUM", False, "SYNLAB"),
    ("PROFILES", "PERFIL DE ANEMIA CARENCIAL", "SERUM", False, "SYNLAB"),
    ("PROFILES", "PERFIL DE GESTANTE", "WHOLE_BLOOD", False, None),
    ("PARASITOLOGY", "PARASITOLOGICO SERIADO 1-2-3", "STOOL", False, None),
    ("PARASITOLOGY", "REACCION INFLAMATORIA", "STOOL", False, None),
    ("PARASITOLOGY", "THEVENON EN HECES 1-2-3", "STOOL", False, None),
    ("PARASITOLOGY", "TEST DE GRAHAM", "SLIDE", False, None),
    ("PARASITOLOGY", "ACAROS PIEL Y PESTANAS", "SLIDE", False, None),
    ("PARASITOLOGY", "COPROLOGICO FUNCIONAL", "STOOL", False, None),
    ("GENERAL_TESTS", "ADA LIQUIDO ASCITICO", "BIOLOGICAL_FLUID", False, "SYNLAB"),
    ("GENERAL_TESTS", "ADA LIQUIDO CEFALORRAQUIDEO", "BIOLOGICAL_FLUID", False, "SYNLAB"),
    ("GENERAL_TESTS", "ADA LIQUIDO PLEURAL", "BIOLOGICAL_FLUID", False, "SYNLAB"),
    ("GENERAL_TESTS", "ANALISIS DE GASES ARTERIALES AGA", "WHOLE_BLOOD", False, None),
    ("GENERAL_TESTS", "PRUEBA DE PATERNIDAD ADN", "WHOLE_BLOOD", False, "SYNLAB"),
    ("PATHOLOGY", "PAP SC VAGINAL", "SLIDE", False, "SYNLAB"),
    ("PATHOLOGY", "PAP LIQUIDOS BIOLOGICOS", "BIOLOGICAL_FLUID", False, "SYNLAB"),
    ("PATHOLOGY", "BLOCK CELL", "BIOLOGICAL_FLUID", False, "SYNLAB"),
    ("PATHOLOGY", "BIOPSIA GANGLIO", "TISSUE", False, "SYNLAB"),
    ("PATHOLOGY", "BIOPSIA GASTRICA", "TISSUE", False, "SYNLAB"),
    ("PATHOLOGY", "BIOPSIA RECTAL", "TISSUE", False, "SYNLAB"),
    ("PATHOLOGY", "BIOPSIA PROSTATA", "TISSUE", False, "SYNLAB"),
    ("PATHOLOGY", "PUNCH PIEL", "TISSUE", False, "SYNLAB"),
    ("PATHOLOGY", "BIOPSIA CERVIX", "TISSUE", False, "SYNLAB"),
    ("PATHOLOGY", "BIOPSIA CORE", "TISSUE", False, "SYNLAB"),
    ("PATHOLOGY", "BIOPSIA BAAF", "TISSUE", False, "SYNLAB"),
)


def env_password(name: str, fallback_name: str | None = None) -> str:
    password = os.getenv(name) or (os.getenv(fallback_name) if fallback_name else None) or ""
    if len(password) < 12:
        raise RuntimeError(f"{name} must contain at least 12 characters.")
    return password


def roles_for(db, codes: tuple[str, ...]) -> list[Role]:
    roles = list(db.scalars(select(Role).where(Role.code.in_(codes))))
    found = {role.code for role in roles}
    missing = set(codes) - found
    if missing:
        raise RuntimeError(f"Missing roles: {', '.join(sorted(missing))}")
    return roles


def ensure_user(db, areas: list[LaboratoryArea], user_spec: dict[str, Any]) -> User:
    user = db.scalar(select(User).where(User.username == user_spec["username"]))
    roles = roles_for(db, user_spec["role_codes"])
    password = env_password(user_spec["password_env"], user_spec.get("password_fallback_env"))
    if not user:
        user = User(
            username=user_spec["username"],
            given_name=user_spec["given_name"],
            family_name=user_spec["family_name"],
            password_hash=hash_password(password),
            roles=roles,
            is_active=True,
        )
        db.add(user)
        db.flush()
    else:
        user.given_name = user_spec["given_name"]
        user.family_name = user_spec["family_name"]
        user.password_hash = hash_password(password)
        user.roles = roles
        user.is_active = True

    if user_spec["can_validate"]:
        for area in areas:
            permission = db.scalar(
                select(UserAreaPermission).where(
                    UserAreaPermission.user_id == user.id,
                    UserAreaPermission.laboratory_area_id == area.id,
                )
            )
            if not permission:
                db.add(
                    UserAreaPermission(
                        user_id=user.id,
                        laboratory_area_id=area.id,
                        can_preliminary_validate=True,
                        can_final_validate=True,
                    )
                )
            else:
                permission.can_preliminary_validate = True
                permission.can_final_validate = True
    return user


def ensure_catalog(db, model, code: str, **values):
    entity = db.scalar(select(model).where(model.code == code))
    if not entity:
        entity = model(code=code, **values)
        db.add(entity)
        db.flush()
    else:
        for field, value in values.items():
            setattr(entity, field, value)
    return entity


def ensure_parameter(db, code: str, name: str, value_type: str, section: str | None = None) -> ParameterDefinition:
    parameter = db.scalar(select(ParameterDefinition).where(ParameterDefinition.code == code))
    if not parameter:
        parameter = ParameterDefinition(code=code, name=name, value_type=value_type, section=section, is_active=True)
        db.add(parameter)
        db.flush()
    else:
        parameter.name = name
        parameter.value_type = value_type
        parameter.section = section
        parameter.options_schema = None
        parameter.is_active = True
    return parameter


def ensure_exam_parameter(db, exam: Exam, parameter: ParameterDefinition, display_order: int, is_required: bool) -> None:
    relation = db.get(ExamParameter, (exam.id, parameter.id))
    if relation:
        relation.display_order = display_order
        relation.external_code = f"ANALIZATE-{parameter.code}"
        relation.is_required = is_required
    else:
        db.add(
            ExamParameter(
                exam_id=exam.id,
                parameter_definition_id=parameter.id,
                display_order=display_order,
                external_code=f"ANALIZATE-{parameter.code}",
                is_required=is_required,
            )
        )


def ensure_exam_specimen(db, exam: Exam, specimen: SpecimenType) -> None:
    relation = db.get(ExamSpecimenType, (exam.id, specimen.id))
    if relation:
        relation.is_favorite = True
    else:
        db.add(ExamSpecimenType(exam_id=exam.id, specimen_type_id=specimen.id, is_favorite=True))


def ensure_institution_catalogs(db) -> list[LaboratoryArea]:
    container_by_code: dict[str, Container] = {}
    for code, name in (("TUBO", "TUBO"), ("FRASCO", "FRASCO"), ("HISOPADO", "HISOPADO"), ("LAMINA", "LAMINA")):
        container_by_code[code] = ensure_catalog(db, Container, code, name=name, is_active=True)

    areas = [
        ensure_catalog(db, LaboratoryArea, code, name=name, section=section, is_active=True)
        for code, name, section in AREAS
    ]

    for origin_name in ORIGINS:
        ensure_catalog(db, Origin, normalized_catalog_key(origin_name), name=origin_name, is_active=True)
    for service_name in SERVICES:
        ensure_catalog(db, Service, normalized_catalog_key(service_name), name=service_name, is_active=True)
    ensure_catalog(db, Clinician, "MEDICO_SOLICITANTE", family_name="MEDICO", given_name="SOLICITANTE", email=None, is_active=True)
    ensure_catalog(db, Destination, "ANALIZATE_LAB", name="LABORATORIO ANALIZATE", is_active=True)

    specimen_by_code: dict[str, SpecimenType] = {}
    for code, name, container_code in SPECIMENS:
        specimen_by_code[code] = ensure_catalog(
            db,
            SpecimenType,
            code,
            name=name,
            container_id=container_by_code[container_code].id,
            parent_id=None,
            is_selectable=True,
            is_active=True,
        )

    area_by_code = {area.code: area for area in areas}
    generic_parameters = [
        (ensure_parameter(db, code, name, value_type, "RESULTADO GENERAL"), display_order, is_required)
        for code, name, display_order, is_required, value_type in GENERIC_PARAMETERS
    ]
    culture_parameters = {
        parameter.code: parameter
        for parameter in db.scalars(
            select(ParameterDefinition).where(
                ParameterDefinition.code.in_([code for code, _display_order, _required in CULTURE_PARAMETER_CODES])
            )
        )
    }

    for area_code, exam_name, specimen_code, is_culture, external_provider in EXAMS:
        code = normalized_catalog_key(exam_name)[:50]
        exam = ensure_catalog(
            db,
            Exam,
            code,
            name=exam_name,
            external_code=f"ANALIZATE-{code}",
            barcode_suffix=code[:12],
            laboratory_area_id=area_by_code[area_code].id,
            sends_to_analyzer=False,
            requires_colony_count=is_culture,
            external_provider=external_provider,
            is_active=True,
        )
        ensure_exam_specimen(db, exam, specimen_by_code[specimen_code])
        if is_culture and all(code in culture_parameters for code, _display_order, _required in CULTURE_PARAMETER_CODES):
            for parameter_code, display_order, is_required in CULTURE_PARAMETER_CODES:
                ensure_exam_parameter(db, exam, culture_parameters[parameter_code], display_order, is_required)
        else:
            for parameter, display_order, is_required in generic_parameters:
                ensure_exam_parameter(db, exam, parameter, display_order, is_required)

    return areas


def disable_development_users(db) -> None:
    disabled_hash = hash_password("disabled-development-account-2026")
    for username in ("dev-admin", "dev-entry", "dev-processor"):
        user = db.scalar(select(User).where(User.username == username))
        if user:
            user.is_active = False
            user.password_hash = disabled_hash


def main() -> None:
    with SessionLocal() as db:
        bootstrap_security_data(db, None, None, "", "", hash_password)
        areas = ensure_institution_catalogs(db)
        for user_spec in CLIENT_USERS:
            ensure_user(db, areas, user_spec)
        disable_development_users(db)
        db.commit()
    print("Analizate production preparation completed.")


if __name__ == "__main__":
    main()
