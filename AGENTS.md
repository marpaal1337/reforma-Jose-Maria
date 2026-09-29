# AGENTS.md

This repo is a **3D design viewer for a home renovation in Valencia** (Spanish-language plans + renders). It contains **no budgets, no prices, no client personal data**. The budget pipeline (PDFs per trade, `Presupuesto.xlsx`, `data/presupuestos.*`, `index.html` dashboard, economic reports) was **removed on 2026-09-26** to focus on renders and design proposals. The GitHub remote is **private** and the history was purged with `git filter-repo`.

## Layout

```
.
├── AGENTS.md
├── Planos/                  planos renombrados PE_*.pdf sin nombre de cliente
│                            (distribución, cotas, carpintería, albañilería…) +
│                            distribución.pdf / estado inicial
├── data/
│   ├── planos3d.json        3D model data: walls, glass, rooms, footprint, texture rect
│   ├── puertas.json         PE, P01–P07, PL y separador PA02 (PE_carpinteria_interior)
│   ├── ventanas.json        V01–V08 measured from PEI.05/06 + north + facade mapping
│   ├── camaras.json         pano/still camera definitions for the Blender tour
│   ├── mobiliario.glb       furniture + joinery exported from escena.blend (glTF)
│   ├── colisiones.json      huellas de colisión del mobiliario (revisar_mobiliario.py)
│   ├── texturas/            tileable finishes (roble, tarima, mármol, azulejo, tejidos…)
│   ├── pbr/                 CC0 PBR maps (Poly Haven + ambientCG) for the Cycles render
│   │   └── hdri/            venice_sunset_4k.hdr (Poly Haven CC0, sol medido en HDRI_SOL)
│   │                        + venice_sunset_env.jpg (1024×512 LDR para el visor web)
│   ├── assets/              CC0 glTF 2k de Poly Haven (plantas, jarrones) solo para el
│   │                        render Blender; `exportar_glb.py` los excluye (prefijo `asset_`)
│   ├── imagenes/            planta_textura.jpg, geometria_debug.png, mobiliario_debug.png,
│   │                        cotas_debug.png, carpinteria_debug*.png
│   └── reales/              client-provided reference images (renders, AC plan, site photo)
├── renders/
│   ├── panos/               12 equirectangular panoramas 4096×2048
│   └── stills/              perspective stills 2560×1440 (s4…) + s4_salon_ventanal_poc.jpg
├── libs/                    vendored Three.js r147 (MIT) inlined into render3d.html
├── informes/                7 design-only Markdown reports (no prices)
│   ├── ANALISIS_PLANOS.md
│   ├── ARQUITECTO_MEMORIA_DESCRIPTIVA.md
│   ├── ARQUITECTO_MEMORIA_CALIDADES.md
│   ├── ARQUITECTO_ANALISIS_DISTRIBUCION.md
│   ├── ARQUITECTO_ANALISIS_ILUMINACION.md
│   ├── DISTRIBUCION_POR_ESTANCIAS.md   (surfaces only, no costs)
│   └── RENDERS_Y_PLANO_AIRES.md
├── skills/arquitecto/       only remaining skill (design role)
├── index.html               entry point: redirects to render3d.html
├── render3d.html            interactive 3D model (Three.js + Cycles bake inlined, ~30 MB)
└── tour3d.html              360° virtual tour (panoramas inlined, ~13 MB)
```

`renders/escena.blend` is gitignored and regenerated locally; it is not tracked.

## Privacy conventions

- Titles in `render3d.html` / `tour3d.html` are anonymized (`Reforma vivienda Valencia`). Do not reintroduce client names, addresses, contractor names, prices, or dashboard links.
- `Zone.Identifier` files (Windows ADS metadata from WhatsApp Web) are kept where they exist in `Planos/` and `data/reales/`; do not delete them.
- Las fotos nuevas de `data/reales/` con personas o fachada (antiguo salón, biblioteca, vistas de terraza…) **no se versionan**: no añadirlas a git.
- Non-ASCII filenames (`í`, `é`, `ñ`, spaces). When globbing, prefer `*.pdf` patterns or quote paths.
- All content is in Spanish. Search terms, room names, material names are Spanish.

