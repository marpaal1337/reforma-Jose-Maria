# Distribución por estancias y validación de mediciones

_Generado el 2026-07-09._

## Superficies por estancia (plano estado inicial PEA.01)

| Estancia | Área (m²) | % del total | Coste estimado (proporcional) |
|---|---:|---:|---:|
| Salón-comedor | 16.4 | 16.9% | 9.562,94 € |
| Dormitorio 1 | 8.1 | 8.3% | 4.723,16 € |
| Dormitorio 2 | 13.7 | 14.1% | 7.988,56 € |
| Dormitorio principal | 24.8 | 25.5% | 14.461,04 € |
| Aseo / Lavabo | 2.6 | 2.7% | 1.516,08 € |
| Baño 1 | 4.5 | 4.6% | 2.623,98 € |
| Baño 2 / Distribuidor | 4.6 | 4.7% | 2.682,29 € |
| Cocina | 9.7 | 10.0% | 5.656,13 € |
| Dormitorio 3 / Despacho | 12.8 | 13.2% | 7.463,76 € |
| **TOTAL** | **97.2** | 100% | **56.677,94 €** |

*Nota: el coste proporcional es orientativo. Algunas partidas (alicatados, 
fontanería, cocina) se concentran en estancias específicas.*

## Reparto ajustado por tipo de partida

Asignamos cada capítulo de Cyss a las estancias donde realmente se aplica:

| Concepto | Criterio de reparto |
|---|---|
| **Pavimento** (cap.02, ~35%) | Proporcional a superficie de cada estancia |
| **Alicatado** (cap.02, ~25%) | Solo baños (1, 2) y cocina (altura 100-240 cm) |
| **Fachada** (cap.02, ~15%) | Exterior — no aplica a estancias interiores |
| **Falso techo pladur** (cap.03) | Proporcional a superficie (todas las estancias) |
| **Demolición** (cap.01) | Proporcional a superficie (~50%) + cocina/baños (~50%) |
| **Electricidad** (cap.04) | Proporcional a superficie + cocina |
| **Fontanería** (cap.05) | Solo cocina y baños |
| **Climatización** (cap.06) | Proporcional a superficie habitable |

### Estimación por estancia

| Estancia | Pavimento | Pladur | Alicatado | Elect. | Font. | Clima | Total est. |
|---|---:|---:|---:|---:|---:|---:|---:|
| Salón-comedor (16.4 m²) | 819,67 € | 1.762,91 € | — | 1.202,87 € | — | 1.112,57 € | **4.898,01 €** |
| Dormitorio 1 (8.1 m²) | 404,83 € | 870,70 € | — | 594,10 € | — | 549,50 € | **2.419,14 €** |
| Dormitorio 2 (13.7 m²) | 684,72 € | 1.472,67 € | — | 1.004,84 € | — | 929,40 € | **4.091,63 €** |
| Dormitorio principal (24.8 m²) | 1.239,49 € | 2.665,86 € | — | 1.818,97 € | — | 1.682,42 € | **7.406,75 €** |
| Aseo / Lavabo (2.6 m²) | 129,95 € | 279,49 € | 421,59 € | 190,70 € | — | 0,00 € | **1.021,72 €** |
| Baño 1 (4.5 m²) | 224,91 € | 483,72 € | 729,68 € | 330,06 € | 1.466,67 € | 0,00 € | **3.235,03 €** |
| Baño 2 / Distribuidor (4.6 m²) | 229,91 € | 494,47 € | 745,89 € | 337,39 € | 1.466,67 € | 0,00 € | **3.274,33 €** |
| Cocina (9.7 m²) | 484,80 € | 1.042,70 € | 1.572,86 € | 711,45 € | 1.466,67 € | 658,04 € | **5.936,52 €** |
| Dormitorio 3 / Despacho (12.8 m²) | 639,74 € | 1.375,93 € | — | 938,82 € | — | 868,35 € | **3.822,84 €** |

*Estimación basada en reparto proporcional. Los importes reales dependen de 
las mediciones exactas de cada partida en el presupuesto de Cyss.*

## Validación de mediciones Cyss vs planos

Comparamos las cantidades del presupuesto Cyss con las dimensiones de los planos:

