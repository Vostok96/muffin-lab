"""assign base culture parameters to all culture exams

Revision ID: 0012_culture_parameters_all_exams
Revises: 0011_andahuaylas_catalog_cleanup
Create Date: 2026-07-18
"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa


revision = "0012_culture_parameters_all_exams"
down_revision = "0011_andahuaylas_catalog_cleanup"
branch_labels = None
depends_on = None


CULTURE_EXAM_CODES = (
    "URINE_CULTURE",
    "COPROCULTIVO",
    "HEMOCULTIVO",
    "CULTIVO_SECRECIONES",
    "OTROS_CULTIVOS",
)


PARAMETERS = (
    (
        "CULTURE_RESULT",
        "RESULTADO DEL CULTIVO",
        1,
        True,
        "SELECT",
        [
            {"code": "NEGATIVO", "label": "NEGATIVO"},
            {"code": "POSITIVO", "label": "POSITIVO"},
            {"code": "NO_TRAJO_MUESTRA", "label": "NO TRAJO MUESTRA"},
            {"code": "MUESTRA_INADECUADA", "label": "MUESTRA INADECUADA"},
        ],
        "CULTIVO MANUAL",
    ),
    ("CULTURE_OBSERVATION", "OBSERVACIONES", 2, False, "LONG_TEXT", None, None),
    (
        "CULTURE_GRAM",
        "COLORACIÓN GRAM",
        3,
        False,
        "SELECT",
        [
            {"code": "COCOS_GRAM_POSITIVOS", "label": "COCOS GRAM POSITIVOS"},
            {"code": "BACILOS_GRAM_NEGATIVOS", "label": "BACILOS GRAM NEGATIVOS"},
            {"code": "LEVADURAS", "label": "LEVADURAS"},
        ],
        "TINCION GRAM",
    ),
    (
        "CULTURE_NITRITE",
        "PRUEBA DE NITRITO",
        4,
        False,
        "SELECT",
        [
            {"code": "NEGATIVO", "label": "NEGATIVO"},
            {"code": "POSITIVO", "label": "POSITIVO"},
            {"code": "NO_APLICA", "label": "NO APLICA"},
        ],
        "TIRA REACTIVA",
    ),
    (
        "CULTURE_COLONY_COUNT",
        "RECUENTO DE COLONIAS",
        5,
        False,
        "SELECT",
        [
            {"code": "001000", "label": "1,000 UFC/mL"},
            {"code": "002000", "label": "2,000 UFC/mL"},
            {"code": "003000", "label": "3,000 UFC/mL"},
            {"code": "004000", "label": "4,000 UFC/mL"},
            {"code": "005000", "label": "5,000 UFC/mL"},
            {"code": "006000", "label": "6,000 UFC/mL"},
            {"code": "007000", "label": "7,000 UFC/mL"},
            {"code": "008000", "label": "8,000 UFC/mL"},
            {"code": "009000", "label": "9,000 UFC/mL"},
            {"code": "010000", "label": "10,000 UFC/mL"},
            {"code": "020000", "label": "20,000 UFC/mL"},
            {"code": "030000", "label": "30,000 UFC/mL"},
            {"code": "040000", "label": "40,000 UFC/mL"},
            {"code": "050000", "label": "50,000 UFC/mL"},
            {"code": "060000", "label": "60,000 UFC/mL"},
            {"code": "070000", "label": "70,000 UFC/mL"},
            {"code": "080000", "label": "80,000 UFC/mL"},
            {"code": "090000", "label": "90,000 UFC/mL"},
            {"code": "100000", "label": "100,000 UFC/mL"},
        ],
        "RECUENTO",
    ),
)


def stable_id(entity: str, code: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"muffin:{entity}:{code}"))


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
            "(id, code, name, section, value_type, options_schema, methodology, is_active) "
            "VALUES (:id, :code, :name, 'MICROBIOLOGY', :value_type, :options_schema, :methodology, true) "
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


def upgrade() -> None:
    bind = op.get_bind()
    parameter_ids: dict[str, str] = {}
    for code, name, _display_order, _required, value_type, options_schema, methodology in PARAMETERS:
        parameter_ids[code] = upsert_parameter(
            bind,
            code=code,
            name=name,
            value_type=value_type,
            options_schema=options_schema,
            methodology=methodology,
        )

    antimicrobial_id = bind.execute(
        sa.text("SELECT id FROM parameter_definition WHERE code = 'CULTURE_ANTIMICROBIAL_ACTIVITY'")
    ).scalar()
    if antimicrobial_id:
        bind.execute(sa.text("UPDATE parameter_definition SET is_active = false WHERE id = :id"), {"id": antimicrobial_id})
        bind.execute(sa.text("DELETE FROM exam_parameter WHERE parameter_definition_id = :id"), {"id": antimicrobial_id})

    exam_ids = [
        row[0]
        for row in bind.execute(
            sa.text("SELECT id FROM exam WHERE code IN :codes").bindparams(
                sa.bindparam("codes", expanding=True)
            ),
            {"codes": CULTURE_EXAM_CODES},
        )
    ]
    if not exam_ids:
        return

    bind.execute(
        sa.text(
            "DELETE FROM exam_parameter "
            "WHERE exam_id IN :exam_ids "
            "AND display_order IN :display_orders "
            "AND parameter_definition_id NOT IN :parameter_ids"
        ).bindparams(
            sa.bindparam("exam_ids", expanding=True),
            sa.bindparam("display_orders", expanding=True),
            sa.bindparam("parameter_ids", expanding=True),
        ),
        {
            "exam_ids": exam_ids,
            "display_orders": [display_order for _code, _name, display_order, *_rest in PARAMETERS],
            "parameter_ids": list(parameter_ids.values()),
        },
    )

    for exam_id in exam_ids:
        for code, _name, display_order, required, _value_type, _options_schema, _methodology in PARAMETERS:
            bind.execute(
                sa.text(
                    "INSERT INTO exam_parameter "
                    "(exam_id, parameter_definition_id, display_order, external_code, is_required) "
                    "VALUES (:exam_id, :parameter_id, :display_order, :external_code, :required) "
                    "ON CONFLICT (exam_id, parameter_definition_id) DO UPDATE SET "
                    "display_order = EXCLUDED.display_order, "
                    "external_code = EXCLUDED.external_code, "
                    "is_required = EXCLUDED.is_required"
                ),
                {
                    "exam_id": exam_id,
                    "parameter_id": parameter_ids[code],
                    "display_order": display_order,
                    "external_code": f"BASE-{code}",
                    "required": required,
                },
            )


def downgrade() -> None:
    pass