## 3D pipeline (scripts/, data/, renders/, *.html)

Fully **reproducible** from the plan + Python + Blender. Budget scripts (`extraer_pdfs.py`, `parsear_presupuestos.py`, `leer_excel.py`, `auditar.py`, `analizar.py`, `generar_html.py`) were deleted.

Remaining scripts:

```
scripts/
├── generar_geometria3d.py   vector geometry of Planos/PE_planta_distribucion.pdf → data/planos3d.json + texture
├── medir_carpinteria.py     medición de carpinterías en Planos/PE_carpinteria_*.pdf
├── medir_puertas.py         door openings detection → data/puertas.json (self-checking)
├── generar_texturas.py      procedural tileable finishes → data/texturas/*.jpg
├── extraer_ventanas.py      window schedule → data/ventanas.json (reads Planos/ only)
├── generar_blender.py       planos3d + ventanas + camaras → renders/escena.blend
├── mobiliario_proyecto.py   mobiliario y carpintería pieza a pieza (cotas de spec_mobiliario.md;
│                            lo llama build_mobiliario)
├── medir_sol_hdri.py        mide el azimut/elevación del sol en un HDRI (para HDRI_SOL)
├── exportar_glb.py          escena.blend → data/mobiliario.glb (UVs + texturas)
├── generar_visor3d.py       planos3d + three.min.js + GLTFLoader + GLB + texturas → render3d.html
├── render_blender.py        renders one camera from escena.blend (Cycles CPU)
├── generar_tour3d.py        renders/panos + camaras.json → tour3d.html
└── revisar_mobiliario.py    control de colocación del mobiliario del GLB (falla si algo choca)
                            y huellas de colisión → data/colisiones.json
```

### How to regenerate (no budgets)

```bash
python3 scripts/generar_geometria3d.py && \
python3 scripts/medir_puertas.py && \
python3 scripts/generar_texturas.py && \
python3 scripts/extraer_ventanas.py && \
python3 scripts/generar_visor3d.py && \
python3 scripts/generar_tour3d.py
```

Control de la colocación del mobiliario (no necesita Blender):

```bash
python3 scripts/revisar_mobiliario.py   # falla si una pieza choca; deja data/imagenes/mobiliario_debug.png
                                        # y regenera data/colisiones.json (paseo del visor)
```

Blender steps need a local Blender 4.2 LTS (not vendored; install it yourself, do not rely on `/tmp`). En este equipo (WSL) Blender vive en `~/opt/blender/blender` y le faltan `libSM.so.6`/`libICE.so.6` del sistema: `scripts/blender.sh` las resuelve desde `~/opt/blender-libs` (extraídas sin sudo) y lanza Blender. Usa el envoltorio:

```bash
./scripts/blender.sh -b --factory-startup -noaudio -P scripts/generar_blender.py   # escena
./scripts/blender.sh -b renders/escena.blend -noaudio -P scripts/exportar_glb.py   # data/mobiliario.glb
./scripts/blender.sh -b renders/escena.blend -noaudio -P scripts/render_blender.py -- \
    --cam p03_salon_ventanal --out renders/panos/p03_salon_ventanal.jpg \
    --samples 320 --res 4096x2048
python3 scripts/generar_visor3d.py
python3 scripts/generar_tour3d.py
```

En WSL, **no lances el horneado a la vez que capturas/render** (el equipo ha sufrido caídas por carga concurrente). Un proceso a la vez y con `nice` si hay que seguir trabajando.

#### Calidad del render (actualizado 2026-09-26)

`generar_blender.py` usa **materiales PBR reales** de `data/pbr/` (Poly Haven + ambientCG, CC0). Si falta `data/pbr/`, cae a procedurales.

