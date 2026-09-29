#!/usr/bin/env python3
"""
Revisa la colocación del mobiliario de data/mobiliario.glb contra el PE.A.02.

No necesita Blender: lee el GLB exportado (data/mobiliario.glb) y la geometría
vectorial del plano (planos3d.json, puertas.json, ventanas.json) y comprueba:

  1. que ninguna pieza se meta en un muro (salvo los elementos de pared),
  2. que cada pieza quede dentro de su estancia (unión de estancias) y que su
     centro caiga en la estancia que le toca por nombre,
  3. que nada invada el barrido de las puertas abatibles ni los 0,8 m libres
     delante de las correderas,
  4. que nada alto tape una ventana por encima del antepecho; los huecos que
     en realidad son puertas (la V05 es la boca del casoneto, con la P04) no
     generan banda,
  5. que no haya piezas solapadas (con excepciones: cojín sobre sofá, colchón
     sobre cama, frentes sobre el mueble…),
  6. pasos mínimos delante de armarios y cocina: 0,9 m medidos desde el muro
     al que están anclados (0,5 m en el d3_armario, imposible en un cuarto de
     1,85 m) y 0,6 m junto a la cama.

Escribe data/imagenes/mobiliario_debug.png (planta con las piezas y los
incumplimientos en rojo), exporta las huellas de colisión a data/colisiones.json
(las usa el paseo del visor 3D) y termina con error si algo falla.

Uso: python3 scripts/revisar_mobiliario.py
"""
from __future__ import annotations

import json
import math
import struct
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PLAN = json.loads((DATA / "planos3d.json").read_text(encoding="utf-8"))
PUERTAS = json.loads((DATA / "puertas.json").read_text(encoding="utf-8"))
VENTANAS = json.loads((DATA / "ventanas.json").read_text(encoding="utf-8"))
GLB = DATA / "mobiliario.glb"
DEBUG = DATA / "imagenes" / "mobiliario_debug.png"
COLISIONES = DATA / "colisiones.json"

TOL_FUERA = 0.12        # margen para considerar una pieza dentro de la vivienda
TOL_MURO = 0.02         # penetración admitida en un muro (m)
TOL_PEGADO = 0.08       # los espejos deben estar pegados a un muro
PASO = 0.9              # paso libre delante de armarios y cocina (m)
PASO_CAMA = 0.6         # paso libre junto a la cama (m)
FONDO_VENTANA = 0.8     # profundidad de la banda que tapa una ventana (m)
FONDO_CORREDERA = 0.8   # franja libre delante de una corredera (m)

# ── plan: polígonos ─────────────────────────────────────────────────────────


def limpiar(pts):
    out = []
    for x, z in pts:
        p = (float(x), float(z))
        if not out or abs(p[0] - out[-1][0]) > 1e-9 or abs(p[1] - out[-1][1]) > 1e-9:
            out.append(p)
    if len(out) > 2 and out[0] == out[-1]:
        out.pop()
    return out


ESTANCIAS = {e["id"]: limpiar(e["pts"]) for e in PLAN["estancias"]}
MUROS = [limpiar(m["pts"]) for m in PLAN["muros"] if m["tipo"] != "vidrio"]
for sep in PUERTAS.get("separadores", []):
    for t in sep["tramos"]:
        (ax, az), (bx, bz) = t["de"], t["a"]
        dx, dz = bx - ax, bz - az
        L = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / L * 0.015, dx / L * 0.015
        MUROS.append([(ax + nx, az + nz), (bx + nx, bz + nz),
                      (bx - nx, bz - nz), (ax - nx, az - nz)])


def en_poligono(p, poly):
    x, z = p
    dentro = False
    for i in range(len(poly)):
        x0, z0 = poly[i]
        x1, z1 = poly[(i + 1) % len(poly)]
        if (z0 > z) != (z1 > z) and x < (x1 - x0) * (z - z0) / (z1 - z0) + x0:
            dentro = not dentro
    return dentro


def en_alguna(p, polys):
    return any(en_poligono(p, q) for q in polys)


def punto_a_arista(p, a, b):
    (px, pz), (ax, az), (bx, bz) = p, a, b
    dx, dz = bx - ax, bz - az
    L2 = dx * dx + dz * dz or 1e-12
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L2))
    return (ax + dx * t, az + dz * t)


