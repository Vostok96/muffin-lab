# Cliente Analizate Huaraz

Estado de trabajo: 2026-09-22. La rama activa es `cliente-analizate` y el
entorno local aislado se encuentra operativo en los puertos 8879/8013.

Analizate es el segundo despliegue institucional de MUFFIN. A diferencia de
Andahuaylas, su alcance no es solo microbiologia hospitalaria: funciona como
laboratorio clinico privado con catalogo amplio, examenes tercerizados y
resultados genericos.

## Rama

- Rama local: `cliente-analizate`.
- Remoto pendiente: publicar `cliente-analizate` en `origin` cuando el primer
  bloque estabilizado este commiteado.
- No modificar la rama `cliente-andahuaylas`; ese despliegue queda congelado
  para su cliente.

## Insumos

- Perfil y branding: `CLIENTES/ANALIZATE - HUARAZ/README.md`.
- Logo: `CLIENTES/ANALIZATE - HUARAZ/logo_remaster.jpeg`.
- Orden general: `CLIENTES/ANALIZATE - HUARAZ/ORDEN DE ANALISIS.docx`.
- Patologia/citologia: `CLIENTES/ANALIZATE - HUARAZ/ORDENES BIOPSIAS.docx`.
- Membrete: `CLIENTES/ANALIZATE - HUARAZ/menbretado analizate ggg (2).docx`.
- Firmantes: `CLIENTES/ANALIZATE - HUARAZ/signers.json` queda vacio hasta que
  el cliente confirme si desea imprimir sello/firma.

No versionar datos clinicos, contrasenas, firmas reales ni adjuntos de
resultados.

## Entorno

Usar `.env.analizate.local.example` como molde y copiarlo a `.env` en el
despliegue real por un canal seguro.

Variables importantes:

```env
DEFAULT_INSTITUTION_NAME=LABORATORIO DE ANALISIS CLINICO ANALIZATE
DEFAULT_INSTITUTION_SLUG=analizate-huaraz
MUFFIN_CLIENT_ROOT=CLIENTES/ANALIZATE - HUARAZ
MUFFIN_BRAND_IMAGE=CLIENTES/ANALIZATE - HUARAZ/logo_remaster.jpeg
MUFFIN_PRODUCT_NAME=MUFFIN Laboratorio de Analisis Clinico
MUFFIN_REPORT_STAMP=0
ANALIZATE_ADMIN_PASSWORD=<secreto real>
ANALIZATE_LAB_PASSWORD=<secreto real>
```

`MUFFIN_REPORT_STAMP=0` oculta el bloque de firma del reporte. Cambiar a `1`
cuando Analizate confirme responsables, credenciales y archivos de sello.

## Preparacion De Base

Desde una base migrada y con seed base:

```bash
docker compose up -d postgres
docker compose run --rm api alembic upgrade head
docker compose run --rm api sh -c "PYTHONPATH=/app python scripts/prepare_analizate_production.py"
docker compose up -d --build api frontend
```

Para desarrollo local aislado sin tocar otra pila MUFFIN en la misma maquina:

```bash
cp .env.analizate.local.example .env.analizate.local
docker compose --env-file .env.analizate.local -f compose.analizate.local.yaml up -d --build
```

Puertos locales:

- Frontend Analizate: `http://127.0.0.1:8879/MUFFIN/Login/Index`
- API Analizate: `http://127.0.0.1:8013/api/v1/health`

Si se ejecuta fuera de Docker, usar el entorno Python del backend y asegurarse
de que `DATABASE_URL`, `ANALIZATE_ADMIN_PASSWORD` y `ANALIZATE_LAB_PASSWORD`
esten definidos.

## Catalogo Inicial

El script `backend/scripts/prepare_analizate_production.py` es idempotente e
incluye:

- Areas de bioquimica, microbiologia, urianalisis, semen, hematologia,
  embarazo, inmunologia, marcadores tumorales, alergias, endocrinologia,
  perfiles, parasitologia, patologia y examenes generales.
- Procedencias y servicios propios de laboratorio privado.
- Muestras habituales: suero, plasma, sangre total, orina, orina 24 horas,
  heces, semen, secrecion, hisopado, esputo, tejido, liquido biologico, lamina
  y raspado de piel/pestanas.
- Cada examen conserva exclusivamente las relaciones examen-muestra declaradas
  por el catalogo de Analizate. El sembrado elimina relaciones antiguas
  incorrectas para evitar que un examen herede muestras de otro.
- `ACAROS PIEL Y PESTANAS` usa `RASPADO DE PIEL / PESTANAS`, no plasma.
- Examenes genericos con parametros `RESULTADO`, `UNIDAD`,
  `VALOR DE REFERENCIA` y `OBSERVACIONES`.
- Cultivos que reutilizan los parametros microbiologicos del core.
- Marca `external_provider=SYNLAB` para examenes que suelen tercerizarse.

Los adjuntos de Synlab ya tienen estructura de datos (`result_attachment`), pero
la carga/descarga por API y la UI quedan como siguiente bloque de desarrollo.

## Correcciones estabilizadas

- El destino de recepcion local es `LABORATORIO ANALIZATE`.
- Los examenes que no son cultivos no muestran ni aceptan antibiogramas.
- El boton de eliminar detalle de orden fue validado contra la API.
- Se corrigio la cache de assets del listado y del formulario de orden.
- Se agrego una version de assets nueva para evitar JavaScript obsoleto en el
  navegador.

## Siguiente Bloque Funcional

1. Crear endpoints autenticados para adjuntos de resultado: subir, listar,
   descargar y eliminar.
2. Agregar UI de adjuntos en la pantalla de resultados para examenes con
   `external_provider`.
3. Ajustar el reporte general para laboratorio clinico no microbiologico.
4. Validar flujo completo: orden, recepcion, resultado generico, validacion
   final y reporte sin firma.
