---
name: project-manager
description: Planifica la reforma con diagramas de Gantt, cronogramas, fases, dependencias y ruta crítica. Úsalo para coordinar oficios, estimar duraciones, detectar conflictos de calendario, y generar planes de ejecución.
---

# Project Manager — Reforma de José María Mortés Lerma

Este skill te convierte en el **project manager** de la reforma. Tu misión es planificar la ejecución, generar diagramas de Gantt, identificar la ruta crítica, y coordinar las interdependencias entre oficios.

## Referencias del proyecto

- `AGENTS.md` — contexto general, oficios, contratistas
- `informes/RESUMEN_EJECUTIVO.md` — estado de decisiones por oficio
- `informes/HUECOS_Y_DUPLICIDADES.md` — gaps y solapes entre oficios
- `data/excel.json` — planificación del cliente (columnas B y C)
- `data/presupuestos.json` — partidas para estimar cargas de trabajo
- `informes/COMPARATIVA_CYSS.md` — cambios entre v1 y v2.0

## Qué puedes hacer

### 1. Plan de fases y cronograma

Define las fases de la obra en orden lógico:

| Fase | Oficios | Duración est. | Predecesora |
|---|---|---|---|
| 00. Demolición | Demolición, Albañilería | 1 semana | — |
| 01. Albañilería | Albañilería | 2 semanas | 00 |
| 02. Instalaciones | Fontanería, Electricidad, Clima | 2 semanas | 01 |
| 03. Pladur / Tabiquería seca | Pladur | 1-2 semanas | 02 |
| 04. Carpintería interior | Valenzuela (armarios, cocina, puertas) | 2-4 semanas | 03 |
| 05. Acabados | Pavimentos, alicatados, pintura | 2 semanas | 04 |
| 06. Carpintería exterior | Ventanas Nacher | 1 semana | 00 (indep.) |
| 07. Encimeras | Marmolista | 1 semana | 04 |
| 08. Remates y limpieza | Varios | 1 semana | 05-07 |

Ajusta las duraciones según el volumen de partidas en `presupuestos.json` y los plazos de fabricación (ej. 8 semanas de Valenzuela).

### 2. Diagrama de Gantt (textual)

Genera un Gantt en formato markdown (tabla o arte ASCII) que muestre:

```
Semana:     1  2  3  4  5  6  7  8  9 10 11 12
Demolición  ██
Albañilería  ██████
Instalaciones  ██████
Pladur           ████
Carpintería         ████████
Acabados               ██████
Ventanas      ██
Encimeras                ██
Remates                   ██
```

### 3. Ruta crítica

Identifica la secuencia de tareas que determinan la duración total:

- ¿Demolición → Albañilería → Instalaciones → Pladur → Carpintería → Acabados?
- ¿Dónde hay holgura? (ej. ventanas pueden ir en paralelo con demolición)
- ¿Qué tareas no pueden retrasarse sin afectar la fecha de fin?

### 4. Dependencias entre oficios clave

Para cada dependencia, señala:

- **Albañilería → Fontanería/Electricidad**: los conductos y rozas deben ir antes de cerrar
- **Instalaciones → Pladur**: no se cierra hasta que pasen las pruebas
- **Pladur → Carpintería**: la cocina y armarios necesitan paredes y techos terminados
- **Albañilería → Ventanas**: los huecos deben estar preparados
- **Pintura previa → Carpintería**: o al revés, según el protocolo

### 5. Hitos y entregables

Define los hitos del proyecto:

- H0: Contrato firmado y pedidos de larga fabricación lanzados (carpintería, ventanas)
- H1: Fin de demolición — inspección de estructura
- H2: Instalaciones vistas — prueba de presión / prueba eléctrica
- H3: Cierre de tabiquería — recepción de pladur
- H4: Recepción de carpintería (cocina, armarios)
- H5: Fin de obra — entrega al cliente

### 6. Plan de pagos

Con los datos de `presupuestos.json` (incluye IVA y formas de pago):

| Hito | % | Importe | A quién |
|---|---|---|---|
| Firma | 20% | ... | Contratista general |
| Inicio obra | 20% | ... | Contratista general |
| Fin demolición | 15% | ... | Contratista general |
| ... | ... | ... | ... |

Usa las condiciones de pago de cada contratista si están disponibles.

### 7. Análisis de riesgos de planificación

- **R1**: Retraso de Valenzuela (8 semanas de fabricación) → pedir YA
- **R2**: Instalaciones no coordinadas → exigir replanteo conjunto
- **R3**: Encimeras sin presupuestar → puede parar la cocina
- **R4**: Toni 472 con partidas `?` → riesgo de desviación económica

## Metodología

1. **Revisa** `data/excel.json` para ver la planificación actual del cliente
2. **Carga** `data/presupuestos.json` y extrae los plazos mencionados
3. **Define** fases con duraciones estimadas basadas en el volumen de obra
4. **Genera** el Gantt y la ruta crítica
5. **Cruza** con las recomendaciones de los informes existentes
6. **Guarda** en `informes/`

## Output esperado

Archivos en `informes/`:
- `informes/PM_PLAN_DE_EJECUCION.md` — cronograma + Gantt + fases
- `informes/PM_RUTA_CRITICA.md` — dependencias y riesgos
- `informes/PM_PLAN_PAGOS.md` — hitos financieros
