#!/usr/bin/env python3
"""
Extrae las ventanas V01-V08 (medidas, antepecho, tipología y mapeo a huecos
del plano) de "Carpintería exterior/desconocido_Carpintería exterior.pdf"
y calcula el norte del plano de "Planos/distribución.pdf".

El PDF de carpintería tiene 2 páginas vectoriales a rotación 270:
  - página 0 (índice 0): PEI.05, planta 1:50 con las etiquetas V01..V08.
  - página 1 (índice 1): PEI.06, alzados 1:30 acotados + cuadro de tipologías.

Método:
  1. Etiquetas V0x: page.get_text("words") transformado con rotation_matrix.
  2. Alzados (pág. 1): los triángulos de flecha de las cotas (relleno beige)
     se reducen a su punta; agrupando puntas colineales se reconstruyen las
     cadenas de cota y sus luces (ancho, alto, antepecho). Se cruzan con los
     textos de cota (en metros, p.ej. "2,98" = 2,98 m) y la cota manda.
  3. Huecos de fachada (pág. 0): la planta se rasteriza con get_pixmap y se
     mide la luz entre muros (relleno gris 209). V03/V04 son ventanas de
     esquina dibujadas con líneas finas -> se miden sus dobles líneas.
  4. Mapeo a data/planos3d.json: huecos entre muros del modelo y muros
     tipo=="vidrio" próximos a cada hueco.
  5. Norte: aguja del símbolo del cajetín de distribución.pdf. Cross-check
     con la calle de OSM (way 23549990 y 622510153) anotado en el JSON.

Reproducible: /tmp/opencode/venv/bin/python scripts/extraer_ventanas.py
Requiere: pymupdf
"""
from __future__ import annotations

import json
import math
import re
from datetime import date
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "Carpintería exterior" / "desconocido_Carpintería exterior.pdf"
PLAN = ROOT / "Planos" / "distribución.pdf"
PLANOS3D = ROOT / "data" / "planos3d.json"
OUT = ROOT / "data" / "ventanas.json"

PT_PER_M_50 = 20.0 / 25.4 * 72.0              # 1:50 -> 56,6929 pt/m
PT_PER_M_30 = (1000.0 / 30.0) / 25.4 * 72.0   # 1:30 -> 94,4882 pt/m

GRAY = 209                                     # relleno de muros (0,8196*255)
BEIGE = (0.5803899765014648, 0.5450999736785889, 0.4431400001049042)
VIDS = [f"V{i:02d}" for i in range(1, 9)]

# Tokens del cuadro PEI.06 con el encoding interno de la fuente (desfase +0x1D)
MOJIBAKE = {
    "3HUVLDQD": "Persiana",
    "PHFDQLVPR": "mecanismo",
    "HOpFWULFR": "eléctrico",
    "&ULVWDO": "Cristal",
    "WUDQVO~FLGR": "traslúcido",
}


def vis_point(page, x, y):
    p = pymupdf.Point(x, y) * page.rotation_matrix
    return (p.x, p.y)


def labels(page):
    """V0x -> (x, y) en coordenadas visuales (rotación aplicada)."""
    out = {}
    for w in page.get_text("words"):
        t = w[4].strip()
        if re.fullmatch(r"V0[1-8]", t):
            out[t] = vis_point(page, (w[0] + w[2]) / 2, (w[1] + w[3]) / 2)
    return out


def numeric_words(page):
    out = []
    for w in page.get_text("words"):
        t = w[4].strip().replace(".", ",")
        if re.fullmatch(r"\d+(,\d+)?", t):
            x, y = vis_point(page, (w[0] + w[2]) / 2, (w[1] + w[3]) / 2)
            out.append((float(t.replace(",", ".")), x, y))
    return out


def near_num(words, x, y, dx=60, dy=30):
    cands = [w for w in words if abs(w[1] - x) <= dx and abs(w[2] - y) <= dy]
    if not cands:
        return None
    return min(cands, key=lambda w: (w[1] - x) ** 2 + (w[2] - y) ** 2)[0]


def match_cota(words, wanted, region, ref_x, ref_y, tol=0.045):
    """Cota de texto con el valor medido dentro de la región del alzado."""
    x0, y0, x1, y1 = region
    cands = [w for w in words
             if abs(w[0] - wanted) <= tol and x0 <= w[1] <= x1 and y0 <= w[2] <= y1]
    if not cands:
        return None
    return min(cands, key=lambda w: (abs(w[0] - wanted),
                                     (w[1] - ref_x) ** 2 + (w[2] - ref_y) ** 2))[0]


