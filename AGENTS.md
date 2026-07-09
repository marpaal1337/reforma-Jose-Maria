# AGENTS.md

This folder is a **document drop, not a codebase**. It contains Spanish-language PDFs for a home renovation ("reforma") for the client **José María Mortés Lerma**. There is no source code, no package manager, no test runner, no build step, and no git repo — do not look for any.

## What's in the folder

Three groups of PDFs, flat (no subdirectories):

1. **Project-lead per-trade packages** (prefix `Jose María Mortes Lerma_<trade>.pdf`, 12 files): `Albañilería`, `Carpintería ext`, `Carpintería int`, `Clima`, `Demolición`, `Detalle baños`, `Electricidad`, `Encimeras`, `Fontanería`, `Pladur`, `Planta distribución`, `Planta estado inicial`. Treat the two `Planta*` files as the before/after floor plans.
2. **General contractor Cyss, version 2.0** (2 files): `Jose María Mortés Lerma. 2.0. Cyss.myp.pdf` (likely *memoria y presupuesto* — scope + budget) and `…Cyss.resumen.pdf` (summary). The `myp` file is the natural cross-reference for totals from the per-trade files.
3. **External/secondary quotes**: `Ventanas Nacher / SOFIA` (windows) and `Valenzuela` interior carpentry, split into `ARMARIOS`, `COCINA`, `PUERTAS`.

## Gotchas a future agent will miss

- **Spelling inconsistency in filenames**: most files use `Mortes`, only the two Cyss files use `Mortés`. Same client. Don't treat them as different people.
- **Duplicate**: `Jose María Mortes Lerma_Carpintería int (1).pdf` has a `(1)` suffix — likely a re-download of the un-suffixed one. Check before assuming it's a new version.
- **NTFS alternate data streams**: every PDF has a sibling `*.pdf:Zone.Identifier` file. These are Windows ADS metadata showing the files came from `https://web.whatsapp.com/`. On Linux they look like normal files; on Windows they would be hidden. Do not interpret them as part of the project.
- **Non-ASCII filenames** (`í`, `é`, `ñ`, spaces). When globbing, prefer `*.pdf` patterns or quote paths. `grep` on bare Spanish words can fail on terminals with the wrong locale (`LANG=C`).
- **All content is in Spanish**. Search terms, line-item names, totals, and trade names are Spanish (`Albañilería`, `Fontanería`, `Pladur`, `myp` = *memoria y presupuesto*, etc.). Translate before searching English docs/forums.

## Conventions when adding files

- Keep the existing flat structure; do not introduce subdirectories without an explicit ask.
- New contractor quotes should follow the existing pattern: `<Trade>[ _<Sub-area>[ _<Contractor>[ _<Doc-type>]]].pdf`.
- Do not delete the `Zone.Identifier` files — they are how the user can tell which platform the PDF came from.

## Verifying changes

There is nothing to build, lint, or test. If you edit or rename files, `ls` is the only verification needed.
