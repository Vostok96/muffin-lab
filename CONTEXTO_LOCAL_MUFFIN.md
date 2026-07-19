# Contexto local MUFFIN

Ubicación local:

```text
/home/workstation/Documentos/MUFFIN
```

Repositorio:

```text
https://github.com/Vostok96/muffin-lab.git
```

Ramas relevantes:

- `main`: MUFFIN padre.
- `cliente-andahuaylas`: variante Hospital Sub Regional de Andahuaylas.

## Qué es MUFFIN

MUFFIN es una plataforma para microbiología hospitalaria. Integra un frontend heredado SIMCORE servido bajo `/MUFFIN/`, un backend FastAPI/PostgreSQL y un proxy de compatibilidad en `server.py`.

Funcionalidades actuales:

- Login con JWT.
- Gestión de pacientes.
- Órdenes y detalles de exámenes.
- Procedencia, servicio y médico.
- Generación de número de orden y código de barras.
- Recepción/verificación de muestras.
- Resultados microbiológicos.
- Identificación de microorganismo.
- Antibiograma por panel, panel manual y `PANEL SIN ATB`.
- Validación preliminar/final.
- Reporte imprimible/PDF con firma del validador final.
- Dashboard con conteos operativos.
- Modo claro/oscuro.
- Branding por cliente vía variables y carpeta `CLIENTES/`.

## Estructura útil

- `server.py`: servidor frontend, proxy, branding, PDF, dashboard y caché.
- `backend/app/`: API.
- `backend/alembic/versions/`: migraciones.
- `backend/app/seed.py`: catálogos base y datos de desarrollo.
- `backend/scripts/prepare_andahuaylas_production.py`: preparación idempotente del cliente Andahuaylas.
- `mirror/_pages/`: HTML heredado capturado.
- `mirror/MUFFIN/Scripts/Views/`: JS de pantallas.
- `mirror/MUFFIN/Content/muffin.css`: capa visual MUFFIN.
- `CLIENTES/_plantilla/`: molde de nuevo cliente.
- `CLIENTES/Hospital Sub Regional Andahuaylas/`: perfil del cliente Andahuaylas.
- `docs/MUFFIN_PADRE.md`: guía técnica del core.
- `docs/CLIENTE_ANDAHUAYLAS.md`: guía del despliegue Andahuaylas.

## Ejecución local

Frontend local:

```bash
python3 server.py
```

Abrir:

```text
http://127.0.0.1:8877/MUFFIN/
```

Stack Docker local/NAS:

```bash
docker compose up -d --build
docker compose ps
```

API:

```text
http://127.0.0.1:8000/api/v1/health
```

## Cliente Andahuaylas

Dominio:

```text
https://andahuaylas.microbiolog-ia.com/MUFFIN/
```

NAS:

```text
/volume1/docker/muffin-andahuaylas/source
```

Contenedores:

- `muffin-postgres`
- `muffin-api`
- `muffin-frontend`

El `.env` real y contraseñas no se guardan en este repositorio.

## Catálogos importantes

Base:

- Exámenes: urocultivo, coprocultivo, hemocultivo, cultivo de secreciones, otros cultivos/términos generales.
- Muestras: jerarquía en `EXAM_SPECIMEN_HIERARCHY`.
- Contenedor base: `CONTENEDOR SEGUN PROTOCOLO`.
- Destino base: `MESA DE MICROBIOLOGIA`.
- Resultado de cultivo: negativo, positivo, no trajo muestra, muestra inadecuada.
- Gram: cocos Gram positivos, bacilos Gram negativos, levaduras.
- Nitrito: opcional.
- Recuento: 1,000 a 100,000 UFC/mL.
- Método AST por defecto: `DISCO`.

Andahuaylas:

- Procedencias: consulta externa, emergencia, hospitalización, referido, UCI.
- Servicios: lista en `backend/scripts/prepare_andahuaylas_production.py`.
- Médico: solo `MEDICO DE TURNO`.

## Agregar nuevo cliente

1. Crear rama desde `main`.
2. Crear carpeta `CLIENTES/<Nombre Institucion>`.
3. Copiar `CLIENTES/_plantilla/README.md` como guía.
4. Agregar logo y assets permitidos.
5. Crear `signers.json` si habrá firmas en PDF.
6. Colocar firmas reales en `CLIENTES/<cliente>/usuarios/` sin versionarlas.
7. Configurar `.env` con `DEFAULT_INSTITUTION_*`, `MUFFIN_CLIENT_ROOT`, logos y owner.
8. Crear script/migración idempotente si hay catálogo institucional propio.
9. Ejecutar smoke funcional completo antes de producción.
10. Documentar el cliente en `docs/CLIENTE_<NOMBRE>.md` y en su carpeta.

## Agregar exámenes

Ruta técnica:

1. Agregar `Exam`.
2. Agregar `SpecimenType`.
3. Relacionar `ExamSpecimenType`.
4. Agregar o reutilizar `ParameterDefinition`.
5. Relacionar `ExamParameter`.
6. Definir `barcode_suffix`.
7. Crear migración Alembic o script idempotente.
8. Probar orden, recepción, resultado, validación y PDF.

Para cultivos nuevos, reutilizar los parámetros `CULTURE_*` salvo que el examen necesite lógica distinta.

## Agregar usuarios

Roles:

- `ADMIN`
- `PROCESS_ADMIN`
- `PROCESSOR`
- `ENTRY`
- `CONSULTANT`
- `COLLECTOR`
- `CLINICIAN`

Para validar, además del rol, el usuario necesita permiso de área `MICROBIOLOGY` con validación preliminar/final.

Para firmar reportes, agregarlo a `signers.json` y poner su imagen local en `usuarios/`.

## Backup y migración

Backup:

```bash
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --file=/tmp/muffin.backup
docker compose cp postgres:/tmp/muffin.backup ./muffin.backup
```

Restore:

```bash
docker compose up -d postgres
docker compose cp ./muffin.backup postgres:/tmp/muffin.backup
docker compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/muffin.backup
docker compose up -d --build api frontend
```

Copiar también:

- `.env` productivo por canal seguro.
- Carpeta `CLIENTES/<cliente>/usuarios/`.
- Assets locales no versionados.
- Exportaciones/PDF externos si se habilitan.

## Validación antes de commit/despliegue

```bash
python3 -m py_compile server.py
node --check mirror/MUFFIN/Scripts/Views/Mic_orden_detalle_resultado_microbiologia.js
git status --short
```

Cuando Docker/API estén activos:

```bash
docker compose exec api pytest
```

## Reglas de seguridad

- No guardar contraseñas en MD.
- No versionar `.env`.
- No subir datos clínicos, dumps, bases locales ni PDFs reales.
- No subir firmas/sellos reales.
- Mantener PostgreSQL fuera de exposición pública.
- Cambios generales vuelven a `main`; cambios de marca quedan en rama/perfil de cliente.
