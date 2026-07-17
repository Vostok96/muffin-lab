# Avance de MUFFIN

Actualizado: 2026-07-17

## Politica de trabajo

MUFFIN se construye, prueba y corrige en local antes de desplegarse en el NAS. El NAS es el destino de preproduccion y produccion, no el entorno de experimentacion.

No se realiza ningun despliegue al NAS hasta cumplir todos los criterios locales de la fase de calidad: migraciones, pruebas funcionales, rendimiento, seguridad, respaldo y restauracion.

La institucion objetivo inicial es el `Hospital Sub Regional de Andahuaylas`. Toda nueva capacidad debe construirse pensando en un tenant unico con posibilidad de replicarse luego en otros hospitales sin bifurcar el codigo.

## Completado

- Plataforma MUFFIN centrada en el Hospital Sub Regional de Andahuaylas, con compatibilidad temporal con el frontend heredado de SIMCORE.
- Identidad visual MUFFIN: diseno operativo, paleta teal/mint/peach/cream con modo claro y oscuro.
- Modelo de datos base: `docs/MODELO_DATOS_MUFFIN.md`.
- Contrato API v1: `docs/MUFFIN_API_V1.yaml`.
- Base FastAPI con PostgreSQL, Docker x86_64, Alembic, JWT, Argon2, roles, permisos de area y auditoria.
- Docker Compose validado en Linux x86_64 con Docker 29.1.3 y Compose v2.40.3 contra PostgreSQL 16.
- 6 migraciones aplicadas desde volumen vacio: seguridad, catalogos, clinica, resultados, microbiologia avanzada y salidas/integraciones.
- Semilla ficticia idempotente con datos de todas las fases. Usuario rapido `admin`/`admin`.
- 5 smoke tests + prueba de outputs pasando desde volumen vacio. 27 unit tests en <1s.
- 25 verificaciones de seguridad automatizadas. 13 benchmarks de rendimiento (p95 < 150ms lecturas, < 300ms escrituras).
- Respaldo/restauracion PostgreSQL verificado (pg_dump 370 KB, 34 tablas).
- Manual operativo (`docs/MANUAL_OPERATIVO.md`) y checklist de aceptacion (`docs/CHECKLIST_ACEPTACION.md`).
- Frontend heredado transformado: branding SIMCORE → MUFFIN en las 29 paginas capturadas, navbar muffin-nav, CSS teal, modo oscuro con toggle pill sol/luna, persistencia en localStorage.
- Pantalla de login real en `/MUFFIN/Login/Index` con diseno MUFFIN, conexion JWT a la API y CORS habilitado.
- Proxy SIMCORE→MUFFIN en `server.py` que traduce llamadas del frontend capturado a la API real. 12 endpoints de catalogos y usuarios funcionales (lectura + escritura + eliminacion).
- Usuarios: creacion via proxy desde formulario SIMCORE, eliminacion/desactivacion con boton inyectado, reactivacion via API.
- Leyenda de permisos por rol en `docs/PERMISOS_ROL.md` con 18 acciones × 7 roles + mapeo SIMCORE↔MUFFIN.
- Documento objetivo institucional: `docs/ARQUITECTURA_OBJETIVO_MUFFIN_ANDAHUAYLAS.md`.

El backend existe solo en local. No hay datos clinicos, secretos reales ni despliegue en el NAS.

## Frontend y proxy (nuevo)

### Transformacion SIMCORE → MUFFIN

- 29 paginas HTML capturadas: 0 referencias a SIMCORE, 4069 a MUFFIN.
- `mirror/SIMCORE_WEB/` renombrado a `mirror/MUFFIN/`. Rutas `/SIMCORE_WEB/*` → `/MUFFIN/*`.
- Navbar `muffin-nav` con gradiente teal en todas las paginas.
- Logo `MUFFIN_ICONO.jpg`, titulos, footer y copyright actualizados.
- `muffin.css` (14 KB) con variables teal, overrides Bootstrap (jumbotron, cards, tablas, formularios, botones, DataTables) y dark mode completo.
- Toggle de modo oscuro: boton pill sol/luna flotante (abajo-derecha en paginas internas, arriba-derecha en login). Persiste via `localStorage('muffin-theme')`. Respeta `prefers-color-scheme` del sistema.
- Login page en `docs/login.html`: diseno independiente con gradiente teal, tarjeta blanca, CORS a API, limpieza de token al cargar.
- Logout en `/MUFFIN/Home/Salir`: limpia `localStorage` y redirige a login.

