#!/usr/bin/env python3
"""
Genera data/planos3d.json, data/imagenes/planta_textura.jpg y
data/imagenes/geometria_debug.png a partir de la geometría vectorial de
Planos/distribución.pdf (sin OCR: el PDF es CAD vectorial).

El JSON alimenta el visor 3D `render3d.html`.

Requiere: pymupdf, numpy, pillow

Uso:
    python3 scripts/generar_geometria3d.py
"""
from __future__ import annotations

import json
import math
from collections import deque
from datetime import date
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "Planos" / "distribución.pdf"
PNG = ROOT / "Planos" / "distribución.png"
OUT_JSON = ROOT / "data" / "planos3d.json"
OUT_TEXTURE = ROOT / "data" / "imagenes" / "planta_textura.jpg"
OUT_DEBUG = ROOT / "data" / "imagenes" / "geometria_debug.png"

# 1:50 => 1 m real = 20 mm de papel = 20/25.4*72 pt
PT_PER_M = 20.0 / 25.4 * 72.0
FILL_MURO = (0.81961, 0.81961, 0.81961)        # muros (gris oscuro)
FILL_ALICATADO = (0.92941, 0.92941, 0.92941)   # suelos alicatados (gris claro)
ALTURA_MURO = 2.6
ALTURA_VIDRIO = 2.3
GRID = 40  # px por metro para el análisis de estancias

# Semillas de estancia (id, nombre, x, z) en metros de modelo. Varias semillas
# pueden compartir id (p. ej. el pasillo o el salón, que son espacios abiertos).
SEEDS = [
    ("dorm-1", "Dormitorio 1", -5.8, -2.4),
    ("bano-1", "Baño 1", -2.6, -2.4),
    ("bano-2", "Baño 2", 0.3, -2.4),
    ("dorm-principal", "Dormitorio principal", 4.3, -2.0),
    ("pasillo", "Pasillo", -5.0, -1.0),
    ("pasillo", "Pasillo", -1.5, -1.0),
    ("pasillo", "Pasillo", 1.5, -1.0),
    ("dorm-2", "Dormitorio 2", -5.3, 1.5),
    ("dorm-3", "Dormitorio 3", -2.6, 1.5),
    ("salon", "Salón · comedor · cocina", 0.5, 0.5),
    ("salon", "Salón · comedor · cocina", 3.0, 1.0),
    ("salon", "Salón · comedor · cocina", 5.5, 1.5),
    ("salon", "Salón · comedor · cocina", 3.0, 2.8),
    ("recibidor", "Recibidor", 0.9, 3.3),
]

# Terraza (polígono manual, no está cerrada por muros en el plano)
TERRAZA = {"id": "terraza", "nombre": "Terraza", "pts": [[8.23, -0.5], [9.5, -0.5], [9.5, 3.45], [8.23, 3.45]]}


def vis_transform(page):
    def fn(x, y):
        p = pymupdf.Point(x, y) * page.rotation_matrix
        return (p.x, p.y)

    return fn


def polygon_points(drawing, fn):
    """Devuelve la lista de subcaminos (polígonos) de un dibujo."""
    paths = []
    cur = []
    for it in drawing["items"]:
        if it[0] == "l":
            a = fn(it[1].x, it[1].y)
            b = fn(it[2].x, it[2].y)
            if cur and (abs(cur[-1][0] - a[0]) > 1e-6 or abs(cur[-1][1] - a[1]) > 1e-6):
                paths.append(cur)
                cur = []
            if not cur:
                cur.append(a)
            cur.append(b)
        elif it[0] == "re":
            if cur:
                paths.append(cur)
                cur = []
            r = it[1]
            paths.append([fn(r.x0, r.y0), fn(r.x1, r.y0), fn(r.x1, r.y1), fn(r.x0, r.y1)])
        elif it[0] == "qu":
            if cur:
                paths.append(cur)
                cur = []
            q = it[1]
            paths.append([fn(q.ul.x, q.ul.y), fn(q.ur.x, q.ur.y), fn(q.lr.x, q.lr.y), fn(q.ll.x, q.ll.y)])
    if cur:
        paths.append(cur)
    out = []
    for pts in paths:
        if len(pts) > 1 and abs(pts[0][0] - pts[-1][0]) <= 1e-6 and abs(pts[0][1] - pts[-1][1]) <= 1e-6:
            pts.pop()
        if len(pts) >= 3:
            out.append(pts)
    return out


