# Especificación de mobiliario y carpintería (fuente: PE/I.06-07, PE/A.03-04, PE/I.01, PE/I.09 + renders de la diseñadora)

Coordenadas del MODELO en metros: x = este, z = sur (+z hacia abajo en el plano). Alturas en metros desde el suelo.
`box(x0, z0, x1, z1, h0, h1, nombre, material)` = caja alineada a ejes (ver generar_blender.py).
Prefijos de nombre por estancia (los usa revisar_mobiliario.py): d3_ dorm-3, d2_ dorm-2, est_ estudio,
dp_ dorm-principal, ves_ vestidor, b1_ bano-1 (ducha), b2_ bano-2 (bañera), rec_ recibidor, lav_ lavadero,
coc_ cocina (y isla*, placa, taburete_*, campana), salón sin prefijo especial (tv_, sofa_, mesa_, silla_, …), tz_ balcón.

Materiales (nombres orientativos; la tarea de materiales define los finales):
- `roble_mel` = melamina imitación roble (frentes cocina, armarios, muebles lavabo, zapatero, M05, estanterías E01/E02, PA01)
- `grafito` = melamina gris grafito satinada (cuerpo isla), `gris_osc` interiores
- `silestone` = Silestone Charcoal Soapstone (encimera + laterales + frontal de la isla, a inglete)
- `dekton` = Dekton Marmorio (encimera y frontal/salpicadero cocina, encimera lavadero)
- `resina` = encimera de resina blanca mate de los lavabos
- `travertino_porc` = porcelánico aspecto travertino (alicatados baño, pavimento baño 60×120, pared TV salón)
- `laca` = lacado blanco (puertas, M02)
- `cerezo` = madera de cerezo barnizada (biblioteca reutilizada del Estudio)
- `metal_negro`, `cobre` (grifería de baños: cobre cepillado como en el render), `negro_mate` (grifo cocina, electrodomésticos), `cristal`, `vidrio_acido`, `espejo`, `led` (emisivo 3000 K; 4000 K en cocina)

---------------------------------------------------------------------------------------------------
## COCINA (techo 2,30) — PE/I.07 + PE/I.09 + render cocina
Frente lineal contra el muro oeste (x = -1.53 cara del muro), fondo 0.60 → frentes en x = -0.93. Módulos N→S:
| módulo | z0 | z1 | contenido |
|---|---|---|---|
| columna frigorífico combi panelado | -0.50 | 0.10 | 0.10 zócalo, cuerpo hasta 2.30, 2 puertas roble_mel, tirador metálico vertical |
| almacenaje (bajo) | 0.10 | 0.50 | |
| carro basuras (bajo) | 0.50 | 0.95 | |
| fregadero (bajo) | 0.95 | 1.75 | fregadero bajo encimera 0.55×0.40 en x∈[-1.38,-0.97], z∈[1.14,1.69]; grifo negro_mate |
| columna horno | 1.75 | 2.35 | 0.10 zócalo; lavavajillas panelado 0.10–0.88; horno negro (cristal) 0.90–1.50; micro negro 1.50–1.95; armario 1.95–2.30 |
- Bajos: zócalo 0.00–0.10 (retranqueado 5 cm, gris_osc), cuerpo 0.10–0.88, uñero integrado (ranura horizontal 2 cm bajo encimera).
- Encimera `dekton` 0.88–0.90 sobre z∈[0.10,1.75], x∈[-1.53,-0.91]; copetes laterales 5 cm.
- Salpicadero `dekton` en la pared x=-1.53 (0.02 de grueso), z∈[0.10,1.75], 0.90–1.50.
- Altos `roble_mel` 1.50–2.30, fondo 0.35 (x∈[-1.53,-1.18]), z∈[0.10,1.75], 4 puertas de 0.41; perfil LED bajo los altos (`led`, 4000 K) a 1.49.
- ISLA: x∈[0.01,0.81], z∈[-0.52,1.72], altura total 0.90. Cuerpo `grafito` x∈[0.01,0.56] (cajones hacia el OESTE: N→S almacenaje 0.6 [-0.50,0.10], cajonera 0.8 [0.10,0.90], cajonera 0.8 [0.90,1.70]); vuelo de 0.25 al ESTE para taburetes.
  Tablero `silestone` 0.02 (0.88–0.90) sobre toda la isla; laterales norte y sur `silestone` 0.02 de grueso, 0.00–0.90, a inglete (cascada); frontal ESTE (lado taburetes) `silestone` panel 2.20×0.88 retranqueado bajo el vuelo en x=0.54..0.56.
  Placa vitro negra 0.60×0.50 enrasada, centrada en x=0.29, z=0.50.
