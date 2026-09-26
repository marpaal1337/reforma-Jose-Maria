#!/usr/bin/env python3
"""
Mide la posición del sol (azimut/elevación) en un HDRI equirectangular para
rellenar `HDRI_SOL` en scripts/generar_blender.py.

El azimut sigue el convenio de Blender: 0° = +X, +90° = +Y. La elevación se
mide desde el horizonte.

Uso (con Blender, offline, una vez por HDRI):

    source /tmp/opencode/blender_env.sh
    "$BLENDER" -b --factory-startup -noaudio -P scripts/medir_sol_hdri.py -- \
        data/pbr/hdri/nombre_4k.hdr
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
import numpy as np


def main() -> None:
    argv = sys.argv
    hdr = Path(argv[argv.index("--") + 1])
    img = bpy.data.images.load(str(hdr.resolve()))
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    lum = px[..., :3].mean(axis=2)

    trabajo = lum.copy()
    for rango in range(3):
        iy, ix = np.unravel_index(np.argmax(trabajo), trabajo.shape)
        u = (ix + 0.5) / w            # arrays de Blender: fila 0 = abajo
        v_arriba = 1.0 - (iy + 0.5) / h
        az = math.degrees(math.pi * (2.0 * u - 1.0))   # 0° = +X, +90° = +Y
        el = 90.0 - math.degrees(math.pi * v_arriba)   # desde el horizonte
        print(f"rango={rango} az={az:.1f} el={el:.1f} lum={lum[iy, ix]:.1f}")
        yy, xx = np.ogrid[:h, :w]
        trabajo[(yy - iy) ** 2 + (xx - ix) ** 2 < (h * 0.08) ** 2] = -1.0


if __name__ == "__main__":
    main()
