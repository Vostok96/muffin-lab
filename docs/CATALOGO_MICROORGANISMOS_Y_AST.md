# Catalogo de microorganismos y modelo AST

## Decision de integracion

MUFFIN ya dispone de la tabla operativa `organism`, con UUID, codigo estable,
nombre y estado activo. Los aislados clinicos referencian esa tabla mediante
`isolate.organism_id`. Crear otra tabla operativa llamada
`catalogo_microorganismos` duplicaria los datos y dejaria el nuevo catalogo sin
relacion con resultados, auditoria, API ni VITEK.

El archivo `catalogo_microorganismos.sql` satisface el formato de intercambio
solicitado (`id` autoincremental y `nombre_cientifico`), pero no debe desplegarse
junto con `organism`. La migracion `0008_ast_catalogs` carga los 2.452 nombres
revisados directamente en `organism` con codigos deterministas para evitar una
tabla operativa duplicada.

## Depuracion de la fuente

- Fuente: `lista.txt`, codificada en CP1252.
- Filas logicas: 2.540.
- Filas de JavaScript o vacias descartadas: 5.
- Duplicados exactos normalizados descartados: 9.
- Valores separados por no ser nombres cientificos: 74.
- Nombres candidatos conservados: 2.452.

La normalizacion convierte espacios no separables, colapsa espacios, aplica
Unicode NFC y deduplica sin distinguir mayusculas de minusculas. Conserva la
primera grafia encontrada y no aplica `upper`, `lower` ni `title`, porque eso
alteraria la nomenclatura cientifica, siglas, serotipos y nombres virales.

Los 74 valores separados estan en
`catalogo_microorganismos_cuarentena.csv`. Incluyen resultados negativos como
`No growth`, estados operativos como `Rejected sample`, flora normal y
categorias generales como `Gram negative rods` o `Yeast`. Esos conceptos deben
modelarse como resultados, comentarios o categorias, nunca como organismos.

La lista sigue necesitando validacion taxonomica humana. Se conservaron de
forma intencional complejos, grupos, nombres a nivel de genero, identificaciones
compuestas y posibles errores ortograficos para no corregir silenciosamente un
dato clinico.

## Modelo relacional operativo

```text
result 1 --- N isolate N --- 1 organism
                   |
                   +--- 0..1 colony_count_option
                   |
                   +--- 0..1 ast_panel
                              |
                              N
                    ast_panel_antibiotic
                              N
                              |
                           antibiotic

isolate 1 --- N antimicrobial_result N --- 1 antibiotic
```

### Identificacion y cultivo

- `result`: resultado general vinculado de manera unica a un item de orden.
- `isolate`: un aislamiento identificado dentro de un resultado; almacena
  microorganismo, recuento, fenotipo, comentario y panel AST seleccionado.
- `organism`: catalogo unico de microorganismos.
- `colony_count_option`: catalogo de recuentos semicuantitativos.

### Panel y sensibilidad

- `antibiotic`: catalogo unico de antimicrobianos.
- `ast_panel`: definicion reutilizable de un panel de sensibilidad.
- `ast_panel_antibiotic`: relacion entre panel y antibiotico, con orden de
  presentacion y metodo predeterminado.
- `antimicrobial_result`: resultado por aislado y antibiotico; contiene CMI o
  valor, interpretacion, metodo y marca de reporte.

La combinacion `(isolate_id, antibiotic_id)` es unica. Las interpretaciones
admitidas son `S`, `SDD`, `I`, `R`, `POS`, `NEG` y `NA`. Un panel asignado no
puede validarse mientras conserve filas `NA` o no tenga resultados AST.

## Flujo manual

1. El item debe estar recibido y tener un resultado materializado.
2. El usuario agrega un aislado seleccionando microorganismo y panel.
3. El panel crea sus filas AST con interpretacion `NA`.
4. El usuario registra CMI/valor, interpretacion, metodo y si se reporta.
5. Se guardan primero identificacion y AST, y luego el resultado general.
6. La validacion preliminar exige parametros obligatorios y AST completo.
7. Cualquier cambio microbiologico invalida la validacion preliminar.
8. Un resultado final requiere reapertura antes de modificar aislados o AST.

## Procedencia y fechas

El antiguo campo `Tipo de localizacion` representa el ambito asistencial, no el
sitio anatomico. Ahora se muestra como `Ambito asistencial (derivado)` y no se
captura manualmente. La API lo calcula a partir de procedencia y servicio como
ambulatorio, hospitalizacion general, cuidados intermedios, UCI, urgencia o
desconocido. Es util para vigilancia epidemiologica y antibiogramas acumulados
sin duplicar el catalogo de servicios.

Las fechas de toma y recepcion aceptan fechas historicas. La API rechaza fechas
futuras y una recepcion anterior a la toma. Las correcciones se auditan y no se
permiten una vez validado, rechazado o cancelado el resultado.

## Generacion reproducible

Desde la raiz del proyecto:

```bash
python3 backend/scripts/build_organism_catalog.py
```

El script verifica el SHA-256 de la fuente y los conteos esperados antes de
reemplazar el SQL y la cuarentena.
