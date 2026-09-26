#!/usr/bin/env python3
"""
Renderiza una cámara de `renders/escena.blend` (panorámica o still).

Uso:
    "$BLENDER" -b renders/escena.blend -noaudio -P scripts/render_blender.py -- \
        --cam p03_salon_ventanal --out renders/panos/p03_salon_ventanal.jpg \
        --samples 384 --res 4096x2048
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import bpy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--cam", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--samples", type=int, default=384)
    p.add_argument("--threshold", type=float, default=0.01)
    p.add_argument("--res", default="4096x2048")
    return p.parse_args(argv)


def main():
    a = parse_args()
    scene = bpy.context.scene
    cam = bpy.data.objects.get(a.cam)
    if cam is None:
        raise SystemExit(f"cámara no encontrada: {a.cam}")
    scene.camera = cam
    scene.cycles.samples = a.samples
    scene.cycles.adaptive_threshold = a.threshold
    w, h = (int(v) for v in a.res.lower().split("x"))
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    out = Path(a.out)
    if not out.is_absolute():
        out = Path(bpy.data.filepath).parent.parent / out
    out.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"RENDER_OK {out} {w}x{h} samples={a.samples} {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
