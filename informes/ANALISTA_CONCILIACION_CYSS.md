# ANALISTA_CONCILIACION_CYSS.md — Cyss vs subcontratistas por capítulo

_Generado el 2026-07-09._

---

## Metodología

Se compara **cada capítulo del presupuesto de Cyss v2.0** (el vigente) con las ofertas de subcontratistas independientes para el mismo oficio. El objetivo es detectar:
- **Sobreprecio de Cyss**: cuando Cyss es más caro que la subcontrata directa.
- **Alcance reducido de Cyss**: cuando Cyss es más barato pero probablemente incluye menos partidas.
- **Partidas sin equivalente**: trabajos que Cyss incluye pero la subcontrata no, o viceversa.
- **Gaps**: oficios que Cyss no cubre pero son necesarios.

### Nota sobre el IVA

Cyss aplica **10%** (tipo reducido de rehabilitación). Las subcontratas aplican **21%**. Para comparar manzanas con manzanas, la columna principal es **Base Imponible** (sin IVA). La columna "Con IVA" se incluye como referencia del coste real de cada opción.

---

## Capítulo 01 — DEMOLICIÓN

| Concepto | Cyss v2.0 | Subcontrata | Diferencia |
|---|---|---|---|
| Base Imponible | **4.571,48 €** | — | No hay oferta independiente |
| Con IVA (c/tipo) | 5.028,63 € | — | — |

**Subcontrata disponible**: No. El único PDF de demolición es el plano legacy `desconocido_Demolición.pdf` que no contiene presupuesto.

**Análisis**: Cyss v2.0 subió este capítulo un **27,4%** respecto a v1 (de 3.587,67 a 4.571,48 €). El incremento se debe a más metros cuadrados de partición (14,65 → 36 m² según el myp). Es razonable si las mediciones son correctas. Sin oferta alternativa, no hay base para decir si es caro o barato.

**Veredicto**: Sin alternativa. Asumir precio Cyss.

---

## Capítulo 02 — ALBAÑILERÍA

| Concepto | Cyss v2.0 | Subcontrata (Toni 472) | Diferencia |
|---|---|---|---|
| Base Imponible | **13.880,05 €** | **17.725,00 €** | **Cyss -3.844,95 € (-21,7%)** |
| Con IVA (c/tipo) | 15.268,06 €* | 21.447,25 € | Cyss -6.179,19 € |
| Partidas sin precio | 0 | 5 | Riesgo en Toni (+2.000–3.700 € est.) |

_* Proporcional dentro del total Cyss._

### Análisis detallado

| Partida | Cyss v2.0 | Toni 472 | Observación |
|---|---|---|---|
| Fachada ladrillo | ✅ Incluida (PTZ010e) | Partidas 2.1–2.3 (5.750 €) | Cyss probablemente más barato |
| Falcado ventanas | ✅ Incluido | Partidas 2.2–2.7 (2.250 € + 2 sin precio) | Similar |
| Colocación pavimento | ✅ Incluido (RAG012 + RAG012c) | Partidas 2.9–2.10 (2.030 €) | Difícil cotejo por mediciones |
| Alicatado | ✅ Incluido (RAG012b) | Partidas 2.11–2.13 (470 €) | **Cyss muy superior** → más m² |
| Colocación plato ducha | ✅ Incluido (SMS020) | 200 € | Precio unitario similar |
| Colocación bañera | ✅ Incluido (SMS020b) | 220 € | Precio unitario similar |
| Picado de pilar | ✅ Incluido (DPP100b) | 2.400 € | Partida muy cara en Toni |
| Pintura plástica | ✅ Incluido (RIP035) | **Sin precio** | Posible coste oculto en Toni |
| Colocación casoneto | ✅ Incluido (FCL060o) | 3.780 € | **Diferencia enorme** — Cyss mucho más barato |
| Nivelación mortero | ✅ Incluido (RSB020) | — | En Toni está dentro de otras partidas |

**⚠️ Riesgo de alcance reducido en Cyss v2.0**: El cap.02 bajó de 22.700,96 € (v1) a 13.880,05 € (v2.0). La diferencia se explica porque ciertas partidas (yeso, alicatado, colocación pavimento) se movieron al cap.03 (Pladur). **No es un ahorro real, es una reasignación contable**. Hay que verificar que el alcance total (cap.02 + cap.03) es equivalente al de Toni 472.

