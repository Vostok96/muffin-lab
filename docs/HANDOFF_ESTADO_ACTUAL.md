# Traspaso del estado actual de MUFFIN

Fecha: 2026-07-17

Este documento es la fuente autoritativa para continuar el trabajo. Los
documentos `AGENT_CONTEXT.md`, `AVANCE_MUFFIN.md` y `README.md` contienen partes
historicas que ya no describen por completo el sistema actual.

## Advertencias antes de trabajar

- Directorio activo: `/home/workstation/Documentos/MUFFIN`.
- Este directorio no es actualmente un repositorio Git.
- La base local ya contiene al menos una orden ingresada manualmente. No usar
  `docker compose down -v`, no borrar el volumen y no reconstruir la base desde
  cero sin autorizacion expresa del usuario.
- No documentar ni versionar identificadores de pacientes, historias clinicas,
  resultados o respaldos de la base.
- `.env.local` contiene configuracion local y no debe publicarse.
- El NAS no ha sido desplegado y continua fuera de esta etapa.
- El respaldo previo a la migracion 0008 esta en
  `/tmp/muffin_before_0008.sql`. Es temporal y no debe versionarse.

## Servicios en ejecucion

- Frontend/proxy: `http://127.0.0.1:8877/MUFFIN/Login/Index`.
- API: `http://127.0.0.1:8000/api/v1`.
- Swagger: `http://127.0.0.1:8000/api/docs`.
- PostgreSQL: contenedor `muffin-postgres`.
- API: contenedor `muffin-api`.
- Frontend actual: proceso `python3 server.py`.
- Usuario rapido exclusivamente local: `admin` / `admin`.
- Institucion activa objetivo: `Hospital Sub Regional de Andahuaylas`.

Estado comprobado al cerrar esta sesion:

```text
muffin-api        healthy
muffin-postgres   healthy
frontend 8877     activo
```

## Arquitectura actual

- `server.py`: servidor del frontend heredado y proxy de compatibilidad entre
  rutas SIMCORE y la API MUFFIN.
- `mirror/`: HTML, JavaScript y assets del frontend capturado, servido bajo
  `/MUFFIN/`.
- `backend/app/`: FastAPI, modelos SQLAlchemy, schemas, servicios y routers.
- `backend/alembic/`: migraciones y datos versionados de catalogos.
- PostgreSQL 16: persistencia local.
- Docker Compose: `compose.yaml` + `compose.local.yaml` + `.env.local`.
- La arquitectura objetivo institucional esta definida en
  `docs/ARQUITECTURA_OBJETIVO_MUFFIN_ANDAHUAYLAS.md`.

La migracion vigente es:

```text
0008_ast_catalogs (head)
```

## Funcionalidad terminada

### Seguridad y usuarios

- JWT, Argon2, roles y permisos por area.
- Roles MUFFIN mapeados al frontend heredado.
- Permisos de validacion preliminar y final por area.
- Auditoria y eventos de flujo.
- El proxy reutiliza el JWT del navegador mediante `jQuery.ajaxPrefilter`.

### Interfaz general

- Branding MUFFIN, modo claro/oscuro y rutas `/MUFFIN/`.
- Datos visibles y capturados normalizados a mayusculas en tiempo real.
- La conversion a mayusculas conserva la posicion del cursor.
- UUID internos no se convierten a mayusculas.
- Edad calculada y de solo lectura.
- Medico mostrado como `MEDICO DE TURNO` cuando corresponde.

### Pacientes, ordenes y muestras

- Guardado y actualizacion de pacientes.
- Guardado de ordenes con procedencia, servicio, medico y observaciones.
- Catalogos de procedencias y servicios en espanol.
- Jerarquia Examen -> Muestra persistida por `0007_specimen_hierarchy`.
- Cinco grupos principales de muestras microbiologicas.
- Se rechazan agrupadores no terminales como muestras finales.
- Registro de toma, recepcion, destino y comentarios.
- Fechas historicas permitidas; se rechazan fechas futuras y recepcion anterior
  a toma.
- Se probo toma `2026-07-13` y recepcion `2026-07-14`, incluyendo recarga del
  formulario sin cambio de fecha.
- Las fechas se muestran en UTC-5 para evitar desplazamiento de dia.

### Ambito asistencial

El campo heredado `Tipo de localizacion` no representaba una localizacion
anatomica. Tampoco debe duplicar `Procedencia` o `Servicio`.

Ahora se muestra como `Ambito asistencial (derivado)`, de solo lectura. La API
lo calcula a partir de procedencia y servicio:

- `AMBULATORIO`
- `HOSPITALIZACION GENERAL`
- `CUIDADOS INTERMEDIOS`
- `CUIDADOS INTENSIVOS (UCI)`
- `URGENCIA`
- `DESCONOCIDO`

Reglas relevantes:

- `CONSULTA EXTERNA` con una especialidad neutral produce `AMBULATORIO`.
- `HOSPITALIZACION` con un servicio hospitalario produce hospitalizacion
  general.
