# MUFFIN padre - guía de continuidad

MUFFIN padre es el molde común para desplegar microbiología hospitalaria en distintas instituciones. El core debe conservar flujos, catálogos base, backend, seguridad, reportes y compatibilidad del frontend heredado. Cada cliente solo debe cambiar identidad visual, catálogos institucionales puntuales, usuarios y operación.

## Arquitectura

- `server.py`: frontend/proxy compatible con rutas `/MUFFIN/...`. Sirve el mirror heredado, inyecta sesión, tema, footer, branding, rutas de PDF, dashboard y proxy a FastAPI.
- `mirror/`: HTML, CSS y JS heredados de SIMCORE adaptados para MUFFIN.
- `backend/`: API FastAPI con SQLAlchemy, Alembic, PostgreSQL, JWT, roles, permisos, auditoría, catálogos, órdenes, resultados y reportes.
- `docs/login.html`: login MUFFIN contra `POST /api/v1/auth/login`.
- `CLIENTES/`: perfiles e insumos por institución. El padre no debe depender de una institución específica.
- `compose.yaml`: despliegue Docker con `postgres`, `api` y `frontend`.

## Perfil de cliente

La identidad institucional se configura por entorno, no por edición directa del core.

Variables principales:

```env
DEFAULT_INSTITUTION_NAME=Nombre Legal de la Institución
DEFAULT_INSTITUTION_SLUG=nombre-institucion
MUFFIN_CLIENT_ROOT=CLIENTES/Nombre Institucion
MUFFIN_BRAND_IMAGE=CLIENTES/Nombre Institucion/logo.png
MUFFIN_PRODUCT_IMAGE=MUFFIN_ICONO.jpg
MUFFIN_MASCOT_IMAGE=MUFFIN_SINFONDO.png
MUFFIN_SIGNERS_CONFIG=CLIENTES/Nombre Institucion/signers.json
MUFFIN_PRODUCT_NAME=MUFFIN Microbiología Hospitalaria
MUFFIN_PRODUCT_TAGLINE=Microbiología: Unidad de Fuentes, Flujos e Informes Nosocomiales
MUFFIN_COPYRIGHT_OWNER=Nombre Legal de la Institución
MUFFIN_IP_OWNER=RyM SAC
MUFFIN_VERSION=1.0
```

Plantilla: `CLIENTES/_plantilla/README.md`.

Firmantes: `signers.json` define usuario, nombre, credencial y ruta local del sello/firma. Las imágenes reales van en `CLIENTES/<cliente>/usuarios/`, carpeta ignorada por git.

## Catálogos base

Los catálogos base están en `backend/app/seed.py` y migraciones Alembic.

- Áreas: `MICROBIOLOGY`, `RECEPTION`.
- Procedencias mínimas base: `HOSPITALIZACION`, `UCI`. Las variantes pueden ampliar/restringir.
- Servicio mínimo base: `EMERGENCIA`, `UCI`. Las variantes pueden ampliar/restringir.
- Médico predeterminado: `MEDICO DE TURNO`.
- Destino operativo: `MICROBIOLOGY_BENCH` / `MESA DE MICROBIOLOGIA`.
- Contenedor base: `CONTENEDOR_PROTOCOLO` / `CONTENEDOR SEGUN PROTOCOLO`.
- Exámenes base: `UROCULTIVO`, `COPROCULTIVO`, `HEMOCULTIVO`, `CULTIVO DE SECRECIONES`, `OTROS CULTIVOS / TÉRMINOS GENERALES`.
- Muestras: jerarquía por examen en `EXAM_SPECIMEN_HIERARCHY`.
- Microorganismos: catálogo amplio cargado en `backend/alembic/versions/0008_ast_catalogs.py` desde `backend/app/data/organisms_v1.json`, más opciones `sp.` para géneros frecuentes.
- Antibióticos/paneles: catálogo AST base y paneles heredados; método por defecto `DISCO`.

Catálogo institucional: debe ir en un script propio del cliente o migración idempotente. No eliminar históricos; desactivar opciones no oficiales si solo se quiere restringir nuevas órdenes.

## Flujo funcional

1. Login con JWT.
2. Registro de paciente y orden.
3. Selección de procedencia, servicio, médico, examen y muestra.
4. Código de barras autogenerado por orden/detalle.
5. Verificación/recepción de muestra.
6. Registro de resultado microbiológico.
7. Identificación de microorganismo.
8. Antibiograma por panel o panel sin ATB.
9. Validación preliminar/final.
10. Reporte imprimible/PDF autenticado.

Estados de reporte:

- `FINALIZADO`: cultivo validado final.
- `RECHAZADO`: no trajo muestra o muestra inadecuada.
- `EN PROCESO`: registrado/guardado sin validación final.

Métodos:

- Resultado de cultivo positivo: `CULTIVO MANUAL`.
- Gram: `TINCION GRAM`.
- Nitrito: `TIRA REACTIVA`.
- AST `DISCO`: valor `-`.
- AST `CMI`: valor editable.

