# Cliente: Hospital Sub Regional de Andahuaylas

Esta variante es el primer despliegue institucional de MUFFIN. Debe mantenerse como rama/perfil de cliente sobre MUFFIN padre.

## Identidad

- Institución: Hospital Sub Regional de Andahuaylas.
- Slug: `hospital-sub-regional-andahuaylas`.
- Dominio público: `andahuaylas.microbiolog-ia.com`.
- Producto: MUFFIN Microbiología Hospitalaria.
- Versión visible: `1.0`.
- Propiedad intelectual de MUFFIN: RyM SAC.

Insumos:

- Logo institucional: `CLIENTES/Hospital Sub Regional Andahuaylas/logo andahuylas.png`.
- Captura web de referencia: `CLIENTES/Hospital Sub Regional Andahuaylas/pagina web del hospital.png`.
- Perfil local: `CLIENTES/Hospital Sub Regional Andahuaylas/README.md`.
- Firmantes: `CLIENTES/Hospital Sub Regional Andahuaylas/signers.json`.
- Firmas reales: `CLIENTES/Hospital Sub Regional Andahuaylas/usuarios/` ignorado por git.

## Variables de despliegue

El `.env` del NAS debe contener, además de secretos:

```env
DEFAULT_INSTITUTION_NAME=Hospital Sub Regional de Andahuaylas
DEFAULT_INSTITUTION_SLUG=hospital-sub-regional-andahuaylas
MUFFIN_CLIENT_ROOT=CLIENTES/Hospital Sub Regional Andahuaylas
MUFFIN_BRAND_IMAGE=CLIENTES/Hospital Sub Regional Andahuaylas/logo andahuylas.png
MUFFIN_PRODUCT_IMAGE=MUFFIN_ICONO.jpg
MUFFIN_MASCOT_IMAGE=MUFFIN_SINFONDO.png
MUFFIN_SIGNERS_CONFIG=CLIENTES/Hospital Sub Regional Andahuaylas/signers.json
MUFFIN_COPYRIGHT_OWNER=Hospital Sub Regional de Andahuaylas
MUFFIN_IP_OWNER=RyM SAC
MUFFIN_VERSION=1.0
```

## Usuarios productivos iniciales

No documentar contraseñas. Las credenciales se entregan por canal operativo y deben rotarse.

- `admin-hsr`: administrador.
- `kpena`: Katherine Mariely Peña Vega, CBP 16728, valida y firma.
- `rcalderon`: Ruth N. Calderon De La Cruz, CBP 17484, valida y firma.
- `wsalazar`: Wilder Salazar, solo lectura de resultados (`CONSULTANT`).

Regla de firma: el PDF muestra solo la firma del usuario que realizó la validación final. Nunca deben aparecer dos firmas juntas en un resultado.

## Catálogo institucional

Procedencias activas:

- `CONSULTA EXTERNA`
- `EMERGENCIA`
- `HOSPITALIZACIÓN`
- `REFERIDO`
- `UCI`

Servicios activos:

- `ALOJAMIENTO CONJUNTO`
- `CARDIOLOGIA`
- `CENTRO OBSTETRICO`
- `CIRUGIA GENERAL`
- `CIRUGIA PEDIATRICA`
- `DERMATOLOGIA`
- `ENDOCRINOLOGIA`
- `GASTROENTEROLOGIA`
- `GINECOLOGIA`
- `HOSP. CIRUGIA`
- `HOSP. GINECO-OBSTETRICIA`
- `HOSP. MEDICINA`
- `HOSP. NEO I`
- `HOSP. NEO II`
- `HOSP. PEDIATRIA`
- `MEDICINA FISICA Y REHABILITACION`
- `MEDICINA INTERNA`
- `NEUMOLOGIA`
- `NEUROCIRUGIA`
- `NEUROLOGIA`
- `OBSTETRICIA`
- `ODONTOLOGIA`
- `ODONTO-PEDIATRIA`
- `OFTALMOLOGIA`
- `ONCOLOGIA`
- `OTORRINOLARINGOLOGIA`
- `PAGANTES`
- `PEDIATRIA`
- `PROGRAMA DE ETS/VIH-SIDA`
- `PROGRAMA DE TUBERCULOSIS`
- `PSICOLOGIA`
- `PSIQUIATRIA`
- `REFERENCIA`
- `REPOSO EMERGENCIA`
- `REUMATOLOGIA`
- `SALA DE OPERACIONES`
- `SALUD MENTAL`
- `TOPICO CIRUGIA`
- `TOPICO GINECO-OBSTETRICIA`
- `TOPICO MEDICINA`
- `TOPICO PEDIATRIA`
- `TRAUMA SHOK`
- `TRAUMATOLOGIA`
- `UCI`
- `UCIN`
- `UROLOGIA`