### Proxy SIMCORE → MUFFIN API

`server.py` actua como capa de compatibilidad entre el frontend capturado y la API MUFFIN:

| SIMCORE (frontend capturado) | MUFFIN API | Metodo |
|---|---|---|
| `Mic_usuario/Obtener` | `GET /api/v1/admin/users` | Proxy (traduce campos y roles) |
| `Mic_usuario/Guardar` | `POST /api/v1/admin/users` | Proxy (crea o notifica existente) |
| `Mic_usuario/Eliminar` | `DELETE /api/v1/admin/users/{id}` | Proxy (desactiva) |
| `Mic_usuario/Reactivar` | `POST /api/v1/admin/users/{id}/reactivate` | Proxy (reactiva) |
| `Mic_area/Obtener` | `GET /api/v1/catalogs/areas` | Proxy |
| `Mic_procedencia/Obtener` | `GET /api/v1/catalogs/origins` | Proxy |
| `Mic_servicio/Obtener` | `GET /api/v1/catalogs/services` | Proxy |
| `Mic_medico/Obtener` | `GET /api/v1/catalogs/clinicians` | Proxy |
| `Mic_examen/Obtener` | `GET /api/v1/catalogs/exams` | Proxy |
| `Mic_orga/Obtener` | `GET /api/v1/catalogs/organisms` | Proxy |
| `Mic_antibiotico/Obtener` | `GET /api/v1/catalogs/antibiotics` | Proxy |
| `Mic_parametro/Obtener` | `GET /api/v1/catalogs/parameters` | Proxy |
| `Mic_muestra/Obtener` | `GET /api/v1/catalogs/specimen-types` | Proxy |
| `Mic_destinos/Obtener` | `GET /api/v1/catalogs/destinations` | Proxy |
| `Mic_muestra_contenedor/Obtener` | `GET /api/v1/catalogs/containers` | Proxy |

La autenticacion del proxy usa el usuario `admin`/`admin` como puente. El mapeo de roles SIMCORE↔MUFFIN esta en `server.py` (ROLE_MAP / ROLE_REV). Encoding UTF-8 con `raw.decode("utf-8")` — caracteres como Ñ funcionan correctamente.

### Boton de eliminar usuario

Script inyectado en `Mic_usuario.html`: agrega boton rojo "Desactivar" o verde "Reactivar" en cada fila de la DataTable, con confirmacion y manejo de errores del backend. Campo contrasena enmascarado con `type="password"`.

### Correcciones criticas (auditoria 2026-07-16)

- `api_req()` ahora captura el campo `detail` de respuestas HTTP 4xx/5xx y lo reenvia al frontend como `mensaje` en vez de devolver None.
- Delete proxy verifica si el usuario ya esta inactivo antes de llamar al backend, y rechaza con mensaje claro. Proteccion contra desactivar al usuario admin rapido.
- Reactivate proxy verifica si el usuario ya esta activo antes de llamar al backend.
- Catalog proxy con mapeo de campos por endpoint: cada catalogo devuelve los field names exactos que espera el frontend SIMCORE (`area_id`/`area_desc`, `medico_colegiatura`/`medico_nombres`, `orga_id`/`orga_desc`, etc).
- Endpoints proxy para area permissions (list/guardar/eliminar) y cambio de password — stubs que evitan 404 y estan listos para integracion con API futura.
- Todos los 15 paginas capturadas devuelven HTTP 200. Smoke test backend sigue pasando.

## Orden revisado de construccion

### 1. Entorno local reproducible

- Ejecutar Docker Compose localmente contra PostgreSQL antes de usar el NAS.
- Crear datos ficticios de desarrollo y un administrador local no reutilizable.
- Verificar que la migracion se aplique desde una base vacia.
- Mantener `.env` fuera de Git y documentar variables obligatorias.

Este punto es bloqueante para las fases siguientes.