- **Cielo**: HDRI real `data/pbr/hdri/venice_sunset_4k.hdr` (CC0) + sol direccional alineado (`SOL_AZ`); light portals reales en cada hueco de `ventanas.json` + relleno suave por hueco; downlights como **spot 70°**; exposición +1,4 EV, AgX Base Contrast, light tree y cáusticas off. La viñeta del compositor solo se aplica a los stills (en panos, `render_blender.py` la desactiva).
- **Detalle**: pintura con micro-bump y albedo realista, vidrio IOR 1,52, **rodapiés** por estancia, bevel 4 mm en muros, mármol y mosaico PBR en baños.
- **Acabados del proyecto (2026-09-29)**: techos a 2,30/2,46 con tabicas de pladur; suelo de madera en toda la vivienda salvo baños (travertino porcelánico 60×120) y terraza; alicatado de travertino (2,30 en zona de agua, 1,20 en el resto) en baños y lavadero; pared de TV revestida, pilar de hormigón picado y tiras LED (3000 K; 4000 K en cocina); ventanas negras y fachada salmón. Texturas en `data/texturas/` y `data/pbr/`: Silestone Charcoal y Dekton Marmorio (sin juntas), cerezo y hormigón abujardado.
- **Atrezzo CC0** (`data/assets/`, Poly Haven): plantas en maceta y jarrones con fallback procedural; se excluyen del GLB del visor (`asset_*`).
- Stills a **2560×1440 con DOF f/5,6**.

`generar_geometria3d.py` only needs the plan (`Planos/PE_planta_distribucion.pdf` + `distribución.png`) and Python deps `pymupdf`, `numpy`, `pillow`. `generar_visor3d.py` needs `libs/three.min.js` y `libs/GLTFLoader.js` (ya vendored), `data/imagenes/planta_textura.jpg`, `data/texturas/` y `data/mobiliario.glb` (si falta el GLB, el visor arranca sin mobiliario; si falta `data/colisiones.json`, el paseo queda solo con los muros).

Tiempos medidos: ~20 min por panorama 4096×2048 a 320 muestras (Cycles CPU, 20 hilos, 2 en paralelo). `renders/escena.blend` no se versiona (se regenera).

### Visor 3D (`render3d.html`)

Modelo 3D generado de la **geometría vectorial** del plano de distribución PE/A.03 (escala calibrada 1:50, 56,69 pt/m). **13 estancias, 95,4 m² útiles**, con las alturas del plano (2,46 m libres y 2,30 m con falso techo en baños, vestidor, pasillo, cocina y recibidor).