# ── alzados (página 1, 1:30) ────────────────────────────────────────────────

def arrow_tips(page):
    """Puntas de los triángulos de flecha (relleno beige) de las cotas."""
    tips = []
    M = page.rotation_matrix
    for d in page.get_drawings():
        f = d.get("fill")
        if not f or not all(abs(a - b) < 0.02 for a, b in zip(f, BEIGE)):
            continue
        pts = []
        for it in d["items"]:
            if it[0] == "l":
                for p in (it[1], it[2]):
                    q = p * M
                    if not any(abs(q.x - u) < 0.1 and abs(q.y - v) < 0.1 for u, v in pts):
                        pts.append((q.x, q.y))
        if len(pts) != 3:
            continue
        ds = sorted((math.dist(pts[i], pts[j]), i, j)
                    for i in range(3) for j in range(i + 1, 3))
        _, i, j = ds[0]
        k = ({0, 1, 2} - {i, j}).pop()
        tips.append(pts[k])
    return tips


def dim_groups(page, tips):
    """Cadenas de cota: cada línea larga del dibujo une dos puntas de flecha."""
    M = page.rotation_matrix
    groups = []
    seen = set()

    def nearest_tip(p):
        best = None
        for t in tips:
            d = math.hypot(t[0] - p.x, t[1] - p.y)
            if d <= 8 and (best is None or d < best[0]):
                best = (d, t)
        return best and best[1]

    for d in page.get_drawings():
        for it in d["items"]:
            if it[0] != "l":
                continue
            a, b = it[1] * M, it[2] * M
            horiz = abs(a.y - b.y) <= 0.5 and abs(a.x - b.x) > 25
            vert = abs(a.x - b.x) <= 0.5 and abs(a.y - b.y) > 25
            if not (horiz or vert):
                continue
            t1, t2 = nearest_tip(a), nearest_tip(b)
            if not t1 or not t2 or t1 is t2:
                continue
            orient = "h" if horiz else "v"
            idx = 1 if horiz else 0
            if abs(t1[idx] - t2[idx]) > 8:
                continue
            lo = min(t1[1 - idx], t2[1 - idx])
            hi = max(t1[1 - idx], t2[1 - idx])
            coord = (t1[idx] + t2[idx]) / 2
            key = (orient, round(lo, 1), round(hi, 1), round(coord, 1))
            if key in seen:
                continue
            seen.add(key)
            groups.append({"orient": orient, "span": hi - lo, "coord": coord,
                           "lo": lo, "hi": hi})
    return groups


