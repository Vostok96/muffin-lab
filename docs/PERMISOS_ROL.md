# Permisos por rol — MUFFIN

## Roles del sistema

| Rol | Código | Descripción |
|---|---|---|
| **Administrador** | `ADMIN` | Acceso total: usuarios, catálogos, áreas, auditoría, borrado de aislados. |
| **Admin de procesos** | `PROCESS_ADMIN` | Catálogos (CRUD), validación preliminar/final, aislados y AST. Sin acceso a usuarios. |
| **Procesador** | `PROCESSOR` | Resultados (guardar, validar preliminar/final si tiene permiso de área), aislados y AST. Sin catálogos. |
| **Ingreso** | `ENTRY` | Pacientes, órdenes, items, print jobs, notificaciones. Sin resultados. |
| **Consultas** | `CONSULTANT` | Solo lectura: pacientes, órdenes, resultados, catálogos. |
| **Toma de muestras** | `COLLECTOR` | Registrar toma y recepción de muestras. Sin acceso a resultados. |
| **Clínico** | `CLINICIAN` | Solo lectura limitada: consultas de resultados de sus pacientes. |

## Permisos de área

Los roles `PROCESSOR` y `PROCESS_ADMIN` requieren permisos explícitos por área de laboratorio para validar resultados:

| Permiso | Significado |
|---|---|
| `can_preliminary_validate` | Puede hacer validación preliminar en esa área |
| `can_final_validate` | Puede hacer validación final en esa área |

El rol `ADMIN` tiene validación implícita en todas las áreas sin necesidad de permisos explícitos.

## Qué puede hacer cada rol

| Acción | ADMIN | PROCESS_ADMIN | PROCESSOR | ENTRY | COLLECTOR | CONSULTANT | CLINICIAN |
|---|---|---|---|---|---|---|---|
| Crear/editar usuarios | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Crear/editar catálogos | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Ver catálogos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Crear/editar pacientes | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Crear/editar órdenes | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Registrar toma de muestra | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Registrar recepción | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Guardar resultados | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Validar resultados (preliminar) | ✅ | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ |
| Validar resultados (final) | ✅ | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ |
| Reabrir resultado validado | ✅ | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ |
| Crear/editar aislados | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Borrar aislados | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Crear/editar AST | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Eliminar paciente desde UI | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Retirar examen de orden | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Print jobs / notificaciones | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Mensajes de instrumento | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver auditoría | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Ver resultados (lectura) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

*Requiere permiso de área (`can_preliminary_validate` / `can_final_validate`)

Desde 2026-08-13, los endpoints de validacion preliminar, validacion final y
reapertura tambien exigen rol `ADMIN`, `PROCESS_ADMIN` o `PROCESSOR`. Un permiso
de area asignado por error no debe habilitar validacion a `CONSULTANT`.

En la variante Andahuaylas, `CONSULTANT` se usa para usuarios de solo lectura en
la pantalla `Resultados`: buscar y visualizar resultados, sin mutaciones.

## Mapeo SIMCORE → MUFFIN

| SIMCORE (número) | MUFFIN (código) |
|---|---|
| 1 — Admin Super | `ADMIN` |
| 2 — Admin Usuario Procesos | `PROCESS_ADMIN` |
| 3 — Usuario Procesos | `PROCESSOR` |
| 4 — Usuario Ingreso / Consultas | `ENTRY` |
| 5 — Usuario Consultas | `CONSULTANT` |
| 6 — Usuario Toma de Muestras | `COLLECTOR` |
| 7 — Médico Consultas | `CLINICIAN` |