- Campana de techo enrasada 0.90×0.50 (gris claro/acero) en el falso techo sobre la placa (x∈[-0.16,0.74], z∈[0.25,0.75], 2.28–2.30).
- 3 taburetes negros (asiento Ø0.38 a 0.75, patas finas metal_negro, reposapiés) en (0.88,-0.07), (0.88,0.60), (0.88,1.27).

## SALÓN · COMEDOR (techo 2,46)
- PILAR picado de hormigón visto: x∈[3.44,3.77], z∈[-0.42,-0.10], 0–2.46, material `hormigon_picado`.
- PARED TV "alicatado salón h=2,40" (PE/I.01): revestimiento `travertino_porc` 0.06, x∈[3.77,7.88], z∈[-0.42,-0.36], 0.00–2.40 (juntas de 1.20×0.60 horizontales).
  Oscuro de pladur con tira LED 3000 K sobre ella: ranura en techo x∈[3.77,7.88], z∈[-0.42,-0.30], con `led` a 2.42–2.46.
- M05 mueble TV (NO suspendido, PE/I.07): x∈[4.32,7.32], z∈[-0.36,0.04], 0.00–0.30 (zócalo retranqueado 3 cm 0.00–0.03), 5 puertas roble_mel con uñero.
- TV 65" negra mural centrada x=5.82, 0.95–1.78 (1.45×0.83), separada 3 cm de la pared.
- APARADOR curvo (render): x∈[2.00,3.20], z∈[-0.42,-0.02], cuerpo 0.18–0.78 roble_mel con extremos redondeados (radio 0.20), 4 patas finas metal_negro. Sobre él, cuadro textil grande beige 1.00×1.20 centrado x=2.60, 1.05–2.25.
- MESA COMEDOR: tablero `cristal` 0.012 a 0.75, x∈[2.67,3.57], z∈[1.19,3.00]; pie de `travertino` (dos bloques 0.35×0.35×0.73 en z=1.55 y z=2.65 centrados en x=3.12, o una lama 0.20×1.20).
  6 SILLAS carcasa tapizada crema (bouclé → `tejido_claro`) con patas de roble: oeste x∈[2.37,2.67] en z∈[1.52,1.97] y [2.23,2.67]; este x∈[3.57,3.87] mismas z; norte x∈[2.89,3.34] z∈[0.89,1.19]; sur x∈[2.89,3.34] z∈[3.00,3.30]. Respaldo hacia fuera de la mesa.
  LÁMPARA colgante de tambor blanco Ø0.60×0.30 centrada (3.12, 2.10), parte baja a 1.65, cable negro al techo.
- SOFÁ (plano): x∈[4.75,7.05], z∈[2.62,3.41] (respaldo al sur contra z=3.41), 3 plazas, tapizado beige `tejido`, asiento a 0.42, brazos bajos 0.60, patas finas metal_negro (render "Outline").
- ALFOMBRA crema x∈[4.50,7.30], z∈[1.20,3.30], 0.004.
- MESA DE CENTRO: x∈[5.13,6.52], z∈[1.44,2.08]; dos bloques `travertino` 0.35 de alto + tablero `cristal` a 0.36–0.38.
- BUTACA BKF (mariposa, cuero coñac): centro (7.38,1.94), mirando al suroeste (hacia el sofá/mesa).
- LÁMPARA DE PIE (render): (7.60,3.25), fuste negro, pantalla blanca Ø0.40 a 1.50–1.75.
- PLANTA strelitzia en maceta blanca estriada (asset CC0 existente): (7.55,0.25).
- 3 CUADROS sobre el sofá en la pared sur (z=3.61): centros x = 5.10, 5.90, 6.70; 0.60×0.80, 1.20–2.00; marco roble.
- SIN cortinas (el render no las lleva): eliminar las actuales.

