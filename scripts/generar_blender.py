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
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
PLAN = json.loads((ROOT / "data" / "planos3d.json").read_text(encoding="utf-8"))
VENT = json.loads((ROOT / "data" / "ventanas.json").read_text(encoding="utf-8"))
CAMARAS = json.loads((ROOT / "data" / "camaras.json").read_text(encoding="utf-8"))
OUT = ROOT / "renders" / "escena.blend"

ALTURA = 2.60
TECHO = 2.50

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


def tile_material(name, tile=(0.86, 0.85, 0.82), grout=(0.62, 0.61, 0.58)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 1.2, 1 / 0.6, 1.0)
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Mortar Size"].default_value = 0.012
    brick.inputs["Color1"].default_value = (*tile, 1)
    brick.inputs["Color2"].default_value = (0.82, 0.81, 0.78, 1)
    brick.inputs["Mortar"].default_value = (*grout, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], brick.inputs["Vector"])
    nt.links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
    set_in(bsdf, "Roughness", 0.28)
    noise_bump(mat, scale=200, strength=0.02)
    return mat


def build_materials():
    m = {}
    m["muro"] = principled("muro", base=(0.90, 0.885, 0.855), rough=0.92)
    m["techo"] = principled("techo", base=(0.93, 0.92, 0.90), rough=0.95)
    m["suelo_madera"] = wood_material("suelo_madera", (0.40, 0.26, 0.155),
                                      (0.47, 0.32, 0.20), (0.37, 0.24, 0.14),
                                      (0.09, 5.0, 1.0), rough=0.34)
    m["terraza"] = wood_material("terraza_madera", (0.30, 0.20, 0.12),
                                 (0.38, 0.26, 0.16), (0.26, 0.17, 0.10),
                                 (0.5, 2.0, 1.0), rough=0.6)
    m["marmol"] = stone_material("marmol", (0.80, 0.78, 0.74), (0.62, 0.61, 0.59),
                                 scale=1.4, rough=0.15)
    m["azulejo"] = tile_material("azulejo")
    m["travertino"] = stone_material("travertino", (0.72, 0.64, 0.51),
                                     (0.58, 0.50, 0.38), scale=2.2, rough=0.6)
    m["roble"] = wood_material("roble", (0.38, 0.24, 0.135), (0.46, 0.30, 0.175),
                               (0.35, 0.22, 0.12), (0.18, 4.0, 1.0), rough=0.42)
    m["piedra_negra"] = principled("piedra_negra", base=(0.045, 0.042, 0.040),
                                   rough=0.18, spec=0.7)
    m["cobre"] = principled("cobre", base=(0.72, 0.43, 0.20), rough=0.28, metal=1.0)
    m["aluminio"] = principled("aluminio", base=(0.12, 0.115, 0.11), rough=0.35,
                               metal=1.0, spec=0.6)
    m["cristal"] = principled("cristal", base=(1, 1, 1), rough=0.015, trans=1.0)
    m["espejo"] = principled("espejo", base=(0.95, 0.95, 0.95), rough=0.02, metal=1.0)
    mat = principled("concreto", base=(0.62, 0.60, 0.57), rough=0.7)
    noise_bump(mat, scale=25, strength=0.25)
    m["concreto"] = mat
    m["tejido"] = principled("tejido", base=(0.80, 0.76, 0.68), rough=0.95)
    noise_bump(m["tejido"], scale=300, strength=0.15)
    m["tejido_claro"] = principled("tejido_claro", base=(0.87, 0.84, 0.78), rough=0.95)
    noise_bump(m["tejido_claro"], scale=300, strength=0.15)
    m["lino"] = principled("lino", base=(0.86, 0.83, 0.76), rough=0.95)
    m["negro_mate"] = principled("negro_mate", base=(0.02, 0.02, 0.02), rough=0.6)
    m["pantalla"] = principled("pantalla", base=(0.012, 0.012, 0.014), rough=0.08,
                               spec=0.8)
    m["planta"] = principled("planta", base=(0.07, 0.16, 0.055), rough=0.7)
    m["maceta"] = principled("maceta", base=(0.85, 0.84, 0.80), rough=0.7)
    m["led"] = principled("led", base=(1.0, 0.93, 0.82), rough=0.5,
                          emission=(1.0, 0.86, 0.66), emit_str=16.0)
    m["ext_suelo"] = principled("ext_suelo", base=(0.45, 0.44, 0.42), rough=0.9)
    m["ext_edificio"] = principled("ext_edificio", base=(0.30, 0.28, 0.26), rough=0.95)
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