def poly_area(pts):
    s = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def poly_perimeter(pts):
    s = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        s += math.hypot(x1 - x0, y1 - y0)
    return s


def thinness(pts):
    """Espesor aproximado de un polígono alargado: t ~ 2*A/P."""
    return 2.0 * poly_area(pts) / max(poly_perimeter(pts), 1e-9)


def _clip(poly, keep):
    """Sutherland-Hodgman contra un semiplano. keep(p) dice si p se conserva."""
    if len(poly) < 3:
        return []
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ka, kb = keep(a), keep(b)
        if kb:
            if not ka:
                out.append(_cruce(a, b, keep))
            out.append(b)
        elif ka:
            out.append(_cruce(a, b, keep))
    return out


def _cruce(a, b, keep):
    """Punto donde el segmento a->b cruza el borde (búsqueda binaria)."""
    lo, hi = 0.0, 1.0
    ka = keep(a)
    for _ in range(40):
        mid = (lo + hi) / 2
        m = (a[0] + (b[0] - a[0]) * mid, a[1] + (b[1] - a[1]) * mid)
        if keep(m) == ka:
            lo = mid
        else:
            hi = mid
    return (a[0] + (b[0] - a[0]) * hi, a[1] + (b[1] - a[1]) * hi)


def resta_rect(poly, rect):
    """Resta un rectángulo (x0,x1,z0,z1, en las mismas unidades) de un
    polígono convexo. Devuelve la lista de piezas (hasta 4)."""
    x0, x1, z0, z1 = rect
    izq = _clip(poly, lambda p: p[0] <= x0)
    der = _clip(poly, lambda p: p[0] >= x1)
    mid = _clip(_clip(poly, lambda p: p[0] >= x0), lambda p: p[0] <= x1)
    aba = _clip(mid, lambda p: p[1] <= z0)
    arr = _clip(mid, lambda p: p[1] >= z1)
    return [q for q in (izq, der, aba, arr)
            if len(q) >= 3 and poly_area(q) > 1.0]


def punzonar_puertas(muros_pdf, cx, cz):
    """Abre los huecos de data/puertas.json en los rellenos de muro (coords
    vis pt). Solo puertas con pared h/v y hueco real (no D7/D8/PA02, que no
    llevan muro). Devuelve la lista de polígonos resultante."""
    try:
        puertas = json.loads((ROOT / "data" / "puertas.json")
                             .read_text(encoding="utf-8"))["puertas"]
    except (OSError, KeyError, ValueError):
        return muros_pdf
    rects = []
    for p in puertas:
        if p["tipo"] in ("corredera",) and p["id"] == "D7":
            continue
        if p["tipo"] in ("vidriera",):
            continue
        if p["pared"] not in ("h", "v"):
            continue
        cxm, czm = p["centro"]
        w = p["ancho"] / 2 + 0.03
        t = 0.20  # cubre cualquier espesor de muro/tabique
        if p["pared"] == "h":
            rects.append(((cxm - w) * PT_PER_M + cx, (cxm + w) * PT_PER_M + cx,
                          (czm - t) * PT_PER_M + cz, (czm + t) * PT_PER_M + cz))
        else:
            rects.append(((cxm - t) * PT_PER_M + cx, (cxm + t) * PT_PER_M + cx,
                          (czm - w) * PT_PER_M + cz, (czm + w) * PT_PER_M + cz))
    if not rects:
        return muros_pdf
    out = []
    for poly in muros_pdf:
        pendientes = [poly]
        for r in rects:
            x0, x1, z0, z1 = r
            if max(p[0] for p in poly) < x0 or min(p[0] for p in poly) > x1 \
                    or max(p[1] for p in poly) < z0 or min(p[1] for p in poly) > z1:
                continue
            nuevos = []
            for q in pendientes:
                if max(p[0] for p in q) < x0 or min(p[0] for p in q) > x1 \
                        or max(p[1] for p in q) < z0 or min(p[1] for p in q) > z1:
                    nuevos.append(q)
                    continue
                partes = resta_rect(q, r)
                if not partes:
                    nuevos.append(q)  # el rectángulo lo cubre todo: conservar
                    continue
                hueco = _hueco_exact(q, r)
                if abs(sum(poly_area(t) for t in partes)
                       - (poly_area(q) - hueco)) > 0.01 * poly_area(q):
                    nuevos.append(q)  # no convexo: se conserva sin punzonar
                else:
                    nuevos.extend(partes)
            pendientes = nuevos
        out.extend(pendientes)
    print(f"muros: {len(muros_pdf)} polígonos -> {len(out)} tras abrir huecos")
    return out


