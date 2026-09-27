#!/usr/bin/env python3
"""
Extrae el entorno urbano real del piso desde OpenStreetMap -> data/entorno.json

Guarda SOLO geometría en metros de la escena de Blender (X, Y con Z arriba),
relativa al piso: volúmenes de edificios con su número de plantas, calzadas con
su anchura, carriles bici, zonas verdes y árboles. No guarda latitud/longitud,
nombres de calles, direcciones ni ninguna otra etiqueta de OSM.

Uso (las coordenadas se pasan en la llamada y NO se guardan en el repo):

    python3 scripts/extraer_entorno.py --lat <lat> --lon <lon> --rumbo <grados>

  --lat/--lon  un punto de la calle frente a la fachada principal (el de un
               Street View sirve: .../@<lat>,<lon>,3a,<fov>y,<rumbo>h,...).
  --rumbo      dirección (0 = norte, 90 = este) desde ese punto hacia la fachada.

El script lanza un rayo con ese rumbo y toma el primer lado de edificio que corta
como fachada del ventanal V01. El mundo se gira y traslada para que ese lado
quede en X = X_FACHADA (cara exterior del muro de V01, con la normal hacia +X) y
el punto de corte coincida con el centro de V01.

Datos © OpenStreetMap contributors, licencia ODbL 1.0.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "entorno.json"
VENT = json.loads((ROOT / "data" / "ventanas.json").read_text(encoding="utf-8"))
PLAN = json.loads((ROOT / "data" / "planos3d.json").read_text(encoding="utf-8"))

OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]
# cara exterior de la fachada de V01 en coordenadas del modelo (x máx. de la huella)
X_FACHADA = max(p[0] for p in PLAN["huella"])
CARRIL = 3.1          # m por carril
APARCAMIENTO = 2.2    # banda de aparcamiento en línea
VIAS = {"primary": 2, "secondary": 2, "tertiary": 2, "residential": 2,
        "unclassified": 2, "living_street": 1, "service": 1,
        "primary_link": 1, "secondary_link": 1, "tertiary_link": 1}


def overpass(lat, lon, radio):
    q = (f"[out:json][timeout:170];("
         f'way["building"](around:{radio},{lat},{lon});'
         f'way["highway"](around:{radio},{lat},{lon});'
         f'node["natural"="tree"](around:{radio},{lat},{lon});'
         f'way["leisure"~"park|garden"](around:{radio},{lat},{lon});'
         f'way["landuse"~"grass|recreation_ground"](around:{radio},{lat},{lon});'
         f");out tags geom;")
    datos = urllib.parse.urlencode({"data": q}).encode()
    ultimo = None
    for url in OVERPASS:
        try:
            req = urllib.request.Request(url, data=datos, headers={
                "User-Agent": "reforma-render/1.0 (uso privado)",
                "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=200) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001 — probamos el siguiente espejo
            ultimo = e
    raise SystemExit(f"Overpass no responde: {ultimo}")


def area2(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] -
               pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) / 2


def dentro(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--rumbo", type=float, required=True)
    ap.add_argument("--radio", type=int, default=450)
    a = ap.parse_args()

    osm = overpass(a.lat, a.lon, a.radio)["elements"]
    kx = 111320.0 * math.cos(math.radians(a.lat))
    ky = 110540.0

    def enu(p):  # metros este/norte respecto al punto de la calle
        return ((p["lon"] - a.lon) * kx, (p["lat"] - a.lat) * ky)

    # 1) fachada: primer lado de edificio que corta el rayo con el rumbo dado
    r = math.radians(a.rumbo)
    d = (math.sin(r), math.cos(r))
    mejor = None
    for e in osm:
        if "building" not in e.get("tags", {}) or e["type"] != "way":
            continue
        g = [enu(p) for p in e["geometry"]]
        for i in range(len(g) - 1):
            (x1, y1), (x2, y2) = g[i], g[i + 1]
            den = d[0] * (y2 - y1) - d[1] * (x2 - x1)
            if abs(den) < 1e-9:
                continue
            t = (x1 * (y2 - y1) - y1 * (x2 - x1)) / den
            u = (x1 * d[1] - y1 * d[0]) / den
            if t > 0 and 0 <= u <= 1 and (mejor is None or t < mejor[0]):
                mejor = (t, (x2 - x1, y2 - y1))
    if mejor is None:
        raise SystemExit("El rayo no corta ningún edificio: revisa --rumbo")
    t, (ex_, ey_) = mejor
    hit = (d[0] * t, d[1] * t)
    L = math.hypot(ex_, ey_)
    tx, ty = ex_ / L, ey_ / L
    n = (-ty, tx)                      # normal del lado...
    if n[0] * d[0] + n[1] * d[1] > 0:  # ...hacia la calle (contra el rayo)
        n = (ty, -tx)
    rumbo_fachada = math.degrees(math.atan2(n[0], n[1])) % 360
    ey = (-n[1], n[0])                 # +Y de Blender = +X girado 90° antihorario

    v01 = next(v for v in VENT["ventanas"] if v["id"] == "V01")
    y_v01 = -v01["hueco_plano"]["centro"][1]  # modelo (x, z) -> Blender (x, -z)

    def bl(p):
        dx, dy = p[0] - hit[0], p[1] - hit[1]
        return (round(X_FACHADA + dx * n[0] + dy * n[1], 2),
                round(y_v01 + dx * ey[0] + dy * ey[1], 2))

    huella = [(x, -z) for x, z in PLAN["huella"]]

    def cerca(pts, lim):
        return any(math.hypot(x, y) < lim for x, y in pts)

    edificios, vias, verdes, arboles = [], [], [], []
    for e in osm:
        tg = e.get("tags", {})
        if e["type"] == "node" and tg.get("natural") == "tree":
            p = bl(enu(e))
            if math.hypot(*p) < a.radio:
                arboles.append(list(p))
            continue
        if e["type"] != "way" or "geometry" not in e:
            continue
        pts = [bl(enu(p)) for p in e["geometry"]]
        if "building" in tg:
            if len(pts) < 4 or pts[0] != pts[-1]:
                continue
            pts = pts[:-1]
            if area2(pts) < 0:
                pts = pts[::-1]
            if abs(area2(pts)) < 4.0 or not cerca(pts, a.radio):
                continue
            try:
                plantas = int(float(tg.get("building:levels", "0")))
            except ValueError:
                plantas = 0
            propio = (any(dentro(q, pts) for q in huella) or
                      any(dentro(q, huella) for q in pts))
            edificios.append({"pts": [list(q) for q in pts], "plantas": plantas,
                              "propio": propio})
        elif tg.get("highway") in VIAS:
            ow = tg.get("oneway") == "yes"
            try:
                carriles = int(tg.get("lanes", ""))
            except ValueError:
                carriles = 1 if ow else VIAS[tg["highway"]]
            ancho = carriles * CARRIL
            if tg["highway"] in ("secondary", "tertiary", "residential"):
                ancho += APARCAMIENTO * (1 if ow else 2)
            if cerca(pts, a.radio):
                vias.append({"pts": [list(q) for q in pts], "ancho": round(ancho, 1),
                             "tipo": "calzada"})
        elif tg.get("highway") == "cycleway":
            if cerca(pts, a.radio):
                vias.append({"pts": [list(q) for q in pts], "ancho": 2.0, "tipo": "bici"})
        elif tg.get("landuse") in ("grass", "recreation_ground") or \
                tg.get("leisure") in ("park", "garden"):
            if len(pts) >= 4 and pts[0] == pts[-1] and cerca(pts, a.radio):
                tipo = "parque" if tg.get("leisure") == "park" else "cesped"
                verdes.append({"pts": [list(q) for q in pts[:-1]], "tipo": tipo})

    # árboles dentro de un edificio (patios de manzana cubiertos, errores de OSM)
    arboles = [p for p in arboles if not any(dentro(p, b["pts"]) for b in edificios)]
    datos = {
        "fuente": "© OpenStreetMap contributors (ODbL 1.0), vía scripts/extraer_entorno.py",
        "generado": dt.date.today().isoformat(),
        "nota": ("Metros de Blender relativos al piso (Z arriba). Fachada de V01 "
                 f"en X = {X_FACHADA}. Sin coordenadas geográficas, nombres ni "
                 "direcciones."),
        "rumbo_fachada": round(rumbo_fachada, 1),
        "edificios": edificios,
        "vias": vias,
        "verdes": verdes,
        "arboles": arboles,
    }
    OUT.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    prop = sum(b["propio"] for b in edificios)
    print(f"rumbo de la fachada de V01: {rumbo_fachada:.1f}° (0=N, 90=E); "
          f"fachada a {t:.1f} m del punto")
    print(f"{len(edificios)} edificios ({prop} propios), {len(vias)} vías, "
          f"{len(verdes)} verdes, {len(arboles)} árboles -> {OUT.relative_to(ROOT)} "
          f"({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
