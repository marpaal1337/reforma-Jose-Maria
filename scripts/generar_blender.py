#!/usr/bin/env python3
"""
Construye `renders/escena.blend` para el tour 360 de la reforma, a partir de:
  - data/planos3d.json   (geometría exacta: muros, huella, estancias, alicatados)
  - data/ventanas.json   (V01–V08 medidas del PEI.05/06)

Ejecutar con Blender (ver AGENTS.md):
    source /tmp/opencode/blender_env.sh
    "$BLENDER" -b --factory-startup -noaudio -P scripts/generar_blender.py

Genera la escena amueblada (nivel B), los materiales, la iluminación de mediodía
difuso y las cámaras (12 panorámicas equirectangulares + 4 stills).
No renderiza: de eso se encarga `scripts/render_blender.py`.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
PLAN = json.loads((ROOT / "data" / "planos3d.json").read_text(encoding="utf-8"))
VENT = json.loads((ROOT / "data" / "ventanas.json").read_text(encoding="utf-8"))
CAMARAS = json.loads((ROOT / "data" / "camaras.json").read_text(encoding="utf-8"))
PUERTAS = json.loads((ROOT / "data" / "puertas.json").read_text(encoding="utf-8"))
OUT = ROOT / "renders" / "escena.blend"

ALTURA = PLAN["altura_muro"]      # 2,46 m (altura de muro del PE)
TECHO = ALTURA

# Altura libre de cada estancia (2,30 con falso techo; 2,46 el resto). Se
# prefiere el campo `altura` de planos3d.json si viene informado.
ALTURAS_ESTANCIA = {
    "dorm-3": 2.46, "bano-2": 2.30, "bano-1": 2.30, "vestidor": 2.30,
    "dorm-principal": 2.46, "pasillo": 2.30, "dorm-2": 2.46, "estudio": 2.46,
    "cocina": 2.30, "salon": 2.46, "recibidor": 2.30, "lavadero": 2.46,
    "terraza": None,
}

PANOS = [(p["id"], p["x"], p["z"], p["yaw"], p["nombre"]) for p in CAMARAS["panos"]]

STILLS = CAMARAS["stills"]


def set_in(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value
        return True
    return False


# ── materiales ───────────────────────────────────────────────────────────────

def principled(name, base=(0.8, 0.8, 0.8), rough=0.8, metal=0.0, trans=0.0,
               ior=1.45, emission=None, emit_str=0.0, spec=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_in(bsdf, "Base Color", (*base, 1.0))
    set_in(bsdf, "Roughness", rough)
    set_in(bsdf, "Metallic", metal)
    set_in(bsdf, "IOR", ior)
    if trans:
        set_in(bsdf, "Transmission Weight", trans) or set_in(bsdf, "Transmission", trans)
    if emission is not None:
        set_in(bsdf, "Emission Color", (*emission, 1.0))
        set_in(bsdf, "Emission Strength", emit_str)
    set_in(bsdf, "Specular IOR Level", spec) or set_in(bsdf, "Specular", spec)
    return mat


def vidrio_arquitectonico(name, tinte=(0.93, 0.97, 0.95), ior=1.52):
    """Vidrio de ventana sin refracción (truco estándar de arquitectura):
    transparente + reflejo especular con Fresnel. La refracción real de una
    caja de vidrio fina dejaba un círculo luminoso visto desde fuera."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = ior
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*tinte, 1.0)
    try:
        gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    except RuntimeError:
        gl = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    gl.inputs["Roughness"].default_value = 0.01
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return mat


def visillo(name):
    """Visillo: tela translúcida con parte transparente real, para que el sol
    la atraviese (con transmisión tipo vidrio y cáusticas apagadas proyectaba
    sombra opaca)."""
    mat = principled(name, base=(0.96, 0.95, 0.92), rough=0.6)
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    bsdf = nt.nodes["Principled BSDF"]
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tl.inputs["Color"].default_value = (0.95, 0.94, 0.90, 1.0)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    m1 = nt.nodes.new("ShaderNodeMixShader")
    m1.inputs[0].default_value = 0.5
    nt.links.new(bsdf.outputs[0], m1.inputs[1])
    nt.links.new(tl.outputs[0], m1.inputs[2])
    m2 = nt.nodes.new("ShaderNodeMixShader")
    m2.inputs[0].default_value = 0.55
    nt.links.new(m1.outputs[0], m2.inputs[1])
    nt.links.new(tr.outputs[0], m2.inputs[2])
    nt.links.new(m2.outputs[0], out.inputs["Surface"])
    return mat


def noise_bump(mat, scale=40.0, strength=0.06):
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = 6.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def _pintar_lamina(nombre, w, h, arriba, medio, abajo, sol_xy, sol_r, sol_c,
                   semilla):
    """Pinta una lámina abstracta cálida píxel a píxel (degradado vertical en
    tres tramos + disco de sol con borde suave + veta horizontal + grano
    determinista). 100 % procedural, sin imágenes externas. La imagen queda
    empaquetada en el .blend y viaja a los dos GLB como textura real
    (exportar_glb.py y hornear_visor.py conservan los nodos TEX_IMAGE)."""
    img = bpy.data.images.new(nombre, w, h, alpha=False)
    img.colorspace_settings.name = "sRGB"
    sx, sy = sol_xy
    aspecto = w / h
    pix = [0.0] * (w * h * 4)
    for j in range(h):
        v = j / (h - 1)
        if v < 0.45:
            t = v / 0.45
            base = [abajo[k] + (medio[k] - abajo[k]) * t for k in range(3)]
        else:
            t = (v - 0.45) / 0.55
            base = [medio[k] + (arriba[k] - medio[k]) * t for k in range(3)]
        for i in range(w):
            u = i / (w - 1)
            d = math.hypot((u - sx) * aspecto, v - sy)
            mm = max(0.0, 1.0 - d / sol_r)
            sol = mm * mm * (3.0 - 2.0 * mm)
            veta = 0.030 * math.sin(2 * math.pi * (v * 9.0 + 0.12 * math.sin(
                2 * math.pi * u * 3.0)))
            g = math.sin(i * 12.9898 + j * 78.233 + semilla * 37.7) * 43758.55
            grano = (g - math.floor(g) - 0.5) * 0.07
            k = (j * w + i) * 4
            for c in range(3):
                val = base[c] * (1.0 - sol) + sol_c[c] * sol + veta + grano
                pix[k + c] = max(0.0, min(1.0, val))
            pix[k + 3] = 1.0
    img.pixels.foreach_set(pix)
    img.pack()
    return img


def lamina_cuadro(name, w, h, arriba, medio, abajo, sol_xy, sol_r, sol_c,
                  semilla):
    """Material de cuadro con su lámina procedural como imagen real."""
    img = _pintar_lamina(name + "_img", w, h, arriba, medio, abajo, sol_xy,
                         sol_r, sol_c, semilla)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    set_in(bsdf, "Roughness", 0.9)
    return mat


def _pintar_colcha(nombre, lado=192, c1=(0.68, 0.44, 0.28),
                   c2=(0.87, 0.75, 0.60), bandas=7, semilla=5.0):
    """Tejido a rayas tileable para las colchas: bandas + trama + grano."""
    img = bpy.data.images.new(nombre, lado, lado, alpha=False)
    img.colorspace_settings.name = "sRGB"
    pix = [0.0] * (lado * lado * 4)
    for j in range(lado):
        v = j / lado
        f = 0.5 + 0.5 * math.cos(2 * math.pi * bandas * v)
        for i in range(lado):
            u = i / lado
            trama = 0.5 + 0.5 * math.sin(2 * math.pi * u * 64.0) * math.sin(
                2 * math.pi * v * 64.0)
            g = math.sin(i * 12.9898 + j * 78.233 + semilla * 91.7) * 43758.55
            grano = (g - math.floor(g) - 0.5) * 0.05
            k = (j * lado + i) * 4
            for c in range(3):
                val = (c1[c] + (c2[c] - c1[c]) * f) * (0.94 + 0.06 * trama)
                pix[k + c] = max(0.0, min(1.0, val + grano))
            pix[k + 3] = 1.0
    img.pixels.foreach_set(pix)
    img.pack()
    return img


def colcha_rayas(name):
    """Colcha a rayas cálidas con relieve de tejido sutil."""
    img = _pintar_colcha(name + "_img")
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    noise_bump(mat, scale=220, strength=0.08)
    set_in(bsdf, "Roughness", 0.95)
    return mat


