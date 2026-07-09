# Análisis de Partidas Alzadas — Aparejador

_Generado el 2026-07-09._

Se analizan todas las partidas del tipo **"Partida alzada"**, **"Lote"**, **"Ud" sin desglose**, **"pa"** (partida alzada) o cualquier importe global sin justificación de medición.

---

## 1. Cyss v2.0 — Partidas alzadas detectadas

### 1.1 Capítulo 01 — Demolición

| Código | Descripción | Ud | Importe | ¿Justificada? |
|---|---|---|---|---|
| DSM010c | Demolición cocina completa | Ud | 800,00 € | ✅ Justificada — precio global de mercado para demolición completa de cocina (alicatados, mobiliario, instalaciones) |
| DSM010b | Demolición baño completo | Ud (×2) | 600,00 €/ud | ✅ Justificada — 2 baños, 600 €/ud es precio estándar |

**Valoración**: Ambas partidas alzadas tienen precio de mercado estándar y alcance descrito en la medición. No son "comodín".

---

### 1.2 Capítulo 02 — Albañilería

| Código | Descripción | Ud | Cant. | P.Unitario | Importe | ¿Justificada? |
|---|---|---|---|---|---|---|
| FCL060c | Falcado ventana c/mod | Ud | 2 | 305 € | 610 € | ✅ Justificada — ud con descripción |
| FCL060k | Falcado ventana s/mod | Ud | 5 | 225 € | 1.125 € | ✅ |
| FCL060p | Falcado ventanal s/mod | Ud | 1 | 275 € | 275 € | ✅ |
| FCL060b | Falcado ventanal c/mod | Ud | 1 | 315 € | 315 € | ✅ |
| FCL060q | Premarco madera | Ud | 5 | 55 € | 275 € | ✅ |
| FCL060o | Casoneto pladur | Ud | 1 | 90 € | 90 € | ✅ |

**Falcados de ventanas**: Seis falcados individualizados con precios diferenciados según tipo (con/sin modificación, ventana/ventanal). **Correctamente desglosados.** No son partidas alzadas opacas.

---

### 1.3 Capítulo 04 — Instalación Eléctrica — Partidas "pa"

| Código | Descripción | Ud | Importe | ¿Justificada? |
|---|---|---|---|---|
| RAG012k | Ayudas albañilería a instalación eléctrica | pa | **900,00 €** | ⚠️ **Partida alzada sin desglose** |

**Análisis**: 
- No se especifica qué incluye: ¿regatas? ¿tapado de regatas? ¿material?
- En Toni 472 las "regatas necesarias" están marcadas con `?` (sin precio)
- En v1 de Cyss esta misma partida también era de 900 €

**Recomendación**: 
- **Mantener** si Cyss acredita que es el coste real de las ayudas (regatas, reposición, material de agarre)
- Alternativa: pedir desglose en horas de oficial + ayudante + material

---

### 1.4 Capítulo 05 — Fontanería — Partidas "pa"

| Código | Descripción | Ud | Importe | ¿Justificada? |
|---|---|---|---|---|
| RAG012h | Ayudas albañilería a fontanería | pa | **400,00 €** | ⚠️ **Partida alzada sin desglose** |

**Análisis**:
- Similar a la eléctrica: incluye regatas, pasatubos, recibidos
- Precio inferior a la de electricidad (400 vs 900 €) porque el volumen de ayudas es menor

**Recomendación**: 
- **Mantener** si Cyss justifica el importe
- No es un comodín — es práctica habitual

---

### 1.5 Capítulo 06 — Climatización — Partidas "pa"

| Código | Descripción | Ud | Importe | ¿Justificada? |
|---|---|---|---|---|
| RAG012m | Ayudas albañilería a climatización | pa | **400,00 €** | ⚠️ **Partida alzada sin desglose** |

**Análisis**: Misma naturaleza que las anteriores. 400 € para ayudas de climatización (conductos, líneas frigoríficas, soportes de equipo exterior).

**Recomendación**: 
- **Mantener.** Un precio inferior sería sospechoso.

---

### 1.6 Capítulo 14 — Varios — Partidas "pa" y alzadas

