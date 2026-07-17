# Paneles de antibiograma y antibióticos — SIMCORE V3.1.15

## Alcance

Este documento registra los paneles configurados en SIMCORE y los antibióticos asociados a cada uno, respetando los nombres, la interpretación predeterminada y el orden mostrados en el sistema.

> **Nota:** La columna **Orden SIMCORE** conserva los valores originales, incluso cuando dos o más antibióticos comparten el mismo número de orden.

---

# Resumen de paneles

| Orden del panel | Panel |
|---:|---|
| 1 | PANEL SIN ATB |
| 10 | PANEL AST-N401 |
| 11 | PANEL AST-N402 |
| 13 | PANEL AST-N403 |
| 15 | PANEL AST-P663 |
| 16 | PANEL AST-ST03 |
| 17 | PANEL AST-YS08 |

---

# 1. PANEL AST-N401

| Orden SIMCORE | Antibiótico | Interpretación predeterminada |
|---:|---|:---:|
| 1 | Amikacina | S |
| 2 | Ampicilina/Sulbactam | S |
| 3 | Cefalotina | S |
| 4 | Cefazolina | S |
| 5 | Ceftazidima | S |
| 5 | Cefepima | S |
| 6 | Ceftriaxona | S |
| 7 | Ciprofloxacina | S |
| 8 | Ertapenem | S |
| 9 | Fosfomicina | S |
| 10 | Gentamicina | S |
| 10 | Nitrofurantoina | S |
| 11 | Trimetoprima/Sulfametoxazol | S |
| 11 | Meropenem | S |
| 12 | Norfloxacina | S |

**Total de antibióticos:** 15

---

# 2. PANEL AST-N402

| Orden SIMCORE | Antibiótico | Interpretación predeterminada |
|---:|---|:---:|
| 1 | Amikacina | S |
| 2 | Ampicilina/Sulbactam | S |
| 3 | Cefazolina | S |
| 4 | Ceftriaxona | S |
| 4 | Cefepima | S |
| 5 | Ciprofloxacina | S |
| 6 | Ertapenem | S |
| 7 | Gentamicina | S |
| 8 | Imipenem | S |
| 9 | Meropenem | S |
| 10 | Piperacilina/Tazobactam | S |
| 11 | Tigeciclina | S |

**Total de antibióticos:** 12

---

# 3. PANEL AST-N403

| Orden SIMCORE | Antibiótico | Interpretación predeterminada |
|---:|---|:---:|
| 1 | Amikacina | S |
| 2 | Ampicilina/Sulbactam | S |
| 3 | Aztreonam | S |
| 4 | Ceftazidima | S |
| 5 | Ciprofloxacina | S |
| 5 | Cefepima | S |
| 5 | Ceftazidime/Avibactam | S |
| 6 | Ertapenem | S |
| 7 | Imipenem | S |
| 8 | Meropenem | S |
| 9 | Piperacilina/Tazobactam | S |
| 9 | Ceftolozane/Tazobactam | S |
| 10 | Tigeciclina | S |

**Total de antibióticos:** 13

---

# 4. PANEL AST-P663

| Orden SIMCORE | Antibiótico | Interpretación predeterminada |
|---:|---|:---:|
| 1 | Ampicilina | S |
| 1 | Bencilpenicilina G | S |
| 2 | Ceftarolina | S |
| 2 | Ciprofloxacina | S |
| 3 | Clindamicina | S |
| 4 | Daptomicina | S |
| 5 | Eritromicina | S |
| 6 | Gentamicina | S |
| 7 | Levofloxacina | S |
| 8 | Linezolid | S |
| 9 | Oxacilina | S |
| 10 | Rifampicina | S |
| 11 | Tetraciclina | S |
| 12 | Vancomicina | S |
| 12 | Trimetoprima/Sulfametoxazol | S |
| 12 | Estreptomicina Alto Carga (Sinergia) | S |
| 13 | Nitrofurantoina | S |

**Total de antibióticos:** 17

---

# 5. PANEL AST-ST03

| Orden SIMCORE | Antibiótico | Interpretación predeterminada |
|---:|---|:---:|
| 1 | Bencilpenicilina G(neumonia) | S |
| 2 | Bencilpenicilina G(oral) | S |
| 3 | Bencilpenicilina G(meningitis) | S |
| 4 | Bencilpenicilina G(otro) | S |
| 5 | Cefotaxima(meningitis) | S |
| 6 | Cefotaxima(otro) | S |
| 7 | Ceftriaxona(meningitis) | S |
| 8 | Ceftriaxona(otro) | S |
| 9 | Eritromicina | S |
| 10 | Clindamicina | S |
| 11 | Linezolid | S |
| 12 | Vancomicina | S |
| 14 | Tetraciclina | S |
| 15 | Tigeciclina | S |
| 16 | Cloramfenicol | S |
| 17 | Rifampicina | S |
| 19 | Trimetoprima/Sulfametoxazol | S |

**Total de antibióticos:** 17

---

# 6. PANEL AST-YS08

| Orden SIMCORE | Antimicrobiano | Interpretación predeterminada |
|---:|---|:---:|
| 1 | Anfotericina B | S |
| 2 | Caspofungin | S |
| 3 | Fluconazol | S |
| 5 | Micafungin | S |
| 6 | Voriconazol | S |

**Total de antimicrobianos:** 5

---

# 7. PANEL SIN ATB

Este panel no contiene antibióticos asociados.

---

# Resumen cuantitativo

| Panel | Cantidad de antimicrobianos |
|---|---:|
| PANEL AST-N401 | 15 |
| PANEL AST-N402 | 12 |
| PANEL AST-N403 | 13 |
| PANEL AST-P663 | 17 |
| PANEL AST-ST03 | 17 |
| PANEL AST-YS08 | 5 |
| PANEL SIN ATB | 0 |
| **Total de relaciones panel–antimicrobiano** | **79** |

---

# Observaciones para implementación

1. Mantener exactamente los nombres utilizados por SIMCORE al realizar una migración o carga masiva.
2. No renumerar automáticamente los campos de orden: existen valores repetidos dentro de varios paneles.
3. La letra `S` corresponde a la interpretación predeterminada configurada en el mantenedor.
4. Antes de ejecutar inserciones en producción, verificar los identificadores reales de:
   - `Mic_orga_panel`
   - `Mic_antibiotico`
   - `Mic_orga_panel_detalle`
5. Realizar una copia de seguridad de la base de datos antes de cualquier carga masiva.
6. Este documento reproduce la configuración extraída del sistema; no constituye una recomendación clínica ni sustituye las reglas vigentes de CLSI, EUCAST o el fabricante.

