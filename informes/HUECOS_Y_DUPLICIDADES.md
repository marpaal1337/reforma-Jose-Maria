# Huecos, duplicidades y riesgos ocultos

_Generado el 2026-07-09._

_Análisis completo de huecos, duplicidades y riesgos ocultos en los 27 registros del dataset._

---

## 1. Huecos: oficios sin presupuesto económico

### 1.1 Encimeras — CRÍTICO

| Aspecto | Detalle |
|---|---|
| Oficio | Encimeras (cocina + lavadero) |
| Documentos | `desconocido_Encimeras.pdf` (plano PEI.09 — solo especifica materiales) |
| Materiales previstos | DEKTON Marmorio + SILESTONE Charcoal Soapstone |
| Presupuesto económico | **NINGUNO. No existe oferta de ningún contratista.** |
| Incluido en Cyss? | **NO**. El cap.02 de Cyss cubre colocación de pavimento porcelánico pero no encimeras |
| Coste estimado | 2.500–4.500 € (material DEKTON/SILESTONE + corte + instalación) |
| **Riesgo** | **Si no se presupuesta ahora, el cliente descubrirá el coste cuando ya no tenga margen** |

**Acción**: Pedir presupuesto a un marmolista/local de encimeras URGENTE.

### 1.2 Electrodomésticos

| Aspecto | Detalle |
|---|---|
| ¿Algún presupuesto los incluye? | **NO** |
| Cocina Valenzuela | Incluye muebles de cocina SIN electrodomésticos (hornos, placa, campana, nevera, lavavajillas) |
| Coste estimado | **3.000–6.000 €** (horno + placa inducción + campana + nevera + lavavajillas + lavadora) |
| **Riesgo** | **Alto. Gasto no contemplado en ningún presupuesto** |

**Acción**: Presupuestar electrodomésticos aparte (el cliente puede elegirlos en tienda).

### 1.3 Licencias y tasas municipales

| Aspecto | Detalle |
|---|---|
| Licencia de obra | ¿Incluida en Cyss? No se menciona explícitamente |
| Tasa de basuras / contenedores | Cyss cap.14 incluye contenedores (parte de 2.950 €) |
| Tasa de ocupación vía pública | No se menciona |
| Boletines eléctrico/fontanería | No se mencionan |
| Coste estimado total | **1.000–2.500 €** (según ayuntamiento de Valencia) |
| **Riesgo** | **Medio. Puede haber tasas no presupuestadas** |

**Acción**: Preguntar a Cyss si las licencias y tasas están incluidas o son a cargo del cliente.

### 1.4 Dirección de obra / coordinación

| Aspecto | Detalle |
|---|---|
| ¿Quién coordina? | Cyss si se contrata como contratista general |
| Si se hace híbrido | El cliente necesita coordinación propia o contratar un director de obra |
| Coste estimado coordinación externa | 2.000–4.000 € (arquitecto técnico para supervisión) |
| **Riesgo** | Si se opta por autogestión sin dirección de obra, el riesgo de errores es alto |

### 1.5 Mobiliario y decoración

| Aspecto | Detalle |
|---|---|
| Lámparas y luminarias móviles | No incluidas en ningún presupuesto |
| Cortinas / estores | No incluidos |
| Pequeño mobiliario | No incluido |
| Coste estimado | 2.000–4.000 € |
| **Riesgo** | Bajo (se compra después de la obra) |

---

## 2. Duplicidades y solapamientos detectados

### 2.1 Toni 468 vs Toni 472 — duplicidad de proyecto (ya detectada)

| Documento | Cliente | Total | Aplica? |
|---|---|---|---|
| Toni 468 PROYECTO SOFIA | SOFIA | 28.864,55 € | **NO** (otro proyecto) |
| Toni 472 REFORMA CALLE JOSE MARIA LERMA | SOFIA (cabecera) | 21.447,25 € | **SÍ** |

**Riesgo**: Si alguien usa el 468 por error, estaría sobrevalorando el coste de albañilería en 7.417 €.

