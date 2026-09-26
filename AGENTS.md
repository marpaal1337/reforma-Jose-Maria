# AGENTS.md

This repo is a **3D design viewer for a home renovation in Valencia** (Spanish-language plans + renders). It contains **no budgets, no prices, no client personal data**. The budget pipeline (PDFs per trade, `Presupuesto.xlsx`, `data/presupuestos.*`, `index.html` dashboard, economic reports) was **removed on 2026-09-26** to focus on renders and design proposals. The GitHub remote is **private** and the history was purged with `git filter-repo`.

## Layout

```
.
├── AGENTS.md
├── Planos/                  (floor plans: distribución, estado inicial + PNGs)
├── data/
│   ├── planos3d.json        3D model data: walls, glass, rooms, footprint, texture rect
│   ├── puertas.json         D0–D8 + PA02 measured from PE.A.02/PEI.07
│   ├── ventanas.json        V01–V08 measured from PEI.05/06 + north + facade mapping
│   ├── camaras.json         pano/still camera definitions for the Blender tour
│   ├── mobiliario.glb       furniture + joinery exported from escena.blend (glTF)
│   ├── texturas/            tileable finishes (roble, tarima, mármol, azulejo, tejidos…)
│   ├── pbr/                 CC0 PBR maps (Poly Haven + ambientCG) for the Cycles render
│   ├── imagenes/            planta_textura.jpg, geometria_debug.png, plano_aires_recorte.jpg
│   ├── reales/              client-provided reference images (renders, AC plan, site photo)
│   └── planos_b64.json      base64 plans for planos.html
├── renders/
│   ├── panos/               12 equirectangular panoramas 4096×2048
│   └── stills/              perspective stills 1920×1080
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
├── planos.html              2D plan viewer (Leaflet, self-contained, ~413 KB)
├── render3d.html            interactive 3D model (Three.js inlined, ~3.3 MB)
└── tour3d.html              360° virtual tour (panoramas inlined, ~7.5 MB)
```

`renders/escena.blend` is gitignored and regenerated locally; it is not tracked.

## Privacy conventions

- Titles in `planos.html` / `render3d.html` / `tour3d.html` are anonymized (`Reforma vivienda Valencia`). Do not reintroduce client names, addresses, contractor names, prices, or `index.html` links.
- `Zone.Identifier` files (Windows ADS metadata from WhatsApp Web) are kept where they exist in `Planos/` and `data/reales/`; do not delete them.
- Non-ASCII filenames (`í`, `é`, `ñ`, spaces). When globbing, prefer `*.pdf` patterns or quote paths.
- All content is in Spanish. Search terms, room names, material names are Spanish.

## 3D pipeline (scripts/, data/, renders/, *.html)

Fully **reproducible** from the plan + Python + Blender. Budget scripts (`extraer_pdfs.py`, `parsear_presupuestos.py`, `leer_excel.py`, `auditar.py`, `analizar.py`, `generar_html.py`) were deleted.

Remaining scripts:

```
scripts/
├── generar_geometria3d.py   vector geometry of Planos/distribución.pdf → data/planos3d.json + texture
├── medir_puertas.py         door openings detection → data/puertas.json (self-checking)
├── generar_texturas.py      procedural tileable finishes → data/texturas/*.jpg
├── extraer_ventanas.py      window schedule → data/ventanas.json (reads Planos/ only)
├── generar_blender.py       planos3d + ventanas + camaras → renders/escena.blend
├── exportar_glb.py          escena.blend → data/mobiliario.glb (UVs + texturas)
├── generar_visor3d.py       planos3d + three.min.js + GLTFLoader + GLB + texturas → render3d.html
├── render_blender.py        renders one camera from escena.blend (Cycles CPU)
└── generar_tour3d.py        renders/panos + camaras.json → tour3d.html
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

Blender steps need a local Blender 4.2 LTS (not vendored; install it yourself, do not rely on `/tmp`):

```bash
blender -b --factory-startup -noaudio -P scripts/generar_blender.py        # escena
blender -b renders/escena.blend -noaudio -P scripts/exportar_glb.py        # data/mobiliario.glb
blender -b renders/escena.blend -noaudio -P scripts/render_blender.py -- \
    --cam p03_salon_ventanal --out renders/panos/p03_salon_ventanal.jpg \
    --samples 320 --res 4096x2048
