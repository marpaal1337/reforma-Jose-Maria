#!/usr/bin/env python3
"""
Referencia Cycles de la misma cámara que las capturas del visor.

Uso:
    python3 scripts/ref_cycles.py --cam s4_salon_ventanal [--out /tmp/ref-s4.jpg]
                                  [--samples 128] [--res 1280x720]
    python3 scripts/ref_cycles.py --todas --out-dir /tmp/refs [--samples 128]

Llama a ~/opt/blender/blender -b renders/escena.blend -P scripts/render_blender.py.
Si Blender no arranca (p.ej. falta libSM6 en WSL: sudo apt-get install -y libsm6),
el script lo dice y no deja renders a medias.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENVOLTORIO = ROOT / "scripts" / "blender.sh"
BLENDER_CANDIDATOS = [
    Path.home() / "opt" / "blender" / "blender",
    Path("/usr/bin/blender"),
    Path("/snap/bin/blender"),
]
STILLS = ["s1_salon_tv", "s2_cocina_comedor", "s3_dorm_principal", "s4_salon_ventanal"]


def blender() -> str:
    """Prefiere scripts/blender.sh (resuelve libSM/libICE locales sin sudo)."""
    if ENVOLTORIO.exists():
        return str(ENVOLTORIO)
    for b in BLENDER_CANDIDATOS:
        if b.exists():
            return str(b)
    raise SystemExit("no hay blender: usa scripts/blender.sh o instala Blender 4.2")


def renderizar(cam: str, out: str, samples: int, res: str) -> None:
    b = blender()
    cmd = [str(b), "-b", "renders/escena.blend", "-noaudio",
           "-P", "scripts/render_blender.py", "--",
           "--cam", cam, "--out", out,
           "--samples", str(samples), "--res", res]
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(f"blender falló ({r.returncode}) con {cam}: "
                         "revisa la salida de Blender arriba")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cam", default="s4_salon_ventanal")
    p.add_argument("--out", default="/tmp/ref-salon.jpg")
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--res", default="1280x720")
    p.add_argument("--todas", action="store_true")
    p.add_argument("--out-dir", default="/tmp/refs")
    a = p.parse_args()
    if a.todas:
        outdir = Path(a.out_dir)
        outdir.mkdir(parents=True, exist_ok=True)
        for cam in STILLS:
            renderizar(cam, str(outdir / f"{cam}.jpg"), a.samples, a.res)
    else:
        renderizar(a.cam, a.out, a.samples, a.res)


if __name__ == "__main__":
    sys.exit(main())