- `UCI` prevalece sobre hospitalizacion general.
- Evidencia contradictoria produce `DESCONOCIDO`.
- `UCIN` permanece ambiguo hasta que el usuario confirme si significa cuidados
  intensivos o intermedios neonatales.

La derivacion esta en `backend/app/services.py`. No volver a guardar este dato
en `order_item.location`: ese campo corresponde a la ubicacion fisica o de flujo
de la muestra.

### Bandeja y resultados manuales

- `/api/v1/result-worklist` alimenta la bandeja de resultados.
- Busqueda por orden, paciente, examen, muestra y codigo de barras.
- Filtros por fecha, estado y resultado de cultivo.
- El selector derecho de la bandeja muestra estados de resultado de cultivo:
  positivo, negativo, no trajo muestra, muestra inadecuada y sin resultado.
- El proxy conserva compatibilidad con filtros por area si recibe un UUID de
  area heredado, pero la UI ya no expone ese selector en esta pantalla.
- Pacientes recibidos sin resultado aparecen como pendientes.
- Parametros dinamicos por examen cargan y guardan desde el frontend.
- Guardado en proceso, validacion preliminar, validacion final y reapertura.

### Identificacion y antibiograma

El formulario manual ya esta conectado a las entidades reales:

```text
result -> isolate -> organism
isolate -> ast_panel
ast_panel -> ast_panel_antibiotic -> antibiotic
isolate -> antimicrobial_result -> antibiotic
```

Funcionamiento verificado:

- Crear un aislado desde `Agregar Panel`.
- Seleccionar microorganismo y panel.
- Autocompletar filas AST desde el panel.
- Cargar aislados existentes al reabrir el formulario.
- Guardar recuento, fenotipo y comentario.
- Guardar CMI/valor, interpretacion, metodo y marca `No reportar`.
- Traducir `+/-` a `POS/NEG` en la API.
- Guardar AST antes de validar el resultado general.
- Invalidar validacion preliminar al modificar identificacion o AST.
- Bloquear cambios de aislados y AST despues de validacion final.
- Eliminar primero resultados AST hijos al borrar un aislado.

Se probo desde el frontend crear temporalmente `PANEL AST-N401`, leer sus 15
filas AST con interpretacion `S` y eliminar el aislado de prueba.

## Paneles AST cargados

La migracion `0008_ast_catalogs` cargo exactamente los paneles de
`SIMCORE_Paneles_y_Antibioticos.md`:

| Orden | Panel | Relaciones |
|---:|---|---:|
| 1 | PANEL SIN ATB | 0 |
| 10 | PANEL AST-N401 | 15 |
| 11 | PANEL AST-N402 | 12 |
| 13 | PANEL AST-N403 | 13 |
| 15 | PANEL AST-P663 | 17 |
| 16 | PANEL AST-ST03 | 17 |
| 17 | PANEL AST-YS08 | 5 |

Total activo: 7 paneles y 79 relaciones panel-antimicrobiano.

Se conservaron los ordenes SIMCORE repetidos. Para ello se elimino la
restriccion unica incorrecta sobre `(ast_panel_id, display_order)` y se dejo un
indice no unico.

El panel tecnico anterior `GN_URINE` permanece en la base solo por compatibilidad
con el caso ficticio, pero esta inactivo y no aparece en el desplegable.

La interpretacion predeterminada `S` se reprodujo exactamente desde SIMCORE.
Esto no constituye recomendacion clinica. Antes de produccion debe decidirse si
se mantiene este comportamiento o si se exige confirmacion explicita de cada
interpretacion segun CLSI/EUCAST y el instrumento.

## Catalogo de microorganismos

Fuente original: `lista.txt`, codificada en CP1252.

Resultado de depuracion:

- 2.540 filas logicas de origen.
- 5 filas JavaScript o vacias descartadas.
- 9 duplicados eliminados.
- 74 valores no cientificos puestos en cuarentena.
- 2.452 nombres cargados en la tabla operativa `organism`.

No se creo una segunda tabla operativa. La migracion carga los nombres en
`organism` con codigos deterministas y conserva las relaciones de `isolate`.

Archivos:

- `backend/scripts/build_organism_catalog.py`: generador reproducible.
- `backend/alembic/data/organisms_v1.json`: datos versionados para migracion.
- `docs/catalogo_microorganismos.sql`: exportacion independiente solicitada.
- `docs/catalogo_microorganismos_cuarentena.csv`: 74 valores separados.
- `docs/CATALOGO_MICROORGANISMOS_Y_AST.md`: criterios y modelo relacional.

El modal `Agregar Panel` recibe los 2.452 organismos y tiene un campo de busqueda
por nombre cientifico. La respuesta completa se midio en aproximadamente 235 ms
en local.

La depuracion no reemplaza una revision taxonomica. Se conservaron complejos,
grupos, identificaciones compuestas y posibles errores historicos para no
corregir silenciosamente datos clinicos.

## Verificaciones finales

