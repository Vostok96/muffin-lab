from decimal import Decimal
import re
from typing import Any
import unicodedata

from sqlalchemy import Sequence, select, text
from sqlalchemy.orm import Session

from app.models import AuditEvent, Role, User, WorkflowEvent


ROLE_SEEDS = {
    "ADMIN": "ADMINISTRADOR",
    "PROCESS_ADMIN": "ADMINISTRADOR DE PROCESOS",
    "PROCESSOR": "PROCESADOR DE LABORATORIO",
    "ENTRY": "REGISTRO DE ORDENES",
    "CONSULTANT": "USUARIO DE CONSULTAS",
    "COLLECTOR": "RECOLECTOR DE MUESTRAS",
    "CLINICIAN": "CONSULTA CLINICA",
}

order_number_sequence = Sequence("lab_order_number_seq")

ORIGIN_CARE_SETTINGS = {
    "CONSULTA_EXTERNA": "AMBULATORIO",
    "HOSPITAL": "INTERNADO_NO_UCI",
    "HOSPITALIZACION": "INTERNADO_NO_UCI",
    "UCI": "UCI",
    "EMERGENCIA": "URGENCIA",
    "URGENCIA": "URGENCIA",
}
SERVICE_CARE_SETTINGS = {
    "ALOJAMIENTO_CONJUNTO": "INTERNADO_NO_UCI",
    "HOSP_CIRUGIA": "INTERNADO_NO_UCI",
    "HOSP_GINECO_OBSTRETICIA": "INTERNADO_NO_UCI",
    "HOSP_MEDICINA": "INTERNADO_NO_UCI",
    "HOSP_NEO_I": "INTERNADO_NO_UCI",
    "HOSP_NEO_II": "INTERNADO_NO_UCI",
    "HOSP_PEDIATRIA": "INTERNADO_NO_UCI",
    "EMERGENCIA": "URGENCIA",
    "EMERGENCIA_ANTERIOR": "URGENCIA",
    "REPOSO_EMERGENCIA": "URGENCIA",
    "TRAUMA_SHOK": "URGENCIA",
}


def normalized_catalog_key(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(character for character in normalized if not unicodedata.combining(character))
    return re.sub(r"[^A-Z0-9]+", "_", ascii_value.upper()).strip("_")


def care_setting_evidence(code: str | None, name: str | None, mapping: dict[str, str]) -> str | None:
    evidence = {mapping[key] for value in (code, name) if (key := normalized_catalog_key(value)) in mapping}
    return evidence.pop() if len(evidence) == 1 else None


def derive_care_setting(
    origin_code: str | None,
    origin_name: str | None,
    service_code: str | None,
    service_name: str | None,
) -> str:
    origin = care_setting_evidence(origin_code, origin_name, ORIGIN_CARE_SETTINGS)
    service = care_setting_evidence(service_code, service_name, SERVICE_CARE_SETTINGS)
    if not origin and not service:
        return "DESCONOCIDO"
    if not origin or not service or origin == service:
        return origin or service or "DESCONOCIDO"
    if {origin, service} == {"INTERNADO_NO_UCI", "UCI"}:
        return "UCI"
    if {origin, service} == {"INTERNADO_NO_UCI", "CUIDADOS_INTERMEDIOS"}:
        return "CUIDADOS_INTERMEDIOS"
    return "DESCONOCIDO"


def record_audit(
    db: Session,
    *,
    actor_user_id: str | None,
    entity_type: str,
    entity_id: str | None,
    action: str,
    before_data: dict | None = None,
    after_data: dict | None = None,
    reason: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_data=before_data,
        after_data=after_data,
        reason=reason,
    )
    db.add(event)
    return event


def record_workflow_event(
    db: Session,
    *,
    order_item_id: str,
    event_type: str,
    performed_by: str | None,
    details: dict | None = None,
) -> WorkflowEvent:
    event = WorkflowEvent(
        order_item_id=order_item_id,
        event_type=event_type,
        performed_by=performed_by,
        details=details,
    )
    db.add(event)
    return event


def generate_order_number(db: Session, ordered_at) -> str:
    sequence_value = db.scalar(select(order_number_sequence.next_value()))
    return f"{ordered_at:%Y%m%d}-{sequence_value:06d}"


def parameter_definition_snapshot(parameter: Any) -> dict:
    def json_decimal(value: Decimal | None) -> str | None:
        return str(value) if value is not None else None

    return {
        "code": parameter.code,
        "name": parameter.name,
        "section": parameter.section,
        "value_type": parameter.value_type,
        "options_schema": parameter.options_schema,
        "methodology": parameter.methodology,
        "unit": parameter.unit,
        "reference_low": json_decimal(parameter.reference_low),
        "reference_high": json_decimal(parameter.reference_high),
        "reference_text": parameter.reference_text,
    }


def get_roles(db: Session, role_codes: list[str]) -> list[Role]:
    requested = {code.upper() for code in role_codes}
    roles = list(db.scalars(select(Role).where(Role.code.in_(requested))))
    found = {role.code for role in roles}
    missing = requested - found
    if missing:
        raise ValueError(f"Unknown roles: {', '.join(sorted(missing))}")
    return roles


def bootstrap_security_data(db: Session, username: str | None, password: str | None, given_name: str, family_name: str, password_hasher) -> None:
    # Uvicorn workers start concurrently. Serialize the check-and-insert bootstrap
    # transaction so a fresh database cannot receive duplicate role inserts.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext('muffin.bootstrap_security_data'))"))

    for code, name in ROLE_SEEDS.items():
        role = db.scalar(select(Role).where(Role.code == code))
        if role:
            role.name = name
        else:
            db.add(Role(code=code, name=name))
    db.flush()

    if username and password and not db.scalar(select(User).where(User.username == username)):
        admin_role = db.scalar(select(Role).where(Role.code == "ADMIN"))
        user = User(
            username=username,
            given_name=given_name,
            family_name=family_name,
            password_hash=password_hasher(password),
            roles=[admin_role],
        )
        db.add(user)
        db.flush()
        record_audit(
            db,
            actor_user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            action="BOOTSTRAP_ADMIN_CREATED",
            after_data={"username": user.username, "roles": ["ADMIN"]},
        )
    db.commit()


def autofill_antimicrobial_results(
    db: Session,
    *,
    isolate_id: str,
    ast_panel_id: str,
    default_method: str | None = None,
) -> None:
    from app.models import AntimicrobialResult, AstPanelAntibiotic

    existing = {
        row.antibiotic_id
        for row in db.scalars(
            select(AntimicrobialResult).where(AntimicrobialResult.isolate_id == isolate_id)
        )
    }
    panel_antibiotics = list(
        db.scalars(
            select(AstPanelAntibiotic)
            .where(AstPanelAntibiotic.ast_panel_id == ast_panel_id)
            .order_by(AstPanelAntibiotic.display_order)
        )
    )
    for entry in panel_antibiotics:
        if entry.antibiotic_id in existing:
            continue
        db.add(
            AntimicrobialResult(
                isolate_id=isolate_id,
                antibiotic_id=entry.antibiotic_id,
                interpretation=entry.default_interpretation,
                method=default_method or entry.default_method,
                is_reportable=True,
            )
        )