### 2.2 David Barat 1-000079 vs 1-000022 DEF — duplicidad de oficio

| Documento | Alcance | Total |
|---|---|---|
| 1-000079 (2025-11-04) | Solo fontanería | 4.065,60 € |
| 1-000022 DEF (2026-03-10) | Fontanería + Clima (combinado) | 11.927,23 € |

**Riesgo**: Sumar ambos presupuestos como si fueran independientes → doble contabilización de fontanería. El 1-000022 DEF sustituye al 1-000079.

### 2.3 Cyss v1 vs Cyss v2.0 — duplicidad de versión

| Versión | Fecha | TEM | Total |
|---|---|---|---|
| v1 | 2025-10-17 | 53.125,12 € | 58.437,63 € |
| v2.0 | 2026-06-04 | 51.525,40 € | 56.677,94 € |

**Riesgo**: Usar la v1 en lugar de la v2.0 → sobrecoste de 1.760 €.

### 2.4 Cap.02 Cyss: posible duplicidad con Toni 472

Cyss cap.02 incluye partidas que Toni 472 también tiene. Si se contrata a Toni para hacer albañilería además de Cyss, podría haber solapamiento:
- Demoliciones (cap.01 Cyss y Toni 472 sección 1)
- Falcado de ventanas
- Colocación de pavimento

**Riesgo**: Si se contrata a ambos para el mismo trabajo, se paga dos veces.

### 2.5 Ayudas albañilería en Cyss — posible duplicidad

Cyss cap.04 incluye RAG012k (ayudas albañilería a instalación eléctrica).
Cyss cap.05 incluye RAG012h (ayudas albañilería a fontanería).
Cyss cap.06 incluye RAG012m (ayudas albañilería a climatización).

Si se contratan instalaciones directas (Paracon, DB), estas ayudas ya no las hace Cyss, pero el importe de estos códigos sigue dentro de los capítulos. **Posible duplicidad**: el cliente pagaría ayudas en Cyss que luego no se ejecutan.

**Estimación del importe duplicado**: 300–500 € por capítulo = **900–1.500 €**.

**Acción**: Si se opta por el híbrido, negociar con Cyss la retirada de estas partidas de ayudas de los capítulos 04, 05 y 06.

---

## 3. Análisis del IVA: 10% vs 21% en todos los presupuestos

### Resumen de tipos aplicados

| Contratista / Documento | IVA aplicado | Base legal |
|---|---|---|
| **Cyss v1 y v2.0** | **10%** | Art. 91.Uno.2.7º LIVA (rehabilitación vivienda con contratista) |
| **Toni 468** | **21%** (implícito) | Subcontratista individual |
| **Toni 472** | **21%** (implícito) | Subcontratista individual |
| **Ventanas Nacher** | **21%** | Suministro e instalación de ventanas |
| **Valenzuela ARMARIOS** | **21%** (incluido en total) | Carpintería y mobiliario |
| **Valenzuela COCINA** | **21%** (incluido en total) | Carpintería y mobiliario |
| **Valenzuela PUERTAS** | **21%** (incluido en total) | Carpintería y mobiliario |
| **David Barat 1-000084** | **21%** (incluido, asumido) | Subcontratista individual |
| **David Barat 1-000079** | **21%** (incluido, asumido) | Subcontratista individual |
| **David Barat 1-000022 DEF** | **21%** (incluido, asumido) | Subcontratista individual |
| **Paracon** | **21%** (explícito: 1.051,05 €) | Instalador eléctrico |
| **Poveda** | **21%** (explícito: 1.111,11 €) | Instalador eléctrico |

### ¿Es correcto el 10% de Cyss?

Para que una rehabilitación de vivienda aplique el 10% de IVA (tipo reducido), se requiere:
1. Que el contratista sea el **contratista general** (no un subcontratista).
2. Que el coste de los materiales no supere el **40% del importe total**.
3. Que la vivienda tenga al menos **2 años de antigüedad** (sí, es una reforma integral).