def build_shell(m):
    poly_ngon(PLAN["huella"], 0.0, "suelo", m["suelo_madera"])
    for e in PLAN["estancias"]:
        if e["id"] in ("bano-1", "bano-2"):
            poly_ngon(e["pts"], 0.006, f"pav_{e['id']}", m["azulejo"])
        elif e["id"] == "recibidor":
            poly_ngon(e["pts"], 0.006, "pav_recibidor", m["marmol"])
        elif e["id"] == "terraza":
            poly_ngon(e["pts"], 0.004, "pav_terraza", m["terraza"])
    poly_ngon(PLAN["huella"], TECHO, "techo", m["techo"])

    walls = []
    for i, w in enumerate(PLAN["muros"]):
        if w["tipo"] == "vidrio":
            continue
        walls.append(poly_prism(w["pts"], 0.0, ALTURA, f"muro_{i:03d}", m["muro"]))
    return walls


def build_bandas(m, walls):
    """Ventanas de fachada de banda (norte): abrir hueco y montar carpintería."""
    bandas = [
        (3.50, 8.23, -3.21, 1.00, 2.30),   # dormitorio principal (norte)
        (-6.24, -4.00, -3.21, 1.00, 2.30), # dormitorio 1 (norte)
        (2.40, 8.20, 3.64, 0.05, 2.40),    # salón-comedor (sur)
        (-7.20, -6.30, 2.95, 0.05, 2.20),  # dormitorio 2 (sur)
        (-3.45, -2.55, 2.95, 0.05, 2.20),  # dormitorio 3 (sur)
    ]
    for k, (x0, x1, z, ante, head) in enumerate(bandas):
        for ob in walls:
            a, b, c, d = bbox(ob)
            if a < x1 + 0.2 and b > x0 - 0.2 and c < -z + 0.3 and d > -z - 0.3:
                cort = box(x0 - 0.02, z - 0.25, x1 + 0.02, z + 0.25, ante, head,
                           f"cort_{k}", None, bevel=0.0)
                cut(ob, cort)
        box(x0, z - 0.02, x0 + 0.06, z + 0.02, ante, head, f"banda_marco_i_{k}",
            m["aluminio"], bevel=0.0)
        box(x1 - 0.06, z - 0.02, x1, z + 0.02, ante, head, f"banda_marco_d_{k}",
            m["aluminio"], bevel=0.0)
        box(x0, z - 0.02, x1, z + 0.02, head - 0.06, head, f"banda_marco_s_{k}",
            m["aluminio"], bevel=0.0)
        box(x0, z - 0.02, x1, z + 0.02, ante, ante + 0.06, f"banda_marco_b_{k}",
            m["aluminio"], bevel=0.0)
        box(x0 + 0.05, z - 0.006, x1 - 0.05, z + 0.006, ante + 0.05, head - 0.05,
            f"banda_vidrio_{k}", m["cristal"], bevel=0.0)
        n = max(2, int(round((x1 - x0) / 1.15)))
        for i in range(1, n):
            xk = x0 + (x1 - x0) * i / n
            box(xk - 0.025, z - 0.02, xk + 0.025, z + 0.02, ante, head,
                f"banda_mont_{k}_{i}", m["aluminio"], bevel=0.0)
        box(x0 - 0.06, z - 0.13, x1 + 0.06, z + 0.13, head, ALTURA,
            f"banda_dintel_{k}", m["muro"], bevel=0.0)
        box(x0 - 0.06, z - 0.13, x1 + 0.06, z + 0.13, 0.0, ante,
            f"banda_antepecho_{k}", m["muro"], bevel=0.0)


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
        if vert:
            x = cx
            marco("v", cx, cz, ancho, ante, head, f"marco_{v['id']}", m["aluminio"])
            box(x - 0.006, cz - ancho / 2 + t, x + 0.006, cz + ancho / 2 - t,
                ante + t, head - t, f"vidrio_{v['id']}", m["cristal"], bevel=0.0)
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
                ante + t, head - t, f"vidrio_{v['id']}", m["cristal"], bevel=0.0)
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
    """Puertas interiores aproximadas (según arcos del plano)."""
    puertas = [
        (-4.35, -0.47, "h", 0.9, 0),    # dorm-1 (desde pasillo)
        (-1.80, -1.50, "h", 0.8, 0),    # baño 1
        (0.45, -1.50, "h", 0.8, 0),     # baño 2
        (3.35, -0.47, "h", 0.9, 0),     # dormitorio principal
        (-3.05, -0.47, "h", 0.85, 0),   # dorm-3
        (-2.05, -0.47, "h", 0.85, 0),   # dorm-2
        (0.65, 4.10, "h", 1.0, 0),      # entrada
    ]
    for k, (cx, cz, ori, ancho, hueco) in enumerate(puertas):
        x0, x1 = cx - ancho / 2, cx + ancho / 2
        box(x0 - 0.03, cz - 0.10, x0 + 0.03, cz + 0.10, 0, 2.15, f"pmarco_i_{k}",
            m["roble"], bevel=0.0)
        box(x1 - 0.03, cz - 0.10, x1 + 0.03, cz + 0.10, 0, 2.15, f"pmarco_d_{k}",
            m["roble"], bevel=0.0)
        box(x0 - 0.03, cz - 0.10, x1 + 0.03, cz + 0.10, 2.15, 2.30, f"pdintel_{k}",
            m["roble"], bevel=0.0)
        L = ancho - 0.07
        lx = x0 + 0.03 + (L / 2) * math.cos(math.radians(78))
        lz = cz + 0.02 - (L / 2) * math.sin(math.radians(78))
        rot_box(lx, lz, L, 0.045, -78, 0.02, 2.08, f"phoja_{k}", m["roble"],
                bevel=0.004)


