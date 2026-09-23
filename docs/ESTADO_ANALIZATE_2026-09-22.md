# Estado actual de MUFFIN Analizate

Fecha de corte: 2026-09-22  
Rama: `cliente-analizate`  
Repositorio: `Vostok96/muffin-lab`

## Entorno local

- Frontend: `http://127.0.0.1:8879/MUFFIN/Login/Index`
- API: `http://127.0.0.1:8013/api/v1/health`
- Compose: `compose.analizate.local.yaml`
- Proyecto Docker: `muffin-analizate`
- Credenciales locales: definidas en `.env.analizate.local`, archivo ignorado
  por Git.
- No ejecutar `docker compose down -v`: la base contiene datos de prueba y
  el volumen no debe eliminarse.

## Regla de alcance

Andahuaylas queda congelado. Los cambios de esta etapa solo corresponden a la
rama y al entorno de Analizate.

## Correcciones realizadas

1. El destino por defecto de recepción usa `ANALIZATE_LAB`.
2. El alta de muestras fue validada para exámenes no microbiológicos.
3. Los exámenes que no son cultivos ocultan y rechazan antibiogramas/AST.
4. Se corrigió el borrado de detalles de orden.
5. Se corrigió la cache de JavaScript del flujo de órdenes.
6. El sembrado de catálogo ahora elimina relaciones examen-muestra obsoletas;
   antes solo agregaba la relación nueva y podía dejar combinaciones inválidas.
7. `EXAMEN DE ACAROS EN PIEL Y PESTANAS` usa `RASPADO DE PIEL Y PESTANAS`
   con contenedor `LAMINA`; no usa `PLASMA`.
8. Se incorporo `logo_remaster.jpeg` como identidad visual de Analizate y se
   amplio su panel institucional para que el logotipo horizontal sea visible.
9. Se corrigieron relaciones de alta sensibilidad clinica: gases arteriales
   usa sangre arterial/jeringa heparinizada; coagulacion usa plasma citratado;
   prueba de embarazo queda explicitamente en orina; ADA de LCR usa liquido
   cefalorraquideo; y Acaros usa raspado de piel y pestanas.

## Archivos principales modificados en esta etapa

- `backend/scripts/prepare_analizate_production.py`: catálogo y limpieza de
  relaciones examen-muestra.
- `server.py`: versión de assets y proxy Analizate.
- `mirror/_pages/SIMCORE_WEB__Mic_orden.html`: cache del JavaScript de órdenes.
- `mirror/MUFFIN/Scripts/Views/Mic_orden_detalle_resultado_microbiologia.js`:
  reglas de AST para exámenes de cultivo.
- `docs/CLIENTE_ANALIZATE.md`: instrucciones y estado del cliente.

## Comprobaciones realizadas

- API y frontend reconstruidos con el sembrado actualizado.
- 130/130 relaciones de examen-muestra confirmadas por API.
- No existen nombres de examen duplicados en la base local.
- Ácaros, gases arteriales, coagulación, embarazo y ADA de LCR verificados.
- Logo remasterizado y pantalla de ingreso revisados visualmente.

## Próximo despliegue de revisión

- El cliente debe recibir una instancia aislada con datos ficticios y HTTPS.
- Netlify no puede ejecutar por sí solo el stack Docker actual; revisar
  `docs/DESPLIEGUE_NETLIFY_ANALIZATE.md` antes de publicar una URL.
- La opción inmediata es un staging Docker completo detrás de un túnel
  temporal; el NAS y la URL pública quedan después de la aprobación del
  cliente.

## Próximo bloque sugerido

- Auditoría de combinaciones clínicas: muestras, áreas, cultivos, perfiles y
  exámenes tercerizados.
- Separar en el modelo `tipo de espécimen`, `método`, `contenedor y
  conservante`, y `requisitos de toma`; actualmente esos conceptos todavía se
  expresan parcialmente en el nombre de la muestra.
- Resolver perfiles multiespecimen como componentes vinculados, no como una
  única muestra elegible. Son candidatos inmediatos el perfil preoperatorio,
  perfil de gestante y perfiles de anemia.
- Adjuntos de resultados para exámenes con `external_provider`.
- Reporte general para laboratorio clínico privado sin firma.
- Pruebas de permisos por rol y validación final.

## Historial Git relevante

- `06ba7d0` estabilización inicial de Analizate.
- `9af0bb4` clave de cache frontend de Analizate.
- `7a6acfe` compose local aislado.
- `27eea5e` destino de recepción Analizate.
- `73a6934` ocultar AST para exámenes sin cultivo.
- `5d33f74` refresco de assets del listado de órdenes.
- `8b37217` correcciones clínicas de muestras y auditoría del catálogo.
