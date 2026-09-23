# Cliente Analizate Huaraz

Estado de trabajo: 2026-09-22. La rama activa es `cliente-analizate` y el
entorno local aislado se encuentra operativo en los puertos 8879/8013.

Analizate es el segundo despliegue institucional de MUFFIN. A diferencia de
Andahuaylas, su alcance no es solo microbiologia hospitalaria: funciona como
laboratorio clinico privado con catalogo amplio, examenes tercerizados y
resultados genericos.

## Rama

- Rama local: `cliente-analizate`.
- Remoto: `origin/cliente-analizate`, actualizado hasta el commit de auditoría
  clínica.
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
- `EXAMEN DE ACAROS EN PIEL Y PESTANAS` usa `RASPADO DE PIEL Y PESTANAS`.
- `ANALISIS DE GASES ARTERIALES AGA` usa `SANGRE ARTERIAL` en `JERINGA
  HEPARINIZADA`.
- Las pruebas de coagulacion usan `PLASMA CITRATADO` en tubo con citrato.
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
- La pantalla de ingreso usa el logo remasterizado con una presentación más
  visible y paleta institucional de Analizate.
- La auditoría clínica cubre los 130 exámenes sembrados y está documentada en
  `docs/AUDITORIA_CATALOGO_CLINICO_ANALIZATE.md`.

## Previsualización para el cliente

El cliente debe probar una copia aislada, con datos ficticios, antes del NAS y
de la URL pública. El entorno local completo permite probar autenticación,
órdenes, muestras, recepción, resultados, validaciones y reportes.

Netlify no ejecuta directamente el stack actual: `server.py` es un servidor
Python con proxy de compatibilidad, la API es FastAPI y PostgreSQL necesita
almacenamiento persistente. Para esta fase se recomienda publicar el stack
Docker completo detrás de HTTPS mediante un túnel temporal o un servidor de
staging. Netlify puede evaluarse después como frontend separado, cuando la API
tenga una URL pública estable, CORS restringido, almacenamiento de adjuntos y
una estrategia de autenticación definida.

La guía completa está en `docs/DESPLIEGUE_NETLIFY_ANALIZATE.md`.

## Siguiente Bloque Funcional

1. Crear endpoints autenticados para adjuntos de resultado: subir, listar,
   descargar y eliminar.
2. Agregar UI de adjuntos en la pantalla de resultados para examenes con
   `external_provider`.
3. Ajustar el reporte general para laboratorio clinico no microbiologico.
4. Validar flujo completo: orden, recepcion, resultado generico, validacion
   final y reporte sin firma.
