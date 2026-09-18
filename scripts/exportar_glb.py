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
    "roble": ("roble.jpg", 0.42, 0.0, 1.0),
    "piedra_negra": ("piedra_negra.jpg", 0.20, 0.0, 1.0),
    "tejido": ("tejido.jpg", 0.95, 0.0, 1.0),
    "tejido_claro": ("tejido_claro.jpg", 0.95, 0.0, 1.0),
    "lino": ("lino.jpg", 0.95, 0.0, 1.0),
}
COLORES = {
    "negro_mate": (0.02, 0.02, 0.02, 0.6),
    "pantalla": (0.012, 0.012, 0.014, 0.08),
    "planta": (0.07, 0.16, 0.055, 0.7),
    "maceta": (0.85, 0.84, 0.80, 0.7),
    "cobre": (0.72, 0.43, 0.20, 0.28),
    "aluminio": (0.12, 0.115, 0.11, 0.35),
    "espejo": (0.95, 0.95, 0.95, 0.03),
    "cristal": (1.0, 1.0, 1.0, 0.02),
}
METALES = {"cobre", "aluminio", "espejo"}
TRANSPARENTES = {"cristal"}
ESCALA_TEX = {"marmol": 1.5, "azulejo": 1.5, "travertino": 1.2}


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


def aplicar_acabado(mat: bpy.types.Material) -> None:
    bsdf = nodos_simples(mat)
    nombre = mat.name
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
    else:
        rgb, rough = (0.6, 0.6, 0.6), 0.6
        if nombre in COLORES:
            e = COLORES[nombre]
            rgb, rough = e[:3], e[3]
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = 1.0 if nombre in METALES else 0.0
        if nombre in TRANSPARENTES:
            bsdf.inputs["Alpha"].default_value = 0.18
            mat.blend_method = "BLEND"


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "renders" / "escena.blend"))

    quitados = []
    for ob in list(bpy.data.objects):
        if ob.type in {"CAMERA", "LIGHT"} or ob.name.startswith("ext_"):
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
