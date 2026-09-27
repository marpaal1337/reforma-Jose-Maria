#!/usr/bin/env python3
"""
Hornea la luz de Cycles de renders/escena.blend para el visor web y exporta los
recursos del modo Realista de render3d.html.

Se ejecuta con Blender sobre la escena ya generada (generar_blender.py):

    blender -b renders/escena.blend -noaudio -P scripts/hornear_visor.py -- \
        [--muestras 256] [--res 4096] [--rapido]

Salidas en data/visor/ (las lee scripts/generar_visor3d.py):
  interior.glb      interior completo: UV de material (TEXCOORD_0) y de lightmap
                    (TEXCOORD_1); `extras.lm` = atlas; texturas WebP de 1k
  lm_a.jpg, lm_b.jpg  lightmaps: luz difusa de Cycles (directa + indirecta, sin
                    color) dividida por K y en sRGB -> albedo × lightmap × K
  suelo_cerca.jpg, suelo_lejos.jpg  calles, marcas, zonas verdes y sombras
                    horneadas (radiancia / K)
  cielo.jpg         cielo Nishita equirectangular (u=0,5 en +X de Three.js)
  reflejo.jpg       panorama del salón para los reflejos del interior
  arbol_lado.webp, arbol_planta.webp  impostores de la jacaranda
  visor.json        K de cada imagen, sol, luz de cielo para las fachadas,
                    árboles y rectángulos del suelo

Valores por defecto anti-manchas (cocina/dormitorio, 2026-09-27):
  rápido (--rapido): 32 muestras, atlas de 1024. Solo para iterar: el desruido
                    OIDN a 32 muestras deja manchas suaves en superficies
                    lisas (pared, encimera); el completo las elimina.
  completo: 128 muestras, atlas de 4096 (antes 2048: densidad insuficiente
                    para los muros grandes del dormitorio y la isla de cocina).
  gutter entre islas MARGEN_ISLAS_PX = 16 px > dilatado del horneado
                    MARGEN_BAKE_PX = 8 px (EXTEND), para que el horneado no
                    mezcle islas vecinas (bleeding -> manchas oscuras).
  despliegue smart UV a ANGULO_SMART = 60° con separación inicial
                    ISLA_SMART = 0,02; tras empaquetar se verifica el solape
                    con select_overlap y, si supera UMBRAL_SOLAPE loops, se
                    re-despliega con menos islas (75°) y margen ×1,5.
  NO_HORNEAR_MAT excluye del difuso los emisores (led, lampara_pantalla),
                    los cristales (cristal, vidrio_acido), la pantalla y el
                    espejo, más la cortina (visillo translúcido: su transmisión
                    contamina el pase difuso). Los marcos de aluminio y los
                    metales oscuros SÍ se hornean (aportan oclusión del hueco).
  desruido OIDN con prefilter ACCURATE y bounces mínimos asegurados
                    (difuso 4, brillo 4, transmisión/transparencia 8,
                    heredados de generar_blender.py).

Coordenadas: Blender (x, y, z) -> Three.js (x, z, -y).
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
ENT = json.loads((ROOT / "data" / "entorno.json").read_text(encoding="utf-8"))

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
# --salida <dir>: hornea a otra carpeta (pruebas) sin tocar data/visor
OUT = Path(ARGS[ARGS.index("--salida") + 1]).resolve() if "--salida" in ARGS else ROOT / "data" / "visor"


def arg(nombre, defecto):
    if nombre in ARGS:
        return type(defecto)(ARGS[ARGS.index(nombre) + 1])
    return defecto


RAPIDO = "--rapido" in ARGS
MUESTRAS = arg("--muestras", 32 if RAPIDO else 128)
RES = arg("--res", 1024 if RAPIDO else 4096)
RES_SUELO = 1024 if RAPIDO else 4096
TEX_MAX = 1024           # lado máximo de las texturas PBR en el visor

# ── atlas de lightmap: el gutter entre islas debe superar al dilatado del
# horneado (MARGEN_BAKE_PX con EXTEND), o el horneado mezcla islas vecinas
# (bleeding -> manchas oscuras en isla/encimera y paredes).
MARGEN_BAKE_PX = 8       # sc.render.bake.margin en hornear()
MARGEN_ISLAS_PX = 16     # gutter mínimo entre islas en el pack (en píxeles)
ANGULO_SMART = 60.0      # smart UV project: corta en aristas > 60°
ISLA_SMART = 0.02        # separación inicial entre islas (fracción UV)
UMBRAL_SOLAPE = 8        # loops UV solapados tolerados tras select_overlap

ARQ = ("suelo", "pav_", "techo", "muro_", "rodapie_", "dintel_", "antepecho_",
       "marco_", "mont_", "pmarco_", "pdintel_", "ext_balcon", "ext_voladizo",
       "tv_panel", "tv_liston", "pilar")
# Sin aporte difuso útil: emisores (led, lampara_pantalla), cristales
# (cristal, vidrio_acido), pantalla, espejo y cortina (translúcida). El
# aluminio de los marcos y los metales oscuros sí se hornean (dan oclusión).
NO_HORNEAR_MAT = {"cristal", "vidrio_acido", "cortina", "led",
                  "lampara_pantalla", "pantalla", "espejo"}
EXTERIOR_EXPORT = ("ext_balcon", "ext_barandilla", "ext_voladizo", "ext_propio")


def t_log(msg, t0=[time.time()]):
    print(f"VISOR [{time.time() - t0[0]:7.1f}s] {msg}", flush=True)


def b2t(v):
    """Blender -> Three.js."""
    return [round(v[0], 3), round(v[2], 3), round(-v[1], 3)]


# ── selección de objetos ────────────────────────────────────────────────────

def objetos_interior():
    sal = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render:
            continue
        n = ob.name
        if n.startswith("portal_") or n.startswith("ext_corte"):
            continue
        if n.startswith("ext_") and not n.startswith(EXTERIOR_EXPORT):
            continue
        sal.append(ob)
    return sal


def mat0(ob):
    return ob.data.materials[0].name if ob.data.materials and ob.data.materials[0] else ""


def hornear_si(ob):
    # modelos CC0 (plantas, jarrones): los ilumina el entorno en el visor
    if ob.name.startswith(("ext_propio", "asset_")):
        return False
    mats = {m.name for m in ob.data.materials if m}
    return not (mats and mats <= NO_HORNEAR_MAT)


def seleccionar(obs, activo=None):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = activo or (obs[0] if obs else None)


# ── UV ──────────────────────────────────────────────────────────────────────

def uv_caja(me):
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        n = poly.normal
        eje = max(range(3), key=lambda i: abs(n[i]))
        a, b = (1, 2) if eje == 0 else ((0, 2) if eje == 1 else (0, 1))
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (v[a], v[b])


def orientar_normales(ob):
    """Normales coherentes: el generador crea polígonos en el orden del plano
    (a veces horario) y Cycles lo disimula en el render, pero al hornear se
    evalúa el lado de la normal y en el visor esas caras se descartan.
    Volúmenes hacia fuera, suelos hacia arriba y techo hacia abajo."""
    import bmesh
    if ob.name.startswith("asset_"):
        return
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    if ob.name == "techo":
        for f in bm.faces:
            if f.normal.z > 0:
                f.normal_flip()
    elif ob.name == "suelo" or ob.name.startswith("pav_"):
        for f in bm.faces:
            if f.normal.z < 0:
                f.normal_flip()
    else:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


def preparar_uv(obs):
    """Aplica modificadores, orienta normales, garantiza UVMap (material) y
    crea LightMap."""
    seleccionar(obs)
    bpy.ops.object.convert(target="MESH")
    for ob in obs:
        me = ob.data
        if me.users > 1:
            ob.data = me = me.copy()
        orientar_normales(ob)
        if not me.uv_layers:
            uv_caja(me)
        while len(me.uv_layers) > 1:
            me.uv_layers.remove(me.uv_layers[-1])
        me.uv_layers[0].name = "UVMap"
        me.uv_layers[0].active_render = True
        lm = me.uv_layers.new(name="LightMap")
        me.uv_layers.active = lm


def _desplegar(angulo_deg, isla):
    bpy.ops.uv.smart_project(angle_limit=math.radians(angulo_deg),
                              island_margin=isla, area_weight=0.0,
                              correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()


def _empaquetar_islas(margen):
    bpy.ops.uv.pack_islands(rotate=True, margin_method="FRACTION",
                            margin=margen, shape_method="CONVEX")


def _loops_solapados(obs):
    """Loops UV marcados por select_overlap (llamar en modo OBJECT)."""
    total = 0
    for ob in obs:
        uv = ob.data.uv_layers.get("LightMap")
        if uv is not None:
            total += sum(1 for d in uv.data if d.select)
    return total


def empaquetar(obs, margen):
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    seleccionar(obs)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    _desplegar(ANGULO_SMART, ISLA_SMART)
    _empaquetar_islas(margen)
    # verifica solape (bevels y curvas pueden plegarse sobre sí mismos):
    # si hay islas superpuestas, re-despliega con menos islas y más gutter
    bpy.ops.uv.select_overlap()
    bpy.ops.object.mode_set(mode="OBJECT")
    n = _loops_solapados(obs)
    if n > UMBRAL_SOLAPE:
        t_log(f"atlas: {n} loops UV solapados, re-despliegue con menos islas…")
        seleccionar(obs)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        _desplegar(75.0, ISLA_SMART + 0.01)
        _empaquetar_islas(margen * 1.5)
        bpy.ops.object.mode_set(mode="OBJECT")


# ── horneado ────────────────────────────────────────────────────────────────

def nodo_objetivo(mat, img):
    nt = mat.node_tree
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = img
    n.name = n.label = "__hornear__"
    nt.nodes.active = n
    return n


def limpiar_objetivos():
    for mat in bpy.data.materials:
        if mat.node_tree:
            for n in [n for n in mat.node_tree.nodes if n.name.startswith("__hornear__")]:
                mat.node_tree.nodes.remove(n)


def hornear(obs, img, tipo, filtro=None, activo=None, sel_a_act=False, **kw):
    limpiar_objetivos()
    destino = [activo] if sel_a_act else obs
    for ob in destino:
        for mat in ob.data.materials:
            if mat and mat.use_nodes:
                nodo_objetivo(mat, img)
    seleccionar(obs + ([activo] if activo else []), activo)
    sc = bpy.context.scene
    sc.render.bake.margin = MARGEN_BAKE_PX
    sc.render.bake.margin_type = "EXTEND"
    sc.render.bake.use_clear = True
    opts = dict(type=tipo, margin=MARGEN_BAKE_PX, use_clear=True,
                use_selected_to_active=sel_a_act)
    if filtro is not None:
        opts["pass_filter"] = filtro
    opts.update(kw)
    bpy.ops.object.bake(**opts)
    limpiar_objetivos()


def pixeles(img):
    a = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


_DN = {}


def desruido(img):
    """OIDN sobre una imagen float mediante el compositor de una escena vacía."""
    w, h = img.size
    sc = _DN.get("sc")
    if sc is None:
        sc = bpy.data.scenes.new("desruido")
        sc.render.engine = "BLENDER_WORKBENCH"
        cam = bpy.data.objects.new("cam_dn", bpy.data.cameras.new("cam_dn"))
        sc.collection.objects.link(cam)
        sc.camera = cam
        sc.use_nodes = True
        sc.view_settings.view_transform = "Standard"
        sc.render.image_settings.file_format = "OPEN_EXR"
        sc.render.image_settings.color_depth = "32"
        _DN["sc"] = sc
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    nt = sc.node_tree
    nt.nodes.clear()
    ni = nt.nodes.new("CompositorNodeImage")
    ni.image = img
    dn = nt.nodes.new("CompositorNodeDenoise")
    dn.use_hdr = True
    dn.prefilter = "ACCURATE"   # menos manchas en superficies lisas que NONE
    co = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(ni.outputs["Image"], dn.inputs["Image"])
    nt.links.new(dn.outputs["Image"], co.inputs["Image"])
    ruta = OUT / f"_dn_{img.name}.exr"
    sc.render.filepath = str(ruta)
    with bpy.context.temp_override(scene=sc):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    res = bpy.data.images.load(str(ruta), check_existing=False)
    arr = pixeles(res)
    bpy.data.images.remove(res)
    ruta.unlink(missing_ok=True)
    return arr


def srgb(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def guardar_jpg(rgb, ruta, K, calidad=90):
    """rgb lineal (h, w, 3) -> JPEG sRGB de rgb/K (volteado: fila 0 abajo)."""
    h, w = rgb.shape[:2]
    enc = srgb(rgb / K)
    img = bpy.data.images.new(ruta.stem, w, h, alpha=False)
    buf = np.ones((h, w, 4), dtype=np.float32)
    buf[..., :3] = enc
    img.pixels.foreach_set(buf.ravel())
    img.filepath_raw = str(ruta)
    img.file_format = "JPEG"
    try:
        img.save(quality=calidad)
    except TypeError:
        img.save()
    bpy.data.images.remove(img)


def escala_K(rgb, mascara=None, pct=99.5):
    m = rgb.max(axis=2)
    if mascara is not None:
        m = m[mascara]
    m = m[m > 1e-5]
    return float(max(np.percentile(m, pct), 1e-3)) if m.size else 1.0


# ── materiales para glTF ────────────────────────────────────────────────────

SIMPLES = {  # materiales sin equivalente glTF: color base, rugosidad, alfa
    "cristal": ((0.90, 0.95, 0.93), 0.02, 0.12),
    "cortina": ((0.96, 0.95, 0.92), 0.6, 0.55),
    "vidrio_acido": ((0.92, 0.94, 0.93), 0.45, 0.6),
    "lienzo": ((0.86, 0.83, 0.77), 0.9, 1.0),
    # pantalla de la lámpara de pie: el Mix+Translucent de Blender no viaja a
    # glTF; se simplifica a base ámbar y se le devuelve el glow por emisión
    "lampara_pantalla": ((0.82, 0.63, 0.42), 0.9, 1.0),
}


def preparar_materiales(obs):
    usados = {m for ob in obs for m in ob.data.materials if m}
    for mat in usados:
        nt = mat.node_tree
        if mat.name in SIMPLES or mat.name.startswith("ext_") or mat.name == "revoco_fachada":
            col, rough, alfa = SIMPLES.get(mat.name, ((0.60, 0.38, 0.27), 0.9, 1.0))
            nt.nodes.clear()
            b = nt.nodes.new("ShaderNodeBsdfPrincipled")
            o = nt.nodes.new("ShaderNodeOutputMaterial")
            nt.links.new(b.outputs[0], o.inputs["Surface"])
            b.inputs["Base Color"].default_value = (*col, 1.0)
            b.inputs["Roughness"].default_value = rough
            b.inputs["Alpha"].default_value = alfa
            if mat.name == "lampara_pantalla" and "Emission Color" in b.inputs:
                b.inputs["Emission Color"].default_value = (1.0, 0.66, 0.34, 1.0)
                b.inputs["Emission Strength"].default_value = 0.65
            if alfa < 1.0:
                mat.blend_method = "BLEND"
            continue
        if not nt:
            continue
        # Hue/Saturation entre la textura y el color base: se hornea en la imagen
        for hs in [n for n in nt.nodes if n.type == "HUE_SAT"]:
            src = hs.inputs["Color"].links[0].from_node if hs.inputs["Color"].links else None
            if not (src and src.type == "TEX_IMAGE" and src.image):
                continue
            sat = hs.inputs["Saturation"].default_value
            val = hs.inputs["Value"].default_value
            nueva = src.image.copy()
            nueva.name = f"{src.image.name}_{mat.name}"
            if max(nueva.size) > TEX_MAX:
                nueva.scale(TEX_MAX, TEX_MAX)
            p = pixeles(nueva)
            gris = (p[..., :3] @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32))[..., None]
            p[..., :3] = np.clip((gris + (p[..., :3] - gris) * sat) * val, 0, 1)
            nueva.pixels.foreach_set(p.ravel())
            nueva.file_format = "JPEG"
            src.image = nueva
            destino = hs.outputs["Color"].links[0].to_socket if hs.outputs["Color"].links else None
            nt.nodes.remove(hs)
            if destino:
                nt.links.new(src.outputs["Color"], destino)
        # rugosidad/metalizado con textura: su valor medio (el exportador tendría
        # que reempaquetar canales y falla con las imágenes de los modelos CC0)
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            for nombre in ("Roughness", "Metallic"):
                sk = bsdf.inputs[nombre]
                if not sk.links:
                    continue
                src = sk.links[0].from_node
                img = next((n.image for n in [src] + [l.from_node for i in src.inputs
                            for l in i.links] if n.type == "TEX_IMAGE" and n.image), None)
                media = 0.5 if nombre == "Roughness" else 0.0
                if img and img.size[0] > 0:
                    px = pixeles(img)
                    media = float(px[..., 1 if nombre == "Roughness" else 2].mean()) \
                        if img.name.endswith(("arm", "arm.jpg")) else float(px[..., 0].mean())
                nt.links.remove(sk.links[0])
                sk.default_value = min(max(media, 0.0), 1.0)
        # nodos procedurales sueltos (ruido de relieve, rampas): fuera
        for n in list(nt.nodes):
            if n.type in ("TEX_NOISE", "BUMP", "VALTORGB", "TEX_BRICK"):
                nt.nodes.remove(n)
    for img in bpy.data.images:
        if img.source == "FILE" and max(img.size) > TEX_MAX:
            img.scale(min(TEX_MAX, img.size[0]), min(TEX_MAX, img.size[1]))


# ── cielo, reflejos, árboles, suelo ─────────────────────────────────────────

def escena_aux(nombre, res, film_transp=False, muestras=32):
    sc = bpy.data.scenes.new(nombre)
    sc.world = bpy.context.scene.world
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = muestras
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = film_transp
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    return sc


def render_a(sc, ruta):
    sc.render.filepath = str(ruta)
    with bpy.context.temp_override(scene=sc):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    img = bpy.data.images.load(str(ruta), check_existing=False)
    arr = pixeles(img)
    bpy.data.images.remove(img)
    ruta.unlink(missing_ok=True)
    return arr


def cam_equirect(sc, pos):
    cd = bpy.data.cameras.new("eq")
    cd.type = "PANO"
    cd.panorama_type = "EQUIRECTANGULAR"
    cd.clip_end = 5000
    co = bpy.data.objects.new("eq", cd)
    sc.collection.objects.link(co)
    co.location = pos
    co.rotation_euler = (math.pi / 2, 0.0, -math.pi / 2)   # mira a +X, arriba +Z
    sc.camera = co
    return co


def hornear_cielo(info):
    sc = escena_aux("cielo", (2048, 1024) if not RAPIDO else (1024, 512), muestras=16)
    cam_equirect(sc, (0, 0, 0))
    sky = render_a(sc, OUT / "_cielo.exr")[..., :3]
    h = sky.shape[0]
    # bajo el horizonte: el color del horizonte (neblina) en vez del suelo Nishita
    fila_h = h // 2
    horiz = sky[fila_h + 2:fila_h + 6].mean(axis=(0, 1))
    sky[:fila_h] = horiz
    K = escala_K(sky, pct=99.9)
    guardar_jpg(sky, OUT / "cielo.jpg", K, 92)
    # irradiancia del cielo sobre una superficie horizontal (hacia arriba)
    th = (np.arange(h) + 0.5) / h * math.pi - math.pi / 2        # elevación
    arriba = th > 0
    lum = sky @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    w = np.cos(th) * (2 * math.pi / sky.shape[1]) * (math.pi / h)
    E_up = float((lum[arriba] * (np.sin(th[arriba]) * w[arriba])[:, None]).sum())
    col = (sky[arriba] * (np.sin(th[arriba]) * w[arriba])[:, None, None]).sum(axis=(0, 1))
    info["cielo"] = {"K": K, "E_up": E_up,
                     "color": [round(float(c / max(col.max(), 1e-6)), 4) for c in col],
                     "horizonte": [round(float(c), 5) for c in horiz]}
    bpy.data.scenes.remove(sc)
    t_log(f"cielo: K={K:.3f} E_up={E_up:.3f}")


def hornear_reflejo(info):
    """Panorama del salón (escena completa) para los reflejos del interior."""
    sc0 = bpy.context.scene
    co = cam_equirect(sc0, (4.6, -1.6, 1.3))
    res0 = (sc0.render.resolution_x, sc0.render.resolution_y, sc0.cycles.samples,
            sc0.view_settings.view_transform, sc0.view_settings.exposure,
            sc0.view_settings.look, sc0.render.image_settings.file_format,
            sc0.use_nodes)
    sc0.render.resolution_x, sc0.render.resolution_y = (1024, 512)
    sc0.cycles.samples = 64 if not RAPIDO else 16
    sc0.view_settings.view_transform = "Standard"
    sc0.view_settings.look = "None"
    sc0.view_settings.exposure = 0.0
    sc0.use_nodes = False
    sc0.render.image_settings.file_format = "OPEN_EXR"
    sc0.render.image_settings.color_depth = "32"
    cam_prev = sc0.camera
    sc0.camera = co
    arr = render_a(sc0, OUT / "_reflejo.exr")[..., :3]
    sc0.camera = cam_prev
    (sc0.render.resolution_x, sc0.render.resolution_y, sc0.cycles.samples,
     sc0.view_settings.view_transform, sc0.view_settings.exposure,
     sc0.view_settings.look, sc0.render.image_settings.file_format,
     sc0.use_nodes) = res0
    bpy.data.objects.remove(co)
    K = escala_K(arr, pct=99.5)
    guardar_jpg(arr, OUT / "reflejo.jpg", K, 88)
    info["reflejo"] = {"K": K}
    t_log(f"reflejo interior: K={K:.3f}")


def hornear_arbol(info):
    col = bpy.data.collections.get("ext_arbol")
    if not col:
        info["arbol"] = None
        return
    sc = escena_aux("arbol", (1024, 1024), film_transp=True, muestras=32 if RAPIDO else 96)
    inst = bpy.data.objects.new("arbol_i", None)
    inst.instance_type = "COLLECTION"
    inst.instance_collection = col
    sc.collection.objects.link(inst)
    sol = bpy.data.objects["sol"]
    sol2 = bpy.data.objects.new("sol2", sol.data)
    sol2.matrix_world = sol.matrix_world.copy()
    sc.collection.objects.link(sol2)
    ws = [o.matrix_world @ Vector(c) for o in col.all_objects if o.type == "MESH"
          for c in o.bound_box]
    x0, x1 = min(w.x for w in ws), max(w.x for w in ws)
    y0, y1 = min(w.y for w in ws), max(w.y for w in ws)
    z0, z1 = min(w.z for w in ws), max(w.z for w in ws)
    lado = max(x1 - x0, y1 - y0, z1 - z0) * 1.02
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cd = bpy.data.cameras.new("orto")
    cd.type = "ORTHO"
    cd.ortho_scale = lado
    cd.clip_end = 1000
    co = bpy.data.objects.new("orto", cd)
    sc.collection.objects.link(co)
    sc.camera = co
    sc.render.image_settings.file_format = "WEBP"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.quality = 90
    # lateral: mirando hacia el sol (se ve la cara iluminada)
    sd = sol.matrix_world.to_quaternion() @ Vector((0, 0, 1))
    hdir = Vector((sd.x, sd.y, 0)).normalized()
    co.location = Vector((cx, cy, (z0 + z1) / 2)) + hdir * lado * 2
    co.rotation_euler = (-hdir).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = str(OUT / "arbol_lado.webp")
    with bpy.context.temp_override(scene=sc):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    # planta
    co.location = (cx, cy, z1 + lado)
    co.rotation_euler = (0.0, 0.0, 0.0)
    sc.render.filepath = str(OUT / "arbol_planta.webp")
    with bpy.context.temp_override(scene=sc):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    info["arbol"] = {"lado": round(lado, 3), "alto": round(z1 - z0, 3),
                     "ancho": round(max(x1 - x0, y1 - y0), 3),
                     "z_base": round(z0 - ((z0 + z1) / 2 - lado / 2), 3)}
    bpy.data.scenes.remove(sc)
    arboles = []
    for ob in bpy.data.objects:
        if ob.name.startswith("ext_arbol_i") and ob.instance_collection == col:
            s = ob.scale
            arboles.append([round(ob.location.x, 2), round(-ob.location.y, 2),
                            round(s.z * (z1 - z0), 2), round(s.x * (x1 - x0 + y1 - y0) / 2, 2),
                            round(ob.rotation_euler.z, 2)])
    info["arboles"] = arboles
    t_log(f"árboles: impostores + {len(arboles)} posiciones")


def hornear_suelo(info):
    """Suelo urbano (acera, calzadas con marcas, bici, verdes) con sus sombras,
    horneado en dos planos: cerca (160 m) y lejos (1000 m)."""
    fuentes = [o for o in bpy.data.objects if o.name in
               ("ext_suelo", "ext_calzada", "ext_bici", "ext_verdes")]
    suelo_z = min(v.co.z for v in bpy.data.objects["ext_suelo"].data.vertices)
    info["suelo"] = {"y": round(suelo_z, 3)}
    sc = bpy.context.scene
    muestras0 = sc.cycles.samples
    sc.cycles.samples = 16 if RAPIDO else 64
    for nombre, (cx, cy, lado, res) in (("cerca", (20.0, 0.0, 160.0, RES_SUELO)),
                                         ("lejos", (0.0, 0.0, 1000.0, RES_SUELO // 2))):
        bpy.ops.mesh.primitive_plane_add(size=lado, location=(cx, cy, suelo_z + 0.25))
        pl = bpy.context.active_object
        pl.name = f"hb_suelo_{nombre}"
        for vis in ("visible_camera", "visible_diffuse", "visible_glossy",
                    "visible_transmission", "visible_volume_scatter", "visible_shadow"):
            setattr(pl, vis, False)
        mat = bpy.data.materials.new(f"hb_{nombre}")
        mat.use_nodes = True
        pl.data.materials.append(mat)
        img = bpy.data.images.new(f"suelo_{nombre}", res, res, alpha=False, float_buffer=True)
        hornear(fuentes, img, "COMBINED", activo=pl, sel_a_act=True,
                cage_extrusion=0.5, max_ray_distance=1.0)
        arr = desruido(img)[..., :3]
        K = escala_K(arr, pct=99.7)
        guardar_jpg(arr, OUT / f"suelo_{nombre}.jpg", K, 86)
        # Three.js: x = X, z = -Y; la imagen tiene v hacia +Y de Blender
        info["suelo"][nombre] = {"K": K, "rect": [cx - lado / 2, -(cy + lado / 2),
                                                  cx + lado / 2, -(cy - lado / 2)]}
        bpy.data.objects.remove(pl)
        bpy.data.images.remove(img)
        t_log(f"suelo {nombre}: {res}px K={K:.3f}")
    sc.cycles.samples = muestras0


# ── principal ───────────────────────────────────────────────────────────────

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = MUESTRAS
    # rebotes mínimos (los de generar_blender.py): que el rápido y el completo
    # difieran solo en ruido y resolución, no en cantidad de luz indirecta
    sc.cycles.diffuse_bounces = max(sc.cycles.diffuse_bounces, 4)
    sc.cycles.glossy_bounces = max(sc.cycles.glossy_bounces, 4)
    sc.cycles.transmission_bounces = max(sc.cycles.transmission_bounces, 8)
    sc.cycles.transparent_max_bounces = max(sc.cycles.transparent_max_bounces, 8)
    info = {"generado": time.strftime("%Y-%m-%d %H:%M"), "muestras": MUESTRAS,
            "res": RES, "exposicion": sc.view_settings.exposure}
    sol = bpy.data.objects["sol"]
    hacia_sol = sol.matrix_world.to_quaternion() @ Vector((0, 0, 1))
    info["sol"] = {"dir": b2t(hacia_sol), "E": sol.data.energy,
                   "color": list(sol.data.color)}

    hornear_cielo(info)
    hornear_reflejo(info)
    hornear_arbol(info)
    hornear_suelo(info)

    # las jacarandas (22 m más abajo) no cambian la luz del piso y encarecen
    # cada rayo: fuera para hornear el interior (el suelo ya lleva sus sombras)
    for ob in bpy.data.objects:
        if ob.name.startswith("ext_arbol_i"):
            ob.hide_render = True
    obs = objetos_interior()
    preparar_uv(obs)
    grupos = {"a": [o for o in obs if o.name.startswith(ARQ) and hornear_si(o)],
              "b": [o for o in obs if not o.name.startswith(ARQ) and hornear_si(o)]}
    info["K"] = {}
    for g, gobs in grupos.items():
        t_log(f"atlas {g}: {len(gobs)} objetos, UV…")
        empaquetar(gobs, MARGEN_ISLAS_PX / RES)
        img = bpy.data.images.new(f"lm_{g}", RES, RES, alpha=False, float_buffer=True)
        t_log(f"atlas {g}: horneando {RES}px × {MUESTRAS} muestras…")
        hornear(gobs, img, "DIFFUSE", filtro={"DIRECT", "INDIRECT"})
        arr = desruido(img)[..., :3]
        K = escala_K(arr, pct=99.7)
        guardar_jpg(arr, OUT / f"lm_{g}.jpg", K, 90)
        info["K"][g] = K
        for ob in gobs:
            ob["lm"] = g
        bpy.data.images.remove(img)
        t_log(f"atlas {g}: K={K:.3f}")

    # exportación: solo el interior (+ fachada propia y balcones); las plantas
    # CC0 se diezman (sus hojas pesaban >10 MB en el GLB)
    for ob in obs:
        if ob.name.startswith("asset_") and len(ob.data.polygons) > 3000:
            md = ob.modifiers.new("diezmar", "DECIMATE")
            md.ratio = 0.15
    preparar_materiales(obs)
    seleccionar(obs)
    ruta = OUT / "interior.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(ruta), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_cameras=False,
        export_lights=False, export_texcoords=True, export_normals=True,
        export_extras=True, export_materials="EXPORT",
        export_image_format="WEBP", export_image_quality=85)
    info["glb_kb"] = ruta.stat().st_size // 1024
    (OUT / "visor.json").write_text(json.dumps(info, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
    t_log(f"GLB {info['glb_kb']} KB, {len(obs)} mallas -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
