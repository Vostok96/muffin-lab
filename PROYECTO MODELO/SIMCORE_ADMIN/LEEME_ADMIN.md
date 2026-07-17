# SIMCORE - Captura perfil administrador

Esta carpeta contiene la captura visible del SIMCORE WEB iniciando sesion como perfil administrador.

Origen:

```text
http://192.168.0.220/SIMCORE_WEB/
```

## Que hay aqui

```text
mirror/_pages/                         HTML renderizado de pantallas
mirror/SIMCORE_WEB/Content/           CSS y bundles de estilos
mirror/SIMCORE_WEB/Scripts/Views/     JS propio de cada vista
mirror/SIMCORE_WEB/bundles/           jQuery, Bootstrap, Modernizr
mirror/SIMCORE_WEB/Imagenes/          Logo/assets descargados
docs/ARCHITECTURE.md                  Explicacion tecnica detallada
docs/routes.json                      Rutas HTML probadas
docs/assets.json                      Assets descargados o faltantes
docs/endpoints.json                   Endpoints backend detectados
docs/forms.json                       Formularios y actions detectados
docs/capture_manifest.json            Resumen de captura
```

## Resumen

- Paginas HTML capturadas: 31
- Assets descargados correctamente: 34
- Endpoints backend detectados: 96
- Formularios detectados: ver `docs/forms.json`

## Importante

Esto no contiene el codigo fuente real del backend ASP.NET/C#/MVC. Ese codigo no se entrega por HTTP desde el navegador.

Tampoco contiene datos reales de pacientes, resultados u ordenes. No se guardaron respuestas de endpoints de listados o datos clinicos.

Para reconstruir localmente en casa, usar `docs/endpoints.json` como contrato de endpoints y responder con datos ficticios desde el NAS.

Leer primero:

```text
docs/ARCHITECTURE.md
```