def _hueco_exact(poly, rect):
    """Área exacta de la intersección polígono×rect (para polígonos convexos;
    si no lo es, el control de áreas de punzonar_puertas lo descarta)."""
    x0, x1, z0, z1 = rect
    q = _clip(_clip(poly, lambda p: p[0] >= x0), lambda p: p[0] <= x1)
    q = _clip(_clip(q, lambda p: p[1] >= z0), lambda p: p[1] <= z1)
    return poly_area(q) if len(q) >= 3 else 0.0


def extract(page):
    fn = vis_transform(page)
    muros, alicatados = [], []
    for d in page.get_drawings():
        f = d.get("fill")
        if f is None:
            continue
        for pts in polygon_points(d, fn):
            if all(abs(a - b) < 0.005 for a, b in zip(f, FILL_MURO)):
                muros.append(pts)
            elif all(abs(a - b) < 0.005 for a, b in zip(f, FILL_ALICATADO)):
                alicatados.append(pts)
    return muros, alicatados


def seal_gaps(polys, max_gap_pt, max_offset_pt=20.0):
    """Cierra huecos de puertas/ventanas uniendo extremos de muros alineados.

    Devuelve una lista de conectores (rectángulos finos) en coords vis pt.
    """
    edges = []
    for poly in polys:
        n = len(poly)
        t = thinness(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if math.hypot(b[0] - a[0], b[1] - a[1]) >= 0.1 * PT_PER_M:
                edges.append((a, b, t))
    connectors = []
    for i, (a1, b1, t1) in enumerate(edges):
        L1 = math.hypot(b1[0] - a1[0], b1[1] - a1[1])
        d1 = ((b1[0] - a1[0]) / L1, (b1[1] - a1[1]) / L1)
        for j in range(i + 1, len(edges)):
            a2, b2, t2 = edges[j]
            # descartar aristas que comparten vértice
            if min(math.hypot(a1[0] - a2[0], a1[1] - a2[1]),
                   math.hypot(a1[0] - b2[0], a1[1] - b2[1]),
                   math.hypot(b1[0] - a2[0], b1[1] - a2[1]),
                   math.hypot(b1[0] - b2[0], b1[1] - b2[1])) < 1.0:
                continue
            L2 = math.hypot(b2[0] - a2[0], b2[1] - a2[1])
            d2 = ((b2[0] - a2[0]) / L2, (b2[1] - a2[1]) / L2)
            for p, q, dp, dq, tq in ((b1, a2, d1, d2, t2), (b1, b2, d1, d2, t2),
                                     (a1, a2, d1, d2, t2), (a1, b2, d1, d2, t2)):
                vx, vy = q[0] - p[0], q[1] - p[1]
                L = math.hypot(vx, vy)
                if not (0.04 * PT_PER_M < L <= max_gap_pt):
                    continue
                ux, uy = vx / L, vy / L
                if abs(ux * dp[0] + uy * dp[1]) < 0.985:
                    continue
                if abs(ux * dq[0] + uy * dq[1]) < 0.985:
                    continue
                # distancia perpendicular al eje del otro muro
                if abs((p[0] - a2[0]) * d2[1] - (p[1] - a2[1]) * d2[0]) > max_offset_pt:
                    continue
                if abs((q[0] - a1[0]) * d1[1] - (q[1] - a1[1]) * d1[0]) > max_offset_pt:
                    continue
                w = max(0.08 * PT_PER_M, min(0.30 * PT_PER_M, (t1 + tq) / 2))
                nx, ny = -uy * w / 2, ux * w / 2
                connectors.append([[p[0] + nx, p[1] + ny], [q[0] + nx, q[1] + ny],
                                   [q[0] - nx, q[1] - ny], [p[0] - nx, p[1] - ny]])

    # segunda pasada: unir esquinas/T de menos de 0.5 m en cualquier orientación
    endpoints = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if math.hypot(b[0] - a[0], b[1] - a[1]) >= 0.2 * PT_PER_M:
                endpoints.append((a, b))
    for i, (a1, b1) in enumerate(endpoints):
        for j in range(i + 1, len(endpoints)):
            a2, b2 = endpoints[j]
            if min(math.hypot(a1[0] - a2[0], a1[1] - a2[1]),
                   math.hypot(a1[0] - b2[0], a1[1] - b2[1]),
                   math.hypot(b1[0] - a2[0], b1[1] - a2[1]),
                   math.hypot(b1[0] - b2[0], b1[1] - b2[1])) < 1.0:
                continue
            for p, q in ((b1, a2), (b1, b2), (a1, a2), (a1, b2)):
                vx, vy = q[0] - p[0], q[1] - p[1]
                L = math.hypot(vx, vy)
                if not (0.02 * PT_PER_M < L <= 0.5 * PT_PER_M):
                    continue
                if abs(vx) + abs(vy) < 1e-9:
                    continue
                ux, uy = vx / L, vy / L
                w = 0.15 * PT_PER_M
                nx, ny = -uy * w / 2, ux * w / 2
                connectors.append([[p[0] + nx, p[1] + ny], [q[0] + nx, q[1] + ny],
                                   [q[0] - nx, q[1] - ny], [p[0] - nx, p[1] - ny]])
    return connectors


# ── operaciones en rejilla ──────────────────────────────────────────────────

def label(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    n = 0
    for y in range(h):
        for x in range(w):
            if mask[y, x] and lab[y, x] == 0:
                n += 1
                q = deque([(y, x)])
                lab[y, x] = n
                while q:
                    cy, cx = q.popleft()
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = n
                            q.append((ny, nx))
    return lab, n


def watershed(free, seeds_px, shape):
    """Asigna cada píxel libre a la semilla más cercana (BFS multi-fuente)."""
    lab = np.zeros(shape, dtype=np.int32)
    q = deque()
    for sid, (sy, sx) in seeds_px:
        if not free[sy, sx]:
            best, bd = (sy, sx), None
            for dy in range(-int(0.6 * GRID), int(0.6 * GRID) + 1):
                for dx in range(-int(0.6 * GRID), int(0.6 * GRID) + 1):
                    ny, nx = sy + dy, sx + dx
                    if 0 <= ny < shape[0] and 0 <= nx < shape[1] and free[ny, nx]:
                        d = dy * dy + dx * dx
                        if bd is None or d < bd:
                            best, bd = (ny, nx), d
            sy, sx = best
        if lab[sy, sx] == 0:
            lab[sy, sx] = sid
            q.append((sy, sx))
    while q:
        cy, cx = q.popleft()
        cur = lab[cy, cx]
        for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
            if 0 <= ny < shape[0] and 0 <= nx < shape[1] and free[ny, nx] and lab[ny, nx] == 0:
                lab[ny, nx] = cur
                q.append((ny, nx))
    return lab


def trace_contour(mask):
    """Contorno exterior (Moore, con backtrack) de una máscara booleana."""
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return []
    h, w = mask.shape
    dirs = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    start = (int(ys[0]), int(xs[0]))
    cur = start
    back = (start[0], start[1] - 1)
    contour = [start]
    for _ in range(8 * mask.size):
        bd = (back[0] - cur[0], back[1] - cur[1])
        if bd not in dirs:
            break
        bi = dirs.index(bd)
        found = False
        for k in range(1, 9):
            d = dirs[(bi + k) % 8]
            nxt = (cur[0] + d[0], cur[1] + d[1])
            if 0 <= nxt[0] < h and 0 <= nxt[1] < w and mask[nxt]:
                d_back = dirs[(bi + k - 1) % 8]
                back = (cur[0] + d_back[0], cur[1] + d_back[1])
                cur = nxt
                contour.append(cur)
                found = True
                break
        if not found or cur == start:
            break
    return contour


def rdp(points, eps):
    if len(points) < 3:
        return points
    (x0, y0), (x1, y1) = points[0], points[-1]
    dmax, idx = 0.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        den = math.hypot(x1 - x0, y1 - y0)
        d = abs((x1 - x0) * (y0 - py) - (x0 - px) * (y1 - y0)) / den if den > 0 else math.hypot(px - x0, py - y0)
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(points[:idx + 1], eps)[:-1] + rdp(points[idx:], eps)
    return [points[0], points[-1]]


def main() -> int:
    doc = pymupdf.open(PDF)
    page = doc[0]
    muros_pdf, alic_pdf = extract(page)
    print(f"muros: {len(muros_pdf)}  alicatados: {len(alic_pdf)}")

    all_pts = [p for poly in muros_pdf for p in poly]
    x0 = min(p[0] for p in all_pts)
    x1 = max(p[0] for p in all_pts)
    z0 = min(p[1] for p in all_pts)
    z1 = max(p[1] for p in all_pts)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2

    def m(px, pz):
        return ((px - cx) / PT_PER_M, (pz - cz) / PT_PER_M)

    # Huecos de puerta (data/puertas.json): se abren solo en la geometría de
    # salida; el raster de estancias sigue usando los rellenos originales
    # (las puertas se consideran cerradas para delimitar estancias).
    muros_vista = punzonar_puertas(muros_pdf, cx, cz)

    muros = []
    provisionales = []
    for poly in muros_vista:
        t = thinness(poly) / PT_PER_M
        tipo = "estructural" if t >= 0.14 else ("tabique" if t >= 0.045 else "vidrio")
        pts = [m(*p) for p in poly]
        provisionales.append({"tipo": tipo, "t": t, "pts": pts})
    # 2026-09-19: los rellenos finos (<4,5 cm) del CAD no son ventanas sino
    # aristas duplicadas de muros macizos, restos de huecos de puerta y
    # contornos de muebles (ver /tmp/opencode/vidrios_overlay.png: 35
    # fragmentos "vidrio", p. ej. la partición D2/D3 que solo salió como
    # tiras). Regla: se descartan los cortos (<0,8 m); los largos que solapan
    # con un muro sólido se descartan como duplicados; los largos sin muro
    # sólido debajo se conservan como tabique (no como vidrio).
    solidos = [p for p in provisionales if p["tipo"] in ("estructural", "tabique")]
    def caja(p):
        xs = [a for a, _b in p["pts"]]
        zs = [b for _a, b in p["pts"]]
        return min(xs), max(xs), min(zs), max(zs)
    cajas_sol = [caja(p) for p in solidos]
    for p in provisionales:
        if p["tipo"] in ("estructural", "tabique"):
            muros.append({"tipo": p["tipo"], "t": round(p["t"], 3),
                          "pts": [[round(a, 3), round(b, 3)] for a, b in p["pts"]]})
            continue
        x0p, x1p, z0p, z1p = caja(p)
        largo = max(x1p - x0p, z1p - z0p)
        if largo < 0.8:
            continue  # resto de puerta, mueble o pelusa del CAD
        horiz = (x1p - x0p) >= (z1p - z0p)
        duplicado = False
        for sx0, sx1, sz0, sz1 in cajas_sol:
            if horiz:
                if abs((sz0 + sz1) / 2 - (z0p + z1p) / 2) < 0.15 \
                        and sx0 < x1p - 0.3 and sx1 > x0p + 0.3:
                    duplicado = True
                    break
            else:
                if abs((sx0 + sx1) / 2 - (x0p + x1p) / 2) < 0.15 \
                        and sz0 < z1p - 0.3 and sz1 > z0p + 0.3:
                    duplicado = True
                    break
        if duplicado:
            continue  # arista duplicada de un muro ya extraído
        muros.append({"tipo": "tabique", "t": round(max(p["t"], 0.07), 3),
                      "pts": [[round(a, 3), round(b, 3)] for a, b in p["pts"]]})
    print(f"muros: {len(provisionales)} polígonos -> {len(muros)} tras filtrar vidrios")

    # 2026-09-19: jambas de la galería (V03 sur + V04 oeste, PEI.05). Los muros
    # de la galería van en línea fina sin relleno gris, así que la extracción
    # no los ve y los marcos V03/V04 flotaban exentos (la "esquina de cristal"
    # reportada). Se añaden los dos tramos macizos que el plano sí dibuja:
    # oeste-norte (del muro de cocina hasta V04) y sur-este (de V03 al pilar).
    for x0j, z0j, x1j, z1j in ((-1.25, 2.50, -1.11, 3.12),
                               (0.025, 4.25, 0.17, 4.39)):
        muros.append({"tipo": "tabique", "t": 0.14,
                      "pts": [[x0j, z0j], [x1j, z0j], [x1j, z1j], [x0j, z1j]]})

    alicatados = []
    for poly in alic_pdf:
        if poly_area(poly) / (PT_PER_M ** 2) < 0.8:
            continue
        pts = [m(*p) for p in poly]
        alicatados.append({"pts": [[round(a, 3), round(b, 3)] for a, b in pts]})

    conectores = seal_gaps(muros_pdf, max_gap_pt=4.5 * PT_PER_M)
    print(f"conectores de sellado: {len(conectores)}")

    # ── rejilla ──
    ox, oz = x0 - PT_PER_M, z0 - PT_PER_M
    w = int((x1 - x0 + 2 * PT_PER_M) / PT_PER_M * GRID)
    h = int((z1 - z0 + 2 * PT_PER_M) / PT_PER_M * GRID)

    def g2m(px, py):
        vis_x = ox + (px + 0.5) * PT_PER_M / GRID
        vis_z = oz + (py + 0.5) * PT_PER_M / GRID
        return ((vis_x - cx) / PT_PER_M, (vis_z - cz) / PT_PER_M)

    def m2g(mx, mz):
        return (int((mx * PT_PER_M + cx - ox) * GRID / PT_PER_M),
                int((mz * PT_PER_M + cz - oz) * GRID / PT_PER_M))

    def rasterize(polys_pt):
        img = Image.new("1", (w, h), 0)
        dr = ImageDraw.Draw(img)
        for poly in polys_pt:
            dr.polygon([((p[0] - ox) * GRID / PT_PER_M, (p[1] - oz) * GRID / PT_PER_M) for p in poly], fill=1)
        return np.array(img, dtype=bool)

    mask = rasterize(muros_pdf)
    sealed = rasterize(muros_pdf + conectores)
    # dilatar el sello 0.1 m para cerrar juntas de esquina de menos de 0.2 m
    seald = sealed.copy()
    for _ in range(4):
        seald = (seald | np.roll(seald, 1, 0) | np.roll(seald, -1, 0)
                 | np.roll(seald, 1, 1) | np.roll(seald, -1, 1))

    # exterior = componentes libres que tocan el borde de la rejilla
    lab_free, _ = label(~seald)
    border_ids = set(int(v) for v in np.concatenate([lab_free[0, :], lab_free[-1, :], lab_free[:, 0], lab_free[:, -1]]))
    exterior = np.isin(lab_free, [i for i in border_ids if i != 0])
    envelope = ~exterior
    free = envelope & ~mask

    # huella del edificio (contorno exterior de la envolvente) para el suelo 3D
    cont_huella = trace_contour(envelope)
    huella = []
    if len(cont_huella) >= 4:
        cont_m = [g2m(c[1], c[0]) for c in cont_huella]
        huella = [[round(p[0], 2), round(p[1], 2)] for p in rdp(cont_m, 0.05)]
        if len(huella) < 3:
            huella = []

    for rid, _n, sx, sz in SEEDS:
        gx, gz = m2g(sx, sz)
        if 0 <= gz < h and 0 <= gx < w and exterior[gz, gx]:
            print(f"  ! semilla de {rid} en ({sx},{sz}) cae en el exterior (posible fuga)")

    # semillas por zona (varias semillas comparten zona)
    zone_ids = []
    seeds_px = []
    for sid, (rid, _n, sx, sz) in enumerate(SEEDS, start=1):
        if rid not in zone_ids:
            zone_ids.append(rid)
        gx, gz = m2g(sx, sz)
        gx = min(max(gx, 0), w - 1)
        gz = min(max(gz, 0), h - 1)
        seeds_px.append((zone_ids.index(rid) + 1, (gz, gx)))
    lab = watershed(free, seeds_px, (h, w))

    estancias = []
    for zi, rid in enumerate(zone_ids, start=1):
        nombre = next(n for r, n, _, _ in SEEDS if r == rid)
        comp = lab == zi
        npix = int(comp.sum())
        if npix < GRID * GRID * 0.5:
            print(f"  ! {rid}: sin zona asignada")
            continue
        cont = trace_contour(comp)
        if len(cont) < 4:
            continue
        cont_m = [g2m(c[1], c[0]) for c in cont]
        simple = rdp(cont_m, 0.07)
        pts = [[round(p[0], 2), round(p[1], 2)] for p in simple]
        cy_, cx_ = np.mean(np.nonzero(comp), axis=1)
        centro = [round(v, 2) for v in g2m(cx_, cy_)]
        estancias.append({"id": rid, "nombre": nombre,
                          "area": round(npix / (GRID * GRID), 2),
                          "centro": centro, "pts": pts})

    area_terraza = poly_area([(p[0] * PT_PER_M, p[1] * PT_PER_M) for p in TERRAZA["pts"]]) / PT_PER_M ** 2
    estancias.append({"id": TERRAZA["id"], "nombre": TERRAZA["nombre"],
                      "area": round(area_terraza, 2),
                      "centro": [round((TERRAZA["pts"][0][0] + TERRAZA["pts"][1][0]) / 2, 2),
                                 round((TERRAZA["pts"][0][1] + TERRAZA["pts"][2][1]) / 2, 2)],
                      "pts": TERRAZA["pts"], "manual": True})

    print(f"estancias: {len(estancias)}")
    for e in estancias:
        print(f"  {e['id']:16s} {e['area']:6.2f} m2  centro=({e['centro'][0]:6.2f},{e['centro'][1]:6.2f})")

    # ── textura recortada (incluye terraza) ──
    OUT_TEXTURE.parent.mkdir(parents=True, exist_ok=True)
    plan_img = Image.open(PNG).convert("RGB")
    sx_px = plan_img.size[0] / page.rect.width
    sy_px = plan_img.size[1] / page.rect.height
    margen = 0.6 * PT_PER_M
    tx0 = (x0 - margen)
    tz0 = (z0 - margen)
    tx1 = (cx + 9.8 * PT_PER_M)  # cubre la terraza
    tz1 = (z1 + margen)
    crop = plan_img.crop((int(tx0 * sx_px), int(tz0 * sy_px), int(tx1 * sx_px), int(tz1 * sy_px)))
    if crop.size[0] > 2800:
        f = 2800 / crop.size[0]
        crop = crop.resize((2800, int(crop.size[1] * f)), Image.LANCZOS)
    # oscurecer ligeramente los grises del plano (mantiene el blanco) para que
    # el dibujo se lea bien bajo la iluminación ACES del visor 3D
    crop = crop.point(lambda v: int(round(255 * (v / 255) ** 2.2)))
    crop.save(OUT_TEXTURE, quality=86, optimize=True)
    tex_rect = [round((tx0 - cx) / PT_PER_M, 3), round((tz0 - cz) / PT_PER_M, 3),
                round((tx1 - cx) / PT_PER_M, 3), round((tz1 - cz) / PT_PER_M, 3)]

    # ── debug overlay ──
    dbg = plan_img.copy()
    dr = ImageDraw.Draw(dbg, "RGBA")
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    font_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

    def to_px(p):
        return ((p[0] * PT_PER_M + cx) * sx_px, (p[1] * PT_PER_M + cz) * sy_px)

    palette = [(255, 99, 71), (60, 179, 113), (30, 144, 255), (255, 165, 0), (148, 0, 211),
               (0, 206, 209), (255, 215, 0), (199, 21, 133), (46, 139, 87), (70, 130, 180),
               (165, 42, 42)]
    for i, e in enumerate(estancias):
        if len(e["pts"]) < 3:
            continue
        col = palette[i % len(palette)]
        dr.polygon([to_px(p) for p in e["pts"]], fill=col + (80,), outline=col + (255,))
        c = to_px(e["centro"])
        dr.rectangle([c[0] - 4, c[1] - 4, c[0] + 4 + 280, c[1] + 40], fill=(255, 255, 255, 230))
        dr.text((c[0], c[1]), f"{e['nombre']} {e['area']:.1f}m2", fill=(0, 0, 0, 255), font=font)

    for conn in conectores:
        dr.polygon([to_px(p) for p in conn], fill=(255, 0, 0, 120))
    dbg.save(OUT_DEBUG)
    print(f"escrito {OUT_DEBUG.relative_to(ROOT)}")

    data = {
        "generado": date.today().isoformat(),
        "fuente": "Planos/distribución.pdf",
        "escala": "1:50",
        "pt_por_m": round(PT_PER_M, 4),
        "altura_muro": ALTURA_MURO,
        "altura_vidrio": ALTURA_VIDRIO,
        "bounds": {"x0": round((x0 - cx) / PT_PER_M, 3), "z0": round((z0 - cz) / PT_PER_M, 3),
                   "x1": round((x1 - cx) / PT_PER_M, 3), "z1": round((z1 - cz) / PT_PER_M, 3)},
        "huella": huella,
        "muros": muros,
        "alicatados": alicatados,
        "estancias": estancias,
        "textura": {"archivo": str(OUT_TEXTURE.relative_to(ROOT)),
                    "margen_m": round(margen / PT_PER_M, 3), "rect_m": tex_rect},
    }
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"escrito {OUT_JSON.relative_to(ROOT)} ({OUT_JSON.stat().st_size/1024:.0f} KB)")
    print(f"escrito {OUT_TEXTURE.relative_to(ROOT)} ({OUT_TEXTURE.stat().st_size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
