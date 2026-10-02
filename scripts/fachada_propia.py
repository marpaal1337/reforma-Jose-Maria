#!/usr/bin/env python3
"""
Geometría del edificio propio derivada de data/entorno.json (sin bpy: la usan
generar_blender.py y generar_visor3d.py).

El edificio es PB + 7 plantas y el piso está en la 7ª, la última (fotos de la
fachada y de la grúa). OSM da `building:levels` = 9, que no se usa para el
propio. En OSM los cuerpos con balcones salen como entrantes de ~0,8 m sobre la
línea de fachada: aquí se toman como columnas de balcones apiladas.

Todo en metros de la escena de Blender (x = este, y = norte, z = altura sobre
el suelo del piso; la calle está en −ALTURA_PISO).
"""
import math
import random

PLANTA = 2.95                         # altura entre forjados
BAJO = 4.0                            # planta baja (comercial)
PISO_N = 7                            # planta del piso (la última)
ALTURA_PISO = BAJO + (PISO_N - 1) * PLANTA
Z_CUB = PLANTA                        # cota de la cubierta sobre el suelo del piso
PETO = 1.05                           # peto de coronación sobre la cubierta
SALMON = (0.62, 0.34, 0.22)           # revoco de la fachada (lineal)
VUELO = 1.32                          # vuelo de los balcones desde la fachada


def limpiar(pts):
    """Misma limpieza que generar_blender._limpiar (las UV `u` dependen de
    ella: hay que recorrer exactamente los mismos vértices)."""
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) > 0.05:
            out.append(tuple(p))
    if len(out) > 2 and math.dist(out[0], out[-1]) <= 0.05:
        out.pop()
    return out


def dentro(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def principal(edificios):
    """Índice del edificio propio que contiene el origen (el del piso). Hay un
    segundo `propio` (el vecino de medianera) que se trata como cualquier otro."""
    for i, b in enumerate(edificios):
        if b.get("propio") and dentro((0.0, 0.0), limpiar(b["pts"])):
            return i
    return None


def recortar_fuera(pts, huella, margen=0.08, paso=0.25):
    """Saca de la huella del piso el polígono de un edificio vecino. El contorno
    OSM de la medianera se mete hasta ~1 m en D2 y D3: se densifica el borde y
    cada punto que cae dentro de `huella` se lleva hacia el oeste (el vecino está
    a ese lado) hasta su primer cruce con el contorno, `margen` más allá. Mismas
    coordenadas que `pts` (x, y de Blender)."""
    h = limpiar(huella)
    xs, ys = [p[0] for p in h], [p[1] for p in h]
    caja = (min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1)

    def cerca(p):
        return caja[0] <= p[0] <= caja[2] and caja[1] <= p[1] <= caja[3]

    def oeste(p):                       # x del cruce más próximo a la izquierda de p
        mejor = None
        for i in range(len(h)):
            (x1, y1), (x2, y2) = h[i], h[i - 1]
            if (y1 > p[1]) != (y2 > p[1]):
                x = x1 + (x2 - x1) * (p[1] - y1) / (y2 - y1)
                if x < p[0] and (mejor is None or x > mejor):
                    mejor = x
        return mejor

    for paso_i in (paso, 0.05):         # la 2ª pasada afina las cuerdas de las esquinas
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            k = max(1, int(math.dist(a, b) / paso_i)) if cerca(a) or cerca(b) else 1
            for j in range(k):
                p = (a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k)
                if cerca(p) and dentro(p, h):
                    x = oeste(p)
                    if x is not None:
                        p = (x - margen, p[1])
                out.append(p)
        pts = out
    return limpiar(pts)


def _area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1]
               - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) / 2


def columnas(pts):
    """Columnas de balcones = entrantes de la fachada a la calle (+x). Devuelve
    [{"x": cara del cuerpo, "y0", "y1", "piso": bool}] ordenadas por y."""
    pts = limpiar(pts)
    n = len(pts)
    # línea de fachada: la arista larga con normal +x más frecuente
    if _area(pts) < 0:
        pts = pts[::-1]
    largas = []
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
        L = math.hypot(xb - xa, yb - ya)
        if L > 4.0 and abs(xb - xa) < 0.15 and yb > ya + 4.0:
            largas.append((xa + xb) / 2)
    if not largas:
        return []
    x_main = sorted(largas)[len(largas) // 2]
    grupos, actual = [], []
    for x, y in pts:
        if x > x_main + 0.4 and x < x_main + 1.5 and -20 < y < 60:
            actual.append((x, y))
        elif actual:
            grupos.append(actual)
            actual = []
    if actual:
        grupos.append(actual)
    cols = []
    for g in grupos:
        ys = [p[1] for p in g]
        cols.append({"x": sum(p[0] for p in g) / len(g), "y0": min(ys), "y1": max(ys),
                     "piso": min(ys) - 0.9 <= -1.465 <= max(ys) + 0.9})
    return sorted(cols, key=lambda c: c["y0"])


def _dist_seg(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy)
                                               / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def _holgura(p, pts):
    return min(_dist_seg(p, pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts)))


def azotea(pts):
    """Elementos de cubierta colocados sobre la azotea, lejos del peto:
    {"escalera": (x, y), "ascensor": (x, y), "chimeneas": [...], "antenas": [...]}."""
    pts = limpiar(pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cand = []
    x = min(xs)
    while x <= max(xs):
        y = min(ys)
        while y <= max(ys):
            if dentro((x, y), pts):
                h = _holgura((x, y), pts)
                if h >= 3.0:
                    cand.append((h, x, y))
            y += 1.0
        x += 1.0
    cand.sort(reverse=True)
    out = {"escalera": None, "ascensor": None, "chimeneas": [], "antenas": []}
    if not cand:
        return out
    a = cand[0]
    out["escalera"] = (a[1], a[2])
    for h, x, y in cand[1:]:
        if math.hypot(x - a[1], y - a[2]) >= 12.0:
            out["ascensor"] = (x, y)
            break
    rnd = random.Random(5)
    libres = [(x, y) for h, x, y in cand if h >= 1.5]
    rnd.shuffle(libres)
    for x, y in libres:
        if len(out["chimeneas"]) < 5 and all(math.hypot(x - c[0], y - c[1]) > 6.0
                                              for c in out["chimeneas"]):
            out["chimeneas"].append((x, y))
    for x, y in libres[::7]:
        if (len(out["antenas"]) < 2 and math.hypot(x - a[1], y - a[2]) > 5.0
                and all(math.hypot(x - c[0], y - c[1]) > 3.0 for c in out["chimeneas"])):
            out["antenas"].append((x, y))
    return out


if __name__ == "__main__":
    import json
    from pathlib import Path
    E = json.loads((Path(__file__).resolve().parent.parent / "data" / "entorno.json")
                   .read_text(encoding="utf-8"))
    i = principal(E["edificios"])
    b = E["edificios"][i]
    print("propio principal:", i, "plantas OSM", b["plantas"], "vértices", len(limpiar(b["pts"])))
    for c in columnas(b["pts"]):
        print("columna", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in c.items()})
    print("azotea", azotea(b["pts"]))
