# Plantilla de cliente MUFFIN

Use esta carpeta como molde para una nueva institución. No coloque aquí datos clínicos, credenciales ni firmas reales versionadas.

## Archivos esperados

- `logo.png`: logo principal de la institución. Se sirve como `/MUFFIN_ICONO.jpg`.
- `mascota.png`: opcional. Si no se define, MUFFIN usa su icono de producto.
- `signers.json`: opcional. Define responsables autorizados y rutas locales de sus sellos/firma.
- `usuarios/`: carpeta local ignorada por git para sellos/firma digitalizados.

## Variables de entorno

Configure estas variables en `.env` del despliegue:

```env
DEFAULT_INSTITUTION_NAME=Nombre Legal de la Institución
DEFAULT_INSTITUTION_SLUG=nombre-institucion
MUFFIN_CLIENT_ROOT=CLIENTES/Nombre Institucion
MUFFIN_BRAND_IMAGE=CLIENTES/Nombre Institucion/logo.png
MUFFIN_MASCOT_IMAGE=CLIENTES/Nombre Institucion/mascota.png
MUFFIN_SIGNERS_CONFIG=CLIENTES/Nombre Institucion/signers.json
MUFFIN_PRODUCT_NAME=MUFFIN Microbiología Hospitalaria
MUFFIN_PRODUCT_TAGLINE=Microbiología: Unidad de Fuentes, Flujos e Informes Nosocomiales
MUFFIN_COPYRIGHT_OWNER=Nombre Legal de la Institución
MUFFIN_IP_OWNER=RyM SAC
MUFFIN_VERSION=1.0
```

## Firmantes

Copie `signers.example.json` a `signers.json` dentro de la carpeta real del cliente. Las rutas `file` se resuelven relativas a esa carpeta.

Las imágenes de firma/sello deben quedar en `usuarios/` y no se suben a git.