Médico activo para nuevas órdenes: `MEDICO DE TURNO`.

Los catálogos se cargan y restringen con:

- `backend/scripts/prepare_andahuaylas_production.py`
- `backend/alembic/versions/0010_andahuaylas_catalogs.py`
- `backend/alembic/versions/0011_andahuaylas_catalog_cleanup.py`

Las opciones fuera del catálogo oficial se desactivan, no se eliminan.

## Flujo clínico validado

- Crear paciente/orden.
- Buscar paciente por HC.
- Autogenerar número de orden.
- Autogenerar código de barras por detalle.
- Seleccionar examen/muestra desde listas heredadas del padre.
- Recepcionar/verificar muestra.
- Registrar resultado negativo, positivo, rechazado o en proceso.
- Agregar identificación con panel AST.
- Usar `PANEL SIN ATB` para identificación sola o antibióticos manuales.
- Validar preliminar/final.
- Imprimir/reporte PDF desde sesión autenticada.

## Reglas de resultado

- Estado final del reporte:
  - `FINALIZADO` si hay validación final.
  - `RECHAZADO` si el resultado indica no trajo muestra o muestra inadecuada.
  - `EN PROCESO` si está registrado/guardado sin final.
- Nitrito es opcional.
- `COLORACIÓN GRAM`: cocos Gram positivos, bacilos Gram negativos, levaduras.
- Recuento: 1,000 a 100,000 UFC/mL.
- AST por defecto: `DISCO`, valor `-`.
- AST `CMI`: permite valor editable.
- `NR`: antibiótico no reportado, se omite del PDF.

## Despliegue actual

NAS:

- Proyecto: `/volume1/docker/muffin-andahuaylas/source`.
- Contenedores: `muffin-postgres`, `muffin-api`, `muffin-frontend`.
- Frontend expuesto por Cloudflare Tunnel hacia puerto NAS configurado.
- Servicios Docker con `restart: unless-stopped`.
- Ultima reconstruccion verificada: 2026-08-13.
- Estado verificado: `muffin-api` healthy, `muffin-frontend` healthy,
  `muffin-postgres` healthy.
- Health publico verificado:
  `https://andahuaylas.microbiolog-ia.com/api/v1/health`.

Notas productivas recientes:

- `wsalazar` fue verificado con rol `CONSULTANT`, sin permisos de area. Un
  intento de validacion final con item falso devolvio HTTP 403, por bloqueo de
  rol antes de acceder a un resultado real.
- El rol `CONSULTANT` solo debe visualizar/buscar resultados. No debe guardar,
  validar, finalizar, borrar resultado ni editar identificacion/antibiograma.
- La UI de ordenes permite eliminar pacientes para roles autorizados; el backend
  bloquea pacientes con resultados finales validados.
- La UI de ordenes permite retirar examenes registrados por error mediante
  cancelacion trazable. No usar borrado fisico para ese flujo.
- Si aparecen nombres como `, ` en listados, primero revisar carga/paginacion del
  proxy. El incidente del 2026-08-13 fue por limite de 100 pacientes con una base
  productiva de 212 pacientes, no por filas corruptas.

Comandos útiles:

```bash
docker compose ps
docker compose logs --tail=100 frontend
docker compose logs --tail=100 api
docker compose up -d --build frontend
docker compose up -d --build api frontend
```

## Backup y migración

Backup lógico:

```bash
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --file=/tmp/muffin-andahuaylas.backup
docker compose cp postgres:/tmp/muffin-andahuaylas.backup ./muffin-andahuaylas.backup
```

Además copiar por canal seguro:

- `.env` productivo.
- `CLIENTES/Hospital Sub Regional Andahuaylas/usuarios/`.
- Cualquier storage externo de PDF/exportaciones si se activa.

Restore:

```bash
docker compose up -d postgres
docker compose cp ./muffin-andahuaylas.backup postgres:/tmp/muffin-andahuaylas.backup
docker compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/muffin-andahuaylas.backup
docker compose up -d --build api frontend
```

## Rendimiento observado

Medición pública posterior a optimización:

- HTML resultados: alrededor de 430 ms.
- Bundle pesado `PluginsJS`: alrededor de 570 ms con `CF-Cache-Status: HIT`.
- CSS/JQuery/JS de resultados: cacheados por Cloudflare con Brotli.

Siguiente mejora si el volumen crece mucho: paginación server-side real en `/result-worklist`.

## Cuidado para próximos cambios

- No subir datos clínicos ni pruebas productivas.
- No dejar órdenes QA en producción.
- No versionar contraseñas ni `.env`.
- No subir sellos/firma reales.
- Si aparece una mejora genérica, portarla a `main`/MUFFIN padre.
