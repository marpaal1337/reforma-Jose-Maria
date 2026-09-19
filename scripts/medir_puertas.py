#!/usr/bin/env python3
"""
Mide los huecos de puerta del plano de distribución y vuelca data/puertas.json.

Método: sobre data/imagenes/planta_textura.jpg (del que se conoce su
rectángulo en metros, ver data/planos3d.json -> textura.rect_m) se barren las
líneas de muro con las puertas y se buscan tramos claros >= 0,55 m (= huecos).
Los tipos de puerta, bisagras y sentidos de apertura están tomados del plano
PEI.07 de carpintería interior y de los arcos/hojas dibujados en el PE.A.02
(verificación manual 2026-09-18).

Uso (requiere PIL + numpy, p. ej. /tmp/opencode/venv):
    /tmp/opencode/venv/bin/python scripts/medir_puertas.py
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PLAN = json.loads((ROOT / "data" / "planos3d.json").read_text(encoding="utf-8"))
RECT = PLAN["textura"]["rect_m"]
IMG = Image.open(ROOT / "data" / "imagenes" / "planta_textura.jpg").convert("L")
W, H = IMG.size
SXM = W / (RECT[2] - RECT[0])
SZM = H / (RECT[3] - RECT[1])
PX = IMG.load()

UMBRAL = 170          # < umbral => trazo de muro
ANCHO_MIN = 0.55      # hueco mínimo de puerta (m)


def oscuro(x: float, z: float) -> bool:
    xi = int((x - RECT[0]) * SXM)
    zi = int((z - RECT[1]) * SZM)
    return 0 <= xi < W and 0 <= zi < H and PX[xi, zi] < UMBRAL


def barrido(linea: str, fijo: float, a: float, b: float,
            paso: float = 0.04, banda: float = 0.05) -> list[tuple[float, float]]:
    """Devuelve [(x0,x1), ...] de tramos claros sobre la línea de muro."""
    vals = []
    v = a
    while v <= b + 1e-9:
        if linea == "h":
            n = sum(oscuro(v, fijo + d) for d in (-banda, 0.0, banda))
        else:
            n = sum(oscuro(fijo + d, v) for d in (-banda, 0.0, banda))
        vals.append((v, n < 2))
        v += paso
    huecos, ini = [], None
    for v, libre in vals:
        if libre and ini is None:
            ini = v
        elif not libre and ini is not None:
            if v - ini >= ANCHO_MIN and _borde_real(linea, fijo, ini, a, b):
                huecos.append((round(ini, 2), round(v, 2)))
            ini = None
    if ini is not None and vals[-1][0] - ini >= ANCHO_MIN \
            and _borde_real(linea, fijo, ini, a, b):
        huecos.append((round(ini, 2), round(vals[-1][0], 2)))
    return huecos


def _borde_real(linea: str, fijo: float, ini: float, a: float, b: float) -> bool:
    """Un hueco que nace en el borde del rango solo vale si fuera hay vacío
    (muro que continúa = rango truncado, no hueco)."""
    if ini <= a + 0.045:
        v = ini - 0.08
        if linea == "h":
            return not any(oscuro(v, fijo + d) for d in (-0.05, 0.0, 0.05))
        return not any(oscuro(fijo + d, v) for d in (-0.05, 0.0, 0.05))
    return True


# (id, línea, coord_fija, desde, hasta, centros_esperados)
LINEAS = [
    ("sur-dorm1", "h", -0.47, -8.30, -6.30, [-7.85]),
    ("sur-dorm23", "h", -0.47, -6.50, -1.00, [-4.04, -3.14]),
    ("sur-bano1", "h", -1.50, -4.80, -1.70, [-2.22]),
    ("sur-bano2", "h", -1.50, -1.20, 2.00, []),
    ("este-bano2", "v", 1.70, -3.20, -1.40, [-1.96]),
    ("oeste-dormprin", "v", 1.90, -2.20, -0.40, [-0.97]),
    ("fachada", "h", 4.42, 0.00, 2.00, [1.19]),
]


def main() -> None:
    detectados: dict[str, list[tuple[float, float]]] = {}
    for lid, linea, fijo, a, b, _esp in LINEAS:
        huecos = barrido(linea, fijo, a, b)
        detectados[lid] = huecos
        print(f"{lid:15s} huecos: {huecos}")

    # Verificación contra lo medido a mano (2026-09-18)
    esperado = {
        "sur-dorm1": [(-8.20, -7.50)],
        "sur-dorm23": [(-4.42, -3.66), (-3.54, -2.74)],
        "sur-bano1": [(-2.63, -1.81)],
        "sur-bano2": [],
        "este-bano2": [(-2.36, -1.56)],
        "oeste-dormprin": [(-1.30, -0.64)],
        "fachada": [(0.78, 1.60)],
    }
    ok = True
    for lid, huecos in esperado.items():
        det = detectados[lid]
        for (e0, e1) in huecos:
            bueno = [d for d in det
                     if abs(d[0] - e0) <= 0.12 and abs(d[1] - e1) <= 0.12]
            if not bueno:
                print(f"  !! {lid}: sin detección para {(e0, e1)} "
                      f"(detectados {det})")
                ok = False
        extra = [d for d in det if not any(
            abs(d[0] - e0) <= 0.12 and abs(d[1] - e1) <= 0.12
            for (e0, e1) in huecos)]
        if extra:
            print(f"  .. {lid}: tramos abiertos extra (sin puerta): {extra}")
    if not ok:
        raise SystemExit("La detección no coincide con la verificación manual")

    puertas = [
        {"id": "D1", "nombre": "Dormitorio 1",
         "tipo": "abatible", "pared": "h", "centro": [-7.85, -0.47],
         "ancho": 0.70, "alto": 2.03, "bisagra": "E", "apertura": "S"},
        {"id": "D2", "nombre": "Dormitorio 2",
         "tipo": "abatible", "pared": "h", "centro": [-4.04, -0.47],
         "ancho": 0.76, "alto": 2.03, "bisagra": "E", "apertura": "S"},
        {"id": "D3", "nombre": "Dormitorio 3",
         "tipo": "abatible", "pared": "h", "centro": [-3.14, -0.47],
         "ancho": 0.80, "alto": 2.03, "bisagra": "O", "apertura": "S"},
        {"id": "D4", "nombre": "Dormitorio principal",
         "tipo": "abatible", "pared": "v", "centro": [1.90, -0.97],
         "ancho": 0.66, "alto": 2.03, "bisagra": "S", "apertura": "E"},
        {"id": "D5", "nombre": "Baño 2 (en suite)",
         "tipo": "abatible", "pared": "v", "centro": [1.70, -1.96],
         "ancho": 0.80, "alto": 2.03, "bisagra": "S", "apertura": "O"},
        {"id": "D6", "nombre": "Baño 1 (corredera vidriera)",
         "tipo": "corredera", "pared": "h", "centro": [-2.22, -1.50],
         "ancho": 0.82, "alto": 2.03, "bolsillo": "O", "vidrio": True,
         "hoja": "cerrada"},
        {"id": "D7", "nombre": "Casoneto P04 (corredera)",
         "tipo": "corredera", "pared": "h", "centro": [-0.10, 2.48],
         "ancho": 0.60, "alto": 2.03, "bolsillo": "E", "vidrio": False},
        {"id": "D0", "nombre": "Entrada (existente)",
         "tipo": "existente", "pared": "h", "centro": [1.19, 4.42],
         "ancho": 0.82, "alto": 2.00, "hoja": "cerrada"},
        {"id": "D8", "nombre": "Distribuidor (vidriera P03)",
         "tipo": "vidriera", "pared": "v", "centro": [0.70, 4.01],
         "ancho": 0.78, "alto": 2.36, "bisagra": "S", "apertura": "E"},
    ]
    separadores = [
        {"id": "PA02", "nombre": "Separador recibidor (vidrio fijo)",
         "tipo": "fijo", "tramos": [
             {"de": [-0.66, 2.44], "a": [-0.10, 2.44]},
             {"de": [-0.10, 2.44], "a": [0.12, 3.19]},
         ]},
    ]
    out = {"generado": "medición plano PE.A.02 + PEI.07",
           "puertas": puertas, "separadores": separadores}
    (ROOT / "data" / "puertas.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("escrito data/puertas.json (%d puertas)" % len(puertas))


if __name__ == "__main__":
    main()