| Código | Descripción | Ud | Cant. | Importe | ¿Justificada? |
|---|---|---|---|---|---|
| RAG012l | Limpieza durante la obra | pa | 1 | **200,00 €** | 🟡 Aceptable — limpieza periódica global |
| RAG012g | Trabajos verticales | pa | 1 | **600,00 €** | ⚠️ **Sin desglose** |
| RAG012i | Contenedor de escombros | Ud | 8 | 1.800,00 € | ✅ 8 contenedores × 225 € — precio unitario conocido |
| 14.1 | Plataforma elevadora | ud | 1 | **350,00 €** | ✅ Partida añadida en v2.0, precio de mercado |

#### 1.6.1 Trabajos verticales (RAG012g) — 600 €

**Descripción en Cyss**: "Trabajos verticales por fachada interior para colocación de saneamiento y enfoscado."

**Análisis**: 
- Partida alzada sin desglose de horas ni materiales
- Se refiere a trabajos en fachada interior (patio de luces) que requieren plataforma o andamio
- **Justificación**: En v2.0 se añadió la plataforma elevadora (350 €) como partida separada. Los 600 € de "trabajos verticales" posiblemente se solapan.

⚠️ **Posible duplicidad**: "Trabajos verticales" (600 €) + "Plataforma elevadora" (350 €) = 950 € por trabajos en altura. Habría que preguntar a Cyss si los 600 € incluyen el alquiler de la plataforma o si la partida 14.1 es adicional.

**Recomendación**: 
- **Aclarar con Cyss** el alcance de ambas partidas
- Si se solapan, eliminar una
- Si son complementarias (verticales = albañilería en altura, plataforma = alquiler del equipo), mantener

---

### 1.7 Capítulo 13 — Iluminación

| Código | Descripción | Ud | Cant. | Importe | ¿Justificada? |
|---|---|---|---|---|---|
| ILU009 | Instalación de luminarias y electrodomésticos no integrados | h | 1 | **600,00 €** | ⚠️ **Partida alzada disfrazada de "hora"** |

**Análisis**: 
- La unidad es "h" (hora) pero la cantidad es 1, resultando 600 €/hora — **imposible** como tarifa horaria real.
- Es una partida alzada que encaja en Cyss como mano de obra para montaje de todas las luminarias y electrodomésticos no integrados (campana, placa vitro, horno).

**Recomendación**: 
- **Mantener**, pero renombrar a "pa" para evitar confusiones
- El importe (600 €) es aceptable para montaje de toda la iluminación LED (12,8 + 4,2 + 1,7 m de tiras + downlights de Poveda/Paracon si aplican)

---

## 2. Toni 472 — Partidas alzadas

Toni estructura su presupuesto en **partidas globales por tarea**, sin desglose de mediciones (m², ml, ud). Esto es común en presupuestos de albañilería tradicional.

### 2.1 Partidas sin precio (marcadas con `?`)

| Nº | Descripción | Importe | ¿Comodín? |
|---|---|---|---|
| 1.13 | DESMONTAJE DE SPLIT | `?` | 🟡 Sin precio — a confirmar |
| 1.14 | DESMONTAJE DE SPLIT CON RECUPERACION | `?` | 🟡 Sin precio — a confirmar |
| 2.6 | FALCADO DE PREMARCOS | `?` | 🟡 Sin precio — a confirmar |
| 2.7 | COLOCACION DE VIERTEAGUAS | `?` | 🟡 Sin precio — a confirmar |
| 2.20 | PINTURA PLASTICA | `?` | 🟡 Sin precio — a confirmar |

**Análisis**: 
- El propio contratista no cerró estas partidas. Son elementos cuyo precio depende de una decisión o medición pendiente.
- **No son comodines** — son partidas abiertas que deben cerrarse antes de firmar.

### 2.2 Partidas alzadas con importe — ¿justificadas o comodín?

