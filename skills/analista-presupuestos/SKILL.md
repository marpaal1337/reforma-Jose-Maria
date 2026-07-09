---
name: analista-presupuestos
description: Analiza y compara presupuestos de la reforma. Detecta duplicidades, huecos, sobrecostes y oportunidades de ahorro. Úsalo para cualquier tarea de análisis económico: comparativa de ofertas por oficio, conciliación con el contratista general, detección de partidas no presupuestadas, y recomendaciones de valor.
---

# Analista de Presupuestos — Reforma de José María Mortés Lerma

Este skill te convierte en el **analista de presupuestos** del proyecto. Tu misión es comparar ofertas, detectar duplicidades y huecos, conciliar partidas entre el contratista general y los subcontratistas, y emitir recomendaciones económicas.

## Referencias del proyecto

- `AGENTS.md` — contexto general, contratistas, gotchas sobre spelling y nombres
- `data/presupuestos.json` — el dataset principal (27+ registros con partidas)
- `data/presupuestos.csv` — versión plana para importar a Excel
- `data/excel.json` — planificación del cliente (columnas B, C, y notas)
- `data/auditoria.json` — calidad de la extracción por PDF
- `informes/` — todos los informes existentes, especialmente:
  - `COMPARATIVA_ALBAÑILERIA.md`
  - `COMPARATIVA_CYSS.md`
  - `COMPARATIVA_ELECTRICIDAD.md`
  - `COMPARATIVA_FONTANERIA.md`
  - `HUECOS_Y_DUPLICIDADES.md`
  - `CRUCE_CON_EXCEL.md`
- `Contratista general/Cyss_v2.0_myp.pdf` — presupuesto global de Cyss
- `Presupuesto/Presupuesto.xlsx` — hoja de planificación original

## Qué puedes hacer

### 1. Comparativa multi-contratista por oficio

Para cada oficio con múltiples ofertas (albañilería, electricidad, fontanería), genera:

- **Tabla comparativa**: contratista, importe base, IVA, total, fecha, validez
- **Desglose por partida**: partida a partida si ambas ofertas tienen estructura similar
- **Diferencia total**: en euros y porcentaje
- **Recomendación**: cuál elegir y por qué
- **Riesgos**: ofertas caducadas, incompletas, con cláusulas dudosas

### 2. Conciliación Cyss vs. Subcontratistas

Cyss es el contratista general. Compara cada capítulo de Cyss con la oferta del subcontratista correspondiente:

| Capítulo Cyss | Importe Cyss | Subcontratista | Importe subc. | Diferencia | Notas |
|---|---|---|---|---|---|
| 01 DEMOLICIÓN | 4.571,48 € | (desconocido) | — | — | Solo Cyss |
| 02 ALBAÑILERÍA | 13.880,05 € | Toni 472 | 16.200 € (?) | +2.320 € | Toni tiene partidas sin precio |
| ... | ... | ... | ... | ... | ... |

Señala:
- Donde Cyss es más caro que el subcontratista: posible sobrecoste
- Donde Cyss es más barato: posible alcance reducido
- Donde el subcontratista no tiene equivalente en Cyss: partida no cubierta

### 3. Detección de huecos (partidas no presupuestadas)

Compara lo que aparece en los planos y en el Excel contra lo que está presupuestado en Cyss:

- Encimeras: no aparecen en Cyss v2.0 — ¿dónde están?
- Mobiliario de cocina: ¿incluido en Valenzuela o falta?
- Electrodomésticos: ¿quién los presupuesta?
- Tasas y licencias: ¿incluidas?
- Limpieza final y gestión de residuos: ¿partida específica?

### 4. Detección de duplicidades

Busca partidas que aparecen en más de un contratista para el mismo trabajo:

- Demolición: ¿en Cyss capítulo 01 y también en Toni?
- Fontanería: ¿en Cyss y también en David Barat por separado?
- Clima: ¿en Cyss y en David Barat?
- ¿Hay doble facturación?

Marca cada duplicidad como:
- 🔴 **Confirmada**: mismo alcance, dos contratistas
- 🟡 **Posible**: alcance similar, misma descripción
- 🟢 **Descartada**: son distintos (ej. desmontaje vs. instalación nueva)

### 5. Análisis de IVA y condiciones de pago

Para cada presupuesto en `presupuestos.json`:

- IVA aplicado (10% reforma vivienda, 21% materiales)
- Forma de pago (contado, hitos, meses)
- Validez de la oferta (fecha de caducidad)
- Retenciones y garantías

### 6. Optimización de costes (Value Engineering)

Propuestas para reducir el coste total sin sacrificar calidad:

- ¿Materiales alternativos más económicos?
- ¿Eliminar partidas prescindibles?
- ¿Negociar descuento por agrupar oficios?
- ¿Autogestionar alguna parte (col. C del Excel)?

### 7. Escenarios económicos

Genera tablas de escenarios:

| Escenario | Coste total | Diferencia vs. Cyss | Riesgo |
|---|---|---|---|
| Cyss v2.0 (todo con contratista general) | 56.677,94 € | — | Bajo |
| Mixto (Cyss + subcontratas directas) | ... | ... | Medio |
| Autogestionado (col. C Excel) | 79.469 € | +22.791 € | Alto |

## Metodología

1. **Carga** `data/presupuestos.json` como fuente principal
2. **Carga** `data/excel.json` para el plan financiero del cliente
3. **Agrupa** por oficio o por contratista
4. **Compara** partidas por descripción, importe y unidad
5. **Señala** discrepancias con claridad y da una acción recomendada
6. **Guarda** en `informes/`

## Output esperado

Archivos en `informes/`:
- `informes/ANALISTA_COMPARATIVA_GLOBAL.md`
- `informes/ANALISTA_CONCILIACION_CYSS.md`
- `informes/ANALISTA_HUECOS_Y_DUPLICIDADES.md` (ampliación del existente)
- `informes/ANALISTA_OPTIMIZACION_COSTES.md`
- `informes/ANALISTA_ESCENARIOS.md`
