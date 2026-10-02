#!/usr/bin/env python3
"""
Genera render3d.html: visor 3D autocontenido (Three.js incluido, sin build)
a partir de visor/src/ (index.html, visor.css, visor.js, realista.js, carga.js)
y de los datos: data/planos3d.json, data/imagenes/planta_textura.jpg,
data/mobiliario.glb, data/texturas/*.jpg, data/colisiones.json (huellas de
colisión del mobiliario, generadas por revisar_mobiliario.py) y data/visor/
(horneado de Cycles, modo Realista).

Este script solo empaqueta: el código del visor vive en visor/src/. Para
iterar sin regenerar los 30 MB usa `python3 scripts/dev_visor.py` (reutiliza
las funciones de aquí).

Requiere: libs/three.min.js y libs/GLTFLoader.js (ver AGENTS.md)

Uso:
    python3 scripts/generar_visor3d.py                 # autocontenido (base64)
    python3 scripts/generar_visor3d.py --no-embed      # carga data/mobiliario.glb, sin Realista
                                                       # (requiere servidor local: file:// bloquea fetch/CORS)
    python3 scripts/generar_visor3d.py --salida x.html # HTML de pruebas fuera del repo
    python3 scripts/generar_visor3d.py --visor <dir>   # horneado alternativo
"""
from __future__ import annotations

import base64
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SRC = ROOT / "visor" / "src"
THREE = ROOT / "libs" / "three.min.js"
GLTF = ROOT / "libs" / "GLTFLoader.js"
GLB = DATA / "mobiliario.glb"
ENV_JPG = DATA / "pbr" / "hdri" / "venice_sunset_env.jpg"
COL_FILE = DATA / "colisiones.json"
VISOR_DEFECTO = DATA / "visor"  # horneado de scripts/hornear_visor.py

