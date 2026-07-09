# Verificación de Mediciones — Aparejador

_Generado el 2026-07-09._

## 1. Superficies de referencia desde planos

### Estado inicial (PEA.01)

| Estancia | Superficie (m²) | Altura (m) |
|---|---:|---:|
| Estancia 1 | 16,4 | 2,52 |
| Estancia 2 | 8,1 | 2,54 |
| Estancia 3 | 13,7 | 2,31 |
| Estancia 4 | 24,8 | 2,54 |
| Estancia 5 | 2,6 | 2,31 |
| Estancia 6 | 4,5 | 2,29 |
| Estancia 7 | 4,6 | 2,29 |
| Estancia 8 | 9,7 | 2,53 |
| Estancia 9 | 12,8 | 2,53 |
| **Total** | **97,2** | — |

**Nota**: La suma de superficies (97,2 m²) incluye el espesor de particiones interiores. La superficie pavimentada real será inferior (~88-92 m²).

### Distribución propuesta (PEA.02)

El plano de distribución tiene menos texto extraíble, pero se conservan las mismas dimensiones generales. No hay datos de superficies por estancia en el texto extraído.

---

## 2. Capítulo 01 — Demolición (Cyss v2.0)

### Verificación de unidades

| Código | Descripción | Ud | Cantidad Cyss | Precio Ud | Importe | Coherencia |
|---|---|---|---|---|---|---|
| DSM010c | Demolición cocina | Ud | 1 | 800,00 € | 800,00 € | ✅ 1 cocina |
| DSM010b | Demolición baño | Ud | **2** | 600,00 € | 1.200,00 € | ⚠️ En planos solo se ve 1 baño completo + 1 baño parcial (2 estancias) |
| DPT020c | Demolición partición interior | m² | **92,16** | 18,00 € | 1.658,88 € | ✅ 36 ml × 2,56 m = 92,16 m². Coherente con nueva tabiquería |
| DPT020 | Demolición falso techo | m² | **10,6** | 12,00 € | 127,20 € | ⚠️ Solo pasillo. ¿Faltan falsos techos de otras estancias? |
| DPT020d | Ampliación hueco ventana V07 | m² | **0,726** | 100,00 € | 72,60 € | ✅ 0,60 × 1,21 m |
| DRS011c | Levantado pavimento | m² | **2,6** | 18,00 € | 46,80 € | ⚠️ Solo balcón. ¿No se levanta el pavimento interior? |
| DRS011 | Levantado rodapié | m | **63** | 2,00 € | 126,00 € | ✅ Perímetro estimado de la vivienda |
| DFC010c | Levantado ventana | Ud | **6** | 20,00 € | 120,00 € | ✅ Coincide con V01-V06 |
| DFC010 | Levantado ventanal | Ud | 1 | 40,00 € | 40,00 € | ✅ 1 ventanal |
| DPP020 | Desmontaje puertas | Ud | **7** | 10,00 € | 70,00 € | ✅ |
| DPP020c | Desmontaje armario | Ud | **3** | 60,00 € | 180,00 € | ✅ |
| DPP020d | Desmontaje calentador | Ud | 1 | 10,00 € | 10,00 € | ✅ |
| DPP020e | Desmontaje split s/ recuperación | Ud | 1 | 10,00 € | 10,00 € | ✅ |
| DPP020b | Desmontaje split c/ recuperación | Ud | 2 | 55,00 € | 110,00 € | ✅ |
| | **TOTAL cap. 01** | | | | **4.571,48 €** | |

**⚠️ Incidencias detectadas**:
- **DRS011c** (levantado pavimento): solo 2,6 m² en balcón. El pavimento interior existente (88,3 m²) **no se demuele** según Cyss; se coloca el nuevo sobre el existente o se nivela con mortero (partida RSB020 está en v1 pero **desapareció en v2.0**). Esto puede afectar cotas de puertas y altura de trasdosados.
- **DPT020** (demolición falso techo): 10,6 m² solo en pasillo pero luego Cyss instala 93,4 m² de falso techo nuevo (cap. 03). ¿Los techos existentes no se demuelen, se trasdosan por debajo? Habrá que verificarlo.
- **DPT020c**: 92,16 m² de demolición de particiones. El volumen es coherente con una reforma integral que abre espacios.

---

