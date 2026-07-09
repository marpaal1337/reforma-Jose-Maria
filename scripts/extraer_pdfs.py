#!/usr/bin/env python3
"""
Extrae texto plano de cada PDF a data/texto/<carpeta>__<archivo>.txt
usando pdfplumber. Sin OCR: todos los PDFs del proyecto son texto.

Uso:
    python3 scripts/extraer_pdfs.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "texto"

SKIP = {"Zone.Identifier", ".git", "scripts", "data", "informes", ".venv", "node_modules"}


def is_pdf(p: Path) -> bool:
    return p.suffix.lower() == ".pdf" and not p.name.endswith(":Zone.Identifier")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(p for p in ROOT.rglob("*.pdf") if is_pdf(p))
    if not pdfs:
        print("No se encontraron PDFs.", file=sys.stderr)
        return 1

    for pdf in pdfs:
        rel = pdf.relative_to(ROOT)
        out = OUT / f"{rel.parent.name}__{pdf.stem}.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            with pdfplumber.open(pdf) as doc:
                pages = [pg.extract_text() or "" for pg in doc.pages]
            out.write_text("\n\n".join(pages), encoding="utf-8")
            chars = sum(len(p) for p in pages)
            print(f"OK  {rel}  ->  {out.name}  ({chars} chars, {len(pages)} pp)")
        except Exception as e:
            print(f"ERR {rel}: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