| Nº | Descripción | Importe | ¿Justificada? |
|---|---|---|---|
| 1.1 | DEMOLICIÓN COCINA | 650 € | ✅ Precio global de mercado |
| 1.2 | DEMOLICIÓN BAÑO COMPLETO | 1.000 € | ✅ Precio global de mercado |
| 1.3 | DEMOLICIÓN LADRILLO HUECO | 2.350 € | ⚠️ **Sin desglose** — comparable a 92,16 m² × 25,5 €/m² de Cyss |
| 2.1 | COLOCACION LADRILLO | 280 € | 🟡 Muy genérica |
| 2.2-2.5 | FALCADOS DE VENTANAS (4 partidas) | 650+1.000+250+350 € | ✅ Desglosadas por tipo |
| 2.8 | COLOCACION DE CASONETO | **3.780 €** | 🔴 **Comodín — precio desorbitado sin justificación** |
| 2.19 | PICADO DE PILAR | **2.400 €** | 🔴 **Comodín — precio desorbitado** |
| 2.18 | TUBO FLEXIBLE PARA CAMPANA | 350 € | ⚠️ Elevado para un tubo flexible de 150 mm |
| 14.1 | LIMPIEZA OBRA (Toni 468) | 600 € | ✅ |
| 14.3 | 8 CONTENEDORES (Toni 468) | 1.840 € | ✅ 8 × 230 € — comparable a Cyss 8 × 225 € |

#### 🔴 CASONETO (3.780 €) — Análisis detallado

| Concepto | Toni 472 | Cyss v2.0 | Diferencia |
|---|---|---|---|
| Casoneto | 1 Ud × 3.780 € | 1 Ud × 90 € | **×42 veces más** |

- En Cyss aparece como "Colocación de casoneto en tabique de pladur" — 90 €, que es un precio razonable para un cajón de obra pequeño para persiana.
- En Toni (3.780 €) podría incluir:
  - Casoneto completo de obra de albañilería (no pladur)
  - Mecanismo de persiana motorizada
  - Aislamiento interior
  - Varios metros lineales (no 1 ud)
  
**⚠️ Grave riesgo de interpretación errónea.** Cyss probablemente cuenta una unidad simple de falcado de un hueco pequeño, mientras que Toni cuenta el cajón completo de persiana para un ventanal grande (quizá 6-8 m lineales). Precio por metro lineal: ~470-630 €/ml — admisible para persiana motorizada con cajón de obra.

**Recomendación**: 
- **Preguntar a Toni** qué incluye exactamente (medidas lineales, tipo de persiana, aislamiento, motorización)
- **Preguntar a Cyss** qué alcance incluye su partida de 90 €
- Si el casoneto es el del salón (ventanal grande), la partida de Cyss es insuficiente

#### 🔴 PICADO DE PILAR (2.400 €) — Análisis detallado

| Concepto | Toni 472 | Cyss v2.0 | Diferencia |
|---|---|---|---|
| Picado de pilar | 1 Ud × 2.400 € | 1 Ud × 220 € | **×11 veces más** |

- Cyss: "Picado de pilar, rascado, limpieza y posterior protección con esmalte incoloro para dejarlo visto" — 220 €
- Toni: "PICADO DE PILAR" — 2.400 €

**Posibles explicaciones:**
1. ✅ Toni incluye el picado completo de un pilar de hormigón armado visto de gran tamaño (ej. 40×40 cm, altura 2,50 m = 4 m² de picado). Un picado manual de hormigón a base de martillo neumático puede costar ~100-150 €/m², resultando 400-600 €. Pero 2.400 € es excesivo.
2. ⚠️ En Toni 468 (proyecto SOFIA), la misma partida "PICADO PILAR" es de 350 € — **coherente con Cyss**.
3. ❌ Posible error: quizá el importe de 2.400 € corresponde a otra partida (¿pintura?) y está mal asignado.

**Recomendación**: 
- **Solicitar a Toni** justificación del precio — parece un error
- Comparar con su presupuesto 468 donde vale 350 €
- **No aceptar el precio sin justificación**

---

## 3. Valenzuela — Partidas alzadas

### 3.1 Armarios — 10 partidas

