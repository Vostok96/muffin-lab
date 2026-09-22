"""add KOH direct exam and exam-specific negative options

Revision ID: 0013_koh_exam_options
Revises: 0012_culture_params_all_exams
Create Date: 2026-09-22
"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa


revision = "0013_koh_exam_options"
down_revision = "0012_culture_params_all_exams"
branch_labels = None
depends_on = None


NEGATIVE_OPTION_PARAMETERS = {
    "URINE_CULTURE": (
        "URO_CULTURE_RESULT",
        "RESULTADO DEL UROCULTIVO",
        [
            {"code": "NEGATIVO_UROPATOGENOS", "label": "NEGATIVO A UROPATOGENOS"},
            {"code": "POSITIVO", "label": "POSITIVO"},
            {"code": "NO_TRAJO_MUESTRA", "label": "NO TRAJO MUESTRA"},
            {"code": "MUESTRA_INADECUADA", "label": "MUESTRA INADECUADA"},
        ],
    ),
    "COPROCULTIVO": (
        "COPRO_CULTURE_RESULT",
        "RESULTADO DEL COPROCULTIVO",
        [
            {"code": "NEGATIVO_ENTEROPATOGENOS", "label": "NEGATIVO PARA ENTEROPATOGENOS"},
            {"code": "POSITIVO", "label": "POSITIVO"},
            {"code": "NO_TRAJO_MUESTRA", "label": "NO TRAJO MUESTRA"},
            {"code": "MUESTRA_INADECUADA", "label": "MUESTRA INADECUADA"},
        ],
    ),
    "HEMOCULTIVO": (
        "HEMO_CULTURE_RESULT",
        "RESULTADO DEL HEMOCULTIVO",
        [
            {"code": "NEGATIVO_5_DIAS_INCUBACION", "label": "NEGATIVO DESPUES DE 5 DIAS DE INCUBACION"},
            {"code": "POSITIVO", "label": "POSITIVO"},
            {"code": "NO_TRAJO_MUESTRA", "label": "NO TRAJO MUESTRA"},
            {"code": "MUESTRA_INADECUADA", "label": "MUESTRA INADECUADA"},
        ],
    ),
}

KOH_PARAMETERS = (
    (
        "KOH_RESULT",
        "RESULTADO KOH",
        1,
        True,
        "SELECT",
        [
            {"code": "NEGATIVO", "label": "NO SE OBSERVAN ESTRUCTURAS FUNGICAS"},
            {"code": "POSITIVO", "label": "SE OBSERVAN ESTRUCTURAS FUNGICAS"},
        ],
        "EXAMEN DIRECTO KOH",
    ),
    ("KOH_STRUCTURES", "ESTRUCTURAS OBSERVADAS", 2, False, "LONG_TEXT", None, "EXAMEN DIRECTO KOH"),
    ("KOH_OBSERVATION", "OBSERVACIONES", 3, False, "LONG_TEXT", None, None),
)

KOH_SPECIMENS = (
    ("OTR_RASPADO_PIEL", "RASPADO DE PIEL"),
    ("OTR_ESCAMAS_PIEL", "ESCAMAS DE PIEL"),
    ("OTR_UNAS", "UÑAS"),
    ("OTR_CABELLOS", "CABELLOS"),
)


def stable_id(entity: str, code: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"muffin:{entity}:{code}"))


def upsert_area(bind: sa.Connection) -> str:
    return bind.execute(
        sa.text(
            "INSERT INTO laboratory_area (id, code, name, section, is_active, created_at, updated_at) "
            "VALUES (:id, 'MICROBIOLOGY', 'MICROBIOLOGIA', 'MICROBIOLOGY', true, now(), now()) "
            "ON CONFLICT (code) DO UPDATE SET "
            "name = EXCLUDED.name, section = EXCLUDED.section, is_active = true, updated_at = now() "
            "RETURNING id"
        ),
        {"id": stable_id("laboratory_area", "MICROBIOLOGY")},
    ).scalar_one()


def upsert_container(bind: sa.Connection) -> str:
    return bind.execute(
        sa.text(
            "INSERT INTO container (id, code, name, is_active, created_at, updated_at) "
            "VALUES (:id, 'CONTENEDOR_PROTOCOLO', 'CONTENEDOR SEGUN PROTOCOLO', true, now(), now()) "
            "ON CONFLICT (code) DO UPDATE SET "
            "name = EXCLUDED.name, is_active = true, updated_at = now() "
            "RETURNING id"
        ),
        {"id": stable_id("container", "CONTENEDOR_PROTOCOLO")},
    ).scalar_one()


def upsert_specimen(
    bind: sa.Connection,
    *,
    code: str,
    name: str,
    container_id: str,
    parent_id: str | None,
    is_selectable: bool,
) -> str:
    return bind.execute(
        sa.text(
            "INSERT INTO specimen_type "
            "(id, code, name, container_id, parent_id, is_selectable, is_active, created_at, updated_at) "
            "VALUES (:id, :code, :name, :container_id, :parent_id, :is_selectable, true, now(), now()) "
            "ON CONFLICT (code) DO UPDATE SET "
            "name = EXCLUDED.name, container_id = EXCLUDED.container_id, parent_id = EXCLUDED.parent_id, "
            "is_selectable = EXCLUDED.is_selectable, is_active = true, updated_at = now() "
            "RETURNING id"
        ),
        {
            "id": stable_id("specimen_type", code),
            "code": code,
            "name": name,
            "container_id": container_id,
            "parent_id": parent_id,
            "is_selectable": is_selectable,
        },
    ).scalar_one()


def upsert_exam(bind: sa.Connection, area_id: str) -> str:
    return bind.execute(
        sa.text(
            "INSERT INTO exam "
            "(id, code, name, external_code, barcode_suffix, laboratory_area_id, sends_to_analyzer, "
            "requires_colony_count, is_active, created_at, updated_at) "
            "VALUES (:id, 'KOH_DIRECTO', 'EXAMEN DIRECTO KOH', 'MUFFIN-KOH_DIRECTO', 'KOH', "
            ":area_id, false, false, true, now(), now()) "
            "ON CONFLICT (code) DO UPDATE SET "
            "name = EXCLUDED.name, external_code = EXCLUDED.external_code, barcode_suffix = EXCLUDED.barcode_suffix, "
            "laboratory_area_id = EXCLUDED.laboratory_area_id, sends_to_analyzer = false, "
            "requires_colony_count = false, is_active = true, updated_at = now() "
            "RETURNING id"
        ),
        {"id": stable_id("exam", "KOH_DIRECTO"), "area_id": area_id},
    ).scalar_one()


def upsert_parameter(
    bind: sa.Connection,
    *,
    code: str,
    name: str,
    value_type: str,
    options_schema: list[dict[str, str]] | None,
    methodology: str | None,
) -> str:
    statement = (
        sa.text(
            "INSERT INTO parameter_definition "
            "(id, code, name, section, value_type, options_schema, methodology, is_active, created_at, updated_at) "
            "VALUES (:id, :code, :name, 'MICROBIOLOGY', :value_type, :options_schema, :methodology, true, now(), now()) "
            "ON CONFLICT (code) DO UPDATE SET "
            "name = EXCLUDED.name, section = EXCLUDED.section, value_type = EXCLUDED.value_type, "
            "options_schema = EXCLUDED.options_schema, methodology = EXCLUDED.methodology, "
            "is_active = true, updated_at = now() "
            "RETURNING id"
        )
        .bindparams(sa.bindparam("options_schema", type_=sa.JSON()))
    )
    return bind.execute(
        statement,
        {
            "id": stable_id("parameter_definition", code),
            "code": code,
            "name": name,
            "value_type": value_type,
            "options_schema": options_schema,
            "methodology": methodology,
        },
    ).scalar_one()


def set_exam_parameter(
    bind: sa.Connection,
    *,
    exam_id: str,
    parameter_id: str,
    code: str,
    display_order: int,
    is_required: bool,
) -> None:
    bind.execute(
        sa.text(
            "INSERT INTO exam_parameter "
            "(exam_id, parameter_definition_id, display_order, external_code, is_required) "
            "VALUES (:exam_id, :parameter_id, :display_order, :external_code, :is_required) "
            "ON CONFLICT (exam_id, parameter_definition_id) DO UPDATE SET "
            "display_order = EXCLUDED.display_order, external_code = EXCLUDED.external_code, "
            "is_required = EXCLUDED.is_required"
        ),
        {
            "exam_id": exam_id,
            "parameter_id": parameter_id,
            "display_order": display_order,
            "external_code": f"AND-{code}",
            "is_required": is_required,
        },
    )


def upgrade() -> None:
    bind = op.get_bind()
    area_id = upsert_area(bind)
    container_id = upsert_container(bind)
    parent_id = upsert_specimen(
        bind,
        code="OTR_PIEL_ANEXOS",
        name="PIEL Y ANEXOS (MICOLOGÍA)",
        container_id=container_id,
        parent_id=None,
        is_selectable=False,
    )

    specimen_ids = [
        upsert_specimen(
            bind,
            code=code,
            name=name,
            container_id=container_id,
            parent_id=parent_id,
            is_selectable=True,
        )
        for code, name in KOH_SPECIMENS
    ]

    koh_exam_id = upsert_exam(bind, area_id)
    for specimen_id in specimen_ids:
        bind.execute(
            sa.text(
                "INSERT INTO exam_specimen_type (exam_id, specimen_type_id, is_favorite) "
                "VALUES (:exam_id, :specimen_id, false) "
                "ON CONFLICT (exam_id, specimen_type_id) DO NOTHING"
            ),
            {"exam_id": koh_exam_id, "specimen_id": specimen_id},
        )

    for code, name, display_order, required, value_type, options_schema, methodology in KOH_PARAMETERS:
        parameter_id = upsert_parameter(
            bind,
            code=code,
            name=name,
            value_type=value_type,
            options_schema=options_schema,
            methodology=methodology,
        )
        set_exam_parameter(
            bind,
            exam_id=koh_exam_id,
            parameter_id=parameter_id,
            code=code,
            display_order=display_order,
            is_required=required,
        )

    for exam_code, (parameter_code, parameter_name, options_schema) in NEGATIVE_OPTION_PARAMETERS.items():
        exam_id = bind.execute(sa.text("SELECT id FROM exam WHERE code = :code"), {"code": exam_code}).scalar()
        if not exam_id:
            continue
        parameter_id = upsert_parameter(
            bind,
            code=parameter_code,
            name=parameter_name,
            value_type="SELECT",
            options_schema=options_schema,
            methodology="CULTIVO MANUAL",
        )
        bind.execute(
            sa.text(
                "DELETE FROM exam_parameter USING parameter_definition "
                "WHERE exam_parameter.parameter_definition_id = parameter_definition.id "
                "AND exam_parameter.exam_id = :exam_id "
                "AND parameter_definition.code = 'CULTURE_RESULT'"
            ),
            {"exam_id": exam_id},
        )
        set_exam_parameter(
            bind,
            exam_id=exam_id,
            parameter_id=parameter_id,
            code=parameter_code,
            display_order=1,
            is_required=True,
        )


def downgrade() -> None:
    pass
