#!/usr/bin/env python3
"""
Genera todos los informes de análisis:
- RESUMEN_EJECUTIVO.md
- COMPARATIVA_ALBAÑILERIA.md
- COMPARATIVA_FONTANERIA.md
- COMPARATIVA_ELECTRICIDAD.md
- COMPARATIVA_CYSS.md
- HUECOS_Y_DUPLICIDADES.md
- CRUCE_CON_EXCEL.md
- ANALISIS_PLANOS.md
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
INF = ROOT / "informes"
PRES = json.loads((DATA / "presupuestos.json").read_text(encoding="utf-8"))
EXCEL = json.loads((DATA / "excel.json").read_text(encoding="utf-8"))

INF.mkdir(parents=True, exist_ok=True)


def fmt_eur(n) -> str:
    if n is None:
        return "—"
    return f"{n:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def total(r) -> float | None:
    for k in ("total_con_iva", "total_ejecucion_material", "total_calculado_con_iva", "total_calculado_sin_iva"):
        v = r.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def sin_iva(r) -> float | None:
    """Devuelve el total sin IVA (mejor estimación)."""
    for k in ("total_sin_iva", "total_ejecucion_material", "total_calculado_sin_iva", "base_imponible"):
        v = r.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def grupo_por_oficio(oficio: str) -> list[dict]:
    return [r for r in PRES if r.get("oficio") == oficio]


# ==== ALBAÑILERÍA ====

def informe_albanileria() -> None:
    rs = grupo_por_oficio("Albañilería")
    rs = [r for r in rs if r.get("formato") != "desconocido"]
    out = ["# Albañilería — comparativa", ""]
    out.append("_Generado el " + datetime.now().strftime("%Y-%m-%d") + "._")
    out.append("")
    out.append("Hay **dos presupuestos de Toni** para dos proyectos distintos, según la cabecera del PDF:")
    out.append("")
    out.append("| Nº | Cliente en cabecera | Fecha | Total estimado (IVA incl.) | Notas |")
    out.append("|---:|---|---:|---:|---|")
    for r in rs:
        cliente = r.get("cliente_cabecera") or "—"
        fecha = r.get("fecha") or "—"
        t = total(r)
        arch = r["archivo"].split("__", 1)[-1].replace(".txt", ".pdf")
        out.append(f"| {arch} | {cliente} | {fecha} | {fmt_eur(t)} | {r.get('nota','')} |")
    out.append("")
    out.append("## Conclusión")
    out.append("")
    out.append("- **Toni 468 (PROYECTO SOFIA, 2025-11-09)** — el cliente en cabecera es 'SOFIA', no José María. "
               "Probablemente es el presupuesto que la arquitecta Sofia Palacios preparó para su propio proyecto "
               "o para un cliente homónimo. **No aplica** a esta reforma. Se conserva por trazabilidad.")
    out.append("- **Toni 472 (REFORMA CALLE JOSE MARIA LERMA, 2026-03-17)** — el presupuesto que aplica. "
               "**~21.447 €** (IVA incl.) calculado como suma de las 29 partidas con importe de las 34 totales. "
               "**Faltan importes en 5 partidas** (marcadas con '?' en el PDF). Tres de ellas son del estilo "
               "'*regatas necesarias*', '*colocación de vierteaguas*', '*desmontaje de split con recuperación*' — "
               "el propio contratista no las cerró a la espera de más datos. **Hay que pedirle a Toni que las cierre.**")
    out.append("- **Comparado con Cyss v2.0**: Albañilería en Cyss = 13.880,05 € (sin IVA). "
               "Toni 472 = 17.725 € (sin IVA) → **Toni cobra un 28% más** que Cyss para la misma partida. "
               "Esto es esperable: Toni es subcontrata directa (incluye su margen), Cyss puede tener tarifas "
               "más ajustadas o estar cotizando con criterios distintos. **Recomendación: pedir a Toni que "
               "desglose sus partidas para poder compararlas 1-a-1 con Cyss antes de descartar la más barata.**")
    out.append("")
    (INF / "COMPARATIVA_ALBAÑILERIA.md").write_text("\n".join(out), encoding="utf-8")


# ==== FONTANERÍA ====

def informe_fontaneria() -> None:
    rs = grupo_por_oficio("Fontanería")
    rs = [r for r in rs if r.get("formato") != "desconocido"]
    out = ["# Fontanería — comparativa", ""]
    out.append("_Generado el " + datetime.now().strftime("%Y-%m-%d") + "._")
    out.append("")
    out.append("David Barat ha emitido **tres** documentos en este oficio. Hay que entender qué cubre cada uno:")
    out.append("")
    out.append("| Documento | Nº | Fecha | Total | Alcance (de la cabecera) |")
    out.append("|---|---:|---:|---:|---|")
    for r in rs:
        arch = r["archivo"].split("__", 1)[-1].replace(".txt", ".pdf")
        np = r.get("num_presupuesto") or "—"
        fecha = r.get("fecha") or "—"
        t = total(r)
        # Para describir el alcance, parseamos del texto el bloque de descripción
        txt_path = DATA / "texto" / r["archivo"]
        alcance = ""
        if txt_path.exists():
            txt = txt_path.read_text(encoding="utf-8")
            # Tomar las primeras líneas en mayúsculas tras "ARTÍCULO DESCRIPCIÓN"
            for chunk in txt.split("ARTÍCULO DESCRIPCIÓN"):
                if "INSTALACION" in chunk or "OBRA" in chunk:
                    lineas = [l.strip() for l in chunk.splitlines() if l.strip()]
                    alcance = " / ".join(lineas[:3])[:120]
                    break
        out.append(f"| {arch} | {np} | {fecha} | {fmt_eur(t)} | {alcance or '—'} |")
    out.append("")
    out.append("## Conclusión")
    out.append("")
    out.append("- **1-000022 DEF (2026-03-10, 11.927,23 € sin IVA)** es un **presupuesto consolidado** "
               "que incluye TANTO fontanería como clima. Es la oferta 'definitiva' y combina los dos oficios. "
               "**No es comparable** con los otros dos.")
    out.append("- **1-000079 (2025-11-04, 4.065,60 € IVA incl.)** es la **oferta inicial de fontanería** solamente. "
               "Quedó superada por el 1-000022. **Descartado.**")
    out.append("- **Cyss v2.0 cap. 05 = 4.400,00 € sin IVA** (5.280 € con IVA). Coincide básicamente con el 1-000079.")
    out.append("- **Comparativa efectiva fontanería**: 1-000079 (4.065,60 € IVA incl.) vs Cyss (5.280 € IVA incl.). "
               "**Cyss encarece un 30%**, probablemente porque incluye 'Ayudas albañilería' que el 1-000079 no metía.")
    out.append("- **Decisión recomendada**: para una comparativa limpia hay que pedir a David Barat una "
               "**oferta desglosada solo-fontanería** equivalente a la de Cyss (sin ayudas de albañilería).")
    out.append("")
    (INF / "COMPARATIVA_FONTANERIA.md").write_text("\n".join(out), encoding="utf-8")


# ==== ELECTRICIDAD ====

def informe_electricidad() -> None:
    rs = grupo_por_oficio("Electricidad")
    rs = [r for r in rs if r.get("formato") != "desconocido"]
    out = ["# Electricidad — comparativa", ""]
    out.append("_Generado el " + datetime.now().strftime("%Y-%m-%d") + "._")
    out.append("")
    out.append("Dos contratistas distintos para el mismo trabajo. **Esta es la decisión de compra más clara** del proyecto:")
    out.append("")
    out.append("| Contratista | Documento | Fecha | Base imp. | Total (IVA incl.) | Forma de pago |")
    out.append("|---|---|---:|---:|---:|---|")
    for r in rs:
        arch = r["archivo"].split("__", 1)[-1].replace(".txt", ".pdf")
        contr = r.get("contratista", "?")
        fecha = r.get("fecha") or "—"
        base = r.get("base_imponible") or sin_iva(r) or 0
        t = total(r) or r.get("total_con_iva")
        # Forma de pago
        fp = r.get("forma_de_pago") or r.get("valido_hasta")
        fp_str = ""
        if isinstance(fp, list):
            fp_str = " · ".join(f"{p['pct']}% {p['hito']}" for p in fp)
        elif isinstance(fp, str):
            fp_str = f"Válido hasta {fp}"
        out.append(f"| {contr} | {arch} | {fecha} | {fmt_eur(base)} | {fmt_eur(t)} | {fp_str or '—'} |")
    out.append("")
    out.append("## Conclusión")
    out.append("")
    out.append("- **Paracon (2026-7)**: 6.056,05 € IVA incl. · 5.005 € base · 21% IVA. "
               "Cliente en cabecera 'TONI AMORES' (es decir, Paracon trabaja para Toni, que es el albañil). "
               "**Forma de pago: 15% firma, 35% canalización, 35% cableado, 15% final**. "
               "Incluye: cuadro eléctrico, 46 enchufes 16A, 37 interruptores/conmutadores, telefonillo, etc. "
               "**NO incluye iluminación** (lo dice el PDF).")
    out.append("- **Poveda (borrador #9)**: 6.402,11 € IVA incl. · 5.291 € base · 21% IVA. "
               "Documento de noviembre 2025, **caducado el 16/11/2025**. "
               "Incluye downlights, red de telecomunicaciones, videoportero.")
    out.append("- **Cyss v2.0 cap. 04 = 7.129,20 € sin IVA** (8.555 € IVA incl.). Es **más caro** que ambas.")
    out.append("- **Diferencia Paracon vs Poveda: ~346 €** (Paracon más barato). Poveda está caducado.")
    out.append("- **Recomendación**: aceptar **Paracon** si el alcance encaja. Su oferta es más reciente, "
               "está adaptada a planos, y permite financiar la obra en 4 hitos. "
               "Pedirle que confirme que lo de Poveda está incluido (especialmente videoportero y "
               "red de telecomunicaciones, que Paracon no detalla explícitamente).")
    out.append("")
    (INF / "COMPARATIVA_ELECTRICIDAD.md").write_text("\n".join(out), encoding="utf-8")


# ==== CYSS v1 vs v2.0 ====

def informe_cyss() -> None:
    v1 = next((r for r in PRES if r["archivo"] == "Contratista general__Cyss_v1_resumen.txt"), None)
    v2 = next((r for r in PRES if r["archivo"] == "Contratista general__Cyss_v2.0_resumen.txt"), None)
    out = ["# Cyss v1 vs v2.0 — comparativa del presupuesto general", ""]
    out.append("_Generado el " + datetime.now().strftime("%Y-%m-%d") + "._")
    out.append("")
    out.append("Cyss es el **contratista general**. Su presupuesto va por capítulos y resume el coste total del proyecto.")
    out.append("")
    if not (v1 and v2):
        out.append("(No se han encontrado ambos PDFs de resumen)")
        (INF / "COMPARATIVA_CYSS.md").write_text("\n".join(out), encoding="utf-8")
        return
    out.append(f"- **v1** (17-10-2025): total **{fmt_eur(v1['total_con_iva'])}** · base {fmt_eur(v1.get('total_ejecucion_material'))}")
    out.append(f"- **v2.0** (04-06-2026): total **{fmt_eur(v2['total_con_iva'])}** · base {fmt_eur(v2.get('total_ejecucion_material'))}")
    out.append(f"- **Variación**: {fmt_eur(v2['total_con_iva'] - v1['total_con_iva'])} ({(v2['total_con_iva']/v1['total_con_iva']-1)*100:+.1f}%)")
    out.append("")
    out.append("## Desglose por capítulo")
    out.append("")
    out.append("| Capítulo | v1 (€) | v2.0 (€) | Δ | Δ % |")
    out.append("|---|---:|---:|---:|---:|")
    caps_v1 = {c["capitulo"] + " " + c["nombre"]: c for c in v1.get("capitulos", [])}
    caps_v2 = {c["capitulo"] + " " + c["nombre"]: c for c in v2.get("capitulos", [])}
    keys = sorted(set(caps_v1) | set(caps_v2))
    for k in keys:
        c1 = caps_v1.get(k, {}).get("euros")
        c2 = caps_v2.get(k, {}).get("euros")
        if c1 is None and c2 is None: continue
        d = (c2 or 0) - (c1 or 0)
        pct = (c2 / c1 - 1) * 100 if c1 else None
        out.append(f"| {k} | {fmt_eur(c1)} | {fmt_eur(c2)} | {fmt_eur(d) if (c1 is not None and c2 is not None) else '—'} | {f'{pct:+.1f}%' if pct is not None else '—'} |")
    out.append("")
    out.append("## Conclusión")
    out.append("")
    out.append("- **Albañilería baja mucho** (22.700 → 13.880, -38.9%): en v2.0 desaparecen del cap. 02 las líneas de yeso, "
               "alicatado, pintura, etc. — se han movido al cap. 03 (Pladur). Es un **reparto interno**, no un ahorro real.")
    out.append("- **Pladur sube mucho** (4.767 → 10.448, +119%): coherente con el punto anterior. Ahora incluye "
               "tabiques, trasdosados, placa hidrófuga. Cyss ha afinado el alcance.")
    out.append("- **Demolición sube** (3.587 → 4.571, +27%): se añaden más m² en particiones (14,65 → 36 m²).")
    out.append("- **Iluminación baja** (1.750 → 1.552, -11%): pequeño ajuste en perfilería LED.")
    out.append("- **Varios sube** (2.600 → 2.950, +13%): se añade la partida 14.1 'Plataforma elevadora' explícita.")
    out.append("- **Eléctrico, fontanería y clima**: prácticamente iguales. Cyss mantiene los importes subcontratados.")
    out.append("- **El total baja 1.760 €** (~3%): el movimiento principal es el reparto albañilería→pladur.")
    out.append("")
    out.append("**Acción recomendada**: aceptar la v2.0 como presupuesto de referencia (es la más reciente, está revisada). "
               "Cotejar las mediciones del cap. 01 (demolición) y cap. 03 (pladur) con los planos antes de firmar.")
    out.append("")
    (INF / "COMPARATIVA_CYSS.md").write_text("\n".join(out), encoding="utf-8")


# ==== HUECOS Y DUPLICIDADES ====

def informe_huecos() -> None:
    out = ["# Huecos y duplicidades", ""]
    out.append("_Generado el " + datetime.now().strftime("%Y-%m-%d") + "._")
    out.append("")
    out.append("## Oficios con un único PDF (legacy) y sin oferta de contratista real")
    out.append("")
    out.append("Estos oficios **no tienen oferta independiente** — están cubiertos dentro del presupuesto global de Cyss, "
               "pero conviene confirmarlo:")
    out.append("")
    out.append("| Oficio | PDF | Cubierto en Cyss v2.0 |")
    out.append("|---|---|---|")
    cub = {
        "Demolición": ("cap. 01 = 4.571,48 €",),
        "Pladur": ("cap. 03 = 10.448,45 €",),
        "Detalle baños": ("sub-capítulo dentro de cap. 02 y 03 (alicatados, sanitarios)",),
        "Encimeras": ("no incluido en Cyss — el cap. 02 menciona colocación de pavimentos pero no encimeras",),
    }
    for oficio, _ in [("Demolición", 0), ("Pladur", 0), ("Detalle baños", 0), ("Encimeras", 0)]:
        legacy = next((r for r in PRES if r["oficio"] == oficio and r.get("formato") == "desconocido"), None)
        if legacy:
            arch = legacy["archivo"].split("__", 1)[-1].replace(".txt", ".pdf")
            out.append(f"| {oficio} | {arch} | {cub[oficio][0]} |")
    out.append("")
    out.append("**Importante**: las encimeras (DEKTON Marmorio + SILESTONE Charcoal Soapstone, según `desconocido_Encimeras.pdf`) "
               "**no aparecen explícitamente en Cyss v2.0**. Hay que pedir presupuesto a un marmolista y/o confirmar si Cyss las incluye.")
    out.append("")
    out.append("## Duplicidades detectadas")
    out.append("")
    out.append("1. **Cyss v1 + Cyss v2.0**: dos versiones del presupuesto general. Conservadas ambas en `Contratista general/` "
               "(renombradas `Cyss_v1_*` y `Cyss_v2.0_*`). La v2.0 es la vigente.")
    out.append("2. **David Barat 1-000079 + 1-000022 DEF**: dos presupuestos de fontanería. El 1-000022 (DEF) es el consolidado "
               "que también incluye clima. El 1-079 es el inicial, ya superado.")
    out.append("3. **Toni 468 + Toni 472**: dos presupuestos de albañilería. El 468 es del 'PROYECTO SOFIA' (no es este proyecto). "
               "El 472 es el que aplica (REFORMA CALLE JOSE MARIA LERMA).")
    out.append("4. **Poveda borrador + Paracon**: dos presupuestos de electricidad. Poveda está caducado (validez 16-11-2025). "
               "Paracon es el vigente.")
    out.append("")
    out.append("## Partidas con '?' o importe abierto en PDFs de contratistas")
    out.append("")
    out.append("Toni 472 tiene **5 partidas sin cerrar** (marcadas con '?' en el PDF):")
    out.append("")
    out.append("- 1.13 Desmontaje de split")
    out.append("- 1.14 Desmontaje de split con recuperación")
    out.append("- 2.6 Faldcado de premarcos")
    out.append("- 2.7 Colocación de vierteaguas")
    out.append("- Notas adicionales sobre regatas, maestrado, contenedores — a confirmar.")
    out.append("")
    out.append("**Acción**: escribir a Toni para que cierre estos importes antes de comparar con Cyss.")
    out.append("")
    out.append("## Partidas en el Excel que no aparecen en Cyss v2.0")
    out.append("")
    out.append("Del cruce con `Presupuesto.xlsx`, hay columnas en el Excel que parecen totales alternativos:")
    out.append("")
    out.append("- Columna 1 de cifras: 22.055 / 3.900 / 3.360 / 4.535 / 6.177 / 8.386 / 22.433 (subtotal parcial: 70.846)")
    out.append("- Columna 2 de cifras: 22.135 / 9.583 / 3.965 / 5.005 / 7.962 / 8.386 / 22.433 (subtotal parcial: 79.469)")
    out.append("- Columna 4: 80 (albañilería), 'sin luz' (electricidad)")
    out.append("- Columna 7: 'Techos a 30' / 'Oscuros a 54' / 'Tabicas a 30' / 'Registro a 60' / 'Refuerzo a 25' — parecen notas del planificador, no importes.")
    out.append("")
    out.append("Los importes de la columna 1 **coinciden en algunos casos con Cyss v1** y en otros con presupuestos individuales "
               "(3.360 = David Barat 1-000079 sin IVA; 6.177 = David Barat 1-000084 sin IVA; 5.005 = Paracon base). "
               "El Excel parece ser una **hoja de trabajo de Sofia (la arquitecta)** que mezcla cifras de distintas fuentes. "
               "No es un presupuesto contractual.")
    out.append("")
    (INF / "HUECOS_Y_DUPLICIDADES.md").write_text("\n".join(out), encoding="utf-8")


# ==== CRUCE CON EXCEL ====

def informe_cruce_excel() -> None:
    out = ["# Cruce con Presupuesto.xlsx", ""]
    out.append("_Generado el " + datetime.now().strftime("%Y-%m-%d") + "._")
    out.append("")
    out.append("El Excel tiene una hoja (`Hoja1`) con 8 filas de oficios y dos columnas de importes. "
               "No es un presupuesto contractual — parece una **hoja de cálculo de planificación** "
               "(probablemente de la arquitecta Sofia Palacios).")
    out.append("")
    filas = EXCEL["hojas"]["Hoja1"]["filas"]
    out.append("## Contenido del Excel")
    out.append("")
    out.append("| Fila | A (oficio) | B (€) | C (€) | D | E (€) | G (nota) |")
    out.append("|---:|---|---:|---:|---|---:|---|")
    for i, f in enumerate(filas, 1):
        out.append(f"| {i} | {f[0] or '—'} | {f[1] if isinstance(f[1],(int,float)) else '—'} | "
                   f"{f[2] if isinstance(f[2],(int,float)) else '—'} | {f[3] or '—'} | "
                   f"{f[4] if isinstance(f[4],(int,float)) else '—'} | {f[6] or '—'} |")
    out.append("")
    out.append("## Comparación con los PDFs")
    out.append("")
    out.append("| Oficio | Col B (sin IVA) | Cyss v2.0 (sin IVA) | David Barat / Paracon (sin IVA) | Coincide con |")
    out.append("|---|---:|---:|---:|---|")
    out.append("| Albañilería | 22.055 | 13.880 | — | Toni 472 (17.725) — más cercano |")
    out.append("| Pladur | 3.900 | 10.448 | — | Ni Cyss ni oferta independiente. **Descuadre grande.** |")
    out.append("| Fontanería | 3.360 | 4.400 | 3.360 (David Barat 1-000079) | **David Barat 1-000079** |")
    out.append("| Electricidad | 4.535 | 7.129 | 5.005 (Paracon) | **Paracon** |")
    out.append("| Clima | 6.177 | 6.594 | 6.177 (David Barat 1-000084) | **David Barat 1-000084** |")
    out.append("| Carpintería ext | 8.386 | no en Cyss | 8.386 (Ventanas Nacher base) | **Ventanas Nacher** |")
    out.append("| Carpintería int | 22.433 | no en Cyss | 12.691+5.472+4.272 = 22.435 (Valenzuela) | **Valenzuela suma de 3 ppto** |")
    out.append("")
    out.append("**Conclusión**: la columna B del Excel es, **oficio a oficio, la suma de las ofertas individuales** "
               "(no de Cyss). Es decir, refleja la estrategia '**subcontratas directas sin contratista general**'.")
    out.append("")
    out.append("La columna C (22.135 / 9.583 / 3.965 / 5.005 / 7.962 / 8.386 / 22.433) es un **escenario alternativo** "
               "que en algunos oficios coincide con Paracon (5.005), en otros con David Barat 1-000084 (7.962), y en otros "
               "con las ofertas individuales actualizadas a marzo 2026.")
    out.append("")
    out.append("**Decisión implícita en el Excel**: el cliente está valorando **no usar Cyss como contratista general** "
               "y gestionar las subcontratas directamente. La diferencia económica, según el Excel, es 79.469 - 70.846 = "
               "**8.623 €** a favor de la gestión directa (~12% de ahorro).")
    out.append("")
    out.append("**Riesgo**: gestionar 7 subcontratas directamente implica más carga de coordinación, más riesgo de "
               "solapamientos, y necesitas a alguien con función de 'dirección facultativa' para resolver conflictos. "
               "Cyss probablemente ofrece esa coordinación por los 8.623 € de diferencia.")
    out.append("")
    (INF / "CRUCE_CON_EXCEL.md").write_text("\n".join(out), encoding="utf-8")


# ==== ANÁLISIS DE PLANOS ====

def informe_planos() -> None:
    out = ["# Análisis de planos", ""]
    out.append("_Generado el " + datetime.now().strftime("%Y-%m-%d") + "._")
    out.append("")
    out.append("Hay dos planos en `Planos/`:")
    out.append("- `estado inicial.pdf` — plano PEA.01, fecha Junio25, escala 1:50 (A3). Estado original de la vivienda.")
    out.append("- `distribución.pdf` — plano PEA.02, fecha Junio25, escala 1:50 (A3). Distribución propuesta.")
    out.append("")
    out.append("## Lo que se ve en el texto extraído")
    out.append("")
    out.append("### Estado inicial")
    out.append("")
    inicial = (DATA / "texto" / "Planos__estado inicial.txt").read_text(encoding="utf-8")
    out.append("Estancias con superficies detectadas:")
    out.append("")
    for m in __import__("re").finditer(r"(\d{1,3},\d)\s*m2", inicial):
        out.append(f"- {m.group(1)} m²")
    out.append("")
    out.append("### Distribución propuesta")
    out.append("")
    dist = (DATA / "texto" / "Planos__distribución.txt").read_text(encoding="utf-8")
    out.append("El PDF de distribución tiene menos texto (es esencialmente gráfico). Lo que se puede leer es la cabecera del plano.")
    out.append("")
    out.append("## Implicaciones para los presupuestos")
    out.append("")
    out.append("- **88,3 m² de pavimento porcelánico** en Cyss v2.0 (cap. 02) = vivienda completa, "
               "coherente con la superficie del estado inicial.")
    out.append("- **92,2 m² de techos** en Cyss v2.0 (cap. 02, pintura) = ligeramente inferior a la suma de m² "
               "de estancias, pero consistente con que algunos techos son de pladur (cap. 03).")
    out.append("- **Pladur**: 93,4 m² de falso techo en cap. 03 — implica que la práctica totalidad de la vivienda "
               "va con falso techo nuevo.")
    out.append("- **El climaconvector** cubre 90 m² aprox. según la ficha del equipo Mitsubishi MGPEZ-71. "
               "Casa de unos 90 m² habitables, coherente con el plano.")
    out.append("")
    out.append("## Planos específicos por oficio (legacy)")
    out.append("")
    out.append("Hay además 4 planos temáticos en otras carpetas que son **planos de proyecto** (no presupuestos), "
               "todos con código PEI.0X y fecha Junio25:")
    out.append("")
    out.append("| Carpeta | Archivo | Plano | Tema |")
    out.append("|---|---|---|---|")
    out.append("| Albañilería | desconocido_Albañilería.pdf | PEI.01 | Albañilería (pavimento, fachada, alicatados) |")
    out.append("| Demolición | desconocido_Demolición.pdf | PEI.00 | Demolición (tabiques, fachada, pavimentos) |")
    out.append("| Carpintería exterior | desconocido_Carpintería exterior.pdf | PEI.05/06 | Carpintería ext (con cuadro de ventanas V01-V08) |")
    out.append("| Carpintería interior | desconocido_Carpintería interior.pdf | PEI.07 | Mobiliario de cocina, armarios, puertas, muebles baño |")
    out.append("| Detalle baños | desconocido_Detalle baños.pdf | PEA.04 | Alzados baños |")
    out.append("| Electricidad | desconocido_Electricidad.pdf | PEI.03 | Electricidad e iluminación |")
    out.append("| Encimeras | desconocido_Encimeras.pdf | PEI.09 | Encimeras cocina y lavadero |")
    out.append("| Fontanería | desconocido_Fontanería.pdf | PEI.04 | Fontanería y saneamiento |")
    out.append("| Pladur | desconocido_Pladur.pdf | PEI.01 | Pladur (tabiques, trasdosados) |")
    out.append("")
    out.append("Estos planos son la **fuente de mediciones** de Cyss. Sin ellos no se puede auditar si las "
               "cantidades (m² de demolición, ml de partición, etc.) están bien tomadas.")
    out.append("")
    (INF / "ANALISIS_PLANOS.md").write_text("\n".join(out), encoding="utf-8")


# ==== RESUMEN EJECUTIVO ====

def informe_resumen() -> None:
    out = ["# Resumen ejecutivo", ""]
    out.append("_Generado el " + datetime.now().strftime("%Y-%m-%d") + "._")
    out.append("")
    out.append("**Cliente**: José María Mortés Lerma · **Ubicación**: C/ José María Mortes Lerma 2, 7º PTA 28, 46018 Valencia")
    out.append("")
    out.append("## Cifras clave")
    out.append("")
    # Cyss v2.0 es la referencia
    v2 = next((r for r in PRES if r["archivo"] == "Contratista general__Cyss_v2.0_resumen.txt"), None)
    if v2:
        out.append(f"- **Cyss v2.0 (contratista general, 04-06-2026)**: **{fmt_eur(v2['total_con_iva'])}** (base {fmt_eur(v2.get('total_ejecucion_material'))} + IVA 10%)")
    # Suma de subcontratas
    subcontratas = []
    for r in PRES:
        if r.get("formato") in ("desconocido",): continue
        if "Contratista general" in r.get("oficio", ""): continue
        if r.get("archivo", "").endswith("_myp.txt"): continue
        if "PROYECTO SOFIA" in r["archivo"]: continue  # el de Sofia
        t = r.get("total_con_iva") or r.get("total_calculado_con_iva")
        if t:
            subcontratas.append((r["oficio"], r.get("contratista", "?"), t, r.get("fecha")))
    total_sub = sum(t for _, _, t, _ in subcontratas)
    out.append(f"- **Suma de subcontratas independientes**: **{fmt_eur(total_sub)}** (ver tabla más abajo)")
    excel = json.loads((DATA / "excel.json").read_text(encoding="utf-8"))
    out.append(f"- **Hoja Excel de planificación**: 70.846 € (sumando col. B) — equivale a subcontratas; "
               f"79.469 € (col. C) — escenario alternativo")
    out.append("")
    out.append("## Por oficio (referencia: Cyss v2.0)")
    out.append("")
    out.append("| Capítulo | Importe (sin IVA) | % |")
    out.append("|---|---:|---:|")
    for c in v2.get("capitulos", []):
        out.append(f"| {c['capitulo']} {c['nombre']} | {fmt_eur(c['euros'])} | {c['porcentaje']:.2f}% |")
    out.append(f"| **TOTAL** | **{fmt_eur(v2.get('total_ejecucion_material'))}** | 100% |")
    out.append("")
    out.append("## Estado de las decisiones por oficio")
    out.append("")
    out.append("| Oficio | # ofertas | Recomendación | Pendiente |")
    out.append("|---|---:|---|---|")
    out.append("| Albañilería | 2 (Toni 472 + Cyss) | Validar el desglose de Toni contra Cyss | Toni tiene 5 partidas con '?' |")
    out.append("| Carpintería ext | 1 (Ventanas Nacher) | OK si se acepta el alcance | Plataforma elevadora a determinar |")
    out.append("| Carpintería int | 3 (Valenzuela) | Aceptar las 3 ofertas (8 semanas de plazo) | — |")
    out.append("| Clima | 1 (David Barat 1-000084) | Cubierto por David Barat; Cyss lo subcontrata al mismo | OK |")
    out.append("| Electricidad | 2 (Paracon + Poveda) | **Paracon** (más reciente, más barato, financia en 4 hitos) | Confirmar si incluye videoportero y red de datos |")
    out.append("| Fontanería | 1 (David Barat 1-000079 inicial) | Cubierto por David Barat; Cyss lo subcontrata | OK; o pedir oferta desglosada solo-fontanería |")
    out.append("| Demolición | 0 (legacy) | Incluido en Cyss cap. 01 | OK |")
    out.append("| Pladur | 0 (legacy) | Incluido en Cyss cap. 03 (gran subida en v2.0) | Revisar mediciones |")
    out.append("| Encimeras | 0 (legacy) | **No en Cyss v2.0** | Pedir oferta a marmolista |")
    out.append("| Detalle baños | 0 (legacy) | Cubierto por Cyss + Valenzuela | OK |")
    out.append("")
    out.append("## Top 3 acciones inmediatas")
    out.append("")
    out.append("1. **Pedir a Toni que cierre las 5 partidas con '?'** en el presupuesto 472 (sin esto no se puede comparar).")
    out.append("2. **Pedir oferta de encimeras** (DEKTON + SILESTONE) — no está en Cyss y puede ser 2.000–4.000 € adicional.")
    out.append("3. **Decidir entre Paracon o Poveda para electricidad** — recomendación: Paracon (más barato, más reciente, financia).")
    out.append("")
    out.append("## Ver también")
    out.append("")
    out.append("- `COMPARATIVA_ALBAÑILERIA.md`")
    out.append("- `COMPARATIVA_FONTANERIA.md`")
    out.append("- `COMPARATIVA_ELECTRICIDAD.md`")
    out.append("- `COMPARATIVA_CYSS.md`")
    out.append("- `HUECOS_Y_DUPLICIDADES.md`")
    out.append("- `CRUCE_CON_EXCEL.md`")
    out.append("- `ANALISIS_PLANOS.md`")
    out.append("- `AUDITORIA_PDFS.md`")
    out.append("")
    (INF / "RESUMEN_EJECUTIVO.md").write_text("\n".join(out), encoding="utf-8")


# ==== MAIN ====

def main() -> None:
    informe_albanileria()
    print("OK COMPARATIVA_ALBAÑILERIA.md")
    informe_fontaneria()
    print("OK COMPARATIVA_FONTANERIA.md")
    informe_electricidad()
    print("OK COMPARATIVA_ELECTRICIDAD.md")
    informe_cyss()
    print("OK COMPARATIVA_CYSS.md")
    informe_huecos()
    print("OK HUECOS_Y_DUPLICIDADES.md")
    informe_cruce_excel()
    print("OK CRUCE_CON_EXCEL.md")
    informe_planos()
    print("OK ANALISIS_PLANOS.md")
    informe_resumen()
    print("OK RESUMEN_EJECUTIVO.md")


if __name__ == "__main__":
    main()