| Partida | Descripción | Importe |
|---|---|---|
| 1 | 6 cajones, barra para perchas y altillos | 2.115,57 € |
| 2 | 2 baldas, 2 zapateros, barra y altillos | 1.654,51 € |
| 3 | estantería, luz led | 1.020,21 € |
| 4 | 2 estantes, 2 cajones, 4 baldas, barra y altillos | 1.929,91 € |
| 5 | 3 cajones, 4 baldas, 2 zapateros, barra y altillos | 2.097,27 € |
| 6 | ESTANTERÍA DORMITORIO 3: 2,26 ML MELAMINA | 450,50 € |
| 7 | MUEBLE BAÑO 1, 1 cajón oculto, 1 cajón y luz led | 629,13 € |
| 8 | MUEBLE BAÑO 2, 1 cajón oculto, 1 cajón y luz led | 811,15 € |
| 9 | MUEBLE ZAPATERO 1,79 ML MELAMINA | 741,06 € |
| 10 | MUEBLE TV 3 ML MELAMINA | 1.242,00 € |

**Análisis**:
- Las partidas describen la configuración pero no el tipo de material, herrajes ni acabados.
- No son "comodín" — describen funcionalidad, pero **no permiten comparar precios unitarios** (precio por ml de armario).

**Evaluación:**
- El armario tipo (2,26 ml × 2.097 € para el más completo): ~928 €/ml
- El zapatero (1,79 ml × 741 €): ~414 €/ml
- El mueble TV (3 ml × 1.242 €): ~414 €/ml
- Los precios por ml son **razonables** para armarios de melamina con interior revestido.

**Recomendación**: 
- **Mantener** — las partidas están suficientemente desglosadas por estancia
- Solicitar a Valenzuela el **presupuesto desglosado por ml** para verificar homogeneidad de precios

### 3.2 Cocina — 2 partidas principales

| Partida | Descripción | Importe |
|---|---|---|
| 1 | Precio cocina sin herrajes | 4.737,30 € |
| 2 | Precio cocina con herrajes | 5.472,20 € (incluye carro basura + luz LED) |

**Análisis**:
- Diferencia por herrajes: 734,90 € — **correcto** para herrajes de calidad media (amortiguación, cajones con guías metálicas).
- Mobiliario de cocina completo (bajos + altos) para cocina estándar (~8-10 módulos) a 4.737 € sin herrajes: **precio razonable** (~474-592 €/módulo).

**Recomendación**: 
- **Mantener** — es una partida alzada típica en presupuestos de cocina
- Solicitar plano de distribución de módulos para verificar que se ajusta a la cocina del plano

### 3.3 Puertas — 4 partidas

| Partida | Descripción | Importe |
|---|---|---|
| 1 | 5 puertas abatibles lacadas con condena (251,46 €/ud × 5) | 1.257,30 € |
| 2 | P03 puerta vidriera abatible madera maciza + cristal translúcido | 1.120,00 € |
| 3 | [Puerta vidriera] y cristal translúcido | 990,00 € |
| 4 | P04 Puerta corredera para casoneto con condena | 351,03 € |

**Análisis**:
- Partida 3 (990 €) parece un **duplicado** o parte de la partida 2 — la descripción es ambigua.
- **Posible error de extracción**: la partida 2 (1.120 € + 990 €) podría ser una sola puerta vidriera de 2.110 € o dos puertas distintas. Verificar con Valenzuela.

**Recomendación**: 
- **Solicitar a Valenzuela** confirmación de si son 2 puertas vidrieras (2.110 €) o 1 (1.120 €)
- Aclarar qué puerta lleva cristal translúcido y cuál es la ubicación

---

## 4. Paracon — Electricidad

### Partida alzada única

| Concepto | Importe |
|---|---|
| Instalación eléctrica completa según planos | **5.005 €** (base) |
| (No incluye iluminación) | |

**Análisis**: 
- Es un **presupuesto global** por estancias con número de mecanismos detallados.
- Incluye 46 enchufes, 37 interruptores/conmutadores, 1 punto TV, 6 tomas de datos, etc.
- NO es una partida alzada opaca — tiene desglose por estancia y recuento de mecanismos.

**Recomendación**: 
- **Mantener** — es un presupuesto cerrado por instalación completa según planos
- Confirmar que incluye red de telecomunicaciones y videoportero (detallados por Poveda)
- El 15% retenido hasta finalización de obra es correcto

---

## 5. David Barat — Fontanería y Clima

### 5.1 Presupuesto 1-000022 DEF (consolidado)

