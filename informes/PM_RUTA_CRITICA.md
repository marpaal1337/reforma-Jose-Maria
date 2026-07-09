# PM — Ruta Crítica del Proyecto

_Generado el 2026-07-09._

---

## 1. Ruta crítica (secuencia que determina la duración total)

La ruta crítica define el **camino más largo** del proyecto. Cualquier retraso en estas actividades retrasa la entrega final.

```
[H0] Firma contrato + Pedido Valenzuela
  │
  ├─ Sem 0-1: Pedido Valenzuela (8 sem. fabricación)
  │     └── (espera de 8 semanas, pasa en paralelo a la obra)
  │
  ├─ [H1] Sem 1-2: Demolición
  │
  ├─ [H2] Sem 2-5: Albañilería estructural
  │     ├── Faldados y premarcos (preparación ventanas)
  │     ├── Regatas para instalaciones
  │     └── Pavimentos y alicatados
  │
  ├─ Sem 3-5: Instalaciones rough-in (eléctrico, fontanería, clima)
  │     └── Deben terminar antes de pladur
  │
  ├─ Sem 4-5: Ventanas Nacher instaladas
  │     └── Deben estar antes de pladur
  │
  ├─ [H3] Sem 5-7: Pladur (cierra paredes y techos)
  │
  ├─ [H4] Sem 7-9: Pintura / Acabados albañilería
  │     └── Debe estar lista antes de montar puertas
  │
  ├─ [H5] ◆ Sem 9: Recepción Valenzuela (8 sem. desde pedido)
  │     └── *** PUNTO CRÍTICO: nada puede adelantar esta fecha ***
  │
  ├─ Sem 9-11: Montaje armarios, cocina, puertas
  │
  ├─ Sem 11-13: Encimeras (DEKTON + SILESTONE)
  │     └── Cocina debe estar montada para medir
  │
  ├─ Sem 12-14: Remates, iluminación, ajustes
  │
  └─ [H6] Sem 15-16: Limpieza final + Entrega
```

**Duración total de la ruta crítica: 16 semanas** (con un margen de 1-2 semanas sobre el cronograma base).

---

## 2. Holguras (slack) por actividad

| Actividad | Holgura estimada | Comentario |
|-----------|:--------------:|------------|
| Demolición | ~0 sem. | Sin holgura: es la primera actividad, cualquier retraso se arrastra |
| Albañilería | ~0 sem. | Sin holgura: de ella dependen instalaciones, ventanas y pladur |
| Ventanas Nacher | ~1 sem. | Pueden instalarse hasta justo antes de pladur |
| Electricidad rough-in | ~1 sem. | Puede terminar justo antes de cerrar con pladur |
| Fontanería rough-in | ~1 sem. | Igual que electricidad |
| Climatización rough-in | ~1 sem. | Igual que electricidad |
| Pladur | ~0 sem. | Debe empezar justo después de instalaciones rough-in |
| Pintura | ~1 sem. | Puede solaparse con instalaciones remate |
| **Montaje Valenzuela** | **~0 sem.** | **No tiene holgura: la obra está parada (fase acabados) esperando los muebles** |
| Encimeras | ~1 sem. | Pueden retrasarse sin afectar remates menores |
| Remates finales | ~2 sem. | Actividad final con algo de colchón |

**Observación**: la holgura real es mínima porque la ruta crítica está dominada por la espera de 8 semanas de Valenzuela. Se puede ganar tiempo empezando actividades en paralelo (instalaciones rough-in con albañilería, pintura con remate de instalaciones), pero la espera de Valenzuela es inamovible.

---

## 3. Actividades que NO pueden retrasarse

| Actividad | Motivo |
|-----------|--------|
| **Pedido Valenzuela** (P0) | Cada día de retraso en el pedido se suma a las 8 semanas y retrasa la entrega final |
| **Demolición** | Sin demolición no arranca nada |
| **Faldados en albañilería** | Sin faldados no se pueden instalar ventanas Nacher |
| **Instalación ventanas Nacher** | Sin ventanas no se puede cerrar con pladur |
| **Instalaciones rough-in** | Sin tuberías/cables en paredes no se puede cerrar con pladur |
| **Pladur** | Sin pladur no se puede pintar ni montar carpintería interior |
| **Recepción Valenzuela** | Fecha fija (8 sem. desde pedido); no se puede adelantar |
| **Montaje cocina** | Sin cocina montada no se pueden tomar medidas de encimeras |

---

## 4. Dependencias entre oficios

```
DEMOLICIÓN
    │
    ▼
ALBAÑILERÍA (estructura, faldados, pavimentos, alicatados)
    │
    ├────────────────────────────────────────────┐
    ▼                                            ▼
INSTALACIONES (rough-in)                  CARP. EXTERIOR (Nacher)
(eléctrico, fontanería, clima)            (ventanas, ventanal)
    │                                            │
    └────────────────────┬───────────────────────┘
                         ▼
                      PLADUR
                         │
                         ▼
                     PINTURA
                         │
                         ▼
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
INST. REMATE       CARP. INTERIOR        ILUMINACIÓN
(mecanismos,       (Valenzuela:          (perfiles LED,
grifería, ACC)     armarios, cocina,     tiras LED)
                   puertas)
                         │
                         ▼
                     ENCIMERAS
                    (DEKTON + SILESTONE)
                         │
                         ▼
                    LIMPIEZA FINAL
                         │
                         ▼
                     ENTREGA
```

### Dependencias críticas (sin margen)

