#!/usr/bin/env python3
"""
Dibuja los planos de los informes ARQUITECTO_CRITICA_PE_A02 y
ARQUITECTO_ALTERNATIVA_PE_A02B (sin cajetín: no lleva datos del cliente):

  informes/img/pe_a02_hallazgos.png   PE.A.02 con los hallazgos numerados
  informes/img/alt_b_planta.png       Alternativa B (evolución del PE.A.02)
  informes/img/alt_b_plus_planta.png  Variante B+ (cocina con ventana)

La envolvente (muros gruesos, pilares, huecos) sale de la geometría vectorial
de Planos/distribución.pdf, igual que data/planos3d.json. Todo lo demás
(tabiques, puertas, mobiliario) está definido aquí en metros de modelo
(x = este, z = sur).

Requiere: pymupdf, pillow
Uso:  python3 scripts/dibujar_alternativa.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar_geometria3d as g  # noqa: E402

OUT = ROOT / "informes" / "img"
PPM = 110            # px por metro en el plano final
SS = 2               # supersampling
X0, Z0, X1, Z1 = -8.7, -4.9, 9.5, 4.9
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# ---------------------------------------------------------------- envolvente
def cargar_envolvente():
    page = pymupdf.open(g.PDF)[0]
    fn = g.vis_transform(page)
    polys = []
    for d in page.get_drawings():
        f = d.get("fill")
        if f and all(abs(a - g.FILL_MURO[0]) < 0.01 for a in f):
            polys += g.polygon_points(d, fn)
    allp = [p for poly in polys for p in poly]
    cx = (min(p[0] for p in allp) + max(p[0] for p in allp)) / 2
    cz = (min(p[1] for p in allp) + max(p[1] for p in allp)) / 2
    return [[((x - cx) / g.PT_PER_M, (z - cz) / g.PT_PER_M) for x, z in poly] for poly in polys], cx, cz


def es_envolvente(poly):
    xs = [p[0] for p in poly]
    zs = [p[1] for p in poly]
    w, h = max(xs) - min(xs), max(zs) - min(zs)
    if min(w, h) < 0.13:
        return False
    # trasdosado nuevo de 16 cm del baño de la ducha: no es estructura
    return not (abs(min(xs) + 0.64) < 0.03 and abs(max(xs) + 0.12) < 0.03)


# --------------------------------------------------------------------- dibujo
class Lienzo:
    def __init__(self):
        self.w = int((X1 - X0) * PPM * SS)
        self.h = int((Z1 - Z0) * PPM * SS)
        self.im = Image.new("RGB", (self.w, self.h), "white")
        self.d = ImageDraw.Draw(self.im)
        self.f = lambda s: ImageFont.truetype(FONT, int(s * SS))
        self.fb = lambda s: ImageFont.truetype(FONT_B, int(s * SS))

    def p(self, x, z):
        return ((x - X0) * PPM * SS, (z - Z0) * PPM * SS)

    def poly(self, pts, fill=None, outline=None, w=1):
        self.d.polygon([self.p(*q) for q in pts], fill=fill, outline=outline, width=max(1, int(w * SS)) if outline else 0)

    def rect(self, x0, z0, x1, z1, fill=None, outline=None, w=1):
        self.d.rectangle([*self.p(x0, z0), *self.p(x1, z1)], fill=fill, outline=outline, width=max(1, int(w * SS)))

    def line(self, pts, fill="black", w=1, dash=0):
        pp = [self.p(*q) for q in pts]
        if not dash:
            self.d.line(pp, fill=fill, width=int(w * SS))
            return
        for (ax, ay), (bx, by) in zip(pp, pp[1:]):
            L = math.hypot(bx - ax, by - ay)
            n = max(1, int(L / (dash * SS)))
            for i in range(0, n, 2):
                t0, t1 = i / n, min(1, (i + 1) / n)
                self.d.line([(ax + (bx - ax) * t0, ay + (by - ay) * t0),
                             (ax + (bx - ax) * t1, ay + (by - ay) * t1)], fill=fill, width=int(w * SS))

    def circ(self, x, z, r, fill=None, outline=None, w=1):
        cx, cy = self.p(x, z)
        R = r * PPM * SS
        self.d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=fill, outline=outline, width=int(w * SS))

    def txt(self, x, z, s, size=11, color=(40, 40, 40), bold=False, anchor="mm"):
        font = self.fb(size) if bold else self.f(size)
        cx, cy = self.p(x, z)
        self.d.multiline_text((cx, cy), s, font=font, fill=color, anchor=anchor, align="center",
                              spacing=2 * SS)

    def marca(self, x, z, n, color=(200, 30, 30)):
        self.circ(x, z, 0.17, fill=color, outline="white", w=1.5)
        self.txt(x, z, n, size=10, color="white", bold=True)

    def guardar(self, ruta):
        im = self.im.resize((self.w // SS, self.h // SS), Image.LANCZOS)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        im.save(ruta, optimize=True)
        print("escrito", ruta.relative_to(ROOT), im.size)


def arco_puerta(c, hx, hz, dx, dz, nx, nz, ancho, color=(70, 70, 70)):
    """Hoja abatible a 90°: bisagra (hx,hz), hoja cerrada hacia (dx,dz), abre hacia (nx,nz)."""
    a0 = math.atan2(dz, dx)
    a1 = math.atan2(nz, nx)
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    pts = [(hx + ancho * math.cos(a0 + da * t / 20), hz + ancho * math.sin(a0 + da * t / 20)) for t in range(21)]
    c.line([(hx, hz), (hx + nx * ancho, hz + nz * ancho)], fill=color, w=1.4)
    c.line(pts, fill=color, w=0.8)


def corredera(c, x0, z0, x1, z1, color=(70, 70, 70)):
    c.rect(x0, z0, x1, z1, fill=(235, 235, 235), outline=color, w=1)


# ----------------------------------------------------------- base compartida
def base(env, titulo, ventanas=True):
    c = Lienzo()
    for poly in env:
        if es_envolvente(poly):
            c.poly(poly, fill=(205, 205, 205))
    if ventanas:
        azul = (90, 130, 190)
        # huecos de fachada (ventanas.json / PE.I.05)
        for xa, za, xb, zb in [(7.96, 0.50, 7.96, 3.48), (7.96, -2.58, 7.96, -1.22),
                               (-4.87, 3.0, -3.69, 3.0), (-2.9, 3.0, -1.9, 3.0),
                               (-7.19, -3.34, -6.24, -3.34), (-1.16, 4.4, 0.08, 4.4)]:
            c.line([(xa, za), (xb, zb)], fill=azul, w=2)
            if xa == xb:
                c.line([(xa + 0.08, za), (xb + 0.08, zb)], fill=azul, w=1)
            else:
                c.line([(xa, za + 0.06), (xb, zb + 0.06)], fill=azul, w=1)
        c.line([(-1.16, 2.9), (-1.16, 4.3)], fill=azul, w=1)       # V04 (galería, oeste)
        c.line([(8.23, 0.08), (8.23, 3.88), (8.86, 3.88), (8.86, 0.08), (8.23, 0.08)], fill=(140, 140, 140), w=1)
    c.txt(X0 + 0.15, Z0 + 0.25, titulo, size=15, bold=True, anchor="lm")
    return c


def tab(c, x0, z0, x1, z1):
    c.rect(x0, z0, x1, z1, fill=(55, 55, 55))


def mueble(c, x0, z0, x1, z1, etiqueta="", fill=(246, 244, 240), size=7):
    c.rect(x0, z0, x1, z1, fill=fill, outline=(95, 95, 95), w=0.8)
    if etiqueta:
        c.txt((x0 + x1) / 2, (z0 + z1) / 2, etiqueta, size=size, color=(90, 90, 90))


def cama(c, x0, z0, x1, z1, horizontal=False):
    mueble(c, x0, z0, x1, z1, "", fill=(250, 248, 244))
    if not horizontal:   # cabecero al norte
        c.line([(x0, z0 + 0.45), (x1, z0 + 0.45)], fill=(150, 150, 150), w=0.8)
        mid = (x0 + x1) / 2
        c.rect(x0 + 0.06, z0 + 0.05, mid - 0.04, z0 + 0.40, outline=(150, 150, 150))
        c.rect(mid + 0.04, z0 + 0.05, x1 - 0.06, z0 + 0.40, outline=(150, 150, 150))


def sombra_techo(c, x0, z0, x1, z1):
    c.rect(x0, z0, x1, z1, fill=(250, 214, 96))


# ====================================================== ALTERNATIVA B
def dibujar_b(env, plus=False):
    c = base(env, "ALTERNATIVA B+ · cocina con ventana (variante)" if plus else "ALTERNATIVA B · evolución del PE.A.02")
    # ---- tabiquería (0,10 m) que se mantiene en su sitio
    for r in [(-4.11, -3.24, -4.00, -1.44), (-4.11, -1.54, -2.63, -1.44), (-1.81, -1.54, 1.85, -1.44),
              (-1.30, -2.94, -1.25, -1.44), (-0.99, -3.24, -0.93, -1.44),
              (1.75, -3.24, 1.85, -2.41), (1.75, -1.59, 1.85, -1.37), (1.75, -0.57, 1.85, -0.42),
              (1.75, -0.52, 7.88, -0.42), (4.07, -3.18, 4.15, -1.32),
              (-7.55, -0.52, -4.42, -0.42), (-4.72, -1.54, -4.61, -1.37), (-4.72, -0.57, -4.61, -0.42),
              (-3.62, -0.52, -3.53, -0.42), (-2.73, -0.52, -1.62, -0.42),
              (-3.62, -0.42, -3.53, 2.88), (0.08, 2.44, 0.81, 2.54)]:
        tab(c, *r)
    if not plus:
        tab(c, -1.62, -0.42, -1.53, 2.44)          # estudio | cocina
    else:
        tab(c, -1.62, -0.42, -1.53, -0.30)         # solo el arranque junto al pasillo
    # trasdosado del baño de la ducha (nicho WC) y del inodoro del baño 2 quedan dentro de cada baño

    # ---- techos con oscuro (tira LED) en zonas clave
    sombra_techo(c, 3.77, -0.42, 7.85, -0.36)      # pared TV
    sombra_techo(c, 4.15, -3.24, 7.85, -3.20)      # cabecero

    # ---- puertas
    arco_puerta(c, 1.754, -1.644, 0, -1, -1, 0, 0.72)               # P02 baño ducha (desde vestidor)
    corredera(c, -2.63, -1.57, -1.81, -1.41)                         # P04 baño bañera
    arco_puerta(c, -4.707, -0.624, 0, -1, -1, 0, 0.72)               # P07 dorm 3
    arco_puerta(c, -3.676, -0.424, -1, 0, 0, 1, 0.72)                # P06 dorm 2
    if not plus:
        arco_puerta(c, -3.475, -0.424, 1, 0, 0, 1, 0.72)             # P05 estudio
    arco_puerta(c, -1.576, -0.574, 0, -1, -1, 0, 0.90, color=(30, 90, 160))  # P03 acústica (hoja 0,90)
    arco_puerta(c, 1.854, -0.624, 0, -1, 1, 0, 0.72)                 # P01 suite
    corredera(c, 4.15, -2.12, 4.22, -1.32)                           # corredera suite (panel roble sobre carril)
    c.line([(4.15, -2.12), (4.15, -0.52)], fill=(30, 90, 160), w=0.8, dash=4)
    corredera(c, -0.72, 2.44, 0.08, 2.54)                            # PL corredera lavadero
    c.line([(0.08, 2.58), (-0.82, 2.58)], fill=(30, 90, 160), w=0.8, dash=4)
    arco_puerta(c, 0.815, 4.33, 1, 0, 0, -1, 0.88)                   # PE existente

    # ---- ENTRADA
    mueble(c, 0.32, 2.54, 0.77, 4.30, "ARMARIO\nENTRADA\n2,30 h", fill=(238, 224, 205), size=7)
    c.circ(1.5, 3.2, 0.28, outline=(120, 120, 120))                  # espejo/banco de apoyo (esquema)
    # ---- LAVADERO
    mueble(c, -1.16, 3.70, 0.08, 4.30, "lavadora + secadora\nencimera 0,90", size=6)
    mueble(c, -1.16, 2.9, -0.82, 3.2, "", size=6)
    c.txt(-0.55, 3.2, "LAVADERO\n2,2 m²", size=8, bold=True)
    c.line([(-0.95, 3.4), (-0.2, 3.4)], fill=(60, 130, 200), w=1, dash=5)   # tendedero extensible

    # ---- SUITE
    mueble(c, 1.88, -3.24, 3.50, -2.64, "A01", fill=(238, 224, 205), size=7)
    mueble(c, 3.50, -2.64, 4.07, -1.32, "A02", fill=(238, 224, 205), size=7)
    mueble(c, 1.88, -1.45, 2.40, -0.60, "cajonera\nisla", size=6)
    c.txt(2.85, -1.0, "VESTIDOR\n6,0 m²", size=8, bold=True)
    cama(c, 4.88, -3.18, 6.68, -1.18)
    mueble(c, 4.40, -3.18, 4.84, -2.78, "", size=6)
    mueble(c, 6.72, -3.18, 7.16, -2.78, "", size=6)
    mueble(c, 7.53, -2.76, 7.85, -1.05, "banco", size=6)
    mueble(c, 4.15, -3.18, 4.43, -2.91, "", fill=(238, 224, 205))
    c.txt(5.9, -0.85, "DORMITORIO PRINCIPAL 10,1 m²", size=8, bold=True)
    # baño 1 (ducha)
    c.rect(-0.93, -3.08, -0.12, -1.54, fill=(236, 240, 244), outline=(120, 120, 120))
    c.line([(-0.12, -3.08), (-0.12, -2.49)], fill=(60, 130, 200), w=1.6)          # mampara fija
    c.line([(-0.93, -1.8), (-0.12, -1.8)], fill=(120, 150, 190), w=1, dash=4)      # canal lineal
    mueble(c, 0.14, -3.08, 0.49, -2.55, "", size=6)
    mueble(c, 0.76, -3.24, 1.75, -2.78, "", size=6)
    c.txt(0.55, -2.0, "BAÑO 1\n(suite) 4,3 m²", size=8, bold=True)
    # baño 2 (bañera)
    mueble(c, -4.00, -3.24, -3.31, -1.54, "", fill=(250, 250, 255))
    mueble(c, -3.08, -3.24, -2.73, -2.60, "", size=6)
    mueble(c, -1.77, -2.94, -1.30, -1.54, "", size=6)
    c.txt(-2.65, -2.1, "BAÑO 2\n(familiar) 4,3 m²", size=8, bold=True)

    # ---- ZONA DE NOCHE
    c.txt(-3.15, -0.99, "PASILLO 2,8 m²", size=7, bold=True)
    # dorm 3 (trapecio)
    mueble(c, -4.71, -3.18, -4.11, -1.54, "A04", fill=(238, 224, 205), size=7)
    cama(c, -7.35, -2.58, -6.45, -0.58)
    mueble(c, -7.35, -3.18, -5.25, -2.59, "escritorio", size=6)
    c.txt(-5.9, -1.5, "DORMITORIO 3\n9,1 m²", size=8, bold=True)
    # dorm 2
    mueble(c, -7.04, -0.42, -6.42, 0.78, "A03", fill=(238, 224, 205), size=7)
    cama(c, -6.42, 0.58, -5.52, 2.58)
    mueble(c, -5.80, -0.30, -4.65, 0.10, "cómoda", size=6)
    mueble(c, -4.21, 1.39, -3.62, 2.88, "escritorio", size=6)
    c.txt(-5.1, 1.4, "DORMITORIO 2\n10,7 m²", size=8, bold=True)

    if not plus:
        # estudio: biblioteca de cerezo + escritorio junto a la ventana V06
        mueble(c, -1.94, -0.30, -1.62, 2.40, "biblioteca de cerezo\n(anclada a forjado)", fill=(214, 168, 140), size=6)
        mueble(c, -3.50, 2.28, -1.94, 2.88, "escritorio\nbajo V06", fill=(246, 244, 240), size=6)
        mueble(c, -3.50, 1.10, -3.05, 2.28, "bajos", fill=(214, 168, 140), size=6)
        c.txt(-2.75, 0.55, "ESTUDIO\n6,3 m²", size=8, bold=True)
    else:
        # cocina oeste con ventana V06: fregadero bajo la ventana, placa en frente oeste
        mueble(c, -3.53, -0.30, -2.93, 1.40, "frigo+\ndespensa\n+horno", fill=(238, 224, 205), size=6)
        mueble(c, -3.53, 1.40, -2.93, 2.30, "placa\n+campana", size=6)
        mueble(c, -2.93, 2.28, -1.62, 2.88, "fregadero\nbajo V06", size=6)
        c.line([(-3.2, 1.9), (-3.2, 2.88)], fill=(200, 80, 60), w=1.4, dash=4)       # conducto campana a la pilastra
        c.txt(-2.35, 0.9, "COCINA\n(ala oeste)", size=8, bold=True)

    # ---- COCINA / CENTRO
    c.txt(0.1, -0.95, "calle de paso 1,10 m", size=7, color=(30, 90, 160))
    c.line([(-1.5, -0.88), (1.8, -0.88)], fill=(30, 90, 160), w=1, dash=5)
    if not plus:
        mueble(c, -1.53, -0.34, -0.93, 0.26, "frigo\n60", fill=(238, 224, 205), size=6)
        mueble(c, -1.53, 0.26, -0.93, 0.86, "despensa\n60", fill=(238, 224, 205), size=6)
        mueble(c, -1.53, 0.86, -0.93, 1.66, "fregadero", size=6)
        mueble(c, -1.53, 1.66, -0.93, 2.40, "LV+horno\n+micro", fill=(238, 224, 205), size=6)
        mueble(c, 0.17, 0.0, 0.97, 1.80, "", fill=(70, 70, 70))
        c.txt(0.57, 1.45, "isla", size=6, color="white")
        c.rect(0.33, 0.45, 0.83, 1.05, fill=(30, 30, 30))                     # inducción 0,60 × 0,52 con extractor
        c.txt(0.58, 0.75, "ind.\n+extr.", size=5.5, color="white")
        for zt in (0.30, 0.90, 1.50):
            c.circ(1.17, zt, 0.19, fill=(60, 60, 60))
        c.txt(0.0, 2.15, "COCINA\n9,4 m² + calle", size=8, bold=True)
    else:
        mueble(c, 0.17, 0.0, 0.97, 1.80, "", fill=(70, 70, 70))
        c.txt(0.57, 0.9, "isla\n(prep +\ndesayuno)", size=6, color="white")
        for zt in (0.30, 0.90, 1.50):
            c.circ(1.17, zt, 0.19, fill=(60, 60, 60))
        c.txt(-0.45, 1.2, "COCINA-COMEDOR", size=8, bold=True)

    # ---- SALÓN
    mueble(c, 3.44, -0.36, 3.77, -0.10, "", fill=(150, 150, 150))                   # pilar visto
    mueble(c, 4.32, -0.36, 7.32, 0.04, "M05 TV", fill=(238, 224, 205), size=6)
    mueble(c, 2.00, -0.36, 3.20, 0.05, "aparador", fill=(238, 224, 205), size=6)
    mueble(c, 2.67, 1.19, 3.57, 3.00, "mesa 0,90×1,80\n(ext. 2,60)", size=6)
    for (x0, z0, x1, z1) in [(2.37, 1.52, 2.67, 1.97), (2.37, 2.23, 2.67, 2.67), (3.57, 1.52, 3.87, 1.97),
                             (3.57, 2.23, 3.87, 2.67), (2.89, 0.89, 3.34, 1.19), (2.89, 3.00, 3.34, 3.30)]:
        mueble(c, x0, z0, x1, z1)
    mueble(c, 4.75, 2.62, 7.05, 3.41, "sofá 3 pl.", size=7)
    mueble(c, 5.13, 1.44, 6.52, 2.08, "")
    c.circ(7.38, 1.94, 0.42, outline=(95, 95, 95))
    if plus:
        mueble(c, 2.40, 3.20, 7.60, 3.58, "biblioteca-escritorio (cerezo)", fill=(214, 168, 140), size=6)
    c.txt(5.0, 0.85, "SALÓN · COMEDOR 24,0 m²", size=8, bold=True)
    c.txt(8.54, 2.0, "balcón", size=6, color=(120, 120, 120))
    c.txt(1.05, 1.95, "", size=6)
    c.txt(1.28, 2.95, "RECIBIDOR\n2,7 m²", size=7, bold=True, color=(30, 30, 30))
    return c


def anotar_pe_a02():
    """PE.A.02 (raster del proyecto) recortado a la vivienda, con marcas de hallazgos."""
    env, cx, cz = cargar_envolvente()
    K = 4963 / 1191
    im = Image.open(g.PNG).convert("RGB")

    def px(x, z):
        return ((cx + x * g.PT_PER_M) * K, (cz + z * g.PT_PER_M) * K)

    ax, az = px(-8.6, -4.9)
    bx, bz = px(9.4, 4.9)
    im = im.crop((int(ax), int(az), int(bx), int(bz)))
    esc = 2000 / im.width
    im = im.resize((2000, int(im.height * esc)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT_B, 17)
    rojo, naranja, azul = (200, 30, 30), (225, 120, 20), (40, 90, 170)
    marcas = [
        ("D1", 0.15, 1.05, rojo), ("D2", 0.15, -0.95, rojo), ("D3", 0.57, 0.45, rojo),
        ("D4", 3.0, -0.95, naranja), ("D5", 1.05, 3.5, naranja), ("D6", -1.58, -0.98, naranja),
        ("D7", -3.6, -0.98, naranja), ("D8", -2.57, 1.7, naranja), ("D9", -5.9, -2.0, naranja),
        ("D9", -5.3, 1.5, naranja), ("D10", -2.2, -0.98, naranja), ("D11", -0.54, 3.5, azul),
        ("I1", -2.7, -2.5, rojo), ("M5", 3.6, -0.23, naranja), ("M6", 3.12, 2.1, naranja),
        ("M8", 8.0, 2.0, azul),
    ]
    for etq, x, z, col in marcas:
        X, Z = px(x, z)
        X, Z = (X - ax) * esc, (Z - az) * esc
        r = 21
        d.ellipse([X - r, Z - r, X + r, Z + r], fill=col, outline="white", width=3)
        d.text((X, Z), etq, font=f if len(etq) < 3 else ImageFont.truetype(FONT_B, 14), fill="white", anchor="mm")
    ruta = OUT / "pe_a02_hallazgos.png"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    im.save(ruta, optimize=True)
    print("escrito", ruta.relative_to(ROOT), im.size)


def main():
    env, _cx, _cz = cargar_envolvente()
    anotar_pe_a02()
    dibujar_b(env).guardar(OUT / "alt_b_planta.png")
    dibujar_b(env, plus=True).guardar(OUT / "alt_b_plus_planta.png")


if __name__ == "__main__":
    main()