## 3. Capítulo 02 — Albañilería (Cyss v2.0)

### Pavimentos

| Partida | Código | Superficie Cyss | Precio Ud | Importe |
|---|---|---|---|---|
| Pavimento porcelánico imitación madera 25×150 | RAG012 | **88,3 m²** | 52,00 € | 4.591,60 € |
| Pavimento porcelánico mármol travertino 60×120 | RAG012c | **6,6 m²** | 52,00 € | 343,20 € |
| **Total pavimento** | | **94,9 m²** | | **4.934,80 €** |

**Verificación frente a planos**:
- Estado inicial: 97,2 m² totales ≈ descontando particiones → ~88-92 m² habitables
- 88,3 + 6,6 = 94,9 m² en Cyss. **Supera la superficie habitable estimada** (~5-7 m² de más).
- Posible explicación: Los 6,6 m² de travertino (balcón/terraza) están incluidos en el total de Cyss pero su superficie ya se contabiliza en el estado inicial. 
- **Discrepancia: ~5% por exceso.** No crítica pero conviene verificar el reparto entre formatos.

### Alicatados

| Código | Descripción | Medición Cyss | Cálculo desde planos |
|---|---|---|---|
| RAG012b | Alicatado porcelánico 60×120 | **38,826 m²** | Baño 1: 6,60 × 2,30 = 15,18 m² |
| | | | Baño 2: 11,30 × 1,20 = 13,56 m² |
| | | | Salón (cocina?): 4,10 × 2,46 = 10,09 m² |
| | | | **Total: 38,83 m²** ✅ |

**Coherente.** Las alturas de alicatado (h=2,30 m baños, h=2,46 m salón-cocina) coinciden con lo indicado en el plano de albañilería PEI.01.

### Pintura

| Código | Superficie Cyss | Desglose |
|---|---|---|
| RIP035 | **296,2 m²** | Techos: 92,2 m² + Paredes: 81,55×2,40=195,72 + 14,90×1,20=17,88 − Ventanas 9,6 = 204 m² |

- **Techos**: 92,2 m² vs 93,4 m² de falso techo (cap. 03). Diferencia de 1,2 m² (~1,3%) — **asumible**, probablemente el falso techo cubre zonas que no se pintan (registros, huecos).
- **Paredes**: 204 m². Perímetro estimado de 81,55 + 14,90 = 96,45 ml × altura media 2,40 m = 231,5 m² brutos − huecos. El descuento de 9,6 m² de ventanas parece **insuficiente** si hay 6 ventanas + 1 ventanal (estimación ~15-18 m² de huecos). **Discrepancia leve (~5-8 m² por exceso).**

---

## 4. Capítulo 03 — Pladur (Cyss v2.0)

| Código | Descripción | Cantidad | Precio | Importe |
|---|---|---|---|---|
| PTW070f | Tabique pladur 94 mm (2+1 placas + lana roca) | **45,974 m²** | 62,80 € | 2.887,17 € |
| PTW070c | Trasdosado autoportante 60 mm + lana roca | **61,298 m²** | 42,40 € | 2.599,04 € |
| PTW070b | Falso techo continuo pladur + lana roca | **93,4 m²** | 38,60 € | 3.605,24 € |
| PTW070g | Placa hidrófuga (zonas húmedas) | **37,743 m²** | 7,40 € | 279,30 € |
| PTW070i | Oscuro pladur | **12,9 m** | 38,60 € | 497,94 € |
| PTW070e | Tabica pladur | **6,6 m** | 38,60 € | 254,76 € |

### Verificación tabiquería nueva

- **45,974 m² de tabique nuevo**: 18,10 ml × 2,54 m altura. Coherente con una redistribución que crea 2-3 habitaciones nuevas.
- **61,298 m² de trasdosado**: perímetro total de fachada y particiones a revestir. El cálculo (27,30 × 2,54 = 69,34 m² − 13,7 m² de ventanas = 55,64 m²) + 4,60 + 0,88 = 61,30 m². **Correcto.**
- **93,4 m² de falso techo**: práctica totalidad de la vivienda (97,2 m² del estado inicial − ~4 m² de zonas sin falso techo). **Coherente.**
- **37,743 m² de placa hidrófuga**: 16,41 ml × 2,30 m en baños. Coherente con las dos estaciones húmedas.
- **12,9 m de oscuros**: Perímetro estimado de huecos de ventanas y puertas a revestir. Parece **insuficiente** para 6 ventanas + 1 ventanal + 7 puertas (estimación ~25-30 ml). **Posible infra-medición.**

