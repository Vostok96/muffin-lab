# MUFFIN padre - guía técnica para continuidad

Este documento orienta a futuros agentes o desarrolladores que retomen el repositorio. MUFFIN padre es el core común; las versiones por institución deben derivarse desde aquí sin contaminar el núcleo con decisiones específicas de un cliente.

## Propósito

MUFFIN cubre el flujo de microbiología hospitalaria:

1. Registro y mantenimiento de pacientes.
2. Creación de órdenes y detalle de exámenes.
3. Recepción/verificación de muestras.
4. Registro de resultados microbiológicos.
5. Identificación, recuento y antibiograma.
6. Validación preliminar/final.
7. Emisión de reportes y consultas.

El frontend conserva compatibilidad visual y funcional con pantallas heredadas de SIMCORE, pero el backend objetivo es FastAPI/PostgreSQL.

## Arquitectura local

- `server.py`: servidor local del frontend heredado. Sirve páginas bajo `/MUFFIN/`, inyecta favicon, sesión, modo claro/oscuro, uppercase, footer corporativo y proxies hacia la API.
- `mirror/`: HTML, CSS, JS y assets capturados desde el frontend heredado.
- `backend/`: API FastAPI con SQLAlchemy, Alembic, JWT, roles, permisos de área, auditoría y scripts de smoke/security tests.
- `docs/login.html`: login propio MUFFIN. Solicita JWT a la API y guarda la sesión en `localStorage` para que el frontend heredado pueda operar.
- `docs/`: documentación técnica, operativa, API y handoff.
- `CLIENTES/`: insumos de branding por institución. No son cargados por defecto por MUFFIN padre.

## Tecnologías

- Python 3.13 para servidor local y backend.
- FastAPI para API.
- SQLAlchemy y Alembic para persistencia/migraciones.
- PostgreSQL en despliegue Docker; SQLite solo como default local si no se configura.
- JWT Bearer con `PyJWT`.
- Hash de contraseñas con `pwdlib.PasswordHash.recommended()`.
- Frontend heredado con Bootstrap, jQuery, DataTables y Font Awesome.
- Docker Compose para entorno API/PostgreSQL.

## Flujo de autenticación

1. Usuario abre `/MUFFIN/Login/Index`.
2. `docs/login.html` llama `POST /api/v1/auth/login`.
3. La API valida usuario activo y hash de contraseña.
4. La API devuelve JWT Bearer con expiración.
5. El frontend guarda `muffin_token` en `localStorage`.
6. `SESSION_SCRIPT` en `server.py` valida `/auth/me` y agrega `Authorization: Bearer ...` a llamadas AJAX `/MUFFIN/...`.
7. Los proxies de `server.py` rechazan peticiones sin token con 401.
8. Los reportes abiertos en ventana se obtienen con `fetch` autenticado y se escriben en el popup.

Notas de seguridad:

- No usar `admin/admin` en producción.
- No versionar `.env` real.
- `APP_ENV=production` exige `JWT_SECRET` fuerte.
- Mantener la API detrás de HTTPS/proxy en despliegue real.
- `localStorage` se conserva por compatibilidad con frontend heredado; no debe considerarse equivalente a cookies `HttpOnly`.

## Personalización por institución

La versión institucional debe vivir en rama, fork o paquete de despliegue separado. Cambios esperados:

- `MUFFIN_ICONO.jpg`, `MUFFIN_FAVICON.png` y assets gráficos.
- Paleta CSS en `mirror/MUFFIN/Content/muffin.css`.
- Footer inyectado en `APP_FOOTER_MARKUP` dentro de `server.py`.
- Variables `DEFAULT_INSTITUTION_NAME` y `DEFAULT_INSTITUTION_SLUG`.
- `.env` productivo con secretos únicos.
- Nombre de dominio, proxy HTTPS, backup y almacenamiento.

No cambiar en una variante:

- Contratos de API sin volver el cambio al padre.
- Migraciones compartidas sin revisar impacto.
- Estructura de roles/permisos sin documentar.
- Lógica clínica común para resolver solo una marca institucional.

## Pantalla de resultados de microbiología

Archivos principales:

- `mirror/MUFFIN/Scripts/Views/Mic_orden_detalle_resultado_microbiologia.js`
- `mirror/_pages/SIMCORE_WEB__Mic_orden_detalle__Resultado_microbiologia.html`
- `mirror/MUFFIN/Content/muffin.css`
- `server.py`

Estado actual:

- `#cboFiltro` filtra por procedencia.
- `#cboArea` filtra por resultado/cultivo: todos, positivo, negativo, no trajo muestra, contaminado, en proceso.
- DataTables está traducido al español de forma inline.
- En móvil, DataTables muestra columnas clave y permite expandir fila para ver detalle y acciones.
- El reporte de resultados se abre mediante fetch autenticado.

## Validaciones recomendadas

Antes de cerrar una tanda de cambios:

```bash
python3 -m py_compile server.py
node --check mirror/MUFFIN/Scripts/Views/Mic_orden_detalle_resultado_microbiologia.js
```

Para backend, cuando la API y Postgres estén levantados:

```bash
docker compose exec api pytest
docker compose exec -e DEV_SEED_PASSWORD=... api python scripts/security_review.py
```

Para responsive, usar Chrome headless/CDP o Playwright y validar al menos:

- 360 x 800
- 390 x 844
- 430 x 932
- 1440 x 900

Criterios mínimos:

- `document.documentElement.scrollWidth` igual al ancho del viewport en móvil.
- Menú hamburguesa sin desbordes.
- Filtros apilados y legibles.
- Tabla sin scroll horizontal de página.
- Fila responsive expandible y acciones accesibles.
- Footer sin superponerse al contenido.

## Residuos que no deben subirse

- `__pycache__/`
- `*.pyc`
- `*.log`
- capturas temporales en `/tmp`
- bases `.db`, `.sqlite`, `.sqlite3`
- `.env` y `.env.local`
- dumps de pacientes, órdenes o resultados reales

## Estado Git esperado

El padre debe mantenerse con commits pequeños y trazables. Para variantes institucionales:

1. Crear rama desde `main`.
2. Aplicar branding/configuración.
3. Documentar cambios en un MD propio de la institución.
4. No mezclar datos reales ni secretos.
5. Si aparece una mejora general, portarla de vuelta a `main`.