def build_mobiliario(m):
    oak = m["roble"]
    fab, fab2, lino = m["tejido"], m["tejido_claro"], m["lino"]
    negro, piedra, tra = m["piedra_negra"], m["travertino"], m["travertino"]

    # SALÓN
    box(4.05, -0.45, 6.95, -0.40, 0.02, 2.45, "tv_panel", tra, bevel=0.0)
    box(3.55, -0.45, 4.05, -0.39, 0.02, 2.45, "tv_liston_i", oak, bevel=0.0)
    box(6.95, -0.45, 7.45, -0.39, 0.02, 2.45, "tv_liston_d", oak, bevel=0.0)
    box(4.05, -0.40, 6.95, -0.35, 2.46, 2.50, "tv_cove", m["led"], bevel=0.0)
    box(4.95, -0.395, 6.05, -0.34, 0.95, 1.75, "tv", m["pantalla"], bevel=0.0)
    box(4.25, -0.45, 6.75, -0.05, 0.22, 0.45, "tv_mueble", oak, bevel=0.01)
    box(3.30, -0.47, 3.78, -0.05, 0.0, 2.50, "pilar_visto", m["concreto"], bevel=0.0)
    box(4.40, 2.55, 6.70, 3.45, 0.16, 0.44, "sofa_base", fab, bevel=0.02)
    box(4.40, 3.14, 6.70, 3.50, 0.44, 0.84, "sofa_respaldo", fab, bevel=0.02)
    box(4.30, 2.50, 4.53, 3.50, 0.16, 0.60, "sofa_brazo_i", fab, bevel=0.02)
    box(6.57, 2.50, 6.80, 3.50, 0.16, 0.60, "sofa_brazo_d", fab, bevel=0.02)
    box(4.58, 2.58, 6.52, 3.16, 0.44, 0.53, "sofa_cojin", fab2, bevel=0.02)
    for i, x in enumerate((4.95, 5.55, 6.15)):
        box(x - 0.27, 3.00, x + 0.27, 3.22, 0.50, 0.80, f"cojin_{i}", lino, bevel=0.03)
    box(3.90, 1.15, 7.05, 3.00, 0.004, 0.014, "alfombra", fab2, bevel=0.0)
    box(5.05, 1.55, 5.95, 2.25, 0.28, 0.42, "mesa_centro", tra, bevel=0.01)
    box(6.85, 1.05, 7.45, 1.75, 0.16, 0.42, "butaca", fab, bevel=0.02)
    box(6.80, 1.00, 7.50, 1.10, 0.42, 0.95, "butaca_res", fab, bevel=0.02)
    cylinder(6.55, 2.65, 0.13, 0.0, 1.42, "lampara_pie", negro)
    sphere(6.55, 2.65, 1.52, 0.16, "lampara_pant", m["led"])
    cylinder(3.85, 2.75, 0.16, 0.0, 0.35, "maceta", m["maceta"])
    for i, (dx, dz) in enumerate(((0, 0), (0.20, 0.10), (-0.18, 0.12), (0.10, -0.18))):
        sphere(3.85 + dx, 2.75 + dz, 0.80 + i * 0.14, 0.22, f"planta_{i}",
               m["planta"], sy=0.75)
    box(7.00, 0.10, 7.55, 1.55, 0.0, 0.75, "aparador", oak, bevel=0.02)
    for i, x in enumerate((5.00, 5.75, 6.50)):
        box(x - 0.22, 3.40, x + 0.22, 3.42, 1.25, 1.85, f"cuadro_{i}", m["techo"],
            bevel=0.0)

    # COCINA
    box(-1.53, -0.40, -1.00, 2.35, 0.02, 0.90, "coc_mueble", oak, bevel=0.006)
    box(-1.56, -0.43, -0.96, 2.38, 0.90, 0.94, "coc_encimera", negro, bevel=0.004)
    box(-1.53, -0.40, -1.00, 0.15, 0.94, 2.25, "coc_columna", oak, bevel=0.006)
    box(-1.20, -0.36, -1.03, 0.11, 1.05, 1.60, "coc_horno1", negro, bevel=0.0)
    box(-1.20, -0.36, -1.03, 0.11, 1.65, 2.15, "coc_horno2", negro, bevel=0.0)
    box(-1.53, 0.30, -1.25, 2.35, 1.50, 2.25, "coc_altos", oak, bevel=0.006)
    box(-1.53, 0.30, -1.27, 2.35, 1.46, 1.50, "coc_led", m["led"], bevel=0.0)
    box(-1.42, 1.05, -1.12, 1.50, 0.935, 0.945, "coc_freg", negro, bevel=0.0)
    box(-0.15, 0.35, 1.05, 1.55, 0.02, 0.88, "isla", oak, bevel=0.01)
    box(-0.19, 0.31, 1.09, 1.59, 0.88, 0.94, "isla_tapa", negro, bevel=0.004)
    box(0.10, 0.60, 0.72, 1.30, 0.941, 0.947, "placa", m["pantalla"], bevel=0.0)
    for i, z in enumerate((0.55, 1.0, 1.45)):
        cylinder(1.35, z, 0.16, 0.60, 0.66, f"taburete_{i}", negro)
        cylinder(1.35, z, 0.14, 0.02, 0.60, f"taburete_pie_{i}", negro)
    box(0.10, 0.50, 0.80, 1.35, 2.44, 2.49, "campana", m["pantalla"], bevel=0.0)
    # comedor
    box(2.30, 1.40, 3.60, 2.80, 0.72, 0.76, "mesa", oak, bevel=0.008)
    for dx, dz in ((0.04, 0.04), (1.26, 0.04), (0.04, 1.36), (1.26, 1.36)):
        box(2.30 + dx, 1.40 + dz, 2.34 + dx, 1.44 + dz, 0.0, 0.72, f"mesa_pie",
            negro, bevel=0.0)
    for i, z in enumerate((1.70, 2.20, 2.70)):
        for x, side in ((2.02, -1), (3.88, 1)):
            box(x - 0.22, z - 0.22, x + 0.22, z + 0.22, 0.44, 0.47,
                f"silla_{i}_{side}", fab2, bevel=0.02)
            box(x - 0.22, z - 0.22, x + 0.22, z + 0.22, 0.47, 0.86,
                f"silla_res_{i}_{side}", fab2, bevel=0.02)
            for lx, lz in ((-0.16, -0.16), (0.16, -0.16), (-0.16, 0.16), (0.16, 0.16)):
                box(x + lx - 0.015, z + lz - 0.015, x + lx + 0.015, z + lz + 0.015,
                    0.0, 0.44, f"silla_pie_{i}_{side}", oak, bevel=0.0)

    # DORMITORIO PRINCIPAL
    box(1.95, -3.10, 2.55, -1.20, 0.02, 2.40, "dp_armario", oak, bevel=0.008)
    box(4.40, -3.05, 6.00, -1.05, 0.12, 0.34, "dp_cama", oak, bevel=0.02)
    box(4.36, -3.08, 6.04, -1.00, 0.34, 0.52, "dp_colchon", lino, bevel=0.03)
    box(4.44, -2.70, 5.96, -1.10, 0.50, 0.58, "dp_colcha", fab2, bevel=0.03)
    for i, x in enumerate((4.75, 5.65)):
        box(x - 0.32, -3.02, x + 0.32, -2.72, 0.52, 0.64, f"dp_almohada_{i}",
            lino, bevel=0.05)
    box(4.34, -3.12, 6.06, -3.04, 0.0, 1.15, "dp_cabecero", oak, bevel=0.01)
    box(4.34, -3.13, 6.06, -3.10, 2.44, 2.49, "dp_cove", m["led"], bevel=0.0)
    box(3.98, -3.05, 4.32, -2.68, 0.0, 0.46, "dp_mesita_i", tra, bevel=0.01)
    box(6.08, -3.05, 6.42, -2.68, 0.0, 0.46, "dp_mesita_d", tra, bevel=0.01)
    box(3.60, -2.90, 6.80, -0.90, 0.004, 0.012, "dp_alfombra", fab2, bevel=0.0)
    for i, x in enumerate((4.15, 6.25)):
        cylinder(x, -2.86, 0.02, 1.30, 2.30, f"dp_hilo_{i}", negro, n=8)
        sphere(x, -2.86, 1.28, 0.09, f"dp_pant_{i}", m["led"], seg=12, ring=6)
    box(6.60, -1.05, 7.90, -0.62, 0.0, 0.45, "dp_banco", fab, bevel=0.02)

    # DORMITORIO 1 (arriba izquierda)
    box(-7.00, -2.95, -6.10, -1.00, 0.12, 0.34, "d1_cama", oak, bevel=0.02)
    box(-7.04, -2.99, -6.06, -0.96, 0.34, 0.50, "d1_colchon", lino, bevel=0.03)
    box(-6.99, -2.65, -6.11, -1.05, 0.48, 0.56, "d1_colcha", fab2, bevel=0.03)
    box(-6.80, -2.94, -6.20, -2.66, 0.50, 0.62, "d1_almohada", lino, bevel=0.05)
    box(-7.02, -3.02, -6.08, -2.94, 0.0, 1.05, "d1_cabecero", oak, bevel=0.01)
    box(-4.55, -3.00, -4.05, -1.10, 0.02, 2.40, "d1_armario", oak, bevel=0.008)
    box(-6.60, -2.10, -6.00, -1.50, 0.0, 0.74, "d1_mesita", oak, bevel=0.01)

    # DORMITORIO 2 (abajo izquierda)
    box(-6.95, 0.70, -4.95, 2.20, 0.12, 0.34, "d2_cama", oak, bevel=0.02)
    box(-6.99, 0.66, -4.91, 2.24, 0.34, 0.52, "d2_colchon", lino, bevel=0.03)
    box(-6.60, 0.72, -4.98, 2.18, 0.50, 0.58, "d2_colcha", fab2, bevel=0.03)
    for i, z in enumerate((1.05, 1.85)):
        box(-6.92, z - 0.30, -6.62, z + 0.30, 0.52, 0.64, f"d2_almohada_{i}",
            lino, bevel=0.05)
    box(-6.99, 0.62, -4.91, 0.70, 0.0, 1.10, "d2_cabecero", oak, bevel=0.01)
    box(-5.60, -0.05, -3.70, 0.45, 0.02, 2.40, "d2_armario", oak, bevel=0.008)
    box(-6.95, 0.20, -6.65, 0.55, 0.0, 0.46, "d2_mesita_i", tra, bevel=0.01)
    box(-6.95, 2.35, -6.65, 2.70, 0.0, 0.46, "d2_mesita_d", tra, bevel=0.01)

    # DORMITORIO 3 / ESTUDIO
    box(-3.45, 0.30, -2.55, 2.20, 0.12, 0.34, "d3_cama", oak, bevel=0.02)
    box(-3.49, 0.26, -2.51, 2.24, 0.34, 0.50, "d3_colchon", lino, bevel=0.03)
    box(-3.44, 0.60, -2.56, 2.19, 0.48, 0.56, "d3_colcha", fab2, bevel=0.03)
    box(-3.25, 0.34, -2.75, 0.60, 0.50, 0.62, "d3_almohada", lino, bevel=0.05)
    box(-3.47, 0.22, -2.53, 0.30, 0.0, 1.05, "d3_cabecero", oak, bevel=0.01)
    box(-2.12, 0.60, -1.68, 1.90, 0.72, 0.76, "d3_escritorio", oak, bevel=0.008)
    for dz in (0.64, 1.84):
        box(-2.06, dz - 0.03, -1.74, dz + 0.03, 0.0, 0.72, "d3_pie", negro, bevel=0.0)
    box(-2.30, 1.05, -1.95, 1.45, 0.42, 0.88, "d3_silla", fab2, bevel=0.02)
    box(-3.45, 2.35, -2.95, 2.85, 0.02, 2.30, "d3_armario", oak, bevel=0.008)

    # BAÑO 1 (ducha)
    for k, (x0, z0, x1, z1) in enumerate(((-3.95, -3.16, -1.35, -3.10),
                                          (-3.95, -3.16, -3.89, -1.50),
                                          (-1.41, -3.16, -1.35, -1.50),
                                          (-3.95, -1.56, -1.35, -1.50))):
        box(x0, z0, x1, z1, 0.0, 2.30, f"b1_azulejo_{k}", m["azulejo"], bevel=0.0)
    box(-3.85, -3.10, -2.85, -2.20, 0.0, 0.06, "b1_plato", m["techo"], bevel=0.0)
    box(-2.90, -3.10, -2.86, -2.20, 0.05, 2.0, "b1_mampara", m["cristal"], bevel=0.0)
    box(-3.90, -2.12, -2.80, -2.08, 0.05, 2.0, "b1_mampara2", m["cristal"], bevel=0.0)
    cylinder(-3.35, -3.08, 0.02, 0.9, 2.1, "b1_columna", m["cobre"], n=10)
    box(-3.43, -3.10, -3.27, -3.06, 1.9, 2.05, "b1_ducha", m["cobre"], bevel=0.0)
    box(-2.10, -3.12, -1.62, -2.62, 0.0, 0.44, "b1_wc", m["techo"], bevel=0.02)
    box(-2.06, -3.14, -1.66, -3.00, 0.44, 0.95, "b1_cisterna", m["techo"], bevel=0.0)
    box(-3.00, -1.98, -1.60, -1.56, 0.35, 0.85, "b1_mueble", oak, bevel=0.006)
    box(-3.04, -2.02, -1.56, -1.52, 0.85, 0.90, "b1_encimera", tra, bevel=0.004)
    box(-2.30, -1.90, -2.10, -1.70, 0.90, 1.05, "b1_lavabo", m["techo"], bevel=0.02)
    cylinder(-2.20, -1.72, 0.015, 0.90, 1.20, "b1_grifo", m["cobre"], n=10)
    box(-3.00, -1.545, -1.60, -1.52, 1.05, 1.95, "b1_espejo", m["espejo"], bevel=0.0)
    box(-3.00, -1.99, -1.60, -1.95, 0.30, 0.35, "b1_led", m["led"], bevel=0.0)

    # BAÑO 2 (bañera)
    for k, (x0, z0, x1, z1) in enumerate(((-0.91, -3.16, 1.76, -3.10),
                                          (-0.91, -3.16, -0.85, -1.50),
                                          (1.70, -3.16, 1.76, -1.50),
                                          (-0.91, -1.56, 1.76, -1.50))):
        box(x0, z0, x1, z1, 0.0, 2.30, f"b2_azulejo_{k}", m["azulejo"], bevel=0.0)
    box(0.25, -3.12, 1.70, -2.32, 0.0, 0.55, "b2_banera", m["techo"], bevel=0.02)
    box(0.32, -3.05, 1.63, -2.39, 0.40, 0.52, "b2_banera_int", m["azulejo"], bevel=0.0)
    box(-0.80, -3.10, -0.35, -2.60, 0.0, 0.44, "b2_wc", m["techo"], bevel=0.02)
    box(-0.76, -3.13, -0.39, -3.00, 0.44, 0.95, "b2_cisterna", m["techo"], bevel=0.0)
    box(0.30, -1.99, 1.66, -1.57, 0.35, 0.85, "b2_mueble", oak, bevel=0.006)
    box(0.26, -2.03, 1.70, -1.53, 0.85, 0.90, "b2_encimera", tra, bevel=0.004)
    box(0.80, -1.91, 1.00, -1.71, 0.90, 1.05, "b2_lavabo", m["techo"], bevel=0.02)
    cylinder(0.90, -1.73, 0.015, 0.90, 1.20, "b2_grifo", m["cobre"], n=10)
    box(0.30, -1.545, 1.66, -1.52, 1.05, 1.95, "b2_espejo", m["espejo"], bevel=0.0)

    # RECIBIDOR / CASONETO
    box(-0.45, 2.55, 0.30, 4.00, 0.02, 2.40, "rec_armario", oak, bevel=0.008)
    box(0.75, 2.60, 1.30, 3.05, 0.0, 0.45, "rec_banco", oak, bevel=0.01)
    box(1.05, 3.20, 1.32, 3.60, 0.9, 1.9, "rec_espejo", m["espejo"], bevel=0.0)
    box(0.25, 3.95, 0.90, 3.99, 0.0, 2.15, "rec_puerta", m["roble"], bevel=0.004)

    # TERRAZA
    for i, z in enumerate((0.05, 1.85)):
        box(8.35, z, 9.05, z + 1.55, 0.10, 0.32, f"tz_hamaca_{i}", fab2, bevel=0.02)
        box(8.35, z + 1.35, 9.05, z + 1.55, 0.32, 0.62, f"tz_res_{i}", fab2, bevel=0.02)
    box(8.45, -0.45, 9.25, -0.15, 0.0, 0.40, "tz_mesita", tra, bevel=0.01)
    cylinder(9.20, 3.10, 0.20, 0.0, 0.55, "tz_maceta", m["maceta"])
    sphere(9.20, 3.10, 0.85, 0.30, "tz_planta", m["planta"], sy=0.8)
    # peto de terraza
    box(9.42, -0.50, 9.55, 3.50, 0.0, 1.05, "peto_e", m["muro"], bevel=0.0)
    box(8.23, 3.42, 9.55, 3.55, 0.0, 1.05, "peto_s", m["muro"], bevel=0.0)