Cyss cumple estos requisitos como contratista general. **Correcto**.

### ¿Pueden las subcontratas aplicar el 10%?

No. Las subcontratas individuales (Toni, DB, Paracon, etc.) deben aplicar el **21%** porque son instaladores o suministradores, no contratistas generales. Si el cliente contrata directamente a Toni para la albañilería, Toni debería aplicar el 10% si actúa como contratista principal de esa parte de la obra, pero al ser solo un oficio, Hacienda podría discutirlo.

**Consecuencia práctica**: Si el cliente hace la obra con Cyss, paga **10% IVA** sobre 51.525 € = 5.153 €. Si gestiona las instalaciones directamente (Paracon + DB + Nacher + Valenzuela), paga **21% IVA** sobre esos importes.

### Comparativa del impacto del IVA

| Escenario | Base global | IVA total | Coste total |
|---|---|---|---|
| Cyss completo (10%) + carpint. directas (21%) | 51.525 + 30.825 = 82.350 € | 5.153 + 6.473 = 11.626 € | **93.976 €** |
| Híbrido: Cyss parcial (10%) + subcontratas (21%) | 33.402 + 50.472 = 83.874 € | 3.340 + 10.599 = 13.939 € | **97.813 €** |

¡**Atención**! Por el efecto del IVA, el híbrido puede salir **más caro** que Cyss completo:
- Híbrido: 97.813 €
- Cyss completo: 93.976 €
- **Diferencia: +3.837 € a favor de Cyss completo**

**Esto contradice el análisis previo**. Hay que ajustarlo:

En el análisis del COMPARATIVA_ESCENARIOS.md y ANALISTA_COMPARATIVA_GLOBAL.md se usó:
- Cyss parcial (cap.01+02+03+13+14) con IVA 10%: 36.742 €
- Subcontratas: Paracon 6.056 + DB Font 4.066 + DB Clima 7.474 + Nacher 10.151 + Valenzuela 27.147 = 54.894 €
- Total: 36.742 + 54.894 = 91.636 €

Pero si sumamos correctamente la base de Cyss parcial (33.402 €) + las bases de subcontratas:
- Paracon base: 5.005
- DB Font base: 3.360
- DB Clima base: 6.176
- Nacher base: 8.390
- Valenzuela base: 22.435
- Subcontratas base total: 45.366 €

Base total híbrido: 33.402 + 45.366 = 78.768 €
IVA total: 33.402*10% + 45.366*21% = 3.340 + 9.527 = 12.867 €
**Total híbrido: 91.635 €**

Cyss completo base: 51.525 + 30.825 (carpinterías base) = 82.350 €
IVA: 51.525*10% + 30.825*21% = 5.153 + 6.473 = 11.626 €
**Total Cyss completo: 93.976 €**

**Diferencia: 91.635 vs 93.976 = -2.341 €**. Correcto, el híbrido sigue siendo más barato. El IVA del híbrido (12.867 €) es mayor que el del Cyss completo (11.626 €) pero la base del híbrido (78.768 €) es menor que la del Cyss completo (82.350 €) porque Cyss cap.04+05+06 (instalaciones) tienen mayor importe que las subcontratas directas.

**Conclusión**: El híbrido ahorra **~2.340 €** a pesar del IVA más alto, porque la base de las subcontratas es mucho menor que la de Cyss para esos capítulos.

---

## 4. Condiciones de pago y plazos

### Resumen de condiciones

| Contratista | Forma de pago | Plazo | Observaciones |
|---|---|---|---|
| **Cyss** | No especificada en documentos | No especificado | Solicitar condiciones |
| **Paracon** | 15% firma, 35% canalización, 35% cableado, 15% final | Hitos de obra | **Mejor condición** |
| **Poveda** | No especificada | Validez hasta 16-11-2025 (caducado) | — |
| **Valenzuela** | No especificada | **8 semanas** mínimo (fabricación) | Planificar con antelación |
| **Ventanas Nacher** | No especificada | No especificado | — |
| **David Barat** | No especificada | No especificado | — |