def dist_a_arista(p, a, b):
    q = punto_a_arista(p, a, b)
    return math.hypot(p[0] - q[0], p[1] - q[1])


def dist_a_poligono(p, poly):
    return min(dist_a_arista(p, poly[i], poly[(i + 1) % len(poly)])
               for i in range(len(poly)))


def dist_a_estancias(p):
    """distancia a la estancia más cercana (0 si está dentro de alguna)"""
    mejor = 1e9
    for poly in ESTANCIAS.values():
        if en_poligono(p, poly):
            return 0.0
        mejor = min(mejor, dist_a_poligono(p, poly))
    return mejor


def _signo(v):
    return (v > 1e-9) - (v < -1e-9)


def _cruce(a, b, c, d):
    def lado(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return _signo(lado(a, b, c)) * _signo(lado(a, b, d)) < 0 and \
        _signo(lado(c, d, a)) * _signo(lado(c, d, b)) < 0


def poligonos_chocan(a, b, tol=0.0):
    for p in a:
        if en_poligono(p, b) and dist_a_poligono(p, b) > tol:
            return True
    for p in b:
        if en_poligono(p, a) and dist_a_poligono(p, a) > tol:
            return True
    for i in range(len(a)):
        for j in range(len(b)):
            if _cruce(a[i], a[(i + 1) % len(a)], b[j], b[(j + 1) % len(b)]):
                return True
    return False


def encoger(poly, tol):
    """Erosiona un polígono convexo `tol` metros hacia dentro (desplazando
    cada arista por su normal interior). Sirve para que los cruces de aristas
    respeten la tolerancia: los muros del modelo invaden ~5 mm el interior y
    las piezas a ras de muro 'chocaban' sin penetrar de verdad. Devuelve [] si
    la erosión se come la pieza (placas más finas que 2·tol)."""
    n = len(poly)
    if n < 3 or tol <= 0:
        return list(poly)
    poly = list(poly)
    # poda de micro-aristas (chaflanes de 4 mm del bisel): sin esto la
    # intersección de aristas desplazadas da resultados sin sentido
    cambio = True
    while cambio and len(poly) > 3:
        cambio = False
        for i in range(len(poly)):
            a, b, c = poly[i - 1], poly[i], poly[(i + 1) % len(poly)]
            l1 = math.hypot(b[0] - a[0], b[1] - a[1])
            l2 = math.hypot(c[0] - b[0], c[1] - b[1])
            ax, az = b[0] - a[0], b[1] - a[1]
            bx, bz = c[0] - a[0], c[1] - a[1]
            L = math.hypot(bx, bz) or 1.0
            if min(l1, l2) < 0.012 and abs(ax * bz - az * bx) / L < 0.012:
                poly.pop(i)
                cambio = True
                break
    n = len(poly)

    def area(p):
        return sum(p[i][0] * p[(i + 1) % len(p)][1] -
                   p[(i + 1) % len(p)][0] * p[i][1]
                   for i in range(len(p))) / 2

    area2 = area(poly)
    sgn = 1.0 if area2 >= 0 else -1.0          # CCW: interior a la izquierda
    rectas = []
    for i in range(n):
        (ax, az), (bx, bz) = poly[i], poly[(i + 1) % n]
        dx, dz = bx - ax, bz - az
        L = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / L * sgn, dx / L * sgn
        rectas.append((ax + nx * tol, az + nz * tol, dx, dz))
    out = []
    for i in range(n):
        x1, z1, dx1, dz1 = rectas[i - 1]
        x2, z2, dx2, dz2 = rectas[i]
        den = dx1 * dz2 - dz1 * dx2
        if abs(den) < 1e-9:
            continue
        t = ((x2 - x1) * dz2 - (z2 - z1) * dx2) / den
        out.append((x1 + dx1 * t, z1 + dz1 * t))
    if len(out) < 3:
        return []
    a1 = area(out)
    if area2 * a1 <= 0 or abs(a1) > abs(area2):   # erosión total: no hay pieza
        return []
    return out


def casco(puntos):
    pts = sorted(set(puntos))
    if len(pts) <= 2:
        return pts

    def cruz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    inf, sup = [], []
    for p in pts:
        while len(inf) >= 2 and cruz(inf[-2], inf[-1], p) <= 0:
            inf.pop()
        inf.append(p)
    for p in reversed(pts):
        while len(sup) >= 2 and cruz(sup[-2], sup[-1], p) <= 0:
            sup.pop()
        sup.append(p)
    return inf[:-1] + sup[:-1]


def rect_poligono(cx, cz, ux, uz, largo, ancho):
    vx, vz = -uz, ux
    return [(cx + ux * largo / 2 + vx * ancho / 2, cz + uz * largo / 2 + vz * ancho / 2),
            (cx - ux * largo / 2 + vx * ancho / 2, cz - uz * largo / 2 + vz * ancho / 2),
            (cx - ux * largo / 2 - vx * ancho / 2, cz - uz * largo / 2 - vz * ancho / 2),
            (cx + ux * largo / 2 - vx * ancho / 2, cz + uz * largo / 2 - vz * ancho / 2)]


# ── GLB: una pieza por nodo ─────────────────────────────────────────────────

class Pieza:
    def __init__(self, nombre, hull, h0, h1, caja):
        self.nombre = nombre
        self.hull = hull
        self.h0 = h0
        self.h1 = h1
        self.caja = caja            # (x0, x1, z0, z1)

    @property
    def centro(self):
        x0, x1, z0, z1 = self.caja
        return ((x0 + x1) / 2, (z0 + z1) / 2)

    def solapa(self, otra, eps=0.025):
        x0, x1, z0, z1 = self.caja
        a0, a1, b0, b1 = otra.caja
        return (min(x1, a1) - max(x0, a0) > eps and
                min(z1, b1) - max(z0, b0) > eps and
                min(self.h1, otra.h1) - max(self.h0, otra.h0) > eps)


def leer_glb(path):
    b = path.read_bytes()
    if b[:4] != b"glTF":
        raise SystemExit(f"{path}: no es un GLB")
    largo = struct.unpack_from("<I", b, 12)[0]
    j = json.loads(b[20:20 + largo])
    off = 20 + largo
    blen, btype = struct.unpack_from("<II", b, off)
    if btype != 0x4E4942:
        raise SystemExit(f"{path}: falta el bloque binario")
    return j, b[off + 8:off + 8 + blen]


def piezas_glb(path=GLB):
    j, binario = leer_glb(path)
    acc, bvs = j["accessors"], j["bufferViews"]
    comp = {5126: ("f", 4), 5123: ("H", 2), 5125: ("I", 4), 5121: ("B", 1)}
    piezas = {}
    for nodo in j["nodes"]:
        if "mesh" not in nodo:
            continue
        nombre = nodo.get("name", "")
        pts, h0, h1 = [], 1e9, -1e9
        x0 = z0 = 1e9
        x1 = z1 = -1e9
        for prim in j["meshes"][nodo["mesh"]]["primitives"]:
            a = acc[prim["attributes"]["POSITION"]]
            mn, mx = a["min"], a["max"]
            x0, z0 = min(x0, mn[0]), min(z0, mn[2])
            x1, z1 = max(x1, mx[0]), max(z1, mx[2])
            h0, h1 = min(h0, mn[1]), max(h1, mx[1])
            bv = bvs[a["bufferView"]]
            base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
            fmt, _ = comp[a["componentType"]]
            vals = struct.unpack_from("<" + fmt * (a["count"] * 3), binario, base)
            for i in range(a["count"]):
                pts.append((round(vals[i * 3], 3), round(vals[i * 3 + 2], 3)))
        if pts:
            piezas[nombre] = Pieza(nombre, casco(pts), h0, h1, (x0, x1, z0, z1))
    return piezas


# ── clasificación ───────────────────────────────────────────────────────────

ESTRUCTURA = ("suelo", "techo", "falso_techo_", "tabica_", "rev_", "pav_",
              "muro_", "marco_", "pmarco_", "vidrio_",
              "mont_", "dintel_", "pdintel_", "phoja_", "antepecho_", "rodapie_",
              "dl_disco_", "peto_", "pilar_visto", "cortina_", "ext_", "asset_",
              "b1_azulejo_", "b2_azulejo_")
# elementos pegados a un muro: se admiten los solapes de unos centímetros del
# modelo (encimera, sanitarios, panel de TV…) y se revisan aparte los espejos
EN_PARED = ("cuadro_", "espejo", "tv", "tv_",
            "coc_",
            "b1_", "b2_",
            "ves_", "rec_zapatero", "rec_led_zapatero", "rec_espejo",
            "lav_", "tz_",
            "dp_panelado", "dp_est_", "dp_cabecero", "dp_listones_",
            "dp_mesita_", "dp_banco",
            "d3_a04_", "d3_e02_", "d3_cabecero", "d3_escritorio",
            "d2_a03_", "d2_e01_", "d2_cabecero", "d2_comoda",
            "d2_escritorio",
            "est_bajos_", "est_a_", "est_b_", "aparador_")

PREFIJOS = (
    ("d1_", "dorm-3"), ("d3_", "dorm-3"), ("d2_", "dorm-2"),
    ("est_", "estudio"), ("dp_", "dorm-principal"), ("ves_", "vestidor"),
    ("b1_", "bano-1"), ("b2_", "bano-2"),
    ("rec_", "recibidor"), ("lav_", "lavadero"), ("tz_", "terraza"),
    ("coc_", "cocina"), ("isla", "cocina"), ("placa", "cocina"),
    ("taburete_", "cocina"), ("campana", "cocina"),
    ("tv_", "salon"), ("tv", "salon"),
    ("sofa_", "salon"), ("cojin_", "salon"), ("alfombra", "salon"),
    ("mesa_centro", "salon"), ("butaca", "salon"), ("lampara_", "salon"),
    ("aparador", "salon"), ("cuadro_", "salon"), ("planta", "salon"),
    ("mesa", "salon"), ("silla_", "salon"), ("ceramic", "salon"),
)

# grupos que pueden solaparse entre sí (misma pieza compuesta)
GRUPOS_SOLAPE = (
    ("coc_",),
    ("isla", "isla_cuerpo", "isla_zocalo", "isla_cajon_", "isla_tablero",
     "isla_lateral_", "isla_frontal", "placa", "campana", "taburete_"),
    ("tv", "tv_", "cuadro_", "cuadro_aparador"),
    ("sofa_", "alfombra"),
    ("mesa_comedor", "mesa_comedor_pie_", "silla_"),
    ("lampara_comedor", "lampara_comedor_cable"),
    ("lampara_pie", "lampara_pie_base", "lampara_pant"),
    ("mesa_centro", "mesa_centro_base_"),
    ("butaca_",),
    ("aparador", "aparador_", "cuadro_aparador"),
    ("rec_zapatero", "rec_zapatero_puerta_", "rec_led_zapatero"),
    ("rec_espejo",),
    ("lav_",),
    ("ves_",),
    ("dp_panelado", "dp_est_"),
    ("dp_cama", "dp_colchon", "dp_manta", "dp_almohada_", "dp_cabecero",
     "dp_listones_", "dp_mesita_", "dp_cable_", "dp_colgante_"),
    ("d3_a04_",),
    ("d3_e02_",),
    ("d3_cama", "d3_cama_nido", "d3_colchon", "d3_manta", "d3_almohada",
     "d3_cabecero"),
    ("d3_escritorio", "d3_escritorio_pie_"),
    ("d3_silla", "d3_silla_asiento", "d3_silla_respaldo", "d3_silla_pie_"),
    ("d2_a03_",),
    ("d2_e01_",),
    ("d2_cama", "d2_cama_nido", "d2_colchon", "d2_manta", "d2_almohada",
     "d2_cabecero"),
    ("d2_comoda", "d2_comoda_cajon_", "d2_comoda_unero_"),
    ("d2_escritorio", "d2_escritorio_pie_"),
    ("d2_silla", "d2_silla_asiento", "d2_silla_respaldo", "d2_silla_pie_"),
    ("est_bajos_",),
    ("est_a_",),
    ("est_b_",),
    ("est_peninsula", "est_peninsula_redondeo", "est_peninsula_pie",
     "est_peninsula_base"),
    ("est_silla", "est_silla_asiento", "est_silla_respaldo", "est_silla_pie_"),
    ("b1_",),
    ("b2_",),
    ("tz_",),
)

# paso libre exigido delante de cada pieza (m); d3_armario es la excepción:
# el dormitorio 3 mide 1,85 m y el paso real queda en 0,52 m
PASO_MINIMO = {"ves_a01_cuerpo": 0.9,
               "d3_a04_cuerpo": 0.9, "d2_a03_cuerpo": 0.9,
               "est_a_fondo": 0.9, "est_b_fondo": 0.9,
               "coc_bajo_fregadero": 0.9, "coc_altos": 0.9}

ALTURA_TAPA = 0.35      # por encima del antepecho se considera que tapa

# ── colisiones del visor (data/colisiones.json) ─────────────────────────────
# huellas convexas en planta que usa el paseo del visor 3D (círculo-polígono).
# El campo "g" (salon/resto/base) se conserva informativo: el visor muestra
# todo el mobiliario, así que aplica todas las huellas.
COLISION_H0 = 0.75      # con la base por debajo de esta cota la pieza estorba
COLISION_H1 = 0.35      # y debe llegar al menos a esta altura
COLISION_BLANDAS = ("cojin_", "almohada", "colcha", "colchon", "manta",
                    "funda_", "alfombra")   # suaves: no bloquean el paso
SALON = ("tv_", "tv", "pilar_visto", "sofa_", "cojin_", "alfombra",
         "mesa_centro", "butaca", "aparador", "cuadro_", "coc_", "isla",
         "isla_tapa", "placa", "campana", "lampara_", "planta_", "cortina_")
RESTO = ("d1_", "d2_", "d3_", "dp_", "rec_", "tz_", "mesa", "silla_",
         "taburete_")


def coincide(nombre, patron):
    return nombre.startswith(patron) if patron.endswith("_") else nombre == patron


def es_estructura(nombre):
    return any(coincide(nombre, p) for p in ESTRUCTURA)


def en_lista(nombre, lista):
    return any(coincide(nombre, p) for p in lista)


def _grupo_colision(nombre):
    if nombre.startswith("b1_") or nombre.startswith("b2_"):
        return "resto"
    if en_lista(nombre, SALON):
        return "base"
    if en_lista(nombre, RESTO):
        return "resto"
    return "base"


def colisiones(piezas):
    """Huella de colisión (convexa, en planta) de cada pieza que estorba al
    caminar, con su centro y radio envolvente para el rechazo rápido."""
    out = []
    for nombre, p in sorted(piezas.items()):
        if not (not es_estructura(nombre) or nombre == "pilar_visto"):
            continue
        if len(p.hull) < 3 or p.h0 > COLISION_H0 or p.h1 < COLISION_H1:
            continue
        if any(coincide(nombre, s) for s in COLISION_BLANDAS):
            continue
        pts = [[round(x, 3), round(z, 3)] for x, z in p.hull]
        cx = sum(q[0] for q in pts) / len(pts)
        cz = sum(q[1] for q in pts) / len(pts)
        r = max(math.hypot(q[0] - cx, q[1] - cz) for q in pts)
        out.append({"n": nombre, "g": _grupo_colision(nombre), "p": pts,
                    "c": [round(cx, 3), round(cz, 3)], "r": round(r, 3)})
    return out


def en_pared(nombre):
    return any(coincide(nombre, p) for p in EN_PARED) or "espejo" in nombre


def estancia_de(nombre):
    for pref, eid in PREFIJOS:
        if nombre.startswith(pref):
            return eid
    return None


def mismos_grupo(a, b):
    for grupo in GRUPOS_SOLAPE:
        if any(coincide(a, p) for p in grupo) and any(coincide(b, p) for p in grupo):
            return True
    return False


# ── puertas y ventanas ──────────────────────────────────────────────────────


def sector_abatible(p):
    ancho = p["ancho"]
    cx, cz = p["centro"]
    if p["pared"] == "h":
        # gozne en un extremo; u apunta del gozne al otro jambor
        if p["bisagra"] == "E":
            gozne, u = (cx + ancho / 2, cz), (-1.0, 0.0)
        else:
            gozne, u = (cx - ancho / 2, cz), (1.0, 0.0)
        v = (0.0, 1.0) if p.get("apertura") == "S" else (0.0, -1.0)
    else:
        if p["bisagra"] == "S":
            gozne, u = (cx, cz + ancho / 2), (0.0, -1.0)
        else:
            gozne, u = (cx, cz - ancho / 2), (0.0, 1.0)
        v = (1.0, 0.0) if p.get("apertura") == "E" else (-1.0, 0.0)
    pts = [gozne]
    for i in range(13):
        a = math.pi / 2 * i / 12
        pts.append((gozne[0] + ancho * (math.cos(a) * u[0] + math.sin(a) * v[0]),
                    gozne[1] + ancho * (math.cos(a) * u[1] + math.sin(a) * v[1])))
    return pts


def lado_servido(p, eid):
    cx, cz = p["centro"]
    n = (0.0, 1.0) if p["pared"] == "h" else (1.0, 0.0)
    for s in (1, -1):
        if en_poligono((cx + n[0] * 0.35 * s, cz + n[1] * 0.35 * s), ESTANCIAS[eid]):
            return (n[0] * s, n[1] * s)
    return None


SIRVE = {"P01": "vestidor", "P02": "bano-1", "P03": "pasillo", "P04": "bano-2",
         "P05": "estudio", "P06": "dorm-2", "P07": "dorm-3", "PE": "recibidor",
         "PL": "lavadero"}


def barreras_puertas():
    out = {}
    for p in PUERTAS["puertas"]:
        if p["id"] == "PE":       # entrada existente, sin datos de barrido
            continue
        if p["tipo"] == "corredera":
            n = lado_servido(p, SIRVE.get(p["id"]))
            if not n:
                continue
            cx, cz = p["centro"]
            u = (1.0, 0.0) if p["pared"] == "h" else (0.0, 1.0)
            caja = rect_poligono(cx + n[0] * FONDO_CORREDERA / 2,
                                 cz + n[1] * FONDO_CORREDERA / 2,
                                 u[0], u[1], p["ancho"], FONDO_CORREDERA)
            out[p["id"]] = (p, caja)
        else:
            out[p["id"]] = (p, sector_abatible(p))
    return out


ORIENT_FACHADA = {"norte": "h", "sur": "h", "este": "v", "oeste": "v"}


def bandas_ventanas():
    huecos = VENTANAS["huecos_planos3d"]
    out = []
    for v in VENTANAS["ventanas"]:
        h = v["hueco_plano"]
        # huecos que en realidad son puertas (p. ej. la V05 es la boca del
        # casoneto, que lleva la corredera P04): no tienen banda
        if any(math.hypot(p["centro"][0] - h["centro"][0],
                          p["centro"][1] - h["centro"][1]) < 0.45
               for p in PUERTAS["puertas"]):
            continue
        # ventanales de suelo a techo (V01): el mobiliario a su paso es una
        # decisión de proyecto, no un error
        if v["antepecho_m"] is None and (v["alto_m"] or 0.0) >= 2.0:
            continue
        fachada = (h.get("fachada") or "").split("-")[0]
        # el hueco de planos3d más cercano de la misma fachada da la orientación
        mejor, c = 1e9, None
        for cand in huecos:
            if cand["fachada"].split("-")[0] != fachada:
                continue
            d = math.hypot(cand["centro"][0] - h["centro"][0],
                           cand["centro"][1] - h["centro"][1])
            if d < mejor:
                mejor, c = d, cand
        if c is None:
            # sin hueco vectorial equivalente (p. ej. el esquinero oeste), se usa
            # el centro y la longitud medidos en la planta
            c = {"centro": h["centro"], "longitud_m": h["longitud_m"],
                 "orientacion": ORIENT_FACHADA.get(fachada, "h")}
        cx, cz = c["centro"]
        orient = c.get("orientacion", "v")
        u = (0.0, 1.0) if orient == "v" else (1.0, 0.0)
        n = (1.0, 0.0) if orient == "v" else (0.0, 1.0)
        # una banda por cada lado interior (el ventanal V01 da al salón y a la terraza)
        for s in (1, -1):
            if not en_alguna((cx + n[0] * 0.4 * s, cz + n[1] * 0.4 * s),
                             list(ESTANCIAS.values())):
                continue
            caja = rect_poligono(cx + n[0] * s * FONDO_VENTANA / 2,
                                 cz + n[1] * s * FONDO_VENTANA / 2,
                                 u[0], u[1], max(c["longitud_m"], v["ancho_m"]),
                                 FONDO_VENTANA)
            out.append((v, caja))
    return out


# ── pasos libres ────────────────────────────────────────────────────────────


def libre_desde(origen, dirn, limite, bloqueadores, paso=0.03):
    t = 0.02
    while t <= limite:
        q = (origen[0] + dirn[0] * t, origen[1] + dirn[1] * t)
        if en_alguna(q, MUROS):
            return t
        for o in bloqueadores:
            if o.h0 < 1.8 and en_poligono(q, o.hull):
                return t
        t += paso
    return limite


# ── revisión ────────────────────────────────────────────────────────────────


def revisar():
    piezas = piezas_glb()
    mob = {n: p for n, p in piezas.items() if not es_estructura(n)}
    fallos = []
    en_muro = set()

    for nombre, p in sorted(mob.items()):
        eid = estancia_de(nombre)
        if eid is None:
            fallos.append(("sin-estancia", nombre, "prefijo desconocido"))
            continue
        if not en_pared(nombre):
            hull = encoger(p.hull, TOL_MURO)
            for m in MUROS:
                if poligonos_chocan(hull, m):
                    fallos.append(("muro", nombre, "se mete en un muro"))
                    en_muro.add(nombre)
                    break
            for q in p.hull:
                if dist_a_estancias(q) > TOL_FUERA:
                    fallos.append(("fuera", nombre, "se sale de la vivienda"))
                    break
        if "espejo" in nombre and \
                not any(dist_a_poligono(q, m) <= TOL_PEGADO
                        for q in p.hull for m in MUROS):
            fallos.append(("flota", nombre, "el espejo no tiene muro detrás"))

    for pid, (p, zona) in barreras_puertas().items():
        for nombre, pc in mob.items():
            if poligonos_chocan(pc.hull, zona, tol=0.01):
                modo = "el barrido" if p["tipo"] != "corredera" else "los 0,8 m"
                fallos.append(("puerta", nombre, f"invade {modo} de {pid}"))

    for v, caja in bandas_ventanas():
        antepecho = v["antepecho_m"] if v["antepecho_m"] is not None else 0.0
        for nombre, pc in mob.items():
            if pc.h1 <= antepecho + ALTURA_TAPA:
                continue
            if poligonos_chocan(encoger(pc.hull, 0.05), caja):
                fallos.append(("ventana", nombre,
                               f"tapa {v['id']} por encima del antepecho"))

    nombres = sorted(mob)
    for i, a in enumerate(nombres):
        for b in nombres[i + 1:]:
            if mob[a].solapa(mob[b]) and not mismos_grupo(a, b):
                fallos.append(("solape", a, f"se solapa con {b}"))

    for nombre, minimo in PASO_MINIMO.items():
        p = mob.get(nombre)
        if not p or nombre in en_muro:
            continue
        x0, x1, z0, z1 = p.caja
        # el frente mira hacia dentro desde el muro más próximo; si la pieza
        # está exenta, se usa la dirección al centro de su estancia
        mejor, q = 1e9, None
        for m in MUROS:
            for i in range(len(m)):
                pt = punto_a_arista(p.centro, m[i], m[(i + 1) % len(m)])
                dist = math.hypot(pt[0] - p.centro[0], pt[1] - p.centro[1])
                if dist < mejor:
                    mejor, q = dist, pt
        if q is not None and mejor <= 1.5:
            dx, dz = p.centro[0] - q[0], p.centro[1] - q[1]
        else:
            eid = estancia_de(nombre)
            poly = ESTANCIAS[eid]
            dx = sum(r[0] for r in poly) / len(poly) - p.centro[0]
            dz = sum(r[1] for r in poly) / len(poly) - p.centro[1]
        if abs(dx) >= abs(dz):
            d = (1.0 if dx >= 0 else -1.0, 0.0)
            origen = (x1 if dx >= 0 else x0, (z0 + z1) / 2)
        else:
            d = (0.0, 1.0 if dz >= 0 else -1.0)
            origen = ((x0 + x1) / 2, z1 if dz >= 0 else z0)
        libre = libre_desde(origen, d, minimo + 0.1,
                            [o for o in mob.values()
                             if o is not p and not mismos_grupo(o.nombre, nombre)])
        if libre < minimo:
            fallos.append(("paso", nombre,
                           f"solo {libre:.2f} m delante (mínimo {minimo:g})"))

    for nombre, p in mob.items():
        if not nombre.endswith("_cama") or "sofa" in nombre:
            continue
        x0, x1, z0, z1 = p.caja
        if (z1 - z0) >= (x1 - x0):      # eje largo en z: lados en x
            lados = [((x0, (z0 + z1) / 2), (-1.0, 0.0)),
                     ((x1, (z0 + z1) / 2), (1.0, 0.0))]
        else:
            lados = [(((x0 + x1) / 2, z0), (0.0, -1.0)),
                     (((x0 + x1) / 2, z1), (0.0, 1.0))]
        anchos = []
        for origen, d in lados:
            anchos.append(libre_desde(
                origen, d, PASO_CAMA + 0.1,
                [o for o in mob.values()
                 if o is not p and not mismos_grupo(o.nombre, nombre)]))
        if max(anchos) < PASO_CAMA:
            fallos.append(("paso", nombre,
                           f"solo {max(anchos):.2f} m libres junto a la cama"))

    return piezas, mob, fallos


# ── imagen de control ───────────────────────────────────────────────────────


def dibujar(piezas, mob, fallos, puertas):
    xs = [q[0] for p in ESTANCIAS.values() for q in p]
    zs = [q[1] for p in ESTANCIAS.values() for q in p]
    x0, x1 = min(xs) - 0.6, max(xs) + 0.6
    z0, z1 = min(zs) - 0.6, max(zs) + 0.6
    esc = min(90.0, 1700 / (x1 - x0))
    ancho, alto = int((x1 - x0) * esc), int((z1 - z0) * esc)

    def px(p):
        return ((p[0] - x0) * esc, (p[1] - z0) * esc)

    img = Image.new("RGB", (ancho, alto), "#FAF7F2")
    dr = ImageDraw.Draw(img, "RGBA")
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except OSError:
        font = ImageFont.load_default()

    for poly in ESTANCIAS.values():
        dr.polygon([px(q) for q in poly], fill=(255, 253, 248, 255),
                   outline=(200, 193, 182, 255))
    for m in MUROS:
        dr.polygon([px(q) for q in m], fill=(70, 66, 60, 255))
    for pid, (p, zona) in puertas.items():
        dr.polygon([px(q) for q in zona], outline=(181, 101, 29, 220))
        cx, cz = p["centro"]
        dr.text(px((cx, cz)), pid, fill=(140, 75, 20, 255), font=font,
                anchor="mm")

    malos = {nombre for _, nombre, _ in fallos}
    for nombre, p in mob.items():
        color = (200, 60, 40, 150) if nombre in malos else (120, 140, 160, 90)
        dr.polygon([px(q) for q in p.hull], fill=color,
                   outline=(90, 90, 90, 160))
    for nombre, p in mob.items():
        dr.text(px(p.centro), nombre, fill=(60, 58, 55, 235), font=font,
                anchor="mm")
    for _, nombre, detalle in fallos:
        p = mob.get(nombre)
        if p:
            dr.text(px((p.centro[0], p.centro[1] + 0.16)), f"! {detalle}",
                    fill=(190, 30, 20, 255), font=font, anchor="mm")
    img.save(DEBUG)
    return DEBUG


def main():
    piezas, mob, fallos = revisar()
    cols = colisiones(piezas)
    COLISIONES.write_text(json.dumps(
        {"generado": date.today().isoformat(), "radio": 0.26, "piezas": cols},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    ruta = dibujar(piezas, mob, fallos, barreras_puertas())
    print(f"piezas: {len(piezas)} ({len(mob)} de mobiliario) · "
          f"incumplimientos: {len(fallos)} · colisiones: {len(cols)} · "
          f"control: {ruta.relative_to(ROOT)}")
    print(f"  huellas de colisión -> {COLISIONES.relative_to(ROOT)}")
    for tipo, nombre, detalle in fallos:
        print(f"  [{tipo:12s}] {nombre:22s} {detalle}")
    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
