# MUFFIN para Hospital Sub Regional de Andahuaylas

MUFFIN es la plataforma institucional de microbiologia para el Hospital Sub Regional de Andahuaylas, con una base de codigo unica preparada para operar luego en otros hospitales.

Este repositorio contiene:

- HTML renderizado de las pantallas principales heredadas.
- Bundles CSS/JS que entrega el servidor.
- Scripts de vistas de `Scripts/Views`.
- Imagenes y recursos publicos encontrados.
- Mapa de rutas y endpoints usados por el frontend.
- Servidor local para montar la captura bajo `/MUFFIN/`.

No contiene:

- Base de datos real.
- Ordenes reales.
- Resultados reales.
- Nombres/DNI/HC de pacientes.
- Credenciales reales.
- Codigo servidor C#/MVC, porque ese codigo no se entrega por HTTP.

## Ejecutar

```powershell
cd MUFFIN
.\run_local.ps1
```

Abrir:

```text
http://127.0.0.1:8877/MUFFIN/
```

El servidor local mantiene compatibilidad temporal con rutas heredadas cuando hace falta, pero el destino operativo es `/MUFFIN/...`.

## Backend local/NAS

El frontend espera endpoints como:

```text
/SIMCORE_WEB/Mic_orden/Obtener
/SIMCORE_WEB/Mic_orden/Guardar
/SIMCORE_WEB/Mic_parametro/Obtener
/SIMCORE_WEB/Mic_orden_detalle_res/Guardar
```

El archivo `docs/endpoints.json` lista las rutas detectadas. El servidor incluido responde con stubs vacios para que la UI no se rompa. El backend real de MUFFIN se esta construyendo localmente en `backend/` y sustituira esos stubs de forma gradual despues de sus pruebas locales.

## Estado de MUFFIN

El avance, la politica de desarrollo local antes del NAS y el orden de construccion estan documentados en `docs/AVANCE_MUFFIN.md`. La direccion objetivo institucional esta en `docs/ARQUITECTURA_OBJETIVO_MUFFIN_ANDAHUAYLAS.md`.

En Linux, el frontend heredado de referencia puede verse con `python3 server.py` en `http://127.0.0.1:8877/MUFFIN/`. Se mantiene separado de la API nueva para preservar su comportamiento hasta construir el adaptador correspondiente.

La guia de continuacion para la proxima sesion Linux esta en `docs/HANDOFF_LINUX.md`.

## Recapturar desde SIMCORE

Usar solo para estructura/frontend, no para datos:

```powershell
$env:SIMCORE_SOURCE_USER = "TU_USUARIO_SIMCORE"
$env:SIMCORE_SOURCE_PASS = "TU_PASSWORD_SIMCORE"
python .\tools\capture_simcore_frontend.py
```

La herramienta inicia sesion, descarga paginas de menu y assets publicos. No llama endpoints de listados de pacientes/ordenes.