---

## 5. Comparativa Cyss v2.0 vs Toni 472 — Albañilería

| Partida | Cyss v2.0 | Cant. | Importe | Toni 472 | Cant. | Importe | Δ % |
|---|---|---|---|---|---|---|---|
| Demolición cocina | DSM010c | 1 Ud | 800 € | 1.1 | 1 Ud | 650 € | Cyss +23% |
| Demolición baño | DSM010b | 2 Ud | 1.200 € | 1.2 | 1 Ud | 1.000 € | No comparable (Cyss incluye 2 baños) |
| Demolición ladrillo | DPT020c | 92,16 m² | 1.659 € | 1.3 | 1 Ud | 2.350 € | **Cyss -29%** (Toni a precio global) |
| Demolición falso techo | DPT020 | 10,6 m² | 127 € | 1.4 | 1 Ud | 180 € | **Cyss -29%** |
| Ampliación hueco | DPT020d | 0,73 m² | 73 € | 1,5 | 1 Ud | 200 € | **Cyss -64%** |
| Levantado pavimento | DRS011c | 2,6 m² | 47 € | 1.6 | 1 Ud | 220 € | **Cyss -79%** |
| Levantado rodapié | DRS011 | 63 m | 126 € | 1.7 | 1 Ud | 180 € | **Cyss -30%** |
| Levantado ventanas | DFC010c | 6 Ud | 120 € | 1.8 | 1 Ud | 150 € | No comparable |
| Desmontaje puertas | DPP020 | 7 Ud | 70 € | 1.10 | 1 Ud | 250 € | No comparable |
| Falcado ventanas c/mod | FCL060c | 2 Ud | 610 € | 2.2 | 1 Ud | 650 € | Similar |
| Falcado ventanas s/mod | FCL060k | 5 Ud | 1.125 € | 2.3+2.4 | 2 Ud | 1.250 € | Cyss -10% |
| Pavimento porcelánico | RAG012 | 88,3 m² | 4.592 € | 2.9+2.10 | — | 2.030 € | **No comparable** (Toni no incluye material) |
| Alicatado | RAG012b | 38,83 m² | 2.019 € | 2.11 | — | 120 € | **No comparable** (Toni solo mano de obra) |
| Picado pilar | DPP100b | 1 Ud | 220 € | 2.19 | 1 Ud | 2.400 € | **Discrepancia GRAVE** — Cyss 220 € vs Toni 2.400 € |
| Casoneto | FCL060o | 1 Ud | 90 € | 2.8 | 1 Ud | 3.780 € | **Discrepancia GRAVE** — Cyss 90 € vs Toni 3.780 € |

### ⚠️ Discrepancias > 5% detectadas

1. **Picado de pilar (Toni 2.400 € / Cyss 220 €)**: Toni probablemente incluye el picado completo de un pilar de hormigón visto, más el rascado, limpieza y esmalte incoloro. Cyss lo presupuesta en 220 € y Toni en 2.400 € — **diferencia del +991%**. Posible error de interpretación: quizá el pilar es de gran tamaño o Toni incluye refuerzo estructural. **Urge aclarar.**

2. **Casoneto (Toni 3.780 € / Cyss 90 €)**: El casoneto es un cajón de obra para persiana o cortina. Toni lo valora en 3.780 € (quizá incluye varios metros lineales de casoneto con mecanismo motorizado). Cyss lo considera una unidad simple a 90 €. La diferencia del 4.100% sugiere que **no es el mismo elemento** o que Toni incluye persiana motorizada + cajón completo. **Urge aclarar.**

3. **Demolición de tabiquería**: Cyss la mide por m² (92,16 m² × 18 € = 1.659 €). Toni la da como partida alzada (2.350 €). A precio unitario, Toni es un 42% más caro.

4. **Levantado de pavimento**: Cyss solo cuenta 2,6 m² del balcón (47 €). Toni lo da como partida alzada de 220 €. Cyss parece **no contemplar** el picado del pavimento interior, solo la nivelación con mortero. Si se pica todo, el importe de Cyss sería insuficiente.