def pantalla_calida(name):
    """Pantalla de la lámpara de pie: ámbar cálido translúcido (~3000 K).

    Base media (no blanco puro) + emisión suave + mezcla translúcida para
    que la luz del punto interior la atraviese sin quemarla en Cycles. En
    los GLB la mezcla se simplifica (ver exportar_glb.py y hornear_visor.py)
    pero se conservan base cálida + emisión suave."""
    mat = principled(name, base=(0.82, 0.63, 0.42), rough=0.9,
                     emission=(1.0, 0.66, 0.34), emit_str=0.65)
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    bsdf = nt.nodes["Principled BSDF"]
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tl.inputs["Color"].default_value = (0.85, 0.62, 0.38, 1.0)
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = 0.45
    nt.links.new(bsdf.outputs[0], mx.inputs[1])
    nt.links.new(tl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return mat


def uv_retrato(ob, x0, x1, h0, h1):
    """UV 0..1 en las caras frontales de un cuadro para encuadrar su lámina
    (las UV de caja en metros recortarían la imagen). Los cantos se dejan con
    las UV de `uv_proyectar()` (que salta los `cuadro_*`)."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uvl = me.uv_layers.active.data
    for poly in me.polygons:
        if abs(poly.normal.y) < 0.9:
            continue
        for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
            co = me.vertices[me.loops[li].vertex_index].co
            uvl[li].uv = ((co.x - x0) / (x1 - x0), (co.z - h0) / (h1 - h0))


PBR_DIR = ROOT / "data" / "pbr"
HDRI_DIR = PBR_DIR / "hdri"
ASSETS_DIR = ROOT / "data" / "assets"
# Posición del sol (azimut/elevación en grados) medida en cada HDRI equirectangular
# (data/pbr/hdri/): sol del archivo venice_sunset_4k.hdr (Poly Haven, CC0).
HDRI_SOL = {"venice_sunset_4k.hdr": (35.9, 3.5)}
# Azimut del sol en la escena (Blender: +X = este, -Y = sur). Con el HDRI de
# Venecia (-40°) el ventanal V01 ve la laguna con el sol poniente al sureste.
SOL_AZ = -40.0


# Entorno urbano real (OSM, ver scripts/extraer_entorno.py): si existe, sustituye
# al HDRI por cielo físico + sol real y levanta la ciudad alrededor del piso.
ENTORNO_JSON = ROOT / "data" / "entorno.json"
ENTORNO = (json.loads(ENTORNO_JSON.read_text(encoding="utf-8"))
           if ENTORNO_JSON.is_file() else None)
PLANTA = 2.95          # altura entre forjados del edificio
BAJO = 4.0             # planta baja comercial
ALTURA_PISO = BAJO + 6 * PLANTA   # suelo del 7º sobre la calle (~21,7 m, estimado)
# Sol: fecha/hora de los renders (hora UTC) y latitud/longitud de la ciudad (no
# del edificio). 15-oct 11:30 hora local: sol a ~139°/33°, casi de frente a la
# fachada principal (130°), por encima del edificio de enfrente.
SOL_UTC = (2026, 10, 15, 9, 30)
SOL_FUERZA = 14.0      # lámpara SUN (W/m²) y cielo Nishita: ajustados con renders
CIELO_FUERZA = 0.30    # de prueba para que el interior quede como con el HDRI
CIUDAD_LAT_LON = (39.47, -0.38)


def posicion_sol(utc, lat, lon):
    """Azimut (desde el norte, horario) y elevación del sol en grados (NOAA)."""
    import datetime as dt
    t = dt.datetime(*utc)
    n = t.timetuple().tm_yday
    h = t.hour + t.minute / 60
    g = 2 * math.pi / 365 * (n - 1 + (h - 12) / 24)
    eq = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                   - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    de = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g)
          - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
          - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    ha = math.radians((h * 60 + eq + 4 * lon) / 4 - 180)
    la = math.radians(lat)
    cz = math.sin(la) * math.sin(de) + math.cos(la) * math.cos(de) * math.cos(ha)
    ze = math.acos(max(-1.0, min(1.0, cz)))
    c = (math.sin(la) * math.cos(ze) - math.sin(de)) / (math.cos(la) * math.sin(ze))
    az = math.degrees(math.acos(max(-1.0, min(1.0, c))))
    az = (az + 180) % 360 if ha > 0 else (540 - az) % 360
    return az, 90 - math.degrees(ze)


def rumbo_a_blender(rumbo):
    """Ángulo en el plano XY de Blender (desde +X, antihorario) de un rumbo
    geográfico. +X es la normal de la fachada de V01 (`rumbo_fachada`)."""
    return (ENTORNO["rumbo_fachada"] if ENTORNO else 90.0) - rumbo


def hdri_path():
    """HDRI de `data/pbr/hdri/` con sol medido, o None (cae a Nishita)."""
    for nombre in HDRI_SOL:
        f = HDRI_DIR / nombre
        if f.is_file():
            return f
    return None


def pbr_material(name, key, tex_m=1.0, rot=0.0, nor=0.8, rough_mul=1.0,
                 value=1.0, sat=1.0, rough=0.7):
    """Material PBR con texturas de `data/pbr` (`<key>_Diffuse/_Rough/_nor_gl.jpg`).

    Texturas CC0 de Poly Haven / ambientCG descargadas en `data/pbr/`.
    `tex_m` = tamaño real de la textura en metros; coordenadas de objeto
    (los vértices van en metros y los objetos no tienen transformación).
    Devuelve None si faltan los archivos: el llamador cae al procedural.
    """
    diff = PBR_DIR / f"{key}_Diffuse.jpg"
    if not diff.exists():
        return None
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / tex_m,) * 3
    mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(rot))
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])

    td = nt.nodes.new("ShaderNodeTexImage")
    td.image = bpy.data.images.load(str(diff))
    td.image.colorspace_settings.name = "sRGB"
    nt.links.new(mp.outputs["Vector"], td.inputs["Vector"])
    if value != 1.0 or sat != 1.0:
        hs = nt.nodes.new("ShaderNodeHueSaturation")
        hs.inputs["Saturation"].default_value = sat
        hs.inputs["Value"].default_value = value
        nt.links.new(td.outputs["Color"], hs.inputs["Color"])
        nt.links.new(hs.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        nt.links.new(td.outputs["Color"], bsdf.inputs["Base Color"])

    rgh = PBR_DIR / f"{key}_Rough.jpg"
    if rgh.exists() and rough_mul > 0.0:
        tr = nt.nodes.new("ShaderNodeTexImage")
        tr.image = bpy.data.images.load(str(rgh))
        tr.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs["Vector"], tr.inputs["Vector"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = rough_mul
        nt.links.new(tr.outputs["Color"], mul.inputs[0])
        nt.links.new(mul.outputs["Value"], bsdf.inputs["Roughness"])
    else:
        set_in(bsdf, "Roughness", rough)

    nr = PBR_DIR / f"{key}_nor_gl.jpg"
    if nr.exists() and nor > 0.0:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = bpy.data.images.load(str(nr))
        tn.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs["Vector"], tn.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = nor
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def wood_material(name, c1, c2, c3, scale, rough=0.45):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Y"
    wave.inputs["Scale"].default_value = 2.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.15
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (*c2, 1)
    e3 = ramp.color_ramp.elements.new(0.55)
    e3.color = (*c3, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    noise_bump(mat, scale=90, strength=0.05)
    set_in(bsdf, "Roughness", rough)
    return mat


def stone_material(name, base, vein, scale=3.5, rough=0.4, bump=0.08):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = scale
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (*base, 1)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (*vein, 1)
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    noise_bump(mat, scale=120, strength=bump)
    set_in(bsdf, "Roughness", rough)
    return mat


def tile_material(name, tile=(0.86, 0.85, 0.82), grout=(0.62, 0.61, 0.58),
                  tile_x=1.2, tile_y=0.6, rough=0.28, bump=0.02):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / tile_x, 1 / tile_y, 1.0)
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Mortar Size"].default_value = 0.012
    brick.inputs["Color1"].default_value = (*tile, 1)
    brick.inputs["Color2"].default_value = (0.82, 0.81, 0.78, 1)
    brick.inputs["Mortar"].default_value = (*grout, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], brick.inputs["Vector"])
    nt.links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
    set_in(bsdf, "Roughness", rough)
    noise_bump(mat, scale=200, strength=bump)
    return mat


def pbr_baldosa(name, key, tile_x=1.2, tile_y=0.6, joint=(0.84, 0.82, 0.78),
                tex_m=2.0, rot=0.0, rough=0.35, nor=0.4):
    """Material PBR de `data/pbr/<key>` con juntas de losa `tile_x`×`tile_y` m
    (2 mm, más claras). Devuelve None si falta la textura difusa."""
    diff = PBR_DIR / f"{key}_Diffuse.jpg"
    if not diff.exists():
        return None
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")

    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / tex_m, 1.0 / tex_m, 1.0)
    mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(rot))
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    td = nt.nodes.new("ShaderNodeTexImage")
    td.image = bpy.data.images.load(str(diff))
    td.image.colorspace_settings.name = "sRGB"
    nt.links.new(mp.outputs["Vector"], td.inputs["Vector"])

    mp2 = nt.nodes.new("ShaderNodeMapping")
    mp2.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    nt.links.new(tc.outputs["UV"], mp2.inputs["Vector"])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.squash = 1.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.002
    br.inputs["Brick Width"].default_value = tile_x
    br.inputs["Row Height"].default_value = tile_y
    br.inputs["Mortar Smooth"].default_value = 0.0
    br.inputs["Mortar"].default_value = (*joint, 1.0)
    nt.links.new(mp2.outputs["Vector"], br.inputs["Vector"])
    mixc = nt.nodes.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    fac = _sock(mixc.inputs, "Factor_Float")
    nt.links.new(br.outputs["Fac"], fac)
    _sock(mixc.inputs, "A_Color").default_value = (*joint, 1.0)
    nt.links.new(td.outputs["Color"], _sock(mixc.inputs, "B_Color"))
    nt.links.new(_sock(mixc.outputs, "Result_Color"), bsdf.inputs["Base Color"])

    if nor > 0.0 and (PBR_DIR / f"{key}_nor_gl.jpg").exists():
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = bpy.data.images.load(str(PBR_DIR / f"{key}_nor_gl.jpg"))
        tn.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs["Vector"], tn.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = nor
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    set_in(bsdf, "Roughness", rough)
    return mat


def build_materials():
    m = {}
    m["muro"] = principled("muro", base=(0.90, 0.88, 0.84), rough=0.88)
    noise_bump(m["muro"], scale=160, strength=0.03)
    m["techo"] = principled("techo", base=(0.95, 0.95, 0.94), rough=0.95)
    noise_bump(m["techo"], scale=120, strength=0.02)
    m["suelo_madera"] = pbr_material("suelo_madera", "oak_wood_planks", tex_m=1.5,
                                     rot=0.0, nor=0.5, rough_mul=0.85,
                                     value=1.06, sat=0.9) or \
        wood_material("suelo_madera", (0.40, 0.26, 0.155), (0.47, 0.32, 0.20),
                      (0.37, 0.24, 0.14), (0.09, 5.0, 1.0), rough=0.34)
    m["terraza"] = pbr_material("terraza_madera", "oak_wood_planks", tex_m=0.9,
                                nor=0.7, rough_mul=1.6, value=0.85, sat=0.7) or \
        wood_material("terraza_madera", (0.30, 0.20, 0.12), (0.38, 0.26, 0.16),
                      (0.26, 0.17, 0.10), (0.5, 2.0, 1.0), rough=0.6)
    m["pav_exterior"] = tile_material("pav_exterior", tile=(0.64, 0.63, 0.61),
                                      grout=(0.56, 0.55, 0.53), tile_x=0.6,
                                      tile_y=0.6, rough=0.5)
    m["marmol"] = pbr_material("marmol", "marble_01", tex_m=1.5, nor=0.4,
                               rough_mul=0.5) or \
        stone_material("marmol", (0.80, 0.78, 0.74), (0.62, 0.61, 0.59),
                       scale=1.4, rough=0.15)
    m["azulejo"] = pbr_material("azulejo", "marble_tiles", tex_m=0.9, nor=0.7,
                                rough_mul=0.9) or tile_material("azulejo")
    m["travertino"] = pbr_material("travertino", "travertine", tex_m=2.0,
                                   nor=0.6, rough_mul=1.0) or \
        stone_material("travertino", (0.72, 0.64, 0.51), (0.58, 0.50, 0.38),
                       scale=2.2, rough=0.6)
    m["travertino_porc"] = pbr_baldosa("travertino_porc", "travertine",
                                       tile_x=1.2, tile_y=0.6,
                                       joint=(0.84, 0.82, 0.78), tex_m=2.0,
                                       rot=90.0, rough=0.35, nor=0.5) or \
        m["travertino"]
    m["silestone"] = pbr_material("silestone", "silestone_charcoal", tex_m=1.0,
                                  nor=0.4, rough_mul=0.9) or \
        principled("silestone", base=(0.035, 0.037, 0.042), rough=0.35)
    m["dekton"] = pbr_material("dekton", "dekton_marmorio", tex_m=1.2, nor=0.3,
                               rough_mul=1.0) or \
        stone_material("dekton", (0.80, 0.79, 0.77), (0.66, 0.65, 0.64),
                       scale=1.4, rough=0.3)
    m["cerezo"] = pbr_material("cerezo", "cerezo", tex_m=0.8, nor=0.5,
                               rough_mul=1.0) or \
        wood_material("cerezo", (0.42, 0.16, 0.08), (0.59, 0.30, 0.17),
                      (0.36, 0.13, 0.07), (0.14, 4.0, 1.0), rough=0.30)
    m["hormigon_picado"] = pbr_material("hormigon_picado", "hormigon_picado",
                                        tex_m=0.6, nor=0.7, rough_mul=1.0) or \
        principled("hormigon_picado", base=(0.20, 0.20, 0.195), rough=0.65)
    m["roble_mel"] = pbr_material("roble_mel", "oak_veneer_01", tex_m=0.8,
                                  nor=0.35, rough_mul=1.05, value=1.0,
                                  sat=0.95) or m["roble"]
    m["grafito"] = principled("grafito", base=(0.075, 0.075, 0.080), rough=0.45)
    m["gris_osc"] = principled("gris_osc", base=(0.12, 0.12, 0.12), rough=0.5)
    m["resina"] = principled("resina", base=(0.90, 0.90, 0.89), rough=0.35)
    m["roble"] = pbr_material("roble", "oak_veneer_01", tex_m=1.83, rot=90,
                              nor=0.35, rough_mul=0.9) or \
        wood_material("roble", (0.38, 0.24, 0.135), (0.46, 0.30, 0.175),
                      (0.35, 0.22, 0.12), (0.18, 4.0, 1.0), rough=0.42)
    m["roble_h"] = pbr_material("roble_h", "oak_veneer_01", tex_m=1.83,
                                nor=0.35, rough_mul=0.9) or m["roble"]
    m["piedra_negra"] = principled("piedra_negra", base=(0.045, 0.042, 0.040),
                                   rough=0.18, spec=0.7)
    m["cobre"] = principled("cobre", base=(0.76, 0.45, 0.32), rough=0.32,
                            metal=1.0, spec=0.6)
    set_in(m["cobre"].node_tree.nodes["Principled BSDF"], "Anisotropic", 0.4)
    m["latón"] = principled("laton", base=(0.62, 0.48, 0.24), rough=0.35, metal=1.0)
    m["cromo"] = principled("cromo", base=(0.86, 0.87, 0.89), rough=0.06,
                            metal=1.0)
    m["aluminio"] = principled("aluminio", base=(0.030, 0.030, 0.032), rough=0.34,
                               metal=1.0, spec=0.6)
    set_in(m["aluminio"].node_tree.nodes["Principled BSDF"], "Anisotropic", 0.45)
    m["porcelana"] = principled("porcelana", base=(0.92, 0.92, 0.91), rough=0.10,
                                spec=0.5)
    m["fregadero"] = principled("fregadero", base=(0.025, 0.025, 0.028), rough=0.35)
    m["cristal"] = vidrio_arquitectonico("cristal")
    m["espejo"] = principled("espejo", base=(0.95, 0.95, 0.95), rough=0.02, metal=1.0)
    m["concreto"] = pbr_material("concreto", "brushed_concrete", tex_m=1.6,
                                 nor=0.3, rough_mul=0.9, sat=0.4, value=1.0)
    if m["concreto"] is None:
        m["concreto"] = principled("concreto", base=(0.62, 0.60, 0.57), rough=0.7)
        noise_bump(m["concreto"], scale=25, strength=0.25)
    m["tejido"] = pbr_material("tejido", "cotton_jersey", tex_m=0.53, nor=1.0,
                               rough_mul=1.0, value=1.05, sat=0.45) or \
        principled("tejido", base=(0.80, 0.76, 0.68), rough=0.95)
    m["tejido_claro"] = pbr_material("tejido_claro", "cotton_jersey", tex_m=0.53,
                                     nor=1.0, rough_mul=1.0, value=1.16,
                                     sat=0.5) or \
        principled("tejido_claro", base=(0.87, 0.84, 0.78), rough=0.95)
    m["lino"] = principled("lino", base=(0.79, 0.74, 0.64), rough=0.95)
    noise_bump(m["lino"], scale=300, strength=0.15)
    m["alfombra"] = pbr_material("alfombra", "hessian_230", tex_m=0.54, nor=0.9,
                                 value=1.08, sat=0.55) or m["tejido_claro"]
    m["cuero"] = pbr_material("cuero", "brown_leather", tex_m=0.7, nor=0.9,
                              rough_mul=0.9) or \
        principled("cuero", base=(0.25, 0.11, 0.05), rough=0.5)
    m["cortina"] = visillo("cortina")
    m["negro_mate"] = principled("negro_mate", base=(0.02, 0.02, 0.02), rough=0.6)
    m["metal_negro"] = principled("metal_negro", base=(0.035, 0.035, 0.037),
                                  rough=0.42, metal=1.0)
    m["blanco_laca"] = principled("blanco_laca", base=(0.93, 0.93, 0.91), rough=0.35)
    m["laca"] = m["blanco_laca"]
    m["blanco_electro"] = principled("blanco_electro", base=(0.92, 0.92, 0.90),
                                     rough=0.15, spec=0.75)
    m["vidrio_acido"] = principled("vidrio_acido", base=(0.92, 0.94, 0.93),
                                   rough=0.45, trans=0.55)
    m["pantalla"] = principled("pantalla", base=(0.012, 0.012, 0.014), rough=0.08,
                               spec=0.8)
    m["planta"] = principled("planta", base=(0.055, 0.13, 0.045), rough=0.55)
    m["tierra"] = principled("tierra", base=(0.045, 0.032, 0.022), rough=0.95)
    m["maceta"] = principled("maceta", base=(0.85, 0.84, 0.80), rough=0.7)
    # Láminas de los 3 cuadros del salón: una imagen procedural por cuadro
    # (paisaje abstracto cálido distinto: atardecer, campo y mar). Son nodos
    # TEX_IMAGE reales para que viajen a los dos GLB (exportar_glb.py las
    # conserva; hornear_visor.py no limpia los TEX_IMAGE). Antes los tres
    # compartían un único "lienzo" beige sin imagen y salían en blanco.
    paletas = [
        # arriba, medio, abajo, pos_sol, radio_sol, color_sol, semilla
        ((0.78, 0.42, 0.22), (0.89, 0.62, 0.36), (0.94, 0.83, 0.64),
         (0.62, 0.62), 0.16, (0.99, 0.92, 0.76), 11.0),   # atardecer
        ((0.62, 0.62, 0.44), (0.78, 0.70, 0.50), (0.45, 0.42, 0.30),
         (0.38, 0.66), 0.12, (0.97, 0.90, 0.72), 23.0),   # campo
        ((0.36, 0.50, 0.56), (0.72, 0.62, 0.50), (0.85, 0.74, 0.58),
         (0.50, 0.58), 0.14, (0.99, 0.93, 0.78), 37.0),   # mar
    ]
    for i, (ar, me, ab, sol_xy, sol_r, sol_c, sem) in enumerate(paletas):
        m[f"lienzo_{i}"] = lamina_cuadro(f"lienzo_{i}", 192, 288, ar, me, ab,
                                         sol_xy, sol_r, sol_c, sem)
    m["led"] = principled("led", base=(1.0, 0.93, 0.82), rough=0.5,
                          emission=(1.0, 0.86, 0.66), emit_str=2.5)
    m["led_frio"] = principled("led_frio", base=(0.94, 0.96, 1.0), rough=0.5,
                               emission=(0.88, 0.93, 1.0), emit_str=2.5)
    # Pantalla de la lámpara de pie (antes: base casi blanca + emisión 1,4
    # que se quemaba en ambos modos). Ahora ámbar translúcido ~3000 K.
    m["lampara_pantalla"] = pantalla_calida("lampara_pantalla")
    # Colchas de los 4 dormitorios (antes: tejido_claro casi blanco).
    m["colcha"] = colcha_rayas("colcha")
    m["ext_suelo"] = principled("ext_suelo", base=(0.45, 0.44, 0.42), rough=0.9)
    m["ext_edificio"] = principled("ext_edificio", base=(0.30, 0.28, 0.26), rough=0.95)
    # Barandilla de los balcones vecinos: bronce oscuro casi negro.
    m["bronce_barandilla"] = principled("bronce_barandilla",
                                        base=(0.09, 0.07, 0.055), rough=0.5,
                                        metal=1.0)
    # Fachada propia: revoco salmón-beige con juntas de panel 1,20×0,90 m.
    m["revoco"] = pbr_baldosa("revoco_fachada", "fachada_revoco",
                              tile_x=1.2, tile_y=0.9, joint=(0.80, 0.66, 0.58),
                              tex_m=2.0, rot=0.0, rough=0.88, nor=0.35) or \
        principled("revoco_fachada", base=(0.585, 0.365, 0.266), rough=0.88)
    return m


# ── geometría: modelo (x, z) -> Blender (x, -z), altura -> Z ─────────────────

def mesh_from(verts, faces, name, mat, smooth=False, bevel=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if bevel:
        md = ob.modifiers.new("bev", "BEVEL")
        md.width = bevel
        md.segments = 2
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(40)
    return ob


def poly_prism(pts, z0, z1, name, mat, bevel=0.0):
    n = len(pts)
    verts = [(x, -z, z0) for x, z in pts] + [(x, -z, z1) for x, z in pts]
    faces = [list(range(n))[::-1], list(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, j + n, i + n])
    return mesh_from(verts, faces, name, mat, bevel=bevel)


def poly_ngon(pts, h, name, mat):
    verts = [(x, -z, h) for x, z in pts]
    return mesh_from(verts, [list(range(len(pts)))], name, mat)


def box(x0, z0, x1, z1, h0, h1, name, mat, bevel=0.006):
    pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    return poly_prism(pts, h0, h1, name, mat, bevel=bevel)


def prismas(lista, name, mat):
    """Varios prismas en una sola malla. Cada uno = 8 vértices (x, z, h): cuatro
    de la base (x0z0, x1z0, x1z1, x0z1) y los cuatro de arriba en el mismo orden."""
    verts, faces = [], []
    for v8 in lista:
        b = len(verts)
        verts += [(x, -z, h) for x, z, h in v8]
        faces += [[b, b + 3, b + 2, b + 1], [b + 4, b + 5, b + 6, b + 7],
                  [b, b + 1, b + 5, b + 4], [b + 1, b + 2, b + 6, b + 5],
                  [b + 2, b + 3, b + 7, b + 6], [b + 3, b, b + 4, b + 7]]
    return mesh_from(verts, faces, name, mat)


def cajas(lista, name, mat):
    """Cajas alineadas (x0, z0, x1, z1, h0, h1) fusionadas en una malla."""
    return prismas([[(x0, z0, h0), (x1, z0, h0), (x1, z1, h0), (x0, z1, h0),
                     (x0, z0, h1), (x1, z0, h1), (x1, z1, h1), (x0, z1, h1)]
                    for x0, z0, x1, z1, h0, h1 in lista], name, mat)


def cylinder(x, z, r, h0, h1, name, mat, n=24):
    verts, faces = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        verts.append((x + r * math.cos(a), -z + r * math.sin(a), h0))
    for i in range(n):
        a = 2 * math.pi * i / n
        verts.append((x + r * math.cos(a), -z + r * math.sin(a), h1))
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, j + n, i + n])
    faces.append(list(range(n)))
    faces.append(list(range(n, 2 * n))[::-1])
    return mesh_from(verts, faces, name, mat, smooth=True)


def sphere(x, z, h, r, name, mat, seg=14, ring=7, sy=1.0):
    verts, faces = [], []
    for i in range(ring + 1):
        phi = math.pi * i / ring
        for j in range(seg):
            th = 2 * math.pi * j / seg
            verts.append((x + r * math.sin(phi) * math.cos(th),
                          -z + sy * r * math.sin(phi) * math.sin(th),
                          h + r * math.cos(phi)))
    for i in range(ring):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            c = (i + 1) * seg + (j + 1) % seg
            d = (i + 1) * seg + j
            faces.append([a, b, c, d])
    return mesh_from(verts, faces, name, mat, smooth=True)


def rot_box(cx, cz, largo, ancho, ang_deg, h0, h1, name, mat, bevel=0.0):
    """Caja girada `ang_deg` (sentido plano: 0=+x, 90=+z)."""
    a = math.radians(ang_deg)
    ux, uz = math.cos(a), math.sin(a)
    vx, vz = -uz, ux
    pts = []
    for sgn_l, sgn_a in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        px = cx + sgn_l * largo / 2 * ux + sgn_a * ancho / 2 * vx
        pz = cz + sgn_l * largo / 2 * uz + sgn_a * ancho / 2 * vz
        pts.append((px, pz))
    return poly_prism(pts, h0, h1, name, mat, bevel=bevel)


def elipsoide(cx, cz, h, rx, ry, rz, ang_deg, name, mat, seg=16, ring=8,
              tilt_deg=0.0):
    """Elipsoide orientado: semiejes (rx, ry, rz), giro en planta `ang_deg`
    e inclinación `tilt_deg` (alrededor del eje local Y)."""
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    t = math.radians(tilt_deg)
    ct, st = math.cos(t), math.sin(t)
    verts, faces = [], []
    for i in range(ring + 1):
        phi = math.pi * i / ring
        for j in range(seg):
            th = 2 * math.pi * j / seg
            ex = rx * math.sin(phi) * math.cos(th)
            ey = ry * math.sin(phi) * math.sin(th)
            ez = rz * math.cos(phi)
            ex, ez = ex * ct + ez * st, -ex * st + ez * ct
            verts.append((cx + ca * ex - sa * ey, -cz + sa * ex + ca * ey, h + ez))
    for i in range(ring):
        for j in range(seg):
            p = i * seg + j
            q = i * seg + (j + 1) % seg
            rr = (i + 1) * seg + (j + 1) % seg
            s = (i + 1) * seg + j
            faces.append([p, q, rr, s])
    return mesh_from(verts, faces, name, mat, smooth=True)


def caja_inclinada(x0, z0, x1, z1, h0, h1, dx_top, dz_top, name, mat, bevel=0.0):
    """Caja con la cara superior desplazada (colchones y cojines apoyados)."""
    pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    verts = [(x, -z, h0) for x, z in pts] + \
            [(x + dx_top, -(z + dz_top), h1) for x, z in pts]
    faces = [list(range(4))[::-1], list(range(4, 8))]
    for i in range(4):
        j = (i + 1) % 4
        faces.append([i, j, j + 4, i + 4])
    return mesh_from(verts, faces, name, mat, bevel=bevel)


def barra(p0, p1, r, name, mat, n=10):
    """Cilindro (barra/rodillo) entre dos puntos 3D del modelo (x, z, h)."""
    a = Vector((p0[0], -p0[1], p0[2]))
    b = Vector((p1[0], -p1[1], p1[2]))
    d = (b - a).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.98 else Vector((1, 0, 0))
    u = d.cross(up).normalized()
    v = d.cross(u).normalized()
    verts, faces = [], []
    for i in range(n):
        t = 2 * math.pi * i / n
        off = u * (r * math.cos(t)) + v * (r * math.sin(t))
        verts.append(tuple(a + off))
    for i in range(n):
        t = 2 * math.pi * i / n
        off = u * (r * math.cos(t)) + v * (r * math.sin(t))
        verts.append(tuple(b + off))
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, j + n, i + n])
    faces.append(list(range(n)))
    faces.append(list(range(n, 2 * n))[::-1])
    return mesh_from(verts, faces, name, mat, smooth=True)


def cortina(x0, z0, z1, h0, h1, ondas=5, amp=0.055, name="cortina", mat=None,
            seg=64):
    """Panel de cortina ondulado (plano x≈x0, cuelga de z0 a z1)."""
    verts, faces = [], []
    for i in range(seg + 1):
        t = i / seg
        z = z0 + (z1 - z0) * t
        x = x0 + amp * math.sin(2 * math.pi * ondas * t)
        verts.append((x, -z, h0))
        verts.append((x, -z, h1))
    for i in range(seg):
        a = 2 * i
        faces.append([a, a + 1, a + 3, a + 2])
    return mesh_from(verts, faces, name, mat)


def butaca_mariposa(cx, cz, ang_deg, m, name="butaca"):
    """Butaca mariposa (BKF): asiento colgante de cuero y varilla de acero."""
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)

    def pt(u, v, h):
        return (cx + ca * u - sa * v, cz + sa * u + ca * v, h)

    l, w = 0.80, 0.60
    metal, cuero = m["metal_negro"], m["cuero"]
    for side in (-1, 1):
        v = side * w / 2
        barra(pt(-l * 0.36, v, 0.0), pt(l * 0.33, v, 0.74), 0.011,
              f"{name}_pata_a_{side}", metal)
        barra(pt(l * 0.36, v, 0.0), pt(-l * 0.33, v, 0.80), 0.011,
              f"{name}_pata_b_{side}", metal)
        barra(pt(-l * 0.33, v, 0.80), pt(l * 0.33, v, 0.74), 0.011,
              f"{name}_rail_{side}", metal)
    barra(pt(-l * 0.33, -w / 2, 0.80), pt(-l * 0.33, w / 2, 0.80), 0.011,
          f"{name}_travesano_i", metal)
    barra(pt(l * 0.33, -w / 2, 0.74), pt(l * 0.33, w / 2, 0.74), 0.011,
          f"{name}_travesano_d", metal)

    nu, nv = 18, 7
    verts, faces = [], []
    for iu in range(nu + 1):
        u = iu / nu
        lu = (u - 0.5) * (l - 0.10)
        caida = 0.17 * math.sin(math.pi * u)
        for iv in range(nv + 1):
            v = iv / nv
            lv = (v - 0.5) * (w - 0.08)
            borde = 0.045 * math.sin(math.pi * v)
            p = pt(lu, lv, 0.775 - caida - borde)
            verts.append((p[0], -p[1], p[2]))
    for iu in range(nu):
        for iv in range(nv):
            p = iu * (nv + 1) + iv
            faces.append([p, p + 1, p + nv + 2, p + nv + 1])
    return mesh_from(verts, faces, f"{name}_lona", cuero, smooth=True)


def planta_monstera(x, z, name, m, alto=1.30, n_hojas=7):
    """Planta de hojas grandes (maceta, tierra, tallos y hojas)."""
    cylinder(x, z, 0.17, 0.0, 0.37, f"{name}_maceta", m["maceta"], n=22)
    cylinder(x, z, 0.155, 0.37, 0.385, f"{name}_tierra", m["tierra"], n=18)
    giros = (10, 62, 130, 195, 250, 305, 340, 85)
    for k in range(n_hojas):
        g = math.radians(giros[k % len(giros)])
        d = 0.14 + 0.10 * (k % 3)
        h = 0.50 + 0.14 * k
        base = (x + 0.05 * math.cos(g), z + 0.05 * math.sin(g), 0.35)
        top = (x + d * math.cos(g), z + d * math.sin(g), h)
        barra(base, top, 0.010, f"{name}_tallo_{k}", m["planta"])
        ang = math.degrees(g) + 90
        elipsoide(top[0], top[1], top[2] + 0.14, 0.075, 0.016, 0.17, ang,
                  f"{name}_hoja_{k}", m["planta"], tilt_deg=14)


def marco(orient, cx, cz, ancho, ante, head, name, mat, t=0.06, d=0.075):
    """Marco de ventana en 4 piezas (no macizo)."""
    if orient == "v":
        x = cx
        box(x - d / 2, cz - ancho / 2, x + d / 2, cz - ancho / 2 + t, ante, head,
            name + "_i", mat, bevel=0.0)
        box(x - d / 2, cz + ancho / 2 - t, x + d / 2, cz + ancho / 2, ante, head,
            name + "_d", mat, bevel=0.0)
        box(x - d / 2, cz - ancho / 2, x + d / 2, cz + ancho / 2, head - t, head,
            name + "_s", mat, bevel=0.0)
        box(x - d / 2, cz - ancho / 2, x + d / 2, cz + ancho / 2, ante, ante + t,
            name + "_b", mat, bevel=0.0)
    else:
        z = cz
        box(cx - ancho / 2, z - d / 2, cx - ancho / 2 + t, z + d / 2, ante, head,
            name + "_i", mat, bevel=0.0)
        box(cx + ancho / 2 - t, z - d / 2, cx + ancho / 2, z + d / 2, ante, head,
            name + "_d", mat, bevel=0.0)
        box(cx - ancho / 2, z - d / 2, cx + ancho / 2, z + d / 2, head - t, head,
            name + "_s", mat, bevel=0.0)
        box(cx - ancho / 2, z - d / 2, cx + ancho / 2, z + d / 2, ante, ante + t,
            name + "_b", mat, bevel=0.0)


def cut(obj, cutter):
    md = obj.modifiers.new("cut", "BOOLEAN")
    md.operation = "DIFFERENCE"
    md.object = cutter
    md.solver = "EXACT"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


# ── escena ───────────────────────────────────────────────────────────────────

def bbox(ob):
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    return min(xs), max(xs), min(ys), max(ys)


def vidrios_sin_sombra():
    """Los vidrios no proyectan sombra (truco estándar de arquitectura): el
    sol entra por los huecos sin que el cristal lo bloquee."""
    for ob in bpy.data.objects:
        if ob.type == "MESH" and (ob.name.startswith("vidrio") or
                                  ob.name.startswith("phoja_corr")):
            ob.visible_shadow = False


def uv_proyectar(escala=1.0):
    """Proyección tipo cubo por cara (para PBR y para el GLB del visor).

    Asigna UVs = coordenadas de los dos ejes no dominantes de la normal.
    Con `escala=1` las UV quedan en metros y los materiales PBR repiten la
    textura en su tamaño real (`tex_m`). Respeta las UV propias de los modelos
    CC0 (`asset_`), del entorno (`ext_`) y de los cuadros (`cuadro_*`, que
    llevan su lámina encuadrada 0..1 desde `uv_retrato`)."""
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name.startswith(("asset_", "ext_", "cuadro_")):
            continue
        me = ob.data
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        uvl = me.uv_layers.active.data
        for poly in me.polygons:
            n = poly.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
                co = me.vertices[me.loops[li].vertex_index].co
                if ax == 0:
                    uv = (co.y, co.z)
                elif ax == 1:
                    uv = (co.x, co.z)
                else:
                    uv = (co.x, co.y)
                uvl[li].uv = (uv[0] / escala, uv[1] / escala)


def _altura_estancia(e):
    a = e.get("altura")
    return a if a else ALTURAS_ESTANCIA.get(e["id"])


def _techo_en(x, z):
    """Cota de la cara inferior del techo en el punto (x, z) del plano: 2,30 bajo
    falso techo, 2,46 (forjado) en el resto. Los downlights cuelgan de ella."""
    for e in PLAN["estancias"]:
        if e["id"] != "terraza" and _dentro((x, z), e["pts"]):
            return _altura_estancia(e) or ALTURA
    return ALTURA


def build_shell(m):
    # suelo continuo de tarima en toda la vivienda
    poly_ngon(PLAN["huella"], 0.0, "suelo", m["suelo_madera"])
    # pavimentos: baños en porcelánico imitación travertino, balcón en gres
    for e in PLAN["estancias"]:
        if e["id"] in ("bano-1", "bano-2"):
            poly_ngon(e["pts"], 0.006, f"pav_{e['id']}", m["travertino_porc"])
        elif e["id"] == "terraza":
            poly_ngon(e["pts"], 0.004, "pav_terraza", m["pav_exterior"])
    # forjado superior a 2,46
    poly_ngon(PLAN["huella"], ALTURA, "techo", m["techo"])
    # falsos techos a 2,30 (bajada) en baños, vestidor, pasillo, cocina y recibidor
    # (misma cota superior que el forjado: en órbita ambos se ocultan y desde
    # abajo solo se ve la cara inferior; el hueco de 5 mm dejaba ver el forjado
    # sin hornear a través de la tabica)
    for e in PLAN["estancias"]:
        if _altura_estancia(e) == 2.30:
            poly_prism(e["pts"], 2.30, ALTURA, f"falso_techo_{e['id']}",
                       m["techo"], bevel=0.0)

    walls = []
    for i, w in enumerate(PLAN["muros"]):
        if w["tipo"] == "vidrio":
            continue
        walls.append(poly_prism(w["pts"], 0.0, ALTURA, f"muro_{i:03d}", m["muro"],
                                bevel=0.004))
    # tabicas de pladur (0,10 m) de 2,30 a 2,46 donde un cuarto bajo da a uno alto
    for k, (o, c, (a, b)) in enumerate((
            ("x", 1.81, (-0.42, 2.44)),      # cocina | salón
            ("x", 1.78, (2.44, 3.47)),       # recibidor | salón
            ("x", 4.11, (-3.24, -0.42)),     # vestidor | dormitorio principal
            ("x", -4.707, (-1.44, -0.52)),   # pasillo | dormitorio 3 (sobre P07)
    )):
        if o == "x":
            box(c - 0.05, a, c + 0.05, b, 2.30, ALTURA, f"tabica_{k}",
                m["techo"], bevel=0.0)
        else:
            box(a, c - 0.05, b, c + 0.05, 2.30, ALTURA, f"tabica_{k}",
                m["techo"], bevel=0.0)
    return walls


def build_revestimientos(m):
    """Alicatados de baños y lavadero, frente de TV del salón, pilar visto de
    hormigón picado y cornisas de led (3000 K). Todo va con prefijo `rev_` para
    que el visor y el control de mobiliario lo traten como estructura."""
    tra = m["travertino_porc"]
    T = 0.01                                  # grosor de las losas de revestimiento

    def rev(nombre, x0, z0, x1, z1, h0, h1, mat=None):
        box(x0, z0, x1, z1, h0, h1, nombre, mat or tra, bevel=0.0)

    # ── BAÑO 2 (bañera) · interior x[-4.00,-1.30], z[-3.24,-1.54] ──
    # pared oeste y muros norte/sur de la zona de bañera (x[-4.00,-3.31]) a 2,30
    rev("rev_b2_oeste", -4.00, -3.24, -4.00 + T, -1.54, 0.0, 2.30)
    rev("rev_b2_norte_bano", -4.00, -3.24, -3.31, -3.24 + T, 0.0, 2.30)
    rev("rev_b2_sur_bano", -4.00, -1.54 - T, -3.31, -1.54, 0.0, 2.30)
    # resto del muro norte a 1,20
    rev("rev_b2_norte", -3.31, -3.24, -1.77, -3.24 + T, 0.0, 1.20)
    # pilar de esquina x[-1.77,-1.30], z[-3.24,-2.94]
    rev("rev_b2_pilar_o", -1.77, -3.24, -1.77 + T, -2.94, 0.0, 1.20)
    rev("rev_b2_pilar_s", -1.77, -2.94 - T, -1.30, -2.94, 0.0, 1.20)
    # pared este (x=-1.30) y muro sur x[-3.31,-2.63] a 1,20 (hueco P04 libre)
    rev("rev_b2_este", -1.30, -2.94, -1.30 + T, -1.54, 0.0, 1.20)
    rev("rev_b2_sur", -3.31, -1.54 - T, -2.63, -1.54, 0.0, 1.20)

    # ── BAÑO 1 (ducha) · interior x[-0.93,1.75], z[-3.24,-1.54] ──
    rev("rev_b1_oeste", -0.93, -3.24, -0.93 + T, -1.54, 0.0, 2.30)
    rev("rev_b1_norte_ducha", -0.93, -3.24, -0.12, -3.24 + T, 0.0, 2.30)
    rev("rev_b1_sur_ducha", -0.93, -1.54 - T, -0.12, -1.54, 0.0, 2.30)
    # nicho x[-0.93,-0.64], z[-3.24,-3.08]
    rev("rev_b1_nicho_e", -0.64, -3.24, -0.64 + T, -3.08, 0.0, 2.30)
    rev("rev_b1_nicho_s", -0.93, -3.08 - T, -0.64, -3.08, 0.0, 2.30)
    # resto a 1,20
    rev("rev_b1_norte", 0.76, -3.24, 1.75, -3.24 + T, 0.0, 1.20)
    rev("rev_b1_tras_wc", -0.12, -3.08 - T, 0.76, -3.08, 0.0, 1.20)
    rev("rev_b1_este_n", 1.75 - T, -3.24, 1.75, -2.41, 0.0, 1.20)
    rev("rev_b1_este_s", 1.75 - T, -1.59, 1.75, -1.54, 0.0, 1.20)
    rev("rev_b1_sur", -0.12, -1.54 - T, 1.75, -1.54, 0.0, 1.20)

    # ── LAVADERO x[-1.16,0.08], z[2.49,4.30] a 1,20 (puerta libre) ──
    rev("rev_lav_norte", -1.16, 2.49, -0.72, 2.49 + T, 0.0, 1.20)
    rev("rev_lav_sur", -1.16, 4.30 - T, 0.08, 4.30, 0.0, 1.20)
    rev("rev_lav_oeste", -1.16, 2.49, -1.16 + T, 4.30, 0.0, 1.20)
    rev("rev_lav_este", 0.08 - T, 2.49, 0.08, 4.30, 0.0, 1.20)

    # ── SALÓN: frente de TV revestido (PE/I.01), losa de 0,06 m ──
    rev("rev_salon_tv", 3.77, -0.42, 7.88, -0.36, 0.0, 2.40, m["travertino_porc"])

    # ── Pilar visto de hormigón picado ──
    box(3.44, -0.42, 3.77, -0.10, 0.0, ALTURA, "rev_pilar_hormigon",
        m["hormigon_picado"], bevel=0.012)

    # ── Cornisas de led (3000 K) + sombra fina oscura ──
    def led(nombre, x0, z0, x1, z1, h):
        box(x0, z0, x1, z1, h - 0.04, h, f"rev_led_{nombre}", m["led"], bevel=0.0)
        box(x0 - 0.01, z0 - 0.01, x1 + 0.01, z1 + 0.01, h, h + 0.015,
            f"rev_gap_{nombre}", m["negro_mate"], bevel=0.0)

    led("salon", 3.77, -0.36, 7.88, -0.32, ALTURA - 0.02)
    led("dorm", 3.82, -3.18, 7.84, -3.14, ALTURA - 0.02)
    led("bano2", -3.99, -3.24, -3.95, -1.54, 2.30 - 0.02)
    led("bano1", -0.92, -3.08, -0.88, -1.54, 2.30 - 0.02)
    print(f"REVESTIMIENTOS {len([o for o in bpy.data.objects if o.name.startswith('rev_')])} piezas")


def _tris_muros():
    tris = []
    for w in PLAN["muros"]:
        if w["tipo"] == "vidrio":
            continue
        pts = w["pts"]
        for i in range(1, len(pts) - 1):
            tris.append((pts[0], pts[i], pts[i + 1]))
    return tris


def _en_tri(px, pz, tri):
    (ax, az), (bx, bz), (cx, cz) = tri
    d1 = (px - bx) * (az - bz) - (ax - bx) * (pz - bz)
    d2 = (px - cx) * (bz - cz) - (bx - cx) * (pz - cz)
    d3 = (px - ax) * (cz - az) - (cx - ax) * (pz - az)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def _tramos_junto_a_muro(x0, z0, ux, uz, a0, a1, tris, paso=0.04):
    """Subtramos de [a0, a1] del borde de estancia que tienen muro al lado
    (sondeo a 3, 8 y 14 cm a ambos lados). Los bordes abiertos entre estancias
    (salón-recibidor, pasillo…) no llevan rodapié."""
    nx, nz = -uz, ux
    xs = [x0 + ux * a0, x0 + ux * a1]
    zs = [z0 + uz * a0, z0 + uz * a1]
    cerca = [t for t in tris
             if min(p[0] for p in t) < max(xs) + 0.2 and max(p[0] for p in t) > min(xs) - 0.2
             and min(p[1] for p in t) < max(zs) + 0.2 and max(p[1] for p in t) > min(zs) - 0.2]
    out, ini, t = [], None, a0
    while t <= a1 + 1e-6:
        px, pz = x0 + ux * t, z0 + uz * t
        hay = any(_en_tri(px + s * nx * d, pz + s * nz * d, tri)
                  for d in (0.03, 0.08, 0.14) for s in (1, -1) for tri in cerca)
        if hay and ini is None:
            ini = t
        elif not hay and ini is not None:
            out.append((ini, t - paso / 2))
            ini = None
        t += paso
    if ini is not None:
        out.append((ini, a1))
    return [(max(a0, u0), min(a1, u1)) for u0, u1 in out if u1 - u0 > 0.12]


def build_rodapies(m):
    """Rodapié blanco de 9 cm siguiendo el contorno de cada estancia, cortado en
    los huecos de puertas y en el separador PA02."""
    aperturas = [(p["centro"][0], p["centro"][1], p["ancho"])
                 for p in PUERTAS["puertas"]]
    for t in PUERTAS["separadores"][0]["tramos"]:
        (ax, az), (bx, bz) = t["de"], t["a"]
        aperturas.append(((ax + bx) / 2, (az + bz) / 2,
                          math.hypot(bx - ax, bz - az)))
    alto, grosor, margen = 0.09, 0.013, 0.025
    tris = _tris_muros()
    libres = 0
    k = 0
    for e in PLAN["estancias"]:
        pts = e["pts"]
        cx = sum(p[0] for p in pts) / len(pts)
        cz = sum(p[1] for p in pts) / len(pts)
        for i in range(len(pts)):
            (x0, z0), (x1, z1) = pts[i], pts[(i + 1) % len(pts)]
            dx, dz = x1 - x0, z1 - z0
            L = math.hypot(dx, dz)
            if L < 0.25:
                continue
            ux, uz = dx / L, dz / L
            nx, nz = -uz, ux
            if nx * ((x0 + x1) / 2 - cx) + nz * ((z0 + z1) / 2 - cz) < 0:
                nx, nz = -nx, -nz
            cortes = []
            for ax, az, ancho in aperturas:
                t = (ax - x0) * ux + (az - z0) * uz
                dist = abs((ax - x0) * nx + (az - z0) * nz)
                if dist < 0.16 and 0 <= t <= L:
                    cortes.append((t - ancho / 2 - margen, t + ancho / 2 + margen))
            cortes.sort()
            tramos, ini = [], 0.0
            for a, b in cortes:
                if a > ini:
                    tramos.append((ini, min(a, L)))
                ini = max(ini, b)
            if ini < L:
                tramos.append((ini, L))
            junto = [s_ for a0, a1 in tramos
                     for s_ in _tramos_junto_a_muro(x0, z0, ux, uz, a0, a1, tris)]
            libres += sum(b - a for a, b in tramos) - sum(b - a for a, b in junto)
            for t0, t1 in junto:
                if t1 - t0 < 0.06:
                    continue
                q0 = (x0 + ux * t0, z0 + uz * t0)
                q1 = (x0 + ux * t1, z0 + uz * t1)
                quad = [q0, q1, (q1[0] + nx * grosor, q1[1] + nz * grosor),
                        (q0[0] + nx * grosor, q0[1] + nz * grosor)]
                poly_prism(quad, 0.0, alto, f"rodapie_{k:03d}", m["blanco_laca"])
                k += 1
    print(f"RODAPIES {k} tramos ({libres:.1f} m de bordes sin muro descartados)")


def suavizar_tapizados():
    """Almohadas, cojines y tapizados con subdivisión sobre el bisel: formas
    mullidas en vez de cajas."""
    pref = ("dp_almohada", "d1_almohada", "d2_almohada", "d3_almohada", "cojin_",
            "sofa_asiento", "sofa_respaldo", "sofa_brazo", "silla_",
            "d2_silla", "d3_silla", "est_silla")
    n = 0
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.startswith(pref) and "pie" not in ob.name:
            md = ob.modifiers.new("sub", "SUBSURF")
            md.levels = md.render_levels = 2
            n += 1
    print(f"TAPIZADOS suavizados: {n}")


def build_bandas(m, walls):
    """(Desactivado 2026-09-19: las 5 bandas de cinta —dorm. principal y dorm. 1
    al norte, salón-comedor, dorm. 2 y dorm. 3 al sur— no existen en el plano
    PEI.05 de carpintería exterior: la fachada norte es un muro macizo salvo
    V08, la sur solo tiene los huecos V06/V07 y el salón solo abre al este
    (V01). Ver overlay /tmp/opencode/bandas_v_overlay.png. Se conserva la
    función vacía para no romper la llamada en main().)"""
    return


def build_ventanas(m):
    for v in VENT["ventanas"]:
        h = v["hueco_plano"]
        cx, cz = h["centro"]
        ancho = v["ancho_m"]
        alto = v["alto_m"]
        ante = v["antepecho_m"] if v["antepecho_m"] is not None else 0.0
        if v["id"] in ("V01", "V05"):
            ante = 0.0
        head = min(ante + alto, ALTURA)
        vert = h["fachada"] in ("este", "oeste")
        t = 0.055
        # V03/V04/V05 (baños y lavadero) llevan vidrio translúcido al ácido
        glass = m["vidrio_acido"] if v["id"] in ("V03", "V04", "V05") else m["cristal"]
        if vert:
            x = cx
            marco("v", cx, cz, ancho, ante, head, f"marco_{v['id']}", m["aluminio"])
            box(x - 0.006, cz - ancho / 2 + t, x + 0.006, cz + ancho / 2 - t,
                ante + t, head - t, f"vidrio_{v['id']}", glass, bevel=0.0)
            n = max(1, int(round(ancho / 1.0)))
            for k in range(1, n):
                zk = cz - ancho / 2 + ancho * k / n
                box(x - 0.022, zk - 0.022, x + 0.022, zk + 0.022, ante, head,
                    f"mont_{v['id']}_{k}", m["aluminio"], bevel=0.0)
            if head < ALTURA:
                box(x - 0.14, cz - ancho / 2 - 0.05, x + 0.14, cz + ancho / 2 + 0.05,
                    head, ALTURA, f"dintel_{v['id']}", m["muro"], bevel=0.0)
            if ante > 0.01:
                box(x - 0.14, cz - ancho / 2 - 0.05, x + 0.14, cz + ancho / 2 + 0.05,
                    0.0, ante, f"antepecho_{v['id']}", m["muro"], bevel=0.0)
        else:
            z = cz
            marco("h", cx, cz, ancho, ante, head, f"marco_{v['id']}", m["aluminio"])
            box(cx - ancho / 2 + t, z - 0.006, cx + ancho / 2 - t, z + 0.006,
                ante + t, head - t, f"vidrio_{v['id']}", glass, bevel=0.0)
            n = max(1, int(round(ancho / 1.0)))
            for k in range(1, n):
                xk = cx - ancho / 2 + ancho * k / n
                box(xk - 0.022, z - 0.022, xk + 0.022, z + 0.022, ante, head,
                    f"mont_{v['id']}_{k}", m["aluminio"], bevel=0.0)
            if head < ALTURA:
                box(cx - ancho / 2 - 0.05, z - 0.14, cx + ancho / 2 + 0.05, z + 0.14,
                    head, ALTURA, f"dintel_{v['id']}", m["muro"], bevel=0.0)
            if ante > 0.01:
                box(cx - ancho / 2 - 0.05, z - 0.14, cx + ancho / 2 + 0.05, z + 0.14,
                    0.0, ante, f"antepecho_{v['id']}", m["muro"], bevel=0.0)


def build_puertas(m):
    """Puertas interiores según data/puertas.json (PE.A.02 + PEI.07).

    Tipos: abatibles lacadas blancas (P01, P02, P05, P06, P07), corredera de
    bolsillo P04, vidrieras de roble (P03) y acero negro (PL), entrada
    existente PE (panelada, cerrada) y separador fijo PA02. Los huecos ya
    vienen abiertos en PLAN["muros"]; aquí solo marcos, hojas y dinteles.
    Nombres compatibles con el filtro del visor (pmarco_*, pdintel_*, phoja_*,
    dintel_*, vidrio_*).
    """
    laca, roble = m["blanco_laca"], m["roble"]
    acido, negro = m["vidrio_acido"], m["metal_negro"]
    por_id = {p["id"]: p for p in PUERTAS["puertas"]}
    centro_est = {e["id"]: (sum(p[0] for p in e["pts"]) / len(e["pts"]),
                            sum(p[1] for p in e["pts"]) / len(e["pts"]))
                  for e in PLAN["estancias"]}

    def dir_abre(p):
        """Ángulo (grados) de la hoja abierta 90° hacia la estancia `abre_a`."""
        base = 0.0 if p["pared"] == "h" else 90.0
        cen = centro_est.get(p.get("abre_a"))
        if cen is None:
            return base
        hx, hz = p["bisagra_xz"]
        d = [math.hypot(hx + math.cos(math.radians(base + s)) - cen[0],
                        hz + math.sin(math.radians(base + s)) - cen[1])
             for s in (90, -90)]
        return base + (90.0 if d[0] <= d[1] else -90.0)

    def marco(pid, p, mat, t=0.06, d=0.20):
        h, ancho = p["alto"], p["ancho"]
        cx, cz = p["centro"]
        if p["pared"] == "h":
            x0, x1 = cx - ancho / 2, cx + ancho / 2
            for suf, xx in (("i", x0), ("d", x1)):
                box(xx - t / 2, cz - d / 2, xx + t / 2, cz + d / 2, 0, h,
                    f"pmarco_{pid}_{suf}", mat, bevel=0.0)
            box(x0 - t / 2, cz - d / 2, x1 + t / 2, cz + d / 2, h, h + 0.06,
                f"pmarco_{pid}_s", mat, bevel=0.0)
        else:
            z0, z1 = cz - ancho / 2, cz + ancho / 2
            for suf, zz in (("i", z0), ("d", z1)):
                box(cx - d / 2, zz - t / 2, cx + d / 2, zz + t / 2, 0, h,
                    f"pmarco_{pid}_{suf}", mat, bevel=0.0)
            box(cx - d / 2, z0 - t / 2, cx + d / 2, z1 + t / 2, h, h + 0.06,
                f"pmarco_{pid}_s", mat, bevel=0.0)

    def dintel(pid, p, d=0.20):
        if p.get("en_paso") or p["tipo"] == "fijo":
            return
        h, ancho = p["alto"], p["ancho"]
        cx, cz = p["centro"]
        if p["pared"] == "h":
            box(cx - ancho / 2 - 0.03, cz - d / 2, cx + ancho / 2 + 0.03,
                cz + d / 2, h, ALTURA, f"dintel_{pid}", m["muro"], bevel=0.0)
        else:
            box(cx - d / 2, cz - ancho / 2 - 0.03, cx + d / 2,
                cz + ancho / 2 + 0.03, h, ALTURA, f"dintel_{pid}", m["muro"],
                bevel=0.0)

    def caja_hoja(name, hinge, ang, u0, u1, v0, v1, h0, h1, mat, bevel=0.0):
        """Caja en el sistema de la hoja: u a lo largo (desde la bisagra), v el
        grosor, h la altura."""
        ca, sa = math.cos(ang), math.sin(ang)

        def P(u, v):
            return (hinge[0] + ca * u - sa * v, hinge[1] + sa * u + ca * v)

        poly_prism([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)], h0, h1,
                   name, mat, bevel=bevel)

    def hoja_abatible(pid, p, mat, grueso=0.04):
        ang = math.radians(dir_abre(p))
        hx, hz = p["bisagra_xz"]
        largo = p["hoja_ancho"]
        cx = hx + math.cos(ang) * largo / 2
        cz = hz + math.sin(ang) * largo / 2
        rot_box(cx, cz, largo, grueso, math.degrees(ang), 0.02, p["alto"],
                f"phoja_{pid}", mat, bevel=0.004)

    def tirador(pid, p, mat):
        """Tirador de manivela cerca del canto libre, a ~1,05 m."""
        ang = math.radians(dir_abre(p))
        hx, hz = p["bisagra_xz"]
        ex = hx + math.cos(ang) * (p["hoja_ancho"] - 0.09)
        ez = hz + math.sin(ang) * (p["hoja_ancho"] - 0.09)
        nx, nz = -math.sin(ang), math.cos(ang)
        box(ex - 0.03 + nx * 0.02, ez - 0.03 + nz * 0.02,
            ex + 0.03 + nx * 0.09, ez + 0.03 + nz * 0.09, 1.03, 1.07,
            f"pmarco_{pid}_man", mat, bevel=0.0)

    # ── abatibles lacadas blancas ────────────────────────────────────────────
    for pid in ("P01", "P02", "P05", "P06", "P07"):
        p = por_id[pid]
        marco(pid, p, laca)
        dintel(pid, p)
        hoja_abatible(pid, p, laca)
        tirador(pid, p, laca)

    # ── P04: corredera de bolsillo (30 % visible, uñero blanco) ──────────────
    p = por_id["P04"]
    marco("P04", p, laca, t=0.05, d=0.12)
    dintel("P04", p)
    cx, zc, h = p["centro"][0], p["centro"][1], p["alto"]
    x0, x1 = cx - p["ancho"] / 2, cx + p["ancho"] / 2
    vis = 0.30 * p["hoja_ancho"]
    este = p.get("bolsillo") != "O"
    lx0, lx1 = (x1 - 0.02 - vis, x1 - 0.02) if este else (x0 + 0.02, x0 + 0.02 + vis)
    box(lx0, zc - 0.02, lx1, zc + 0.02, 0.02, h, "phoja_P04", laca, bevel=0.004)
    libre = lx0 if este else lx1
    box(libre - 0.09 if not este else libre + 0.01, zc - 0.024,
        libre - 0.01 if not este else libre + 0.09, zc + 0.024, 1.00, 1.12,
        "pmarco_P04_unero", m["negro_mate"], bevel=0.0)

    # ── P03: vidriera al pasillo (roble + vidrio ácido, travesaño 0,88 m) ────
    p = por_id["P03"]
    marco("P03", p, roble, t=0.05, d=0.14)
    dintel("P03", p)
    ang = math.radians(dir_abre(p))
    hx, hz = p["bisagra_xz"]
    L, alto = p["hoja_ancho"], p["alto"]
    t = 0.05
    caja_hoja("phoja_P03_i", (hx, hz), ang, 0.0, t, -0.025, 0.025, 0.0, alto, roble)
    caja_hoja("phoja_P03_d", (hx, hz), ang, L - t, L, -0.025, 0.025, 0.0, alto, roble)
    for suf, (h0, h1) in (("bajo", (0.0, t)), ("alto", (alto - t, alto)),
                          ("rail", (0.84, 0.92))):
        caja_hoja(f"phoja_P03_{suf}", (hx, hz), ang, t, L - t, -0.025, 0.025,
                  h0, h1, roble)
    for suf, (h0, h1) in (("vid_bajo", (t, 0.84)), ("vid_alto", (0.92, alto - t))):
        caja_hoja(f"vidrio_P03_{suf}", (hx, hz), ang, t, L - t, -0.006, 0.006,
                  h0, h1, acido)
    caja_hoja("pmarco_P03_tir", (hx, hz), ang, L - 0.18, L - 0.08, 0.035, 0.055,
              0.95, 1.15, roble, bevel=0.004)

    # ── PL: vidriera negra del lavadero (0,70 × 2,30) ────────────────────────
    p = por_id["PL"]
    marco("PL", p, negro, t=0.03, d=0.10)
    dintel("PL", p)
    ang = math.radians(dir_abre(p))
    hx, hz = p["bisagra_xz"]
    L, alto = p["hoja_ancho"], p["alto"]
    t = 0.03
    caja_hoja("phoja_PL_i", (hx, hz), ang, 0.0, t, -0.02, 0.02, 0.0, alto, negro)
    caja_hoja("phoja_PL_d", (hx, hz), ang, L - t, L, -0.02, 0.02, 0.0, alto, negro)
    for suf, (h0, h1) in (("bajo", (0.0, t)), ("alto", (alto - t, alto))):
        caja_hoja(f"phoja_PL_{suf}", (hx, hz), ang, t, L - t, -0.02, 0.02,
                  h0, h1, negro)
    caja_hoja("vidrio_PL", (hx, hz), ang, t, L - t, -0.006, 0.006, t, alto - t,
              acido)

    # ── PE: entrada existente (hoja cerrada panelada en blanco) ──────────────
    p = por_id["PE"]
    marco("PE", p, laca, t=0.06, d=0.30)
    dintel("PE", p, d=0.30)
    cx, zc, h = p["centro"][0], p["centro"][1], p["alto"]
    x0, x1 = cx - p["ancho"] / 2, cx + p["ancho"] / 2
    box(x0 + 0.02, zc - 0.02, x1 - 0.02, zc + 0.02, 0.02, h, "phoja_PE",
        laca, bevel=0.004)
    for k, (h0, h1) in enumerate(((0.12, 0.86), (1.02, 1.85))):
        box(x0 + 0.10, zc - 0.038, x1 - 0.10, zc - 0.018, h0, h1,
            f"phoja_PE_panel_{k}", laca, bevel=0.004)
    box(x1 - 0.16, zc - 0.03, x1 - 0.10, zc + 0.03, 1.03, 1.07,
        "pmarco_PE_man", laca, bevel=0.0)

    # ── PA02: separador fijo de vidrio al ácido con travesaño de roble ───────
    for k, tramo in enumerate(PUERTAS["separadores"][0]["tramos"]):
        (ax, az), (bx, bz) = tramo["de"], tramo["a"]
        L = math.hypot(bx - ax, bz - az)
        ang = math.degrees(math.atan2(bz - az, bx - ax))
        cxm, czm = (ax + bx) / 2, (az + bz) / 2
        rot_box(cxm, czm, L, 0.02, ang, 0.0, 2.30, f"vidrio_pa02_{k}", acido,
                bevel=0.0)
        rot_box(cxm, czm, L, 0.05, ang, 0.84, 0.90,
                f"pmarco_pa02_{k}_rail", roble, bevel=0.0)
        rot_box(cxm, czm, L, 0.05, ang, 2.26, 2.30,
                f"pmarco_pa02_{k}_cab", roble, bevel=0.0)
        for suf, (ex, ez) in (("i", (ax, az)), ("d", (bx, bz))):
            box(ex - 0.02, ez - 0.02, ex + 0.02, ez + 0.02, 0.0, 2.30,
                f"pmarco_pa02_{k}_{suf}", roble, bevel=0.0)


def cargar_asset(nombre, alto, x, z, ang=0.0, h=0.0):
    """Coloca un modelo CC0 de `data/assets/<nombre>/` (glTF 2k de Poly Haven,
    https://api.polyhaven.com/files/<nombre>) escalado a `alto` m de altura.
    Devuelve False si falta el modelo: el llamador cae a la geometría
    procedural. El prefijo `asset_` hace que `exportar_glb.py` los excluya del
    GLB del visor (tamaño contenido)."""
    ruta = ASSETS_DIR / nombre / f"{nombre}_2k.gltf"
    if not ruta.is_file():
        return False
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ruta))
    nuevos = [o for o in bpy.data.objects if o not in antes]
    if not nuevos:
        return False
    raices = [o for o in nuevos if o.parent not in nuevos]
    xs, zs = [], []
    for ob in nuevos:
        if ob.type != "MESH":
            continue
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            xs.append(w.x)
            zs.append(w.z)
    if not zs:
        return False
    alto_real = max(zs) - min(zs)
    if alto_real <= 1e-6:
        return False
    esc = alto / alto_real
    em = bpy.data.objects.new(f"asset_{nombre}", None)
    bpy.context.collection.objects.link(em)
    for r in raices:
        r.parent = em
    em.scale = (esc, esc, esc)
    em.rotation_euler = (0.0, 0.0, math.radians(ang))
    em.location = (x, -z, h - min(zs) * esc)
    for ob in nuevos:
        ob.name = f"asset_{nombre}_{ob.name}"
    del xs
    return True


def build_mobiliario(m):
    """Mobiliario y carpintería del proyecto (piezas y cotas en
    `mobiliario_proyecto.py`, tomadas de PE/I.06-07, PE/A.03-04 y PE/I.09)."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import mobiliario_proyecto
    mobiliario_proyecto.construir(m, sys.modules[__name__])


# ── entorno urbano (OSM) ─────────────────────────────────────────────────────
# Todo lo del entorno lleva prefijo `ext_`: exportar_glb.py lo excluye del visor.

PALETA_FACHADAS = [          # revocos y ladrillo del barrio (lineal)
    (0.60, 0.38, 0.27),      # salmón (el propio edificio, semilla 0)
    (0.63, 0.53, 0.41),      # beige
    (0.70, 0.68, 0.63),      # blanco roto
    (0.64, 0.46, 0.40),      # rosa pálido
    (0.60, 0.47, 0.27),      # ocre
    (0.38, 0.17, 0.11),      # ladrillo
    (0.50, 0.52, 0.54),      # gris
]

TIENDAS = [                  # rótulos de los bajos comerciales (fotos de la calle)
    (0.55, 0.07, 0.05),      # rojo (pizzería)
    (0.05, 0.10, 0.32),      # azul
    (0.08, 0.26, 0.12),      # verde
    (0.78, 0.76, 0.70),      # crema
    (0.62, 0.22, 0.05),      # naranja
    (0.10, 0.32, 0.36),      # azul verdoso
]


def _sock(sockets, ident):
    return next(s for s in sockets if s.identifier == ident)


def _math(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def _mix(nt, fac, a, b):
    """Mezcla de color (a -> b según fac); a/b pueden ser tuplas o salidas."""
    n = nt.nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    f = _sock(n.inputs, "Factor_Float")
    if isinstance(fac, (int, float)):
        f.default_value = fac
    else:
        nt.links.new(fac, f)
    for ident, x in (("A_Color", a), ("B_Color", b)):
        s = _sock(n.inputs, ident)
        if isinstance(x, tuple):
            s.default_value = (*x[:3], 1.0)
        else:
            nt.links.new(x, s)
    return _sock(n.outputs, "Result_Color")


def _rampa(nt, fac, colores):
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.interpolation = "CONSTANT"
    els = r.color_ramp.elements
    while len(els) < len(colores):
        els.new(0.5)
    for i in range(len(colores)):        # posiciones primero: al moverlas se reordenan
        els[i].position = i / len(colores)
    for i, c in enumerate(colores):
        els[i].color = (*c, 1.0)
    nt.links.new(fac, r.inputs["Fac"])
    return r.outputs["Color"]


def _uv_xy(nt):
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    return sep.outputs["X"], sep.outputs["Y"]


def mat_fachadas():
    """Revoco con retícula de ventanas: Brick Texture sobre UV métricas (u a lo
    largo de la fachada, v = altura sobre la calle). Revoco por edificio
    (atributo de cara `semilla`), persianas bajadas a distinta altura, línea de
    forjado, bajo comercial oscuro y cubierta en el material 1."""
    mat = bpy.data.materials.new("ext_fachada")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    u, v = _uv_xy(nt)
    vp = _math(nt, "SUBTRACT", v, BAJO - PLANTA)   # filas alineadas con las plantas
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(u, comb.inputs["X"])
    nt.links.new(vp, comb.inputs["Y"])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.squash = 1.0
    for k, val in (("Scale", 1.0), ("Mortar Size", 0.8), ("Mortar Smooth", 0.0),
                   ("Bias", 0.0), ("Brick Width", 3.1), ("Row Height", PLANTA)):
        br.inputs[k].default_value = val
    br.inputs["Color1"].default_value = (0.0, 0.0, 0.0, 1.0)
    br.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1.0)
    nt.links.new(comb.outputs[0], br.inputs["Vector"])
    muro = br.outputs["Fac"]                              # 1 = revoco, 0 = hueco
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(br.outputs["Color"], sep.inputs[0])
    rnd = sep.outputs[0]                                  # aleatorio por ventana

    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_type = "GEOMETRY"
    at.attribute_name = "semilla"
    revoco = _rampa(nt, at.outputs["Fac"], PALETA_FACHADAS)
    vr = _math(nt, "FRACT", _math(nt, "DIVIDE", vp, PLANTA))
    forjado = _math(nt, "LESS_THAN", vr, 0.05)
    revoco = _mix(nt, _math(nt, "MULTIPLY", forjado, 0.35), revoco, (0.0, 0.0, 0.0))

    umbral = _math(nt, "SUBTRACT", 0.73, _math(nt, "MULTIPLY", rnd, 0.42))
    persiana = _math(nt, "GREATER_THAN", vr, umbral)
    tono = _math(nt, "GREATER_THAN", _math(nt, "FRACT", _math(nt, "MULTIPLY", rnd, 5.3)), 0.55)
    col_pers = _mix(nt, tono, (0.52, 0.46, 0.36), (0.68, 0.67, 0.64))
    hueco = _mix(nt, persiana, (0.016, 0.02, 0.026), col_pers)
    color = _mix(nt, muro, hueco, revoco)

    # ── toldos, equipos de A/A y bajos comerciales (fotos de la calle) ──
    ventana = _math(nt, "SUBTRACT", 1.0, muro, clamp=True)
    fx = _math(nt, "MULTIPLY",
               _math(nt, "FRACT", _math(nt, "DIVIDE", u, 3.1)), 3.1)

    # toldo crema con raya en el tercio superior (~1/3 de ventanas, como en
    # las fotos de la calle; sincronizado con scripts/visor_realista.js)
    hay_toldo = _math(nt, "MULTIPLY",
                      _math(nt, "GREATER_THAN", rnd, 0.22),
                      _math(nt, "LESS_THAN", rnd, 0.58))
    banda_t = _math(nt, "MULTIPLY",
                    _math(nt, "GREATER_THAN", vr, 0.60),
                    _math(nt, "LESS_THAN", vr, 0.72))
    toldo = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", ventana, hay_toldo),
                  banda_t)
    raya = _math(nt, "GREATER_THAN",
                 _math(nt, "FRACT", _math(nt, "MULTIPLY", rnd, 7.7)), 0.5)
    col_toldo = _mix(nt, raya, (0.72, 0.66, 0.52), (0.82, 0.78, 0.67))
    color = _mix(nt, toldo, color, col_toldo)
    sombra_t = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", ventana, hay_toldo),
                     _math(nt, "MULTIPLY",
                           _math(nt, "GREATER_THAN", vr, 0.585),
                           _math(nt, "LESS_THAN", vr, 0.605)))
    color = _mix(nt, sombra_t, color, (0.30, 0.28, 0.24))

    # equipo de A/A junto al borde derecho (~1/4 de ventanas, como en
    # las fotos de la calle; sincronizado con scripts/visor_realista.js)
    hay_aa = _math(nt, "MULTIPLY",
                   _math(nt, "GREATER_THAN", rnd, 0.05),
                   _math(nt, "LESS_THAN", rnd, 0.30))
    aa_x = _math(nt, "MULTIPLY",
                 _math(nt, "GREATER_THAN", fx, 2.15),
                 _math(nt, "LESS_THAN", fx, 2.65))
    aa_v = _math(nt, "MULTIPLY",
                 _math(nt, "GREATER_THAN", vr, 0.30),
                 _math(nt, "LESS_THAN", vr, 0.40))
    aa = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", ventana, hay_aa),
               _math(nt, "MULTIPLY", aa_x, aa_v))
    rejilla = _math(nt, "GREATER_THAN",
                    _math(nt, "FRACT", _math(nt, "MULTIPLY", vr, 60.0)), 0.5)
    col_aa = _mix(nt, rejilla, (0.62, 0.62, 0.60), (0.76, 0.76, 0.74))
    color = _mix(nt, aa, color, col_aa)

    # bajo comercial: escaparate oscuro y rótulo de color por edificio
    bajo = _math(nt, "LESS_THAN", v, BAJO - 0.35)
    escaparate = _math(nt, "MULTIPLY", bajo, _math(nt, "LESS_THAN", v, 2.7))
    color = _mix(nt, escaparate, color, (0.020, 0.026, 0.038))
    rotulo = _math(nt, "MULTIPLY", bajo, _math(nt, "GREATER_THAN", v, 2.7))
    color = _mix(nt, rotulo, color, _rampa(nt, at.outputs["Fac"], TIENDAS))
    nt.links.new(color, bsdf.inputs["Base Color"])
    rough = _math(nt, "ADD", 0.14, _math(nt, "MULTIPLY", muro, 0.76))
    rough = _math(nt, "ADD", _math(nt, "MULTIPLY", rough,
                                   _math(nt, "SUBTRACT", 1.0, bajo)),
                  _math(nt, "MULTIPLY", bajo, 0.3))
    nt.links.new(rough, bsdf.inputs["Roughness"])

    cub = bpy.data.materials.new("ext_cubierta")
    cub.use_nodes = True
    nc = cub.node_tree
    bc = nc.nodes["Principled BSDF"]
    at2 = nc.nodes.new("ShaderNodeAttribute")
    at2.attribute_type = "GEOMETRY"
    at2.attribute_name = "semilla"
    base = _rampa(nc, at2.outputs["Fac"], [(0.42, 0.19, 0.14), (0.50, 0.30, 0.25),
                                           (0.55, 0.54, 0.50), (0.46, 0.24, 0.18)])
    nz = nc.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.6
    base = _mix(nc, _math(nc, "MULTIPLY", nz.outputs["Fac"], 0.35), base, (0.30, 0.28, 0.26))
    nc.links.new(base, bc.inputs["Base Color"])
    set_in(bc, "Roughness", 0.9)
    return mat, cub


