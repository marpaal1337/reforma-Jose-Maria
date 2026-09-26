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
PUERTAS = json.loads((ROOT / "data" / "puertas.json").read_text(encoding="utf-8"))
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


PBR_DIR = ROOT / "data" / "pbr"


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
    m["muro"] = principled("muro", base=(0.87, 0.86, 0.83), rough=0.92)
    m["techo"] = principled("techo", base=(0.93, 0.92, 0.90), rough=0.95)
    m["suelo_madera"] = pbr_material("suelo_madera", "oak_wood_planks", tex_m=1.2,
                                     nor=0.5, rough_mul=0.85) or \
        wood_material("suelo_madera", (0.40, 0.26, 0.155), (0.47, 0.32, 0.20),
                      (0.37, 0.24, 0.14), (0.09, 5.0, 1.0), rough=0.34)
    m["terraza"] = pbr_material("terraza_madera", "oak_wood_planks", tex_m=0.9,
                                nor=0.7, rough_mul=1.6, value=0.85, sat=0.7) or \
        wood_material("terraza_madera", (0.30, 0.20, 0.12), (0.38, 0.26, 0.16),
                      (0.26, 0.17, 0.10), (0.5, 2.0, 1.0), rough=0.6)
    m["marmol"] = stone_material("marmol", (0.80, 0.78, 0.74), (0.62, 0.61, 0.59),
                                 scale=1.4, rough=0.15)
    m["azulejo"] = tile_material("azulejo")
    m["travertino"] = pbr_material("travertino", "travertine", tex_m=2.0,
                                   nor=0.6, rough_mul=1.0) or \
        stone_material("travertino", (0.72, 0.64, 0.51), (0.58, 0.50, 0.38),
                       scale=2.2, rough=0.6)
    m["roble"] = pbr_material("roble", "oak_veneer_01", tex_m=1.83, rot=90,
                              nor=0.35, rough_mul=0.9) or \
        wood_material("roble", (0.38, 0.24, 0.135), (0.46, 0.30, 0.175),
                      (0.35, 0.22, 0.12), (0.18, 4.0, 1.0), rough=0.42)
    m["roble_h"] = pbr_material("roble_h", "oak_veneer_01", tex_m=1.83,
                                nor=0.35, rough_mul=0.9) or m["roble"]
    m["piedra_negra"] = principled("piedra_negra", base=(0.045, 0.042, 0.040),
                                   rough=0.18, spec=0.7)
    m["cobre"] = principled("cobre", base=(0.72, 0.43, 0.20), rough=0.28, metal=1.0)
    m["latón"] = principled("laton", base=(0.62, 0.48, 0.24), rough=0.35, metal=1.0)
    m["aluminio"] = principled("aluminio", base=(0.12, 0.115, 0.11), rough=0.35,
                               metal=1.0, spec=0.6)
    m["cristal"] = principled("cristal", base=(1, 1, 1), rough=0.015, trans=1.0)
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
    m["lino"] = principled("lino", base=(0.86, 0.83, 0.76), rough=0.95)
    noise_bump(m["lino"], scale=300, strength=0.15)
    m["alfombra"] = pbr_material("alfombra", "hessian_230", tex_m=0.54, nor=0.9,
                                 value=1.08, sat=0.55) or m["tejido_claro"]
    m["cuero"] = pbr_material("cuero", "brown_leather", tex_m=0.7, nor=0.9,
                              rough_mul=0.9) or \
        principled("cuero", base=(0.25, 0.11, 0.05), rough=0.5)
    m["cortina"] = principled("cortina", base=(0.96, 0.95, 0.92), rough=0.6,
                              trans=0.72)
    m["negro_mate"] = principled("negro_mate", base=(0.02, 0.02, 0.02), rough=0.6)
    m["metal_negro"] = principled("metal_negro", base=(0.035, 0.035, 0.037),
                                  rough=0.42, metal=1.0)
    m["blanco_laca"] = principled("blanco_laca", base=(0.93, 0.93, 0.91), rough=0.35)
    m["vidrio_acido"] = principled("vidrio_acido", base=(0.92, 0.94, 0.93),
                                   rough=0.45, trans=0.55)
    m["pantalla"] = principled("pantalla", base=(0.012, 0.012, 0.014), rough=0.08,
                               spec=0.8)
    m["planta"] = principled("planta", base=(0.055, 0.13, 0.045), rough=0.55)
    m["tierra"] = principled("tierra", base=(0.045, 0.032, 0.022), rough=0.95)
    m["maceta"] = principled("maceta", base=(0.85, 0.84, 0.80), rough=0.7)
    arte = principled("lienzo", base=(0.88, 0.85, 0.79), rough=0.9)
    ant = arte.node_tree
    bsdf_a = ant.nodes.get("Principled BSDF")
    texo = ant.nodes.new("ShaderNodeTexNoise")
    texo.inputs["Scale"].default_value = 1.5
    texo.inputs["Detail"].default_value = 4.0
    rampa = ant.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (0.64, 0.58, 0.48, 1)
    rampa.color_ramp.elements[1].color = (0.94, 0.92, 0.88, 1)
    e_art = rampa.color_ramp.elements.new(0.45)
    e_art.color = (0.83, 0.78, 0.68, 1)
    ant.links.new(texo.outputs["Fac"], rampa.inputs["Fac"])
    ant.links.new(rampa.outputs["Color"], bsdf_a.inputs["Base Color"])
    m["lienzo"] = arte
    m["led"] = principled("led", base=(1.0, 0.93, 0.82), rough=0.5,
                          emission=(1.0, 0.86, 0.66), emit_str=16.0)
    m["lampara_pantalla"] = principled("lampara_pantalla", base=(0.95, 0.93, 0.88),
                                       rough=0.85, emission=(1.0, 0.90, 0.74),
                                       emit_str=2.2)
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
    textura en su tamaño real (`tex_m`)."""
    for ob in bpy.data.objects:
        if ob.type != "MESH":
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
    """Puertas interiores según data/puertas.json (medición PE.A.02 + PEI.07).

    Tipos: abatibles lacadas blancas (D1-D5), correderas (D6 vidriera a baño,
    D7 blanca a casoneto), entrada existente (D0, hoja cerrada) y vidriera
    P03 de suelo a techo (D8). Los huecos ya vienen abiertos en PLAN["muros"];
    aquí solo marcos, hojas y dinteles. Nombres compatibles con el filtro del
    visor (pmarco_*, pdintel_*, phoja_*, dintel_*, vidrio_*).
    """
    laca, roble = m["blanco_laca"], m["roble"]
    vidrio, acido = m["cristal"], m["vidrio_acido"]
    por_id = {p["id"]: p for p in PUERTAS["puertas"]}

    def marco_h(pid, x0, x1, zc, h, mat, t=0.06, d=0.20):
        box(x0 - t / 2, zc - d / 2, x0 + t / 2, zc + d / 2, 0, h,
            f"pmarco_{pid}_i", mat, bevel=0.0)
        box(x1 - t / 2, zc - d / 2, x1 + t / 2, zc + d / 2, 0, h,
            f"pmarco_{pid}_d", mat, bevel=0.0)
        box(x0 - t / 2, zc - d / 2, x1 + t / 2, zc + d / 2, h, h + 0.06,
            f"pmarco_{pid}_s", mat, bevel=0.0)

    def marco_v(pid, z0, z1, xc, h, mat, t=0.06, d=0.20):
        box(xc - d / 2, z0 - t / 2, xc + d / 2, z0 + t / 2, 0, h,
            f"pmarco_{pid}_i", mat, bevel=0.0)
        box(xc - d / 2, z1 - t / 2, xc + d / 2, z1 + t / 2, 0, h,
            f"pmarco_{pid}_d", mat, bevel=0.0)
        box(xc - d / 2, z0 - t / 2, xc + d / 2, z1 + t / 2, h, h + 0.06,
            f"pmarco_{pid}_s", mat, bevel=0.0)

    def dintel_h(pid, x0, x1, zc, h0, d=0.20):
        box(x0, zc - d / 2, x1, zc + d / 2, h0, ALTURA,
            f"dintel_{pid}", m["muro"], bevel=0.0)

    def dintel_v(pid, z0, z1, xc, h0, d=0.20):
        box(xc - d / 2, z0, xc + d / 2, z1, h0, ALTURA,
            f"dintel_{pid}", m["muro"], bevel=0.0)

    def hoja_abatible(pid, hinge, ang_deg, largo, h, mat, grueso=0.045):
        a = math.radians(ang_deg)
        cx = hinge[0] + math.cos(a) * largo / 2
        cz = hinge[1] + math.sin(a) * largo / 2
        rot_box(cx, cz, largo, grueso, ang_deg, 0.02, h,
                f"phoja_{pid}", mat, bevel=0.004)

    for pid in ("D1", "D2", "D3"):
        p = por_id[pid]
        x0, x1 = p["centro"][0] - p["ancho"] / 2, p["centro"][0] + p["ancho"] / 2
        zc, h = p["centro"][1], p["alto"]
        marco_h(pid, x0, x1, zc, h, laca)
        dintel_h(pid, x0, x1, zc, h)
        hx = x1 - 0.035 if p["bisagra"] == "E" else x0 + 0.035
        hoja_abatible(pid, (hx, zc), 90, p["ancho"] - 0.07, h, laca)

    for pid in ("D4", "D5"):
        p = por_id[pid]
        xc = p["centro"][0]
        z0, z1 = p["centro"][1] - p["ancho"] / 2, p["centro"][1] + p["ancho"] / 2
        h = p["alto"]
        marco_v(pid, z0, z1, xc, h, laca)
        dintel_v(pid, z0, z1, xc, h)
        hz = z1 - 0.035  # bisagra S en ambas
        ang = 0 if p["apertura"] == "E" else 180
        hoja_abatible(pid, (xc, hz), ang, p["ancho"] - 0.07, h, laca)

    # D6: corredera vidriera a baño 1 (hoja cerrada + guía)
    p = por_id["D6"]
    x0, x1 = p["centro"][0] - p["ancho"] / 2, p["centro"][0] + p["ancho"] / 2
    zc, h = p["centro"][1], p["alto"]
    box(x0 - 0.03, zc - 0.10, x0 + 0.03, zc + 0.10, 0, h,
        "pmarco_D6_i", laca, bevel=0.0)
    box(x1 - 0.03, zc - 0.10, x1 + 0.03, zc + 0.10, 0, h,
        "pmarco_D6_d", laca, bevel=0.0)
    box(x0 - 0.45, zc - 0.05, x1 + 0.15, zc + 0.05, h, h + 0.09,
        "pmarco_rail_D6", m["aluminio"], bevel=0.0)
    box(x0 + 0.02, zc - 0.015, x1 - 0.02, zc + 0.015, 0.02, h,
        "phoja_corr_D6", vidrio, bevel=0.0)
    for xx in (x0 + 0.02, x1 - 0.02):
        box(xx - 0.025, zc - 0.025, xx + 0.025, zc + 0.025, 0.02, h,
            "pmarco_D6_jamba", roble, bevel=0.0)
    box(x0, zc - 0.03, x1, zc + 0.03, h, h + 0.05,
        "pmarco_D6_cab", roble, bevel=0.0)
    dintel_h("D6", x0, x1, zc, h + 0.09)

    # D7: corredera P04 a casoneto (hoja abierta, aparcada al este)
    p = por_id["D7"]
    x0, x1 = p["centro"][0] - p["ancho"] / 2, p["centro"][0] + p["ancho"] / 2
    zc, h = p["centro"][1], p["alto"]
    box(x0 - 0.025, zc - 0.06, x0 + 0.025, zc + 0.06, 0, h + 0.03,
        "pmarco_D7_i", laca, bevel=0.0)
    box(x1 - 0.025, zc - 0.06, x1 + 0.025, zc + 0.06, 0, h + 0.03,
        "pmarco_D7_d", laca, bevel=0.0)
    box(x0 - 0.10, zc + 0.02, x1 + 0.70, zc + 0.10, h, h + 0.09,
        "pmarco_rail_D7", m["aluminio"], bevel=0.0)
    box(x1 + 0.02, zc + 0.06, x1 + 0.62, zc + 0.10, 0.02, h,
        "phoja_corr_D7", laca, bevel=0.004)

    # D0: entrada existente (hoja cerrada panelada en blanco)
    p = por_id["D0"]
    x0, x1 = p["centro"][0] - p["ancho"] / 2, p["centro"][0] + p["ancho"] / 2
    zc, h = p["centro"][1], p["alto"]
    marco_h("D0", x0, x1, zc, h, laca, d=0.30)
    box(x0 + 0.02, zc - 0.025, x1 - 0.02, zc + 0.025, 0.02, h,
        "phoja_D0", laca, bevel=0.004)
    dintel_h("D0", x0, x1, zc, h, d=0.30)

    # D8: vidriera P03 (marco de roble + cristal, hoja abierta 70°)
    p = por_id["D8"]
    hx, hz = 0.70, 4.40
    largo = p["ancho"] - 0.07
    box(hx - 0.03, hz - 0.10, hx + 0.03, hz + 0.10, 0, p["alto"],
        "pmarco_D8_i", roble, bevel=0.0)
    a = math.radians(-20)
    cx = hx + math.cos(a) * largo / 2
    cz = hz + math.sin(a) * largo / 2
    rot_box(cx, cz, largo, 0.04, -20, 0.02, p["alto"],
            "phoja_D8", vidrio, bevel=0.0)
    mx, mz = hx + math.cos(a) * largo - 0.02, hz + math.sin(a) * largo
    box(mx - 0.025, mz - 0.025, mx + 0.025, mz + 0.025, 0.02, p["alto"],
        "pmarco_D8_canto", roble, bevel=0.0)

    # PA02: separador fijo de vidrio al ácido (recto + curvo aproximado)
    for k, t in enumerate(PUERTAS["separadores"][0]["tramos"]):
        (ax, az), (bx, bz) = t["de"], t["a"]
        L = math.hypot(bx - ax, bz - az)
        ang = math.degrees(math.atan2(bz - az, bx - ax))
        rot_box((ax + bx) / 2, (az + bz) / 2, L, 0.02, ang, 0.05, 2.40,
                f"vidrio_pa02_{k}", acido, bevel=0.0)
        for ex, ez in ((ax, az), (bx, bz)):
            box(ex - 0.02, ez - 0.02, ex + 0.02, ez + 0.02, 0.0, 2.45,
                f"pmarco_pa02_{k}", roble, bevel=0.0)


def build_mobiliario(m):
    oak = m["roble"]
    fab, fab2, lino = m["tejido"], m["tejido_claro"], m["lino"]
    negro, piedra, tra = m["piedra_negra"], m["travertino"], m["travertino"]
    metal = m["metal_negro"]

    # SALÓN — frente de TV, sofá, butaca mariposa, mesa, lámpara y cortinas
    # pilar visto (hormigón) y panel de travertino flanqueado por listones
    box(3.30, -0.47, 3.78, -0.05, 0.0, 2.50, "pilar_visto", m["concreto"],
        bevel=0.012)
    box(4.05, -0.45, 6.95, -0.405, 0.02, 2.45, "tv_panel", tra, bevel=0.0)
    for zona, (xa, xb) in enumerate(((3.55, 4.05), (6.95, 7.45))):
        n = max(3, int(round((xb - xa) / 0.062)))
        an = (xb - xa) / (2 * n - 1)
        for k in range(n):
            x0 = xa + k * 2 * an
            box(x0, -0.455, x0 + an, -0.415, 0.02, 2.45,
                f"tv_liston_{zona}_{k}", oak, bevel=0.0)
    box(4.05, -0.40, 6.95, -0.35, 2.46, 2.50, "tv_cove", m["led"], bevel=0.0)
    box(4.95, -0.395, 6.05, -0.345, 0.95, 1.75, "tv", m["pantalla"], bevel=0.008)
    box(4.25, -0.45, 6.75, -0.05, 0.22, 0.45, "tv_mueble", oak, bevel=0.012)
    for k in range(4):
        x0 = 4.28 + k * 0.622
        box(x0, -0.062, x0 + 0.612, -0.048, 0.235, 0.435,
            f"tv_mueble_f{k}", oak, bevel=0.004)
    # sofá bajo de tres plazas: estructura de roble, patas metálicas y
    # colchones de tejido con cantos redondeados
    for k, x in enumerate((4.62, 5.55, 6.48)):
        for j, zz in enumerate((2.70, 3.32)):
            box(x - 0.016, zz - 0.016, x + 0.016, zz + 0.016, 0.0, 0.15,
                f"sofa_pata_{k}_{j}", metal, bevel=0.0)
    box(4.52, 2.62, 6.58, 3.40, 0.15, 0.32, "sofa_bastidor", oak, bevel=0.012)
    for k in range(3):
        x0 = 4.58 + k * 0.675
        box(x0 + 0.008, 2.62, x0 + 0.667, 3.30, 0.32, 0.49,
            f"sofa_asiento_{k}", fab, bevel=0.06)
        caja_inclinada(x0 + 0.008, 3.16, x0 + 0.667, 3.38, 0.46, 0.88,
                       0.0, 0.10, f"sofa_respaldo_{k}", fab, bevel=0.055)
    box(4.40, 2.60, 4.56, 3.42, 0.15, 0.64, "sofa_brazo_i", fab, bevel=0.05)
    box(6.54, 2.60, 6.70, 3.42, 0.15, 0.64, "sofa_brazo_d", fab, bevel=0.05)
    for k, x in enumerate((4.96, 5.90)):
        caja_inclinada(x - 0.17, 3.08, x + 0.17, 3.24, 0.47, 0.79,
                       0.0, 0.09, f"cojin_{k}", lino, bevel=0.05)
    box(3.90, 1.15, 7.05, 3.00, 0.004, 0.016, "alfombra", m["alfombra"],
        bevel=0.0)
    # mesa de centro: dos bases de travertino y tapa de cristal
    for k, x0 in enumerate((5.06, 5.54)):
        box(x0, 1.63, x0 + 0.42, 2.17, 0.012, 0.375, f"mesa_centro_base_{k}",
            tra, bevel=0.008)
    box(4.98, 1.55, 6.02, 2.25, 0.375, 0.39, "mesa_centro_tapa",
        m["cristal"], bevel=0.0)
    # butaca mariposa (cuero y varilla)
    butaca_mariposa(6.55, 1.05, 215, m)
    # lámpara de pie
    cylinder(6.55, 2.65, 0.15, 0.0, 0.025, "lampara_pie_base", metal, n=24)
    cylinder(6.55, 2.65, 0.012, 0.025, 1.38, "lampara_pie", metal, n=10)
    cylinder(6.55, 2.65, 0.175, 1.38, 1.66, "lampara_pant",
             m["lampara_pantalla"], n=28)
    planta_monstera(7.85, -0.35, "planta", m, alto=1.35, n_hojas=7)
    # aparador de roble con frentes y patas metálicas
    box(7.00, 0.10, 7.50, 1.55, 0.12, 0.78, "aparador", oak, bevel=0.02)
    for k, zz in enumerate((0.16, 1.44)):
        box(7.00, zz - 0.02, 7.04, zz + 0.02, 0.0, 0.12,
            f"aparador_pata_{k}", metal, bevel=0.0)
    for k, z0 in enumerate((0.16, 0.86)):
        box(6.985, z0, 6.998, z0 + 0.66, 0.18, 0.72, f"aparador_f{k}", oak,
            bevel=0.004)
    # cuadros sobre el sofá y cortinas del ventanal
    for i, x in enumerate((5.00, 5.75, 6.50)):
        box(x - 0.245, 3.415, x + 0.245, 3.44, 1.21, 1.89,
            f"cuadro_{i}_marco", oak, bevel=0.004)
        box(x - 0.215, 3.40, x + 0.215, 3.42, 1.245, 1.855, f"cuadro_{i}",
            m["lienzo"], bevel=0.0)
    cortina(8.02, 0.55, 1.15, 0.03, 2.42, ondas=1, amp=0.07,
            name="cortina_i", mat=m["cortina"])
    cortina(8.02, 2.83, 3.43, 0.03, 2.42, ondas=1, amp=0.07,
            name="cortina_d", mat=m["cortina"])
    box(7.96, 0.50, 8.05, 3.48, 2.42, 2.46, "cortina_rail", metal, bevel=0.0)

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
            xb = x + side * 0.185
            box(x - 0.21, z - 0.21, x + 0.21, z + 0.21, 0.44, 0.475,
                f"silla_{i}_{side}", fab2, bevel=0.035)
            box(xb - 0.03, z - 0.20, xb + 0.03, z + 0.20, 0.475, 0.85,
                f"silla_res_{i}_{side}", fab2, bevel=0.035)
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

    # TERRAZA
    for i, z in enumerate((0.05, 1.85)):
        box(8.35, z, 9.05, z + 1.55, 0.10, 0.32, f"tz_hamaca_{i}", fab2, bevel=0.02)
        box(8.35, z + 1.35, 9.05, z + 1.55, 0.32, 0.62, f"tz_res_{i}", fab2, bevel=0.02)
    box(8.45, -0.45, 9.25, -0.15, 0.0, 0.40, "tz_mesita", tra, bevel=0.01)
    cylinder(9.20, 3.10, 0.20, 0.0, 0.55, "tz_maceta", m["maceta"])
    sphere(9.20, 3.10, 0.85, 0.30, "tz_planta", m["planta"], sy=0.8)
    # petos de terraza (el norte faltaba en el modelo: hueco al vacío)
    box(9.42, -0.50, 9.55, 3.50, 0.0, 1.05, "peto_e", m["muro"], bevel=0.0)
    box(8.23, 3.42, 9.55, 3.55, 0.0, 1.05, "peto_s", m["muro"], bevel=0.0)
    box(8.23, -0.62, 9.55, -0.50, 0.0, 1.05, "peto_n", m["muro"], bevel=0.0)


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
    sky.sun_elevation = math.radians(45)
    sky.sun_rotation = math.radians(200)
    sky.sun_intensity = 0.0
    sky.altitude = 30
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.28

    # sol de mañana entrando por el ventanal (fachada este: +x -> -x)
    sd = bpy.data.lights.new("sol", "SUN")
    sd.energy = 14.0
    sd.angle = math.radians(3.5)
    sd.color = (1.0, 0.90, 0.78)
    so = bpy.data.objects.new("sol", sd)
    bpy.context.collection.objects.link(so)
    d = Vector((-0.80, 0.33, -0.60)).normalized()
    so.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    # luz difusa de ventanas (portales); el del ventanal V01 es el principal
    win = [
        (7.9, -1.99, 1.06, 3.0, 2.1, 25),    # ventanal V01 (este, emulado por dentro)
        (0.0, 6.8, 5.5, 13, 5.5, 90),        # norte (Blender +Y)
        (0.0, -6.8, 5.5, 12, 5.5, 110),       # sur
    ]
    for k, (x, y, h, sx, sy, power) in enumerate(win):
        ld = bpy.data.lights.new(f"sky_portal_{k}", "AREA")
        ld.shape = "RECTANGLE"
        ld.size = sx
        ld.size_y = sy
        ld.energy = power
        ld.color = (0.85, 0.90, 1.0)
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
        ld.energy = 15
        ld.color = (1.0, 0.84, 0.66)
        lo = bpy.data.objects.new(f"dl_{k}", ld)
        bpy.context.collection.objects.link(lo)
        lo.location = (x, -z, 2.46)
        cylinder(x, z, 0.05, 2.485, 2.50, f"dl_disco_{k}", m["led"], n=16)

    # lámpara de pie (pantalla) y luz rasante del frente de TV
    lp = bpy.data.lights.new("lampara_pt", "POINT")
    lp.energy = 12.0
    lp.color = (1.0, 0.82, 0.62)
    lp.shadow_soft_size = 0.12
    lo = bpy.data.objects.new("lampara_pt", lp)
    bpy.context.collection.objects.link(lo)
    lo.location = (6.55, -2.65, 1.52)

    rl = bpy.data.lights.new("relleno", "AREA")
    rl.shape = "RECTANGLE"
    rl.size = 3.0
    rl.size_y = 2.0
    rl.energy = 30.0
    rl.color = (1.0, 0.96, 0.92)
    ro = bpy.data.objects.new("relleno", rl)
    bpy.context.collection.objects.link(ro)
    ro.location = (2.0, 0.5, 2.2)
    rv = Vector((5.0, -2.5, -0.6)).normalized()
    ro.rotation_euler = rv.to_track_quat("-Z", "Y").to_euler()

    gr = bpy.data.lights.new("graze_tv", "AREA")
    gr.shape = "RECTANGLE"
    gr.size = 3.2
    gr.size_y = 0.25
    gr.energy = 30.0
    gr.color = (1.0, 0.90, 0.78)
    go = bpy.data.objects.new("graze_tv", gr)
    bpy.context.collection.objects.link(go)
    go.location = (5.5, -0.9, 2.30)
    dv = Vector((0.0, 1.0, -0.35)).normalized()
    go.rotation_euler = dv.to_track_quat("-Z", "Y").to_euler()


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
    scene.view_settings.exposure = 0.1
    scene.view_settings.look = "AgX - Medium High Contrast"
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
