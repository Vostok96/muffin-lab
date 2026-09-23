# Revisión externa de Analízate

Estado: propuesta para validación del cliente.  
Rama: `cliente-analizate`.

## Decisión técnica

Netlify no puede ejecutar por sí solo el despliegue actual de MUFFIN. El
proyecto necesita tres piezas con estado persistente:

- `server.py`, que sirve el frontend heredado e inyecta branding, sesión y
  proxies de compatibilidad.
- FastAPI, que contiene autenticación, permisos, órdenes, muestras,
  resultados, reportes y reglas clínicas.
- PostgreSQL, que conserva usuarios, catálogos, órdenes y resultados.

Netlify puede servir archivos estáticos, pero no reemplaza un proceso Python
permanente ni una base PostgreSQL persistente. Las Netlify Functions tampoco
son una conversión directa de este stack y no resuelven por sí mismas la
persistencia, los adjuntos ni las rutas heredadas.

## Opción recomendada para la revisión

Publicar el mismo `compose.analizate.local.yaml` como staging aislado en una
máquina controlada y exponer únicamente el frontend mediante HTTPS, usando un
túnel temporal o un proxy reverso. La API debe seguir en la red privada del
staging y el frontend debe comunicarse con ella a través del proxy de
`server.py`.

Esta opción permite que el cliente pruebe las funciones reales:

- Login, roles y cierre de sesión.
- Creación de pacientes y órdenes.
- Selección de examen y muestra.
- Toma, recepción, rechazo y eliminación.
- Resultados genéricos y microbiológicos.
- Restricción de antibiogramas para exámenes que no son cultivos.
- Validaciones y reportes.

No usar datos clínicos reales, credenciales reales ni el volumen del NAS para
esta revisión.

## Alternativa Netlify posterior

Netlify puede entrar en una segunda etapa como frontend separado, pero requiere
antes:

1. Extraer el frontend de `server.py` o generar una aplicación estática que
   consuma una API externa mediante una variable `API_BASE_URL`.
2. Publicar FastAPI en un servicio capaz de ejecutar Docker o Python.
3. Mantener PostgreSQL en un servicio persistente y respaldado.
4. Configurar CORS solo para el dominio de Netlify y el dominio de staging.
5. Resolver autenticación, expiración JWT, carga de adjuntos y descargas bajo
   HTTPS.
6. Reemplazar las rutas heredadas `/MUFFIN/...` o mantener un adaptador
   compatible en el frontend separado.

No se debe publicar el repositorio actual como sitio estático esperando que la
API y los botones funcionen automáticamente.

## Checklist antes de compartir la URL

- [ ] URL HTTPS de staging, no una URL pública de producción.
- [ ] Base PostgreSQL exclusiva de Analízate y con datos ficticios.
- [ ] Usuario demo con permisos limitados y contraseña temporal.
- [ ] `JWT_SECRET` y contraseñas fuera de Git.
- [ ] PostgreSQL no expuesto a Internet.
- [ ] API accesible solo mediante el proxy del frontend.
- [ ] CORS restringido al dominio de revisión.
- [ ] Adjuntos y reportes verificados sin datos sensibles.
- [ ] Registro de observaciones del cliente por módulo.
- [ ] Copia de respaldo antes de reiniciar o actualizar el staging.

## Flujo recomendado de aprobación

1. El equipo técnico valida localmente en
   `http://127.0.0.1:8879/MUFFIN/Login/Index`.
2. Se replica la misma imagen en staging aislado y se ejecuta la auditoría de
   catálogo.
3. Se entrega al cliente una cuenta demo y una URL HTTPS temporal.
4. El cliente prueba los módulos y registra ajustes funcionales, de texto y de
   catálogo.
5. Se corrigen los hallazgos en `cliente-analizate` y se repite la validación.
6. Solo después de la aprobación se prepara el NAS y la URL pública.

## Estado actual

- Catálogo: 130 exámenes auditados.
- Relaciones examen-muestra: 130/130 correctas según el sembrado.
- API local: saludable.
- Frontend local: saludable.
- Branding Analízate: logo remasterizado y pantalla de ingreso armonizada.
- NAS y URL pública: todavía fuera de esta etapa.

## Documentación externa

- [Netlify Functions](https://docs.netlify.com/build/functions/overview/):
  modelo serverless que Netlify despliega junto al sitio.
- [Netlify Database](https://docs.netlify.com/build/data-and-storage/netlify-database/):
  alternativa administrada si en el futuro se migra el backend y el modelo de
  persistencia a la plataforma.