| De | A | Ventana |
|:--:|:--:|:-------:|
| Albañilería (faldados) | Ventanas Nacher | Sem 4-5 |
| Ventanas Nacher | Pladur | Sem 5-7 |
| Instalaciones rough-in | Pladur | Sem 5-7 |
| Pladur | Pintura | Sem 7-9 |
| Pintura | Recepción Valenzuela | Sem 9 |
| Recepción Valenzuela | Montaje carpintería | Sem 9-11 |
| Montaje cocina | Encimeras | Sem 11-13 |

---

## 5. Hitos del proyecto (H0–H5)

| Código | Hito | Fecha | Dependencia |
|:------:|------|:-----:|:-----------:|
| **H0** | Firma contrato + pedido Valenzuela | 01/09/2026 | — |
| **H1** | Fin demolición | 18/09/2026 | H0 |
| **H2** | Albañilería completa | 09/10/2026 | H1 |
| **H3** | Instalaciones rough-in completas | 09/10/2026 | H2 |
| **H4** | Pladur + pintura terminados | 23/10/2026 | H3 |
| **H5** | Recepción carpintería Valenzuela | 30/10/2026 | H0 + 8 sem. |
| **H6** | Fin obra / entrega | 18/12/2026 | H5, P10, P11 |

---

## 6. Análisis de riesgos

### R1 — Valenzuela 8 semanas de fabricación

| Aspecto | Detalle |
|---------|---------|
| **Riesgo** | Cualquier retraso en la fabricación de Valenzuela (8 sem. desde pedido) desplaza toda la fase de acabados y la entrega |
| **Probabilidad** | Media (plazos largos en carpintería son habituales) |
| **Impacto** | Alto (cada semana de retraso = +1 semana en la entrega final) |
| **Mitigación** | Hacer pedido inmediato en H0; mantener contacto semanal con Valenzuela; establecer penalización por retraso en contrato; visitar taller a las 6 semanas para verificar avance |
| **Plan B** | Si Valenzuela se retrasa >2 semanas, adelantar el máximo de remates (limpieza, iluminación, pintura) para que la instalación sea lo único pendiente |

### R2 — Coordinación de instalaciones (3 oficios en paralelo)

| Aspecto | Detalle |
|---------|---------|
| **Riesgo** | Paracon (electricidad), David Barat (fontanería) y David Barat (clima) deben solaparse con albañilería y entre ellos. Conflictos de espacio en regatas y falsos techos |
| **Probabilidad** | Alta (es la coordinación más compleja de la obra) |
| **Impacto** | Medio (puede causar retrasos de 1-2 semanas si hay que rehacer trabajos) |
| **Mitigación** | Reunión de coordinación pre-obra con Cyss, Paracon y David Barat; definir claramente responsables de rozas/regatas; establecer orden de prioridad: fontanería → clima → electricidad |
| **Plan B** | Cyss incluye partidas de "ayudas a instalaciones" en sus capítulos 04, 05, 06 — usar esas ayudas para resolver conflictos in situ |

### R3 — Encimeras sin presupuesto ni contratista

| Aspecto | Detalle |
|---------|---------|
| **Riesgo** | No hay presupuesto de encimeras (DEKTON Marmorio + SILESTONE Charcoal Soapstone). Ningún contratista lo incluye. Puede no haber marmolista disponible en el momento necesario |
| **Probabilidad** | Alta (actualmente es un hueco confirmado) |
| **Impacto** | Alto (sin encimeras la cocina no está terminada; puede retrasar la entrega) |
| **Mitigación** | Solicitar 3 presupuestos a marmolistas locales en la semana 0; cerrar contrato en la semana 2; tener el material seleccionado y stock confirmado |
| **Coste estimado** | 2.000 – 4.000 € (según COMPARATIVA_CYSS.md) |

### R4 — Partidas con '?' en Toni 472

| Aspecto | Detalle |
|---------|---------|
| **Riesgo** | Toni 472 tiene 5 partidas sin importe (1.13, 1.14 splits; 2.6 faldado premarcos; 2.7 vierteaguas; 2.20 pintura). Si se opta por Toni en lugar de Cyss, estos costes adicionales pueden disparar el presupuesto |
| **Probabilidad** | Media-alta (para el escenario alternativo de contratar a Toni) |
| **Impacto** | Bajo si se elige a Cyss (que es más barato y no tiene partidas abiertas). Impacto medio si se opta por Toni: sobrecoste estimado 2.000-3.000 € adicionales |
| **Mitigación** | En escenario recomendado (Cyss como contratista general), este riesgo no aplica porque Cyss cubre albañilería con presupuesto cerrado de 13.880,05 € |

---

## 7. Resumen de riesgos

| ID | Riesgo | Prob. | Impacto | Nivel |
|:--:|--------|:-----:|:-------:|:-----:|
| **R1** | Retraso fabricación Valenzuela | Media | Alto | 🔴 Crítico |
| **R2** | Conflictos coordinación instalaciones | Alta | Medio | 🟠 Alto |
| **R3** | Encimeras sin contratista | Alta | Alto | 🔴 Crítico |
| **R4** | Partidas '?' Toni 472 (no aplica si se elige Cyss) | Media | Bajo-Medio | 🟡 Medio |

### Acciones inmediatas (semanas 0-1)

1. ✅ Hacer pedido a Valenzuela el mismo día de la firma (R1)
2. ⬜ Solicitar 3 presupuestos de encimeras (R3)
3. ⬜ Convocar reunión de coordinación Cyss + Paracon + David Barat (R2)
4. ⬜ Definir orden de prioridad en rozas: fontanería → conductos clima → eléctrico (R2)
5. ⬜ Establecer hitos de seguimiento semanal con Valenzuela (R1)