## RECIBIDOR (techo 2,30)
- M04 zapatero suspendido: x∈[0.33,0.69], z∈[2.54,4.31], 0.20–0.90, 4 puertas roble_mel con uñero; tira LED bajo el mueble (0.19–0.20).
- ESPEJO redondo Ø0.80 sobre el zapatero, en la pared x=0.32, centro z=3.42, h=1.55 (render).
- PA02 (separador fijo): ver puertas.json (se construye en build_puertas).

## LAVADERO (techo 2,46)
- Encimera `dekton` x∈[-1.16,0.08], z∈[3.70,4.30], 0.88–0.90, con copetes frontal y laterales de 5 cm.
- Lavadora + secadora bajo encimera (blancas 0.60×0.60×0.85): x∈[-1.10,-0.50] y [-0.50,0.08]... ajusta a dos huecos de 0.60.
- Calentador mural blanco 0.35×0.25×0.60 en la pared oeste a 1.60–2.20.
- Alicatado 1.20 en todas las paredes (PE/I.01, línea discontinua) con `travertino_porc`… (o azulejo blanco 30×60 si queda raro).

## VESTIDOR (techo 2,30)
- A01 armario: x∈[1.86,3.50], z∈[-3.24,-2.64], 0.00–2.30; 4 puertas roble_mel (juntas cada 0.41), tiradores metálicos verticales; frente hacia el SUR.
- A02 armario: x∈[3.50,4.11], z∈[-2.64,-1.32], 0.00–2.30; 3 puertas roble_mel; frente hacia el OESTE (x=3.50).
- Relleno x∈[3.50,4.11], z∈[-2.91,-2.64], 0–2.30 roble_mel (y el pilar existente x∈[3.50,3.82], z∈[-3.24,-2.91] ya es muro).

## DORMITORIO PRINCIPAL (techo 2,46)
- PA01 panelado + estantería (cara hacia el dormitorio, x=4.11): panel roble_mel 0.02 x∈[4.11,4.13], z∈[-2.91,-1.32], 0–2.30; estantería abierta x∈[4.11,4.43] (fondo 0.32), z∈[-3.18,-2.91] (0.27), 0–2.30, 4 baldas roble_mel + tira LED vertical en el lateral.
- CABECERO de listones de roble (render): panel x∈[3.82,7.84], z∈[-3.24,-3.18], 0–1.20, listones verticales de 3 cm cada 5 cm (o bump/geometría de ranuras); oscuro con LED 3000 K en el techo a lo largo de z=-3.24 (x 3.82–7.84).
- CAMA 1.80×2.00: x∈[4.88,6.68], z∈[-3.18,-1.18]; base roble baja 0.12–0.30, colchón 0.30–0.52, ropa de lino beige + manta, 2 almohadas.
- MESITAS de travertino abiertas (cubo con hueco): x∈[4.40,4.84] y [6.72,7.16], z∈[-3.18,-2.78], 0–0.50.
- 2 COLGANTES cilíndricos (travertino/roble) sobre las mesitas, a 1.10–1.30, cable negro.
- BANCO bajo la ventana V02 (plano): x∈[7.53,7.91], z∈[-2.76,-1.05], 0–0.45, roble_mel.

