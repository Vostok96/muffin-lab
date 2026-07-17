# Contexto para el proximo agente

> **Documento historico.** El estado autoritativo y actualizado al 2026-07-16
> esta en `docs/HANDOFF_ESTADO_ACTUAL.md`. Leer ese archivo antes de usar las
> instrucciones antiguas de este documento.

Fecha de preparacion: 2026-07-15

Repositorio: `Vostok96/simcore`

Carpeta local original en el laboratorio:

```text
C:\Users\LABORATORIO\Documents\AUTOCHECKER\simcore_real_clone
```

## Objetivo del proyecto

Este repositorio contiene una captura local del frontend real de SIMCORE WEB para poder trabajar mejoras fuera del laboratorio, sin llevar datos de pacientes.

La aplicacion original vive en la intranet del laboratorio bajo:

```text
http://192.168.0.220/SIMCORE_WEB/
```

El clon local conserva el prefijo `/SIMCORE_WEB/` para que el frontend se comporte igual y sea mas facil conectarlo a un backend ficticio o a una base simulada en el NAS del usuario.

## Que contiene

- HTML renderizado de las pantallas principales de SIMCORE.
- Bundles CSS y JS entregados por el servidor original.
- Scripts de vistas ubicados en `mirror/SIMCORE_WEB/Scripts/Views`.
- Logo y assets publicos que el servidor entrego correctamente.
- Mapa de rutas en `docs/routes.json`.
- Mapa de assets en `docs/assets.json`.
- Mapa de endpoints detectados en `docs/endpoints.json`.
- Servidor local en `server.py`.
- Script de arranque en `run_local.ps1`.

## Que no contiene

- Base de datos real.
- Ordenes reales.
- Resultados reales.
- Nombres, DNI, HC ni datos clinicos de pacientes.
- Credenciales reales.
- Codigo fuente servidor C#/MVC original, porque ese codigo no se puede descargar por HTTP desde el navegador.

## Estado de privacidad

Antes de subir se reviso y sanitizo el clon:

- No quedaron credenciales reales en los archivos versionados.
- Los inputs ocultos capturados con `session_user_id` fueron cambiados a `local_demo`.
- Se removio una referencia comentada a un DNI de ejemplo en `Mic_orden_Index.js`.
- Se escanearon patrones de DNI de 8 digitos en paginas, scripts, docs y servidor local.

Si se vuelve a capturar desde SIMCORE, repetir un escaneo de privacidad antes de commitear.

## Como ejecutar en casa

Clonar el repo:

```powershell
git clone https://github.com/Vostok96/simcore.git
cd simcore
```

Ejecutar:

```powershell
.\run_local.ps1
```

Abrir:

```text
http://127.0.0.1:8877/SIMCORE_WEB/
```

Tambien se puede lanzar manualmente:

```powershell
python .\server.py
```

## Backend local y NAS

El servidor incluido responde endpoints con stubs vacios para que la interfaz cargue sin datos reales. Ejemplo:

```text
/SIMCORE_WEB/Mic_orden/Obtener
```

Respuesta esperada en modo local:

```json
{
  "data": [],
  "recordsTotal": 0,
  "recordsFiltered": 0,
  "success": true,
  "mensaje": "Modo local: endpoint stub sin datos reales."
}
```

El siguiente trabajo recomendado es reemplazar gradualmente esos stubs por endpoints locales conectados al NAS o a una base ficticia. Usar `docs/endpoints.json` como inventario de endpoints que el frontend intenta llamar.

## Captura realizada

Resumen de la captura guardado en `docs/CAPTURE_REPORT.md`:

- Paginas capturadas: 29
- Paginas con error: 1
- Assets capturados: 33
- Assets con error: 32
- Endpoints detectados: 99

No se invocaron endpoints de listados de pacientes u ordenes reales durante la captura; solo paginas y assets autenticados.

## Errores conocidos de la captura

Una pagina del SIMCORE original respondio HTTP 500 tambien en origen:

```text
/SIMCORE_WEB/Trans_consultas/Microbiologia_proce_servi_medico
```

Varios assets referenciados por CSS respondieron HTTP 404 en el servidor original, sobre todo fuentes FontAwesome, iconos de DataTables y assets de jQuery UI. Estan documentados en `docs/CAPTURE_REPORT.md`.

## Como recapturar desde el laboratorio

No dejar credenciales en archivos. Usar variables de entorno:

```powershell
$env:SIMCORE_SOURCE_URL = "http://192.168.0.220/SIMCORE_WEB/"
$env:SIMCORE_SOURCE_USER = "TU_USUARIO_SIMCORE"
$env:SIMCORE_SOURCE_PASS = "TU_PASSWORD_SIMCORE"
python .\tools\capture_simcore_frontend.py
```

Despues de recapturar:

```powershell
rg -n "\\b\\d{8}\\b|session_user_id|password|pass" .
git status
```

Revisar manualmente cualquier coincidencia antes de subir.

## Historial importante

Inicialmente se habia subido por error un kit teorico del modulo de imagenes. Ese contenido fue eliminado del repo remoto. Luego se preparo este clon real del frontend SIMCORE y se reemplazo el historial remoto con el commit correcto.

Commit base del clon real:

```text
c73602f Capture real SIMCORE frontend without patient data
```

## Recomendaciones para el proximo agente

- No asumir que este repo contiene el backend real de SIMCORE.
- Mantener el prefijo `/SIMCORE_WEB/` mientras se construye el backend simulado.
- Empezar conectando endpoints de solo lectura con datos ficticios.
- Priorizar `Mic_orden`, `Mic_orden_detalle/Resultado_microbiologia`, `Mic_parametro`, `Mic_examen`, `Mic_orga` y reportes de microbiologia.
- No subir capturas nuevas sin escaneo de privacidad.
- Si se agrega backend real local, documentar variables de entorno y nunca versionar `.env`.

## Actualizacion MUFFIN

El proyecto ahora incluye una base de backend local en `backend/` con FastAPI, PostgreSQL, Alembic, JWT, Argon2, roles, permisos por area y auditoria. No es codigo del backend original de SIMCORE.

El avance y el orden de construccion vigente estan en `docs/AVANCE_MUFFIN.md`. La politica acordada es construir y probar en local antes de cualquier despliegue al NAS ARM64.

La validacion de Docker Compose local se completo el 2026-07-15 en Linux x86_64 con Docker 29.1.3 y Compose v2.40.3. Desde un volumen PostgreSQL vacio, Alembic aplico `0001_security_foundation`, la semilla ficticia termino dos veces sin duplicados, el smoke test devolvio `Local API smoke test passed.` y health devolvio `{"status":"ok","service":"muffin-api"}`.

Durante la primera ejecucion se detecto una carrera entre los dos workers de Uvicorn al crear roles de seguridad. `bootstrap_security_data` ahora adquiere un advisory lock transaccional de PostgreSQL antes del flujo consultar-insertar. La reconstruccion posterior desde `down -v` arranco ambos workers sin excepciones ni violaciones de unicidad.

La fase 1 de `docs/AVANCE_MUFFIN.md` esta cerrada.

La fase 2 de catalogos minimos se completo el 2026-07-16. La migracion vigente es `0002_minimum_catalogs` e incluye procedencias, servicios, medicos, contenedores, tipos de muestra, examenes, parametros, relacion examen-muestra y relacion examen-parametro. Areas y seguridad permanecen en `0001_security_foundation`.

La API de catalogos usa rutas tipadas bajo `/api/v1/catalogs`, lectura para usuarios autenticados y escritura para `ADMIN` o `PROCESS_ADMIN`. Los registros se desactivan en lugar de borrarse; las relaciones configurables si pueden retirarse y toda mutacion se audita. La semilla ficticia incluye un cultivo de orina completo y es idempotente.

Validacion real desde volumen vacio: `0002_minimum_catalogs (head)`, doble semilla correcta, `Local API smoke test passed.` y `Catalog API smoke test passed.`.

