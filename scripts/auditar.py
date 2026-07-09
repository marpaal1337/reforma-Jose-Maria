#!/usr/bin/env python3
"""
Genera data/auditoria.json e informes/AUDITORIA_PDFS.md a partir de
data/presupuestos.json. Inventario + tabla resumen legible.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PRES = json.loads((DATA / "presupuestos.json").read_text(encoding="utf-8"))

OUT_JSON = DATA / "auditoria.json"
OUT_MD = ROOT / "informes" / "AUDITORIA_PDFS.md"


def fmt_eur(n) -> str:
    if n is None:
        return "—"
    return f"{n:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def total_de_presupuesto(r) -> float | None:
    """Devuelve el total con IVA si lo tiene, si no el de ejecución material,
    si no el calculado con IVA, si no el calculado sin IVA."""
    for k in ("total_con_iva", "total_ejecucion_material", "total_calculado_con_iva", "total_calculado_sin_iva"):
        v = r.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def main() -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    # Orden: por oficio, luego por contratista, luego por fecha
    ordenados = sorted(
        PRES,
        key=lambda r: (
            r.get("oficio", ""),
            r.get("contratista", ""),
            r.get("fecha") or "9999",
            r.get("archivo", ""),
        ),
    )

    # JSON
    OUT_JSON.write_text(
        json.dumps(ordenados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"OK {len(ordenados)} -> {OUT_JSON}")

    # Markdown
    hoy = datetime.now().strftime("%Y-%m-%d")
    oficios: dict[str, list] = {}
    for r in ordenados:
        oficios.setdefault(r.get("oficio", "?"), []).append(r)

    lineas = [
        "# Auditoría de PDFs",
        "",
        f"_Generado el {hoy} a partir de {len(ordenados)} documentos._",
        "",
        "## Resumen por oficio",
        "",
        "| Oficio | # docs | Rango de totales (IVA incl.) | Contratistas |",
        "|---|---:|---|---|",
    ]
    for oficio, rs in oficios.items():
        totales = [total_de_presupuesto(r) for r in rs]
        totales = [t for t in totales if t is not None]
        if totales:
            rango = f"{fmt_eur(min(totales))} – {fmt_eur(max(totales))}"
        else:
            rango = "—"
        contratistas = sorted({r.get("contratista", "?") for r in rs})
        lineas.append(
            f"| {oficio} | {len(rs)} | {rango} | {', '.join(contratistas)} |"
        )

    lineas += ["", "## Detalle por documento", ""]
    for oficio, rs in oficios.items():
        lineas.append(f"### {oficio}")
        lineas.append("")
        lineas.append("| Archivo | Contratista | Nº ppto | Fecha | Total | Formato |")
        lineas.append("|---|---|---|---|---:|---|")
        for r in rs:
            archivo = r.get("archivo", "?").replace(".txt", ".pdf")
            archivo = archivo.split("__", 1)[-1]
            contr = r.get("contratista", "—")
            np = r.get("num_presupuesto") or r.get("num_borrador") or "—"
            fecha = r.get("fecha") or "—"
            total = total_de_presupuesto(r)
            fmt = r.get("formato", "—")
            lineas.append(
                f"| {archivo} | {contr} | {np} | {fecha} | {fmt_eur(total)} | `{fmt}` |"
            )
        lineas.append("")

    OUT_MD.write_text("\n".join(lineas), encoding="utf-8")
    print(f"OK -> {OUT_MD}")


if __name__ == "__main__":
    main()
