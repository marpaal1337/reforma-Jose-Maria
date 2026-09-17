# Renders, plano de aires y documentación de obra

_Generado el 2026-09-18 a partir de las imágenes aportadas en `data/reales/`._

## 1. Qué contiene `data/reales/`

| Archivo | Tipo | Contenido |
|---|---|---|
| `salon-render.jpeg` (800×450) | Render | Salón: ventanal corredera a terraza, sofá beige, butaca mariposa, mueble de TV en roble |
| `salon2-render.jpeg` (800×450) | Render | Salón: **pilar visto** (microcemento/hormigón) + frente de TV en piedra y listones de roble, iluminación lineal |
| `salon-cocina_render.jpeg` (800×450) | Render | Salón-comedor con la cocina al fondo, puerta vidriera de madera, aparador |
| `cocina-render.jpeg` (800×450) | Render | Cocina: península de **piedra negra**, frentes de roble, electrodomésticos integrados, espejo arco |
| `dormitorio-principal-render.jpeg` (800×450) | Render | Dormitorio: armario de roble, cabecero de listones, mesita de piedra, lámparas colgantes |
| `baño-principal-render.jpeg` (800×450) | Render | Baño: **bañera**, revestimiento pétreo, mueble de roble con encimera de piedra, grifería cobre |
| `plano-aires.jpeg` (921×2048) | Plano marcado a mano | Plano de **conductos de clima** con estancias etiquetadas y trazado verde/azul/rojo |
| `grua al 7º piso.jpeg` (899×1599) | Foto de obra | Plataforma articulada (Torres) desplegada hasta el 7º piso en fachada |

Los renders se muestran en el visor `render3d.html` (botón **Galería** y ficha de cada estancia). El plano de aires se ha recortado a `data/imagenes/plano_aires_recorte.jpg` para la galería.

## 2. Hallazgo principal: el plano marcado no coincide con el PE.A.02

El plano de aires lleva rótulos de estancias con superficie y altura que **no coinciden con el plano de distribución PE.A.02** sobre el que se generó el modelo 3D:

| Estancia rotulada en el plano de aires | Sup. rotulada | h | Equivalente medido en PE.A.02 (`data/planos3d.json`) |
|---|---:|---:|---|
| Baño 1 | 4,3 m² | 2,30 m | Baño 1 = 4,46 m² ✅ |
| Baño 2 | 4,3 m² | 2,30 m | Baño 2 = 4,82 m² ≈ |
| Estudio | 6,3 m² | 2,46 m | Dormitorio 3 = 6,85 m² (mismo recinto, **nombre distinto**) |
| Cocina | 12,9 m² | 2,30 m | **No existe como estancia**: en PE.A.02 va integrada en el salón (32,3 m²) |
| Lavadero | 2,2 m² | 2,46 m | No se detectó como recinto independiente |
| Recibidor | 2,7 m² | 2,30 m | Recibidor = 6,3 m² (recinto mayor) |
| Vestidor | 6,2 m² | 2,30 m | **No existe** en PE.A.02 |

**Interpretación**: es una **versión distinta de la distribución** (probablemente anterior o una variante con cocina cerrada y vestidor) o el plano de trabajo del instalador de clima. No se puede decidir cuál es la vigente desde el repositorio.

**Acciones**:
1. Confirmar con el arquitecto (SOFIA PALACIOS) cuál es la versión vigente. Si es la del plano marcado, hay que regenerar el modelo 3D y las mediciones: basta aportar el PDF vectorial de esa versión y re-ejecutar `scripts/generar_geometria3d.py`.
2. Hasta confirmarlo, tratar las superficies del visor 3D como **PE.A.02, Junio/25**.

## 3. Trazado de clima (lectura del plano de aires)

- **Verde**: red de conductos perimetral (fachada superior y laterales).
- **Azul**: derivaciones con flechas de impulsión hacia baños, pasillo y dormitorios (cobertura de todas las estancias).
- **Rojo**: recorrido principal desde la unidad (círculo rojo junto al hueco técnico entre baños) hacia cocina, vestidor y salón.

Coherencia con lo presupuestado:

| Concepto | Presupuesto | Fuente |
|---|---|---|
| Máquina por conductos Mitsubishi MGPEZ-71 VJA PRO | Sí (~90 m²) | Cyss v2.0 `ICX010h` |
| Red de conductos Climaver + rejillas de impulsión y retorno | Sí | Cyss v2.0 `ICX010i` |
| Instalación de clima por conductos + rejillas por plenum | 6.177,10 € | David Barat 1-000084 |

Los conductos discurren por el **falso techo (h = 2,30 m)**, coherente con los 93,4 m² de pladur de Cyss. **Verificar**: posición final de la máquina y registro de acceso (el plano la sitúa sobre el hueco técnico entre baños), y que la campana de cocina sale a fachada/conducto (`PTW070`), no en recirculación.

## 4. Renders vs memoria de calidades y presupuesto

Los renders son **ambientación orientativa** (probablemente generados con IA); no deben considerarse vinculantes sin confirmación del cliente.

Materiales que muestran y su estado en el proyecto:

| Acabado del render | Estado |
|---|---|
| Pavimento porcelánico imitación madera | ✅ En memoria (`RAG012`) |
| Alicatado porcelánico 60×120 en baños/cocina | ✅ En memoria (`RAG012b`) |
| Pavimento imitación mármol en recibidor | ✅ En memoria (`RAG012c`) |
| Península/encimera de **piedra negra** | ⚠ **Sin presupuestar** (DEKTON/SILESTONE pendiente, hallazgo ya conocido) |
| Frente de TV y baños en **piedra/travertino** | ❌ No está en la memoria de calidades |
| Carpintería de **roble a medida** (mueble TV, cabecero de listones, frentes) | ❌ Solo hay armarios/cocina de Valenzuela |
| **Grifería acabado cobre/latón** | ❌ Fontanería presupuestada sin acabado especificado |
| **Iluminación arquitectónica** (lineal LED + apliques) | ❌ Solo hay puntos eléctricos básicos en Paracon |
| Puerta vidriera interior de madera | ❌ No presupuestada (la de Valenzuela es de otro tipo) |

**Acción**: si el cliente quiere reproducir los renders, hay que pedir ampliación de precio a Valenzuela (roble a medida), Cyss/Toni (revestimientos pétreos), fontanería (grifería cobre) y electricidad (iluminación lineal). Si no, los renders deben entenderse como referencia visual.

## 5. Foto de obra (plataforma en fachada)

`grua al 7º piso.jpeg` muestra una plataforma articulada trabajando a la altura del 7º piso: montaje de carpintería exterior (Nacher V01–V08) y/o suministro de materiales. Implicaciones:
- Permiso de ocupación de vía pública (calle José María Mortés Lerma) y señalización.
- Coordinación con el plan de ventanas (Nacher: 8 ud, fabricación ~8 semanas) y con las fases de `PM_PLAN_DE_EJECUCION.md`.
- Documentar en el acta de visita (`DO_ACTAS_VISITA.md`) fecha, medio auxiliar y trabajos realizados.

## 6. Resumen de acciones

1. **Confirmar versión vigente de la distribución** (PE.A.02 vs plano de aires). Bloquea mediciones y reparto de costes.
2. Cerrar el presupuesto de **encimeras** (DEKTON/SILESTONE), ya identificado como crítico.
3. Presupuestar los acabados de los renders si son vinculantes: roble a medida, piedra, grifería cobre, iluminación.
4. Validar con David Barat el recorrido del plano de aires (rejillas por estancia, posición de máquina y registro).
5. Documentar la plataforma de fachada y su ventana temporal en la planificación.