# texturas de acabados que usa la geometría del visor (muros y suelos)
TEXTURAS_VISOR = ("suelo_madera", "travertino_porc", "terraza", "muro")


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def data_url(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + b64(path) if path.exists() else ""


def entradas(visor: Path = VISOR_DEFECTO) -> list[Path]:
    """Ficheros de los que depende el HTML (el servidor de desarrollo los vigila)."""
    fijos = [DATA / "planos3d.json", DATA / "imagenes" / "planta_textura.jpg", GLB, ENV_JPG,
             COL_FILE, DATA / "entorno.json", THREE, GLTF, ROOT / "scripts" / "fachada_propia.py"]
    texturas = [DATA / "texturas" / f"{n}.jpg" for n in TEXTURAS_VISOR]
    return fijos + texturas + (sorted(visor.glob("*")) if visor.is_dir() else [])


def fuentes() -> list[Path]:
    """Código del visor (visor/src/*): lo que se edita al iterar."""
    return sorted(SRC.glob("*"))


def cargar(embed: bool = True, realista: bool = True, visor: Path = VISOR_DEFECTO,
           url_datos: str = "") -> dict:
    """Datos del visor. embed=True: base64 dentro del HTML; False: URLs relativas a la
    raíz del repo (con `url_datos` como prefijo). `realista` mete el horneado en el HTML."""
    if not THREE.exists():
        raise SystemExit("Falta libs/three.min.js (ver AGENTS.md: cómo regenerar el visor 3D)")
    if not GLTF.exists():
        raise SystemExit("Falta libs/GLTFLoader.js (descargar de three r147, ver AGENTS.md)")

    plan = json.loads((DATA / "planos3d.json").read_text(encoding="utf-8"))
    texturas = {
        n: ("data:image/jpeg;base64," + b64(DATA / "texturas" / f"{n}.jpg")) if embed
           else f"{url_datos}data/texturas/{n}.jpg"
        for n in TEXTURAS_VISOR if (DATA / "texturas" / f"{n}.jpg").exists()
    }
    env = ""
    if ENV_JPG.exists():
        env = ("data:image/jpeg;base64," + b64(ENV_JPG)) if embed else f"{url_datos}data/pbr/hdri/{ENV_JPG.name}"
    # colisiones del mobiliario (huellas de revisar_mobiliario.py; si falta, el
    # paseo queda con los muros, como antes)
    col = json.loads(COL_FILE.read_text(encoding="utf-8"))["piezas"] if COL_FILE.exists() else []

    real = None
    if realista and (visor / "visor.json").exists() and (visor / "interior.glb").exists():
        info = json.loads((visor / "visor.json").read_text(encoding="utf-8"))
        ent = json.loads((DATA / "entorno.json").read_text(encoding="utf-8"))
        sys.path.insert(0, str(ROOT / "scripts"))
        import fachada_propia
        ip = fachada_propia.principal(ent["edificios"])
        real = {
            "info": info,
            "glb": b64(visor / "interior.glb"),
            "lm": {g: data_url(visor / f"lm_{g}.jpg", "image/jpeg") for g in info["K"]},
            "suelo": {n: data_url(visor / f"suelo_{n}.jpg", "image/jpeg") for n in ("cerca", "lejos")},
            "cielo": data_url(visor / "cielo.jpg", "image/jpeg"),
            "reflejo": data_url(visor / "reflejo.jpg", "image/jpeg"),
            "arbol": {"lado": data_url(visor / "arbol_lado.webp", "image/webp"),
                      "planta": data_url(visor / "arbol_planta.webp", "image/webp")},
            # solo el edificio del piso es "propio" (el otro `propio` de OSM es el
            # vecino de medianera y se dibuja como cualquier otro)
            # el contorno OSM de la medianera se mete en D2/D3: se recorta a la huella
            "edificios": [[[list(p) for p in fachada_propia.recortar_fuera(
                                fachada_propia.limpiar(b["pts"]),
                                [(x, -z) for x, z in plan["huella"]])], b["plantas"]]
                          for i, b in enumerate(ent["edificios"]) if i != ip],
            "propios": [ent["edificios"][ip]["pts"]] if ip is not None else [],
        }

    return {
        "plan": plan,
        "texturas": texturas,
        "env": env,
        "col": col,
        "real": real,
        "tex_b64": b64(DATA / "imagenes" / "planta_textura.jpg"),
        "mob_b64": b64(GLB) if (GLB.exists() and embed) else "",
        "mob_src": "" if embed else f"{url_datos}data/mobiliario.glb",
    }


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def sustituir_js(js: str, d: dict) -> str:
    """Rellena los marcadores de datos de visor.js (no añade saltos de línea)."""
    return (js
            .replace("__COLISIONES__", _json(d["col"]))
            .replace("__TEXTURAS_JS__", _json(d["texturas"]))
            .replace("__MOB_SRC__", d["mob_src"])
            .replace("__ENV_SRC__", d["env"])
            .replace("__TEXTURE__", d["tex_b64"])
            .replace("__DATA__", _json(d["plan"])))


def js_completo(d: dict) -> str:
    """visor.js + realista.js + carga.js, en el orden en que se ejecutan."""
    return sustituir_js((SRC / "visor.js").read_text(encoding="utf-8")
                        + (SRC / "realista.js").read_text(encoding="utf-8")
                        + (SRC / "carga.js").read_text(encoding="utf-8"), d)


def pagina(d: dict, dev: bool = False) -> str:
    """HTML del visor. dev=False: autocontenido. dev=True: CSS/JS/librerías como
    ficheros externos (los sirve scripts/dev_visor.py) y los datos grandes por URL."""
    html = (SRC / "index.html").read_text(encoding="utf-8")
    real_json = _json(d["real"]) if d["real"] else "null"
    if dev:
        html = (html
                .replace("<style>\n__CSS__</style>", '<link rel="stylesheet" href="visor/src/visor.css">')
                .replace("<script>__THREE__</script>", '<script src="libs/three.min.js"></script>')
                .replace("<script>__GLTFLOADER__</script>", '<script src="libs/GLTFLoader.js"></script>')
                .replace("<script>\n__JS__</script>", '<script src="visor.js"></script>'))
    else:
        html = (html
                .replace("__THREE__", THREE.read_text(encoding="utf-8"))
                .replace("__GLTFLOADER__", GLTF.read_text(encoding="utf-8"))
                .replace("__CSS__", (SRC / "visor.css").read_text(encoding="utf-8"))
                .replace("__JS__", js_completo(d)))
    return (html
            .replace("__MOB_B64__", d["mob_b64"])
            .replace("__REAL_JSON__", real_json)
            .replace("__FECHA__", date.today().strftime("%d/%m/%Y"))
            .replace("__PTM__", f"{d['plan']['pt_por_m']:.2f}".replace(".", ",")))


def main(argv: list[str]) -> None:
    def opcion(nombre, defecto):
        return Path(argv[argv.index(nombre) + 1]) if nombre in argv else defecto

    embed = "--no-embed" not in argv
    out = opcion("--salida", ROOT / "render3d.html")  # HTML de pruebas fuera del repo
    d = cargar(embed=embed, realista=embed, visor=opcion("--visor", VISOR_DEFECTO))
    out.write_text(pagina(d), encoding="utf-8")
    print(f"escrito {out} ({out.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main(sys.argv[1:])