def build_exterior(m):
    box(-150.0, -150.0, 150.0, 150.0, -16.0, -15.0, "ext_suelo", m["ext_suelo"],
        bevel=0.0)
    # patio interior al sur (para la vidriera del salón)
    box(-9.0, 3.9, 9.0, 14.0, -3.8, -3.5, "ext_patio", m["ext_suelo"], bevel=0.0)
    # edificios de enfrente (contexto por las ventanas)
    bloques = [(-40, 26, -12, 54, 14), (16, 30, 40, 56, 16), (-44, 56, -14, 90, 12),
               (14, -42, 44, -22, 18), (48, -8, 76, 24, 16)]
    for k, (x0, z0, x1, z1, h) in enumerate(bloques):
        box(x0, z0, x1, z1, -15.0, -15.0 + h, f"ext_b_{k}", m["ext_edificio"],
            bevel=0.0)


def build_luces(m):
    # cielo
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes.get("Background")
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(58)
    sky.sun_rotation = math.radians(200)
    sky.sun_intensity = 0.0
    sky.altitude = 30
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.15

    # sol desde el sur del modelo (viaja hacia +Y de Blender)
    sd = bpy.data.lights.new("sol", "SUN")
    sd.energy = 1.4
    sd.angle = math.radians(9)
    sd.color = (1.0, 0.96, 0.90)
    so = bpy.data.objects.new("sol", sd)
    bpy.context.collection.objects.link(so)
    d = Vector((0.22, 0.80, -0.56)).normalized()
    so.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    # luz difusa de ventanas (portales)
    win = [
        (0.0, 6.8, 5.5, 13, 5.5, 150),     # norte (Blender +Y)
        (0.0, -6.8, 5.5, 12, 5.5, 120),    # sur
        (11.5, -1.5, 5.5, 8, 5.0, 110),    # este
    ]
    for k, (x, y, h, sx, sy, power) in enumerate(win):
        ld = bpy.data.lights.new(f"sky_portal_{k}", "AREA")
        ld.shape = "RECTANGLE"
        ld.size = sx
        ld.size_y = sy
        ld.energy = power
        ld.color = (0.82, 0.88, 1.0)
        lo = bpy.data.objects.new(f"sky_portal_{k}", ld)
        bpy.context.collection.objects.link(lo)
        lo.location = (x, y, h)
        dirv = Vector((-x, -y, 0.6)).normalized()
        lo.rotation_euler = dirv.to_track_quat("-Z", "Y").to_euler()

    # downlights cálidos
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
    for k, (x, z) in enumerate(dls):
        ld = bpy.data.lights.new(f"dl_{k}", "AREA")
        ld.shape = "DISK"
        ld.size = 0.075
        ld.energy = 30
        ld.color = (1.0, 0.84, 0.66)
        lo = bpy.data.objects.new(f"dl_{k}", ld)
        bpy.context.collection.objects.link(lo)
        lo.location = (x, -z, 2.46)
        cylinder(x, z, 0.05, 2.485, 2.50, f"dl_disco_{k}", m["led"], n=16)


