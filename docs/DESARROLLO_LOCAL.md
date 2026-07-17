# Desarrollo local de MUFFIN

## Objetivo

Validar toda correccion en local antes de desplegarla al NAS. El entorno local reproduce la API FastAPI y PostgreSQL mediante Docker Compose, pero usa datos estrictamente ficticios.

## Requisitos

- Docker Desktop con backend WSL2 activo.
- Docker Compose v2.
- Puesto `8000` libre o `MUFFIN_API_PORT` definido en `.env.local`.

Si WSL2 no esta instalado, habilitarlo desde una terminal Windows con privilegios de administrador y reiniciar antes de instalar o iniciar Docker Desktop. No avanzar al NAS para sustituir esta validacion local.

## Primer arranque

1. Copiar `.env.local.example` a `.env.local`.
2. Mantener las credenciales como valores exclusivos de desarrollo; nunca reutilizarlas en NAS o produccion.
3. Ejecutar:

   ```powershell
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml up -d --build
   ```

4. Crear datos ficticios idempotentes:

   ```powershell
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python -m app.seed
   ```

5. Ejecutar la prueba de humo:

   ```powershell
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python scripts/smoke_test.py
   ```

La prueba confirma migracion, salud de API, login JWT y el usuario ficticio `dev-admin`.

6. Ejecutar la prueba de catalogos:

   ```powershell
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python scripts/catalog_smoke_test.py
   ```

La prueba confirma lectura autenticada, escritura administrativa, paginacion, busqueda, desactivacion, duplicados, permisos, relaciones examen-muestra y examen-parametro, y auditoria.

7. Ejecutar la prueba del MVP clinico:

   ```powershell
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python scripts/clinical_smoke_test.py
   ```

La prueba cubre paciente, busqueda por HC, orden, items, barcode, toma, recepcion, rechazo, anulacion, reapertura, permisos y eventos de trazabilidad.

8. Ejecutar la prueba de resultados y validacion:

   ```powershell
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python scripts/result_smoke_test.py
   ```

La prueba cubre el formulario dinamico, el guardado en proceso, la validacion preliminar, la validacion final, el bloqueo posterior y la reapertura justificada.

## Pruebas unitarias del backend

La imagen de ejecucion no instala dependencias de desarrollo. Para correr la suite en un contenedor temporal:

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml run --rm api sh -c 'pip install --no-cache-dir -r requirements-dev.txt && pytest -q'
```

## Frontend heredado de referencia

En Linux, mantenerlo separado de la API nueva:

```bash
python3 server.py
```

Abrir `http://127.0.0.1:8877/SIMCORE_WEB/`. La API nueva permanece en `http://127.0.0.1:8000/api/v1`. Esta separacion evita alterar silenciosamente los contratos JavaScript heredados; el adaptador frontend se construira cuando los flujos de resultados esten estabilizados.

## Datos ficticios incluidos

| Usuario | Rol | Uso |
| --- | --- | --- |
| `dev-admin` | `ADMIN` | Administracion y pruebas de permisos. |
| `dev-entry` | `ENTRY` | Registro de solicitudes. |
| `dev-processor` | `PROCESSOR` | Procesamiento y permisos de validacion en microbiologia. |

Areas: `MICROBIOLOGY` y `RECEPTION`.

Catalogos ficticios: procedencia `HOSPITAL`, servicio `EMERGENCY`, medico `DEV-CLINICIAN`, destino `MICROBIOLOGY_BENCH`, contenedor `STERILE_CUP`, muestra `URINE`, examen `URINE_CULTURE` y parametros `CULTURE_RESULT`, `CULTURE_OBSERVATION` y campos complementarios de positividad, con sus relaciones configuradas. El resultado de cultivo expone `NEGATIVO`, `POSITIVO`, `NO TRAJO MUESTRA` y `MUESTRA INADECUADA`; al elegir `POSITIVO` se despliegan campos adicionales de apoyo clinico.

Caso clinico ficticio: paciente `DEV-HC-0001`, orden `DEV-ORDER-0001` y muestra recibida con barcode `DEV-ORDER-0001-01-UC`. Ninguno representa una persona o atencion real.

Caso de resultado ficticio: el item `DEV-ORDER-0001-01-UC` se siembra con `NO_GROWTH` como resultado guardado para validar la fase 4.

## Reinicio limpio

Para eliminar toda la base ficticia local:

```powershell
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml down -v
```

Luego repetir el primer arranque. Nunca ejecutar este comando contra los volumenes del NAS.
