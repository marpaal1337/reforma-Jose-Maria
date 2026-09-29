#!/usr/bin/env python3
"""
Mide la carpintería interior y las cotas del proyecto a partir de dos planos
en PDF vectorial (sin OCR):

  - Planos/PE_carpinteria_interior.pdf  (PE/I.06, 1:50): mobiliario, puertas
    (arcos de barrido) y etiquetas P01..P07, PA01/PA02, E01/E02, M01..M05,
    A01..A04, PE, COCINA, ISLA.
  - Planos/PE_planta_cotas.pdf          (PE/A.03, 1:50): mismos muros y muebles
    más los textos de estancia (nombre, superficie m2 y altura h=).

Método
------
Se reutilizan las utilidades de `generar_geometria3d.py` para que las
coordenadas caigan EXACTAMENTE en el mismo sistema de modelo (metros) que usa
`render3d.html`:

    muros, _ = g.extract(page)                 # muros ya rotados
    cx, cz   = centro de la caja de los muros
    fn       = g.vis_transform(page)           # rotación de la página
    to_m(px, py) = ((fn(px,py)[0] - cx) / g.PT_PER_M,
                    (fn(px,py)[1] - cz) / g.PT_PER_M)

`cx, cz` valen (558.67, 384.06) para ambos PDF (se comprueba con tolerancia
0.05). Todos los dibujos se filtran a |x| < 10 m y |z| < 6 m y se descartan los
rellenos grises (muros y alicatados). Además, las capas de cotas/sombreados/
textos del CAD (`CAPAS_IGNORADAS`) no generan rectángulos ni arcos (se
conservan como segmentos): sin ese filtro las líneas de cota producen cientos
de rectángulos falsos. La `width` de los segmentos es el grosor de trazo del
PDF en mm.

Extracción
----------
  * segmentos: cada arista 'l' (y los lados de los 're'), en metros.
  * rects:     rectángulos alineados a ejes (items 're', caminos cerrados de 4
               lados y 4 segmentos sueltos que comparten esquinas, tol. 1 cm).
  * arcos:     curvas 'c' encadenadas y ajustadas a un círculo; se marcan como
               `puerta_probable` si 0,55 m <= r <= 1,05 m y el barrido está
               entre 70° y 110°.
  * etiquetas: palabras del plano dentro del área de dibujo.
  * estancias_plano: nombre + superficie (m2) + altura (h=) leídos del PE/A.03.

Salidas
-------
  - data/carpinteria_medida.json
  - data/imagenes/carpinteria_debug.png          (todo el modelo, 3200 px)
  - data/imagenes/carpinteria_debug_oeste.png    (x -8,6 .. 0,5)
  - data/imagenes/carpinteria_debug_este.png     (x -0,5 .. 10)
  - data/imagenes/cotas_debug.png                (PE/A.03, ids con prefijo C)

Requiere: pymupdf, numpy, pillow (las mismas dependencias que el resto).

Uso:
    python3 scripts/medir_carpinteria.py
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import generar_geometria3d as g  # noqa: E402

PDF_CARPINTERIA = ROOT / "Planos" / "PE_carpinteria_interior.pdf"
PDF_COTAS = ROOT / "Planos" / "PE_planta_cotas.pdf"
PLANOS3D = ROOT / "data" / "planos3d.json"
OUT_JSON = ROOT / "data" / "carpinteria_medida.json"
IMAGENES = ROOT / "data" / "imagenes"
OUT_DEBUG = IMAGENES / "carpinteria_debug.png"
OUT_DEBUG_OESTE = IMAGENES / "carpinteria_debug_oeste.png"
OUT_DEBUG_ESTE = IMAGENES / "carpinteria_debug_este.png"
OUT_DEBUG_COTAS = IMAGENES / "cotas_debug.png"

# Área de dibujo del plano (metros de modelo).
LIM_X = 10.0
LIM_Z = 6.0
VISTA = (-8.6, 10.0, -5.0, 5.0)   # x0, x1, z0, z1
TOL_ESQUINA = 0.01                # 1 cm

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
FONT_REG = FONT_DIR / "DejaVuSans.ttf"

NUM_RE = re.compile(r"^\d+(?:[.,]\d+)?$")
TEXTO_M2 = "m2"
UNIDADES = {"m2", "m", "h="}

# Etiquetas de puerta (P-labels) para emparejar cada arco con su hoja.
P_LABEL_RE = re.compile(r"^(PE|P0[1-7]|PA0[12])$")

COL_MURO = (216, 216, 216)
COL_SEG = (20, 40, 140)
COL_RECT = (230, 126, 34)
COL_ARCO = (200, 30, 30)
COL_ETIQ = (20, 130, 40)
COL_ESTANCIA = (130, 30, 160)
COL_GRID = (232, 232, 232)
COL_EJE = (170, 170, 170)

# Capas del CAD que NO son mobiliario/carpintería (cotas, sombreados, textos):
# se conservan como segmentos, pero no generan rectángulos ni arcos.
CAPAS_IGNORADAS = {"0_Cotas", "0_Texto", "0_Sombreado", "0_Sombreado 2"}


# ── transformación ──────────────────────────────────────────────────────────

class Transform:
    """PDF -> coordenadas de modelo (metros) reutilizando generar_geometria3d."""

    def __init__(self, pdf: Path):
        self.doc = pymupdf.open(pdf)
        self.page = self.doc[0]
        muros, _ = g.extract(self.page)
        pts = [p for poly in muros for p in poly]
        x0 = min(p[0] for p in pts)
        x1 = max(p[0] for p in pts)
        z0 = min(p[1] for p in pts)
        z1 = max(p[1] for p in pts)
        self.cx = (x0 + x1) / 2
        self.cz = (z0 + z1) / 2
        self.fn = g.vis_transform(self.page)

    def to_m(self, px: float, py: float) -> tuple[float, float]:
        a, b = self.fn(px, py)
        return ((a - self.cx) / g.PT_PER_M, (b - self.cz) / g.PT_PER_M)


def _in_area(p: tuple[float, float]) -> bool:
    return abs(p[0]) < LIM_X and abs(p[1]) < LIM_Z


def _is_grey(fill) -> bool:
    """Rellenos grises del CAD (muros 0,82 y alicatados 0,93): se ignoran."""
    if fill is None:
        return False
    mx, mn = max(fill), min(fill)
    return (mx - mn) < 0.02 and 0.05 < mx < 0.97


def _dashed(drawing) -> bool:
    dz = drawing.get("dashes")
    if not dz:
        return False
    return str(dz).strip() not in ("[] 0", "[]0", "[]")


# ── segmentos ───────────────────────────────────────────────────────────────

def extract_segments(page, tf: Transform) -> list[dict]:
    """Aristas de línea ('l') y lados de rectángulo ('re') dentro del área."""
    crudos = []
    for d in page.get_drawings():
        if _is_grey(d.get("fill")):
            continue
        col = [round(float(c), 3) for c in (d.get("color") or (0.0, 0.0, 0.0))]
        w = round(float(d.get("width") or 0.0), 3)
        dash = _dashed(d)
        capa = d.get("layer") or ""
        for it in d["items"]:
            if it[0] == "l":
                pares = [(tf.to_m(it[1].x, it[1].y), tf.to_m(it[2].x, it[2].y))]
            elif it[0] == "re":
                r = it[1]
                esquinas = [tf.to_m(r.x0, r.y0), tf.to_m(r.x1, r.y0),
                            tf.to_m(r.x1, r.y1), tf.to_m(r.x0, r.y1)]
                pares = list(zip(esquinas, esquinas[1:] + esquinas[:1]))
            else:
                continue
            for p0, p1 in pares:
                if not (_in_area(p0) and _in_area(p1)):
                    continue
                crudos.append((p0, p1, w, tuple(col), dash, capa))

    vistos: dict[tuple, dict] = {}
    for p0, p1, w, col, dash, capa in crudos:
        a = (round(p0[0], 3), round(p0[1], 3))
        b = (round(p1[0], 3), round(p1[1], 3))
        k0, k1 = sorted((a, b))
        clave = (k0, k1, w, col)
        if clave in vistos:
            vistos[clave]["dashed"] = vistos[clave]["dashed"] or dash
            continue
        vistos[clave] = {"p0": list(a), "p1": list(b),
                         "width": round(w * 25.4 / 72.0, 3), "colour": list(col),
                         "dashed": dash, "layer": capa}
    return list(vistos.values())


# ── rectángulos ─────────────────────────────────────────────────────────────

def detectar_rects(segmentos: list[dict], prefijo: str) -> list[dict]:
    """Rectángulos alineados a ejes a partir de segmentos h/v.

    Cubre los tres casos del enunciado: items 're', caminos cerrados de 4 lados
    y 4 segmentos sueltos que comparten esquinas (tolerancia 1 cm).
    """
    horiz, vert = [], []
    for s in segmentos:
        if s.get("layer") in CAPAS_IGNORADAS:
            continue
        (x0, z0), (x1, z1) = s["p0"], s["p1"]
        if abs(z1 - z0) <= 1e-3 and abs(x1 - x0) > TOL_ESQUINA:
            horiz.append((min(x0, x1), max(x0, x1), (z0 + z1) / 2, s))
        elif abs(x1 - x0) <= 1e-3 and abs(z1 - z0) > TOL_ESQUINA:
            vert.append((min(z0, z1), max(z0, z1), (x0 + x1) / 2, s))

    vx: dict[float, list] = defaultdict(list)
    for v in vert:
        vx[round(v[2], 2)].append(v)

    def hay_vertical(x: float, zlo: float, zhi: float) -> bool:
        for k in (round(x, 2), round(x - 0.01, 2), round(x + 0.01, 2)):
            for v in vx.get(k, []):
                if v[0] <= zlo + TOL_ESQUINA and v[1] >= zhi - TOL_ESQUINA:
                    return True
        return False

    vistos: dict[tuple, dict] = {}
    for i in range(len(horiz)):
        ax0, ax1, az, sa = horiz[i]
        for j in range(i + 1, len(horiz)):
            bx0, bx1, bz, sb = horiz[j]
            if abs(az - bz) <= 0.03:
                continue
            if abs(ax0 - bx0) > TOL_ESQUINA or abs(ax1 - bx1) > TOL_ESQUINA:
                continue
            zlo, zhi = sorted((az, bz))
            if zhi - zlo <= 0.03:
                continue
            if not hay_vertical(ax0, zlo, zhi) or not hay_vertical(ax1, zlo, zhi):
                continue
            x0, x1 = sorted((ax0, ax1))
            clave = (round(x0, 2), round(zlo, 2), round(x1, 2), round(zhi, 2))
            if clave in vistos:
                continue
            dash = sa["dashed"] or sb["dashed"]
            vistos[clave] = {"x0": clave[0], "z0": clave[1],
                             "x1": clave[2], "z1": clave[3],
                             "ancho": round(clave[2] - clave[0], 3),
                             "fondo": round(clave[3] - clave[1], 3),
                             "colour": list(sa["colour"]), "dashed": bool(dash)}

    rects = sorted(vistos.values(),
                   key=lambda r: (r["z0"], r["x0"], -(r["ancho"] * r["fondo"])))
    for n, r in enumerate(rects, start=1):
        r["id"] = f"{prefijo}R{n}"
    return [{"id": r["id"], **{k: r[k] for k in
             ("x0", "z0", "x1", "z1", "ancho", "fondo", "colour", "dashed")}}
            for r in rects]


# ── arcos ───────────────────────────────────────────────────────────────────

def _bezier(p1: tuple[float, float], c1: tuple[float, float],
            c2: tuple[float, float], p4: tuple[float, float],
            t: float) -> tuple[float, float]:
    mt = 1.0 - t
    return (mt ** 3 * p1[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t ** 3 * p4[0],
            mt ** 3 * p1[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t ** 3 * p4[1])


def ajustar_circulo(pts: list[tuple[float, float]]) -> tuple[float, float, float]:
    """Ajuste algebraico (Kasa) de un círculo a una nube de puntos."""
    a = np.asarray(pts, dtype=float)
    x, y = a[:, 0], a[:, 1]
    A = np.column_stack([x, y, np.ones_like(x)])
    b = -(x * x + y * y)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    D, E, F = sol
    cx, cz = -D / 2.0, -E / 2.0
    r = math.sqrt(max(cx * cx + cz * cz - F, 0.0))
    return cx, cz, r


def extraer_arcos(page, tf: Transform, prefijo: str) -> list[dict]:
    """Curvas 'c' encadenadas y ajustadas a círculo dentro del área."""
    out: list[dict] = []
    for d in page.get_drawings():
        if _is_grey(d.get("fill")):
            continue
        if (d.get("layer") or "") in CAPAS_IGNORADAS:
            continue
        curvas = [it for it in d["items"] if it[0] == "c"]
        if not curvas:
            continue
        col = [round(float(c), 3) for c in (d.get("color") or (0.0, 0.0, 0.0))]

        # Encadenar curvas consecutivas (fin de una ~ inicio de la siguiente).
        cadenas, actual = [], []
        for it in curvas:
            ini = tf.to_m(it[1].x, it[1].y)
            fin = tf.to_m(it[4].x, it[4].y)
            ctrl = (tf.to_m(it[2].x, it[2].y), tf.to_m(it[3].x, it[3].y))
            if actual and math.dist(actual[-1][1], ini) > 0.01:
                cadenas.append(actual)
                actual = []
            actual.append((ini, fin, ctrl))
        if actual:
            cadenas.append(actual)

        for cadena in cadenas:
            pts: list[tuple[float, float]] = []
            for ini, fin, (c1, c2) in cadena:
                for k in range(9):
                    pts.append(_bezier(ini, c1, c2, fin, k / 8.0))
            if len(pts) < 4 or not all(_in_area(p) for p in pts):
                continue
            cx, cz, r = ajustar_circulo(pts)
            if r <= 0.01 or r > 20:
                continue
            ini, fin = cadena[0][0], cadena[-1][1]
            a0 = math.degrees(math.atan2(ini[1] - cz, ini[0] - cx))
            a1 = math.degrees(math.atan2(fin[1] - cz, fin[0] - cx))
            barrido = (a1 - a0) % 360
            barrido = min(barrido, 360 - barrido)
            out.append({
                "cx": round(cx, 3), "cz": round(cz, 3), "radius": round(r, 3),
                "start_angle": round(a0, 1), "end_angle": round(a1, 1),
                "p0": [round(ini[0], 3), round(ini[1], 3)],
                "p1": [round(fin[0], 3), round(fin[1], 3)],
                "barrido": round(barrido, 1),
                "colour": col,
                "puerta_probable": bool(0.55 <= r <= 1.05 and 70 <= barrido <= 110),
            })
    out.sort(key=lambda a: (a["cz"], a["cx"]))
    for n, a in enumerate(out, start=1):
        a["id"] = f"{prefijo}A{n}"
    orden = ["id", "cx", "cz", "radius", "start_angle", "end_angle",
             "barrido", "p0", "p1", "puerta_probable"]
    return [{k: a[k] for k in orden} for a in out]


# ── etiquetas ───────────────────────────────────────────────────────────────

def extraer_etiquetas(page, tf: Transform) -> list[dict]:
    out = []
    for w in page.get_text("words"):
        x0, y0, x1, y1, texto = w[0], w[1], w[2], w[3], w[4]
        p = tf.to_m((x0 + x1) / 2, (y0 + y1) / 2)
        if not _in_area(p):
            continue
        if not texto.strip():
            continue
        out.append({"texto": texto, "x": round(p[0], 3), "z": round(p[1], 3)})
    out.sort(key=lambda e: (e["z"], e["x"]))
    return out


# ── estancias del plano de cotas ────────────────────────────────────────────

def extraer_estancias(etiquetas: list[dict]) -> list[dict]:
    """Empareja cada superficie ('x,x' + 'm2') con su nombre (arriba) y su
    altura ('h=' + 'x,xx' abajo), recorriendo hacia abajo en z."""
    palabras = [(e["x"], e["z"], e["texto"]) for e in etiquetas]
    idx_m2 = [(x, z) for x, z, t in palabras if t == TEXTO_M2]

    areas = []
    for x, z, t in palabras:
        if not NUM_RE.match(t) or ("," not in t and "." not in t):
            continue
        if not any(abs(mx - x) < 0.5 and abs(mz - z) < 0.05 for mx, mz in idx_m2):
            continue
        areas.append((x, z, float(t.replace(",", "."))))
    areas.sort(key=lambda a: (a[1], a[0]))

    # alturas: palabra 'h=' y el número inmediatamente a su derecha.
    alturas = []
    for x, z, t in palabras:
        if t != "h=":
            continue
        cerca = [(abs(nx - x), nz, nt) for nx, nz, nt in palabras
                 if abs(nz - z) < 0.05 and 0.02 < nx - x < 0.6 and NUM_RE.match(nt)]
        if cerca:
            _, nz, nt = min(cerca)
            alturas.append((x, z, float(nt.replace(",", "."))))

    def nombre_de(ax, az):
        toks = []
        for x, z, t in palabras:
            if not (az - 0.65 <= z <= az - 0.03):
                continue
            if abs(x - ax) > 0.7:
                continue
            if t in UNIDADES or t in (TEXTO_M2,):
                continue
            if NUM_RE.match(t) and len(t) > 1:
                continue
            toks.append((z, x, t))
        if not toks:
            return None
        toks.sort()
        return " ".join(t for _, _, t in toks)

    estancias = []
    for ax, az, area in areas:
        nombre = nombre_de(ax, az)
        if not nombre:
            continue
        altura = None
        for hx, hz, hv in alturas:
            if abs(hz - (az + 0.16)) <= 0.13 and abs(hx - ax) <= 0.6:
                altura = hv
                break
        estancias.append({"nombre": nombre, "area_m2": round(area, 2),
                          "altura_m": round(altura, 2) if altura is not None else None,
                          "x": round(ax, 3), "z": round(az, 3)})
    return estancias


# ── dibujo de depuración ────────────────────────────────────────────────────

class Lienzo:
    def __init__(self, x0: float, x1: float, z0: float, z1: float, ancho: int):
        self.x0, self.z0 = x0, z0
        self.s = (ancho - 1) / (x1 - x0)
        self.w = ancho
        self.h = max(1, int(round((z1 - z0) * self.s)))
        self.img = Image.new("RGB", (self.w, self.h), (255, 255, 255))
        self.dr = ImageDraw.Draw(self.img, "RGBA")
        self.font = ImageFont.truetype(str(FONT_BOLD), 22)
        self.font_s = ImageFont.truetype(str(FONT_REG), 16)
        self.font_c = ImageFont.truetype(str(FONT_BOLD), 13)
        self._grid(x0, x1, z0, z1)

    def px(self, p: tuple[float, float]) -> tuple[float, float]:
        return ((p[0] - self.x0) * self.s, (p[1] - self.z0) * self.s)

    def _grid(self, x0: float, x1: float, z0: float, z1: float) -> None:
        for gx in range(int(math.floor(x0)), int(math.ceil(x1)) + 1):
            a = self.px((gx, z0))
            b = self.px((gx, z1))
            self.dr.line([a, b], fill=COL_EJE if gx == 0 else COL_GRID, width=1)
            if -5 <= gx <= 11:
                self.dr.text((a[0] + 3, 3), str(gx), fill=(120, 120, 120), font=self.font_c)
        for gz in range(int(math.floor(z0)), int(math.ceil(z1)) + 1):
            a = self.px((x0, gz))
            b = self.px((x1, gz))
            self.dr.line([a, b], fill=COL_EJE if gz == 0 else COL_GRID, width=1)
            if -5 <= gz <= 5:
                self.dr.text((3, a[1] + 2), str(gz), fill=(120, 120, 120), font=self.font_c)

    def muros(self, muros):
        for m in muros:
            self.dr.polygon([self.px(p) for p in m["pts"]], fill=COL_MURO + (255,))

    def segmentos(self, segs):
        for s in segs:
            self.dr.line([self.px(s["p0"]), self.px(s["p1"])], fill=COL_SEG, width=1)

    def rects(self, rects):
        for r in rects:
            a = self.px((r["x0"], r["z0"]))
            b = self.px((r["x1"], r["z1"]))
            self.dr.rectangle([a, b], outline=COL_RECT, width=3)
            c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            self.dr.text((c[0], c[1]), r["id"], fill=COL_RECT, font=self.font, anchor="mm",
                         stroke_width=3, stroke_fill=(255, 255, 255))

    def arcos(self, arcos):
        for a in arcos:
            c = self.px((a["cx"], a["cz"]))
            rr = a["radius"] * self.s
            self.dr.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr],
                            outline=COL_ARCO, width=2)
            col = (120, 0, 0) if a["puerta_probable"] else (170, 60, 60)
            self.dr.text((c[0], c[1] - 4), f'{a["id"]} r={a["radius"]:.2f}',
                         fill=col, font=self.font, anchor="ms",
                         stroke_width=3, stroke_fill=(255, 255, 255))

    def etiquetas(self, etiquetas):
        for e in etiquetas:
            p = self.px((e["x"], e["z"]))
            self.dr.text(p, e["texto"], fill=COL_ETIQ, font=self.font,
                         anchor="lm", stroke_width=3, stroke_fill=(255, 255, 255))

    def estancias(self, estancias):
        for e in estancias:
            p = self.px((e["x"], e["z"] - 0.55))
            txt = e["nombre"]
            if e["area_m2"] is not None:
                txt += f' {e["area_m2"]:.1f}m2'
            if e["altura_m"] is not None:
                txt += f' h={e["altura_m"]:.2f}m'
            self.dr.text(p, txt, fill=COL_ESTANCIA, font=self.font_s,
                         anchor="lm", stroke_width=3, stroke_fill=(255, 255, 255))

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.img.save(path)


# ── utilidades de salida ────────────────────────────────────────────────────

def cargar_muros() -> list[dict]:
    try:
        data = json.loads(PLANOS3D.read_text(encoding="utf-8"))
        return data.get("muros", [])
    except (OSError, ValueError):
        return []


def resumen(salida: dict, tf: Transform) -> str:
    return (f"  {salida}: cx={tf.cx:.2f}  cz={tf.cz:.2f}")


def nearest_label(arco: dict, etiquetas: list[dict]):
    """Etiqueta de puerta (P-label) más próxima al centro del arco."""
    mejor, dist = None, None
    for e in etiquetas:
        if not P_LABEL_RE.match(e["texto"]):
            continue
        d = math.hypot(e["x"] - arco["cx"], e["z"] - arco["cz"])
        if dist is None or d < dist:
            mejor, dist = e["texto"], d
    return mejor, dist


def main() -> int:
    print("Midiendo carpintería interior y cotas...")

    tf_carp = Transform(PDF_CARPINTERIA)
    tf_cotas = Transform(PDF_COTAS)

    for tf, nombre in ((tf_carp, "carpinteria"), (tf_cotas, "cotas")):
        assert abs(tf.cx - 558.67) <= 0.05, f"{nombre}: cx={tf.cx}"
        assert abs(tf.cz - 384.06) <= 0.05, f"{nombre}: cz={tf.cz}"

    print("Alineación:")
    print(resumen("PE/I.06 carpinteria", tf_carp))
    print(resumen("PE/A.03 cotas     ", tf_cotas))

    paginas = {
        "carpinteria": (tf_carp, "R", ""),
        "cotas": (tf_cotas, "C", "C"),
    }
    bloque = {}
    for clave, (tf, pr, pa) in paginas.items():
        pdf = PDF_CARPINTERIA if clave == "carpinteria" else PDF_COTAS
        segs = extract_segments(tf.page, tf)
        rects = detectar_rects(segs, pr)
        arcos = extraer_arcos(tf.page, tf, pa)
        etiq = extraer_etiquetas(tf.page, tf)
        planos = [{k: s[k] for k in ("p0", "p1", "width", "colour")}
                  for s in segs]
        bloque[clave] = {"segmentos": planos, "rects": rects,
                         "arcos": arcos, "etiquetas": etiq}
        print(f"{clave} ({pdf.name}): {len(segs)} segmentos, {len(rects)} rects, "
              f"{len(arcos)} arcos, {len(etiq)} etiquetas")

    estancias = extraer_estancias(bloque["cotas"]["etiquetas"])
    print(f"estancias_plano: {len(estancias)}")

    print("Puertas probables (arcos):")
    for a in bloque["carpinteria"]["arcos"]:
        if not a["puerta_probable"]:
            continue
        etq, d = nearest_label(a, bloque["carpinteria"]["etiquetas"])
        dtxt = f"{d:.2f} m" if d is not None else "n/a"
        print(f'  {a["id"]}  centro=({a["cx"]:6.2f},{a["cz"]:6.2f})  '
              f'r={a["radius"]:.2f} m  etiqueta={etq}  dist={dtxt}')

    print("estancias_plano:")
    for e in estancias:
        alt = f'{e["altura_m"]:.2f} m' if e["altura_m"] is not None else "  -  "
        print(f'  {e["nombre"]:22s} {e["area_m2"]:6.2f} m2  h={alt:6s}  '
              f'({e["x"]:6.2f},{e["z"]:6.2f})')

    data = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "fuente": ["Planos/PE_carpinteria_interior.pdf", "Planos/PE_planta_cotas.pdf"],
        "transform": {"cx": round(tf_carp.cx, 2), "cz": round(tf_carp.cz, 2),
                      "pt_por_m": round(g.PT_PER_M, 2)},
        "carpinteria": bloque["carpinteria"],
        "cotas": {k: v for k, v in bloque["cotas"].items()},
        "estancias_plano": estancias,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    muros = cargar_muros()
    x0, x1, z0, z1 = VISTA
    escenas = [
        (OUT_DEBUG, "carpinteria", bloque["carpinteria"], None, x0, x1, 3200),
        (OUT_DEBUG_OESTE, "carpinteria", bloque["carpinteria"], None, x0, 0.5, 2800),
        (OUT_DEBUG_ESTE, "carpinteria", bloque["carpinteria"], None, -0.5, x1, 2800),
        (OUT_DEBUG_COTAS, "cotas", bloque["cotas"], estancias, x0, x1, 3200),
    ]
    for path, _clave, blq, est, cx0, cx1, ancho in escenas:
        li = Lienzo(cx0, cx1, z0, z1, ancho)
        li.muros(muros)
        li.segmentos(blq["segmentos"])
        li.rects(blq["rects"])
        li.arcos(blq["arcos"])
        li.etiquetas(blq["etiquetas"])
        if est:
            li.estancias(est)
        li.save(path)
        print(f"escrito {path.relative_to(ROOT)}  ({li.w}x{li.h})")

    print(f"escrito {OUT_JSON.relative_to(ROOT)}")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