La fase 3 se completo el 2026-07-16 con `0003_clinical_mvp`: pacientes, ordenes, items muestra-examen, catalogo de destinos y eventos de flujo. La API genera numero de orden y barcode, aplica estados `REGISTERED`, `COLLECTED`, `RECEIVED`, `REJECTED` y `CANCELLED`, y exige motivo y rol para rechazo, anulacion o reapertura. La semilla incluye solo un caso clinico ficticio. `Clinical workflow smoke test passed.` valida el flujo completo.

La fase 4 se cerro el 2026-07-16 en Linux x86_64 con `0004_results_validation`: formulario dinamico por `exam_parameter`, guardado en proceso, validacion preliminar y final, bloqueo tras validacion final, reapertura justificada, semilla de resultado y smoke test propio. La validacion limpia desde un volumen vacio fue completada: `down -v`, arranque, doble semilla idempotente, los cuatro smoke tests (`Local API`, `Catalog API`, `Clinical workflow`, `Result validation`) pasaron, 12 pruebas unitarias pasaron en 0.61s, health devolvio `{"status":"ok","service":"muffin-api"}` y logs sin errores relevantes. El frontend heredado sigue como referencia y aun no consume este flujo de resultados. La siguiente fase es fase 5: microbiologia avanzada. El NAS ARM64 continua reservado para una fase posterior.

La fase 5 se implemento y valido el 2026-07-16 en Linux x86_64 con `0005_microbiology_advanced`: organismos, opciones de recuento de colonias, comentarios definidos, antibioticos, paneles AST con relacion ordenada de antibioticos, aislados (isolate) vinculados a resultados y resultados de sensibilidad (antimicrobial_result) con CMI, interpretacion, metodo y reportabilidad. Autollenado de AST desde el panel seleccionado. Catalogos con CRUD completo, paginacion y desactivacion; permisos de lectura autenticada, edicion para ADMIN/PROCESS_ADMIN/PROCESSOR, borrado para ADMIN/PROCESS_ADMIN. La semilla incluye E. coli con recuento moderado, panel GN_URINE y 5 antibioticos con sensibilidad S. La validacion limpia desde volumen vacio completo: 5 de 5 smoke tests pasados, 20 unit tests pasados en 0.62s, health OK, logs limpios.

La fase 6 se implemento y valido el 2026-07-16 en Linux x86_64 con `0006_outputs_integrations`: print jobs (LABEL/BARCODE/REPORT) con estados PENDING/PRINTED/FAILED; notificaciones (RESULT_READY, CRITICAL_VALUE, SPECIMEN_REJECTED, REPORT_AVAILABLE, CUSTOM) con resolucion automatica del email del clinico y reenvio en caso de fallo; mensajes de instrumento bidireccionales (INBOUND/OUTBOUND) con payload libre y estados PENDING/PROCESSED/FAILED/ACKNOWLEDGED. Semilla con print job impreso, notificacion enviada y fallida, y mensajes VITEK2. 6 de 6 smoke tests y 27 unit tests pasan contra volumen vacio.

La fase 7 se cerro el 2026-07-16 en Linux x86_64 con pruebas de calidad completas: 27 unit tests (0.62s), 6 smoke tests desde volumen vacio, 25 verificaciones de seguridad automatizadas (autenticacion JWT/Argon2, roles, permisos de area, auditoria, errores), 13 benchmarks de rendimiento (p95 < 150ms en 8 lecturas, < 300ms en 5 escrituras incluyendo Argon2), respaldo/restauracion verificado (pg_dump 370 KB, 34 tablas, datos de semilla intactos), manual operativo (`docs/MANUAL_OPERATIVO.md`) y checklist de aceptacion con 13 secciones (`docs/CHECKLIST_ACEPTACION.md`). La siguiente fase es fase 8: despliegue controlado en NAS ARM64 (construir imagenes multi-arquitectura, volumenes persistentes, secretos, HTTPS, restauracion de respaldo, pruebas de humo y monitoreo de recursos).