- Muros extruidos a 2,60 m clasificados por espesor (`estructural` ≥ 0,14 m, `tabique` ≥ 0,045 m, `vidrio` = carpinterías), suelos por estancia y alicatados de baños. Los muros van **fusionados en 3 mallas** (una por tipo) y los contornos en un solo `LineSegments`; la altura es fija (2,60 m, sin slider ni intro animada).
- **Puertas PE, P01–P07 y PL + separador PA02 desde `data/puertas.json`** (PE_carpinteria_interior). `generar_geometria3d.py` punzona los huecos en los muros; `generar_blender.py:build_puertas()` pone marcos, hojas y dinteles. P04 (baño de la bañera) es corredera lacada blanca; PE y PL cruzan el paso (marcadas `en_paso`): no punzonan muro y se montan sin dintel.
- **Mobiliario real** de `data/mobiliario.glb` + acabados de `data/texturas/`, **siempre visible** (sin conmutador: toda la casa). Las piezas y sus cotas están en `scripts/mobiliario_proyecto.py` (fuente: `spec_mobiliario.md`, PE/I.06-07, PE/A.03-04, PE/I.01 y PE/I.09); `generar_blender.py:build_mobiliario()` solo lo invoca. El atrezzo CC0 del render (`asset_*`) no viaja al GLB para no disparar el tamaño.
- **Colisiones con mobiliario**: `revisar_mobiliario.py` exporta `data/colisiones.json` (huellas convexas en planta) y `generar_visor3d.py` las embebe; `colisionar()` hace círculo-polígono además de los segmentos de muros. El modo Vuelo sigue sin colisionar.
- Entorno de reflejos PBR desde el propio HDRI reducido (`data/pbr/hdri/venice_sunset_env.jpg`, inline) con degradado de respaldo.
- **Tres modos de cámara**: `Órbita`, `Caminar` (pointer lock, WASD, altura de ojo 1,62 m) y `Vuelo`. En táctil, joystick + arrastre para mirar.
- Dos modos de suelo en la maqueta de respaldo: **Plano** y **Zonas** (en Realista los oculta el horneado). Etiquetas, ficha por estancia con **superficie (sin costes)**, exportación a PNG y vistas `Planta` / `Vista general`.
- **Dibujo bajo demanda** (`pedirFrame()`): sólo se renderiza cuando cambia cámara, teclas, sol o selección; en reposo la GPU queda a cero y las etiquetas sólo se recalculan en esos fotogramas. Resolución adaptativa: `pixelRatio` 1 mientras la cámara se mueve y `min(dpr, 2)` (1,5 táctil) al parar.
- Sin `logarithmicDepthBuffer` ni `preserveDrawingBuffer`; `near/far` por modo (órbita 0,1/300, caminar-vuelo 0,08/250, Realista 0,08/5.000 con el cielo a 0,9·far). El PNG se sigue exportando dibujando justo antes de `toBlob`.
- **Sombras**: el sol está fijo al centro de la vivienda, `shadowMap.autoUpdate=false` y sólo se recalcula al mover el sol, cambiar el mobiliario visible o cruzar el umbral del techo (2,45 m); en Realista se desactivan (la luz ya está horneada).
- **Datos grandes en etiquetas de datos inertes** (`<script type="application/json|octet-stream">`) y decodificación nativa con `fetch(data:)` (respaldo `atob`). Arranca en Realista (o en maqueta si falta el horneado) y carga la maqueta en segundo plano; ambos modos se precompilan (la RV y las capturas usan la maqueta).
- **Indicador `?perf`** (fps, ms, draw calls, triángulos, programas): abrir `render3d.html?perf`.
- Se abre desde `file://`; Three.js + GLTFLoader van inline. Solo Google Fonts es externo.
- `data/imagenes/geometria_debug.png` es el overlay de control tras cambiar el plano.
- La ficha de estancia muestra miniaturas de `data/reales/` (`RENDERS`). Si se añaden imágenes, actualizar `RENDERS` en `scripts/generar_visor3d.py`.
- **Distribución vigente: PE.A.02**. El plano de aires es solo croquis de conductos del instalador, no una versión alternativa. Detalle en `informes/RENDERS_Y_PLANO_AIRES.md`.

### Visor realista (horneado Cycles + entorno OSM)

