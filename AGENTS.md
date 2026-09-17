# AGENTS.md

This folder is a **document drop, not a codebase**. It contains Spanish-language PDFs (and one Excel) for a home renovation ("reforma") for the client **José María Mortés Lerma**. There is no source code, no package manager, no test runner, and no build step.

## Layout

One folder per trade, plus a few special-purpose folders:

```
.
├── AGENTS.md
├── Albañilería/             (masonry)
├── Carpintería exterior/    (windows, exterior woodwork)
├── Carpintería interior/    (interior woodwork: closets, kitchen, doors)
├── Clima/                   (HVAC)
├── Contratista general/     (Cyss global budget — myp + resumen)
├── Demolición/
├── Detalle baños/
├── Electricidad/
├── Encimeras/               (countertops)
├── Fontanería/              (plumbing)
├── Pladur/                  (plasterboard / drywall)
├── Planos/                  (floor plans: distribución, estado inicial)
└── Presupuesto/             (Presupuesto.xlsx)
```

Within each trade folder, files are named `<Contratista>_<Doc>.pdf`. The legacy "project-lead" PDFs (which had no contractor in the name) are kept with the `desconocido_` prefix to flag the missing attribution — they are the same content as the per-trade packages originally distributed by the project lead.

`Contratista general/` holds Cyss's global budget in two versions:
- `Cyss_v1_myp.pdf` / `Cyss_v1_resumen.pdf` — earlier version (no "2.0" in the original filename)
- `Cyss_v2.0_myp.pdf` / `Cyss_v2.0_resumen.pdf` — version 2.0

`myp` = *memoria y presupuesto* (scope + budget). The `myp` file is the natural cross-reference for totals from the per-trade files.

## Contractors (in case you need to look them up)

- **Albañilería**: Toni
- **Carpintería exterior**: Ventanas Nacher (project "SOFIA")
- **Carpintería interior**: Valenzuela (split into ARMARIOS, COCINA, PUERTAS)
- **Clima**: David Barat
- **Electricidad**: Paracon, Poveda
- **Fontanería**: David Barat
- **General contractor**: Cyss
- **All other trades** (Demolición, Detalle baños, Encimeras, Pladur): only the legacy `desconocido_` document

## Gotchas a future agent will miss