| Concepto | Plano (est.) | Cyss v2.0 | Diferencia | Veredicto |
|---|---:|---:|---:|---|
| Pavimento porcelánico | 97.2 m² (sup. total) | 88,3 m² | 8.9 m² | ✅ Coherente (paredes ~9%) |
| Falso techo pladur | 97.2 m² (sup. total) | 93,4 m² | 3.8 m² | ✅ Coherente (prácticamente toda la vivienda) |
| Demolición particiones | ~30-50 m² (est.) | 36,0 m² | — | ✅ Razonable para reforma integral |
| Climatización | 97.2 m² (sup. total) | 90,0 m² | 7.2 m² | ✅ Coherente (resto pasillo/baños) |
| Alicatado baños | ~50-60 m² (est.) | 63 m² (est.) | — | ⚠ Sin dato exacto en Cyss (sin cantidades) |
| Ventanas (Nacher) | 8 ud (V01-V08) | 8 ud (falcados) | 0 | ✅ Coincide |

### Conclusión de la validación

Las cantidades de Cyss v2.0 son **consistentes** con las dimensiones de los planos 
para los conceptos principales (pavimento, pladur, clima, ventanas). 
No se detectan discrepancias significativas que indiquen sobremedición o errores graves.

**Limitación**: el PDF del presupuesto detallado de Cyss no incluye las cantidades 
numéricas en el texto extraíble (están embebidas en el PDF gráfico). 
La validación se ha hecho con los totales del resumen y las superficies de los planos.

## Resumen visual (orientativo)

```
  ┌──────────────────────────────────────────────────┐
  │          PLANO ESTADO INICIAL (PEA.01)           │
  │            Superficie total: 97.2 m²             │
  ├──────────────────────┬───────────────────────────┤
  │ DORM. PRINCIPAL      │ DORM. 3 / DESPACHO        │
  │              24,8 m² │                   12,8 m² │
  ├──────────────────────┼───────────────────────────┤
  │ BAÑO 1               │ DORM. 2                   │
  │               4,5 m² │                   13,7 m² │
  ├──────────────────────┼───────────────────────────┤
  │ DORM. 1              │ BAÑO 2                    │
  │               8,1 m² │                    4,6 m² │
  ├──────────────────────┼───────────────────────────┤
  │ ASE O                │ COCINA                    │
  │               2,6 m² │                    9,7 m² │
  ├──────────────────────┴───────────────────────────┤
  │                  SALÓN-COMEDOR                   │
  │                                          16,4 m² │
  └──────────────────────────────────────────────────┘
```

## Cuadro de ventanas (plano carpintería exterior PEI.05/06)

Del plano de carpintería exterior se identifican **8 ventanas** (V01–V08):

| Ventana | Tipo | Apertura | Color | Notas |
|---|---|---|---|---|
| V01 | 3 hojas correderas | — | Bicolor Cobre ext / Blanco int | Nudo central minimalista |
| V02 | 2 hojas + 2 fijos | 1 oscilo | Bicolor Cobre ext / Blanco int | Persiana tirador derecha |
| V03 | 2 hojas correderas | — | Blanco | — |
| V04 | 2 hojas correderas | — | Blanco | — |
| V05 | 1 hoja | Oscilo batiente | Blanco | Apertura exterior |
| V06 | 2 hojas | 1 oscilo | Blanco | Persiana tirador derecha · Quitamiedos 110 cm |
| V07 | 2 hojas | 1 oscilo | Blanco | Persiana tirador derecha · Quitamiedos 110 cm |
| V08 | 2 hojas | 1 oscilo | Blanco | Persiana tirador derecha · Quitamiedos 110 cm |

**Importe Nacher**: 10.151,48 € IVA incl. (8.389,65 € base) para las 8 unidades.

## Plano de albañilería (PEI.01) — leyenda

| Concepto | Especificación |
|---|---|
| Picado pilares hormigón | — |
| Pavimento porcelánico | 60×120 cm (88,3 m² en Cyss) |
| Fachada de ladrillo | — |
| Alicatado baño 1 | h máx = 230 cm |
| Alicatado baño 2 | h máx = 100–120 cm |
| Alicatado salón | h máx = 240 cm (detalle junto a ventanas) |

## Plano de pladur (PEI.01) — leyenda

| Concepto | Especificación |
|---|---|
| Tabique pladur | 10 cm con lana de roca |
| Trasdosado pladur | 7 cm con lana de roca |
| Placa hidrófuga | Para baños |
| Oscuro pladur | Para zonas de paso |
| Tabica pladur | Para registro |
