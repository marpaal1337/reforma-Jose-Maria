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

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "texturas"
PBR_DIR = ROOT / "data" / "pbr"
SIZE = 512

# hoja de contacto de los tres PBR derivados (se puede pasar otra ruta en argv)
_SCRATCH = Path("/tmp/claude-1000/-home-mpalaciosa-dev-reforma-Jose-Maria/"
                "69ec5b29-feb5-4a00-8a6a-1bd11048441b/scratchpad")
CONTACTO = (_SCRATCH / "pbr_v2.png") if _SCRATCH.is_dir() else \
    (Path("/tmp/opencode") / "pbr_v2.png")


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


# ── PBR derivados de fuentes CC0 de data/pbr ─────────────────────────────────
# Reproducen los mapas Diffuse/Rough/nor_gl que consume generar_blender.py.
# Las fuentes son juegos CC0 de Poly Haven (ver data/pbr/FUENTES_nuevas.txt):
#   marble_01, cherry_veneer (solo difuso), concrete_debris (solo difuso),
#   white_stucco (solo difuso), travertine, oak_veneer_01.

LUMA = np.array([0.2126, 0.7152, 0.0722])


def _rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), np.float32) / 255.0


def _gray(rgb: np.ndarray) -> np.ndarray:
    return rgb @ LUMA


def _save(rgb: np.ndarray, path: Path, quality: int = 92) -> None:
    arr = np.clip(rgb, 0.0, 1.0)
    Image.fromarray((arr * 255.0 + 0.5).astype(np.uint8), "RGB").save(
        path, "JPEG", quality=quality, optimize=True)


def _size_to(rgb: np.ndarray, n: int) -> np.ndarray:
    if max(rgb.shape[:2]) == n:
        return rgb
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB")
    img = img.resize((n, n), Image.LANCZOS)
    return np.asarray(img, np.float32) / 255.0


def _u8(rgb: np.ndarray) -> Image.Image:
    return Image.fromarray((np.clip(rgb, 0, 1) * 255.0 + 0.5).astype(np.uint8),
                           "RGB")


def _remap(a: np.ndarray, lo: float, hi: float, out0: float,
           out1: float) -> np.ndarray:
    t = np.clip((a - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    return out0 + t * (out1 - out0)


def _colorize(rgb: np.ndarray, target, k: float = 0.9) -> np.ndarray:
    """Luminancia de `rgb` recoloreada a `target` (sRGB 0..1) conservando la veta."""
    L = _gray(rgb)
    n = np.clip(L / max(float(L.mean()), 1e-4), 0.0, 3.0) ** k
    return np.clip(np.asarray(target, np.float32)[None, None, :] * n[:, :, None],
                   0.0, 1.0)


def _flat_normal(rgb: np.ndarray, k: float) -> np.ndarray:
    """Aplana un normal map (0,5 = neutro) al `k` de su pendiente."""
    x = (rgb[:, :, 0] - 0.5) * k + 0.5
    y = (rgb[:, :, 1] - 0.5) * k + 0.5
    return np.stack([x, y, rgb[:, :, 2]], -1)


def _normal_desde_altura(h: np.ndarray, strength: float) -> np.ndarray:
    gy, gx = np.gradient(h)
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5,
                     nz / ln * 0.5 + 0.5], -1)


def _vetas(n: int, rng: np.random.Generator, k: tuple[int, int], turb: float,
           finura: float) -> np.ndarray:
    """Vetas continuas de piedra (0 fondo, 1 veta), tileables: fase entera en
    u/v más turbulencia fbm periódica. Sin despiece ni juntas."""
    u, v = grid_uv(n)
    t = fbm(n, n, rng, (3, 6, 12, 24, 48))
    fase = 2.0 * np.pi * (k[0] * u + k[1] * v) + turb * (t - 0.5) * 2.0 * np.pi
    return (1.0 - np.abs(np.sin(fase))) ** finura


def _piedra_vetada(nombre: str, base, veta, seed: int, rough: float,
                   n: int = 1024) -> None:
    """Superficie sinterizada/cuarzo con vetas suaves: difuso, rugosidad y
    normal casi plana (acabado pulido-satinado)."""
    rng = np.random.default_rng(seed)
    nube = fbm(n, n, rng, (4, 8, 16, 32))
    fina = _vetas(n, rng, (2, 1), 1.6, 9.0)
    ancha = _vetas(n, rng, (1, 1), 1.1, 3.0) * 0.45
    grano = fbm(n, n, rng, (96, 192, 384))
    m = np.clip(np.maximum(fina, ancha) * (0.55 + 0.9 * nube), 0.0, 1.0)
    rgb = mix(base, veta, m) * (0.97 + 0.06 * nube)[:, :, None]
    rgb = rgb + (grano - 0.5)[:, :, None] * 0.025
    _save(np.clip(rgb, 0, 1), PBR_DIR / f"{nombre}_Diffuse.jpg")
    r = rough + (grano - 0.5) * 0.06
    _save(np.repeat(np.clip(r, 0.05, 1.0)[:, :, None], 3, 2),
          PBR_DIR / f"{nombre}_Rough.jpg")
    _save(_normal_desde_altura(m * 0.2 + grano * 0.05, 1.0),
          PBR_DIR / f"{nombre}_nor_gl.jpg")


