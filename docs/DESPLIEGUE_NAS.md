# Despliegue de MUFFIN en NAS

MUFFIN se ejecuta en Docker sobre el NAS ARM64. La PC se usa solo para desarrollo.

Tenant inicial: `Hospital Sub Regional de Andahuaylas`.

## Servicios

- `muffin-api`: FastAPI, dos workers y limite de 768 MB.
- `muffin-postgres`: PostgreSQL 16, limite de 1.5 GB.
- Proxy reverso: usar el ya existente en el NAS para HTTPS y el dominio interno; no se incluye un proxy adicional.

El presupuesto inicial de MUFFIN es menor de 2.5 GB. Esto deja memoria para el sistema NAS y las otras aplicaciones sobre un equipo de 8 GB.

## Almacenamiento

- El volumen `muffin_postgres_data` contiene datos activos de PostgreSQL.
- En este NAS se ubicara en HDD. Por ello el modelo incluye indices desde el inicio y los listados seran paginados.
- Los PDF, etiquetas, exportaciones y backups deben ir a un volumen NAS separado del volumen activo de PostgreSQL.
- Si se agrega NVMe en el futuro, mover primero `muffin_postgres_data` al NVMe.

## Preparacion en el NAS

1. Copiar el proyecto al volumen donde Docker almacena sus aplicaciones.
2. Crear `.env` a partir de `.env.example`.
3. Reemplazar `POSTGRES_PASSWORD`, `JWT_SECRET` y `BOOTSTRAP_ADMIN_PASSWORD` por secretos unicos. `JWT_SECRET` debe tener al menos 32 caracteres. Ajustar `DEFAULT_INSTITUTION_NAME` y `DEFAULT_INSTITUTION_SLUG` si el despliegue deja de ser Andahuaylas.
4. Ejecutar `docker compose up -d --build`.
5. Verificar `http://IP_DEL_NAS:8000/api/v1/health`.
6. Configurar el proxy reverso hacia `muffin-api:8000` o `IP_DEL_NAS:8000`, segun el proxy existente.

Las imagenes oficiales de Python y PostgreSQL seleccionan automaticamente la variante `linux/arm64` en el NAS RK3588C. No fijar una imagen `amd64`.

## Operacion segura

- El usuario administrador inicial se crea una sola vez mediante las variables `BOOTSTRAP_ADMIN_*`.
- Tras crear el administrador, retirar `BOOTSTRAP_ADMIN_PASSWORD` del archivo `.env` y reiniciar la API.
- No exponer PostgreSQL fuera de la red Docker.
- Mantener el puerto de la API solo en la red local o detras del proxy HTTPS.
- Programar copias logicas de PostgreSQL y probar restauraciones periodicamente.