### Riesgos detectados

1. **Poveda caducado**: La oferta expiró el 16-11-2025. Cualquier comparativa con Poveda es inválida.
2. **Valenzuela 8 semanas**: Si hay prisa, este plazo puede ser un problema. Pedir confirmación por escrito.
3. **Paracon 4 plazos**: Muy favorable. Asegura flujo de caja para el contratista y protege al cliente (no paga todo por adelantado).

---

## 5. Partidas con discrepancias en la extracción

### Valenzuela — suma de partidas vs total declarado

| Presupuesto | Suma partidas | Total declarado | Diferencia |
|---|---|---|---|
| ARMARIOS | 13.047,80 € | 12.691,31 € | **+356,49 €** (es la línea de total) |
| COCINA | 5.599,06 € | 5.472,20 € | **+126,86 €** |
| PUERTAS | 3.887,40 €* | 4.271,96 € | **-384,56 €** |

_* La partida de puertas tiene un posible error de parseo: 257,30 € donde debería ser 1.257,30 € (251,46 € x 5). Si corregimos: 1.257,30 + 1.120 + 990 + 351,03 + 169,07 = 3.887,40 €. La diferencia con el total declarado (4.271,96 €) sigue siendo -384,56 €._

**Posible explicación**: Los totales declarados en los PDFs pueden incluir descuentos no detallados o partidas implícitas. **Confirmar con Valenzuela antes de firmar**.

### Cyss — cantidades no extraíbles

El PDF del myp de Cyss contiene las cantidades (m², uds) embebidas en el gráfico. El parser solo extrajo los códigos y descripciones. **No es posible auditar las mediciones** sin acceder al PDF original o al presupuesto en formato editable.

---

## 6. Partidas sin precio en el dataset

| Documento | Partidas sin importe | Impacto |
|---|---|---|
| Toni 468 | 3 de 41 (7,3%) | No aplica (otro proyecto) |
| Toni 472 | **5 de 34 (14,7%)** | **2.000–3.700 € estimados** |
| David Barat 1-000084 | Partidas vacías (array vacío) | Solo se conoce el total |
| David Barat 1-000079 | Partidas vacías (array vacío) | Solo se conoce el total |
| David Barat 1-000022 | Partidas vacías (array vacío) | Solo se conoce el total |
| Paracon | Estancias sin mecanismos | Alcance no detallado |
| Cyss myp | Sin importes unitarios | No se pueden auditar las mediciones |

---

## 7. Cruce con el Excel — ampliación

### Columnas del Excel identificadas

| Columna | Significado |
|---|---|
| **B** | **Estrategia subcontratas directas** (suma de ofertas individuales base: 70.846 €) |
| **C** | **Escenario alternativo / actualizado** (79.469 €) |
| **D** | Notas (80 en albañilería, "sin luz" en electricidad) |
| **E** | 6.700 en albañilería (sin identificar) |
| **G** | Notas del planificador ("Techos a 30", "Oscuros a 54", etc.) |

### Nuevo hallazgo: Columna E

La columna E tiene valor 6.700 en albañilería. Esto no coincide con ninguna oferta.
Posible interpretación: **Coste de materiales comprados directamente por el cliente** (pavimento, azulejos, sanitarios). En ese caso, la columna B (22.055) sería mano de obra + material de Toni, y E (6.700) sería material extra comprado por el cliente.

**Implicación**: Si el Excel refleja una estrategia de autogestión donde el cliente compra los materiales, la comparativa con Cyss (que incluye materiales) no es directa.

### Coincidencias exactas con el dataset