### Conclusión sobre la comparativa

La comparación directa Cyss vs Toni es **limitada** porque:
- Cyss incluye **material + mano de obra**
- Toni 472 **no especifica** si incluye materiales o solo mano de obra (los precios de pavimento sugieren solo mano de obra: 2.030 € vs 4.592 € de Cyss con material)
- 5 partidas de Toni están sin precio (marcadas con `?`)

**Recomendación**: Solicitar a Toni un presupuesto **con materiales incluidos** o pedir a Cyss el desglose de coste de material vs mano de obra para poder comparar homogéneamente.

---

## 6. Otras mediciones verificables

### Fontanería — Cyss cap. 05

| Partida | Ud | Cant. | Precio | Total |
|---|---|---|---|---|
| Acometida agua | Ud | 1 | 340 € | 340 € |
| Fontanería cocina | Ud | **4** | 255 € | 1.020 € |
| Fontanería baño 1 | Ud | 5 | 255 € | 1.275 € |
| Fontanería baño 2 | Ud | 5 | 255 € | 1.275 € |
| Desagüe ACC | Ud | 2 | 45 € | 90 € |

⚠️ **Las cantidades de fontanería (4/5/5 puntos) parecen altas para una cocina y dos baños**. Probablemente incluyen puntos de agua caliente + fría como unidades separadas. Habría que confirmar con Cyss.

### Climatización — Cyss cap. 06

| Partida | Ud | Cant. | Precio | Total |
|---|---|---|---|---|
| Red de conductos | Ud | 1 | 2.836 € | 2.836 € |
| Máquina Mitsubishi MGPEZ-71 (7,1 kW) | Ud | 1 | 2.998 € | 2.998 € |
| Preinstalación línea frigorífica | m | 8 | 45 € | 360 € |

✅ Potencia de 7,1 kW para 90 m² ≈ 79 W/m² — correcto para Valencia (zona climática B3). Línea frigorífica de 8 m — coherente con distancia entre unidad interior y exterior.

### Electricidad — Cyss cap. 04

| Partida | Ud Cyss | Ud Paracon | Diferencia |
|---|---|---|---|
| Cuadro eléctrico | 1 | 1 | ✅ |
| Enchufes 16A | 46 | 35 | Cyss +11 ud |
| Enchufes 25A (cocina) | 1 | 5 (horno, vitro, nevera, lavavajillas, micro) | ❌ Cyss cuenta 1 vs 5 de Paracon |
| Interruptores/conmutadores | 37 | 31 | Cyss +6 ud |
| Puntos de luz techo/pared | 27 | No especifica | No comparable |
| Puntos TV | 2 | 2 | ✅ |
| Puntos datos | 6 | 5 | Cyss +1 ud |
| Telefonillo | 1 | 1 (Fermax) | ✅ |

⚠️ **Discrepancia en enchufes 25A**: Cyss presupuesta 1 Ud de 25A (para cocina), pero Paracon detalla 5 electrodomésticos que normalmente requieren línea dedicada (horno, vitro, nevera, lavavajillas, micro). Es posible que Cyss agrupe varios en un mismo punto 25A o que Paracon los detalle individualmente. **Hay que verificar el esquema unifilar.**

---

## 7. Resumen de discrepancias > 5%

| Partida/Concepto | Cyss | Subcontrata | Diferencia | Gravedad |
|---|---|---|---|---|
| Picado de pilar | 220 € | 2.400 € (Toni) | **+991%** | 🔴 Alta |
| Casoneto | 90 € | 3.780 € (Toni) | **+4.100%** | 🔴 Alta |
| Levantado pavimento interior | 0 € (no incluido) | 220 € (Toni) | No incluido en Cyss | 🟡 Media |
| Alicatado baños vs planos | 38,83 m² | 38,83 m² (ok) | 0% | ✅ |
| Pavimento vs plano | 94,9 m² | ~90 m² estimado | ~+5% | 🟡 Leve |
| Oscuros pladur | 12,9 m | ~25-30 m estimado | **−50%** | 🟡 Media |
| Enchufes 25A | 1 Ud | 5 Ud (Paracon) | −80% | 🟡 Media |
| Superficie pintura paredes | 204 m² | ~196 m² estimado | +4% | 🟢 Leve |
