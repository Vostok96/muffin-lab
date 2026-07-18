"""restrict Andahuaylas active catalogs to official values

Revision ID: 0011_andahuaylas_catalog_cleanup
Revises: 0010_andahuaylas_catalogs
Create Date: 2026-07-18
"""

from __future__ import annotations

import re
import unicodedata

from alembic import op
import sqlalchemy as sa


revision = "0011_andahuaylas_catalog_cleanup"
down_revision = "0010_andahuaylas_catalogs"
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


def restrict_catalog(table: str, names: tuple[str, ...]) -> None:
    codes = [catalog_code(name) for name in names]
    statement = sa.text(
        f"UPDATE {table} SET is_active = (code IN :codes), updated_at = now()"
    ).bindparams(sa.bindparam("codes", expanding=True))
    op.get_bind().execute(
        statement,
        {"codes": codes},
    )


def upgrade() -> None:
    restrict_catalog("origin", ORIGINS)
    restrict_catalog("service", SERVICES)
    op.get_bind().execute(
        sa.text("UPDATE clinician SET is_active = (code = 'MEDICO_TURNO'), updated_at = now()")
    )


def downgrade() -> None:
    pass