def derivar_silestone() -> None:
    """Silestone Charcoal Soapstone (isla): carbón casi negro (~sRGB 42) con
    vetas gris claro suaves y escasas; satinado (rugosidad ~0,36)."""
    _piedra_vetada("silestone_charcoal", (0.160, 0.165, 0.172),
                   (0.46, 0.47, 0.48), seed=41, rough=0.36)


def derivar_dekton() -> None:
    """Dekton Marmorio (encimera y frontal): gris cálido marfil con vetas
    grises suaves; pulido (rugosidad ~0,22)."""
    _piedra_vetada("dekton_marmorio", (0.86, 0.845, 0.815),
                   (0.60, 0.595, 0.585), seed=43, rough=0.22)


def derivar_cerezo() -> None:
    """Cerezo barnizado de los años 90 (fotos de la biblioteca): marrón rojizo
    medio (media sRGB ~(146,80,48)) con la veta de cherry_veneer reforzada.
    La fuente queda como cherry_veneer_Diffuse; los derivados son cerezo_*."""
    d = _size_to(_rgb(PBR_DIR / "cherry_veneer_Diffuse.jpg"), 1024)
    L = _gray(d)
    z = (L - float(L.mean())) / max(float(L.std()), 1e-4)
    objetivo = np.asarray((146 / 255.0, 80 / 255.0, 48 / 255.0), np.float32)
    oscuro = np.asarray((104 / 255.0, 50 / 255.0, 30 / 255.0), np.float32)
    t = np.clip(0.5 - z * 0.22, 0.0, 1.0)[:, :, None]      # veta oscura
    cerezo = objetivo[None, None, :] * (1 - t) + oscuro[None, None, :] * t
    cerezo = cerezo * (1.0 + np.clip(z, -2, 2)[:, :, None] * 0.05)
    _save(np.clip(cerezo, 0, 1), PBR_DIR / "cerezo_Diffuse.jpg")

    rough = 0.30 + np.clip(z, -2, 2) * 0.02
    _save(np.repeat(np.clip(rough, 0.24, 0.38)[:, :, None], 3, 2),
          PBR_DIR / "cerezo_Rough.jpg")
    _save(_normal_desde_altura(L, 0.6), PBR_DIR / "cerezo_nor_gl.jpg")


def derivar_hormigon() -> None:
    """Pilar de hormigón picado (abujardado): gris medio neutro (~sRGB 125)
    con árido fino claro y oscuro y relieve rugoso; a 2 m se lee como el
    granito gris del render de la diseñadora."""
    n = 1024
    rng = np.random.default_rng(5)
    tono = fbm(n, n, rng, (3, 6, 12))
    medio = fbm(n, n, rng, (24, 48, 96))
    fino = fbm(n, n, rng, (192, 384, 512))
    v = 0.47 + (tono - 0.5) * 0.10 + (medio - 0.5) * 0.12
    v = v - (fino > 0.66) * 0.16 - (fino > 0.74) * 0.10   # árido oscuro
    v = v + (fino < 0.30) * 0.12                          # árido claro
    v = np.clip(v, 0.12, 0.80)
    gris = np.stack([v * 1.00, v * 0.99, v * 0.975], -1)
    _save(gris, PBR_DIR / "hormigon_picado_Diffuse.jpg")

    rough = 0.72 + (fino - 0.5) * 0.25
    _save(np.repeat(np.clip(rough, 0.55, 0.9)[:, :, None], 3, 2),
          PBR_DIR / "hormigon_picado_Rough.jpg")
    _save(_normal_desde_altura(medio * 0.6 + fino * 0.4, 6.0),
          PBR_DIR / "hormigon_picado_nor_gl.jpg")


def derivar_fachada() -> None:
    """Revoco salmón-beige de la fachada propia (~sRGB (201,163,141)). Las
    fotos locales de fachada no dan más resolución que el estuco CC0 (a 1
    planta ≈ 100 px): se usan solo para fijar el color, no como textura."""
    d = _size_to(_rgb(PBR_DIR / "white_stucco_Diffuse.jpg"), 1024)
    objetivo = (201 / 255.0, 163 / 255.0, 141 / 255.0)
    rev = _colorize(d, objetivo, k=0.55)
    _save(rev, PBR_DIR / "fachada_revoco_Diffuse.jpg")

    g = _gray(d)
    rough = 0.86 + (g - float(g.mean())) * 0.20
    _save(np.repeat(np.clip(rough, 0.78, 0.94)[:, :, None], 3, 2),
          PBR_DIR / "fachada_revoco_Rough.jpg")
    _save(_normal_desde_altura(g, 1.0), PBR_DIR / "fachada_revoco_nor_gl.jpg")