## Resultado microbiológico

Parámetros de cultivo para todos los cultivos:

- `RESULTADO DEL CULTIVO`: negativo, positivo, no trajo muestra, muestra inadecuada.
- `OBSERVACIONES`: texto libre.
- `COLORACIÓN GRAM`: cocos Gram positivos, bacilos Gram negativos, levaduras.
- `PRUEBA DE NITRITO`: opcional.
- `RECUENTO DE COLONIAS`: 1,000 a 100,000 UFC/mL.

Reglas AST:

- Antibióticos en mayúsculas en pantalla y reporte.
- `NR` omite el antibiótico del reporte final.
- `PANEL SIN ATB` permite dos escenarios: identificación sola sin antibiograma, o identificación con antibióticos manuales agregados por el usuario.
- El catálogo de microorganismos y antibióticos usa búsqueda paginada/debounced para no congelar el navegador.

## Cómo agregar exámenes

Opción operativa: usar mantenimiento de exámenes en el frontend si la pantalla está habilitada para el rol.

Opción técnica:

1. Crear o actualizar `Exam` con `code`, `name`, `barcode_suffix`, área y flags.
2. Crear `SpecimenType` y relacionar en `ExamSpecimenType`.
3. Crear parámetros en `ParameterDefinition`.
4. Relacionar parámetros al examen en `ExamParameter` con `display_order` e `is_required`.
5. Si es cultivo, reutilizar los parámetros `CULTURE_*`.
6. Hacerlo mediante migración Alembic o script idempotente de cliente.
7. Probar creación de orden, recepción, resultado, validación y PDF.

## Cómo agregar usuarios

Opción operativa: mantenimiento de usuarios.

Opción técnica/API:

- Crear usuario en `/api/v1/admin/users`.
- Asignar roles: `ADMIN`, `PROCESS_ADMIN`, `PROCESSOR`, `ENTRY`, `CONSULTANT`, `COLLECTOR`, `CLINICIAN`.
- Para validar resultados, asignar permiso de área `MICROBIOLOGY` con `can_preliminary_validate` y/o `can_final_validate`.
- Para firmar PDF, agregar el usuario al `signers.json` del cliente y colocar su sello/firma en carpeta local ignorada.

Nunca guardar contraseñas reales en documentos o git.

## Backups y migración

Backup lógico desde NAS:

```bash
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --file=/tmp/muffin.backup
docker compose cp postgres:/tmp/muffin.backup ./muffin.backup
```

Restore en nuevo NAS:

```bash
docker compose up -d postgres
docker compose cp ./muffin.backup postgres:/tmp/muffin.backup
docker compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/muffin.backup
docker compose up -d --build api frontend
```

Además del backup de PostgreSQL, copiar:

- `.env` productivo por canal seguro.
- `CLIENTES/<cliente>/usuarios/` con firmas/sellos.
- Assets institucionales no versionados.
- Reportes/PDF externos si se decide persistirlos fuera de la base.

## Seguridad

- `APP_ENV=production` exige `JWT_SECRET` fuerte.
- Contraseñas con `pwdlib.PasswordHash.recommended()`.
- JWT Bearer con expiración.
- API y frontend detrás de HTTPS/Cloudflare Tunnel.
- PostgreSQL no debe exponerse públicamente.
- Usuarios demo desactivados en producción.
- No subir `.env`, dumps, bases locales, firmas o datos clínicos.

## Rendimiento

- Assets versionados con `Cache-Control: public, max-age=31536000, immutable`.
- Bundles heredados se sirven con alias `.css`/`.js` para que Cloudflare los cachee.
- Catálogos GET se cachean en `server.py`.
- Resultados usa DataTables con `deferRender`.
- Si la tabla crece a miles de registros por rango, siguiente paso: paginación server-side real en `/result-worklist`.

## Validación recomendada

```bash
python3 -m py_compile server.py
node --check mirror/MUFFIN/Scripts/Views/Mic_orden_detalle_resultado_microbiologia.js
docker compose exec api pytest
```

Smoke funcional mínimo:

- Login.
- Buscar paciente por HC.
- Crear orden con cada procedencia/servicio activo relevante.
- Recepción de muestra.
- Resultado negativo.
- Resultado positivo con panel AST.
- Resultado positivo con `PANEL SIN ATB` sin antibióticos.
- Resultado positivo con `PANEL SIN ATB` y antibióticos manuales.
- Rechazo por no trajo muestra/muestra inadecuada.
- Validación final por usuario autorizado.
- PDF con una sola firma.

## Reglas para futuros agentes

- Llevar mejoras generales de clientes de vuelta al padre.
- No hardcodear nombres/logos de clientes en el core.
- Toda personalización debe quedar en `.env`, `CLIENTES/<cliente>/` o script/migración institucional.
- Mantener commits pequeños y documentar decisiones clínicas.
- No versionar datos reales ni secretos.
