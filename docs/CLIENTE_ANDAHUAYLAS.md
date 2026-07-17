# Variante institucional: Hospital Sub Regional de Andahuaylas

Esta rama deriva de MUFFIN padre y direcciona el producto al primer cliente institucional.

## Institución

- Nombre: Hospital Sub Regional de Andahuaylas
- Slug: `hospital-sub-regional-andahuaylas`
- Producto: MUFFIN Microbiología Hospitalaria

## Insumos usados

- Logo institucional: `CLIENTES/Hospital Sub Regional Andahuaylas/logo andahuylas.png`
- Captura web de referencia: `CLIENTES/Hospital Sub Regional Andahuaylas/pagina web del hospital.png`

La captura web se conserva solo como referencia visual. La primera personalización usa principalmente el logo institucional y el nombre oficial.

## Cambios aplicados

- `server.py`
  - `BRAND_IMAGE` apunta al logo institucional.
  - Footer corporativo identifica al Hospital Sub Regional de Andahuaylas.
  - Reporte de resultados muestra logo y nombre del hospital.

- `docs/login.html`
  - Login muestra logo institucional y nombre completo.
  - Subtítulo mantiene el producto MUFFIN.

- `mirror/MUFFIN/Content/muffin.css`
  - Navbar/sidebar muestra `H.S.R. ANDAHUAYLAS`.
  - Logo se renderiza con `object-fit: contain` para no recortar el emblema.

- `backend/app/config.py`
  - Defaults de institución apuntan al Hospital Sub Regional de Andahuaylas.

- `.env.example` y `.env.local.example`
  - Defaults de institución alineados a la variante.

## Límites

- No se suben fotos de usuarios ni documentos personales.
- `CLIENTES/**/usuarios/` está ignorado por git.
- MUFFIN padre sigue siendo `main`; esta variante vive en rama de cliente.

## Siguientes ajustes posibles

- Ajustar paleta completa con base en el manual visual institucional, si existe.
- Cambiar favicon a emblema del hospital si el cliente lo solicita.
- Agregar textos legales específicos de la institución.
- Preparar `.env` productivo con secretos únicos antes de desplegar.
