#!/usr/bin/env python3
"""
Genera texturas tileables para el mobiliario y los acabados:
data/texturas/*.jpg (madera, tarima, mármol, travertino, azulejo, tejidos...).

Las usan la escena Blender (`generar_blender.py` / `exportar_glb.py`) y el
visor web (`generar_visor3d.py`). Son 100 % procedurales y reproducibles.

Requiere: numpy, pillow

Uso:
    python3 scripts/generar_texturas.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "texturas"
SIZE = 512


# ── ruido periódico (tileable por construcción) ──────────────────────────────

def _smooth(t: np.ndarray) -> np.ndarray:
    return t * t * (3.0 - 2.0 * t)


def noise(h: int, w: int, gh: int, gw: int, rng: np.random.Generator) -> np.ndarray:
    """Ruido de valor bilineal con retícula periódica -> sin costuras."""
    lat = rng.random((gh, gw))
    y = np.linspace(0.0, gh, h, endpoint=False)
    x = np.linspace(0.0, gw, w, endpoint=False)
    y0 = np.floor(y).astype(int) % gh
    x0 = np.floor(x).astype(int) % gw
    fy = _smooth(y - np.floor(y))[:, None]
    fx = _smooth(x - np.floor(x))[None, :]
    y1 = (y0 + 1) % gh
    x1 = (x0 + 1) % gw
    a = lat[np.ix_(y0, x0)]
    b = lat[np.ix_(y0, x1)]
    c = lat[np.ix_(y1, x0)]
    d = lat[np.ix_(y1, x1)]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(h: int, w: int, rng: np.random.Generator, octaves: tuple[int, ...],
        aniso: tuple[float, float] = (1.0, 1.0)) -> np.ndarray:
    """Suma de octavas; `aniso` estira la retícula (veta, vetas largas...)."""
    total = np.zeros((h, w))
    amp, norm = 1.0, 0.0
    for g in octaves:
        gh = max(2, int(round(g * aniso[0])))
        gw = max(2, int(round(g * aniso[1])))
        total += amp * noise(h, w, gh, gw, rng)
        norm += amp
        amp *= 0.5
    return total / norm


def grid_uv(n: int) -> tuple[np.ndarray, np.ndarray]:
    u = np.linspace(0.0, 1.0, n, endpoint=False)[None, :]
    v = np.linspace(0.0, 1.0, n, endpoint=False)[:, None]
    return u, v


def to_img(rgb: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint8), "RGB")


def mix(c1, c2, t):
    c1 = np.asarray(c1, dtype=float)[None, None, :]
    c2 = np.asarray(c2, dtype=float)[None, None, :]
    return c1 * (1 - t)[:, :, None] + c2 * t[:, :, None]


# ── recetas ──────────────────────────────────────────────────────────────────

def wood(size=SIZE, base=(0.48, 0.32, 0.19), light=(0.62, 0.44, 0.27),
         dark=(0.30, 0.19, 0.11), streaks=22.0, seed=7, aniso=(0.12, 1.0)) -> Image.Image:
    rng = np.random.default_rng(seed)
    u, v = grid_uv(size)
    turb = fbm(size, size, rng, (4, 8, 16, 32), aniso=aniso) - 0.5
    rings = 0.5 + 0.5 * np.sin(2 * np.pi * (u * streaks + turb * 0.9))
    rings = _smooth(np.clip(rings, 0, 1))
    fine = fbm(size, size, rng, (64, 128, 256), aniso=(0.04, 1.0))
    t = np.clip(0.42 * rings + 0.58 * fine, 0, 1)
    rgb = mix(dark, light, 0.35 + 0.65 * t)
    rgb = rgb * (0.93 + 0.07 * fine)[:, :, None]
    return to_img(rgb)


def planks(size=SIZE, base=(0.52, 0.35, 0.21), seed=11, rows=6, tone=0.09) -> Image.Image:
    """Tarima: tablas horizontales con juntas largas y despiece alterno."""
    rng = np.random.default_rng(seed)
    u, v = grid_uv(size)
    grain = fbm(size, size, rng, (8, 16, 32, 64), aniso=(0.06, 1.0))
    strip = (v * rows) % 1.0
    plank = np.floor(v * rows).astype(int) % rows
    tint = (rng.random(rows)[plank] - 0.5) * tone
    rgb = mix((0.36, 0.23, 0.13), base, np.clip(0.35 + 0.65 * grain, 0, 1))
    rgb = rgb + tint[:, :, None]
    joint = np.clip(strip * 22.0, 0, 1) * np.clip((1 - strip) * 22.0, 0, 1)
    rgb = rgb * (0.45 + 0.55 * joint)[:, :, None]
    # una testa por tabla, en posición aleatoria
    j = rng.random(rows)
    dist = np.abs(((u - j[plank] + 0.5) % 1.0) - 0.5)
    butt = np.clip(dist / 0.010, 0, 1)
    rgb = rgb * (0.35 + 0.65 * butt)[:, :, None]
    return to_img(rgb)


def stone(size=SIZE, base=(0.82, 0.80, 0.77), vein=(0.55, 0.55, 0.58),
          contrast=7.0, seed=3, softness=0.16) -> Image.Image:
    rng = np.random.default_rng(seed)
    u, v = grid_uv(size)
    turb = fbm(size, size, rng, (4, 8, 16, 32, 64), aniso=(0.35, 1.0))
    band = np.abs(np.sin(2 * np.pi * (u * contrast + turb * 3.0)))
    veins = np.clip(1.0 - band / softness, 0, 1) ** 1.4
    fine = fbm(size, size, rng, (64, 128))
    rgb = mix(vein, base, np.clip(0.55 + 0.45 * fine, 0, 1))
    rgb = rgb * (1 - 0.55 * veins)[:, :, None] + np.asarray((0.93, 0.92, 0.90))[None, None, :] * (0.55 * veins)[:, :, None]
    return to_img(rgb)


def travertine(size=SIZE, base=(0.72, 0.64, 0.51), seed=5) -> Image.Image:
    rng = np.random.default_rng(seed)
    pores = fbm(size, size, rng, (16, 32, 64, 128), aniso=(0.6, 1.0))
    bands = fbm(size, size, rng, (4, 8, 16), aniso=(0.25, 1.0))
    t = np.clip(0.6 * pores + 0.4 * bands, 0, 1)
    rgb = mix((0.58, 0.50, 0.38), base, t)
    holes = (pores < 0.30).astype(float) * (0.30 - pores)
    rgb = rgb - holes[:, :, None] * 1.4
    return to_img(np.clip(rgb, 0, 1))


def tiles(size=SIZE, base=(0.88, 0.87, 0.84), grout=(0.55, 0.54, 0.52),
          n=4, seed=9) -> Image.Image:
    rng = np.random.default_rng(seed)
    u, v = grid_uv(size)
    g = 3.0 / size
    fu = (u * n) % 1.0
    fv = (v * n) % 1.0
    edge = np.minimum(np.minimum(fu, 1 - fu), np.minimum(fv, 1 - fv))
    near = np.clip(edge / g, 0, 1)
    tint = rng.random((n, n)) - 0.5
    rows = np.floor(v * n).astype(int) % n
    cols = np.floor(u * n).astype(int) % n
    t = tint[rows, cols]
    micro = fbm(size, size, rng, (64, 128))
    rgb = mix(grout, base, near) * (1 + 0.04 * t)[:, :, None]
    rgb = rgb * (0.985 + 0.03 * micro)[:, :, None]
    shine = np.clip(1 - np.abs(near - 0.6) / 0.2, 0, 1) * 0.05
    return to_img(np.clip(rgb + shine[:, :, None], 0, 1))


def fabric(size=SIZE, base=(0.80, 0.76, 0.68), seed=13, threads=96.0,
           strength=0.16) -> Image.Image:
    rng = np.random.default_rng(seed)
    u, v = grid_uv(size)
    warp = 0.5 + 0.5 * np.sin(2 * np.pi * u * threads)
    weft = 0.5 + 0.5 * np.sin(2 * np.pi * v * threads)
    weave = np.where(warp > weft, warp, weft)
    fuzz = fbm(size, size, rng, (64, 128, 256))
    t = np.clip(weave * 0.7 + fuzz * 0.3, 0, 1)
    rgb = mix(np.asarray(base) * 0.80, np.asarray(base) * 1.06, t)
    return to_img(rgb * (1 - strength * (1 - t) * 0.5)[:, :, None])


def linen(size=SIZE, base=(0.86, 0.83, 0.76), seed=17) -> Image.Image:
    rng = np.random.default_rng(seed)
    u, v = grid_uv(size)
    fuzz = fbm(size, size, rng, (32, 64, 128, 256))
    warp = 0.5 + 0.5 * np.sin(2 * np.pi * u * 180 + fbm(size, size, rng, (64, 128)) * 3)
    weft = 0.5 + 0.5 * np.sin(2 * np.pi * v * 180 + fbm(size, size, rng, (64, 128)) * 3)
    thread = 0.5 * (warp + weft)
    t = np.clip(0.45 * fuzz + 0.55 * thread, 0, 1)
    return to_img(mix(np.asarray(base) * 0.86, np.asarray(base) * 1.06, t))


def plaster(size=SIZE, base=(0.90, 0.885, 0.855), seed=21) -> Image.Image:
    rng = np.random.default_rng(seed)
    fine = fbm(size, size, rng, (32, 64, 128, 256))
    patch = fbm(size, size, rng, (4, 8, 16))
    t = np.clip(0.55 * fine + 0.45 * patch, 0, 1)
    rgb = mix(np.asarray(base) * 0.95, np.asarray(base) * 1.03, t)
    return to_img(rgb)


def dark_stone(size=SIZE, base=(0.055, 0.052, 0.050), seed=23) -> Image.Image:
    rng = np.random.default_rng(seed)
    fine = fbm(size, size, rng, (64, 128, 256))
    rgb = mix(np.asarray(base) * 0.6, np.asarray(base) * 2.2, fine)
    return to_img(rgb)


def deck(size=SIZE, base=(0.42, 0.29, 0.18), seed=29) -> Image.Image:
    """Tarima exterior: tablas estrechas con ranura y veta marcada."""
    rng = np.random.default_rng(seed)
    u, v = grid_uv(size)
    rows = 10
    plank = np.floor(v * rows).astype(int) % rows
    grain = fbm(size, size, rng, (8, 16, 32, 64), aniso=(0.06, 1.0))
    tint = (rng.random(rows)[plank] - 0.5) * 0.10
    rgb = mix(np.asarray(base) * 0.60, np.asarray(base) * 1.30,
              np.clip(0.3 + 0.7 * grain, 0, 1)) + tint[:, :, None]
    strip = (v * rows) % 1.0
    groove = np.clip(strip / 0.035, 0, 1) * np.clip((1 - strip) / 0.035, 0, 1)
    rgb = rgb * (0.35 + 0.65 * groove)[:, :, None]
    return to_img(rgb)


TEXTURAS = {
    "roble": wood,
    "suelo_madera": lambda: planks(base=(0.52, 0.35, 0.21), seed=11),
    "terraza": deck,
    "marmol": lambda: stone(base=(0.84, 0.82, 0.79), vein=(0.52, 0.52, 0.56),
                            contrast=6.0, seed=3, softness=0.14),
    "travertino": travertine,
    "azulejo": tiles,
    "tejido": fabric,
    "tejido_claro": lambda: fabric(base=(0.88, 0.85, 0.79), seed=31, strength=0.12),
    "lino": linen,
    "muro": plaster,
    "techo": lambda: plaster(base=(0.93, 0.92, 0.90), seed=27),
    "piedra_negra": dark_stone,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in TEXTURAS.items():
        img = fn()
        path = OUT / f"{name}.jpg"
        img.save(path, "JPEG", quality=86, optimize=True)
        print(f"OK {path.relative_to(ROOT)} ({path.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