PBR_DERIVADOS = (
    ("silestone_charcoal", derivar_silestone),
    ("dekton_marmorio", derivar_dekton),
    ("cerezo", derivar_cerezo),
    ("hormigon_picado", derivar_hormigon),
    ("fachada_revoco", derivar_fachada),
)


# ── texturas del visor (maqueta), desde los difusos PBR ──────────────────────

def _tile_from(path: Path, size: int) -> np.ndarray:
    return _size_to(_rgb(path), size)


def tex_visor_silestone(size: int = 512) -> Image.Image:
    return _u8(_tile_from(PBR_DIR / "silestone_charcoal_Diffuse.jpg", size))


def tex_visor_dekton(size: int = 1024) -> Image.Image:
    """Dekton Marmorio (derivado procedimental, sin juntas)."""
    return _u8(_tile_from(PBR_DIR / "dekton_marmorio_Diffuse.jpg", size))


def tex_visor_travertino_porc(size: int = 1024) -> Image.Image:
    """Porcelánico imitación travertino en losa 1,20×0,60 m con junta clara."""
    d = _tile_from(PBR_DIR / "travertine_Diffuse.jpg", size)
    h = int(round(size * 0.60 / 1.20))          # 2:1 = una losa 1,20×0,60
    img = np.asarray(_u8(d).resize((size, h), Image.LANCZOS), np.float32) / 255.0
    junta = 0.006                                # ~3 mm de 1,20 m (legible)
    u = np.linspace(0.0, 1.0, size, endpoint=False)[None, :]
    v = np.linspace(0.0, 1.0, h, endpoint=False)[:, None]
    borde = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v))
    near = np.clip(borde / junta, 0, 1)[:, :, None]
    claro = np.asarray((0.94, 0.93, 0.90), np.float32)[None, None, :]
    img = img * (0.10 + 0.90 * near) + claro * (0.90 * (1 - near))
    return _u8(np.clip(img, 0, 1))


def tex_visor_cerezo(size: int = 512) -> Image.Image:
    return _u8(_tile_from(PBR_DIR / "cerezo_Diffuse.jpg", size))


def tex_visor_hormigon(size: int = 512) -> Image.Image:
    return _u8(_tile_from(PBR_DIR / "hormigon_picado_Diffuse.jpg", size))


def tex_visor_roble_mel(size: int = 512) -> Image.Image:
    """Roble melamina: chapa de roble algo más cálida y oscura."""
    d = _tile_from(PBR_DIR / "oak_veneer_01_Diffuse.jpg", size)
    warm = d * np.asarray((1.02, 0.97, 0.90), np.float32)[None, None, :] * 0.93
    return _u8(np.clip(warm, 0, 1))


TEXTURAS_VISOR = {
    "silestone": tex_visor_silestone,
    "dekton": tex_visor_dekton,
    "travertino_porc": tex_visor_travertino_porc,
    "cerezo": tex_visor_cerezo,
    "hormigon": tex_visor_hormigon,
    "roble_mel": tex_visor_roble_mel,
}


def hoja_contacto(ruts) -> Image.Image:
    """Miniatura lateral de los tres resultados PBR (difusos)."""
    objetivos = {
        "silestone_charcoal": PBR_DIR / "silestone_charcoal_Diffuse.jpg",
        "dekton_marmorio": PBR_DIR / "dekton_marmorio_Diffuse.jpg",
        "cerezo": PBR_DIR / "cerezo_Diffuse.jpg",
        "hormigon_picado": PBR_DIR / "hormigon_picado_Diffuse.jpg",
    }
    lado, hueco = 360, 14
    ancho = len(objetivos) * lado + (len(objetivos) + 1) * hueco
    alto = lado + 2 * hueco + 26
    hoja = Image.new("RGB", (ancho, alto), (26, 26, 28))
    for i, (nombre, ruta) in enumerate(objetivos.items()):
        im = Image.open(ruta).convert("RGB").resize((lado, lado), Image.LANCZOS)
        x = hueco + i * (lado + hueco)
        hoja.paste(im, (x, hueco))
    return hoja


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in TEXTURAS.items():
        img = fn()
        path = OUT / f"{name}.jpg"
        img.save(path, "JPEG", quality=86, optimize=True)
        print(f"OK {path.relative_to(ROOT)} ({path.stat().st_size/1024:.0f} KB)")

    for nombre, fn in PBR_DERIVADOS:
        fn()
        print(f"PBR {nombre} -> data/pbr/{nombre}_{{Diffuse,Rough,nor_gl}}.jpg")

    for nombre, fn in TEXTURAS_VISOR.items():
        path = OUT / f"{nombre}.jpg"
        fn().save(path, "JPEG", quality=88, optimize=True)
        print(f"OK {path.relative_to(ROOT)} ({path.stat().st_size/1024:.0f} KB)")

    destino = CONTACTO
    if len(sys.argv) > 1 and sys.argv[-1].endswith(".png"):
        destino = Path(sys.argv[-1])
    destino.parent.mkdir(parents=True, exist_ok=True)
    hoja_contacto(None).save(destino, "PNG")
    print(f"CONTACTO {destino}")


if __name__ == "__main__":
    main()
