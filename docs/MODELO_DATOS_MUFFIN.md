# Modelo de datos de MUFFIN

Estado: base del MVP. Seguridad, catalogos minimos, pacientes, ordenes, trazabilidad de muestra, resultados dinamicos, microbiologia avanzada y salidas/integraciones estan implementados hasta la migracion `0006_outputs_integrations`.

## Criterios

- Identificadores internos: UUID. Los codigos de negocio se almacenan por separado y son unicos cuando aplique.
- Fechas: ISO 8601 en UTC; fecha y hora de toma/recepcion conservan su zona horaria de origen.
- Borrado: no se elimina informacion clinica. Los catalogos se desactivan y las anulaciones se auditan.
- Auditoria: toda accion clinica, validacion, impresion e integracion se registra en `audit_event`.
- Datos de pacientes: se minimizan y se protegen con permisos de rol y area.

## Entidades de seguridad

| Entidad | Campos principales | Proposito |
| --- | --- | --- |
| `user` | `id`, `username`, `given_name`, `family_name`, `password_hash`, `is_active` | Cuenta de acceso; nunca almacena contrasena en texto plano. |
| `role` | `id`, `code`, `name` | Perfil de acceso, por ejemplo: administrador, ingreso, proceso, toma de muestra o consulta. |
| `user_role` | `user_id`, `role_id` | Permite asignar uno o mas roles a una cuenta. |
| `laboratory_area` | `id`, `code`, `name`, `section` | Area responsable del trabajo, por ejemplo microbiologia. |
| `user_area_permission` | `user_id`, `laboratory_area_id`, `can_preliminary_validate`, `can_final_validate` | Autoriza operacion y validaciones por area. |

## Entidades clinicas y de solicitud

| Entidad | Campos principales | Proposito |
| --- | --- | --- |
| `patient` | `id`, `medical_record_number`, `document_number`, `family_name`, `given_name`, `birth_date`, `sex` | Identificacion minima del paciente. `medical_record_number` es unico por institucion. |
| `origin` | `id`, `code`, `name`, `is_active` | Procedencia de la solicitud. |
| `service` | `id`, `code`, `name`, `is_active` | Servicio hospitalario solicitante. |
| `clinician` | `id`, `code`, `family_name`, `given_name`, `email`, `is_active` | Profesional solicitante y destino de alertas. |
| `lab_order` | `id`, `order_number`, `ordered_at`, `patient_id`, `origin_id`, `service_id`, `clinician_id`, `clinical_notes`, `status` | Cabecera de solicitud microbiologica. |
| `order_item` | `id`, `lab_order_id`, `item_number`, `exam_id`, `specimen_type_id`, `barcode`, `collection_at`, `received_at`, `destination_id`, `specimen_notes`, `location`, `rejection_reason`, `status` | Unidad de trabajo trazable: examen solicitado sobre una muestra. |

`lab_order.order_number` es unico. `order_item.barcode` es unico una vez asignado. En el MVP un item representa una muestra-examen, igual que el detalle de orden heredado. Si posteriormente se requiere una sola muestra para multiples examenes, se incorporara una entidad `specimen` sin cambiar los contratos de resultados.

## Catalogos de laboratorio

| Entidad | Campos principales | Proposito |
| --- | --- | --- |
| `exam` | `id`, `code`, `name`, `external_code`, `barcode_suffix`, `laboratory_area_id`, `sends_to_analyzer`, `requires_colony_count`, `is_active` | Examen o metodo microbiologico configurable. |
| `parameter_definition` | `id`, `code`, `name`, `section`, `value_type`, `options_schema`, `methodology`, `unit`, `reference_low`, `reference_high`, `reference_text`, `is_active` | Define un parametro dinamico. `value_type`: `TEXT`, `LONG_TEXT`, `SELECT`, `DATE` o `DATETIME`; `SELECT` exige opciones. |
| `exam_parameter` | `exam_id`, `parameter_definition_id`, `display_order`, `external_code`, `is_required` | Relacion ordenada entre examen y parametro; el orden no se repite dentro de un examen. |
| `specimen_type` | `id`, `code`, `name`, `container_id`, `is_active` | Tipo de muestra aceptable. |
| `container` | `id`, `code`, `name`, `is_active` | Contenedor de recoleccion. |
| `exam_specimen_type` | `exam_id`, `specimen_type_id`, `is_favorite` | Muestras permitidas por examen. |
| `destination` | `id`, `code`, `name`, `is_active` | Destino o etapa de verificacion configurada. |

Las lecturas de catalogos requieren autenticacion. Las altas, actualizaciones, desactivaciones y relaciones requieren rol `ADMIN` o `PROCESS_ADMIN`. Los codigos se normalizan a mayusculas, los listados se paginan y cada cambio se registra en `audit_event`.