## DORMITORIO 3 (noroeste, techo 2,46)
- A04 armario: x∈[-4.71,-4.11], z∈[-3.18,-1.54], 0–2.30, 4 puertas roble_mel, frente al OESTE.
- E02 estantería fija trapezoidal entre el muro oeste inclinado y x=-7.35, z∈[-3.18,-0.92] (fondo 0.62 al norte → 0.09 al sur): 2 baldas roble_mel de 0.04 a 1.10 y 1.60.
- CAMA NIDO 0.90×2.00: x∈[-7.35,-6.45], z∈[-2.58,-0.58], cabecero al NORTE (la supletoria se queda recogida).
- ESCRITORIO bajo la ventana: x∈[-7.35,-5.25], z∈[-3.18,-2.59], tablero 0.72–0.75 roble_mel, 2 patas/costados; SILLA en (-5.88,-2.40).

## DORMITORIO 2 (suroeste, techo 2,46)
- A03 armario: x∈[-7.04,-6.42], z∈[-0.42,0.78], 0–2.40, 3 puertas roble_mel, frente al ESTE.
- E01 estantería fija trapezoidal entre el muro oeste inclinado y x=-6.42, z∈[0.78,2.46] (fondo 0.62 → 0.23): baldas roble_mel 0.04 a 1.00, 1.48 y 1.94.
- CAMA NIDO 0.90×2.00: x∈[-6.42,-5.52], z∈[0.58,2.58], cabecero al SUR.
- CÓMODA baja: x∈[-5.80,-4.65], z∈[-0.42,0.01], 0–0.80, roble_mel.
- ESCRITORIO: x∈[-4.21,-3.62], z∈[1.39,2.88], tablero a 0.72–0.75; SILLA x∈[-4.52,-4.21], z∈[1.91,2.36] mirando al este.

## ESTUDIO (techo 2,46) — BIBLIOTECA DE CEREZO REUTILIZADA (fotos data/reales/*bibloteca*.jpeg)
Pieza existente del cliente, madera de cerezo barnizada rojiza (`cerezo`), tiradores metálicos curvos. Distribución propuesta (1.91×3.30; puerta P05 barre la esquina noroeste):
- MUEBLES BAJOS en L: bajo la ventana (pared sur) x∈[-3.53,-1.94], z∈[2.43,2.88], 0.08–0.72 + tapa 0.72–0.75; y retorno por la pared oeste x∈[-3.53,-3.08], z∈[1.30,2.43]. Puertas batientes de 0.45 y una cajonera de 4 cajones bajo la ventana.
- ESTANTERÍA ALTA A (con módulo de escritorio) contra la pared este: x∈[-1.94,-1.62] (fondo 0.32), z∈[-0.40,1.05]; 3 calles (0.45/0.50/0.50) con costados de 0.025 hasta 2.25; baldas cada ~0.33 desde 0.80; en la calle central un armario bajo 0–0.74 con encimera.
- MESA PENÍNSULA de extremo redondeado: tablero cerezo 0.03 a 0.72–0.75, x∈[-2.94,-1.94], z∈[0.45,1.05], extremo oeste semicircular (radio 0.30); pie central metal_negro Ø0.08 con base circular Ø0.45 cerca del extremo redondeado.
- ESTANTERÍA ALTA B exenta contra la pared este: x∈[-1.92,-1.62], z∈[1.10,2.40], 3 calles, costados hasta 2.30 (el central sobresale 0.10 arriba como en la foto), 7 baldas.
- SILLA de escritorio en (-2.55,0.75) mirando al este.