Estado: completado el 2026-07-15 en Linux x86_64. `docker compose config` fue valido; PostgreSQL y API quedaron saludables; Alembic aplico `0001_security_foundation` desde un volumen vacio; la semilla termino correctamente dos veces; la prueba devolvio `Local API smoke test passed.` y health devolvio `{"status":"ok","service":"muffin-api"}`. Los logs finales quedaron sin errores de API ni PostgreSQL.

### 2. Catalogos minimos del MVP

Los catalogos basicos deben construirse antes de ordenes; no pertenecen a la fase avanzada.

- Areas, procedencias, servicios y medicos.
- Examenes, tipos de muestra, contenedores y relacion examen-muestra.
- Usuarios, roles y permisos por area ya iniciados.
- Parametros de resultado y relacion examen-parametro.

Estado: completado el 2026-07-16 en Linux x86_64. Alembic alcanzo `0002_minimum_catalogs (head)` desde un volumen vacio. La semilla ficticia completa termino correctamente dos veces. Las pruebas de humo de seguridad y catalogos devolvieron `Local API smoke test passed.` y `Catalog API smoke test passed.`. La API permite lectura autenticada y reserva altas, cambios, desactivaciones y relaciones a `ADMIN` o `PROCESS_ADMIN`; no expone borrado fisico de registros de catalogo.

### 3. MVP clinico y trazabilidad de muestra

- Paciente y busqueda por historia clinica.
- Orden y detalle muestra-examen.
- Generacion de numero de orden y codigo de barras.
- Registro de toma, recepcion, destino y eventos de flujo.
- Rechazo, anulacion y reapertura con motivo y auditoria.

El rechazo de muestra y los eventos de flujo se agregan como requisito clinico explicito; no deben quedar implicitos en un campo de estado.

Estado: completado el 2026-07-16 en Linux x86_64. La migracion vigente es `0003_clinical_mvp`; la semilla incorpora un paciente, una orden y una muestra recibida estrictamente ficticios. `Clinical workflow smoke test passed.` cubre busqueda por HC, alta y actualizacion de paciente, orden, items, barcode, toma, recepcion, rechazo, anulacion, reapertura, permisos y trazabilidad. La suite unitaria final devolvio `9 passed`. Las 59 rutas capturadas del frontend de referencia respondieron HTTP 200 en el puerto 8877 sin reescribir su comportamiento; su integracion adaptada con la API se realizara despues de estabilizar resultados y validacion.

### 4. Resultados y validacion

Estado: cerrado el 2026-07-16 en Linux x86_64. La migracion vigente es `0004_results_validation`. Validacion limpia completada desde un volumen vacio: `down -v`, arranque, doble semilla idempotente, cuatro pruebas de humo pasadas, 12 pruebas unitarias pasadas, health `{"status":"ok","service":"muffin-api"}`, logs sin errores relevantes. El adaptador del frontend para consumir este flujo queda pendiente como tarea de UI.

- Captura de parametros dinamicos por examen.
- Guardado en proceso, validacion preliminar y validacion final.
- Bloqueo posterior a validacion final.
- Reapertura solo con permiso, motivo y evento de auditoria.
- Permisos de validacion por area ya definidos en la base de seguridad.
- La semilla incorpora un resultado ficticio `NO_GROWTH` para `DEV-ORDER-0001-01-UC` y la prueba `Result validation smoke test passed.` cubre el flujo completo.

### 5. Microbiologia avanzada

Estado: implementado y validado el 2026-07-16 en Linux x86_64. Migracion `0005_microbiology_advanced` aplicada desde volumen vacio. Incluye organismos, recuentos de colonias, comentarios definidos, antibioticos, paneles AST con relacion de antibioticos ordenada, aislados vinculados a resultados y resultados de sensibilidad (antimicrobial_result) con CMI, interpretacion, metodologia y trazabilidad.

