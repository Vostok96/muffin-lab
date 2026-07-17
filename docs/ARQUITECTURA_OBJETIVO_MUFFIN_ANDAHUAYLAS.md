# Arquitectura objetivo de MUFFIN para Andahuaylas

Fecha: 2026-07-17

Este documento fija la direccion objetivo para el despliegue inicial de MUFFIN en el Hospital Sub Regional de Andahuaylas. El sistema ya no debe pensarse como una copia local de SIMCORE, sino como una plataforma institucional centralizada y multi-tenant.

## Objetivo

- Una sola aplicacion MUFFIN para varias instituciones.
- Un backend unico con contexto por institucion.
- Un dominio principal comun.
- Un frontend que cambie identidad visual y alcance funcional segun el tenant autenticado.

## Tenant inicial

- Institucion base: `Hospital Sub Regional de Andahuaylas`
- Slug tecnico: `andahuaylas`
- Producto visible: `MUFFIN`
- Dominio de acceso: `sitme.microbiolog-ia.com`

## Principios

- El usuario siempre entra a MUFFIN, no a una instalacion aislada por hospital.
- La institucion activa se resuelve desde el login y se conserva en la sesion/JWT.
- Todo dato clinico, catalogo operativo y configuracion sensible debe filtrarse por `institution_id`.
- La interfaz puede personalizar logo, nombre y tema, pero el modelo de dominio debe ser estable.
- Las diferencias entre hospitales deben resolverse por configuracion, no por ramas de codigo.

## Flujo de acceso

1. El usuario visita `https://sitme.microbiolog-ia.com/login/?next=/`.
2. Ingresa `usuario + contrasena`.
3. El backend valida credenciales y recupera:
   - roles
   - permisos de area
   - institucion asociada
   - configuracion visual
4. El frontend renderiza la sesion con el nombre de la institucion activa.
5. Todas las consultas posteriores operan dentro del tenant autenticado.

## Modelo de datos objetivo

Las tablas clinicas y operativas deben incluir un campo de pertenencia institucional, ya sea de forma directa o por relacion:

- `institution`
- `user.institution_id`
- `patient.institution_id`
- `lab_order.institution_id`
- `exam.institution_id` cuando el catalogo no sea global
- `parameter_definition.institution_id` cuando la parametrizacion sea local
- cualquier catalogo editable por hospital

Reglas:

- `medical_record_number` debe ser unico por institucion, no globalmente si el hospital reutiliza rangos.
- Los codigos operativos deben poder coexistir entre instituciones cuando el negocio lo requiera.
- Los registros historicos nunca deben moverse de tenant.

## Backend

- `FastAPI` como capa de negocio y autorizacion.
- `PostgreSQL` como persistencia comun.
- `JWT` con claims de usuario, roles e institucion.
- `SQLAlchemy + Alembic` para evolucionar el modelo.
- `server.py` solo como puente temporal con el frontend legado.

## Frontend

- Un solo frontend servido bajo el dominio institucional.
- Branding por tenant:
  - nombre de hospital
  - logo
  - texto de bienvenida
  - colores o acentos si se requieren
- No duplicar pantallas por hospital.
- Las reglas de acceso deben depender de datos del backend, no de ocultar botones solamente.

## Despliegue

- Produccion inicial en Andahuaylas.
- Infraestructura unica en el NAS mientras el contrato y la capacidad lo permitan.
- Separacion futura por base de datos o instancia solo si el crecimiento o la seguridad lo exigen.
- HTTPS obligatorio para sesiones reales.

## Orden de construccion

1. Cerrar el contexto institucional en autenticacion y sesion.
2. Hacer que el frontend muestre el nombre del hospital activo.
3. Aplicar `institution_id` a los modelos clinicos y catalogos editables.
4. Mantener compatibilidad temporal con SIMCORE solo donde falte adaptacion.
5. Eliminar dependencias duras del comportamiento local de desarrollo.

## Criterio de exito

MUFFIN queda listo para Andahuaylas cuando:

- el usuario entra con sus credenciales y ve su institucion,
- las ordenes y resultados quedan aislados por tenant,
- la misma aplicacion puede reutilizarse para otros hospitales sin bifurcar el codigo,
- la compatibilidad con SIMCORE ya no define el diseno final.