**Veredicto**: ⚠ **Cyss aparentemente más barato, pero hay que confirmar que el alcance combinado cap.02+03 equivale a Toni 472**. Si es así, Cyss gana. Si Toni cierra sus 5 partidas pendientes, la diferencia se reduce.

---

## Capítulo 03 — PLADUR

| Concepto | Cyss v2.0 | Subcontrata | Diferencia |
|---|---|---|---|
| Base Imponible | **10.448,45 €** | — | No hay oferta independiente |
| Con IVA | 11.493,30 € | — | — |

**Subcontrata disponible**: No. El único PDF es el plano legacy `desconocido_Pladur.pdf` sin presupuesto.

**Análisis**: Cyss v2.0 subió este capítulo un **119%** respecto a v1 (de 4.767,86 a 10.448,45 €). Ahora incluye tabiques, trasdosados, placa hidrófuga y falso techo. El importe incluye material + mano de obra. Para una vivienda de 97 m², el coste de ~108 €/m² de falso techo + tabiques es razonable.

**Veredicto**: Sin alternativa. Si se busca ahorro, pedir oferta a un instalador de pladur local podría revelar ahorros del 20–30%.

---

## Capítulo 04 — INSTALACIÓN ELÉCTRICA

| Concepto | Cyss v2.0 | Paracon | Poveda | Diferencia |
|---|---|---|---|---|
| Base Imponible | **7.129,20 €** | **5.005,00 €** | 5.291,00 € | **Paracon -2.124,20 € (-29,8%)** |
| Con IVA (c/tipo) | 7.842,12 € | 6.056,05 € | 6.402,11 € | Paracon -1.786,07 € |
| Partidas con precio | 11 códigos | No detallado | 4 partidas | — |

### Desglose de partidas Cyss cap.04

| Código | Descripción |
|---|---|
| IEC020 | Cuadro eléctrico elevado vertical |
| IEC020j | Cuadro telecomunicaciones |
| IEC020c | Punto de enchufe 16A |
| IEC020g | Punto de enchufe 25A |
| IEC020f | Interruptores, conmutadores y cruces |
| IEC020h | Suministro y colocación telefonillo universal |
| IEC020e | Punto de luz con pulsador y timbre |
| IEC020d | Punto de luz Techo/Pared 10A |
| IEC020i | Punto TV |
| IEC020b | Punto de Datos 16A |
| RAG012k | Ayudas albañilería a instalación eléctrica |

### Lo que incluye Cyss y NO incluye Paracon (potencialmente)

| Concepto | Precio estimado |
|---|---|
| Videoportero a color (Poveda: 400 €) | ~400 € |
| Red de telecomunicaciones (Poveda: 560 €) | ~560 € |
| Downlights / iluminación empotrada (Poveda: 756 €) | ~756 € |
| Ayudas albañilería (RAG012k) | ~300–500 € |
| **Total partidas potencialmente adicionales** | **~2.016–2.216 €** |

Si Paracon no incluye estos conceptos, su coste real sería ~6.056 + 2.016 = **~8.072 €**, superando a Cyss (7.842 €).

### ⚠ Posible sobrecoste de Cyss

Si Paracon SÍ incluye todo el alcance de Cyss (videoportero, red, ayudas), entonces **Cyss es un 29,8% más caro en base** — un sobrecoste claro.

**Veredicto**: ⚠ **Posible sobrecoste de Cyss de 1.786 €** si Paracon cubre el mismo alcance. Pero hay que confirmar el alcance de Paracon antes de decidir.

---

## Capítulo 05 — INSTALACIÓN FONTANERÍA

| Concepto | Cyss v2.0 | DB 1-000079 | DB 1-000022 DEF (combo) | Diferencia |
|---|---|---|---|---|
| Base Imponible | **4.400,00 €** | **3.359,99 €** | 9.857,22 € (font+clima) | **DB -1.040,01 € (-23,6%)** |
| Con IVA (c/tipo) | 4.840,00 € | 4.065,60 € | 11.927,23 € | DB -774,40 € |

### Desglose de partidas Cyss cap.05