## BAÑO 2 — con BAÑERA (oeste, techo 2,30) — PE/A.04 "Baño 1" + render baño
Interior x∈[-4.00,-1.30], z∈[-3.24,-1.54]; pilar/patinillo en la esquina NE x∈[-1.77,-1.30], z∈[-3.24,-2.94].
- BAÑERA acrílica blanca: x∈[-4.00,-3.31], z∈[-3.24,-1.54], 0–0.55 (faldón `travertino_porc`), grifería termostática `cobre` en la pared oeste a 0.80 + ducha de mano; mampara fija de cristal 0.80 en x=-3.31, z∈[-3.24,-2.44], 0.55–2.00.
- INODORO de suelo con cisterna vista (render): cisterna x∈[-3.08,-2.73], z∈[-3.24,-3.09], 0.40–0.85; taza centrada x=-2.905 hasta z=-2.60, 0–0.40.
- MUEBLE LAVABO (1.40, suspendido): x∈[-1.77,-1.30], z∈[-2.94,-1.54], cuerpo 0.30–0.86 roble_mel con 2 cajones y uñero; encimera `resina` 0.86–0.88 con seno integrado centrado z=-2.24; tira LED bajo el mueble a 0.29–0.30; grifo mural `cobre` a 1.05.
- ESPEJO 1.40×0.90 en la pared este x=-1.30 (enrasado sobre el alicatado), z∈[-2.94,-1.54], 1.20–2.10, con tira LED retroiluminada arriba.
- Oscuro con LED 3000 K a lo largo del muro oeste (sobre la bañera), en el techo x∈[-4.00,-3.90].
- ALICATADO `travertino_porc` (placas 0.01 contra el muro): altura 2.30 en muro oeste y en los tramos norte/sur de la bañera (x∈[-4.00,-3.31]); 1.20 en el resto (norte x∈[-3.31,-1.77], caras del pilar, este bajo el espejo, sur fuera del hueco de P04).
- PAVIMENTO porcelánico `travertino_porc` 60×120 en todo el baño.

## BAÑO 1 — con DUCHA (este, techo 2,30) — PE/A.04 "Baño 2"
Interior x∈[-0.93,1.75], z∈[-3.24,-1.54]; nicho de 0.16 en la esquina NO x∈[-0.93,-0.64], z∈[-3.24,-3.08]; trasdosado de 0.16 detrás del inodoro x∈[-0.12,0.76], z∈[-3.24,-3.08].
- DUCHA: plato de obra enrasado (mismo porcelánico con pendiente, sin escalón) x∈[-0.93,-0.12], z∈[-3.08,-1.54]; rociador de techo cuadrado 0.30 `cobre` a 2.20 + grifería `cobre` en la pared oeste; mampara fija de cristal en x=-0.12, z∈[-3.08,-2.49], 0–2.00.
- INODORO SUSPENDIDO: taza x∈[0.14,0.49], z∈[-3.08,-2.55], 0.40 (colgada, sin pie); pulsador cromado/cobre en el trasdosado a 1.00.
- M02 armario empotrado lacado blanco en el trasdosado: x∈[-0.12,0.76], z∈[-3.24,-3.08], 1.20–2.31 (frente enrasado en z=-3.08, 2 puertas con uñero).
- M01 MUEBLE LAVABO (1.00, suspendido): x∈[0.76,1.75], z∈[-3.24,-2.78], cuerpo 0.30–0.86 roble_mel, encimera `resina` 0.86–0.88, seno centrado x=1.25, LED bajo 0.29–0.30; grifo mural `cobre`.
- ESPEJO 1.00×1.11 sobre el lavabo en z=-3.24, x∈[0.76,1.75], 1.20–2.31.
- Oscuro LED 3000 K en el techo junto al muro oeste (x∈[-0.93,-0.83]).
- ALICATADO: 2.30 en el ámbito de la ducha (oeste, norte x∈[-0.93,-0.12] incl. nicho, sur x∈[-0.93,-0.12]); 1.20 en el resto (trasdosado bajo M02, norte bajo el espejo, este fuera de P02, sur).
- PAVIMENTO porcelánico 60×120.

## BALCÓN
- Suelo x∈[8.23,8.86], z∈[0.08,3.88] (gres/terrazo gris claro). Barandilla de pletinas horizontales `metal_negro` bronce oscuro (foto vistaterraza) en x=8.86 y en los lados z=0.08 / 3.88, altura 1.10 (pasamanos 0.05×0.05 + 3 pletinas horizontales + montantes cada 0.60).
- Nada de mesa bistró ni jardineras (no aparecen en el proyecto). Una planta en maceta como mucho.

## Qué eliminar del mobiliario actual
Todo lo que no esté arriba: sofá-cama y armarios inventados, "Armario vestidor" de dorm-1, banco/armario del recibidor antiguo, casoneto, cortinas, mesa bistró y jardineras del balcón, butaca en posición antigua, etc.