- **Spelling of the client's surname in filenames varies**:
  - `Mortes` — most per-trade PDFs (project lead's files)
  - `Mortés` — the Cyss files only
  - `Martes` — typo by Valenzuela in their filenames (the original "JOSE MARIA MARTES LERMA")
  - All three refer to the same person. Do not treat them as different clients.
- **Legacy `desconocido_` files**: the original `Jose María Mortes Lerma_<trade>.pdf` set had no contractor in the name. The `desconocido_` prefix in the renamed versions signals the missing attribution, not that the content is unknown.
- **NTFS alternate data streams**: every PDF/xlsx has a sibling `*.pdf:Zone.Identifier` file. These are Windows ADS metadata showing the files came from `https://web.whatsapp.com/`. On Linux they look like normal files; on Windows they would be hidden. Do not interpret them as part of the project, and do not delete them — they let the user tell which platform a file came from.
- **Non-ASCII filenames** (`í`, `é`, `ñ`, spaces). When globbing, prefer `*.pdf` patterns or quote paths. `grep` on bare Spanish words can fail on terminals with the wrong locale (`LANG=C`).
- **All content is in Spanish**. Search terms, line-item names, totals, trade names are Spanish. Translate before searching English docs/forums.
- **Multiple quotes per trade exist** (e.g. two for Albañilería from Toni, two for Fontanería from David Barat, two for Electricidad from different contractors). When asked for "the quote for X", the user usually wants a comparison across all of them, not just the first.

## Conventions when adding files

- One folder per trade. Do not create subfolders inside a trade folder unless grouping many quotes by sub-area becomes necessary (e.g. if Carpintería interior splits into ARMARIOS / COCINA / PUERTAS gets crowded).
- Filename pattern: `<Contratista>_<Doc>.pdf` (the trade is already in the folder name; do not repeat it as a prefix).
- If a contractor is unknown, prefix with `desconocido_` (e.g. `desconocido_Albañilería.pdf`).
- New Cyss versions follow `Cyss_v<version>_<myp|resumen>.pdf`.
- Do not delete the `Zone.Identifier` files.

## Analysis pipeline (scripts/, data/, informes/, index.html, planos.html, render3d.html)

The repository now includes an **analysis pipeline** that extracts, parses, and visualises all PDFs. The pipeline is fully **reproducible** — run the scripts in order to regenerate all artefacts from scratch.

### Repo additions

```
.
├── .gitignore                  ignores data/texto/ and __pycache__
├── index.html                  interactive dashboard (33 KB, self-contained except Google Fonts CDN)
├── planos.html                 2D plan viewer (Leaflet, self-contained)
├── render3d.html               interactive 3D model (Three.js inlined, self-contained)
├── libs/
│   └── three.min.js            vendored Three.js r147 (MIT) inlined into render3d.html
├── data/
│   ├── presupuestos.json       master parsed data (27 records with line items)
│   ├── presupuestos.csv        flat table for spreadsheet import
│   ├── auditoria.json          extraction audit (pages, character counts, warnings per PDF)
│   ├── excel.json              Presupuesto.xlsx → parsed columns B & C
│   ├── planos3d.json           3D model data: walls, glass, rooms, footprint, texture rect
│   └── imagenes/
│       ├── planta_textura.jpg  cropped plan used as the 3D floor texture
│       └── geometria_debug.png overlay to verify extracted walls/rooms
│   └── texto/                  (gitignored) raw text dumps per PDF
├── informes/                   29 Markdown reports
│   ├── RESUMEN_EJECUTIVO.md           ← start here
│   ├── AUDITORIA_PDFS.md              extraction quality log
│   ├── COMPARATIVA_CYSS.md            Cyss v1 → v2.0 deltas
│   ├── COMPARATIVA_ALBAÑILERIA.md      Toni 468 (SOFIA) vs Toni 472
│   ├── COMPARATIVA_FONTANERIA.md       David Barat 1-000022 (mixed) vs standalone
│   ├── COMPARATIVA_ELECTRICIDAD.md    Paracon vs Poveda
│   ├── COMPARATIVA_ESCENARIOS.md      economic scenarios comparison
│   ├── HUECOS_Y_DUPLICIDADES.md       gaps, overlapping scopes, missing trades, risks
│   ├── CRUCE_CON_EXCEL.md             contract totals vs planning spreadsheet
│   ├── ANALISIS_PLANOS.md            floor plans (dimensions, layout notes)
│   ├── ANALISTA_COMPARATIVA_GLOBAL.md multi-contractor comparison by trade
│   ├── ANALISTA_CONCILIACION_CYSS.md  Cyss vs subcontractors by chapter
│   ├── ANALISTA_OPTIMIZACION_COSTES.md value engineering proposals
│   ├── ARQUITECTO_MEMORIA_DESCRIPTIVA.md architectural description
│   ├── ARQUITECTO_MEMORIA_CALIDADES.md material specifications
│   ├── ARQUITECTO_ANALISIS_DISTRIBUCION.md layout analysis
│   ├── ARQUITECTO_ANALISIS_ILUMINACION.md lighting analysis
│   ├── APAREJADOR_VERIFICACION_MEDICIONES.md measurement verification
│   ├── APAREJADOR_ANALISIS_MATERIALES.md materials analysis
│   ├── APAREJADOR_SISTEMAS_CONSTRUCTIVOS.md construction systems
│   ├── APAREJADOR_PARTIDAS_ALZADAS.md incomplete items detection
│   ├── PM_PLAN_DE_EJECUCION.md execution plan / Gantt
│   ├── PM_RUTA_CRITICA.md critical path analysis
│   ├── PM_PLAN_PAGOS.md payment schedule
│   ├── DO_PLAN_CONTROL_CALIDAD.md quality control plan
│   ├── DO_CHECKLIST_MATERIALES.md materials checklist
│   ├── DO_ACTAS_VISITA.md site visit reports
│   ├── DO_PROTOCOLO_PRUEBAS_FINALES.md final testing protocol
│   └── DISTRIBUCION_POR_ESTANCIAS.md room-by-room distribution
└── scripts/
    ├── extraer_pdfs.py          pdftotext fallback to pdfplumber → data/texto/
    ├── parsear_presupuestos.py   per-contractor parsers → data/presupuestos.json + .csv
    ├── leer_excel.py              openpyxl → data/excel.json
    ├── auditar.py                 rutaudit → data/auditoria.json + AUDITORIA_PDFS.md
    ├── analizar.py                reads JSONs → reports in informes/
    ├── generar_html.py            reads presupuestos.json → index.html
    ├── generar_geometria3d.py     vector geometry of Planos/distribución.pdf → data/planos3d.json + texture
    └── generar_visor3d.py         data/planos3d.json + libs/three.min.js → render3d.html
```

### How to regenerate

```bash
python3 scripts/extraer_pdfs.py && \
python3 scripts/parsear_presupuestos.py && \
python3 scripts/auditar.py && \
python3 scripts/leer_excel.py && \
python3 scripts/analizar.py && \
python3 scripts/generar_html.py && \
python3 scripts/generar_geometria3d.py && \
python3 scripts/generar_visor3d.py
```

`generar_geometria3d.py` only needs the plan (`Planos/distribución.pdf` + `distribución.png`) and Python deps `pymupdf`, `numpy`, `pillow`. `generar_visor3d.py` needs `libs/three.min.js` (already vendored) and `data/imagenes/planta_textura.jpg`.

### Key findings (as of 2026-07-09)

| Item | Value |
|------|-------|
| Cyss v2.0 total (IVA incl.) | **56.677,94 €** |
| Toni 472 (albañilería) | 21.447 € (5 items marked `?` — unbudgeted) |
| Toni 468 | **SOFIA project** — different client, not applicable |
| David Barat DEF (mixed) | 11.927,23 € fontanería + clima combined |
| Electricidad | **Paracon** 6.056 € (cheaper + 4 instalments) vs Poveda 10.570 € (expired) |
| Encimeras | **Not priced** in Cyss — need a separate stoneworker quote |
| Excel col B | 70.846 € (sum of subcontractor quotes) |
| Excel col C | 79.469 € (alternative scenario — client self-managing) |
| Interior medido del plano (render3d) | **102,9 m²** útiles + 7,5 m² terraza |

### Dashboard (`index.html`)

Opens from `file://` in any modern browser. Features:
- Dark/light mode toggle (persisted in `localStorage`)
- Sortable & filterable main table (all 27+ budget records)
- Donut chart of Cyss v2.0 by trade
- Bar charts comparing multiple quotes per trade
- Timeline visualisation
- KPI cards per trade with budget summaries
- Alert/action block with top recommendations

Google Fonts (Inter + Source Serif 4) are loaded from CDN — requires internet. Fallback fonts are defined and the page is readable offline.

### Visor 3D (`render3d.html`)

Modelo 3D generado de la **geometría vectorial** del plano de distribución (no es una aproximación a ojo: la escala se calibró con las cotas del PDF y es exactamente 1:50, 56,69 pt/m).

- Muros extruidos a 2,60 m clasificados por espesor (`estructural` ≥ 0,14 m, `tabique` ≥ 0,045 m, `vidrio` = carpinterías), suelos por estancia y alicatados de baños.
- Dos modos de suelo: **Plano** (textura del plano recortada) y **Zonas** (color por estancia, superficie medida).
- Slider de altura de muros, slider de posición solar (sombras en tiempo real), etiquetas, ficha por estancia con superficie y coste orientativo (reparto proporcional del total Cyss v2.0), exportación a PNG y vistas `Planta` / `Vista general`.
- Se abre desde `file://`; Three.js va inline (sin CDN ni módulos ES). Solo Google Fonts es externo.
- La detección de estancias (watershed + sellado de huecos) se valida contra las cotas del arquitecto: p. ej. Dormitorio 1 = 8,08 m² vs 8,1 m² etiquetado, Baño 1 = 4,46 m² vs 4,5 m².
- `data/imagenes/geometria_debug.png` es el overlay de control: colores por tipo de muro y áreas detectadas. Revisarlo tras cambiar el plano.

## Agentes / Skills del proyecto (skills/)

El repositorio incluye **skills locales** para que un agente de IA (o el usuario) adopte un rol específico al analizar el proyecto. Cada skill es un archivo `SKILL.md` dentro de su carpeta en `skills/`.

### Roles disponibles

| Rol | Carpeta | Para qué sirve |
|---|---|---|
| **Arquitecto** | `skills/arquitecto/` | Memorias descriptivas y de calidades, análisis de planos, distribución, iluminación, paleta de materiales |
| **Arquitecto Técnico / Aparejador** | `skills/arquitecto-tecnico/` | Verificación de mediciones, análisis de materiales y sistemas constructivos, detección de partidas incompletas |
| **Project Manager** | `skills/project-manager/` | Diagramas de Gantt, planificación de fases, ruta crítica, dependencias entre oficios, plan de pagos |
| **Analista de Presupuestos** | `skills/analista-presupuestos/` | Comparativa de ofertas, conciliación Cyss vs. subcontratistas, detección de huecos y duplicidades, optimización de costes, escenarios económicos |
| **Director de Ejecución** | `skills/director-ejecucion/` | Plan de control de calidad, actas de visita, checklists de materiales, no conformidades, protocolo de pruebas finales |

### Cómo usar una skill

Desde la interfaz de opencode, invoca el skill por su nombre, por ejemplo:

> Usa el skill de project-manager para generar un diagrama de Gantt

O carga el skill directamente con la herramienta `skill`:

```
skill: project-manager
```

Cada skill sabe qué datos leer (`data/presupuestos.json`, `data/excel.json`, `Planos/`, etc.), qué informes previos consultar (`informes/`), y en qué formato generar los outputs.

### Outputs esperados

Todos los outputs se guardan en `informes/` con el prefijo del rol:
- `informes/ARQUITECTO_MEMORIA_DESCRIPTIVA.md`
- `informes/PM_PLAN_DE_EJECUCION.md`
- `informes/ANALISTA_COMPARATIVA_GLOBAL.md`
- etc.

## Verifying changes

There is nothing to build, lint, or test. `ls <folder>/` is the only verification needed. Use `ls` and `git status` to confirm renames/moves landed as intended.

If a new PDF is added: re-run the pipeline above. Check `informes/AUDITORIA_PDFS.md` to confirm the new file was parsed correctly.