## Entidades de procesamiento y resultado

| Entidad | Campos principales | Proposito |
| --- | --- | --- |
| `result` | `id`, `order_item_id`, `status`, `saved_at`, `saved_by`, `preliminary_at`, `preliminary_by`, `final_at`, `final_by` | Contenedor clinico de resultado del item. |
| `result_value` | `id`, `result_id`, `parameter_definition_id`, `value_text`, `value_code`, `observed_at` | Valor de cada parametro dinamico. |
| `workflow_event` | `id`, `order_item_id`, `event_type`, `occurred_at`, `performed_by`, `details` | Toma, recepcion, envio a instrumento, validacion, anulacion o reapertura. |

## Entidades de microbiologia avanzada

Estas entidades estan implementadas en `backend/` desde la fase 5.

| Entidad | Campos principales | Proposito |
| --- | --- | --- |
| `organism` | `id`, `code`, `name`, `is_active` | Microorganismo identificable. |
| `antibiotic` | `id`, `code`, `name`, `is_active` | Antimicrobiano configurable. |
| `ast_panel` | `id`, `code`, `name`, `is_active` | Panel de sensibilidad por microorganismo o metodologia. |
| `ast_panel_antibiotic` | `ast_panel_id`, `antibiotic_id`, `display_order`, `default_method` | Antibioticos incluidos en un panel. |
| `colony_count_option` | `id`, `code`, `name`, `is_active` | Valores permitidos para recuento de colonias. |
| `defined_comment` | `id`, `code`, `text`, `is_active` | Comentario reutilizable para muestra o resultado. |
| `isolate` | `id`, `result_id`, `organism_id`, `colony_count_option_id`, `phenotype`, `comment`, `ast_panel_id` | Microorganismo identificado en el resultado. |
| `antimicrobial_result` | `id`, `isolate_id`, `antibiotic_id`, `mic_value`, `interpretation`, `method`, `is_reportable` | Resultado de sensibilidad. `interpretation`: S, SDD, I, R, positivo, negativo o no aplicable. |

## Soporte, auditoria e integracion

| Entidad | Campos principales | Proposito |
| --- | --- | --- |
| `audit_event` | `id`, `actor_user_id`, `entity_type`, `entity_id`, `action`, `occurred_at`, `before_data`, `after_data`, `reason` | Bitacora inmutable de acciones relevantes. |
| `print_job` | `id`, `order_item_id`, `kind`, `requested_by`, `requested_at`, `status` | Solicitudes de etiqueta, codigo de barras o documento. |
| `notification` | `id`, `order_item_id`, `type`, `recipient`, `payload`, `status`, `sent_at` | Alertas por correo u otros canales. |
| `instrument_message` | `id`, `order_item_id`, `direction`, `payload`, `status`, `processed_at` | Intercambio con analizador o instrumento. |

## Relaciones principales

```text
patient 1 --- n lab_order 1 --- n order_item 1 --- 1 result
lab_order n --- 1 origin / service / clinician
order_item n --- 1 exam / specimen_type
exam n --- n parameter_definition, mediante exam_parameter
result 1 --- n result_value
user n --- n role, mediante user_role
user n --- n laboratory_area, mediante user_area_permission
```

La cadena `isolate`/`antimicrobial_result` esta implementada en la fase 5. El autollenado de resultados de sensibilidad se activa al asignar un panel AST al aislado.

## Estados controlados

### Estado de orden

`DRAFT`, `REGISTERED`, `CANCELLED`, `CLOSED`.

### Estado de item de orden

`REGISTERED` -> `COLLECTED` -> `RECEIVED` -> `IN_PROCESS` -> `RESULT_SAVED` -> `PRELIMINARY_VALIDATED` -> `FINAL_VALIDATED`.

Ramas permitidas: `REGISTERED`, `COLLECTED` o `RECEIVED` pueden pasar a `REJECTED` o `CANCELLED` segun el rol. Una reapertura de rechazo o anulacion exige `ADMIN` o `PROCESS_ADMIN`, motivo y evento de auditoria. La reapertura restaura `REGISTERED`, `COLLECTED` o `RECEIVED` de acuerdo con las marcas temporales conservadas. Una reapertura posterior a validacion final ya esta implementada en la fase de resultados y exige permiso de area, motivo y auditoria.

## Reglas no negociables

1. No se permite validacion final sin resultado guardado.
2. La validacion preliminar y final requieren permisos explicitos para el area del examen.
3. Un resultado final no se edita; se reabre con motivo y auditoria.
4. Los valores de resultado se guardan con su definicion de parametro para preservar trazabilidad aunque cambie el catalogo despues.
5. Los identificadores externos y codigos de barras se validan como unicos.
6. Los catalogos inactivos no se ofrecen en nuevas ordenes, pero permanecen visibles en el historial.