def seg_components(page):
    """Componentes conexas de los trazos (para situar cada alzado)."""
    M = page.rotation_matrix
    segs = []
    for d in page.get_drawings():
        for it in d["items"]:
            if it[0] == "l":
                a, b = it[1] * M, it[2] * M
                segs.append((a.x, a.y, b.x, b.y))
            elif it[0] == "re":
                r = it[1]
                pts = [pymupdf.Point(r.x0, r.y0) * M, pymupdf.Point(r.x1, r.y0) * M,
                       pymupdf.Point(r.x1, r.y1) * M, pymupdf.Point(r.x0, r.y1) * M]
                for k in range(4):
                    a, b = pts[k], pts[(k + 1) % 4]
                    segs.append((a.x, a.y, b.x, b.y))
    par = list(range(len(segs)))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb

    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            a, b = segs[i], segs[j]
            d = min(math.hypot(a[p] - b[q], a[p + 1] - b[q + 1])
                    for p in (0, 2) for q in (0, 2))
            if d <= 0.75:
                union(i, j)
    comps = {}
    for i in range(len(segs)):
        comps.setdefault(find(i), []).append(segs[i])
    out = []
    for ids in comps.values():
        xs = [v for s in ids for v in (s[0], s[2])]
        ys = [v for s in ids for v in (s[1], s[3])]
        out.append({"x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys)})
    return out


def measure_elevations(page, lab, words):
    tips = arrow_tips(page)
    groups = dim_groups(page, tips)
    comps = seg_components(page)
    out = {}
    for vid, (lx, ly) in lab.items():
        near = []
        for c in comps:
            if (c["y0"] + c["y1"]) / 2 >= ly:
                continue
            dx = max(c["x0"] - lx, 0.0, lx - c["x1"])
            if dx <= 60 and (c["y0"] + c["y1"]) / 2 > ly - 320:
                near.append((dx, c))
        if not near:
            continue
        comp = max(near, key=lambda t: (t[1]["x1"] - t[1]["x0"]) * (t[1]["y1"] - t[1]["y0"]))[1]
        hs = [g for g in groups if g["orient"] == "h"
              and comp["y0"] - 60 <= g["coord"] <= comp["y0"] + 5
              and comp["x0"] - 20 <= (g["lo"] + g["hi"]) / 2 <= comp["x1"] + 20]
        vs = [g for g in groups if g["orient"] == "v"
              and comp["x1"] - 15 <= g["coord"] <= comp["x1"] + 70]
        res = {"medido": {}, "cota": {},
               "bbox": [round(comp[k], 1) for k in ("x0", "y0", "x1", "y1")]}
        region = (comp["x0"] - 260, comp["y0"] - 60, comp["x1"] + 260, comp["y1"] + 200)
        if hs:
            g = max(hs, key=lambda g: g["span"])
            w = g["span"] / PT_PER_M_30
            res["medido"]["ancho_m"] = round(w, 3)
            c = near_num(words, (g["lo"] + g["hi"]) / 2, g["coord"], dx=80, dy=25)
            if c is None or abs(c - w) > 0.08:
                c = match_cota(words, w, region, (g["lo"] + g["hi"]) / 2, g["coord"])
            if c and abs(c - w) < 0.08:
                res["cota"]["ancho_m"] = c
        if vs:
            coord = max({round(g["coord"], 1) for g in vs},
                        key=lambda c: len([t for t in tips
                                           if abs(t[0] - c) <= 8
                                           and comp["y0"] - 40 <= t[1] <= comp["y1"] + 140]))
            ys = sorted({round(t[1], 1) for t in tips
                         if abs(t[0] - coord) <= 8
                         and comp["y0"] - 40 <= t[1] <= comp["y1"] + 140})
            uniq = []
            for y in ys:
                if not uniq or y - uniq[-1] > 6:
                    uniq.append(y)
            res["alturas_pt"] = uniq
            if len(uniq) == 2:
                alto = (uniq[1] - uniq[0]) / PT_PER_M_30
                res["medido"]["alto_m"] = round(alto, 3)
                c = match_cota(words, alto, region, coord, (uniq[0] + uniq[1]) / 2)
                if c and abs(c - alto) < 0.08:
                    res["cota"]["alto_m"] = c
            elif len(uniq) >= 3:
                alto = (uniq[-2] - uniq[0]) / PT_PER_M_30
                res["medido"]["alto_m"] = round(alto, 3)
                c = match_cota(words, alto, region, coord, (uniq[0] + uniq[-2]) / 2)
                if c and abs(c - alto) < 0.08:
                    res["cota"]["alto_m"] = c
                ant = (uniq[-1] - uniq[-2]) / PT_PER_M_30
                res["medido"]["antepecho_m"] = round(ant, 3)
                c = match_cota(words, ant, region, coord, (uniq[-2] + uniq[-1]) / 2)
                if c and abs(c - ant) < 0.08:
                    res["cota"]["antepecho_m"] = c
        out[vid] = res
    return out


# ── planta (página 0, 1:50) ─────────────────────────────────────────────────

def p0_wall_center(page):
    """Centro (vis) del bbox de muros grises; base del paso a coords de modelo."""
    M = page.rotation_matrix
    xs, ys = [], []
    for d in page.get_drawings():
        f = d.get("fill")
        if not f or not all(abs(a - b) < 0.005
                            for a, b in zip(f, (0.81961, 0.81961, 0.81961))):
            continue
        for it in d["items"]:
            pts = []
            if it[0] == "l":
                pts = [it[1], it[2]]
            elif it[0] == "re":
                r = it[1]
                pts = [pymupdf.Point(r.x0, r.y0), pymupdf.Point(r.x1, r.y1)]
            elif it[0] == "qu":
                q = it[1]
                pts = [q.ul, q.ur, q.lr, q.ll]
            for p in pts:
                q = p * M
                xs.append(q.x)
                ys.append(q.y)
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


class Raster:
    """Planta rasterizada con acceso rápido al gris de muro (209,209,209)."""

    def __init__(self, page, zoom=3.0):
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        self.s = pix.samples
        self.n = pix.n
        self.stride = pix.stride
        self.w = pix.width
        self.h = pix.height
        self.Z = zoom
        self.pat = bytes([GRAY, GRAY, GRAY])

    def px(self, v):
        return int(round(v * self.Z))

    def row_gray(self, y_pt, x0_pt, x1_pt):
        r = self.px(y_pt)
        if r < 0 or r >= self.h:
            return 0
        c0, c1 = max(0, self.px(x0_pt)), min(self.w, self.px(x1_pt))
        if c1 <= c0:
            return 0
        row = self.s[r * self.stride + c0 * self.n: r * self.stride + c1 * self.n]
        return row.count(self.pat) / self.Z

    def col_gray(self, x_pt, y0_pt, y1_pt):
        return sum(1 for _ in self.col_bytes(x_pt, y0_pt, y1_pt) if _) / self.Z

    def col_bytes(self, x_pt, y0_pt, y1_pt):
        c = self.px(x_pt)
        r0, r1 = max(0, self.px(y0_pt)), min(self.h, self.px(y1_pt))
        s = self.s
        stride, n = self.stride, self.n
        return bytes(1 if s[r * stride + c * n:r * stride + c * n + 3] == self.pat else 0
                     for r in range(r0, r1))

    def row_longest(self, y_pt, x0_pt, x1_pt):
        r = self.px(y_pt)
        c0, c1 = max(0, self.px(x0_pt)), min(self.w, self.px(x1_pt))
        if r < 0 or r >= self.h or c1 <= c0:
            return 0.0
        row = self.s[r * self.stride + c0 * self.n: r * self.stride + c1 * self.n]
        runs = [len(m.group()) // 3 for m in re.finditer(rb"(?:\xd1\xd1\xd1)+", row)]
        return (max(runs) if runs else 0) / self.Z

    def col_longest(self, x_pt, y0_pt, y1_pt):
        col = self.col_bytes(x_pt, y0_pt, y1_pt)
        runs = [len(m.group()) for m in re.finditer(rb"\x01{3,}", col)]
        return (max(runs) if runs else 0) / self.Z


def find_bands(plt, lx, ly, horiz):
    """Bandas de muro (gris con tirada continua) cercanas a la etiqueta."""
    hits = []
    t = 1.0
    while t <= 150.0:
        for coord in (ly - t, ly + t) if horiz else (lx - t, lx + t):
            if horiz:
                total = plt.row_gray(coord, lx - 140, lx + 140)
                run = plt.row_longest(coord, lx - 140, lx + 140)
            else:
                total = plt.col_gray(coord, ly - 140, ly + 140)
                run = plt.col_longest(coord, ly - 140, ly + 140)
            if total >= 30 and run >= 40:
                hits.append(coord)
        t += 1.0
    if not hits:
        return []
    hits.sort()
    bands = []
    for c in hits:
        if bands and c - bands[-1][-1] <= 2.0:
            bands[-1].append(c)
        else:
            bands.append([c])
    ref = ly if horiz else lx
    out = []
    for b in bands:
        if b[-1] - b[0] >= 2.0:
            center = (b[0] + b[-1]) / 2
            out.append((center, b[-1] - b[0]))
    out.sort(key=lambda bc: abs(bc[0] - ref))
    return out


def find_opening(plt, lx, ly, cota):
    """Prueba fachada horizontal (N/S) y vertical (E/O); devuelve la más afín."""
    candidates = []
    for horiz in (True, False):
        for center, thickness in find_bands(plt, lx, ly, horiz)[:3]:
            runs = []
            start = None
            x = -170.0
            while x <= 170.0:
                if horiz:
                    cov = plt.col_gray(lx + x, center - 8, center + 8)
                else:
                    cov = plt.row_gray(ly + x, center - 8, center + 8)
                is_wall = cov >= 1.5
                if not is_wall and start is None:
                    start = x
                if is_wall and start is not None:
                    runs.append((start, x))
                    start = None
                x += 0.5
            runs = [r for r in runs if r[0] > -169.5 and r[1] < 169.5]
            if not runs:
                continue
            with_label = [r for r in runs if r[0] <= 0.0 <= r[1]]
            if with_label:
                run = min(with_label, key=lambda r: r[1] - r[0])
            else:
                run = min(runs, key=lambda r: min(abs(r[0]), abs(r[1])))
            base = lx if horiz else ly
            len_m = (run[1] - run[0]) / PT_PER_M_50
            candidates.append({"orient": "h" if horiz else "v",
                               "center": center, "lo": base + run[0],
                               "hi": base + run[1], "len_pt": run[1] - run[0],
                               "len_m": len_m, "band_thickness": thickness,
                               "contiene_etiqueta": bool(with_label)})
    if not candidates:
        return None
    candidates.sort(key=lambda r: (abs(r["len_m"] - cota),
                                   0 if r["contiene_etiqueta"] else 1,
                                   abs(r["center"] - (ly if r["orient"] == "h" else lx))))
    return candidates[0]


def opening_from_frame_lines(page, lx, ly, cota):
    """Alternativa vectorial para V03/V04 (dobles líneas de la carpintería)."""
    M = page.rotation_matrix
    vert, horiz = [], []
    for d in page.get_drawings():
        for it in d["items"]:
            if it[0] != "l":
                continue
            a, b = it[1] * M, it[2] * M
            if abs(a.x - b.x) < 0.5 and abs(a.y - b.y) > 10:
                if abs(a.x - lx) < 70 and min(a.y, b.y) - 20 < ly < max(a.y, b.y) + 20:
                    vert.append((a.x, min(a.y, b.y), max(a.y, b.y)))
            if abs(a.y - b.y) < 0.5 and abs(a.x - b.x) > 10:
                if abs(a.y - ly) < 70 and min(a.x, b.x) - 20 < lx < max(a.x, b.x) + 20:
                    horiz.append((a.y, min(a.x, b.x), max(a.x, b.x)))
    best_all = None
    for lines, orient in ((horiz, "h"), (vert, "v")):
        if len(lines) < 2:
            continue
        best = None
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                off = abs(lines[i][0] - lines[j][0])
                if off > 8:
                    continue
                lo = min(lines[i][1], lines[j][1])
                hi = max(lines[i][2], lines[j][2])
                span = (hi - lo) / PT_PER_M_50
                key = (off, abs(span - cota))
                if best is None or key < best[0]:
                    best = (key, lines[i][0], lines[j][0], lo, hi, span)
        if best and abs(best[5] - cota) < 0.35:
            cand = {"orient": orient, "center": (best[1] + best[2]) / 2,
                    "lo": best[3], "hi": best[4], "len_pt": best[4] - best[3],
                    "len_m": best[5], "metodo": "lineas_marco"}
            if best_all is None or abs(cand["len_m"] - cota) < abs(best_all["len_m"] - cota):
                best_all = cand
    return best_all


# ── planos3d.json ───────────────────────────────────────────────────────────

def bbox(m):
    xs = [p[0] for p in m["pts"]]
    zs = [p[1] for p in m["pts"]]
    return min(xs), min(zs), max(xs), max(zs)


def model_gaps(muros):
    """Huecos entre muros de planos3d.json agrupados por fachada."""
    bands = [
        ("este", "v", 7.6, 8.4, -3.2, 3.7, 8.0),
        ("sur-dormitorios", "h", 2.75, 3.25, -6.76, -1.0, 3.0),
        ("sur-galera", "h", 2.30, 2.70, -2.0, 1.0, 2.5),
        ("sur-bay", "h", 4.20, 4.60, -1.2, 2.0, 4.4),
        ("norte", "h", -3.60, -3.10, -8.3, 8.3, -3.35),
    ]
    gaps = []
    for name, axis, b0, b1, e0, e1, transv in bands:
        covered = []
        for m in muros:
            x0, z0, x1, z1 = bbox(m)
            if axis == "v":
                if not (b0 <= (x0 + x1) / 2 <= b1 and (x1 - x0) < 0.6):
                    continue
                a, b = z0, z1
            else:
                if not (b0 <= (z0 + z1) / 2 <= b1 and (z1 - z0) < 0.6):
                    continue
                a, b = x0, x1
            if b - a >= 0.05:
                covered.append((a, b))
        if not covered:
            continue
        covered.sort()
        merged = []
        for a, b in covered:
            if merged and a <= merged[-1][1] + 0.02:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        cursor = e0
        for a, b in merged:
            if a - cursor > 0.4:
                mid = (cursor + a) / 2
                centro = ([round(mid, 2), transv] if axis == "h"
                          else [transv, round(mid, 2)])
                gaps.append({"fachada": name, "orientacion": axis, "centro": centro,
                             "longitud_m": round(a - cursor, 2)})
            cursor = max(cursor, b)
    return gaps


def cluster_vidrio(muros):
    """Agrupa muros tipo=='vidrio' contiguos (tiras finas, no huecos)."""
    idx = [i for i, m in enumerate(muros) if m["tipo"] == "vidrio"]
    comps = []
    for i in idx:
        xi = bbox(muros[i])
        placed = False
        for c in comps:
            if not placed and (min(xi[2], c["bbox"][2]) + 0.1 >= max(xi[0], c["bbox"][0]) - 0.4
                               and min(xi[3], c["bbox"][3]) + 0.1 >= max(xi[1], c["bbox"][1]) - 0.4):
                c["idx"].append(i)
                c["bbox"] = [min(c["bbox"][k], xi[k]) for k in range(4)]
                placed = True
        if not placed:
            comps.append({"idx": [i], "bbox": list(xi)})
    out = []
    for c in comps:
        x0, z0, x1, z1 = c["bbox"]
        horiz = (x1 - x0) >= (z1 - z0)
        out.append({"indices": c["idx"],
                    "centro": [round((x0 + x1) / 2, 2), round((z0 + z1) / 2, 2)],
                    "longitud_m": round((x1 - x0) if horiz else (z1 - z0), 2),
                    "orientacion": "horizontal" if horiz else "vertical",
                    "espesor_m": muros[c["idx"][0]]["t"]})
    return out


# ── norte ───────────────────────────────────────────────────────────────────

def north_angle(page):
    M = page.rotation_matrix
    circle, needle = None, None
    for d in page.get_drawings():
        kinds = [it[0] for it in d["items"]]
        pts = []
        for it in d["items"]:
            if it[0] == "l":
                pts += [it[1] * M, it[2] * M]
            elif it[0] == "c":
                pts += [it[k] * M for k in (1, 2, 3, 4)]
        if not pts:
            continue
        xs = [q.x for q in pts]
        ys = [q.y for q in pts]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if x0 < 1000 or y0 < 700:
            continue
        if kinds == ["c", "c", "c", "c"] and (x1 - x0) > 20:
            circle = (x0, y0, x1, y1)
        if kinds == ["l"] and len(pts) == 2 and 6 < math.hypot(x1 - x0, y1 - y0) < 25:
            needle = ((pts[0].x, pts[0].y), (pts[1].x, pts[1].y))
    if not circle or not needle:
        return None
    cx, cy = (circle[0] + circle[2]) / 2, (circle[1] + circle[3]) / 2
    a, b = needle
    tip = a if math.hypot(a[0] - cx, a[1] - cy) > math.hypot(b[0] - cx, b[1] - cy) else b
    base = b if tip is a else a
    ang = math.degrees(math.atan2(-(tip[1] - base[1]), tip[0] - base[0])) % 360
    return ang, tip, (round(cx, 1), round(cy, 1))


# ── notas ───────────────────────────────────────────────────────────────────

def elev_note(vid, e):
    bits = []
    med, cot = e.get("medido", {}), e.get("cota", {})
    if med:
        bits.append("geometría alzado 1:30: "
                    + ", ".join(f"{k}={v}" for k, v in med.items()))
    if cot:
        bits.append("cotas de texto en metros: "
                    + ", ".join(f"{k}={v}" for k, v in cot.items()))
    if vid in ("V06", "V07", "V08"):
        bits.append("quitamiedos a 1,10 m del suelo; el alféizar queda a 0,89 m")
    if vid == "V05":
        bits.append("puerta-galería de altura completa; sin antepecho acotado")
    if vid == "V01":
        bits.append("sin cota de antepecho (arranque no acotado)")
    return ". ".join(bits)


def gap_note(vid, op, ancho, matched):
    txt = (f"Luz medida en planta 1:50 ({op['metodo']}): {op['len_m']:.2f} m "
           f"vs cota de alzado {ancho:.2f} m.")
    if matched:
        txt += f" Coincide con hueco vectorial de planos3d ({matched['fachada']})."
    else:
        txt += " No hay hueco vectorial equivalente en planos3d.json."
    if vid in ("V03", "V04"):
        txt += (" Ventana de esquina (esquinero 90°): el hueco se dibuja con líneas "
                "finas, centro/longitud aproximados.")
    if vid == "V08":
        txt += (" planos3d no abre hueco en el muro norte (el muro se extrae continuo); "
                "la planta dibuja ~0,97 m frente a 1,17 m de cota.")
    return txt


# ── principal ───────────────────────────────────────────────────────────────

def main() -> int:
    doc = pymupdf.open(PDF)
    plan = pymupdf.open(PLAN)
    if len(doc) < 2:
        raise SystemExit("El PDF de carpintería debería tener 2 páginas")
    p0, p1 = doc[0], doc[1]

    lab_plan = labels(p0)
    lab_alz = labels(p1)
    words1 = numeric_words(p1)
    elevations = measure_elevations(p1, lab_alz, words1)

    p3d = json.loads(PLANOS3D.read_text(encoding="utf-8"))
    bounds = p3d["bounds"]
    muros = p3d["muros"]
    gaps = model_gaps(muros)
    vidrios = cluster_vidrio(muros)

    # tipologías y color del cuadro PEI.06
    schedule = {}
    for vid, (lx, ly) in lab_alz.items():
        rows = {}
        for w in p1.get_text("words"):
            t = w[4].strip()
            x, y = vis_point(p1, (w[0] + w[2]) / 2, (w[1] + w[3]) / 2)
            if ly - 2 <= y <= ly + 46 and lx - 10 <= x <= lx + 150:
                rows.setdefault(round(y), []).append((x, t))
        lines = []
        for key in sorted(rows):
            toks = [t for _, t in sorted(rows[key])]
            toks = [MOJIBAKE.get(t, t) for t in toks]
            line = " ".join(toks).strip()
            if line and line != vid:
                lines.append(line)
        schedule[vid] = lines
    colors = {}
    for vid, lines in schedule.items():
        cols = [ln for ln in lines if re.search(r"Blanco|Cobre|Negro|bicolor", ln, re.I)]
        colors[vid] = cols[0] if cols else ""
    tipos = {vid: " | ".join(lines[:4]) for vid, lines in schedule.items()}

    plt = Raster(p0)
    pc = p0_wall_center(p0)

    def to_model(vx, vz):
        return round((vx - pc[0]) / PT_PER_M_50, 2), round((vz - pc[1]) / PT_PER_M_50, 2)

    vents = []
    for vid in VIDS:
        e = elevations.get(vid, {})
        geo, cot = e.get("medido", {}), e.get("cota", {})
        ancho = cot.get("ancho_m", geo.get("ancho_m"))
        alto = cot.get("alto_m", geo.get("alto_m"))
        ante = cot.get("antepecho_m", geo.get("antepecho_m"))
        if ancho is None or alto is None:
            raise SystemExit(f"sin medidas para {vid}")

        op = None
        if vid in lab_plan:
            lx, ly = lab_plan[vid]
            if vid in ("V03", "V04"):
                op = opening_from_frame_lines(p0, lx, ly, ancho)
            if op is None:
                op = find_opening(plt, lx, ly, ancho)
                if not op or abs(op["len_m"] - ancho) > 0.45:
                    alt = opening_from_frame_lines(p0, lx, ly, ancho)
                    if alt and (not op or abs(alt["len_m"] - ancho)
                                < abs(op["len_m"] - ancho)):
                        op = alt
            if op and "metodo" not in op:
                op["metodo"] = "raster_muros"

        hueco = None
        if op:
            if op["orient"] == "h":
                cx, cz = to_model((op["lo"] + op["hi"]) / 2, op["center"])
            else:
                cx, cz = to_model(op["center"], (op["lo"] + op["hi"]) / 2)
            fachada = fachada_de(cx, cz, bounds, op["orient"])
            near_vid = [c for c in vidrios
                        if math.hypot(cx - c["centro"][0], cz - c["centro"][1]) <= 2.0]
            cand_gaps = [g for g in gaps
                         if g["orientacion"] == op["orient"]
                         and math.hypot(cx - g["centro"][0],
                                        cz - g["centro"][1]) < 1.5]
            matched = min(cand_gaps, key=lambda g: math.hypot(
                cx - g["centro"][0], cz - g["centro"][1])) if cand_gaps else None
            diff = abs(op["len_m"] - ancho)
            conf = "alta" if diff <= 0.12 else "media"
            if vid in ("V03", "V04", "V08"):
                conf = "media" if diff <= 0.25 else "baja"
            if matched and abs(matched["longitud_m"] - ancho) > 0.35:
                conf = "baja"
            hueco = {
                "indices_vidrio": sorted(i for c in near_vid for i in c["indices"]),
                "centro": [cx, cz],
                "longitud_m": round(op["len_m"], 2),
                "fachada": fachada,
                "confianza": conf,
                "metodo": op["metodo"],
                "notas": gap_note(vid, op, ancho, matched),
            }

        vents.append({
            "id": vid,
            "pagina": 1,
            "ancho_m": round(ancho, 2),
            "alto_m": round(alto, 2),
            "antepecho_m": round(ante, 2) if ante is not None else None,
            "tipologia": tipos.get(vid, ""),
            "color": colors.get(vid, ""),
            "notas": elev_note(vid, e),
            "hueco_plano": hueco,
        })

    ng = north_angle(plan[0])
    if ng:
        norte, tip, center = ng
        norte_notas = (
            f"Aguja del cajetín de distribución.pdf: punta desde el centro {center} "
            f"hasta {tuple(round(v, 1) for v in tip)}; ángulo {norte:.2f}° CCW respecto "
            f"a +x de la página (sentido matemático). Cross-check OSM: la calle junto al "
            f"nº2 (way 23549990) corre a 269,2°/88,8° y la fachada de calle es paralela; "
            f"con esta aguja las fachadas del modelo quedan a 42,5°/132,5°, unos 46° de "
            f"discrepancia. El símbolo se repite idéntico en todas las hojas (distribución, "
            f"estado inicial, carpintería, demolición), por lo que es el norte del "
            f"proyecto, pero conviene confirmarlo con el arquitecto."
        )
    else:
        norte, norte_notas = None, "No se localizó el símbolo de norte en distribución.pdf."

    data = {
        "generado": date.today().isoformat(),
        "fuente": {
            "ventanas": str(PDF.relative_to(ROOT)),
            "norte": str(PLAN.relative_to(ROOT)),
            "planos3d": str(PLANOS3D.relative_to(ROOT)),
        },
        "escalas": {"planta_PEI.05": "1:50", "alzados_PEI.06": "1:30",
                    "pt_por_m_1_50": round(PT_PER_M_50, 4),
                    "pt_por_m_1_30": round(PT_PER_M_30, 4)},
        "paginas": {"indice_0": "PEI.05 planta 1:50 (etiquetas V0x)",
                    "indice_1": "PEI.06 alzados 1:30 (medidas y cuadro)",
                    "campo_pagina_ventanas": "índice 0-based de la página del alzado"},
        "unidades_cota": (
            "Las cotas del cuadro son metros con coma decimal (2,98 = 2,98 m). "
            "La geometría a 1:30 lo confirma: p.ej. la cota 2,98 m mide 281,6 pt "
            "(281,6/94,488 = 2,98). En data/texto/*.txt hay artefactos del "
            "extractor antiguo con los dígitos invertidos (93,0=0,39; 12,1=1,21; "
            "98,0=0,89; 24,1=1,42; 52,1=1,25; 40,1=1,04; 17,0=0,71); con "
            "page.get_text('words') los valores salen correctos."
        ),
        "norte_grados": round(norte, 2) if norte is not None else None,
        "norte_notas": norte_notas,
        "notas_fachadas": (
            "La orientación de cada hueco usa los ejes del modelo de planos3d "
            "(norte=z mínimo, sur=z máximo, este=x máximo, oeste=x mínimo), que es "
            "la convención de AGENTS.md. AVISO: según la aguja del norte, los ejes "
            "del plano estarían girados ~42,5°; ver norte_notas. Clasificación del "
            "informe ARQUITECTO_ANALISIS_DISTRIBUCION.md: V01-V04 fachada principal "
            "(salón-comedor y dormitorio principal) y V05-V08 fachada trasera/patio "
            "(dormitorios 2, 3 y cocina)."
        ),
        "huecos_planos3d": gaps,
        "muros_vidrio_planos3d": vidrios,
        "ventanas": vents,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"escrito {OUT.relative_to(ROOT)}")
    for v in vents:
        h = v["hueco_plano"] or {}
        print(f"  {v['id']}  {v['ancho_m']:.2f}x{v['alto_m']:.2f}  "
              f"ant={v['antepecho_m']}  {h.get('fachada', '?'):8s} "
              f"conf={h.get('confianza', '-'):5s} hueco={h.get('centro')} "
              f"L={h.get('longitud_m')}")
    print(f"norte_grados={data['norte_grados']}  ({len(vents)} ventanas, "
          f"{len(vidrios)} grupos vidrio, {len(gaps)} huecos planos3d)")
    return 0


def fachada_de(cx, cz, bounds, orient):
    if orient == "h":
        return "norte" if abs(cz - bounds["z0"]) <= abs(cz - bounds["z1"]) else "sur"
    return "oeste" if abs(cx - bounds["x0"]) <= abs(cx - bounds["x1"]) else "este"


if __name__ == "__main__":
    raise SystemExit(main())
