"""Development-only seed data for local MUFFIN environments."""

import os
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.database import SessionLocal
from app.models import (
    Antibiotic,
    AntimicrobialResult,
    AstPanel,
    AstPanelAntibiotic,
    Clinician,
    ColonyCountOption,
    Container,
    DefinedComment,
    Destination,
    Exam,
    ExamParameter,
    ExamSpecimenType,
    InstrumentMessage,
    Isolate,
    LaboratoryArea,
    LabOrder,
    Notification,
    OrderItem,
    Organism,
    Origin,
    Patient,
    ParameterDefinition,
    PrintJob,
    Result,
    ResultValue,
    Role,
    Service,
    SpecimenType,
    User,
    UserAreaPermission,
)
from app.security import hash_password
from app.services import bootstrap_security_data, parameter_definition_snapshot, record_audit, record_workflow_event


DEVELOPMENT_USERS = (
    ("dev-admin", "ADMINISTRADOR", "DESARROLLO", ("ADMIN",)),
    ("dev-entry", "REGISTRO", "DESARROLLO", ("ENTRY",)),
    ("dev-processor", "PROCESADOR", "DESARROLLO", ("PROCESSOR",)),
)

QUICK_LOGIN_USER = ("admin", "ADMINISTRADOR", "LOCAL", ("ADMIN",), "admin")

DEVELOPMENT_AREAS = (
    ("MICROBIOLOGY", "MICROBIOLOGIA", "MICROBIOLOGY"),
    ("RECEPTION", "RECEPCION DE MUESTRAS", "MICROBIOLOGY"),
)

