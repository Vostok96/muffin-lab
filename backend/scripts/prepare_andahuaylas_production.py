"""Prepare the Hospital Sub Regional de Andahuaylas production dataset.

Run after migrations and the catalog seed. Passwords are read from environment
variables so deployment secrets are not stored in the repository.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import (
    Antibiotic,
    AntimicrobialResult,
    AstPanelAntibiotic,
    Clinician,
    Destination,
    Exam,
    ExamParameter,
    InstrumentMessage,
    Isolate,
    LaboratoryArea,
    LabOrder,
    Notification,
    OrderItem,
    Origin,
    ParameterDefinition,
    Patient,
    PrintJob,
    Result,
    ResultValue,
    Role,
    Service,
    SpecimenType,
    User,
    UserAreaPermission,
    WorkflowEvent,
)
from app.security import hash_password
from app.services import normalized_catalog_key, parameter_definition_snapshot, record_workflow_event


CLIENT_USERS = (
    {
        "username": "admin-hsr",
        "given_name": "Administrador",
        "family_name": "HSR Andahuaylas",
        "role_codes": ("ADMIN",),
        "password_env": "ANDAHUAYLAS_ADMIN_PASSWORD",
        "password_fallback_env": "BOOTSTRAP_ADMIN_PASSWORD",
        "can_validate": False,
    },
    {
        "username": "kpena",
        "given_name": "Katherine Mariely",
        "family_name": "Peña Vega",
        "role_codes": ("PROCESS_ADMIN",),
        "password_env": "ANDAHUAYLAS_KPENA_PASSWORD",
        "can_validate": True,
    },
    {
        "username": "rcalderon",
        "given_name": "Ruth N.",
        "family_name": "Calderon De La Cruz",
        "role_codes": ("PROCESS_ADMIN",),
        "password_env": "ANDAHUAYLAS_RCALDERON_PASSWORD",
        "can_validate": True,
    },
)

ANDAHUAYLAS_ORIGINS = (
    "CONSULTA EXTERNA",
    "EMERGENCIA",
    "HOSPITALIZACIÓN",
    "REFERIDO",
    "UCI",
)

ANDAHUAYLAS_SERVICES = (
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

CULTURE_EXAM_CODES = (
    "URINE_CULTURE",
    "COPROCULTIVO",
    "HEMOCULTIVO",
    "CULTIVO_SECRECIONES",
    "OTROS_CULTIVOS",
)

CULTURE_PARAMETER_RELATIONS = (
    ("CULTURE_RESULT", 1, True),
    ("CULTURE_OBSERVATION", 2, False),
    ("CULTURE_GRAM", 3, False),
    ("CULTURE_NITRITE", 4, False),
    ("CULTURE_COLONY_COUNT", 5, False),
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


def ensure_user(db, area: LaboratoryArea, user_spec: dict) -> User:
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
        permission = db.scalar(
            select(UserAreaPermission).where(
                UserAreaPermission.user_id == user.id,
                UserAreaPermission.laboratory_area_id == area.id,
            )
        )
        if not permission:
            permission = UserAreaPermission(
                user_id=user.id,
                laboratory_area_id=area.id,
                can_preliminary_validate=True,
                can_final_validate=True,
            )
            db.add(permission)
        else:
            permission.can_preliminary_validate = True
            permission.can_final_validate = True
    return user


def disable_development_users(db) -> None:
    disabled_hash = hash_password("disabled-development-account-2026")
    for username in ("dev-admin", "dev-entry", "dev-processor"):
        user = db.scalar(select(User).where(User.username == username))
        if user:
            user.is_active = False
            user.password_hash = disabled_hash


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


def ensure_institution_catalogs(db) -> None:
    official_origin_codes = {normalized_catalog_key(name) for name in ANDAHUAYLAS_ORIGINS}
    for origin_name in ANDAHUAYLAS_ORIGINS:
        ensure_catalog(
            db,
            Origin,
            normalized_catalog_key(origin_name),
            name=origin_name,
            is_active=True,
        )
    for origin in db.scalars(select(Origin).where(Origin.code.notin_(official_origin_codes))):
        origin.is_active = False

    official_service_codes = {normalized_catalog_key(name) for name in ANDAHUAYLAS_SERVICES}
    for service_name in ANDAHUAYLAS_SERVICES:
        ensure_catalog(
            db,
            Service,
            normalized_catalog_key(service_name),
            name=service_name,
            is_active=True,
        )
    for service in db.scalars(select(Service).where(Service.code.notin_(official_service_codes))):
        service.is_active = False

    on_call = ensure_catalog(
        db,
        Clinician,
        "MEDICO_TURNO",
        family_name="MEDICO",
        given_name="DE TURNO",
        email=None,
        is_active=True,
    )
    for clinician in db.scalars(select(Clinician).where(Clinician.id != on_call.id)):
        clinician.is_active = False


def ensure_culture_result_parameters(db) -> None:
    parameter_codes = [code for code, _order, _required in CULTURE_PARAMETER_RELATIONS]
    parameters = {
        parameter.code: parameter
        for parameter in db.scalars(
            select(ParameterDefinition).where(ParameterDefinition.code.in_(parameter_codes))
        )
    }
    exams = list(db.scalars(select(Exam).where(Exam.code.in_(CULTURE_EXAM_CODES))))
    for exam in exams:
        for parameter_code, display_order, is_required in CULTURE_PARAMETER_RELATIONS:
            parameter = parameters.get(parameter_code)
            if not parameter:
                continue
            relation = db.get(ExamParameter, (exam.id, parameter.id))
            if relation:
                relation.display_order = display_order
                relation.external_code = f"BASE-{parameter_code}"
                relation.is_required = is_required
            else:
                db.add(
                    ExamParameter(
                        exam_id=exam.id,
                        parameter_definition_id=parameter.id,
                        display_order=display_order,
                        external_code=f"BASE-{parameter_code}",
                        is_required=is_required,
                    )
                )


def normalize_microbiology_catalogs(db) -> None:
    area = db.scalar(select(LaboratoryArea).where(LaboratoryArea.code == "MICROBIOLOGY"))
    if not area:
        raise RuntimeError("MICROBIOLOGY area is missing. Run the seed first.")

    nitrite = db.scalar(select(ParameterDefinition).where(ParameterDefinition.code == "CULTURE_NITRITE"))
    if nitrite:
        nitrite.methodology = "TIRA REACTIVA"
        for relation in db.scalars(
            select(ExamParameter).where(ExamParameter.parameter_definition_id == nitrite.id)
        ):
            relation.is_required = False
        for value in db.scalars(select(ResultValue).where(ResultValue.parameter_definition_id == nitrite.id)):
            value.is_required = False
            value.parameter_snapshot = parameter_definition_snapshot(nitrite)

    gram = db.scalar(select(ParameterDefinition).where(ParameterDefinition.code == "CULTURE_GRAM"))
    if gram:
        gram.methodology = "TINCION GRAM"
        for value in db.scalars(select(ResultValue).where(ResultValue.parameter_definition_id == gram.id)):
            value.parameter_snapshot = parameter_definition_snapshot(gram)

    antimicrobial_activity = db.scalar(
        select(ParameterDefinition).where(ParameterDefinition.code == "CULTURE_ANTIMICROBIAL_ACTIVITY")
    )
    if antimicrobial_activity:
        antimicrobial_activity.is_active = False
        for relation in db.scalars(
            select(ExamParameter).where(ExamParameter.parameter_definition_id == antimicrobial_activity.id)
        ):
            db.delete(relation)

    ensure_culture_result_parameters(db)

    for antibiotic in db.scalars(select(Antibiotic)):
        antibiotic.name = antibiotic.name.upper()
    for link in db.scalars(select(AstPanelAntibiotic)):
        link.default_method = "DISCO"

    ensure_institution_catalogs(db)


def delete_result_graph(db, result: Result) -> None:
    for isolate in list(db.scalars(select(Isolate).where(Isolate.result_id == result.id))):
        for row in list(db.scalars(select(AntimicrobialResult).where(AntimicrobialResult.isolate_id == isolate.id))):
            db.delete(row)
        db.delete(isolate)
    for value in list(db.scalars(select(ResultValue).where(ResultValue.result_id == result.id))):
        db.delete(value)
    db.delete(result)


def delete_order_graph(db, order: LabOrder) -> None:
    for item in list(order.items):
        result = db.scalar(select(Result).where(Result.order_item_id == item.id))
        if result:
            delete_result_graph(db, result)
        for model in (WorkflowEvent, PrintJob, Notification, InstrumentMessage):
            for row in list(db.scalars(select(model).where(model.order_item_id == item.id))):
                db.delete(row)
        db.delete(item)
    db.delete(order)


def reset_demo_data(db) -> None:
    patient_ids = {patient.id for patient in db.scalars(select(Patient))}
    for order in list(db.scalars(select(LabOrder))):
        delete_order_graph(db, order)
    db.flush()
    for patient_id in patient_ids:
        remaining = db.scalar(select(func.count(LabOrder.id)).where(LabOrder.patient_id == patient_id))
        patient = db.get(Patient, patient_id)
        if patient and not remaining:
            db.delete(patient)


def ensure_example_order(db) -> None:
    if db.scalar(select(func.count(LabOrder.id))) > 0:
        return

    origin = ensure_catalog(db, Origin, "HOSPITALIZACION", name="HOSPITALIZACION", is_active=True)
    service = ensure_catalog(db, Service, "EMERGENCIA", name="EMERGENCIA", is_active=True)
    clinician = ensure_catalog(db, Clinician, "MEDICO_TURNO", family_name="MEDICO", given_name="DE TURNO", email=None, is_active=True)
    destination = ensure_catalog(db, Destination, "MICROBIOLOGY_BENCH", name="MESA DE MICROBIOLOGIA", is_active=True)
    exam = db.scalar(select(Exam).where(Exam.code == "URINE_CULTURE"))
    specimen_type = db.scalar(select(SpecimenType).where(SpecimenType.code == "URO_CHORRO_MEDIO"))
    if not exam or not specimen_type:
        raise RuntimeError("UROCULTIVO catalogs are missing. Run the seed first.")

    patient = Patient(
        medical_record_number="DEV-HC-0001",
        document_number="DEV-DOC-0001",
        family_name="FICTICIO",
        given_name="PACIENTE",
        birth_date=date(1990, 1, 15),
        sex="X",
    )
    db.add(patient)
    db.flush()

    collection_at = datetime(2026, 7, 17, 14, 0, tzinfo=timezone.utc)
    received_at = datetime(2026, 7, 17, 14, 30, tzinfo=timezone.utc)
    order = LabOrder(
        order_number="20260717-000001",
        ordered_at=datetime(2026, 7, 17, 13, 45, tzinfo=timezone.utc),
        patient_id=patient.id,
        origin_id=origin.id,
        service_id=service.id,
        clinician_id=clinician.id,
        clinical_notes="ORDEN FICTICIA DE EJEMPLO PARA PRUEBAS INICIALES.",
        status="REGISTERED",
    )
    db.add(order)
    db.flush()

    item = OrderItem(
        lab_order_id=order.id,
        item_number=1,
        exam_id=exam.id,
        specimen_type_id=specimen_type.id,
        barcode="20260717000001-01-UC",
        collection_at=collection_at,
        received_at=received_at,
        destination_id=destination.id,
        specimen_notes="MUESTRA FICTICIA DE EJEMPLO.",
        location="MESA DE MICROBIOLOGIA",
        status="RECEIVED",
    )
    db.add(item)
    db.flush()
    for event_type in ("REGISTERED", "COLLECTED", "RECEIVED"):
        record_workflow_event(
            db,
            order_item_id=item.id,
            event_type=event_type,
            performed_by=None,
            details={"production_example": True},
        )


def main() -> None:
    with SessionLocal() as db:
        normalize_microbiology_catalogs(db)
        area = db.scalar(select(LaboratoryArea).where(LaboratoryArea.code == "MICROBIOLOGY"))
        for user_spec in CLIENT_USERS:
            ensure_user(db, area, user_spec)
        disable_development_users(db)
        if os.getenv("ANDAHUAYLAS_RESET_DEMO_DATA") == "1":
            reset_demo_data(db)
        ensure_example_order(db)
        db.commit()
    print("Andahuaylas production preparation completed.")


if __name__ == "__main__":
    main()
