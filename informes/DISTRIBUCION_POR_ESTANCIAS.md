# Distribución por estancias y superficies medidas

_Actualizado el 2026-09-26 tras eliminar los presupuestos del repositorio. Solo superficies y datos de plano; sin estimaciones económicas._

## Superficies por estancia (plano estado inicial PEA.01)

| Estancia | Área (m²) | % del total |
|---|---:|---:|
| Salón-comedor | 16.4 | 16.9% |
| Dormitorio 1 | 8.1 | 8.3% |
| Dormitorio 2 | 13.7 | 14.1% |
| Dormitorio principal | 24.8 | 25.5% |
| Aseo / Lavabo | 2.6 | 2.7% |
| Baño 1 | 4.5 | 4.6% |
| Baño 2 / Distribuidor | 4.6 | 4.7% |
| Cocina | 9.7 | 10.0% |
| Dormitorio 3 / Despacho | 12.8 | 13.2% |
| **TOTAL** | **97.2** | 100% |

*Superficies del plano PEA.01. El modelo 3D (PE.A.02) mide 102,9 m² útiles + 7,5 m² terraza; ver `data/planos3d.json`.*

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

_Medidas en `data/ventanas.json` (V01–V08 medidas del PEI.05/06)._

## Plano de albañilería (PEI.01) — leyenda

| Concepto | Especificación |
|---|---|
| Picado pilares hormigón | — |
| Pavimento porcelánico | 60×120 cm |
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
