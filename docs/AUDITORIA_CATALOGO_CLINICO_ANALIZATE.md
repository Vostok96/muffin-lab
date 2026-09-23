# Auditoría clínica del catálogo de Analízate

Fecha: 2026-09-22  
Alcance: rama `cliente-analizate` únicamente.

## Criterio

Una relación clínica no debe mezclar cuatro conceptos distintos:

1. Examen solicitado.
2. Espécimen o material biológico.
3. Método o técnica de toma/procesamiento.
4. Contenedor, aditivo y condiciones de transporte.

El catálogo actual puede seleccionar la muestra y conserva el contenedor, pero
todavía no tiene campos independientes para método, aditivo, volumen,
temperatura o tiempo máximo. Por eso los casos inequívocos se corrigieron en
el catálogo y los perfiles complejos quedan marcados para una ampliación de
modelo, evitando aparentar una precisión clínica que no existe.

## Correcciones aplicadas

| Examen o grupo | Espécimen correcto | Contenedor / toma |
|---|---|---|
| Examen de ácaros en piel y pestañas | Raspado de piel y pestañas | Lámina |
| Análisis de gases arteriales AGA | Sangre arterial | Jeringa heparinizada |
| INR, TPT, TTPA, fibrinógeno, dímero D | Plasma citratado | Tubo con citrato de sodio |
| Perfil de coagulación | Plasma citratado | Tubo con citrato de sodio |
| Test de embarazo en orina | Orina | Frasco |
| ADA de líquido cefalorraquídeo | Líquido cefalorraquídeo | Frasco |

Los nombres antiguos de Ácaros y Test de embarazo se migran por alias para no
crear duplicados en bases ya sembradas.

## Revisión por área

- Bioquímica: suero es coherente para el catálogo actual; confirmar con cada
  plataforma si algunos analitos se procesan preferentemente en plasma.
- Microbiología: orina, heces, semen, esputo y secreciones son coherentes como
  categorías generales. Cultivo de hongos y examen directo de hongos necesitan
  subtipos de material, por ejemplo piel, uña, cabello o secreción.
- Urianálisis: orina y orina de 24 horas son coherentes; el catálogo debe
  distinguir muestra aislada de recolección temporizada en instrucciones de
  toma.
- Semen: semen es coherente; espermatograma y espermocultivo necesitan
  instrucciones de abstinencia, recolección completa y tiempo de entrega.
- Hematología: sangre total es coherente para hemograma, reticulocitos, grupo
  sanguíneo y gota gruesa; suero es coherente para hierro, ferritina, B12 y
  folato; coagulación requiere plasma citratado.
- Inmunología, endocrinología y marcadores tumorales: suero es una relación
  inicial razonable, pero debe verificarse contra el inserto y plataforma del
  proveedor, sobre todo para pruebas tercerizadas.
- Parasitología: heces, lámina y raspados deben mantenerse como materiales
  distintos. La prueba de Graham requiere cinta adhesiva perianal y no debe
  reutilizarse como una lámina genérica.
- Anatomía patológica: tejido, frotis cervicovaginal, líquidos y bloque celular
  son materiales diferentes; no deben resolverse todos como “líquido biológico”.

## Casos que requieren ampliación

Los perfiles preoperatorio, de gestante, de anemia carencial, de anemia
hemolítica y otros perfiles clínicos pueden incluir simultáneamente sangre
total, suero, orina y/o plasma citratado. Una sola muestra elegible no
representa correctamente esos perfiles. La solución propuesta es que un
perfil sea un conjunto de exámenes componentes, cada uno con su propia muestra,
contenedor y método; al crear la orden, MUFFIN debe generar sus componentes o
solicitar las muestras requeridas de forma explícita.

## Próximo cambio de modelo

Agregar a la relación examen-muestra:

- `collection_method` o técnica de toma.
- `container_id` y `additive` cuando el contenedor no sea suficiente.
- `patient_preparation`.
- `transport_conditions` y estabilidad.
- `is_required` y `display_order` para perfiles multiespecimen.

La validación final de estos campos debe realizarla el responsable del
laboratorio y, para exámenes tercerizados, contrastarse con el manual del
proveedor. Las relaciones corregidas en esta auditoría se basan en prácticas
preanalíticas generales; no sustituyen las instrucciones del fabricante.

## Referencias de control

- [MedlinePlus: prueba de embarazo](https://medlineplus.gov/lab-tests/pregnancy-test/),
  que distingue muestras de orina y sangre para hCG.
- [IARC/WHO: recolección de especímenes biológicos](https://precama.iarc.who.int/methods/biological-specimen-collection/),
  como referencia general para diferenciar suero, plasma y sangre total.
- [WHO: gestión de muestras y contenido preanalítico](https://extranet.who.int/hslp/who-hslp-download/package/501/material/179),
  para mantener separadas la muestra, la toma y las condiciones de manejo.