def build_cameras():
    scene = bpy.context.scene
    cams = []
    for name, x, z, yaw, _label in PANOS:
        cd = bpy.data.cameras.new(name)
        cd.type = "PANO"
        cd.panorama_type = "EQUIRECTANGULAR"
        cd.clip_end = 300
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
        co = bpy.data.objects.new(st["id"], cd)
        bpy.context.collection.objects.link(co)
        co.location = (st["x"], -st["z"], st["h"])
        d = Vector((st["tx"] - st["x"], -(st["tz"] - st["z"]),
                    st["th"] - st["h"])).normalized()
        co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        cams.append(co)
    scene.camera = cams[0]


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 8
    scene.cycles.transparent_max_bounces = 8
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = -0.15
    scene.render.use_persistent_data = True
    scene.render.threads_mode = "AUTO"


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    m = build_materials()
    setup_render()
    walls = build_shell(m)
    build_bandas(m, walls)
    build_ventanas(m)
    build_puertas(m)
    build_mobiliario(m)
    build_exterior(m)
    build_luces(m)
    build_cameras()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
    nb = len([o for o in bpy.data.objects if o.type == "MESH"])
    print(f"OK escena: {nb} mallas, {len(PANOS)} panos, {len(STILLS)} stills -> {OUT}")


if __name__ == "__main__":
    main()
