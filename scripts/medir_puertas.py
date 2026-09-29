#!/usr/bin/env python3
"""
Construye data/puertas.json a partir de los arcos de barrido medidos en
data/carpinteria_medida.json (plano PE/I.06 carpintería interior) más la tabla
de metadatos de las hojas (plano PE/I.07).

Método: cada puerta abatible del plano está dibujada con su arco de barrido
(centro = bisagra, radio = hoja, p0/p1 = extremos de la hoja cerrada y abierta).
El script localiza ese arco, comprueba que su bisagra coincide con la esperada
(tolerancia 5 cm; si no, aborta con error) y deriva de él el centro del hueco,
el ancho, la bisagra y el sentido de apertura. Las correderas (P04) y el
separador fijo (PA02) no dibujan arco: se toman de la tabla.

Uso:
    python3 scripts/medir_puertas.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIDA = ROOT / "data" / "carpinteria_medida.json"
OUT = ROOT / "data" / "puertas.json"

TOL_BISAGRA = 0.05  # m (tolerancia bisagra medida vs. esperada)

# Tabla de metadatos (PE/I.07 + PE/I.06). "bisagra_esperada" es la posición del
# centro del arco en el plano; el resto de geometría se deriva del arco.
PUERTAS_ESPEC = [
    {"id": "PE", "nombre": "Entrada (existente)", "tipo": "existente",
     "bisagra_esperada": (0.815, 4.326), "hoja": 0.80, "alto": 2.03,
     "acabado": "lacado blanco, panelada", "abre_a": "recibidor",
     "hoja_estado": "cerrada"},
    {"id": "P01", "nombre": "Vestidor · dormitorio principal", "tipo": "abatible",
     "bisagra_esperada": (1.854, -0.624), "hoja": 0.72, "alto": 2.03,
     "acabado": "lacado blanco, manivela blanca", "abre_a": "vestidor",
     "en_paso": True},
    {"id": "P02", "nombre": "Baño 1 (ducha)", "tipo": "abatible",
     "bisagra_esperada": (1.754, -1.644), "hoja": 0.72, "alto": 2.03,
     "acabado": "lacado blanco", "abre_a": "bano-1"},
    {"id": "P03", "nombre": "Pasillo · zona de día", "tipo": "vidriera",
     "bisagra_esperada": (-1.576, -0.574), "hoja": 0.82, "alto": 2.30,
     "acabado": "roble natural + vidrio translúcido, travesaño 0.88 m, tirador de madera",
     "abre_a": "pasillo", "en_paso": True, "marco_ancho": 0.98},
    {"id": "P04", "nombre": "Baño 2 (bañera)", "tipo": "corredera",
     "bisagra_esperada": None, "hoja": 0.72, "alto": 2.03,
     "acabado": "lacado blanco, uñero", "abre_a": "bano-2",
     "pared": "h", "centro": [-2.22, -1.49], "ancho": 0.82,
     "bolsillo": "O", "vidrio": False},
    {"id": "P05", "nombre": "Estudio", "tipo": "abatible",
     "bisagra_esperada": (-3.475, -0.424), "hoja": 0.72, "alto": 2.03,
     "acabado": "lacado blanco", "abre_a": "estudio"},
    {"id": "P06", "nombre": "Dormitorio 2", "tipo": "abatible",
     "bisagra_esperada": (-3.676, -0.424), "hoja": 0.72, "alto": 2.03,
     "acabado": "lacado blanco", "abre_a": "dorm-2"},
    {"id": "P07", "nombre": "Dormitorio 3", "tipo": "abatible",
     "bisagra_esperada": (-4.707, -0.624), "hoja": 0.72, "alto": 2.03,
     "acabado": "lacado blanco", "abre_a": "dorm-3", "en_paso": True},
    {"id": "PL", "nombre": "Lavadero", "tipo": "vidriera_negra",
     "bisagra_esperada": (0.028, 2.493), "hoja": 0.70, "alto": 2.30,
     "acabado": "perfil de acero negro + vidrio translúcido", "abre_a": "lavadero",
     "marco_ancho": 0.78},
]

SEPARADORES = [
    {"id": "PA02", "nombre": "Separador recibidor · salón (vidrio ácido fijo)",
     "tipo": "fijo", "pared": "v", "alto": 2.30, "marco": "roble 0.04",
     "travesano_altura": 0.87,
     "tramos": [{"de": [1.78, 2.44], "a": [1.78, 3.47]}]},
]


def cargar_arcos() -> list[dict]:
    data = json.loads(MEDIDA.read_text(encoding="utf-8"))
    return [a for a in data["carpinteria"]["arcos"] if a.get("puerta_probable")]


def buscar_arco(arcos: list[dict], bisagra: tuple[float, float]) -> dict | None:
    """Arco cuya bisagra (centro) está a menos de TOL_BISAGRA del esperado."""
    mejor, dist = None, TOL_BISAGRA
    for a in arcos:
        d = math.hypot(a["cx"] - bisagra[0], a["cz"] - bisagra[1])
        if d <= dist:
            mejor, dist = a, d
    return mejor


def derivar(arc: dict) -> dict:
    """A partir del arco deduce centro del hueco, ancho, bisagra y apertura."""
    hx, hz = arc["cx"], arc["cz"]
    p0, p1 = arc["p0"], arc["p1"]

    def alineacion(p):
        return min(abs(p[0] - hx), abs(p[1] - hz))

    # extremo cerrado = el más alineado con la bisagra (sobre el eje del muro)
    if alineacion(p0) <= alineacion(p1):
        cerrado, abierto = p0, p1
    else:
        cerrado, abierto = p1, p0
    dx, dz = abs(cerrado[0] - hx), abs(cerrado[1] - hz)
    if dz <= dx:                      # muro horizontal: bisagra y jamba comparten z
        pared = "h"
        bisagra = "O" if hx < cerrado[0] else "E"
        apertura = "S" if abierto[1] > hz else "N"
    else:
        pared = "v"
        bisagra = "N" if hz < cerrado[1] else "S"
        apertura = "E" if abierto[0] > hx else "O"
    centro = [round((hx + cerrado[0]) / 2, 3), round((hz + cerrado[1]) / 2, 3)]
    return {"pared": pared, "bisagra": bisagra, "apertura": apertura,
            "centro": centro, "bisagra_xz": [round(hx, 3), round(hz, 3)],
            "ancho_medido": round(math.hypot(cerrado[0] - hx, cerrado[1] - hz), 3)}


def main() -> int:
    arcos = cargar_arcos()
    puertas, errores = [], []
    for esp in PUERTAS_ESPEC:
        bis = esp["bisagra_esperada"]
        arc = buscar_arco(arcos, bis) if bis else None
        if bis and arc is None:
            errores.append(f"{esp['id']}: sin arco cerca de {bis}")
            continue
        p = {"id": esp["id"], "nombre": esp["nombre"], "tipo": esp["tipo"],
             "alto": esp["alto"], "hoja_ancho": esp["hoja"],
             "acabado": esp["acabado"], "abre_a": esp["abre_a"],
             "en_paso": bool(esp.get("en_paso"))}
        if arc is not None:
            d = derivar(arc)
            if abs(d["ancho_medido"] - esp["hoja"]) > 0.08:
                print(f"  .. {esp['id']}: hoja medida {d['ancho_medido']:.2f} m "
                      f"(esperada {esp['hoja']:.2f})")
            p["pared"] = d["pared"]
            p["centro"] = d["centro"]
            p["bisagra"] = d["bisagra"]
            p["apertura"] = d["apertura"]
            p["bisagra_xz"] = d["bisagra_xz"]
            p["ancho"] = round(esp.get("marco_ancho", esp["hoja"] + 0.08), 2)
        else:  # P04 corredera: geometría de la tabla, sin arco
            p["pared"] = esp["pared"]
            p["centro"] = list(esp["centro"])
            p["ancho"] = esp["ancho"]
            p["bolsillo"] = esp["bolsillo"]
            p["vidrio"] = esp["vidrio"]
        if esp.get("hoja_estado"):
            p["hoja"] = esp["hoja_estado"]
        puertas.append(p)

    if errores:
        for e in errores:
            print(f"  !! {e}")
        raise SystemExit("No cuadran las bisagras con los arcos medidos")
    if len(puertas) != 9:
        raise SystemExit(f"Se esperaban 9 puertas, hay {len(puertas)}")

    out = {"generado": "medición PE/I.06 (arcos) + PE/I.07 (hojas)",
           "fuente": ["Planos/PE_carpinteria_interior.pdf", "data/carpinteria_medida.json"],
           "puertas": puertas, "separadores": SEPARADORES}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"escrito data/puertas.json ({len(puertas)} puertas + "
          f"{len(SEPARADORES)} separador)")
    for p in puertas:
        bis = p.get("bisagra", "-")
        ap = p.get("apertura", "-")
        print(f"  {p['id']:3s} {p['nombre']:34s} {p['tipo']:15s} "
              f"pared={p['pared']} centro=({p['centro'][0]:6.2f},{p['centro'][1]:6.2f}) "
              f"ancho={p['ancho']:.2f} bisagra={bis} abre={ap} "
              f"en_paso={p['en_paso']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