def _desglose_via(w):
    """(carriles, bandas de aparcamiento) de una calzada: extraer_entorno da
    ancho = carriles·3,1 + aparcamiento·2,2 por banda y la solución es única."""
    for k in (0, 1, 2):
        n = (w - 2.2 * k) / 3.1
        if round(n) >= 1 and abs(n - round(n)) < 0.06:
            return int(round(n)), k
    return max(1, int(w // 3.1)), 0


def mat_asfalto():
    """Asfalto con bordillo, rígola, línea de aparcamiento y separadores de carril
    en UV métricas (u a lo largo, v a lo ancho desde el lado derecho). Atributos
    de cara: `ancho` y `p_der`/`p_izq` (ancho de la banda de aparcamiento)."""
    mat = bpy.data.materials.new("ext_asfalto")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    u, v = _uv_xy(nt)

    def atr(nombre):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_type = "GEOMETRY"
        a.attribute_name = nombre
        return a.outputs["Fac"]

    def entre(x, lo, hi):
        return _math(nt, "MULTIPLY", _math(nt, "GREATER_THAN", x, lo),
                     _math(nt, "LESS_THAN", x, hi))

    w, pd, pi_ = atr("ancho"), atr("p_der"), atr("p_izq")
    vd = _math(nt, "SUBTRACT", w, v)
    bord = _math(nt, "MAXIMUM", _math(nt, "LESS_THAN", v, 0.12),
                 _math(nt, "LESS_THAN", vd, 0.12))
    rig = _math(nt, "MAXIMUM", entre(v, 0.12, 0.40), entre(vd, 0.12, 0.40))

    def raya(x, ref):        # línea de 10 cm a la distancia `ref` del borde (si hay banda)
        return _math(nt, "MULTIPLY", _math(nt, "GREATER_THAN", ref, 0.1),
                     _math(nt, "LESS_THAN", _math(nt, "ABSOLUTE", _math(
                         nt, "SUBTRACT", x, ref)), 0.05))

    lin_ap = _math(nt, "MAXIMUM", raya(v, pd), raya(vd, pi_))
    # sin aparcamiento: línea de borde continua junto a la rígola
    borde1 = _math(nt, "MULTIPLY", entre(v, 0.52, 0.64), _math(nt, "LESS_THAN", pd, 0.1))
    borde2 = _math(nt, "MULTIPLY", entre(vd, 0.52, 0.64), _math(nt, "LESS_THAN", pi_, 0.1))
    # separadores de carril discontinuos cada 3,1 m desde el borde de la banda
    vv = _math(nt, "SUBTRACT", v, pd)
    carril = _math(nt, "LESS_THAN", _math(nt, "ABSOLUTE", _math(
        nt, "SUBTRACT", vv, _math(nt, "MULTIPLY", _math(nt, "ROUND", _math(
            nt, "DIVIDE", vv, 3.1)), 3.1))), 0.06)
    dentro_ = _math(nt, "MULTIPLY", _math(nt, "GREATER_THAN", vv, 0.9),
                    _math(nt, "GREATER_THAN", _math(nt, "SUBTRACT", vd, pi_), 0.9))
    trazo = _math(nt, "LESS_THAN", _math(nt, "FRACT", _math(nt, "DIVIDE", u, 9.0)), 0.35)
    carril = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", carril, dentro_), trazo)
    marca = _math(nt, "MAXIMUM", _math(nt, "MAXIMUM", lin_ap, carril),
                  _math(nt, "MAXIMUM", borde1, borde2))
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.8
    base = _mix(nt, _math(nt, "MULTIPLY", nz.outputs["Fac"], 0.5),
                (0.085, 0.085, 0.088), (0.125, 0.122, 0.118))
    color = _mix(nt, rig, base, (0.20, 0.20, 0.20))
    color = _mix(nt, bord, color, (0.46, 0.45, 0.43))
    color = _mix(nt, marca, color, (0.62, 0.62, 0.58))
    nt.links.new(color, bsdf.inputs["Base Color"])
    set_in(bsdf, "Roughness", 0.85)
    return mat


def mat_suelo_urbano():
    """Acera de baldosa 40×40 en coordenadas de objeto (mundo)."""
    mat = bpy.data.materials.new("ext_acera")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    for k, val in (("Scale", 1.0), ("Mortar Size", 0.006), ("Brick Width", 0.4),
                   ("Row Height", 0.4), ("Bias", 0.0)):
        br.inputs[k].default_value = val
    br.inputs["Color1"].default_value = (0.50, 0.48, 0.44, 1.0)
    br.inputs["Color2"].default_value = (0.57, 0.55, 0.51, 1.0)
    br.inputs["Mortar"].default_value = (0.38, 0.36, 0.33, 1.0)
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], bsdf.inputs["Base Color"])
    set_in(bsdf, "Roughness", 0.8)
    return mat


