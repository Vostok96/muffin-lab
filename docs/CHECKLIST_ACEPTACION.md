# Checklist de aceptacion local — MUFFIN

Fecha: 2026-07-17 | Version: 0.1.0

Cada item debe verificarse en local (x86_64) con Docker Compose desde un volumen PostgreSQL vacio (`down -v`).

## 1. Entorno reproducible

- [x] `docker compose config` valido sin errores
- [x] `docker compose up -d --build` levanta ambos servicios
- [x] `docker compose ps` muestra `muffin-api` y `muffin-postgres` saludables
- [x] Alembic aplica las 6 migraciones automaticamente
- [x] `curl /api/v1/health` devuelve `{"status":"ok","service":"muffin-api"}`

## 2. Seguridad

- [x] Endpoints requieren autenticacion (401 sin token)
- [x] Roles ADMIN, PROCESS_ADMIN, PROCESSOR, ENTRY, COLLECTOR, CONSULTANT aplicados
- [x] Permisos de validacion por area (`can_preliminary_validate`, `can_final_validate`)
- [x] Contrasenas almacenadas con Argon2id (no texto plano)
- [x] JWT con expiracion de 30 minutos
- [x] Auditoria registra CREATE, UPDATE, DELETE, SAVE, VALIDATE, REOPEN
- [x] Advisory lock en bootstrap de seguridad evita carreras entre workers

## 3. Catalogos

- [x] CRUD para areas, origenes, servicios, clinicos, contenedores, destinos, muestras, examenes, parametros
- [x] Relaciones examen-muestra y examen-parametro configurables
- [x] Desactivacion en lugar de borrado fisico
- [x] Paginacion con busqueda por codigo/nombre
- [x] Duplicados de codigo rechazados (409)
- [x] Catalogos de microbiologia: organismos, recuentos, comentarios, antibioticos, paneles AST
- [x] Relacion panel-antibiotico con orden y metodo por defecto

## 4. Flujo clinico

- [x] Creacion y busqueda de pacientes por HC
- [x] Creacion de ordenes con numero secuencial y codigo de barras unico
- [x] Items muestra-examen con validacion de relacion
- [x] Toma de muestra (COLLECTED)
- [x] Recepcion con destino (RECEIVED)
- [x] Rechazo con motivo (REJECTED)
- [x] Anulacion de item/orden (CANCELLED)
- [x] Reapertura de item/orden con motivo y auditoria
- [x] Eventos de flujo inmutables por item

## 5. Resultados

- [x] Formulario dinamico desde `exam_parameter`
- [x] Guardado en proceso (IN_PROCESS) y listo para validar (RESULT_SAVED)
- [x] Validacion preliminar con permiso de area
- [x] Validacion final con permiso de area
- [x] Bloqueo de edicion tras validacion final
- [x] Reapertura con motivo, permiso y auditoria
- [x] Tipos de valor: TEXT, LONG_TEXT, SELECT, DATE, DATETIME
- [x] Opciones de SELECT validadas contra catalogo

## 6. Microbiologia avanzada

- [x] Aislados vinculados a resultados con organismo, recuento y fenotipo
- [x] Autollenado de resultados de sensibilidad desde panel AST
- [x] Edicion de CMI, interpretacion (S/SDD/I/R/POS/NEG/NA) y metodo
- [x] Reportabilidad configurable por antibiotico
- [x] Borrado de aislados solo para ADMIN/PROCESS_ADMIN

## 7. Salidas e integraciones

- [x] Print jobs: LABEL/BARCODE/REPORT con estados PENDING/PRINTED/FAILED
- [x] Notificaciones: resolucion automatica del email del clinico
- [x] Reenvio de notificaciones fallidas
- [x] Mensajes de instrumento INBOUND/OUTBOUND con payload libre

## 8. Rendimiento

- [x] p95 lecturas < 150 ms (8/8 endpoints)
- [x] p95 escrituras < 300 ms (5/5 endpoints, auth/login Argon2 incluido)
- [x] 13 endpoints benchmarkeados con 30 iteraciones cada uno

## 9. Pruebas de humo

- [x] `Local API smoke test passed.`
- [x] `Catalog API smoke test passed.`
- [x] `Clinical workflow smoke test passed.`
- [x] `Result validation smoke test passed.`
- [x] `Microbiology advanced smoke test passed.`
- [x] `Outputs and integrations smoke test passed.`

## 10. Pruebas unitarias

- [x] 27 tests pasan en < 1 segundo
- [x] Schemas de seguridad, catalogos, clinica, resultados, microbiologia y outputs

## 11. Respaldo y restauracion

- [x] `pg_dump` genera dump SQL completo (~370 KB)
- [x] Las 34 tablas estan presentes en el dump
- [x] Datos de semilla verificados en el dump (DEV-HC-0001, ECOLI, AMK)
- [x] No se pierden datos durante el proceso de respaldo

## 12. Seguridad operativa

- [x] 25/25 verificaciones de seguridad pasan
- [x] Autenticacion, roles, permisos de area, JWT, Argon2, manejo de errores
- [x] `.env.local` y `.env` excluidos de Git via `.gitignore`
- [x] No hay credenciales ni secretos reales en el codigo

## 13. Documentacion

- [x] `docs/AVANCE_MUFFIN.md` — estado y fases vigentes
- [x] `docs/AGENT_CONTEXT.md` — contexto para el proximo agente
- [x] `docs/DESARROLLO_LOCAL.md` — instrucciones de desarrollo
- [x] `docs/MODELO_DATOS_MUFFIN.md` — entidades y reglas
- [x] `docs/MUFFIN_API_V1.yaml` — contrato OpenAPI
- [x] `docs/HANDOFF_LINUX.md` — traspaso a Linux
- [x] `docs/MANUAL_OPERATIVO.md` — operacion y mantenimiento
- [x] `docs/CHECKLIST_ACEPTACION.md` — este documento

## Pendientes para produccion

- [ ] Adaptador del frontend para consumir flujo de resultados dinamicos
- [ ] Despliegue en NAS ARM64 con recursos ajustados (8 GB RAM, HDD)
- [ ] NTP activo en el NAS
- [ ] Proxy HTTPS con Nginx
- [ ] Pruebas de rendimiento en entorno NAS con HDD
- [ ] Carga de datos reales tras aceptacion del laboratorio
- [ ] Retencion de datos y control de acceso a respaldos

## Resultado

**Fase 7: ACEPTADA.** Todos los criterios locales de calidad, rendimiento, seguridad, respaldo y documentacion se cumplen.
