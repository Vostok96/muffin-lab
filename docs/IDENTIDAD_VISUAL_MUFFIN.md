# Identidad visual de MUFFIN

Paleta activa para la interfaz operativa. La identidad toma como referencia el icono de MUFFIN: una cobertura microbiologica suave y amable, aplicada con moderacion para mantener legibilidad clinica.

## Estado del diseno

- Diseno de referencia definido: `mirror/SIMCORE_WEB/muffin-operativo.html`.
- Navegacion completa conservada: operacion, consultas, reportes, catalogos y administracion.
- Paleta activa: azul noche en modo claro y azul tinta en modo oscuro.
- El modo oscuro se activa segun la preferencia del sistema o navegador.
- La identidad kawaii se limita al icono y a acentos pastel; la informacion clinica conserva jerarquia y contraste.
- Las rutas y endpoints heredados no se modifican durante el trabajo visual.

## Modo claro

| Uso | Color | Hexadecimal |
| --- | --- | --- |
| Texto principal | Azul marino | `#23324A` |
| Texto secundario | Gris azulado | `#6E7A91` |
| Fondo de aplicacion | Celeste neblina | `#F4F7FC` |
| Superficie y paneles | Blanco lunar | `#FEFEFF` |
| Color primario | Azul noche | `#506C9C` |
| Primario intenso | Azul marino profundo | `#28446E` |
| Acento suave | Celeste bruma | `#BFD6F2` |
| Acento calido | Coral rosado | `#E7A2A5` |
| Acento rosado | Rosa orquidea | `#D6A6C7` |
| Acento violeta | Periwinkle | `#AAB8E0` |
| Bordes | Gris azulado claro | `#E0E6F1` |

## Modo oscuro

| Uso | Color | Hexadecimal |
| --- | --- | --- |
| Texto principal | Blanco azulado | `#F1F5FF` |
| Texto secundario | Gris perla azul | `#B4C0D7` |
| Fondo de aplicacion | Azul noche | `#0D1528` |
| Superficie y paneles | Azul tinta | `#16213A` |
| Color primario | Celeste periwinkle | `#96B5E8` |
| Primario intenso | Azul hielo | `#D6E4FF` |
| Acento suave | Celeste nocturno | `#89B8DB` |
| Acento calido | Coral rosado | `#E6A0A6` |
| Acento rosado | Rosa orquidea | `#DCA9C9` |
| Acento violeta | Lavanda lunar | `#B7C4F1` |
| Bordes | Azul pizarra | `#2E3D5B` |

## Uso

- El modo claro es el predeterminado.
- El modo oscuro se activa automaticamente cuando el sistema operativo o navegador prefiere una interfaz oscura.
- Los colores no definen por si solos un estado clinico. Los resultados, alertas y validaciones deben mantener texto, icono y reglas de negocio explicitas.
- El rosa, durazno, menta y lavanda se reservan para acentos de interfaz; no sustituyen indicadores de criticidad microbiologica.

## Construccion

El avance y el orden tecnico vigente se mantienen en `docs/AVANCE_MUFFIN.md`. Ese documento es la fuente unica para fases, criterios de aceptacion local y despliegue posterior en el NAS.
