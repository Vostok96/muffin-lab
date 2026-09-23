# Analizate Huaraz

Perfil institucional del laboratorio de analisis clinico Analizate, segundo
cliente/despliegue de MUFFIN. Este cliente parte de MUFFIN padre (rama
`cliente-analizate`) y no comparte datos, secretos ni branding con Andahuaylas.

## Identidad

- Institucion: Laboratorio de Analisis Clinico Analizate (Huaraz).
- Slug: `analizate-huaraz`.
- Carpeta de cliente: `CLIENTES/ANALIZATE - HUARAZ`.
- Domicilio: Pasaje Daniel Coral Vega 450 - Huaraz.
- Telefonos: 947893084 / 945211972.
- Email: laboratorioanalizatehuaraz@gmail.com.
- Logo institucional: `logo_remaster.jpeg` (version remasterizada de mayor
  resolucion).
- Producto: MUFFIN (Laboratorio de Analisis Clinico).
- Propiedad intelectual de MUFFIN: RyM SAC.
- Version visible: `1.0`.

## Variables de entorno usadas

```env
DEFAULT_INSTITUTION_NAME=LABORATORIO DE ANALISIS CLINICO ANALIZATE
DEFAULT_INSTITUTION_SLUG=analizate-huaraz
MUFFIN_INSTITUTION_NAME=Analizate Huaraz
MUFFIN_CLIENT_ROOT=CLIENTES/ANALIZATE - HUARAZ
MUFFIN_BRAND_IMAGE=CLIENTES/ANALIZATE - HUARAZ/logo_remaster.jpeg
MUFFIN_PRODUCT_IMAGE=MUFFIN_ICONO.jpg
MUFFIN_MASCOT_IMAGE=MUFFIN_SINFONDO.png
MUFFIN_SIGNERS_CONFIG=CLIENTES/ANALIZATE - HUARAZ/signers.json
MUFFIN_PRODUCT_NAME=MUFFIN Laboratorio de Analisis Clinico
MUFFIN_PRODUCT_TAGLINE=Laboratorio de analisis clinico Analizate
MUFFIN_COPYRIGHT_OWNER=Analizate Huaraz
MUFFIN_IP_OWNER=RyM SAC
MUFFIN_VERSION=1.0
```

## Alcance

Analizate es un laboratorio de analisis clinico privado. Su catalogo cubre
bioquimica, hematologia, urianalisis, semen, inmunologia, hormonas, marcadores
tumorales, coagulacion, parasitologia, patologia (biopsias/citologia) y
microbiologia, con examenes de resultados genericos (valor + unidad + valor de
referencia + observaciones) y examenes microbiologicos con flujo de cultivo.

Muchos examenes se tercerizan a Synlab. Para ellos:

- El examen puede marcarse con proveedor externo `SYNLAB` (columna
  `external_provider` de `Exam`).
- El resultado permite transcribir los valores en los campos genericos y
  adjuntar el PDF/archivo externo de Synlab.
- Los archivos adjuntos **nunca se imprimen** en el reporte/PDF del resultado;
  solo quedan guardados para consulta.

## Sello / firma del validador

Hasta que Analizate confirme si el sello del personal que valida debe salir
impreso en el resultado (o prefieren sellar manualmente), el reporte se
configura con `MUFFIN_REPORT_STAMP=0` (sello de validacion desactivado en el
PDF). El toggle es por despliegue:

```env
# 1 = imprimir sello/firma del validador final; 0 = no imprimir
MUFFIN_REPORT_STAMP=0
```

`signers.json` queda vacio hasta recibir los responsables autorizados y sus
sellos; cuando se decida activar el sello, se completan y se colocan las
imagenes en `usuarios/` (carpeta ignorada por git).

## Firmantes

Sin firmantes configurados por el momento. Ver `_plantilla/signers.example.json`
como referencia de la estructura.

## Catalogo institucional

Se carga con `backend/scripts/prepare_analizate_production.py` (idempotente).
Incluye:

- Areas/secciones del ORDEN DE ANALISIS provisto (bioquimica, microbiologia,
  urianalisis, semen, hematologia, embarazo, inmunologia, marcadores
  tumorales, alergias, endocrinologia, perfiles, parasitologia, patologia, etc.).
- Examenes con muestra por defecto y parametros genericos de resultado
  (RESULTADO, UNIDAD, VALOR DE REFERENCIA, OBSERVACIONES).
- Examenes microbiologicos reutilizando los parametros de cultivo del core.
- Opciones de origen/servicio/medico definidas para un laboratorio privado.

## Despliegue local

Ver `docs/CLIENTE_ANALIZATE.md` y el archivo de entorno
`.env.analizate.local.example`.

## Revisión externa antes del NAS

Para que el cliente pruebe botones y funciones se necesita publicar el stack
completo con HTTPS y datos ficticios. Netlify solo puede servir una capa web
estática; no reemplaza el servidor Python, la API FastAPI ni PostgreSQL. Usar
la guía `docs/DESPLIEGUE_NETLIFY_ANALIZATE.md` y no exponer el volumen ni las
credenciales locales.