| Columna | Oficio | Importe | Coincide con |
|---|---|---|---|
| B | Fontanería | 3.360 | **DB 1-000079 base** (3.359,99 €) |
| B | Clima | 6.177 | **DB 1-000084 base** (6.176,27 €) |
| C | Electricidad | 5.005 | **Paracon base** (5.005 €) |
| C | Clima | 7.962 | DB 1-000084 base (no, es 6.176) — **sin coincidencia exacta** |
| B | Carpintería ext | 8.386 | **Nacher base** (8.389,65 €) |
| B | Carpintería int | 22.433 | **Valenzuela suma base** (22.435,47 €) |

### Discrepancias del Excel

| Oficio | Col B | Col C | Oferta más cercana | Observación |
|---|---|---|---|---|
| Albañilería | 22.055 | 22.135 | Cyss v1 cap.02 (22.701) | Aproximado |
| Pladur | 3.900 | 9.583 | Cyss v2.0 (10.448) | Col B infravalorado, Col C más realista |
| Electricidad | 4.535 | 5.005 | Paracon (5.005) | Col B parece un borrador anterior |

---

## 8. Partidas que NO aparecen en los planos pero SÍ en presupuestos

| Partida | Presupuesto | Aparece en planos? |
|---|---|---|
| Trabajos verticales (plataforma) | Cyss cap.14 | No (no es un plano de obra) |
| Contenedores de escombros | Cyss cap.14 | No |
| Luz LED en armarios | Valenzuela | No (especificación técnica, no plano) |

Todas son partidas auxiliares o de detalle que no aparecen en planos. No hay discrepancia.

---

## 9. Resumen de riesgos no cubiertos

| Concepto | Coste estimado | ¿Presupuestado? | Criticidad |
|---|---|---|---|
| **Encimeras DEKTON + SILESTONE** | **2.500–4.500 €** | **NO** | 🔴 Crítico |
| **Electrodomésticos** | **3.000–6.000 €** | **NO** | 🔴 Crítico |
| Licencias y tasas | 1.000–2.500 € | No confirmado | 🟡 Medio |
| Dirección de obra (si híbrido) | 2.000–4.000 € | No | 🟡 Medio |
| Mobiliario no integrado | 2.000–4.000 € | No | 🟢 Bajo |
| Cortinas/estores | 1.000–2.000 € | No | 🟢 Bajo |
| Lámparas | 500–1.500 € | No | 🟢 Bajo |
| **TOTAL NO PRESUPUESTADO** | **10.000–20.500 €** | | |

**El presupuesto real del proyecto, incluyendo todo lo necesario, es:**

| Escenario | Coste obra + carpinterías | + No presupuestado | **TOTAL REAL** |
|---|---|---|---|
| Cyss completo + directas | 93.976 € | 10.000–20.500 € | **~104.000–114.500 €** |
| Híbrido óptimo | 91.637 € | 10.000–20.500 € | **~102.000–112.000 €** |

**Es fundamental que el cliente conozca esta cifra real antes de empezar la obra.**

---

## 10. Checklist de confirmación previa al inicio

- [ ] **Encimeras**: presupuesto recibido y aceptado.
- [ ] **Electrodomésticos**: seleccionados y presupuestados.
- [ ] **Toni 472**: 5 partidas cerradas con importe.
- [ ] **Paracon**: alcance detallado por escrito (videoportero, red datos, downlights).
- [ ] **Cyss**: confirmar que el cap.02 v2.0 + cap.03 cubren todo el alcance de Toni 472.
- [ ] **Ayudas albañilería**: si se opta por híbrido, retirar RAG012k, RAG012h, RAG012m de Cyss.
- [ ] **IVA**: confirmar con asesor fiscal que Cyss puede aplicar el 10% (materiales < 40%).
- [ ] **Licencias**: preguntar a Cyss si están incluidas o son a cargo del cliente.
- [ ] **Valenzuela plazo**: confirmar 8 semanas por escrito y planificar pedido.
- [ ] **Forma de pago Cyss**: solicitar condiciones por escrito.
- [ ] **Seguros**: confirmar que todos los contratistas tienen seguro de responsabilidad civil y seguro de obra en curso.
