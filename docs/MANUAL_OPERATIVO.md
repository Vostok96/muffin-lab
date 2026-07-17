# Manual operativo de MUFFIN

Version: 0.1.0 | Fecha: 2026-07-17

Tenant inicial: `Hospital Sub Regional de Andahuaylas`.

## 1. Arquitectura

MUFFIN es una aplicacion de microbiologia clinica compuesta por:

- **Backend**: FastAPI + PostgreSQL 16, empaquetado en Docker.
- **Frontend heredado**: servidor Python con assets estaticos heredados, servido bajo `/MUFFIN/` (puerto 8877).
- **Infraestructura**: Docker Compose v2 con dos servicios (`api`, `postgres`).

## 2. Despliegue local

### Requisitos

- Docker Engine >= 29 y Docker Compose v2.
- Puerto 8000 y 8877 libres (configurables en `.env.local`).
- Al menos 2 GB de RAM disponibles para los contenedores.

### Primer arranque

```bash
cd MUFFIN
cp .env.local.example .env.local
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml up -d --build
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api python -m app.seed
```

La API queda en `http://127.0.0.1:8000/api/v1` y el frontend en `http://127.0.0.1:8877/MUFFIN/`.

### Detener

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml down
```

### Reiniciar desde cero

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml down -v
# Luego repetir el primer arranque.
```

## 3. Migraciones

Las migraciones se aplican automaticamente al iniciar el contenedor `api` mediante Alembic. Las migraciones vigentes son:

| Migracion | Descripcion |
|---|---|
| `0001_security_foundation` | Usuarios, roles, areas, JWT, Argon2, auditoria |
| `0002_minimum_catalogs` | Catalogos minimos y relaciones |
| `0003_clinical_mvp` | Pacientes, ordenes, items, trazabilidad |
| `0004_results_validation` | Resultados dinamicos y validacion por area |
| `0005_microbiology_advanced` | Organismos, aislados, AST |
| `0006_outputs_integrations` | Print jobs, notificaciones, instrumentos |

Para crear una nueva migracion:

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec api alembic revision --autogenerate -m "descripcion"
```

## 4. Variables de entorno

| Variable | Obligatoria | Proposito |
|---|---|---|
| `POSTGRES_PASSWORD` | Si | Contrasena de PostgreSQL |
| `JWT_SECRET` | Si | Clave para firmar tokens JWT (min 32 caracteres en produccion) |
| `DEV_SEED_PASSWORD` | Si (local) | Contrasena de usuarios de desarrollo |
| `MUFFIN_API_PORT` | No (default 8000) | Puerto de la API |
| `MUFFIN_BIND_ADDRESS` | No (default 0.0.0.0) | Direccion de escucha |

## 5. Usuarios ficticios

| Usuario | Contrasena | Roles |
|---|---|---|
| `dev-admin` | `DEV_SEED_PASSWORD` | ADMIN |
| `dev-entry` | `DEV_SEED_PASSWORD` | ENTRY |
| `dev-processor` | `DEV_SEED_PASSWORD` | PROCESSOR (validacion microbiologia) |

## 6. Respaldo y restauracion

### Crear respaldo

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec postgres \
  pg_dump -U muffin_local -d muffin_local --no-owner --no-acl -f /tmp/muffin_backup_$(date +%Y%m%d).sql
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml cp \
  postgres:/tmp/muffin_backup_$(date +%Y%m%d).sql ./backups/
```

### Restaurar respaldo

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml down -v
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml up -d postgres
sleep 5
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml exec -T postgres \
  psql -U muffin_local -d muffin_local < ./backups/muffin_backup_YYYYMMDD.sql
docker compose --env-file .env.local -f compose.yaml -f compose.local.yaml up -d
```

## 7. Pruebas de calidad

Ejecutar desde la raiz del repositorio con el entorno levantado:

```bash
# Smoke tests (6 pruebas de humo)
docker compose exec api python scripts/smoke_test.py
docker compose exec api python scripts/catalog_smoke_test.py
docker compose exec api python scripts/clinical_smoke_test.py
docker compose exec api python scripts/result_smoke_test.py
docker compose exec api python scripts/microbiology_smoke_test.py
docker compose exec api python scripts/outputs_smoke_test.py

# Rendimiento
docker compose exec -e DEV_SEED_PASSWORD=... api python scripts/performance_benchmark.py

# Seguridad
docker compose exec -e DEV_SEED_PASSWORD=... api python scripts/security_review.py

# Unit tests
docker compose run --rm api sh -c 'pip install --no-cache-dir -r requirements-dev.txt && pytest -q'
```

## 8. Solucion de problemas

### La API no arranca

```bash
docker compose logs api postgres
```

Causas frecuentes:
- Puerto 8000 ocupado: cambiar `MUFFIN_API_PORT` en `.env.local`.
- PostgreSQL no saludable: verificar que `POSTGRES_PASSWORD` este definido.
- Migracion fallida: revisar logs de Alembic.

### El frontend no carga

Verificar que `python3 server.py` este corriendo en puerto 8877.

### Error de permisos

El usuario `dev-processor` tiene permisos de validacion en el area `MICROBIOLOGY`. Otros usuarios requieren asignacion explicita de permisos de area.

## 9. Seguridad

- Las contrasenas se almacenan con Argon2id.
- Los tokens JWT expiran en 30 minutos.
- Las migraciones usan advisory locks para evitar carreras en el arranque.
- Toda accion clinica y de catalogo se registra en `audit_event`.
- Los catalogos se desactivan, nunca se borran fisicamente.
- Las anulaciones y reaperturas exigen motivo y se auditan.

## 10. Limites de recursos (Docker local)

| Servicio | CPU | RAM |
|---|---|---|
| `postgres` | 1.5 cores | 1024 MB |
| `api` | 1.0 cores | 512 MB |

Para el NAS ARM64 (8 GB RAM), se recomienda reducir PostgreSQL a 768 MB y API a 384 MB.

## 11. Monitoreo

- Health endpoint: `GET /api/v1/health` → `{"status":"ok","service":"muffin-api"}`
- Healthcheck de PostgreSQL: `pg_isready` cada 10 segundos.
- Logs: `docker compose logs --tail=200 api postgres`
