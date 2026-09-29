#!/usr/bin/env python3
"""
Exporta el mobiliario de renders/escena.blend a data/mobiliario.glb para el
visor web (render3d.html). Aplica los modificadores de bevel, añade coordenadas
UV por proyección de caja (1 textura/m) y sustituye los materiales procedurales
por texturas de imagen de data/texturas/ (que sí viajan en glTF).

Se ejecuta con Blender (no con python3):

    source /tmp/opencode/blender_env.sh
    "$BLENDER" -b renders/escena.blend -noaudio -P scripts/exportar_glb.py

Salida: data/mobiliario.glb
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "mobiliario.glb"
TEX = ROOT / "data" / "texturas"

# material -> (textura, roughness, metallic, alpha)
ACABADOS = {
    "muro": ("muro.jpg", 0.92, 0.0, 1.0),
    "techo": ("techo.jpg", 0.95, 0.0, 1.0),
    "suelo_madera": ("suelo_madera.jpg", 0.45, 0.0, 1.0),
    "terraza": ("terraza.jpg", 0.62, 0.0, 1.0),
    "terraza_madera": ("terraza.jpg", 0.62, 0.0, 1.0),
    "marmol": ("marmol.jpg", 0.18, 0.0, 1.0),
    "azulejo": ("azulejo.jpg", 0.22, 0.0, 1.0),
    "travertino": ("travertino.jpg", 0.55, 0.0, 1.0),
    "travertino_porc": ("travertino_porc.jpg", 0.35, 0.0, 1.0),
    "roble": ("roble.jpg", 0.42, 0.0, 1.0),
    "roble_h": ("roble.jpg", 0.42, 0.0, 1.0),
    "roble_mel": ("roble_mel.jpg", 0.45, 0.0, 1.0),
    "cerezo": ("cerezo.jpg", 0.30, 0.0, 1.0),
    "silestone": ("silestone.jpg", 0.35, 0.0, 1.0),
    "dekton": ("dekton.jpg", 0.30, 0.0, 1.0),
    "hormigon_picado": ("hormigon.jpg", 0.70, 0.0, 1.0),
    "alfombra": ("tejido_claro.jpg", 0.95, 0.0, 1.0),
    "piedra_negra": ("piedra_negra.jpg", 0.20, 0.0, 1.0),
    "tejido": ("tejido.jpg", 0.95, 0.0, 1.0),
    "tejido_claro": ("tejido_claro.jpg", 0.95, 0.0, 1.0),
    "lino": ("lino.jpg", 0.95, 0.0, 1.0),
}
COLORES = {
    "negro_mate": (0.02, 0.02, 0.02, 0.6),
    "blanco_laca": (0.93, 0.93, 0.91, 0.35),
    "blanco_electro": (0.92, 0.92, 0.90, 0.15),
    "vidrio_acido": (0.92, 0.94, 0.93, 0.45),
    "pantalla": (0.012, 0.012, 0.014, 0.08),
    "planta": (0.07, 0.16, 0.055, 0.7),
    "maceta": (0.85, 0.84, 0.80, 0.7),
    "cobre": (0.76, 0.45, 0.32, 0.32),
    "aluminio": (0.030, 0.030, 0.032, 0.34),
    "espejo": (0.95, 0.95, 0.95, 0.03),
    "cristal": (1.0, 1.0, 1.0, 0.02),
    "metal_negro": (0.035, 0.035, 0.037, 0.42),
    "cromo": (0.86, 0.87, 0.89, 0.06),
    "porcelana": (0.92, 0.92, 0.91, 0.10),
    "fregadero": (0.025, 0.025, 0.028, 0.35),
    "bronce_barandilla": (0.09, 0.07, 0.055, 0.5),
    "cuero": (0.25, 0.11, 0.05, 0.5),
    "cortina": (0.96, 0.95, 0.92, 0.6),
    "lampara_pantalla": (0.82, 0.63, 0.42, 0.9),
    "lienzo": (0.88, 0.85, 0.79, 0.9),
    # melaminas y acabados lisos nuevos
    "grafito": (0.075, 0.075, 0.080, 0.45),
    "gris_osc": (0.12, 0.12, 0.12, 0.5),
    "resina": (0.90, 0.90, 0.89, 0.35),
    "pav_exterior": (0.64, 0.63, 0.61, 0.5),
    "revoco_fachada": (0.585, 0.365, 0.266, 0.88),
    # aproximaciones planas de las láminas procedurales (por si el .blend es
    # anterior a su generación; con imagen se conservan, ver _imagen_base)
    "lienzo_0": (0.72, 0.45, 0.30, 0.9),
    "lienzo_1": (0.55, 0.58, 0.42, 0.9),
    "lienzo_2": (0.42, 0.52, 0.58, 0.9),
    "colcha": (0.72, 0.50, 0.34, 0.95),
    "tierra": (0.045, 0.032, 0.022, 0.95),
}
METALES = {"cobre", "aluminio", "espejo", "metal_negro", "cromo",
           "bronce_barandilla", "laton"}
TRANSPARENTES = {"cristal": 0.18, "vidrio_acido": 0.55, "cortina": 0.5}
# escala de la proyección de caja = 1/tamaño de textura en metros
ESCALA_TEX = {
    "marmol": 1.5, "azulejo": 1.5, "travertino": 1.2,
    "travertino_porc": 1 / 1.2, "silestone": 1.0, "dekton": 1.0,
    "cerezo": 1 / 0.8, "roble_mel": 1 / 0.8, "hormigon_picado": 1 / 0.6,
}


def ensure_uv(me: bpy.types.Mesh, escala: float = 1.0) -> None:
    """Proyección de caja en coordenadas locales -> 1 tile por metro."""
    if me.uv_layers:
        return
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        n = poly.normal
        eje = max(range(3), key=lambda i: abs(n[i]))
        a, b = (1, 2) if eje == 0 else ((0, 2) if eje == 1 else (0, 1))
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (v[a] * escala, v[b] * escala)


def nodos_simples(mat: bpy.types.Material) -> None:
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return bsdf


def _imagen_base(mat: bpy.types.Material):
    """Imagen ya enlazada al Base Color del Principled (láminas lienzo_* y
    colcha procedurales de generar_blender.py): se conserva tal cual, que sí
    viaja en el GLB. Antes `aplicar_acabado` la borraba y dejaba un color
    plano casi blanco."""
    try:
        nodos = mat.node_tree.nodes
    except AttributeError:
        return None
    for n in nodos:
        if n.type != "TEX_IMAGE" or not n.image:
            continue
        try:
            enlaces = n.outputs["Color"].links
        except KeyError:
            continue
        for l in enlaces:
            if l.to_node.type == "BSDF_PRINCIPLED" \
                    and l.to_socket.name == "Base Color":
                return n.image
    return None


def aplicar_acabado(mat: bpy.types.Material) -> None:
    nombre = mat.name
    if nombre.startswith(("lienzo_", "colcha")):
        img = _imagen_base(mat)
        if img is not None:
            # lámina/colcha procedural empaquetada: Principled simple con su
            # imagen para que viaje en el GLB en vez de un plano blanco
            bsdf = nodos_simples(mat)
            tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tex.image = img
            mat.node_tree.links.new(tex.outputs["Color"],
                                    bsdf.inputs["Base Color"])
            bsdf.inputs["Roughness"].default_value = 0.9
            bsdf.inputs["Metallic"].default_value = 0.0
            return
    bsdf = nodos_simples(mat)
    if nombre in ACABADOS:
        fichero, rough, metal, alpha = ACABADOS[nombre]
        img = bpy.data.images.get(fichero)
        if img is None:
            img = bpy.data.images.load(str(TEX / fichero), check_existing=True)
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = img
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    elif nombre == "led":
        bsdf.inputs["Base Color"].default_value = (1.0, 0.93, 0.82, 1.0)
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.86, 0.66, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 2.0
        bsdf.inputs["Roughness"].default_value = 0.5
    elif nombre == "led_frio":
        bsdf.inputs["Base Color"].default_value = (0.94, 0.96, 1.0, 1.0)
        bsdf.inputs["Emission Color"].default_value = (0.88, 0.93, 1.0, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 2.0
        bsdf.inputs["Roughness"].default_value = 0.5
    elif nombre == "lampara_pantalla":
        # ámbar cálido con emisión suave (~3000 K): se conserva la emisión
        # (antes caía al plano casi blanco de COLORES y se quemaba)
        bsdf.inputs["Base Color"].default_value = (0.82, 0.63, 0.42, 1.0)
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.66, 0.34, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.65
        bsdf.inputs["Roughness"].default_value = 0.9
    else:
        rgb, rough = (0.6, 0.6, 0.6), 0.6
        if nombre in COLORES:
            e = COLORES[nombre]
            rgb, rough = e[:3], e[3]
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = 1.0 if nombre in METALES else 0.0
        if nombre in TRANSPARENTES:
            bsdf.inputs["Alpha"].default_value = TRANSPARENTES[nombre]
            mat.blend_method = "BLEND"


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "renders" / "escena.blend"))

    quitados = []
    for ob in list(bpy.data.objects):
        if ob.type in {"CAMERA", "LIGHT"} or ob.name.startswith("ext_") \
                or ob.name.startswith("portal_") or ob.name.startswith("asset_"):
            quitados.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)

    for mat in bpy.data.materials:
        aplicar_acabado(mat)

    n_mallas = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        escala = ESCALA_TEX.get(ob.data.materials[0].name, 1.0) if ob.data.materials else 1.0
        ensure_uv(ob.data, escala)
        n_mallas += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(OUT),
        export_format="GLB",
        export_apply=True,
        export_yup=True,
        export_cameras=False,
        export_lights=False,
        export_texcoords=True,
        export_materials="EXPORT",
    )
    print(f"GLB_OK {OUT.relative_to(ROOT)} {OUT.stat().st_size/1024:.0f} KB "
          f"({n_mallas} mallas, {len(quitados)} objetos quitados)")


if __name__ == "__main__":
    main()