- Alembic: `0008_ast_catalogs (head)`.
- Unit tests: `36 passed`.
- `Microbiology advanced smoke test passed.`.
- API health: correcto.
- Frontend: HTTP 200.
- Paneles visibles desde proxy: 7.
- Microorganismos visibles desde proxy: 2.452.
- Relaciones activas de panel: 79.
- Ambito de la orden manual actual: derivado correctamente como ambulatorio.
- Prueba frontend de agregar/eliminar panel: correcta.
- Prueba visual del formulario de resultados con Chrome headless e inspeccion de
  capturas: correcta. Se valido busqueda de microorganismo, catalogo de 7
  paneles, alta temporal de panel AST-N401, tabla AST de 15 filas, columnas
  `Antibiotico`, `Valor`, `Inter.`, `NR`, `ME`, botones principales y limpieza
  del aislado temporal.
- Se corrigio contraste de modo oscuro en controles y filas AST con estado, y
  una carrera de cierre en modales anidados al guardar paneles rapidamente.
- Se corrigio el menu de sesion en la barra lateral para que abra hacia arriba
  sin recortarse en escritorio.
- Se corrigio el layout de filtros de `Resultados` para que el selector de
  estado no se recorte, y el selector derecho ahora filtra por resultado de
  cultivo.
- La ruta heredada `/MUFFIN/Trans_pdf/Download_res_es?orden_id=...` ya no cae al
  stub local; genera una vista HTML imprimible del reporte de resultados con
  boton `Imprimir / guardar PDF`.
- Copia PostgreSQL previa a 0008: 277.799 bytes en `/tmp`.

## Archivos principales modificados recientemente

- `backend/alembic/versions/0008_ast_catalogs.py`
- `backend/alembic/data/ast_panels_v1.json`
- `backend/alembic/data/organisms_v1.json`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/services.py`
- `backend/app/routers/clinical.py`
- `backend/app/routers/results.py`
- `backend/app/routers/microbiology.py`
- `backend/app/seed.py`
- `backend/scripts/build_organism_catalog.py`
- `backend/scripts/microbiology_smoke_test.py`
- `backend/tests/test_ast_catalog_data.py`
- `backend/tests/test_care_setting.py`
- `backend/tests/test_clinical_schemas.py`
- `backend/tests/test_microbiology_schemas.py`
- `server.py`
- `mirror/MUFFIN/Content/muffin.css`
- `mirror/_pages/SIMCORE_WEB__Mic_orden_detalle__Resultado_microbiologia.html`
- `mirror/MUFFIN/Scripts/Views/Mic_orden_detalle_resultado_microbiologia.js`
- `tools/visual_validate_microbiology_form.py`

## Comandos de trabajo

Ejecutar desde `/home/workstation/Documentos/MUFFIN`.

Levantar o reconstruir API:

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml up -d --build api
```

Ver estado:

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml ps
```

Arrancar frontend manualmente:

```bash
python3 server.py
```

Arrancar frontend desacoplado:

```bash
setsid -f python3 server.py > /tmp/muffin_server.log 2>&1
```

Ejecutar pruebas unitarias dentro del contenedor:

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec -T api python -m pip install -r requirements-dev.txt
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec -T api python -m pytest
```

Ejecutar smoke de microbiologia:

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec -T api python scripts/microbiology_smoke_test.py
```

Regenerar catalogo de microorganismos:

```bash
python3 backend/scripts/build_organism_catalog.py
```

## Limitaciones y pendientes reales

### Prioridad alta

- Decidir con el responsable clinico si `S` puede ser valor predeterminado o si
  cada resultado AST debe requerir confirmacion explicita.
- Revisar taxonomicamente los 2.452 nombres antes de produccion.
- Confirmar el significado institucional de `UCIN`.

### Integracion incompleta

- La pantalla independiente de mantenimiento de paneles heredada no esta
  completamente adaptada para altas, ediciones y bajas. El listado usado por
  `Agregar Panel` si funciona y los siete paneles ya estan cargados.
- El boton `Enviar al Instrumento` sigue siendo un stub; no existe transporte
  VITEK real ni procesamiento automatico de mensajes entrantes.
- El guardado AST del proxy realiza varias llamadas API y no es una transaccion
  atomica unica; una falla intermedia puede requerir reintento.
- La pantalla `Reportes > Produccion` todavia no esta conectada, aunque los
  estados necesarios ya existen en la base.
- Mantenedores heredados de algunos catalogos conservan diferencias de campos y
  metodos; validar cada uno antes de considerarlo terminado.

### Datos y despliegue

- No desplegar al NAS todavia.
- No cargar datos clinicos adicionales hasta revisar permisos, respaldos,
  exportaciones y reporte final.
- No versionar `data`, dumps, `.env.local` ni identificadores clinicos.

## Siguiente paso recomendado

1. Resolver la politica clinica del valor predeterminado `S`.
2. Adaptar la pantalla de mantenimiento de paneles o reemplazarla por una UI
   MUFFIN directa que use los endpoints existentes.
3. Conectar el reporte de produccion.
4. Implementar VITEK solo despues de definir contrato, cola, reintentos,
   trazabilidad y validacion de codigos.
