# Hospital Sub Regional de Andahuaylas

Perfil institucional del primer despliegue productivo de MUFFIN.

## Identidad

- Institución: Hospital Sub Regional de Andahuaylas
- Slug: `hospital-sub-regional-andahuaylas`
- Carpeta de cliente: `CLIENTES/Hospital Sub Regional Andahuaylas`
- Logo institucional: `logo andahuylas.png`
- Producto: MUFFIN Microbiología Hospitalaria
- Propiedad intelectual de MUFFIN: RyM SAC
- Versión visible: `1.0`

## Variables de entorno usadas

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

Si el `.env` productivo solo tiene `DEFAULT_INSTITUTION_NAME` con Andahuaylas, `server.py` mantiene compatibilidad buscando esta carpeta como fallback.

## Firmantes autorizadas

El archivo `signers.json` contiene metadatos versionables. Las imágenes reales están en `usuarios/` y esa carpeta está ignorada por git.

- `kpena`: Katherine Mariely Peña Vega, CBP 16728.
- `rcalderon`: Ruth N. Calderon De La Cruz, CBP 17484.

Regla de reporte: solo aparece la firma de quien realizó la validación final. Si no se puede resolver el usuario validador o falta el archivo de firma, el reporte se imprime sin bloque de firma.

## Catálogo institucional

El catálogo de procedencias/servicios de Andahuaylas se carga con `backend/scripts/prepare_andahuaylas_production.py` y con las migraciones `0010`/`0011` existentes en esta rama.

- Procedencias: `CONSULTA EXTERNA`, `EMERGENCIA`, `HOSPITALIZACIÓN`, `REFERIDO`, `UCI`.
- Médico activo para órdenes: `MEDICO DE TURNO`.
- Servicios: ver constante `ANDAHUAYLAS_SERVICES` en `backend/scripts/prepare_andahuaylas_production.py`.

Las opciones no oficiales se desactivan para nuevas órdenes, pero no se eliminan para no romper históricos.