| Código | Descripción |
|---|---|
| IFI010d | Acometida de agua general y llave de corte general |
| IFI010c | Instalación fontanería cocina |
| IFI010 | Instalación interior baño 1 |
| IFI010b | Instalación interior baño 2 |
| IGI005b | Instalación desagüe para máquina centralizada ACC |
| RAG012h | Ayudas albañilería a fontanería |

### Lo que incluye Cyss que DB puede no incluir

Cyss incluye explícitamente "Ayudas albañilería a fontanería" (RAG012h). David Barat (subcontrata de instalaciones) probablemente no incluye ayudas de albañilería — esas se las cobraría Toni aparte. Este coste puede ocultarse y reaparecer en la factura de albañilería.

### ⚠ Doble riesgo

1. **Oferta DB 1-000079 desactualizada** (nov 2025). Posible subida de precios.
2. **Ayudas de albañilería**: si se contrata fontanería directa, hay que pagar a Toni (o a quien haga la albañilería) las catas, rozas y ayudas. Ese coste está dentro del cap.05 de Cyss pero no en la oferta de DB.

**Veredicto**: ⚠ **Posible sobrecoste de Cyss de ~774 €**, pero el ahorro real puede ser menor si hay que pagar ayudas de albañilería aparte (~200–400 €).

---

## Capítulo 06 — INSTALACIÓN CLIMATIZACIÓN

| Concepto | Cyss v2.0 | DB 1-000084 | DB 1-000022 DEF (combo) | Diferencia |
|---|---|---|---|---|
| Base Imponible | **6.594,00 €** | **6.176,27 €** | 9.857,22 € (font+clima) | **DB -417,73 € (-6,3%)** |
| Con IVA (c/tipo) | 7.253,40 € | 7.474,29 € | 11.927,23 € | Cyss -220,89 € |

### Análisis de alcance

| Partida | Cyss v2.0 | DB 1-000084 |
|---|---|---|
| Red de conductos | ✅ ICX010i | Probablemente incluido |
| Máquina climatización | ✅ ICX010h (posible cambio de modelo: ICX010h vs ICX010g en v1) | Solo se menciona "partidas vacías" |
| Preinstalaciones líneas frigoríficas | ✅ ICX010b | — |
| Ayudas albañilería | ✅ RAG012m | No incluido |

**⚠️ Diferencia de sistema**: Cyss v2.0 añade "Preinstalaciones de líneas frigoríficas de cobre" (ICX010b, nueva en v2.0) y cambia el código de la máquina (ICX010g → ICX010h), lo que sugiere un modelo o especificación diferente. La oferta de DB 1-000084 puede ser para un sistema split convencional, no por conductos.

**Veredicto**: ⚠ **Comparativa no fiable por posible diferencia de alcance/sistema**. Pedir a DB oferta actualizada especificando sistema por conductos equivalente al de Cyss.

---

## Capítulo 13 — ILUMINACIÓN

| Concepto | Cyss v2.0 | Subcontrata | Diferencia |
|---|---|---|---|
| Base Imponible | **1.552,22 €** | — | No hay oferta independiente |
| Con IVA | 1.707,44 € | — | — |

**Subcontrata disponible**: No. Parocon explícitamente dice "no incluye iluminación". Poveda sí incluía 27 downlights (756 €).

**Veredicto**: Sin alternativa real. Mantener en Cyss.

---

## Capítulo 14 — VARIOS

| Concepto | Cyss v2.0 | Subcontrata | Diferencia |
|---|---|---|---|
| Base Imponible | **2.950,00 €** | — | No hay oferta independiente |
| Con IVA | 3.245,00 € | — | — |

Incluye trabajos verticales (plataforma elevadora para fachada) y contenedores de escombros. Subió 350 € respecto a v1. Sin alternativa.

**Veredicto**: Asumir precio Cyss.

---

## Oficios NO incluidos en Cyss

| Oficio | Subcontrata | Importe (base) | IVA | Total |
|---|---|---|---|---|
| Carpintería exterior | Ventanas Nacher | 8.389,65 € | 21% | 10.151,48 € |
| Carpintería interior | Valenzuela | 22.435,47 € | 21% | 27.146,92 € |
| Encimeras | **PENDIENTE** | **¿?** | 21% | **¿?** |

---

## Tabla resumen de conciliación

