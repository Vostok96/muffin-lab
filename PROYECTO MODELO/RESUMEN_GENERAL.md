# Resumen de captura por roles SIMCORE

Fecha de captura: 2026-07-16

Origen:

```text
http://192.168.0.220/SIMCORE_WEB/
```

## Objetivo

Se generaron dos capturas separadas para que un agente pueda estudiar la arquitectura visible de SIMCORE y reconectar el proyecto en un entorno local/NAS sin datos reales.

Las capturas quedaron en:

```text
role_captures/admin/
role_captures/standard_user/
```

Cada carpeta contiene su propio mirror, mapas JSON y documento de arquitectura.

## Captura admin

Ruta:

```text
role_captures/admin/
```

Documento principal:

```text
role_captures/admin/docs/ARCHITECTURE.md
```

Resumen:

- Paginas HTML capturadas: 31
- Assets descargados correctamente: 34
- Endpoints backend detectados: 96
- Formularios detectados: ver `role_captures/admin/docs/forms.json`

El perfil admin entra correctamente a `Home` y ve los modulos principales de configuracion, ordenes, verificacion, resultados, consultas y reportes.

## Captura usuario estandar

Ruta:

```text
role_captures/standard_user/
```

Documento principal:

```text
role_captures/standard_user/docs/ARCHITECTURE.md
```

Resumen:

- Paginas HTML capturadas: 31
- Assets descargados correctamente: 34
- Endpoints backend detectados: 96
- Formularios detectados: ver `role_captures/standard_user/docs/forms.json`

La credencial operativa indicada en la ultima solicitud no autentico y devolvio pantalla de login. Para no dejar una captura falsa, se rehizo esta carpeta con una credencial operativa previa que si inicia sesion. No se versionan usuarios ni passwords reales.

## Comparacion admin vs usuario estandar

En la captura HTTP de frontend:

- Paginas exclusivas de admin: 0
- Paginas exclusivas del usuario estandar: 0
- Endpoints exclusivos de admin: 0
- Endpoints exclusivos del usuario estandar: 0

Conclusion: desde la perspectiva de paginas GET/HTML y scripts descargables, ambos perfiles expusieron la misma superficie de frontend. Si existen diferencias de permisos, probablemente se aplican dentro del backend al ejecutar endpoints AJAX, guardar, eliminar, generar reportes o cargar datos; esas respuestas no fueron descargadas para evitar datos reales.

## Estructura repetida en cada rol

```text
mirror/_pages/                         HTML renderizado de pantallas
mirror/SIMCORE_WEB/Content/           CSS y bundles de estilos
mirror/SIMCORE_WEB/Scripts/Views/     JS propio de cada vista
mirror/SIMCORE_WEB/bundles/           jQuery, Bootstrap, Modernizr
mirror/SIMCORE_WEB/Imagenes/          Logo/assets entregados
docs/routes.json                      Paginas probadas y estado HTTP
docs/assets.json                      Recursos descargados o faltantes
docs/endpoints.json                   Endpoints detectados
docs/forms.json                       Formularios detectados
docs/capture_manifest.json            Resumen de captura
docs/ARCHITECTURE.md                  Explicacion detallada por rol
```

## Backend

No se obtuvo codigo fuente del backend real. SIMCORE parece una aplicacion ASP.NET MVC publicada bajo IIS o similar:

- Rutas: `/SIMCORE_WEB/{Controlador}/{Accion}`
- Bundles ASP.NET: `/Content/PluginsCSS`, `/Content/PluginsJS`, `/bundles/jquery`, `/bundles/bootstrap`, `/bundles/modernizr`
- Scripts por vista: `/Scripts/Views/*`
- Carga de datos por AJAX/DataTables hacia acciones como `Obtener`, `Guardar`, `Actualizar`, `Eliminar`, `Exportar`, `DocumentoPDF`

Para reconstruir en casa, usar `docs/endpoints.json` de cada rol como contrato de endpoints y responder con datos ficticios del NAS.

## Privacidad

Durante esta captura:

- No se guardaron cuerpos de endpoints de datos/listados.
- Se sanitizaron identificadores numericos de 8 digitos en HTML y JS de vistas.
- Se sanitizo `session_user_id` a `local_demo`.
- No se versionaron passwords.

Antes de cualquier recaptura futura, repetir un escaneo de privacidad:

```powershell
rg -n "\\b\\d{8}\\b|session_user_id|password|pass" role_captures
```

Revisar manualmente cualquier coincidencia antes de commitear.

## Orden recomendado para reconectar

1. Levantar un servidor local que preserve `/SIMCORE_WEB/`.
2. Servir el HTML/assets ya capturados.
3. Implementar endpoints `Obtener` con datos ficticios.
4. Implementar endpoints de escritura `Guardar`, `Actualizar`, `Eliminar` contra la base simulada.
5. Probar primero `Mic_orden`, `Mic_orden_detalle/Resultado_microbiologia`, `Mic_parametro`, `Mic_examen`, `Mic_orga`.
6. Agregar reportes/exportaciones solo despues de tener ordenes y resultados ficticios funcionando.
