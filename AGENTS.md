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

## Verifying changes

There is nothing to build, lint, or test. `ls <folder>/` is the only verification needed. Use `ls` and `git status` to confirm renames/moves landed as intended.