- `scripts/extraer_entorno.py`: OpenStreetMap → `data/entorno.json`. Las coordenadas se pasan por CLI y **no se versionan** (`--lat --lon --rumbo [--radio]`, p. ej. un punto de Street View frente a la fachada). El JSON solo guarda geometría relativa en metros de la escena (volúmenes con nº de plantas, calzadas, carriles bici, verdes y árboles), sin lat/lon ni nombres de calles. Datos © OpenStreetMap contributors (ODbL 1.0).
- `scripts/hornear_visor.py`: hornea la luz de Cycles de `renders/escena.blend` → `data/visor/`. Se lanza con Blender (`./scripts/blender.sh -b renders/escena.blend -noaudio -P scripts/hornear_visor.py -- [--muestras N] [--res N] [--rapido] [--salida <dir>]`; `--salida` permite probar sin tocar `data/visor`). Genera `interior.glb` (UV de material + lightmap), `lm_a/b.jpg`, `suelo_cerca/lejos.jpg`, `cielo.jpg`, `reflejo.jpg`, `arbol_*.webp` y `visor.json`. Coste: rápido (`--rapido`, 32 muestras/1024) ~10 min; completo 128 muestras con `--res 2048` ~60–90 min; `--res 4096` (por defecto) multiplica ×4 el tiempo (~4 h). El horneado se corta a medias si WSL se reinicia: deja escrito `visor.json` solo al final y no mezcles un horneado parcial con el anterior.
- `scripts/visor_realista.js`: modo **Realista** del visor (interior con lightmaps + PBR del render y ciudad OSM alrededor a la altura del 7º piso). Lo inyecta `scripts/generar_visor3d.py` (`--visor <dir>` para horneados alternativos). Es el **modo por defecto y único** (sin conmutador en la interfaz; en RV se fuerza la maqueta): `setRealista(true)` tras la carga, y si falta el horneado cae a la maqueta. La exposición se calibra contra los stills Cycles con la constante `AJUSTE_EXPOSICION` (barrido medido con `capturas.mjs` y `ref_cycles.py`: EV 0,90 final frente al 2,30 de usar `exposicion` tal cual; sin compensar salía +0,3/+0,6 EV).
- `scripts/capturas.mjs` + `scripts/capturas.sh`: 6 capturas automáticas del visor con Playwright/Chromium (vistas: `orbita`, `salon`, `terraza`, `cocina`, `dormitorio`, `fachada`). Flags: `--visor/--salida/--ancho/--alto`, `--maqueta` (captura la maqueta en vez del modo Realista) y `--medir` (sin capturas: imprime peso del HTML, tiempo hasta estar listo, draw calls/triángulos/programas/memoria, y ms por fotograma en reposo y orbitando). `capturas.sh` cachea `playwright-core` en `~/.cache/opencode-reforma` (no depende de `/tmp`).
- `scripts/ref_cycles.py`: referencia Cycles de la misma cámara que las capturas (`--cam/--todas`, más `--samples/--res/--out/--out-dir`). Usa `scripts/blender.sh`.
- `data/visor/` es un **artefacto local regenerable** (ya en `.gitignore`): se regenera con `hornear_visor.py` y no se versiona.

### Tour 360 (`tour3d.html`)

Tour virtual con **12 panoramas equirectangulares** desde la geometría del PE.A.02.

- Esfera equirectangular (Three.js inline), arrastrar para mirar, rueda para zoom, teclado.
- **Hotspots** a estancias vecinas, tira de navegación inferior y **miniplano** (clic para saltar).
- Autocontenido (~13 MB con panos 4096×2048). Solo fallan las fuentes de Google sin internet.

## Skills (skills/)

Solo queda el rol de diseño:

| Rol | Carpeta | Para qué sirve |
|---|---|---|
| **Arquitecto** | `skills/arquitecto/` | Memorias descriptivas y de calidades, análisis de planos, distribución, iluminación, paleta de materiales |

Los skills de presupuestos, aparejador, project-manager y dirección de ejecución se eliminaron con el pipeline económico.

Outputs de diseño en `informes/` con prefijo `ARQUITECTO_`, más `ANALISIS_PLANOS.md`, `DISTRIBUCION_POR_ESTANCIAS.md` y `RENDERS_Y_PLANO_AIRES.md`.

## Verifying changes

There is nothing to build or lint. `ls <folder>/` + `git status` para lo demás, y tras tocar mobiliario:

```bash
python3 scripts/revisar_mobiliario.py   # debe terminar con 0 incumplimientos
```

(no necesita Blender: lee `data/mobiliario.glb` y deja `data/imagenes/mobiliario_debug.png`).

Do not reintroduce budget files, prices, client names, addresses, or dashboard links. Visor/tour must stay free of currency amounts, contractor names, client surnames, street addresses and postal codes (spot-check ignoring base64 blobs).