EXAM_SPECIMEN_HIERARCHY = (
    (
        "URINE_CULTURE",
        "UROCULTIVO",
        "UC",
        (
            ("URO_CHORRO_MEDIO", "CHORRO MEDIO", ()),
            ("URO_SONDA_FOLEY", "SONDA VESICAL (FOLEY)", ()),
            ("URO_PUNCION_SUPRAPUBICA", "PUNCIÓN SUPRAPÚBICA", ()),
            ("URO_BOLSA_PEDIATRICA", "BOLSA RECOLECTORA (PEDIATRÍA)", ()),
            ("URO_CATETERISMO_INTERMITENTE", "CATETERISMO VESICAL INTERMITENTE", ()),
            ("URO_NEFROSTOMIA", "ORINA DE NEFROSTOMÍA", ()),
            ("URO_UROSTOMIA", "ORINA DE UROSTOMÍA / CONDUCTO ILEAL", ()),
        ),
    ),
    (
        "COPROCULTIVO",
        "COPROCULTIVO",
        "COP",
        (
            ("COP_HECES_ESPONTANEA", "HECES (EVACUACIÓN ESPONTÁNEA)", ()),
            ("COP_HISOPADO_RECTAL", "HISOPADO RECTAL", ()),
        ),
    ),
    (
        "HEMOCULTIVO",
        "HEMOCULTIVO",
        "HEM",
        (
            ("HEM_SANGRE_PERIFERICA", "SANGRE VENOSA PERIFERICA", ()),
            ("HEM_SANGRE_CVC", "SANGRE POR CATÉTER VENOSO CENTRAL (CVC)", ()),
            ("HEM_SANGRE_ARTERIAL", "SANGRE ARTERIAL", ()),
            ("HEM_SANGRE_PICC", "SANGRE POR CATÉTER PICC", ()),
            ("HEM_SANGRE_RESERVORIO", "SANGRE POR RESERVORIO IMPLANTABLE", ()),
        ),
    ),
    (
        "CULTIVO_SECRECIONES",
        "CULTIVO DE SECRECIONES",
        "SEC",
        (
            (
                "SEC_LESIONES_SUPERFICIALES",
                "SECRECIONES Y LESIONES SUPERFICIALES",
                (
                    ("SEC_HERIDA_QUIRURGICA", "HERIDA QUIRÚRGICA"),
                    ("SEC_HERIDA_TRAUMATICA", "HERIDA TRAUMATICA"),
                    ("SEC_ULCERA", "ÚLCERA"),
                    ("SEC_OCULAR", "SECRECIÓN OCULAR"),
                    ("SEC_OTICA", "SECRECIÓN ÓTICA"),
                    ("SEC_MAMARIA", "SECRECIÓN MAMARIA"),
                    ("SEC_PIE_DIABETICO", "LESIÓN DE PIE DIABÉTICO"),
                    ("SEC_QUEMADURA", "QUEMADURA"),
                ),
            ),
            (
                "SEC_COLECCIONES_PROFUNDAS",
                "COLECCIONES PROFUNDAS",
                (
                    ("SEC_ABSCESO_CERRADO", "SECRECIÓN DE ABSCESO CERRADO"),
                    ("SEC_FISTULA", "FÍSTULA"),
                ),
            ),
            (
                "SEC_TRACTO_RESPIRATORIO",
                "TRACTO RESPIRATORIO",
                (
                    ("SEC_ESPUTO", "ESPUTO"),
                    ("SEC_SECRECION_BRONQUIAL", "SECRECIÓN BRONQUIAL"),
                    ("SEC_ASPIRADO_BRONQUIAL", "ASPIRADO BRONQUIAL"),
                    ("SEC_CEPILLADO_BRONQUIAL", "CEPILLADO BRONQUIAL"),
                    ("SEC_ASPIRADO_TRAQUEAL", "ASPIRADO TRAQUEAL"),
                    ("SEC_LAVADO_BRONCOALVEOLAR", "LAVADO BRONCOALVEOLAR"),
                    ("SEC_HISOPADO_FARINGEO", "HISOPADO / SECRECIÓN FARÍNGEA"),
                    ("SEC_HISOPADO_NASAL", "HISOPADO NASAL"),
                    ("SEC_HISOPADO_NASOFARINGEO", "HISOPADO NASOFARÍNGEO"),
                    ("SEC_ASPIRADO_NASOFARINGEO", "ASPIRADO NASOFARÍNGEO"),
                ),
            ),
            (
                "SEC_TRACTO_GENITOURINARIO",
                "TRACTO GENITOURINARIO",
                (
                    ("SEC_VAGINAL", "SECRECIÓN VAGINAL"),
                    ("SEC_ENDOCERVICAL", "EXUDADO ENDOCERVICAL"),
                    ("SEC_URETRAL", "SECRECIÓN URETRAL"),
                    ("SEC_LOQUIOS", "LOQUIOS"),
                ),
            ),
            (
                "SEC_DISPOSITIVOS_MEDICOS",
                "DISPOSITIVOS MÉDICOS",
                (
                    ("SEC_PUNTA_CVC", "PUNTA DE CATÉTER VENOSO CENTRAL (CVC)"),
                    ("SEC_PUNTA_PERIFERICO", "PUNTA DE CATÉTER PERIFÉRICO"),
                    ("SEC_PUNTA_UMBILICAL", "PUNTA DE CATÉTER UMBILICAL"),
                    ("SEC_TUBO_ENDOTRAQUEAL", "TUBO ENDOTRAQUEAL"),
                ),
            ),
        ),
    ),
    (
        "OTROS_CULTIVOS",
        "OTROS CULTIVOS / TÉRMINOS GENERALES",
        "OTR",
        (
            (
                "OTR_LIQUIDOS_ESTERILES",
                "LÍQUIDOS BIOLÓGICOS ESTÉRILES",
                (
                    ("OTR_LCR", "LÍQUIDO CEFALORRAQUÍDEO (LCR)"),
                    ("OTR_LIQUIDO_ASCITICO", "LÍQUIDO ASCÍTICO (PERITONEAL)"),
                    ("OTR_LIQUIDO_PLEURAL", "LÍQUIDO PLEURAL"),
                    ("OTR_LIQUIDO_SINOVIAL", "LÍQUIDO SINOVIAL (ARTICULAR)"),
                    ("OTR_LIQUIDO_PERICARDICO", "LÍQUIDO PERICÁRDICO"),
                    ("OTR_LIQUIDO_AMNIOTICO", "LÍQUIDO AMNIÓTICO"),
                    ("OTR_BILIS", "BILIS"),
                    ("OTR_DIALISIS_PERITONEAL", "LÍQUIDO DE DIÁLISIS PERITONEAL"),
                    ("OTR_HUMOR_VITREO", "HUMOR VÍTREO"),
                    ("OTR_HUMOR_ACUOSO", "HUMOR ACUOSO"),
                ),
            ),
            (
                "OTR_PIEL_ANEXOS",
                "PIEL Y ANEXOS (MICOLOGÍA)",
                (
                    ("OTR_ESCAMAS_PIEL", "ESCAMAS DE PIEL"),
                    ("OTR_UNAS", "UÑAS"),
                    ("OTR_CABELLOS", "CABELLOS"),
                ),
            ),
            (
                "OTR_TEJIDOS_HUESOS",
                "TEJIDOS Y HUESOS",
                (
                    ("OTR_BIOPSIA_TEJIDO", "BIOPSIA DE TEJIDO BLANDO"),
                    ("OTR_FRAGMENTO_OSEO", "FRAGMENTO ÓSEO"),
                    ("OTR_ORGANO_INTERNO", "ÓRGANO INTERNO"),
                    ("OTR_MEDULA_OSEA", "MÉDULA ÓSEA"),
                    ("OTR_MATERIAL_PROTESICO", "MATERIAL PROTÉSICO / IMPLANTE"),
                ),
            ),
            (
                "OTR_REPRODUCTIVO_MASCULINO",
                "TRACTO REPRODUCTIVO MASCULINO",
                (
                    ("OTR_LIQUIDO_SEMINAL", "LÍQUIDO SEMINAL (ESPERMATOCULTIVO)"),
                    ("OTR_SECRECION_PROSTATICA", "SECRECIÓN PROSTÁTICA"),
                ),
            ),
        ),
    ),
)


