"""load Andahuaylas institutional catalogs

Revision ID: 0010_andahuaylas_catalogs
Revises: 0009_app_settings
Create Date: 2026-07-18
"""

from __future__ import annotations

import re
import unicodedata
import uuid

from alembic import op
import sqlalchemy as sa


revision = "0010_andahuaylas_catalogs"
down_revision = "0009_app_settings"
branch_labels = None
depends_on = None


ORIGINS = (
    "CONSULTA EXTERNA",
    "EMERGENCIA",
    "HOSPITALIZACIÓN",
    "REFERIDO",
    "UCI",
)

SERVICES = (
    "ALOJAMIENTO CONJUNTO",
    "CARDIOLOGIA",
    "CENTRO OBSTETRICO",
    "CIRUGIA GENERAL",
    "CIRUGIA PEDIATRICA",
    "DERMATOLOGIA",
    "ENDOCRINOLOGIA",
    "GASTROENTEROLOGIA",
    "GINECOLOGIA",
    "HOSP. CIRUGIA",
    "HOSP. GINECO-OBSTETRICIA",
    "HOSP. MEDICINA",
    "HOSP. NEO I",
    "HOSP. NEO II",
    "HOSP. PEDIATRIA",
    "MEDICINA FISICA Y REHABILITACION",
    "MEDICINA INTERNA",
    "NEUMOLOGIA",
    "NEUROCIRUGIA",
    "NEUROLOGIA",
    "OBSTETRICIA",
    "ODONTOLOGIA",
    "ODONTO-PEDIATRIA",
    "OFTALMOLOGIA",
    "ONCOLOGIA",
    "OTORRINOLARINGOLOGIA",
    "PAGANTES",
    "PEDIATRIA",
    "PROGRAMA DE ETS/VIH-SIDA",
    "PROGRAMA DE TUBERCULOSIS",
    "PSICOLOGIA",
    "PSIQUIATRIA",
    "REFERENCIA",
    "REPOSO EMERGENCIA",
    "REUMATOLOGIA",
    "SALA DE OPERACIONES",
    "SALUD MENTAL",
    "TOPICO CIRUGIA",
    "TOPICO GINECO-OBSTETRICIA",
    "TOPICO MEDICINA",
    "TOPICO PEDIATRIA",
    "TRAUMA SHOK",
    "TRAUMATOLOGIA",
    "UCI",
    "UCIN",
    "UROLOGIA",
)


def catalog_code(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_value = "".join(character for character in normalized if not unicodedata.combining(character))
    return re.sub(r"[^A-Z0-9]+", "_", ascii_value.upper()).strip("_")


def stable_id(entity: str, code: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"muffin:{entity}:{code}"))


def upsert_catalog(table: str, entity: str, names: tuple[str, ...]) -> None:
    bind = op.get_bind()
    statement = sa.text(
        f"INSERT INTO {table} (id, code, name, is_active, created_at, updated_at) "
        "VALUES (:id, :code, :name, true, now(), now()) "
        "ON CONFLICT (code) DO UPDATE SET "
        "name = EXCLUDED.name, is_active = true, updated_at = now()"
    )
    for name in names:
        code = catalog_code(name)
        bind.execute(statement, {"id": stable_id(entity, code), "code": code, "name": name})


def upgrade() -> None:
    upsert_catalog("origin", "origin", ORIGINS)
    upsert_catalog("service", "service", SERVICES)
    bind = op.get_bind()
    clinician_id = stable_id("clinician", "MEDICO_TURNO")
    bind.execute(
        sa.text(
            "INSERT INTO clinician (id, code, family_name, given_name, email, is_active, created_at, updated_at) "
            "VALUES (:id, 'MEDICO_TURNO', 'MEDICO', 'DE TURNO', NULL, true, now(), now()) "
            "ON CONFLICT (code) DO UPDATE SET "
            "family_name = EXCLUDED.family_name, "
            "given_name = EXCLUDED.given_name, "
            "email = EXCLUDED.email, "
            "is_active = true, "
            "updated_at = now() "
            "RETURNING id"
        ),
        {"id": clinician_id},
    ).scalar_one()
    bind.execute(
        sa.text("UPDATE clinician SET is_active = false, updated_at = now() WHERE code <> 'MEDICO_TURNO'")
    )


def downgrade() -> None:
    # Do not delete or deactivate institutional catalogs on downgrade because
    # production orders may already reference them.
    pass