def mat_plano(nombre, c1, c2, escala, rough=0.9):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = escala
    nt.links.new(_mix(nt, nz.outputs["Fac"], c1, c2), bsdf.inputs["Base Color"])
    set_in(bsdf, "Roughness", rough)
    return mat


def _limpiar(pts):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) > 0.05:
            out.append(tuple(p))
    if len(out) > 2 and math.dist(out[0], out[-1]) <= 0.05:
        out.pop()
    return out


def _dentro(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _dist_seg(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(ax + t * dx - p[0], ay + t * dy - p[1])


class _Malla:
    """Acumula caras con UV por esquina, material y atributos de cara."""

    def __init__(self):
        self.v, self.f, self.uv, self.mi, self.attr = [], [], [], [], {}

    def cara(self, verts, uvs, mi=0, **attrs):
        b = len(self.v)
        self.v += verts
        self.f.append(list(range(b, b + len(verts))))
        self.uv.append(uvs)
        self.mi.append(mi)
        for k, val in attrs.items():
            self.attr.setdefault(k, []).append(val)

    def prisma(self, pts, z0, z1, semilla, tapa_inferior=False):
        """Muros (UV: u a lo largo del perímetro, v = altura sobre la calle) y
        cubierta; `pts` en sentido antihorario."""
        n, acc = len(pts), 0.0
        v0, v1 = z0 + ALTURA_PISO, z1 + ALTURA_PISO
        for i in range(n):
            (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
            L = math.hypot(xb - xa, yb - ya)
            self.cara([(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)],
                      [(acc, v0), (acc + L, v0), (acc + L, v1), (acc, v1)], 0,
                      semilla=semilla)
            acc += L
        self.cara([(x, y, z1) for x, y in pts], list(pts), 1, semilla=semilla)
        if tapa_inferior:
            self.cara([(x, y, z0) for x, y in pts[::-1]], list(pts[::-1]), 1,
                      semilla=semilla)

    def objeto(self, nombre, mats):
        me = bpy.data.meshes.new(nombre)
        me.from_pydata(self.v, [], self.f)
        uvl = me.uv_layers.new(name="UVMap")
        for poly, uvc in zip(me.polygons, self.uv):
            for k, li in enumerate(range(poly.loop_start, poly.loop_start + poly.loop_total)):
                uvl.data[li].uv = uvc[k]
        me.polygons.foreach_set("material_index", self.mi)
        for k, vals in self.attr.items():
            at = me.attributes.new(k, "FLOAT", "FACE")
            at.data.foreach_set("value", vals)
        me.validate(clean_customdata=False)
        ob = bpy.data.objects.new(nombre, me)
        bpy.context.collection.objects.link(ob)
        for mt in mats:
            me.materials.append(mt)
        return ob


def _soldar(ob):
    """Une los vértices duplicados por las UV por cara: el booleano EXACT
    necesita volúmenes cerrados (las UV van por esquina y se conservan)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.005)
    bm.to_mesh(ob.data)
    bm.free()


def _vaciar_volumen_propio(ob, mats):
    """Resta al volumen del edificio propio el piso (huella + terraza, de la cota
    del suelo al remate de los muros) y los patios de luces a los que dan
    V03–V08, que OSM no recoge (se suponen de ~3,5 m)."""
    _soldar(ob)
    ter = next(e for e in PLAN["estancias"] if e["id"] == "terraza")
    tx = [p[0] for p in ter["pts"]]
    tz = [p[1] for p in ter["pts"]]
    # el corte sube 1 cm sobre el forjado (2,46): así su cara superior no queda
    # coplanaria con `techo` y los downlights no acaban dentro de un macizo
    z_corte = ALTURA + 0.01
    cortes = [([(x, -z) for x, z in PLAN["huella"]], -0.02, z_corte),
              ([(min(tx) - 0.05, -(min(tz) - 0.2)), (max(tx) + 0.3, -(min(tz) - 0.2)),
                (max(tx) + 0.3, -(max(tz) + 0.2)), (min(tx) - 0.05, -(max(tz) + 0.2))],
               -0.02, z_corte)]
    for x0, z0, x1, z1 in ((-7.0, 3.20, 0.25, 6.8),     # patio SO: V03–V07
                           (-8.6, -6.8, -5.0, -3.40)):  # patio NE: V08
        cortes.append(([(x0, -z0), (x1, -z0), (x1, -z1), (x0, -z1)],
                       -ALTURA_PISO + BAJO, PLANTA + 3.0))
    for k, (pts, z0, z1) in enumerate(cortes):
        pts = _limpiar(pts)
        area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] -
                   pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
        if area < 0:
            pts = pts[::-1]
        mc = _Malla()
        mc.prisma(pts, z0, z1, 0.0, tapa_inferior=True)
        cutter = mc.objeto(f"ext_corte_{k}", mats)
        _soldar(cutter)
        md = ob.modifiers.new(f"corte_{k}", "BOOLEAN")
        md.operation = "DIFFERENCE"
        md.object = cutter
        md.solver = "EXACT"
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=md.name)
        bpy.data.objects.remove(cutter, do_unlink=True)


def build_cubierta_propia(m, pts, fach, cub):
    """Coronación del edificio propio: peto perimetral con albardilla, casetas de
    escalera y ascensor, chimeneas y antenas (colocadas por fachada_propia).
    El peto es una malla aparte (`ext_propio_peto`, misma UV que los muros) para
    no romper el booleano del volumen, que necesita un sólido cerrado."""
    if not pts:
        return
    fp = _fachada_propia()
    t = 0.25                               # espesor del peto
    z0, z1 = fp.Z_CUB, fp.Z_CUB + fp.PETO
    n = len(pts)
    # normales hacia dentro (polígono antihorario) y vértices del contorno interior
    dirs = []
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
        L = math.hypot(xb - xa, yb - ya) or 1.0
        dirs.append(((xb - xa) / L, (yb - ya) / L, L))
    ints = []
    for i in range(n):
        d0, d1 = dirs[i - 1], dirs[i]
        n0, n1 = (-d0[1], d0[0]), (-d1[1], d1[0])
        k = 1.0 + n0[0] * n1[0] + n0[1] * n1[1]
        f = t / max(k, 0.35)
        ints.append((pts[i][0] + (n0[0] + n1[0]) * f, pts[i][1] + (n0[1] + n1[1]) * f))

    def en_patio(x, y):      # patios de luces que recorta _vaciar_volumen_propio
        return any(min(a, c) - 0.3 <= x <= max(a, c) + 0.3 and
                   min(b, d) - 0.3 <= y <= max(b, d) + 0.3
                   for a, b, c, d in ((-7.0, -6.8, 0.25, -3.2), (-8.6, 3.4, -5.0, 6.8)))

    mp = _Malla()
    acc = 0.0
    v0, v1 = z0 + ALTURA_PISO, z1 + ALTURA_PISO
    for i in range(n):
        j = (i + 1) % n
        (xa, ya), (xb, yb), L = pts[i], pts[j], dirs[i][2]
        if not en_patio((xa + xb) / 2, (ya + yb) / 2):
            (ia, ib) = ints[i], ints[j]
            mp.cara([(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)],
                    [(acc, v0), (acc + L, v0), (acc + L, v1), (acc, v1)], 0, semilla=0.0)
            mp.cara([(ib[0], ib[1], z0), (ia[0], ia[1], z0), (ia[0], ia[1], z1),
                     (ib[0], ib[1], z1)],
                    [(acc + L, v0), (acc, v0), (acc, v1), (acc + L, v1)], 0, semilla=0.0)
            mp.cara([(xa, ya, z1), (xb, yb, z1), (ib[0], ib[1], z1), (ia[0], ia[1], z1)],
                    [(acc, v1), (acc + L, v1), (acc + L, v1), (acc, v1)], 0, semilla=0.0)
        acc += L
    if mp.f:
        mp.objeto("ext_propio_peto", [fach, cub])

    # casetas, chimeneas y antenas de la azotea
    for nombre, rgb, rough in (("caseta_blanco", (0.84, 0.83, 0.80), 0.85),
                               ("albardilla", (0.82, 0.81, 0.78), 0.8),
                               ("antena", (0.35, 0.36, 0.38), 0.5)):
        if nombre not in m:
            m[nombre] = principled(nombre, base=rgb, rough=rough)
    az = fp.azotea(pts)
    cas = []
    for clave, (dx, dy, alto) in (("escalera", (3.3, 3.9, 2.7)), ("ascensor", (1.9, 1.9, 3.4))):
        if az[clave]:
            x, y = az[clave]
            cas.append((x - dx / 2, -(y + dy / 2), x + dx / 2, -(y - dy / 2), z0, z0 + alto))
    for x, y in az["chimeneas"]:
        cas.append((x - 0.225, -(y + 0.225), x + 0.225, -(y - 0.225), z0, z0 + 1.40))
        cas.append((x - 0.30, -(y + 0.30), x + 0.30, -(y - 0.30), z0 + 1.40, z0 + 1.46))
    if cas:
        cajas(cas, "ext_azotea", m["caseta_blanco"])
    ant = []
    for x, y in az["antenas"]:
        ant.append((x - 0.02, -(y + 0.02), x + 0.02, -(y - 0.02), z0, z0 + 3.2))
        ant.append((x - 0.6, -(y + 0.015), x + 0.6, -(y - 0.015), z0 + 2.8, z0 + 2.83))
        ant.append((x - 0.45, -(y + 0.015), x + 0.45, -(y - 0.015), z0 + 3.1, z0 + 3.13))
    if ant:
        cajas(ant, "ext_azotea_antena", m["antena"])


def _fachada_propia():
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import fachada_propia
    return fachada_propia


# balcón del piso (plano PE): x[8,23; 9,55] z[-0,62; 3,55]
BALCON_PISO = (8.23, 9.55, -0.62, 3.55)


def build_balcones(m, columnas):
    """Balcones volados apilados en columnas como en las fotos del edificio:
    canto de forjado grueso de revoco (~0,5 m), barandilla de pletinas de
    bronce, splits y toldos en algunas plantas y la cubierta del último balcón
    (voladizo). La columna del piso usa las cotas del plano; las demás salen de
    los entrantes de OSM. Cada columna son 3-6 mallas (no un objeto por pieza)."""
    rev, neg = m["revoco"], m["bronce_barandilla"]
    for nombre, col, rgb, rough in (
            ("split", None, (0.80, 0.80, 0.78), 0.45),
            ("toldo_a", None, (0.78, 0.70, 0.52), 0.9),
            ("toldo_b", None, (0.90, 0.87, 0.78), 0.9)):
        if nombre not in m:
            m[nombre] = principled(nombre, base=rgb, rough=rough)
    cols = []
    for c in columnas:
        if c["piso"]:
            cols.append(BALCON_PISO)
        else:
            cols.append((c["x"] - 0.17, c["x"] + 1.15, -c["y1"], -c["y0"]))
    if not cols:
        cols = [BALCON_PISO]
    voladizos = []
    for ci, (xi, xf, zi, zf) in enumerate(cols):
        losas, postes, rails, splits = [], [], [], []
        toldos_a, toldos_b = [], []
        xm = xf - 0.065                       # eje de la barandilla frontal
        zs_, zn_ = zf - 0.065, zi + 0.06      # ejes de las laterales
        n = max(2, math.ceil((zs_ - zn_) / 1.1))
        pos_post = [(xm, zn_ + (zs_ - zn_) * i / n) for i in range(n + 1)]
        pos_post += [(x, zc) for x in (xi + 0.2, (xi + xm) / 2) for zc in (zn_, zs_)]
        for k in range(7):
            h = -k * PLANTA
            losas.append((xi, zi, xf, zf, h - 0.50, h + (0.0 if k == 0 else 0.004)))
            for px, pz in pos_post:
                postes.append((px - 0.018, pz - 0.018, px + 0.018, pz + 0.018,
                               h, h + 1.02))
            for a, b, e in ((0.02, 0.04, 1.02), (0.007, 0.03, 0.30),
                            (0.007, 0.03, 0.50), (0.007, 0.03, 0.70),
                            (0.007, 0.03, 0.90)):
                rails.append((xm - a, zn_, xm + a, zs_, h + e, h + e + b))
                rails.append((xi, zs_ - a, xm + a, zs_ + a, h + e, h + e + b))
                rails.append((xi, zn_ - a, xm + a, zn_ + a, h + e, h + e + b))
            if k > 0 and (k * 3 + ci) % 4 == 1:          # split en la esquina
                splits.append((xf - 1.05, zn_ + 0.12, xf - 0.20, zn_ + 0.42,
                               h + 0.05, h + 0.60))
            if k > 0 and (k + ci) % 3 == 1:               # toldo a rayas
                ha, hb = h + 2.38, h + 1.88
                x0, x1, t = xi + 0.05, xf - 0.02, 0.015
                nb = max(4, int((zs_ - zn_) / 0.125))
                for j in range(nb):
                    za = zn_ + (zs_ - zn_) * j / nb
                    zb = zn_ + (zs_ - zn_) * (j + 1) / nb
                    dst = toldos_a if j % 2 == 0 else toldos_b
                    dst.append([(x0, za, ha - t), (x1, za, hb - t), (x1, zb, hb - t),
                                (x0, zb, ha - t), (x0, za, ha), (x1, za, hb),
                                (x1, zb, hb), (x0, zb, ha)])
                    dst.append([(x1 - t, za, hb - 0.22), (x1, za, hb - 0.22),
                                (x1, zb, hb - 0.22), (x1 - t, zb, hb - 0.22),
                                (x1 - t, za, hb), (x1, za, hb), (x1, zb, hb),
                                (x1 - t, zb, hb)])
        voladizos.append((xi, zi - 0.10, xf + 0.15, zf + 0.10, ALTURA + 0.05, PLANTA))
        cajas(losas, f"ext_balcon_c{ci}", rev)
        cajas(postes + rails, f"ext_barandilla_c{ci}", neg)
        if splits:
            cajas(splits, f"ext_balcon_split_c{ci}", m["split"])
        if toldos_a:
            prismas(toldos_a, f"ext_balcon_toldo_a_c{ci}", m["toldo_a"])
            prismas(toldos_b, f"ext_balcon_toldo_b_c{ci}", m["toldo_b"])
    # cubierta de los últimos balcones: una malla con el nombre que el visor
    # oculta en órbita (si no, tapa el piso desde arriba)
    cajas(voladizos, "ext_voladizo", rev)


def pintar_fachada_exterior(mat):
    """Las caras de muro que dan al exterior del piso (terraza, patios) llevan el
    revoco de fachada en vez de la pintura interior."""
    huella = PLAN["huella"]
    n = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.name.startswith(("muro_", "dintel_", "antepecho_")):
            continue
        me = ob.data
        idx = None
        for poly in me.polygons:
            nr = poly.normal
            if abs(nr.z) > 0.2:
                continue
            c = poly.center
            if _dentro((c.x + nr.x * 0.3, -(c.y + nr.y * 0.3)), huella):
                continue
            if idx is None:
                me.materials.append(mat)
                idx = len(me.materials) - 1
            poly.material_index = idx
            n += 1
    print(f"FACHADA caras exteriores con revoco: {n}")


def _arboles_alineacion(vias, edificios, existentes, radio=170.0):
    """Arbolado de alineación que falta en OSM (las fotos lo muestran en la
    calle principal): cada 8,5 m a 1,6 m del bordillo en calzadas anchas, sin
    invadir edificios, otras calzadas ni árboles existentes."""
    cajas = []
    for b in edificios:
        xs = [p[0] for p in b["pts"]]
        ys = [p[1] for p in b["pts"]]
        cajas.append((min(xs) - 3, max(xs) + 3, min(ys) - 3, max(ys) + 3, b["pts"]))
    calz = [(v["pts"], v["ancho"]) for v in vias if v["tipo"] == "calzada"]
    nuevos = []
    for pts, ancho in calz:
        if ancho < 7.0:
            continue
        off = ancho / 2 + 1.6
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            L = math.hypot(x1 - x0, y1 - y0)
            if L < 9:
                continue
            ux, uy = (x1 - x0) / L, (y1 - y0) / L
            t = 4.5
            while t < L - 4.5:
                for s in (-1, 1):
                    p = (x0 + ux * t - s * uy * off, y0 + uy * t + s * ux * off)
                    if math.hypot(*p) > radio:
                        continue
                    if any(math.dist(p, q) < 6.0 for q in existentes) or \
                            any(math.dist(p, q) < 6.0 for q in nuevos):
                        continue
                    choca = False
                    for x_0, x_1, y_0, y_1, poly in cajas:
                        if x_0 < p[0] < x_1 and y_0 < p[1] < y_1 and (
                                _dentro(p, poly) or min(_dist_seg(p, poly[j], poly[j - 1])
                                                        for j in range(len(poly))) < 2.5):
                            choca = True
                            break
                    if choca:
                        continue
                    if any(_dist_seg(p, q[j], q[j + 1]) < w / 2 + 0.8
                           for q, w in calz for j in range(len(q) - 1)):
                        continue
                    nuevos.append(p)
                t += 8.5
    return nuevos


def build_calle(m, arboles):
    """Vida de calle: pasos de cebra en los cruces, alcorques, coches aparcados
    en las bandas de aparcamiento, farolas y contenedores. Los coches y farolas
    son objetos reales (proyectan su sombra en el suelo horneado); el visor los
    redibuja instanciados a partir de las posiciones que exporta hornear_visor."""
    import random
    from collections import defaultdict
    rnd = random.Random(11)
    suelo = -ALTURA_PISO
    calz = [v for v in ENTORNO["vias"] if v["tipo"] == "calzada"]
    tramos_ = [(_limpiar(v["pts"]), v["ancho"]) for v in calz]
    clave = lambda p: (round(p[0], 1), round(p[1], 1))
    inc = defaultdict(list)             # nodo -> [(ancho, dirección saliente)]
    for pts, w in tramos_:
        for j in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[j], pts[j + 1]
            L = math.hypot(x1 - x0, y1 - y0) or 1.0
            inc[clave(pts[j])].append((w, ((x1 - x0) / L, (y1 - y0) / L), pts[j]))
            inc[clave(pts[j + 1])].append((w, ((x0 - x1) / L, (y0 - y1) / L), pts[j + 1]))
    # ── pasos de cebra (barras blancas de 0,5 × 3,5 m cada metro)
    blanco = principled("ext_marca", base=(0.60, 0.60, 0.57), rough=0.7)
    mm = _Malla()
    nz_ = 0
    for nodo, lista in inc.items():
        P = lista[0][2]
        if len(lista) < 3 or math.hypot(*P) > 240:
            continue
        for w, (dx, dy), _ in lista:
            if w < 5.0:
                continue
            otros = max(o[0] for o in lista if o[1] != (dx, dy)) if len(lista) > 1 else w
            s0 = otros / 2 + 1.2
            nx, ny = -dy, dx
            nb = int((w - 0.8) / 1.0)
            for j in range(nb):
                off = -w / 2 + 0.7 + j * 1.0
                a = (P[0] + dx * s0 + nx * (off - 0.25), P[1] + dy * s0 + ny * (off - 0.25))
                b = (a[0] + nx * 0.5, a[1] + ny * 0.5)
                c = (b[0] + dx * 3.5, b[1] + dy * 3.5)
                d = (a[0] + dx * 3.5, a[1] + dy * 3.5)
                mm.cara([(q[0], q[1], suelo + 0.045) for q in (a, b, c, d)],
                        [(0, 0)] * 4, 0)
                nz_ += 1
    if mm.f:
        mm.objeto("ext_marcas", [blanco])
    # ── alcorques bajo cada árbol
    mt = _Malla()
    tierra = principled("ext_alcorque", base=(0.10, 0.08, 0.06), rough=0.95)
    for x, y in arboles:
        if math.hypot(x, y) < 260:
            mt.cara([(x - 0.6, y - 0.6, suelo + 0.04), (x + 0.6, y - 0.6, suelo + 0.04),
                     (x + 0.6, y + 0.6, suelo + 0.04), (x - 0.6, y + 0.6, suelo + 0.04)],
                    [(0, 0)] * 4, 0)
    if mt.f:
        mt.objeto("ext_alcorques", [tierra])
    # ── coches, farolas y contenedores
    cajas_ed = []
    for b in ENTORNO["edificios"]:
        xs = [q[0] for q in b["pts"]]
        ys = [q[1] for q in b["pts"]]
        cajas_ed.append((min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1, b["pts"]))

    def en_edificio(p):
        return any(x0 < p[0] < x1 and y0 < p[1] < y1 and _dentro(p, poly)
                   for x0, x1, y0, y1, poly in cajas_ed)

    car = bpy.data.meshes.new("ext_coche_base")
    cv, cf = [], []
    for (x0, y0, x1, y1, h0, h1) in ((-2.15, -0.87, 2.15, 0.87, 0.28, 0.95),
                                     (-1.05, -0.78, 1.15, 0.78, 0.95, 1.45)):
        b = len(cv)
        cv += [(x0, y0, h0), (x1, y0, h0), (x1, y1, h0), (x0, y1, h0),
               (x0, y0, h1), (x1, y0, h1), (x1, y1, h1), (x0, y1, h1)]
        cf += [[b, b + 3, b + 2, b + 1], [b + 4, b + 5, b + 6, b + 7], [b, b + 1, b + 5, b + 4],
               [b + 1, b + 2, b + 6, b + 5], [b + 2, b + 3, b + 7, b + 6], [b + 3, b, b + 4, b + 7]]
    car.from_pydata(cv, [], cf)
    car.validate()
    pole = bpy.data.meshes.new("ext_farola_base")
    pv, pf = [], []
    for (x0, y0, x1, y1, h0, h1) in ((-0.08, -0.08, 0.08, 0.08, 0.0, 9.0),
                                     (-0.03, -0.03, 1.8, 0.03, 8.9, 9.05)):
        b = len(pv)
        pv += [(x0, y0, h0), (x1, y0, h0), (x1, y1, h0), (x0, y1, h0),
               (x0, y0, h1), (x1, y0, h1), (x1, y1, h1), (x0, y1, h1)]
        pf += [[b, b + 3, b + 2, b + 1], [b + 4, b + 5, b + 6, b + 7], [b, b + 1, b + 5, b + 4],
               [b + 1, b + 2, b + 6, b + 5], [b + 2, b + 3, b + 7, b + 6], [b + 3, b, b + 4, b + 7]]
    pole.from_pydata(pv, [], pf)
    pole.validate()
    coches = farolas = urbano = 0
    for pts, w in tramos_:
        n_, k_ = _desglose_via(w)
        for j in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[j], pts[j + 1]
            L = math.hypot(x1 - x0, y1 - y0)
            if L < 6:
                continue
            ux, uy = (x1 - x0) / L, (y1 - y0) / L
            nx, ny = -uy, ux
            t0 = 9.0 if len(inc[clave(pts[j])]) >= 3 else 1.5
            t1 = 9.0 if len(inc[clave(pts[j + 1])]) >= 3 else 1.5
            for lado, activo in ((-1, k_ >= 1), (1, k_ >= 2)):
                if not activo:
                    continue
                off = lado * (w / 2 - 1.1)
                t = t0 + 2.3
                while t < L - t1 - 2.3:
                    p = (x0 + ux * t + nx * off, y0 + uy * t + ny * off)
                    if math.hypot(*p) < 230 and rnd.random() < 0.78:
                        ob = bpy.data.objects.new(f"ext_coche_i{coches:04d}", car)
                        ob.location = (p[0], p[1], suelo + 0.03)
                        ob.rotation_euler = (0, 0, math.atan2(uy, ux)
                                             + (0.0 if lado < 0 else math.pi)
                                             + rnd.uniform(-0.03, 0.03))
                        ob["color"] = rnd.random()
                        bpy.context.collection.objects.link(ob)
                        coches += 1
                    t += 5.0 + rnd.uniform(-0.2, 0.6)
            if w >= 8.4:
                t = 5.0 + (j % 2) * 14.0
                lado = -1 if (j % 2 == 0) else 1
                while t < L - 5.0:
                    off = lado * (w / 2 + 0.6)
                    p = (x0 + ux * t + nx * off, y0 + uy * t + ny * off)
                    if math.hypot(*p) < 230 and not en_edificio(p):
                        ob = bpy.data.objects.new(f"ext_farola_i{farolas:04d}", pole)
                        ob.location = (p[0], p[1], suelo)
                        ob.rotation_euler = (0, 0, math.atan2(-lado * ny, -lado * nx))
                        bpy.context.collection.objects.link(ob)
                        farolas += 1
                    t += 28.0
                    lado = -lado
            if w >= 5.3:
                t = 20.0 + rnd.uniform(0, 30)
                while t < L - 10.0:
                    off = -(w / 2 + 0.8)
                    p = (x0 + ux * t + nx * off, y0 + uy * t + ny * off)
                    if math.hypot(*p) < 200 and not en_edificio(p):
                        for q in range(rnd.randint(3, 4)):
                            e = bpy.data.objects.new(f"ext_urbano_i{urbano:04d}", None)
                            e.location = (p[0] + ux * 1.25 * q, p[1] + uy * 1.25 * q, suelo)
                            e.rotation_euler = (0, 0, math.atan2(uy, ux))
                            e["tipo"] = rnd.choice((0, 0, 1, 2, 3))
                            bpy.context.collection.objects.link(e)
                            urbano += 1
                    t += 60.0
    print(f"CALLE cebras {nz_} barras, {coches} coches, {farolas} farolas, {urbano} contenedores")


def build_arboles(m, puntos):
    """Jacarandas CC0 (Poly Haven `jacaranda_tree`, glTF 1k en data/assets/, no
    versionado por tamaño) instanciadas en cada árbol; si falta el modelo, copa
    procedural."""
    import random
    src = ASSETS_DIR / "jacaranda_tree" / "jacaranda_tree_1k.gltf"
    col, alto, ancho, z0 = None, 1.0, 1.0, 0.0
    if src.is_file() and (src.parent / "jacaranda_tree.bin").is_file():
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(src))
        nuevos = [o for o in bpy.data.objects if o not in antes]
        col = bpy.data.collections.new("ext_arbol")
        for o in nuevos:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
            o.name = "ext_arbol_" + o.name
        ws = [o.matrix_world @ Vector(c) for o in nuevos if o.type == "MESH"
              for c in o.bound_box]
        z0 = min(w.z for w in ws)
        alto = max(w.z for w in ws) - z0
        ancho = max(max(w.x for w in ws) - min(w.x for w in ws),
                    max(w.y for w in ws) - min(w.y for w in ws))
    rnd = random.Random(7)
    suelo = -ALTURA_PISO
    for k, (x, y) in enumerate(puntos):
        h = rnd.uniform(7.5, 10.5)
        if col:
            e = bpy.data.objects.new(f"ext_arbol_i{k:04d}", None)
            e.instance_type = "COLLECTION"
            e.instance_collection = col
            s = h / alto
            sxy = min(s, rnd.uniform(6.5, 9.0) / ancho)
            e.scale = (sxy, sxy, s)
            e.rotation_euler = (0.0, 0.0, rnd.uniform(0, 2 * math.pi))
            e.location = (x, y, suelo - z0 * s)
            bpy.context.collection.objects.link(e)
        else:
            cylinder(x, -y, 0.14, suelo, suelo + h * 0.5, f"ext_tronco_{k}", m["cuero"], n=8)
            sphere(x, -y, suelo + h * 0.68, h * 0.33, f"ext_copa_{k}", m["planta"], sy=0.8)
    print(f"ARBOLES {len(puntos)} ({'jacaranda CC0' if col else 'procedurales'})")


def build_entorno(m):
    """Ciudad real alrededor del piso desde data/entorno.json (OSM): volúmenes
    con su número de plantas, el propio edificio vaciado donde está el piso,
    calzadas con marcas, carril bici, zonas verdes, acera y arbolado."""
    fach, cub = mat_fachadas()
    if "revoco" not in m:
        m["revoco"] = principled("revoco_fachada", base=PALETA_FACHADAS[0], rough=0.88)
        noise_bump(m["revoco"], scale=60, strength=0.12)
    suelo = -ALTURA_PISO
    import random
    rnd = random.Random(3)

    fp = _fachada_propia()
    ip = fp.principal(ENTORNO["edificios"])
    ciudad = _Malla()
    propios = []
    pts_propio, cols_propio = None, []
    for i, b in enumerate(ENTORNO["edificios"]):
        pts = _limpiar(b["pts"])
        if len(pts) < 3:
            continue
        if i == ip:
            # PB + 7 plantas: el piso es la última (OSM da 9 plantas). Cubierta
            # a la cota real; el peto se añade aparte (build_cubierta_propia)
            mp = _Malla()
            mp.prisma(pts, suelo, fp.Z_CUB, 0.0, tapa_inferior=True)
            propios.append(mp)
            pts_propio, cols_propio = pts, fp.columnas(b["pts"])
            continue
        p = b["plantas"] or 3
        h = BAJO + (p - 1) * PLANTA + 1.0 if p >= 3 else p * 3.4
        semilla = 0.15 + 0.85 * rnd.random()
        ciudad.prisma(pts, suelo, suelo + h, semilla)
    ciudad.objeto("ext_edificios", [fach, cub])
    for k, mp in enumerate(propios):
        ob = mp.objeto(f"ext_propio_{k}", [fach, cub])
        _vaciar_volumen_propio(ob, [fach, cub])

    # calles
    asf = mat_asfalto()
    bici = mat_plano("ext_bici", (0.20, 0.045, 0.035), (0.26, 0.06, 0.045), 2.0, 0.8)
    for tipo, mat, dz in (("calzada", asf, 0.03), ("bici", bici, 0.035)):
        mv = _Malla()
        for i, v in enumerate(ENTORNO["vias"]):
            if v["tipo"] != tipo:
                continue
            pts, w = _limpiar(v["pts"]), v["ancho"]
            _, k_ap = _desglose_via(w) if tipo == "calzada" else (1, 0)
            p_d, p_i = (2.2 if k_ap >= 1 else 0.0), (2.2 if k_ap >= 2 else 0.0)
            z = suelo + dz + (i % 50) * 0.0002
            acc = 0.0
            for j in range(len(pts) - 1):
                (x0, y0), (x1, y1) = pts[j], pts[j + 1]
                L = math.hypot(x1 - x0, y1 - y0)
                nx, ny = -(y1 - y0) / L * w / 2, (x1 - x0) / L * w / 2
                mv.cara([(x0 + nx, y0 + ny, z), (x0 - nx, y0 - ny, z),
                         (x1 - nx, y1 - ny, z), (x1 + nx, y1 + ny, z)],
                        [(acc, w), (acc, 0.0), (acc + L, 0.0), (acc + L, w)], 0, ancho=w,
                        p_der=p_d, p_izq=p_i)
                acc += L
            for x, y in pts[1:-1]:
                r = w / 2
                mv.cara([(x + r * math.cos(a * math.pi / 4), y + r * math.sin(a * math.pi / 4),
                          z - 0.001) for a in range(8)], [(-50.0, 1.5)] * 8, 0, ancho=w,
                        p_der=0.0, p_izq=0.0)
        if mv.f:
            mv.objeto(f"ext_{tipo}", [mat])

    # zonas verdes y acera
    cesped = mat_plano("ext_cesped", (0.045, 0.09, 0.022), (0.085, 0.13, 0.035), 3.0, 0.95)
    tierra = mat_plano("ext_tierra", (0.30, 0.24, 0.16), (0.36, 0.30, 0.21), 1.5, 0.95)
    mg = _Malla()
    for g in ENTORNO["verdes"]:
        pts = _limpiar(g["pts"])
        if len(pts) < 3:
            continue
        z = suelo + (0.012 if g["tipo"] == "parque" else 0.02)
        if sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts))) < 0:
            pts = pts[::-1]        # antihorario: la cara hacia abajo se hornea negra
        mg.cara([(x, y, z) for x, y in pts], list(pts), 0 if g["tipo"] == "cesped" else 1)
    if mg.f:
        mg.objeto("ext_verdes", [cesped, tierra])
    ma = _Malla()
    r = 1500.0
    ma.cara([(-r, -r, suelo), (r, -r, suelo), (r, r, suelo), (-r, r, suelo)],
            [(-r, -r), (r, -r), (r, r), (-r, r)])
    ma.objeto("ext_suelo", [mat_suelo_urbano()])

    arboles = [tuple(p) for p in ENTORNO["arboles"]]
    arboles += _arboles_alineacion(ENTORNO["vias"], ENTORNO["edificios"], arboles)
    build_arboles(m, arboles)
    build_calle(m, arboles)
    build_balcones(m, cols_propio)
    build_cubierta_propia(m, pts_propio, fach, cub)
    pintar_fachada_exterior(m["revoco"])


def build_exterior(m):
    box(-150.0, -150.0, 150.0, 150.0, -16.0, -15.0, "ext_suelo", m["ext_suelo"],
        bevel=0.0)
    # patio interior al sur (para la vidriera del salón)
    box(-9.0, 3.9, 9.0, 14.0, -3.8, -3.5, "ext_patio", m["ext_suelo"], bevel=0.0)
    # edificios de enfrente: solo sin HDRI (con HDRI el contexto urbano es real)
    if hdri_path() is None:
        bloques = [(-40, 26, -12, 54, 14), (16, 30, 40, 56, 16), (-44, 56, -14, 90, 12),
                   (14, -42, 44, -22, 18), (48, -8, 76, 24, 16)]
        for k, (x0, z0, x1, z1, h) in enumerate(bloques):
            box(x0, z0, x1, z1, -15.0, -15.0 + h, f"ext_b_{k}", m["ext_edificio"],
                bevel=0.0)


def build_luces(m):
    scene = bpy.context.scene
    # con el entorno real el HDRI (tomado a pie de calle en otra ciudad) sobra:
    # cielo físico Nishita con el sol en su posición real
    hdri = None if ENTORNO else hdri_path()
    sol_az, sol_el = posicion_sol(SOL_UTC, *CIUDAD_LAT_LON)
    sol_ang = rumbo_a_blender(sol_az)          # en el plano XY de Blender
    if ENTORNO:
        print(f"SOL azimut {sol_az:.1f}° elevación {sol_el:.1f}° "
              f"(fachada {ENTORNO['rumbo_fachada']}°)")

    # cielo: HDRI real de Poly Haven (CC0) si existe; si no, Nishita de respaldo
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes.get("Background")
    if hdri:
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(str(hdri))
        tco = nt.nodes.new("ShaderNodeTexCoord")
        mapn = nt.nodes.new("ShaderNodeMapping")
        sol_az_img, sol_el = HDRI_SOL[hdri.name]
        mapn.inputs["Rotation"].default_value = (
            0.0, 0.0, math.radians(sol_az_img - SOL_AZ))
        nt.links.new(tco.outputs["Generated"], mapn.inputs["Vector"])
        nt.links.new(mapn.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = 2.5
    else:
        sky = nt.nodes.new("ShaderNodeTexSky")
        sky.sky_type = "NISHITA"
        if ENTORNO:
            # sun_rotation 0 = sol hacia +Y y crece en sentido horario (medido)
            sky.sun_elevation = math.radians(sol_el)
            sky.sun_rotation = math.radians(90.0 - sol_ang)
            sky.sun_disc = False          # el disco lo pone la lámpara SUN
            sky.altitude = ALTURA_PISO + 20
            sky.dust_density = 1.6        # calima ligera de ciudad costera
        else:
            sky.sun_elevation = math.radians(45)
            sky.sun_rotation = math.radians(200)
            sky.sun_intensity = 0.0
            sky.altitude = 30
        nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = CIELO_FUERZA if ENTORNO else 0.28

    # sol direccional alineado con el HDRI (sombras nítidas; el disco del HDRI
    # solo aporta luz ambiental y brillo en los reflejos)
    sd = bpy.data.lights.new("sol", "SUN")
    sd.energy = SOL_FUERZA if ENTORNO else (8.0 if hdri else 14.0)
    sd.angle = math.radians(3.5)
    sd.color = (1.0, 0.90, 0.78)
    so = bpy.data.objects.new("sol", sd)
    bpy.context.collection.objects.link(so)
    if hdri:
        _, el = HDRI_SOL[hdri.name]
        p = Vector((math.cos(math.radians(el)) * math.cos(math.radians(SOL_AZ)),
                    math.cos(math.radians(el)) * math.sin(math.radians(SOL_AZ)),
                    math.sin(math.radians(el))))
        d = -p
    elif ENTORNO:
        ce = math.cos(math.radians(sol_el))
        d = -Vector((ce * math.cos(math.radians(sol_ang)),
                     ce * math.sin(math.radians(sol_ang)),
                     math.sin(math.radians(sol_el))))
    else:
        d = Vector((-0.80, 0.33, -0.60)).normalized()
    so.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    # light portals reales en cada hueco de ventana: guían el muestreo del
    # cielo/HDRI y sustituyen los viejos AREA falsos
    mx = sum(p[0] for p in PLAN["huella"]) / len(PLAN["huella"])
    mz = sum(p[1] for p in PLAN["huella"]) / len(PLAN["huella"])
    for v in VENT["ventanas"]:
        h = v["hueco_plano"]
        cx, cz = h["centro"]
        ancho, alto = v["ancho_m"], v["alto_m"]
        ante = 0.0 if v["id"] in ("V01", "V05") else (v["antepecho_m"] or 0.0)
        head = min(ante + alto, ALTURA)
        if h["fachada"] in ("este", "oeste"):
            sx = 1.0 if mx > cx else -1.0
            verts = [(cx, -(cz - ancho / 2), ante), (cx, -(cz + ancho / 2), ante),
                     (cx, -(cz + ancho / 2), head), (cx, -(cz - ancho / 2), head)]
            inward = Vector((sx, 0.0, 0.0))
        else:
            sz = 1.0 if mz > cz else -1.0
            verts = [(cx - ancho / 2, -cz, ante), (cx + ancho / 2, -cz, ante),
                     (cx + ancho / 2, -cz, head), (cx - ancho / 2, -cz, head)]
            inward = Vector((0.0, -sz, 0.0))
        ob = mesh_from(verts, [[0, 1, 2, 3]], f"portal_{v['id']}", None)
        if ob.data.polygons[0].normal.dot(inward) < 0:
            ob.data.flip_normals()
        ob.cycles.is_portal = True
        # un portal solo guía el muestreo: no se ve ni bloquea la luz
        for vis in ("visible_camera", "visible_diffuse", "visible_glossy",
                    "visible_transmission", "visible_volume_scatter",
                    "visible_shadow"):
            setattr(ob, vis, False)

        # relleno suave de día en el propio hueco (flujo de cielo/sol que entra)
        area = ancho * (head - ante)
        if area < 0.4:
            continue
        fl = bpy.data.lights.new(f"dia_{v['id']}", "AREA")
        fl.shape = "RECTANGLE"
        fl.size = ancho * 0.9
        fl.size_y = (head - ante) * 0.9
        fl.energy = (4.5 if ENTORNO else 9.0) * area
        fl.color = (1.0, 0.95, 0.88)
        fo = bpy.data.objects.new(f"dia_{v['id']}", fl)
        bpy.context.collection.objects.link(fo)
        cen = Vector((cx, -(cz), (ante + head) / 2))
        if h["fachada"] in ("este", "oeste"):
            cen.x += inward.x * 0.20
        else:
            cen.y += inward.y * 0.20
        fo.location = cen
        fo.rotation_euler = (-inward).to_track_quat("Z", "Y").to_euler()

    # downlights: spot con cono de 70° (baña paredes y suelo) más el
    # disco emisivo visible
    dls = [
        (1.0, 0.8), (3.8, 0.8), (6.4, 0.8), (1.0, 2.7), (3.8, 2.7), (6.4, 2.7),
        (-1.0, 0.4), (-1.0, 1.6), (0.4, 0.6),
        (3.2, -2.3), (5.2, -2.3), (7.0, -2.3), (5.2, -1.0),
        (-6.3, -2.5), (-5.2, -2.5), (-5.2, -1.2),
        (-6.5, 0.5), (-5.0, 0.5), (-6.5, 2.2), (-5.0, 2.2),
        (-3.1, 0.4), (-2.1, 0.4), (-2.6, 1.9),
        (-3.4, -2.9), (-2.1, -2.9), (-2.1, -1.9),
        (-0.4, -2.9), (1.2, -2.9), (1.2, -1.9),
        (-3.4, -1.0), (-1.2, -1.0), (1.0, -1.0),
        (0.4, 2.9), (0.9, 3.7),
    ]
    DL_W = 22.0
    for k, (x, z) in enumerate(dls):
        hc = _techo_en(x, z)          # 2,30 bajo falso techo, 2,46 bajo forjado
        ld = bpy.data.lights.new(f"dl_{k}", "SPOT")
        ld.energy = DL_W
        ld.color = (1.0, 0.84, 0.66)
        ld.spot_size = math.radians(70)
        ld.spot_blend = 0.5
        ld.shadow_soft_size = 0.025
        lo = bpy.data.objects.new(f"dl_{k}", ld)
        bpy.context.collection.objects.link(lo)
        lo.location = (x, -z, hc - 0.03)
        disco = cylinder(x, z, 0.05, hc - 0.012, hc - 0.002, f"dl_disco_{k}",
                         m["led"], n=16)
        if disco is not None:
            disco.visible_shadow = False   # solo aspecto: no tapa la luz del spot

    # lámpara de pie (pantalla)
    lp = bpy.data.lights.new("lampara_pt", "POINT")
    lp.energy = 8.0
    lp.color = (1.0, 0.82, 0.62)
    lp.shadow_soft_size = 0.12
    lo = bpy.data.objects.new("lampara_pt", lp)
    bpy.context.collection.objects.link(lo)
    lo.location = (6.55, -2.65, 1.52)


def build_cameras():
    scene = bpy.context.scene
    cams = []
    for name, x, z, yaw, _label in PANOS:
        cd = bpy.data.cameras.new(name)
        cd.type = "PANO"
        cd.panorama_type = "EQUIRECTANGULAR"
        cd.clip_end = 3000
        co = bpy.data.objects.new(name, cd)
        bpy.context.collection.objects.link(co)
        co.location = (x, -z, 1.55)
        a = math.radians(yaw)
        d = Vector((math.cos(a), -math.sin(a), 0.0))
        co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        cams.append(co)
    for st in STILLS:
        cd = bpy.data.cameras.new(st["id"])
        cd.lens = st["lens"]
        cd.clip_end = 3000
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = 5.6
        co = bpy.data.objects.new(st["id"], cd)
        bpy.context.collection.objects.link(co)
        co.location = (st["x"], -st["z"], st["h"])
        d = Vector((st["tx"] - st["x"], -(st["tz"] - st["z"]),
                    st["th"] - st["h"])).normalized()
        cd.dof.focus_distance = math.dist((st["x"], -st["z"], st["h"]),
                                          (st["tx"], -st["tz"], st["th"]))
        co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        cams.append(co)
    scene.camera = cams[0]


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    if hasattr(scene.cycles, "denoising_input_passes"):
        scene.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    if hasattr(scene.cycles, "denoising_prefilter"):
        scene.cycles.denoising_prefilter = "ACCURATE"
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 8
    scene.cycles.transparent_max_bounces = 8
    if hasattr(scene.cycles, "use_light_tree"):
        scene.cycles.use_light_tree = True
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.cycles.blur_glossy = 1.0
    scene.cycles.sample_clamp_indirect = 10.0
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 1.2 if ENTORNO else 1.4
    scene.view_settings.look = "AgX - Base Contrast"
    scene.render.use_persistent_data = True
    scene.render.threads_mode = "AUTO"


def build_compositor():
    """Viñeta ligera + glare suave desactivado (el Fog Glow sobre ventanas
    grandes deja halos; queda disponible para activarlo a mano). El
    `render_blender.py` desactiva la viñeta en los panoramas."""
    scene = bpy.context.scene
    scene.use_nodes = True
    nt = scene.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    glare.threshold = 3.0
    glare.size = 4
    glare.mix = -0.9
    glare.mute = True
    glare.name = "glare_soft"
    nt.links.new(rl.outputs["Image"], glare.inputs["Image"])

    ell = nt.nodes.new("CompositorNodeEllipseMask")
    ell.x = 0.5
    ell.y = 0.5
    ell.mask_width = 1.25          # relativo al ancho: elipse con el aspecto
    ell.mask_height = 0.95         # del encuadre 16:9, algo mayor que él
    blur = nt.nodes.new("CompositorNodeBlur")
    blur.filter_type = "FAST_GAUSS"
    blur.use_relative = True
    blur.factor_x = 30.0           # en % del tamaño (0,22 % dejaba borde duro)
    blur.factor_y = 30.0
    nt.links.new(ell.outputs["Mask"], blur.inputs["Image"])

    mix = nt.nodes.new("CompositorNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.35
    nt.links.new(glare.outputs["Image"], mix.inputs[1])
    nt.links.new(blur.outputs["Image"], mix.inputs[2])
    mix.name = "vineta"
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(mix.outputs["Image"], comp.inputs["Image"])
    return nt


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    m = build_materials()
    setup_render()
    build_compositor()
    walls = build_shell(m)
    build_revestimientos(m)
    build_bandas(m, walls)
    build_rodapies(m)
    build_ventanas(m)
    build_puertas(m)
    build_mobiliario(m)
    suavizar_tapizados()
    if ENTORNO:
        build_entorno(m)
    else:
        build_exterior(m)
    uv_proyectar()
    vidrios_sin_sombra()
    build_luces(m)
    build_cameras()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
    nb = len([o for o in bpy.data.objects if o.type == "MESH"])
    print(f"OK escena: {nb} mallas, {len(PANOS)} panos, {len(STILLS)} stills -> {OUT}")


if __name__ == "__main__":
    main()