def get_development_password() -> str:
    password = os.getenv("DEV_SEED_PASSWORD", "")
    if len(password) < 12:
        raise RuntimeError("DEV_SEED_PASSWORD must contain at least 12 characters.")
    return password


def get_or_create_catalog(db, model: type, code: str, **values: Any) -> Any:
    entity = db.scalar(select(model).where(model.code == code))
    if entity:
        for field, value in values.items():
            setattr(entity, field, value)
        return entity
    entity = model(code=code, **values)
    db.add(entity)
    db.flush()
    record_audit(
        db,
        actor_user_id=None,
        entity_type=model.__tablename__,
        entity_id=entity.id,
        action="DEVELOPMENT_SEED",
        after_data={"code": entity.code},
    )
    return entity


def seed() -> None:
    password = get_development_password()
    with SessionLocal() as db:
        bootstrap_security_data(db, None, None, "", "", hash_password)

        areas: dict[str, LaboratoryArea] = {}
        for code, name, section in DEVELOPMENT_AREAS:
            area = db.scalar(select(LaboratoryArea).where(LaboratoryArea.code == code))
            if not area:
                area = LaboratoryArea(code=code, name=name, section=section)
                db.add(area)
                db.flush()
                record_audit(
                    db,
                    actor_user_id=None,
                    entity_type="laboratory_area",
                    entity_id=area.id,
                    action="DEVELOPMENT_SEED",
                    after_data={"code": area.code},
                )
            else:
                area.name = name
                area.section = section
            areas[code] = area

        origin = get_or_create_catalog(db, Origin, "HOSPITALIZACION", name="HOSPITALIZACION")
        service = get_or_create_catalog(db, Service, "EMERGENCIA", name="EMERGENCIA")
        clinician = get_or_create_catalog(
            db,
            Clinician,
            "DEV-CLINICIAN",
            family_name="MEDICO",
            given_name="DE TURNO",
            email="clinician@example.invalid",
        )
        destination = get_or_create_catalog(db, Destination, "MICROBIOLOGY_BENCH", name="MESA DE MICROBIOLOGIA")
        container = get_or_create_catalog(
            db,
            Container,
            "CONTENEDOR_PROTOCOLO",
            name="CONTENEDOR SEGUN PROTOCOLO",
            is_active=True,
        )
        exams: dict[str, Exam] = {}
        specimen_types: dict[str, SpecimenType] = {}
        for exam_code, exam_name, barcode_suffix, level_1_options in EXAM_SPECIMEN_HIERARCHY:
            exam_entity = get_or_create_catalog(
                db,
                Exam,
                exam_code,
                name=exam_name,
                external_code=f"MUFFIN-{exam_code}",
                barcode_suffix=barcode_suffix,
                laboratory_area_id=areas["MICROBIOLOGY"].id,
                sends_to_analyzer=False,
                requires_colony_count=True,
                is_active=True,
            )
            exams[exam_code] = exam_entity
            for level_1_code, level_1_name, children in level_1_options:
                level_1 = get_or_create_catalog(
                    db,
                    SpecimenType,
                    level_1_code,
                    name=level_1_name,
                    container_id=container.id,
                    parent_id=None,
                    is_selectable=not children,
                    is_active=True,
                )
                specimen_types[level_1_code] = level_1
                if not db.get(ExamSpecimenType, (exam_entity.id, level_1.id)):
                    db.add(ExamSpecimenType(exam_id=exam_entity.id, specimen_type_id=level_1.id))
                for level_2_code, level_2_name in children:
                    level_2 = get_or_create_catalog(
                        db,
                        SpecimenType,
                        level_2_code,
                        name=level_2_name,
                        container_id=container.id,
                        parent_id=level_1.id,
                        is_selectable=True,
                        is_active=True,
                    )
                    specimen_types[level_2_code] = level_2
                    if not db.get(ExamSpecimenType, (exam_entity.id, level_2.id)):
                        db.add(ExamSpecimenType(exam_id=exam_entity.id, specimen_type_id=level_2.id))

        exam = exams["URINE_CULTURE"]
        specimen_type = specimen_types["URO_CHORRO_MEDIO"]
        legacy_specimen = db.scalar(select(SpecimenType).where(SpecimenType.code == "URINE"))
        if legacy_specimen:
            legacy_specimen.is_active = False
            legacy_link = db.get(ExamSpecimenType, (exam.id, legacy_specimen.id))
            if legacy_link:
                db.delete(legacy_link)
        result_parameter_specs = [
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
                "CULTIVO",
                "NEGATIVO",
            ),
            ("CULTURE_OBSERVATION", "OBSERVACIONES", 2, False, "LONG_TEXT", None, None, None),
            (
                "CULTURE_GRAM",
                "COLORACIÓN GRAM",
                3,
                False,
                "SELECT",
                [
                    {"code": "NEGATIVO", "label": "NEGATIVO"},
                    {"code": "POSITIVO", "label": "POSITIVO"},
                    {"code": "NO_APLICA", "label": "NO APLICA"},
                ],
                "GRAM",
                None,
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
                "NITRITO",
                None,
            ),
            (
                "CULTURE_COLONY_COUNT",
                "RECUENTO DE COLONIAS",
                5,
                False,
                "SELECT",
                [
                    {"code": "ESCASO", "label": "ESCASO"},
                    {"code": "MODERADO", "label": "MODERADO"},
                    {"code": "ABUNDANTE", "label": "ABUNDANTE"},
                    {"code": "NO_APLICA", "label": "NO APLICA"},
                ],
                "RECUENTO",
                None,
            ),
            (
                "CULTURE_ANTIMICROBIAL_ACTIVITY",
                "DETECCIÓN DE ACTIVIDAD ANTIMICROBIANA",
                6,
                False,
                "SELECT",
                [
                    {"code": "NEGATIVO", "label": "NEGATIVO"},
                    {"code": "POSITIVO", "label": "POSITIVO"},
                    {"code": "NO_APLICA", "label": "NO APLICA"},
                ],
                "ANTIMICROBIANA",
                None,
            ),
        ]
        result_parameters: dict[str, ParameterDefinition] = {}
        for code, name, display_order, is_required, value_type, options_schema, methodology, seed_value in result_parameter_specs:
            parameter_values: dict[str, Any] = {
                "name": name,
                "section": "MICROBIOLOGY",
                "value_type": value_type,
            }
            if options_schema is not None:
                parameter_values["options_schema"] = options_schema
            if methodology is not None:
                parameter_values["methodology"] = methodology
            parameter = get_or_create_catalog(db, ParameterDefinition, code, **parameter_values)
            result_parameters[code] = parameter
            if not db.get(ExamParameter, (exam.id, parameter.id)):
                db.add(
                    ExamParameter(
                        exam_id=exam.id,
                        parameter_definition_id=parameter.id,
                        display_order=display_order,
                        external_code=f"DEV-{code}",
                        is_required=is_required,
                    )
                )
                record_audit(
                    db,
                    actor_user_id=None,
                    entity_type="exam_parameter",
                    entity_id=exam.id,
                    action="DEVELOPMENT_SEED",
                    after_data={
                        "exam_id": exam.id,
                        "parameter_definition_id": parameter.id,
                        "display_order": display_order,
                        "is_required": is_required,
                    },
                )

        patient = db.scalar(select(Patient).where(Patient.medical_record_number == "DEV-HC-0001"))
        if not patient:
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
            record_audit(
                db,
                actor_user_id=None,
                entity_type="patient",
                entity_id=patient.id,
                action="DEVELOPMENT_SEED",
                after_data={"medical_record_number": patient.medical_record_number},
            )
        else:
            patient.family_name = "FICTICIO"
            patient.given_name = "PACIENTE"

        order = db.scalar(select(LabOrder).where(LabOrder.order_number == "DEV-ORDER-0001"))
        if not order:
            collection_at = datetime(2026, 1, 15, 14, 0, tzinfo=timezone.utc)
            received_at = datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc)
            order = LabOrder(
                order_number="DEV-ORDER-0001",
                ordered_at=datetime(2026, 1, 15, 13, 45, tzinfo=timezone.utc),
                patient_id=patient.id,
                origin_id=origin.id,
                service_id=service.id,
                clinician_id=clinician.id,
                clinical_notes="ORDEN ESTRICTAMENTE FICTICIA PARA DESARROLLO LOCAL.",
                status="REGISTERED",
            )
            db.add(order)
            db.flush()
            item = OrderItem(
                lab_order_id=order.id,
                item_number=1,
                exam_id=exam.id,
                specimen_type_id=specimen_type.id,
                barcode="DEV-ORDER-0001-01-UC",
                collection_at=collection_at,
                received_at=received_at,
                destination_id=destination.id,
                specimen_notes="MUESTRA FICTICIA PARA DESARROLLO LOCAL.",
                location="MESA DE DESARROLLO LOCAL",
                status="RECEIVED",
            )
            db.add(item)
            db.flush()
            record_workflow_event(
                db,
                order_item_id=item.id,
                event_type="REGISTERED",
                performed_by=None,
                details={"development_seed": True},
            )
            record_workflow_event(
                db,
                order_item_id=item.id,
                event_type="COLLECTED",
                performed_by=None,
                details={"collection_at": collection_at.isoformat(), "development_seed": True},
            )
            record_workflow_event(
                db,
                order_item_id=item.id,
                event_type="RECEIVED",
                performed_by=None,
                details={"received_at": received_at.isoformat(), "destination_id": destination.id, "development_seed": True},
            )
            record_audit(
                db,
                actor_user_id=None,
                entity_type="lab_order",
                entity_id=order.id,
                action="DEVELOPMENT_SEED",
                after_data={"order_number": order.order_number, "patient_id": patient.id},
            )
        else:
            order.origin_id = origin.id
            order.service_id = service.id
            order.clinician_id = clinician.id
            order.clinical_notes = "ORDEN ESTRICTAMENTE FICTICIA PARA DESARROLLO LOCAL."

        item = db.scalar(select(OrderItem).where(OrderItem.barcode == "DEV-ORDER-0001-01-UC"))
        if item:
            item.exam_id = exam.id
            item.specimen_type_id = specimen_type.id
            item.specimen_notes = "MUESTRA FICTICIA PARA DESARROLLO LOCAL."
            item.location = "MESA DE DESARROLLO LOCAL"
        if item:
            result = db.scalar(select(Result).where(Result.order_item_id == item.id))
            created_result = False
            if not result:
                result = Result(order_item_id=item.id, status="RESULT_SAVED", saved_at=datetime.now(timezone.utc))
                db.add(result)
                db.flush()
                created_result = True

            existing_values = {value.parameter_definition_id: value for value in result.values}
            for code, _, display_order, is_required, value_type, options_schema, methodology, seed_value in result_parameter_specs:
                parameter = result_parameters[code]
                value = existing_values.get(parameter.id)
                if not value:
                    value = ResultValue(
                        result_id=result.id,
                        parameter_definition_id=parameter.id,
                        display_order=display_order,
                        is_required=is_required,
                        parameter_snapshot=parameter_definition_snapshot(parameter),
                    )
                    result.values.append(value)
                value.display_order = display_order
                value.is_required = is_required
                value.parameter_snapshot = parameter_definition_snapshot(parameter)
                if code == "CULTURE_RESULT":
                    value.value_text = seed_value
                    value.value_code = seed_value
                    value.observed_at = item.received_at
                else:
                    value.value_text = None
                    value.value_code = None
                    value.observed_at = None

            item.status = "RESULT_SAVED"
            if created_result:
                record_workflow_event(
                    db,
                    order_item_id=item.id,
                    event_type="RESULT_SAVED",
                    performed_by=None,
                    details={"development_seed": True, "status": result.status},
                )
                record_audit(
                    db,
                    actor_user_id=None,
                    entity_type="result",
                    entity_id=result.id,
                    action="DEVELOPMENT_SEED",
                    after_data={"order_item_id": item.id, "status": result.status},
                )

        # --- Microbiology advanced seed (Phase 5) ---

        organism = get_or_create_catalog(db, Organism, "ECOLI", name="ESCHERICHIA COLI")
        get_or_create_catalog(db, Organism, "KPN", name="KLEBSIELLA PNEUMONIAE")
        get_or_create_catalog(db, Organism, "PAE", name="PSEUDOMONAS AERUGINOSA")

        colony_count_options = [
            ("001000", "1,000 UFC/mL - ESCASO"),
            ("002000", "2,000 UFC/mL - ESCASO"),
            ("003000", "3,000 UFC/mL - ESCASO"),
            ("004000", "4,000 UFC/mL - ESCASO"),
            ("005000", "5,000 UFC/mL - ESCASO"),
            ("006000", "6,000 UFC/mL - ESCASO"),
            ("007000", "7,000 UFC/mL - ESCASO"),
            ("008000", "8,000 UFC/mL - ESCASO"),
            ("009000", "9,000 UFC/mL - ESCASO"),
            ("010000", "10,000 UFC/mL - MODERADO"),
            ("020000", "20,000 UFC/mL - MODERADO"),
            ("030000", "30,000 UFC/mL - MODERADO"),
            ("040000", "40,000 UFC/mL - MODERADO"),
            ("050000", "50,000 UFC/mL - MODERADO"),
            ("060000", "60,000 UFC/mL - MODERADO"),
            ("070000", "70,000 UFC/mL - MODERADO"),
            ("080000", "80,000 UFC/mL - MODERADO"),
            ("090000", "90,000 UFC/mL - MODERADO"),
            ("100000", "100,000 UFC/mL - ABUNDANTE"),
            ("100001", ">100,000 UFC/mL - ABUNDANTE"),
        ]
        colony_count_option_entities = {
            code: get_or_create_catalog(db, ColonyCountOption, code, name=name)
            for code, name in colony_count_options
        }
        for legacy_code in ("RARE", "MODERATE", "ABUNDANT"):
            legacy_option = db.scalar(select(ColonyCountOption).where(ColonyCountOption.code == legacy_code))
            if legacy_option:
                legacy_option.is_active = False

        get_or_create_catalog(db, DefinedComment, "MIXED_FLORA", text="LA MUESTRA PRESENTA FLORA MIXTA.")
        get_or_create_catalog(db, DefinedComment, "CONTAMINATED", text="POSIBLE CONTAMINACION DE LA MUESTRA.")

        amk = get_or_create_catalog(db, Antibiotic, "AMK", name="AMIKACINA")
        amc = get_or_create_catalog(db, Antibiotic, "AMC", name="AMOXICILINA/ACIDO CLAVULANICO")
        ctx = get_or_create_catalog(db, Antibiotic, "CTX", name="CEFOTAXIMA")
        cip = get_or_create_catalog(db, Antibiotic, "CIP", name="CIPROFLOXACINO")
        nit = get_or_create_catalog(db, Antibiotic, "NIT", name="NITROFURANTOINA")

        panel = get_or_create_catalog(
            db,
            AstPanel,
            "GN_URINE",
            name="PANEL DE ORINA PARA GRAMNEGATIVOS",
            is_active=False,
        )

        antibiotics_in_panel = [
            (amk, 1, "MICRODILUCION"),
            (amc, 2, "MICRODILUCION"),
            (ctx, 3, "MICRODILUCION"),
            (cip, 4, "MICRODILUCION"),
            (nit, 5, "MICRODILUCION"),
        ]
        for ant, order, method in antibiotics_in_panel:
            if not db.get(AstPanelAntibiotic, (panel.id, ant.id)):
                db.add(AstPanelAntibiotic(
                    ast_panel_id=panel.id,
                    antibiotic_id=ant.id,
                    display_order=order,
                    default_method=method,
                ))
                record_audit(
                    db,
                    actor_user_id=None,
                    entity_type="ast_panel_antibiotic",
                    entity_id=panel.id,
                    action="DEVELOPMENT_SEED",
                    after_data={"antibiotic_id": ant.id, "display_order": order},
                )

        result = db.scalar(select(Result).where(Result.order_item_id == item.id))
        if result and not db.scalar(select(Isolate).where(Isolate.result_id == result.id)):
            isolate = Isolate(
                result_id=result.id,
                organism_id=organism.id,
                colony_count_option_id=colony_count_option_entities["050000"].id,
                phenotype="FERMENTADOR DE LACTOSA, COLONIAS MUCOIDES",
                comment="AISLADO COMPATIBLE CON EL CUADRO CLINICO.",
                ast_panel_id=panel.id,
            )
            db.add(isolate)
            db.flush()
            record_audit(
                db,
                actor_user_id=None,
                entity_type="isolate",
                entity_id=isolate.id,
                action="DEVELOPMENT_SEED",
                after_data={"result_id": result.id, "organism_id": organism.id},
            )
            ast_data = [
                (amk, "<=2", "S", "MICRODILUCION"),
                (amc, "8/4", "S", "MICRODILUCION"),
                (ctx, "<=0.25", "S", "MICRODILUCION"),
                (cip, "<=0.06", "S", "MICRODILUCION"),
                (nit, "<=16", "S", "MICRODILUCION"),
            ]
            for ant, mic, interp, meth in ast_data:
                ar = AntimicrobialResult(
                    isolate_id=isolate.id,
                    antibiotic_id=ant.id,
                    mic_value=mic,
                    interpretation=interp,
                    method=meth,
                    is_reportable=True,
                )
                db.add(ar)
                record_audit(
                    db,
                    actor_user_id=None,
                    entity_type="antimicrobial_result",
                    entity_id=ar.id,
                    action="DEVELOPMENT_SEED",
                    after_data={"antibiotic_id": ant.id, "interpretation": interp},
                )

        # --- End microbiology seed ---

        # --- Outputs and integrations seed (Phase 6) ---

        if item and not db.scalar(select(PrintJob).where(PrintJob.order_item_id == item.id)):
            db.add(PrintJob(
                order_item_id=item.id,
                kind="LABEL",
                requested_by=None,
                status="PRINTED",
                printed_at=datetime(2026, 1, 15, 14, 35, tzinfo=timezone.utc),
                details="ETIQUETA DE CODIGO DE BARRAS FICTICIA PARA DESARROLLO LOCAL.",
            ))
            record_audit(
                db,
                actor_user_id=None,
                entity_type="print_job",
                entity_id=item.id,
                action="DEVELOPMENT_SEED",
                after_data={"kind": "LABEL", "status": "PRINTED"},
            )

        if item and not db.scalar(select(Notification).where(Notification.order_item_id == item.id)):
            db.add(Notification(
                order_item_id=item.id,
                type="RESULT_READY",
                recipient="clinician@example.invalid",
                payload={"order_number": "DEV-ORDER-0001", "barcode": "DEV-ORDER-0001-01-UC"},
                status="SENT",
                sent_at=datetime(2026, 1, 15, 15, 0, tzinfo=timezone.utc),
            ))
            db.add(Notification(
                order_item_id=item.id,
                type="RESULT_READY",
                recipient="clinician@example.invalid",
                payload={"order_number": "DEV-ORDER-0001", "barcode": "DEV-ORDER-0001-01-UC"},
                status="FAILED",
                error_message="SERVIDOR SMTP TEMPORALMENTE NO DISPONIBLE.",
            ))
            record_audit(
                db,
                actor_user_id=None,
                entity_type="notification",
                entity_id=item.id,
                action="DEVELOPMENT_SEED",
                after_data={"types": ["RESULT_READY", "RESULT_READY"]},
            )

        if item and not db.scalar(
            select(InstrumentMessage).where(
                InstrumentMessage.order_item_id == item.id,
                InstrumentMessage.direction == "OUTBOUND",
            )
        ):
            db.add(InstrumentMessage(
                order_item_id=item.id,
                direction="OUTBOUND",
                payload={"instrument": "VITEK2", "barcode": "DEV-ORDER-0001-01-UC", "exam": "URINE_CULTURE"},
                status="PROCESSED",
                processed_at=datetime(2026, 1, 15, 15, 10, tzinfo=timezone.utc),
                result_summary="EL INSTRUMENTO CONFIRMO LA ORDEN.",
            ))
            db.add(InstrumentMessage(
                order_item_id=item.id,
                direction="INBOUND",
                payload={"organism": "Escherichia coli", "ast": {"AMK": "S", "CIP": "S"}},
                status="PROCESSED",
                processed_at=datetime(2026, 1, 15, 16, 0, tzinfo=timezone.utc),
                result_summary="RESULTADO AST DE VITEK2 RECIBIDO.",
            ))
            record_audit(
                db,
                actor_user_id=None,
                entity_type="instrument_message",
                entity_id=item.id,
                action="DEVELOPMENT_SEED",
                after_data={"directions": ["OUTBOUND", "INBOUND"]},
            )

        # --- End outputs/integrations seed ---

        for username, given_name, family_name, role_codes in DEVELOPMENT_USERS:
            user = db.scalar(select(User).where(User.username == username))
            created = user is None
            if created:
                roles = list(db.scalars(select(Role).where(Role.code.in_(role_codes))))
                user = User(
                    username=username,
                    given_name=given_name,
                    family_name=family_name,
                    password_hash=hash_password(password),
                    roles=roles,
                )
                db.add(user)
                db.flush()
            else:
                user.given_name = given_name
                user.family_name = family_name
            if username == "dev-processor":
                permission = db.scalar(
                    select(UserAreaPermission).where(
                        UserAreaPermission.user_id == user.id,
                        UserAreaPermission.laboratory_area_id == areas["MICROBIOLOGY"].id,
                    )
                )
                if not permission:
                    permission = UserAreaPermission(
                        laboratory_area_id=areas["MICROBIOLOGY"].id,
                        can_preliminary_validate=True,
                        can_final_validate=True,
                    )
                    user.area_permissions.append(permission)
                else:
                    permission.can_preliminary_validate = True
                    permission.can_final_validate = True
            if created:
                record_audit(
                    db,
                    actor_user_id=None,
                    entity_type="user",
                    entity_id=user.id,
                    action="DEVELOPMENT_SEED",
                    after_data={"username": user.username, "roles": list(role_codes)},
                )
        # Quick-login convenience user (password = "admin", for local dev only)
        admin_username, admin_given, admin_family, admin_roles, admin_password = QUICK_LOGIN_USER
        admin_user = db.scalar(select(User).where(User.username == admin_username))
        if not admin_user:
            admin_user = User(
                username=admin_username,
                given_name=admin_given,
                family_name=admin_family,
                password_hash=hash_password(admin_password),
                roles=list(db.scalars(select(Role).where(Role.code.in_(admin_roles)))),
            )
            db.add(admin_user)
            db.flush()
            record_audit(
                db,
                actor_user_id=None,
                entity_type="user",
                entity_id=admin_user.id,
                action="DEVELOPMENT_SEED",
                after_data={"username": admin_username, "roles": list(admin_roles)},
            )
        else:
            admin_user.given_name = admin_given
            admin_user.family_name = admin_family

        # Normalize historic microbiology result snapshots so existing orders
        # use the current parameter definitions when reopened in development.
        for value, parameter in db.execute(
            select(ResultValue, ParameterDefinition)
            .join(ParameterDefinition, ParameterDefinition.id == ResultValue.parameter_definition_id)
            .where(ParameterDefinition.section == "MICROBIOLOGY")
        ):
            current_snapshot = parameter_definition_snapshot(parameter)
            if value.parameter_snapshot != current_snapshot:
                value.parameter_snapshot = current_snapshot
                flag_modified(value, "parameter_snapshot")

        db.commit()


if __name__ == "__main__":
    seed()
    print("Development seed completed.")
