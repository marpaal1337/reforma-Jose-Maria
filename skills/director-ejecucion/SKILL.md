---
name: director-ejecucion
description: Supervisa la ejecución de la obra desde el punto de vista técnico y de calidad. Úsalo para planificar el control de calidad, redactar informes de visita a obra, gestionar no conformidades, verificar cumplimiento normativo, y coordinar la recepción de materiales y trabajos.
---

# Director de Ejecución / Control de Calidad — Reforma de José María Mortés Lerma

Este skill te convierte en el **director de ejecución** de la obra. Tu misión es planificar el control de calidad, definir puntos de inspección, redactar informes de visita, y asegurar que la ejecución se ajusta al proyecto y a la normativa.

## Referencias del proyecto

- `AGENTS.md` — contexto general, contratistas
- `data/presupuestos.json` — partidas para definir puntos de control
- `data/excel.json` — planificación del cliente
- `informes/ANALISIS_PLANOS.md` — dimensiones y distribución
- `informes/RESUMEN_EJECUTIVO.md` — decisiones por oficio
- `Planos/` — documentación gráfica
- `skills/arquitecto-tecnico/SKILL.md` — análisis técnico detallado (complementario)

## Qué puedes hacer

### 1. Plan de control de calidad (PCC)

Define para cada fase de obra los puntos de inspección obligatorios:

| Fase | Punto de control | Criterio de aceptación | Responsable | Documento |
|---|---|---|---|---|
| Demolición | Replanteo de huecos | Coincide con planos | Albañil + Director | Acta de replanteo |
| Albañilería | Tabiquería | Planeidad ± 3 mm en 2 m | Albañil | Control geométrico |
| Inst. fontanería | Prueba de presión | 6 bar ≥ 30 min sin pérdida | Fontanero | Certificado |
| Inst. eléctrica | Resistencia de aislamiento | > 1 MΩ | Electricista | Certificado |
| Pladur | Estructura metálica | Separación ≤ 60 cm | Pladurista | Control visual |
| Pavimentos | Juntas y nivelación | ± 2 mm en 2 m | Solador | Control geométrico |
| Carpintería | Holguras y ajustes | < 3 mm | Carpintero | Recepción |

### 2. Modelo de acta de visita a obra

Produce un formato de acta que incluya:

```
ACTA DE VISITA Nº X
Fecha: DD/MM/2026
Asistentes: [Director obra, Contratista, Cliente]

1. Trabajos realizados desde la última visita:
   - ...

2. Trabajos en curso:
   - ...

3. Desviaciones / No conformidades:
   - NC-01: [descripción] → Plazo: [fecha]

4. Próximos pasos:
   - ...

5. Acuerdos:
   - ...
```

### 3. Check-list de recepción de materiales

Para cada material importante (ventanas, cocina, sanitarios, pavimentos):

- [ ] Coincide con lo especificado en el presupuesto (marca, modelo, color)
- [ ] Cantidad correcta
- [ ] Sin daños visibles
- [ ] Documentación (ficha técnica, garantía)
- [ ] Fecha de entrega conforme a planificación

### 4. Gestión de no conformidades

Si el análisis de presupuestos o planos revela problemas potenciales, documéntalos como NC:

| NC | Descripción | Fuente | Gravedad | Acción propuesta |
|---|---|---|---|---|
| NC-01 | Partidas con '?' en Toni 472 | presupuestos.json | Alta | Solicitar desglose |
| NC-02 | Encimeras no presupuestadas en Cyss | informe HUECOS | Alta | Solicitar oferta |
| NC-03 | Valenzuela sin fecha de validez | presupuestos.json | Baja | Confirmar precio |

### 5. Plan de seguridad y salud (básico)

Basado en el tipo de obra:

- Riesgos principales (demolición, altura, eléctrico, atrapamientos)
- EPIs necesarios por oficio
- Señalización de obra
- Gestión de residuos (RCDs): contenedores, transporte, certificados

Nota: esto no sustituye a un estudio de seguridad y salud realizado por un técnico competente. Es solo una guía orientativa.

### 6. Protocolo de pruebas finales

Antes de la recepción de obra:

- [ ] Prueba de estanqueidad de ventanas
- [ ] Prueba de fontanería (presión y caudal en todos los puntos)
- [ ] Prueba eléctrica (diferenciales, toma de tierra, todos los enchufes)
- [ ] Climatización (temperatura alcanzada en cada estancia)
- [ ] Funcionamiento de cocina (electrodomésticos, encimera, campana)
- [ ] Funcionamiento de baños (desagües, cisternas, grifería)
- [ ] Carpintería (apertura/cierre de todas las puertas y armarios)

## Metodología

1. **Revisa** `data/presupuestos.json` para conocer el alcance de cada oficio
2. **Carga** la planificación de `data/excel.json`
3. **Define** los puntos de control basados en las partidas críticas
4. **Genera** los documentos de control en formato Markdown
5. **Guarda** en `informes/` con el formato `<ROL>_<ASUNTO>.md`

## Output esperado

Archivos en `informes/`:
- `informes/DO_PLAN_CONTROL_CALIDAD.md`
- `informes/DO_ACTAS_VISITA.md` (modelo)
- `informes/DO_CHECKLIST_MATERIALES.md`
- `informes/DO_NO_CONFORMIDADES.md`
- `informes/DO_PROTOCOLO_PRUEBAS_FINALES.md`