| Capítulo | Cyss v2.0 (base) | Subcontrata (base) | Diferencia | ¿Quién gana? | Riesgo |
|---|---|---|---|---|---|
| 01 DEMOLICIÓN | 4.571,48 € | — | — | Solo Cyss | — |
| 02 ALBAÑILERÍA | 13.880,05 € | 17.725,00 € (Toni) | **-3.845 €** Cyss | ✅ **Cyss** | ⚠ Alcance redistribuido a cap.03 |
| 03 PLADUR | 10.448,45 € | — | — | Solo Cyss | — |
| 04 ELECTRICIDAD | 7.129,20 € | 5.005,00 € (Paracon) | **+2.124 €** Cyss | ❌ **Paracon** | ⚠ Alcance Paracon no detallado |
| 05 FONTANERÍA | 4.400,00 € | 3.360,00 € (DB 079) | **+1.040 €** Cyss | ❌ **DB** | ⚠ Ayudas albañilería no incluidas |
| 06 CLIMATIZACIÓN | 6.594,00 € | 6.176,27 € (DB 084) | **+418 €** Cyss | ❌ **DB** (marginal) | ⚠ Pueden ser sistemas distintos |
| 13 ILUMINACIÓN | 1.552,22 € | — | — | Solo Cyss | — |
| 14 VARIOS | 2.950,00 € | — | — | Solo Cyss | — |
| **SUBTOTAL Cyss** | **51.525,40 €** | | | | |
| **SUBTOTAL híbrido** | | **32.266,27 €** (sin cap.04+05+06) + 5.005+3.360+6.176 = **46.807,27 €** | | | |
| Carp. exterior | ❌ No incluido | 8.389,65 € (Nacher) | — | Directa | — |
| Carp. interior | ❌ No incluido | 22.435,47 € (Valenzuela) | — | Directa | — |
| Encimeras | ❌ No incluido | **PENDIENTE** | — | **CRÍTICO** | Sin presupuesto |

---

## Conclusiones por capítulo

### Dónde Cyss es más caro (posible sobrecoste)

| Capítulo | Sobreprecio Cyss (base) | % |
|---|---|---|
| 04 ELECTRICIDAD | +2.124 € | +29,8% |
| 05 FONTANERÍA | +1.040 € | +23,6% |
| 06 CLIMATIZACIÓN | +418 € | +6,3% |
| **Total sobrecoste en instalaciones** | **+3.582 €** | |

### Dónde Cyss es más barato (posible alcance reducido)

| Capítulo | Ahorro Cyss (base) | % |
|---|---|---|
| 02 ALBAÑILERÍA | -3.845 € | -21,7% |

**⚠️ Precaución**: El aparente ahorro en albañilería se debe en parte a que Cyss ha movido partidas al cap.03 (Pladur). El ahorro real de Cyss en obra gruesa (cap.01+02+03) vs ninguna alternativa directa es difícil de cuantificar sin una oferta de pladur independiente.

### Dónde no hay equivalencia (gaps)

| Concepto | Estado |
|---|---|
| Encimeras DEKTON + SILESTONE | **CRÍTICO: Sin presupuesto** |
| Ayudas albañilería a instalaciones | Incluidas en Cyss pero no en subcontratas. Pueden reaparecer. |
| Downlights / iluminación empotrada | En Cyss cap.13. Paracon no los incluye. Poveda sí. |
| Videoportero y red telecomunicaciones | En Cyss cap.04. Paracon no confirma. Poveda sí los detalla. |

---

## Decisión final: por qué el híbrido ahorra ~2.340 €

La cuenta real después de ajustar por IVA y alcance:

| Movimiento | Ahorro real (con IVA) |
|---|---|
| Sacar electricidad de Cyss → Paracon | **-1.786 €** (7.842 Cyss vs 6.056 Paracon) |
| Sacar fontanería de Cyss → DB 1-000079 | **-774 €** (4.840 Cyss vs 4.066 DB) |
| Sacar clima de Cyss → DB 1-000084 | **+221 €** (Cyss más barato: 7.253 vs 7.474 DB) |
| **Ahorro neto** | **-2.339 €** |

Este ahorro, sobre un total de ~94.000 €, representa un **2,5%**. La pregunta para el cliente: ¿2.500 € de ahorro justifican gestionar 3 contratos de instalaciones adicionales?
