# Traspaso a Linux

## Estado al cerrar esta sesion

MUFFIN tiene implementadas y verificadas localmente con Docker las fases de entorno reproducible, seguridad, catalogos minimos, trazabilidad clinica base y resultados dinamicos:

- FastAPI y PostgreSQL 16 definidos en Docker Compose.
- Alembic con migraciones `0001_security_foundation`, `0002_minimum_catalogs`, `0003_clinical_mvp` y `0004_results_validation`.
- JWT, Argon2, roles, permisos por area y auditoria.
- Datos ficticios idempotentes, script de semilla y pruebas de humo de seguridad y catalogos.
- Procedencias, servicios, medicos, contenedores, muestras, examenes, parametros y sus relaciones configurables.
- Pacientes, ordenes, items, destinos, barcodes y trazabilidad de toma, recepcion, rechazo, anulacion y reapertura.
- Resultados dinamicos por parametro, validacion preliminar/final, bloqueo y reapertura justificada con semilla ficticia y prueba de humo propia.
- Modelo de datos, contrato OpenAPI y documentacion de despliegue.
- Frontend de referencia con identidad MUFFIN, paleta azul noche y modo oscuro.

No hay datos clinicos reales, secretos reales ni despliegue en el NAS.

## Punto exacto pendiente

~~Cerrar la validacion limpia de la fase 4 de `docs/AVANCE_MUFFIN.md` desde un volumen PostgreSQL vacio.~~

Cerrado el 2026-07-16. La validacion limpia de fase 4 paso contra un volumen vacio en Linux x86_64: `down -v`, `up -d --build`, doble semilla idempotente, cuatro smoke tests pasados, 12 unit tests pasados, health OK, logs limpios. El adaptador del frontend para consumir resultados queda como tarea de UI.

No pasar al NAS. Mantener todas las nuevas migraciones y pruebas en Docker local.

## Preparacion de Linux

1. Confirmar que Docker Engine y Docker Compose v2 estan disponibles:

   ```bash
   docker --version
   docker compose version
   uname -m
   ```

2. Clonar el repositorio en el disco Linux o, si ya existe, actualizarlo:

   ```bash
   git clone https://github.com/Vostok96/simcore.git MUFFIN
   cd MUFFIN
   ```

   Repositorio existente:

   ```bash
   git pull --ff-only origin main
   ```

3. Crear el entorno local sin reutilizar secretos de NAS:

   ```bash
   cp .env.local.example .env.local
   ```

4. Revisar la composicion resultante antes de iniciar contenedores:

   ```bash
   docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml config
   ```

## Validacion obligatoria de Compose

Ejecutar desde la raiz del repositorio:

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml up -d --build
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml ps
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python -m app.seed
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python scripts/smoke_test.py
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python scripts/catalog_smoke_test.py
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python scripts/clinical_smoke_test.py
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python scripts/result_smoke_test.py
```

Resultado esperado:

```text
Local API smoke test passed.
Catalog API smoke test passed.
Clinical workflow smoke test passed.
Result validation smoke test passed.
```

Verificar tambien:

```bash
curl http://127.0.0.1:8000/api/v1/health
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml logs --tail=100 api postgres
```

El endpoint debe devolver:

```json
{"status":"ok","service":"muffin-api"}
```

## Si la validacion falla

- No modificar los secretos de produccion ni usar el NAS como alternativa.
- Revisar primero `docker compose ... logs api postgres`.
- Corregir compatibilidad de imagen, migracion o variables locales en el repositorio.
- Repetir la prueba desde un volumen limpio:

  ```bash
  docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml down -v
  ```

- Ejecutar otra vez todos los comandos de validacion obligatoria.

## Criterio para cerrar la validacion local

- Compose crea PostgreSQL y API desde una base vacia.
- Alembic aplica `0001_security_foundation`, `0002_minimum_catalogs`, `0003_clinical_mvp` y `0004_results_validation`.
- La semilla puede ejecutarse dos veces sin duplicar registros.
- Las cuatro pruebas de humo pasan: seguridad/login, catalogos, clinica y resultados.
- El endpoint de salud responde `{"status":"ok","service":"muffin-api"}`.
- Los logs de API y PostgreSQL quedan sin errores relevantes.
- No aparecen credenciales ni bases de datos locales en Git.

## Siguiente fase

Fase 5 completada y validada: microbiologia avanzada implementada con migracion `0005_microbiology_advanced`, modelos de organismos, recuentos, comentarios, antibioticos, paneles AST, aislados y resultados de sensibilidad. 5 de 5 smoke tests y 20 unit tests pasan limpio.

Proxima: fase 8 de `docs/AVANCE_MUFFIN.md`: despliegue controlado en NAS ARM64 (construir imagenes multi-arquitectura, volumenes persistentes, secretos, HTTPS, restauracion de respaldo y monitoreo).

## Documentos de referencia

- `docs/AVANCE_MUFFIN.md`: estado y fases vigentes.
- `docs/DESARROLLO_LOCAL.md`: instrucciones de desarrollo local.
- `docs/MODELO_DATOS_MUFFIN.md`: entidades y reglas del dominio.
- `docs/MUFFIN_API_V1.yaml`: contrato API.
- `docs/DESPLIEGUE_NAS.md`: solo para el despliegue posterior al NAS.
- `docs/IDENTIDAD_VISUAL_MUFFIN.md`: diseno y paletas.
