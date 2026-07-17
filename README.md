# MUFFIN padre

MUFFIN es una plataforma base para microbiología hospitalaria. Este repositorio funciona como **MUFFIN padre**: el núcleo común desde el cual se derivan versiones institucionales con logos, nombres, colores, textos legales, branding y configuraciones propias.

> Rama actual de producción institucional: **Hospital Sub Regional de Andahuaylas**. Ver [docs/CLIENTE_ANDAHUAYLAS.md](docs/CLIENTE_ANDAHUAYLAS.md).

El objetivo del repositorio padre es conservar el flujo clínico, la API, el proxy de compatibilidad y la experiencia visual común sin acoplar el producto a una sola institución.

## Qué contiene

- Frontend heredado capturado bajo `mirror/`, servido en rutas `/MUFFIN/...`.
- Servidor local `server.py`, que monta el frontend, inyecta sesión, tema, footer corporativo y proxies de compatibilidad.
- Backend FastAPI en `backend/` con JWT, roles, permisos por área, auditoría, catálogos, órdenes, resultados y reportes.
- Documentación operativa y técnica en `docs/`.
- Recursos base de identidad MUFFIN: `MUFFIN_ICONO.jpg` y `MUFFIN_FAVICON.png`.
- Insumos por cliente en `CLIENTES/`; no se cargan automáticamente en el core.

## Qué no debe contener

- Datos clínicos reales.
- Pacientes, HC, DNI o resultados productivos.
- Credenciales reales.
- Archivos `.env` productivos.
- Cachés, logs, dumps temporales o bases locales.

## Ejecución local

Frontend local:

```bash
python3 server.py
```

Abrir:

```text
http://127.0.0.1:8877/MUFFIN/
```

Backend/API:

```bash
docker compose up -d --build
```

La API queda en:

```text
http://127.0.0.1:8000/api/v1
```

## Seguridad de login

- El backend autentica en `POST /api/v1/auth/login`.
- Las contraseñas se almacenan con `pwdlib.PasswordHash.recommended()`, no en texto plano.
- La sesión usa JWT Bearer con expiración configurable por `ACCESS_TOKEN_MINUTES`.
- Las rutas protegidas usan `HTTPBearer` y roles/permisos de área.
- En producción, `APP_ENV=production` exige un `JWT_SECRET` no trivial de al menos 32 caracteres.
- El frontend local guarda el JWT en `localStorage` para compatibilidad con el frontend heredado. En despliegue real debe ir detrás de HTTPS y con secretos rotados por institución.

## Personalización por institución

Cada versión institucional debe partir del padre y modificar solo la capa de branding/configuración:

- Logo, favicon e imágenes institucionales.
- Nombre legal y nombre corto de la institución.
- Paleta de colores.
- Footer, textos de propiedad intelectual y versión.
- Variables `DEFAULT_INSTITUTION_NAME` y `DEFAULT_INSTITUTION_SLUG`.
- Dominio, proxy HTTPS y secretos de producción.

Evitar modificar flujos clínicos o contratos de API salvo que el cambio deba volver al padre.

## Documentos clave

- [docs/MUFFIN_PADRE.md](docs/MUFFIN_PADRE.md): guía para próximos agentes.
- [docs/MANUAL_OPERATIVO.md](docs/MANUAL_OPERATIVO.md): operación y comandos.
- [docs/DESPLIEGUE_NAS.md](docs/DESPLIEGUE_NAS.md): despliegue.
- [docs/MODELO_DATOS_MUFFIN.md](docs/MODELO_DATOS_MUFFIN.md): modelo de datos.
- [docs/MUFFIN_API_V1.yaml](docs/MUFFIN_API_V1.yaml): contrato OpenAPI.
- [docs/IDENTIDAD_VISUAL_MUFFIN.md](docs/IDENTIDAD_VISUAL_MUFFIN.md): identidad visual base.

## Estado actual

La pantalla de resultados de microbiología ya tiene:

- Filtro por procedencia.
- Filtro por estado de resultado/cultivo.
- DataTables en español.
- Modo claro/oscuro corporativo.
- Responsive móvil validado en 360, 390 y 430 px.
- Footer corporativo MUFFIN/RyM SAC con versión `v1.0`.
- Reporte de resultados servido con JWT de sesión, sin credencial puente hardcodeada.