python3 scripts/generar_visor3d.py
python3 scripts/generar_tour3d.py
```

`generar_geometria3d.py` only needs the plan (`Planos/distribución.pdf` + `distribución.png`) and Python deps `pymupdf`, `numpy`, `pillow`. `generar_visor3d.py` needs `libs/three.min.js` y `libs/GLTFLoader.js` (ya vendored), `data/imagenes/planta_textura.jpg`, `data/texturas/` y `data/mobiliario.glb` (si falta el GLB, el visor arranca sin mobiliario).

Tiempos medidos: ~20 min por panorama 4096×2048 a 320 muestras (Cycles CPU, 20 hilos, 2 en paralelo). `renders/escena.blend` no se versiona (se regenera).

### Visor 3D (`render3d.html`)

Modelo 3D generado de la **geometría vectorial** del plano de distribución (escala calibrada 1:50, 56,69 pt/m).

- Muros extruidos a 2,60 m clasificados por espesor (`estructural` ≥ 0,14 m, `tabique` ≥ 0,045 m, `vidrio` = carpinterías), suelos por estancia y alicatados de baños.
- **Puertas D0–D8 + separador PA02 desde `data/puertas.json`**. `generar_geometria3d.py` punzona los huecos en los muros; `generar_blender.py:build_puertas()` pone marcos, hojas y dinteles.
- **Mobiliario real** de `data/mobiliario.glb` + acabados de `data/texturas/`.
- **Tres modos de cámara**: `Órbita`, `Caminar` (pointer lock, WASD, altura de ojo 1,62 m) y `Vuelo`. En táctil, joystick + arrastre para mirar.
- Dos modos de suelo: **Plano** y **Zonas**. Slider de altura de muros, slider solar, etiquetas, ficha por estancia con **superficie (sin costes)**, exportación a PNG y vistas `Planta` / `Vista general`.
- Se abre desde `file://`; Three.js + GLTFLoader van inline. Solo Google Fonts es externo.
- `data/imagenes/geometria_debug.png` es el overlay de control tras cambiar el plano.
- Botón **Galería**: muestra `data/reales/` + plano de aires. Si se añaden imágenes, actualizar `RENDERS`/`GALERIA` en `scripts/generar_visor3d.py`.
- **Distribución vigente: PE.A.02**. El plano de aires es solo croquis de conductos del instalador, no una versión alternativa. Detalle en `informes/RENDERS_Y_PLANO_AIRES.md`.

### Tour 360 (`tour3d.html`)

Tour virtual con **12 panoramas equirectangulares** desde la geometría del PE.A.02.

- Esfera equirectangular (Three.js inline), arrastrar para mirar, rueda para zoom, teclado.
- **Hotspots** a estancias vecinas, tira de navegación inferior y **miniplano** (clic para saltar).
- Autocontenido (~7,5 MB). Solo fallan las fuentes de Google sin internet.

#### Calidad del render

`generar_blender.py` usa **materiales PBR reales** de `data/pbr/` (Poly Haven + ambientCG, CC0). Si falta `data/pbr/`, cae a procedurales.

## Skills (skills/)

Solo queda el rol de diseño:

| Rol | Carpeta | Para qué sirve |
|---|---|---|
| **Arquitecto** | `skills/arquitecto/` | Memorias descriptivas y de calidades, análisis de planos, distribución, iluminación, paleta de materiales |

Los skills de presupuestos, aparejador, project-manager y dirección de ejecución se eliminaron con el pipeline económico.

Outputs de diseño en `informes/` con prefijo `ARQUITECTO_`, más `ANALISIS_PLANOS.md`, `DISTRIBUCION_POR_ESTANCIAS.md` y `RENDERS_Y_PLANO_AIRES.md`.

## Verifying changes

There is nothing to build, lint, or test. `ls <folder>/` + `git status` is the only verification needed.

Do not reintroduce budget files, prices, client names, addresses, or dashboard links. Visor/tour/planos must stay free of currency amounts, contractor names, client surnames, street addresses and postal codes (spot-check ignoring base64 blobs).