- Catalogos de microorganismos, opciones de recuento, comentarios definidos, antibioticos y paneles AST con CRUD completo, auditoria, paginacion y desactivacion.
- Aislados por resultado con organismo, recuento, fenotipo, comentario y panel AST asociado.
- Autollenado de resultados de sensibilidad desde el panel AST del aislado.
- Edicion de CMI, interpretacion (S/SDD/I/R/POS/NEG/NA), metodo y reportabilidad por antibiotico.
- Permisos: lectura autenticada, edicion de aislados y AST para ADMIN/PROCESS_ADMIN/PROCESSOR, borrado de aislados para ADMIN/PROCESS_ADMIN.
- Semilla ficticia con E. coli, recuento moderado, panel GN_URINE y 5 antibioticos con sensibilidad completa.
- `Microbiology advanced smoke test passed.` cubre catalogos, creacion de aislados, autollenado AST, edicion de sensibilidad, borrado y permisos.
- 8 pruebas unitarias adicionales de schemas (20 total). 5 de 5 smoke tests pasan contra volumen vacio.

### 6. Salidas e integraciones

Estado: implementado y validado el 2026-07-16 en Linux x86_64. Migracion `0006_outputs_integrations` aplicada desde volumen vacio.

- Print jobs con tipos LABEL/BARCODE/REPORT, estados PENDING/PRINTED/FAILED y timestamps.
- Notificaciones con tipos RESULT_READY/CRITICAL_VALUE/SPECIMEN_REJECTED/REPORT_AVAILABLE/CUSTOM, resolucion automatica del email del clinico, estados PENDING/SENT/FAILED y reenvio en caso de fallo.
- Mensajes de instrumento con direccion INBOUND/OUTBOUND, payload libre, estados PENDING/PROCESSED/FAILED/ACKNOWLEDGED y consulta por order item.
- Permisos: lectura autenticada, escritura para ADMIN/PROCESS_ADMIN/PROCESSOR/ENTRY.
- Semilla ficticia con print job de etiqueta impresa, notificacion enviada y fallida, y mensajes OUTBOUND+INBOUND de VITEK2.
- `Outputs and integrations smoke test passed.` cubre print jobs (crear, completar, fallar), notificaciones (crear, actualizar, reenviar) y mensajes de instrumento (crear, actualizar, listar por item).
- 7 pruebas unitarias adicionales (27 total). 6 de 6 smoke tests pasan.

### 7. Calidad y aceptacion local

Estado: cerrado el 2026-07-16 en Linux x86_64.

- 27 pruebas unitarias en 0.62s cubriendo schemas de las 6 fases.
- 6 pruebas de humo (seguridad, catalogos, clinica, resultados, microbiologia, outputs/integraciones) pasando desde volumen vacio con doble semilla idempotente.
- 25 verificaciones de seguridad automatizadas: autenticacion, roles, permisos de area, JWT, Argon2, auditoria, manejo de errores y aislamiento de sesion — todas pasan.
- 13 benchmarks de rendimiento con 30 iteraciones c/u: p95 < 150ms en 8 endpoints de lectura, p95 < 300ms en 5 de escritura (incluye Argon2 en login).
- Respaldo y restauracion verificados: pg_dump de 370 KB con las 34 tablas y datos de semilla intactos.
- Manual operativo (`docs/MANUAL_OPERATIVO.md`) con despliegue, migraciones, respaldo, monitoreo y solucion de problemas.
- Checklist de aceptacion (`docs/CHECKLIST_ACEPTACION.md`) con 13 secciones y criterios explicitos.

Fase 7 superada. El NAS ARM64 queda como siguiente paso (fase 8).

### 8. Despliegue controlado en NAS

- Construir imagenes Docker compatibles con `linux/arm64`.
- Crear volumenes persistentes, secretos, proxy HTTPS y acceso restringido de red.
- Restaurar un respaldo de prueba en el NAS antes de usar datos reales.
- Ejecutar pruebas de humo y monitorear recursos, errores, tiempos de respuesta y espacio.
- Cargar datos reales solo tras la aceptacion funcional del laboratorio.

## Consideraciones nuevas incorporadas

- El NAS tiene HDD y 8 GB de RAM: el sistema debe evitar listados sin paginacion, consultas N+1, reportes sincronicos y servicios auxiliares innecesarios.
- Las marcas temporales dependen de reloj correcto: el NAS debe mantener NTP activo.
- La privacidad no termina en autenticacion: se requiere retencion de datos, minimizacion de exportaciones y control de acceso a respaldos.
- Las migraciones son parte de cada cambio de modelo y deben probarse contra una base vacia y una base con datos ficticios.
- El estado clinico debe estar representado por eventos auditables, no solo por colores o textos de interfaz.