| Partida | Importe (sin IVA) |
|---|---|
| Fontanería: Instalación completa 11 puntos, tubería multicapa PEX-AL-PERT | 3.965 € |
| Clima: Equipo GREE UM CDT 36 + conductos + desmontaje 3 splits | 7.962 € |
| **Total DEF** | **11.927 €** |

**Análisis**: 
- Fontanería como partida alzada: 3.965 € por instalación completa de fontanería (11 puntos). Incluye tubería multicapa, llaves de corte, montaje de sanitarios y griferías, acometida.
  - **Precio razonable** (~360 €/punto)
  - No incluye ayudas de albañilería (400 € en Cyss)
  
- Clima como partida alzada: **7.962 €** con equipo **Gree** (gama media-baja).
  - Cyss: 6.594 € con Mitsubishi Electric (gama alta) — **Cyss es 1.368 € más barato con mejor equipo**.
  - ❗ Diferencia sorprendente. Caben dos posibilidades: (a) Cyss tiene mejor precio por ser contratista general; (b) David Barat incluye más conductos/rejillas.

**Recomendación**: 
- **Abrir las partidas de David Barat** — pedir desglose de materiales y horas
- **Comparar equipos**: Mitsubishi (Cyss) vs Gree (David Barat) no son equivalentes
- Si se opta por David Barat para clima, **exigir equipo Mitsubishi** o justificar el Gree

### 5.2 Presupuesto 1-000079 (fontanería standalone)

| Partida | Importe (IVA incl.) |
|---|---|
| Instalación de fontanería | 4.065,60 € |

Partida alzada sin desglose. Quedó superada por el 1-000022 DEF.

---

## 6. Resumen de partidas alzadas — Decisiones

| Contratista | Partida | Importe | Tipo | Decisión |
|---|---|---|---|---|
| Cyss | Ayudas albañilería electricidad | 900 € | ⚠️ Alzada genérica | **Mantener** — pedir desglose |
| Cyss | Ayudas albañilería fontanería | 400 € | ⚠️ Alzada genérica | **Mantener** |
| Cyss | Ayudas albañilería climatización | 400 € | ⚠️ Alzada genérica | **Mantener** |
| Cyss | Trabajos verticales | 600 € | ⚠️ Posible solape con 14.1 | **Aclarar con Cyss** |
| Cyss | Plataforma elevadora | 350 € | ✅ Justificada | **Mantener** |
| Cyss | Instalación luminarias | 600 € | ⚠️ Unidad incorrecta (h→pa) | **Mantener** — renombrar |
| Toni | Casoneto | 3.780 € | 🔴 **Comodín / desorbitado** | **No aceptar sin justificación** |
| Toni | Picado de pilar | 2.400 € | 🔴 **Comodín / desorbitado** | **No aceptar — pedir revisión** |
| Toni | Tubo campana | 350 € | ⚠️ Precio elevado | Preguntar alcance |
| Toni | 5 partidas `?` | — | 🟡 Abiertas | **Cerrar antes de firmar** |
| Valenzuela | Armarios (10 partidas) | 12.691 € | ✅ Justificadas por estancia | **Mantener** |
| Valenzuela | Cocina (sín/herrajes) | 4.737/5.472 € | ✅ Justificada | **Mantener** — confirmar módulos |
| Valenzuela | Puertas (4 partidas) | 4.272 € | ⚠️ Posible error (partida 3) | **Aclarar puertas vidrieras** |
| Paracon | Inst. eléctrica completa | 5.005 € | ✅ Justificada (desglose estancias) | **Mantener** |
| David Barat | Fontanería + clima DEF | 11.927 € | ⚠️ Alzada sin desglose | **Solicitar desglose** |

### 🔴 Partidas alzadas "comodín" que requieren acción inmediata

1. **Toni — Casoneto (3.780 €)**: El mayor riesgo del proyecto. Diferencia del 4.100% con Cyss. **Aclarar alcance urgente.**
2. **Toni — Picado de pilar (2.400 €)**: Incoherente con su propio presupuesto 468 (350 €). **Solicitar corrección.**
3. **Cyss — Trabajos verticales (600 €) + Plataforma (350 €)**: Posible duplicidad. **Aclarar alcance.**
4. **Valenzuela — Puerta vidriera (1.120 + 990 €)**: Posible duplicado. **Confirmar número de puertas.**
