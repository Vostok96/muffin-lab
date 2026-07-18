# Variante institucional: Hospital Sub Regional de Andahuaylas

Esta rama deriva de MUFFIN padre y direcciona el producto al primer cliente institucional.

## Institución

- Nombre: Hospital Sub Regional de Andahuaylas
- Slug: `hospital-sub-regional-andahuaylas`
- Producto: MUFFIN Microbiología Hospitalaria

## Insumos usados

- Logo institucional: `CLIENTES/Hospital Sub Regional Andahuaylas/logo andahuylas.png`
- Captura web de referencia: `CLIENTES/Hospital Sub Regional Andahuaylas/pagina web del hospital.png`
- Sellos/firma locales ignorados por git:
  - `CLIENTES/Hospital Sub Regional Andahuaylas/usuarios/Katherine Mariely Peña Vega/KATHERINE.jpeg`
  - `CLIENTES/Hospital Sub Regional Andahuaylas/usuarios/Ruth N. Calderon De La Cruz/RUTH.jpeg`

La captura web se conserva solo como referencia visual. La primera personalización usa principalmente el logo institucional y el nombre oficial.

## Cambios aplicados

- `server.py`
  - `BRAND_IMAGE` apunta al logo institucional.
  - `/MUFFIN_PRODUCTO.jpg` sirve el logo propio de MUFFIN para piezas corporativas secundarias.
  - `/MUFFIN_MASCOTA.png` sirve la mascota MUFFIN sin fondo para el sidebar.
  - Footer corporativo identifica al Hospital Sub Regional de Andahuaylas.
  - Reporte de resultados muestra logo y nombre del hospital.
  - Reporte imprimible incluye bloque de responsables autorizadas con sello/firma:
    - Katherine Mariely Peña Vega, CBP 16728.
    - Ruth N. Calderon De La Cruz, CBP 17484.
  - `/MUFFIN/Dashboard/Resumen` entrega conteos operativos del día y últimos 7 días para la portada.

- `mirror/_pages/SIMCORE_WEB__Home__Index.html`
  - Portada prioriza el nombre y logo del Hospital Sub Regional de Andahuaylas.
  - Portada reemplaza secciones de demostración por conteos de producción.
  - Los valores se actualizan automáticamente contra `/MUFFIN/Dashboard/Resumen`.
  - Las tarjetas de conteo son solo informativas, no enlaces de navegación.

- `docs/login.html`
  - Login muestra logo institucional y nombre completo.
  - Subtítulo mantiene el producto MUFFIN.
  - Footer de login muestra logo MUFFIN, significado y propiedad intelectual de RyM SAC.

- `mirror/MUFFIN/Content/muffin.css`
  - Navbar/sidebar muestra `MUFFIN` con el logo de MUFFIN como marca superior.
  - Nombre institucional se muestra centrado, con logo del hospital, en un bloque propio debajo de `Reportes`.
  - Mascota MUFFIN se muestra sin fondo debajo de la tarjeta institucional y salta levemente al hover.
  - Logo se renderiza con `object-fit: contain` para no recortar el emblema.

- `backend/app/config.py`
  - Defaults de institución apuntan al Hospital Sub Regional de Andahuaylas.

- `backend/scripts/prepare_andahuaylas_production.py`
  - Carga idempotente del catálogo institucional de Andahuaylas:
    - 5 procedencias oficiales.
    - 46 servicios oficiales.
  - Los códigos se normalizan sin tildes para estabilidad técnica; los nombres visibles se conservan como catálogo institucional.

- `backend/alembic/versions/0010_andahuaylas_catalogs.py`
  - Aplica el mismo catálogo institucional durante `alembic upgrade head`.
  - Deja solo `MEDICO_TURNO` como médico activo para nuevas órdenes.
  - No elimina valores existentes; solo desactiva médicos distintos a `MEDICO_TURNO` para nuevas órdenes.

- `.env.example` y `.env.local.example`
  - Defaults de institución alineados a la variante.

## Catálogos Institucionales

- Procedencias oficiales: `CONSULTA EXTERNA`, `EMERGENCIA`, `HOSPITALIZACIÓN`, `REFERIDO`, `UCI`.
- Servicios oficiales: cargados desde `ANDAHUAYLAS_SERVICES` en `backend/scripts/prepare_andahuaylas_production.py`.
- Médico activo para órdenes: `MEDICO DE TURNO`.
- La carga no elimina valores existentes; en médicos desactiva valores distintos a `MEDICO_TURNO` para evitar opciones duplicadas.

## Límites

- No se suben fotos de usuarios ni documentos personales.
- `CLIENTES/**/usuarios/` está ignorado por git.
- MUFFIN padre sigue siendo `main`; esta variante vive en rama de cliente.
- Las contraseñas iniciales de usuarios se entregan por canal operativo y no se documentan en el repositorio.

## Siguientes ajustes posibles

- Ajustar paleta completa con base en el manual visual institucional, si existe.
- Cambiar favicon a emblema del hospital si el cliente lo solicita.
- Agregar textos legales específicos de la institución.
- Preparar `.env` productivo con secretos únicos antes de desplegar.
