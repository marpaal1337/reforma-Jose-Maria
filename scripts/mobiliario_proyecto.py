#!/usr/bin/env python3
"""
Mobiliario y carpintería integrada de la reforma (PE/I.06-07, PE/A.03-04,
PE/I.01, PE/I.09 + renders de la disenadora).

Coordenadas del modelo en metros: x = este, z = sur. Alturas desde suelo.
Se invoca desde `generar_blender.build_mobiliario(m)`, que pasa el propio
módulo como `h` con los helpers box/cylinder/sphere/uv_retrato/
butaca_mariposa/planta_monstera/cargar_asset/mesh_from/poly_prism.

Prefijos por estancia (los usa revisar_mobiliario.py): d3_ dorm-3,
d2_ dorm-2 (incluye la biblioteca de cerezo trasladada del estudio),
dp_ dorm-principal, ves_ vestidor, b1_/b2_ baños, rec_ recibidor,
lav_ lavadero, tz_ balcón; cocina con coc_/isla/placa/taburete_/campana y el
salón sin prefijo especial (tv_, sofa_, mesa_, silla_, …). El estudio queda
sin amueblar (est_ sin uso).
"""

import math


# ── helpers locales ─────────────────────────────────────────────────────────

def _multi(h, cajas, name, mat, bevel=0.0):
    """Varias cajas alineadas en una sola malla (listones, pletinas…)."""
    verts, faces = [], []
    for x0, z0, x1, z1, h0, h1 in cajas:
        b = len(verts)
        verts += [(x0, -z0, h0), (x1, -z0, h0), (x1, -z1, h0), (x0, -z1, h0),
                  (x0, -z0, h1), (x1, -z0, h1), (x1, -z1, h1), (x0, -z1, h1)]
        faces += [[b, b + 3, b + 2, b + 1], [b + 4, b + 5, b + 6, b + 7],
                  [b, b + 1, b + 5, b + 4], [b + 1, b + 2, b + 6, b + 5],
                  [b + 2, b + 3, b + 7, b + 6], [b + 3, b, b + 4, b + 7]]
    return h.mesh_from(verts, faces, name, mat, bevel=bevel)


def _disco(h, name, mat, cx, cz, hc, r, grosor, normal, n=32):
    """Disco circular (espejo, puerta de electrodoméstico) centrado en
    (cx, cz, hc) con la normal indicada ('N', 'S', 'E', 'O')."""
    u, v, nv = {
        "E": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
        "O": ((0, 0, 1), (0, 1, 0), (-1, 0, 0)),
        "S": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
        "N": ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    }[normal]
    d = grosor / 2
    verts = []
    for s in (-1, 1):
        for i in range(n):
            a = 2 * math.pi * i / n
            ca, sa = math.cos(a), math.sin(a)
            verts.append((cx + s * d * nv[0] + r * (ca * u[0] + sa * v[0]),
                          -cz + s * d * nv[1] + r * (ca * u[1] + sa * v[1]),
                          hc + s * d * nv[2] + r * (ca * u[2] + sa * v[2])))
    faces = [list(range(n))[::-1], list(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, j + n, i + n])
    return h.mesh_from(verts, faces, name, mat, smooth=False)


def _orientar(verts, faces):
    """Caras hacia fuera: si el volumen con signo del sólido es negativo se
    invierte el orden de todas (no depende de Blender)."""
    vol = 0.0
    for f in faces:
        a = verts[f[0]]
        for i in range(1, len(f) - 1):
            b, c = verts[f[i]], verts[f[i + 1]]
            vol += (a[0] * (b[1] * c[2] - b[2] * c[1])
                    - a[1] * (b[0] * c[2] - b[2] * c[0])
                    + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return [f[::-1] for f in faces] if vol < 0 else faces


def _superelipse(a, b, e, n, frente=0, taper=0.0, e_atras=None):
    """Contorno |x/a|^e + |z/b|^e = 1 (n puntos, centro en el origen). Con
    `frente` = ±1 (sentido de z) el frente se estrecha `taper` (0-1) y la parte
    trasera usa el exponente `e_atras`, más recto, para apoyarse en el muro."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        ee = e_atras if (frente and e_atras and s * frente < 0) else e
        p = 2.0 / ee
        x = a * math.copysign(abs(c) ** p, c)
        z = b * math.copysign(abs(s) ** p, s)
        if frente and taper:
            x *= 1.0 - taper * (1.0 + s * frente) / 2.0
        pts.append((x, z))
    return pts


def _loft(h, name, mat, cx, cz, a, b, perfil, e=2.0, n=40, frente=0, taper=0.0,
          e_atras=None):
    """Sólido cerrado por anillos superelípticos centrados en (cx, cz).
    `perfil` = [(d, altura[, e[, s]])] de abajo arriba: los semiejes del anillo
    son (a·s − d, b·s − d); d ≥ semieje lo colapsa a un punto (cierra la pieza:
    d = 9 es el centro). Recorre el borde exterior, el canto y el interior.
    Los quiebros de más de ~35° del perfil se marcan como aristas vivas
    (sharp) para que el suavizado no emborrone cantos y bordes."""
    def dur(k):
        if k == 0 or k == len(perfil) - 1:
            return False
        (d0, h0), (d1, h1), (d2, h2) = ((min(max(perfil[j][0], -1.0), 1.0),
                                          perfil[j][1]) for j in (k - 1, k, k + 1))
        u, v = (d1 - d0, h1 - h0), (d2 - d1, h2 - h1)
        lu, lv = math.hypot(*u), math.hypot(*v)
        return lu > 0 and lv > 0 and (u[0] * v[0] + u[1] * v[1]) / (lu * lv) < 0.82

    verts, anillos, duros = [], [], []
    for k, r in enumerate(perfil):
        d, alt = r[0], r[1]
        ee = r[2] if len(r) > 2 and r[2] else e
        s = r[3] if len(r) > 3 else 1.0
        ra, rb = a * s - d, b * s - d
        if ra <= 1e-3 or rb <= 1e-3:
            verts.append((cx, -cz, alt))
            anillos.append(len(verts) - 1)            # punto (cierre)
            continue
        i0 = len(verts)
        verts += [(cx + x, -(cz + z), alt)
                  for x, z in _superelipse(ra, rb, ee, n, frente, taper, e_atras)]
        anillos.append((i0, n))
        if dur(k):
            duros.append(i0)
    faces = []
    for r0, r1 in zip(anillos, anillos[1:]):
        p0, p1 = isinstance(r0, int), isinstance(r1, int)
        if p0 and p1:
            continue
        for i in range(n):
            j = (i + 1) % n
            if p0:
                faces.append([r0, r1[0] + j, r1[0] + i])
            elif p1:
                faces.append([r0[0] + i, r0[0] + j, r1])
            else:
                faces.append([r0[0] + i, r0[0] + j, r1[0] + j, r1[0] + i])
    if not isinstance(anillos[0], int):
        faces.append([anillos[0][0] + i for i in range(n)][::-1])
    if not isinstance(anillos[-1], int):
        faces.append([anillos[-1][0] + i for i in range(n)])
    ob = h.mesh_from(verts, _orientar(verts, faces), name, mat, smooth=True)
    for ed in ob.data.edges:
        v0, v1 = ed.vertices
        if any(i0 <= v0 < i0 + n and i0 <= v1 < i0 + n for i0 in duros):
            ed.use_edge_sharp = True
    return ob


def _tubo(h, name, mat, pts, r, n=12):
    """Caño de radio r que sigue la polilínea pts = [(x, z, altura)], con
    marcos de transporte paralelo y tapas planas en los extremos."""
    P = [(x, -z, alt) for x, z, alt in pts]

    def norm(v):
        L = math.sqrt(sum(c * c for c in v)) or 1.0
        return tuple(c / L for c in v)

    def cruz(u, v):
        return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0])

    T = []
    for i in range(len(P)):
        a, b = P[max(i - 1, 0)], P[min(i + 1, len(P) - 1)]
        T.append(norm(tuple(b[k] - a[k] for k in range(3))))
    up = (0, 0, 1) if abs(T[0][2]) < 0.9 else (1, 0, 0)
    N = norm(cruz(T[0], up))
    verts, faces = [], []
    for i, p in enumerate(P):
        if i:
            dp = sum(N[k] * T[i][k] for k in range(3))
            N = norm(tuple(N[k] - T[i][k] * dp for k in range(3)))
        B = cruz(T[i], N)
        for j in range(n):
            t = 2 * math.pi * j / n
            c, s = r * math.cos(t), r * math.sin(t)
            verts.append(tuple(p[k] + c * N[k] + s * B[k] for k in range(3)))
    for i in range(len(P) - 1):
        for j in range(n):
            k = (j + 1) % n
            faces.append([i * n + j, i * n + k, (i + 1) * n + k, (i + 1) * n + j])
    faces.append(list(range(n))[::-1])
    faces.append([(len(P) - 1) * n + j for j in range(n)])
    return h.mesh_from(verts, _orientar(verts, faces), name, mat, smooth=True)


def _arco(xc, z, hc, R, a0, a1, k=12):
    """Puntos (x, z, altura) de un arco en el plano x–altura a z constante."""
    return [(xc + R * math.cos(math.radians(a0 + (a1 - a0) * i / k)), z,
             hc + R * math.sin(math.radians(a0 + (a1 - a0) * i / k)))
            for i in range(k + 1)]


def _silla(h, asiento, madera, x0, z0, x1, z1, respaldo, nombre):
    """Silla simple de 4 patas; el respaldo queda en el lado indicado."""
    h.box(x0, z0, x1, z1, 0.44, 0.475, f"{nombre}_asiento", asiento,
          bevel=0.035)
    t = 0.03
    if respaldo == "N":
        caja = (x0, z0, x1, z0 + t)
    elif respaldo == "S":
        caja = (x0, z1 - t, x1, z1)
    elif respaldo == "O":
        caja = (x0, z0, x0 + t, z1)
    else:
        caja = (x1 - t, z0, x1, z1)
    h.box(*caja, 0.475, 0.86, f"{nombre}_respaldo", asiento, bevel=0.015)
    for i, (lx, lz) in enumerate((
            (x0 + 0.045, z0 + 0.045), (x1 - 0.075, z0 + 0.045),
            (x0 + 0.045, z1 - 0.075), (x1 - 0.075, z1 - 0.075))):
        h.box(lx, lz, lx + 0.03, lz + 0.03, 0.0, 0.44,
              f"{nombre}_pie_{i}", madera, bevel=0.0)


# ── construcción ────────────────────────────────────────────────────────────

def construir(m, h):
    roble_mel = m["roble_mel"]
    roble = m["roble"]
    grafito = m["grafito"]
    gris_osc = m["gris_osc"]
    silestone = m["silestone"]
    dekton = m["dekton"]
    resina = m["resina"]
    travertino = m["travertino"]
    travertino_porc = m["travertino_porc"]
    cerezo = m["cerezo"]
    blanco_laca = m["blanco_laca"]
    laca = m["laca"]
    metal_negro = m["metal_negro"]
    cobre = m["cobre"]
    porcelana = m["porcelana"]
    cromo = m["cromo"]
    negro_mate = m["negro_mate"]
    cristal = m["cristal"]
    vidrio_acido = m["vidrio_acido"]
    espejo = m["espejo"]
    led = m["led"]
    led_frio = m["led_frio"]
    tejido = m["tejido"]
    tejido_claro = m["tejido_claro"]
    lino = m["lino"]
    cuero = m["cuero"]
    bronce = m["bronce_barandilla"]
    pantalla = m["pantalla"]

    # ══ COCINA (techo 2,30) ═════════════════════════════════════════════════
    # frente lineal contra el muro oeste (x = -1.53) y fondo 0.60 (frente -0.93)
    h.box(-1.53, -0.50, -0.98, 0.10, 0.0, 0.10, "coc_zocalo_frigo", gris_osc)
    h.box(-1.53, 0.10, -0.98, 2.35, 0.0, 0.10, "coc_zocalo_bajos", gris_osc)
    h.box(-1.53, -0.50, -0.93, 0.10, 0.10, 2.30, "coc_col_frigo", roble_mel,
          bevel=0.006)
    for k, (z0, z1) in enumerate(((-0.49, -0.20), (-0.19, 0.09))):
        h.box(-0.938, z0, -0.93, z1, 0.12, 2.28,
              f"coc_col_frigo_puerta_{k}", roble_mel, bevel=0.004)
    h.box(-0.928, -0.055, -0.918, -0.035, 0.95, 1.55,
          "coc_frigo_tirador", metal_negro, bevel=0.0)
    h.box(-1.53, 0.10, -0.93, 0.50, 0.10, 0.88, "coc_bajo_almacen",
          roble_mel, bevel=0.006)
    h.box(-1.53, 0.50, -0.93, 0.95, 0.10, 0.88, "coc_bajo_basuras",
          roble_mel, bevel=0.006)
    # bajo del fregadero: cuerpo hasta 0,66 y anillo alrededor de la cubeta
    h.box(-1.53, 0.95, -0.93, 1.75, 0.10, 0.66, "coc_bajo_fregadero",
          roble_mel, bevel=0.006)
    _multi(h, [(-1.53, 0.95, -1.41, 1.75, 0.66, 0.88),
               (-0.95, 0.95, -0.93, 1.75, 0.66, 0.88),
               (-1.41, 0.95, -0.95, 1.11, 0.66, 0.88),
               (-1.41, 1.72, -0.95, 1.75, 0.66, 0.88)],
           "coc_bajo_fregadero_alto", roble_mel)
    h.box(-1.53, 1.75, -0.93, 2.35, 0.10, 0.88, "coc_bajo_horno",
          roble_mel, bevel=0.006)
    # puertas de los bajos (ranura de uñero como línea oscura)
    for k, (z0, z1) in enumerate(((0.12, 0.48), (0.52, 0.93))):
        h.box(-0.938, z0, -0.93, z1, 0.12, 0.86,
              f"coc_bajo_almacen_puerta_{k}", roble_mel, bevel=0.004)
    h.box(-0.938, 0.52, -0.93, 0.93, 0.12, 0.86, "coc_bajo_basuras_puerta",
          roble_mel, bevel=0.004)
    for k, (z0, z1) in enumerate(((0.97, 1.34), (1.36, 1.73))):
        h.box(-0.938, z0, -0.93, z1, 0.12, 0.86,
              f"coc_bajo_fregadero_puerta_{k}", roble_mel, bevel=0.004)
    h.box(-0.928, 0.10, -0.924, 1.75, 0.855, 0.875, "coc_unero", gris_osc)
    # columna horno: lavavajillas panelado, horno y micro negros, armario alto
    h.box(-0.938, 1.78, -0.93, 2.32, 0.12, 0.88, "coc_lavavajillas",
          roble_mel, bevel=0.004)
    h.box(-0.948, 1.80, -0.938, 2.30, 0.90, 1.50, "coc_horno", negro_mate,
          bevel=0.006)
    h.box(-0.948, 1.80, -0.938, 2.30, 1.50, 1.95, "coc_micro", negro_mate,
          bevel=0.006)
    h.box(-1.53, 1.75, -0.93, 2.35, 1.95, 2.30, "coc_alto_horno", roble_mel,
          bevel=0.006)
    h.box(-0.938, 1.78, -0.93, 2.32, 1.97, 2.28, "coc_alto_horno_puerta",
          roble_mel, bevel=0.004)
    # encimera dekton (0,88-0,90) con hueco para el fregadero
    h.box(-1.53, 0.10, -0.91, 1.14, 0.88, 0.90, "coc_encimera_a", dekton,
          bevel=0.004)
    h.box(-1.53, 1.69, -0.91, 1.75, 0.88, 0.90, "coc_encimera_b", dekton,
          bevel=0.004)
    # franja trasera tras la cubeta: apoyo del grifo (antes flotaba en la cubeta)
    h.box(-1.53, 1.14, -1.38, 1.69, 0.88, 0.90, "coc_encimera_c", dekton,
          bevel=0.004)
    h.box(-1.53, 0.10, -0.91, 0.15, 0.83, 0.88, "coc_copete_n", dekton)
    h.box(-1.53, 1.70, -0.91, 1.75, 0.83, 0.88, "coc_copete_s", dekton)
    h.box(-0.97, 1.14, -0.91, 1.69, 0.88, 0.90, "coc_encimera_d", dekton,
          bevel=0.004)         # cubre la franja que dejaba la cubeta
    # cubeta bajo encimera (compuesto negro) con canto y válvula
    _loft(h, "coc_fregadero", m["fregadero"], -1.175, 1.415, 0.205, 0.275,
          [(9, .668), (0, .668), (-.005, .68), (-.005, .868), (-.02, .868),
           (-.02, .878), (0, .878), (.010, .870), (.012, .700), (.03, .682),
           (9, .682)], e=12, n=48)
    h.cylinder(-1.175, 1.415, 0.045, 0.682, 0.686, "coc_valvula", cromo, n=20)
    # grifo monomando negro: base, caño en cuello de cisne y maneta lateral
    h.cylinder(-1.455, 1.415, 0.028, 0.90, 0.93, "coc_grifo_base", metal_negro,
               n=20)
    _tubo(h, "coc_grifo", negro_mate,
          [(-1.455, 1.415, 0.93), (-1.455, 1.415, 1.20)]
          + _arco(-1.30, 1.415, 1.20, 0.155, 180, 0, 14)[1:]
          + [(-1.145, 1.415, 1.16)], 0.014)
    h.barra((-1.455, 1.43, 1.06), (-1.455, 1.53, 1.09), 0.007, "coc_grifo_maneta",
            negro_mate, n=8)
    # salpicadero, altos y perfil LED (4000 K)
    h.box(-1.55, 0.10, -1.53, 1.75, 0.90, 1.50, "coc_salpicadero", dekton)
    h.box(-1.53, 0.10, -1.18, 1.75, 1.50, 2.30, "coc_altos", roble_mel,
          bevel=0.006)
    for k in range(4):
        z0 = 0.10 + k * 0.4125
        h.box(-1.178, z0 + 0.003, -1.17, z0 + 0.411, 1.52, 2.28,
              f"coc_altos_puerta_{k}", roble_mel, bevel=0.004)
    h.box(-1.50, 0.12, -1.20, 1.73, 1.485, 1.50, "coc_led_altos", led_frio)

    # ISLA x[0.01,0.81] z[-0.52,1.72], 0.90 de alto
    h.box(0.06, -0.47, 0.56, 1.67, 0.0, 0.10, "isla_zocalo", gris_osc)
    h.box(0.01, -0.52, 0.56, 1.72, 0.10, 0.88, "isla_cuerpo", grafito,
          bevel=0.006)
    for k, (z0, z1) in enumerate(((-0.49, 0.10), (0.10, 0.90), (0.90, 1.69))):
        h.box(-0.004, z0, 0.01, z1, 0.14, 0.86, f"isla_cajon_{k}", grafito,
              bevel=0.004)
    h.box(0.01, -0.52, 0.81, 1.72, 0.88, 0.90, "isla_tablero", silestone,
          bevel=0.004)
    h.box(0.01, -0.54, 0.81, -0.52, 0.0, 0.90, "isla_lateral_n", silestone)
    h.box(0.01, 1.72, 0.81, 1.74, 0.0, 0.90, "isla_lateral_s", silestone)
    h.box(0.54, -0.50, 0.56, 1.70, 0.02, 0.88, "isla_frontal", silestone)
    h.box(-0.01, 0.25, 0.59, 0.75, 0.90, 0.904, "placa", pantalla)
    h.box(-0.16, 0.25, 0.74, 0.75, 2.28, 2.30, "campana", m["cromo"])
    for k, z in enumerate((-0.07, 0.60, 1.27)):
        h.cylinder(0.88, z, 0.19, 0.72, 0.75, f"taburete_{k}", negro_mate,
                   n=24)
        h.cylinder(0.88, z, 0.018, 0.0, 0.72, f"taburete_pie_{k}",
                   metal_negro, n=14)
        h.cylinder(0.88, z, 0.12, 0.20, 0.22, f"taburete_reposa_{k}",
                   metal_negro, n=20)

    # ══ SALÓN · COMEDOR (techo 2,46) ════════════════════════════════════════
    # M05 mueble de TV (no suspendido) + TV 65" mural
    h.box(4.32, -0.36, 7.32, 0.01, 0.0, 0.03, "tv_mueble_zocalo", gris_osc)
    h.box(4.32, -0.36, 7.32, 0.04, 0.03, 0.30, "tv_mueble", roble_mel,
          bevel=0.006)
    for k in range(5):
        x0 = 4.32 + k * 0.60
        h.box(x0 + 0.003, 0.04, x0 + 0.597, 0.052, 0.05, 0.28,
              f"tv_mueble_puerta_{k}", roble_mel, bevel=0.004)
    h.box(5.095, -0.33, 6.545, -0.28, 0.95, 1.78, "tv", pantalla, bevel=0.008)
    # aparador curvo con cuadro textil
    h.box(2.20, -0.42, 3.00, -0.02, 0.18, 0.78, "aparador", roble_mel,
          bevel=0.02)
    h.cylinder(2.20, -0.22, 0.20, 0.18, 0.78, "aparador_extremo_i", roble_mel,
               n=28)
    h.cylinder(3.00, -0.22, 0.20, 0.18, 0.78, "aparador_extremo_d", roble_mel,
               n=28)
    for k, (x, z) in enumerate(((2.14, -0.09), (3.06, -0.09),
                                (2.14, -0.35), (3.06, -0.35))):
        h.cylinder(x, z, 0.018, 0.0, 0.18, f"aparador_pata_{k}", metal_negro,
                   n=12)
    h.box(2.10, -0.36, 3.10, -0.335, 1.05, 2.25, "cuadro_aparador",
          tejido_claro, bevel=0.0)
    # mesa de comedor de cristal sobre dos bloques de travertino
    h.box(2.67, 1.19, 3.57, 3.00, 0.75, 0.762, "mesa_comedor", cristal)
    for k, z in enumerate((1.55, 2.65)):
        h.box(2.945, z - 0.175, 3.295, z + 0.175, 0.0, 0.75,
              f"mesa_comedor_pie_{k}", travertino, bevel=0.008)
    _silla(h, tejido_claro, roble, 2.37, 1.52, 2.67, 1.97, "O", "silla_c0")
    _silla(h, tejido_claro, roble, 2.37, 2.23, 2.67, 2.67, "O", "silla_c1")
    _silla(h, tejido_claro, roble, 3.57, 1.52, 3.87, 1.97, "E", "silla_c2")
    _silla(h, tejido_claro, roble, 3.57, 2.23, 3.87, 2.67, "E", "silla_c3")
    _silla(h, tejido_claro, roble, 2.89, 0.89, 3.34, 1.19, "N", "silla_c4")
    _silla(h, tejido_claro, roble, 2.89, 3.00, 3.34, 3.30, "S", "silla_c5")
    # lámpara colgante de tambor
    h.cylinder(3.12, 2.10, 0.006, 1.95, 2.46, "lampara_comedor_cable",
               negro_mate, n=8)
    h.cylinder(3.12, 2.10, 0.30, 1.65, 1.95, "lampara_comedor",
               m["lampara_pantalla"], n=32)
    # sofá de tres plazas con respaldo al sur
    h.box(4.75, 2.62, 7.05, 3.41, 0.15, 0.30, "sofa_bastidor", tejido,
          bevel=0.012)
    for k in range(3):
        x0 = 4.90 + k * 0.6667
        h.box(x0, 2.62, x0 + 0.6667, 3.20, 0.30, 0.42,
              f"sofa_asiento_{k}", tejido, bevel=0.06)
    h.box(4.90, 3.20, 6.90, 3.41, 0.30, 0.72, "sofa_respaldo", tejido,
          bevel=0.05)
    h.box(4.75, 2.62, 4.90, 3.41, 0.15, 0.60, "sofa_brazo_i", tejido,
          bevel=0.05)
    h.box(6.90, 2.62, 7.05, 3.41, 0.15, 0.60, "sofa_brazo_d", tejido,
          bevel=0.05)
    for k, (x, z) in enumerate(((4.82, 2.68), (6.98, 2.68),
                                (4.82, 3.35), (6.98, 3.35))):
        h.cylinder(x, z, 0.015, 0.0, 0.15, f"sofa_pata_{k}", metal_negro,
                   n=12)
    h.box(4.50, 1.20, 7.30, 3.30, 0.004, 0.012, "alfombra", m["alfombra"])
    # mesa de centro: dos bloques de travertino y tapa de cristal
    for k, x in enumerate((5.25, 5.95)):
        h.box(x, 1.58, x + 0.45, 1.94, 0.0, 0.36, f"mesa_centro_base_{k}",
              travertino, bevel=0.008)
    h.box(5.13, 1.44, 6.52, 2.08, 0.36, 0.378, "mesa_centro", cristal)
    # (butaca mariposa retirada: despeja el paso al ventanal)
    h.cylinder(7.60, 3.25, 0.15, 0.0, 0.02, "lampara_pie_base", metal_negro,
               n=24)
    h.cylinder(7.60, 3.25, 0.012, 0.02, 1.50, "lampara_pie", metal_negro,
               n=10)
    h.cylinder(7.60, 3.25, 0.20, 1.50, 1.75, "lampara_pant",
               m["lampara_pantalla"], n=28)
    if not h.cargar_asset("potted_plant_01", 1.35, 7.55, 0.25, ang=200):
        h.planta_monstera(7.55, 0.25, "planta_salon", m, alto=1.35, n_hojas=7)
    # tres cuadros sobre el sofá, en la pared sur
    for i, x in enumerate((5.10, 5.90, 6.70)):
        h.box(x - 0.30, 3.575, x + 0.30, 3.605, 1.20, 2.00,
              f"cuadro_{i}_marco", roble_mel, bevel=0.004)
        ob = h.box(x - 0.27, 3.55, x + 0.27, 3.575, 1.23, 1.97,
                   f"cuadro_{i}", m[f"lienzo_{i}"], bevel=0.0)
        h.uv_retrato(ob, x - 0.27, x + 0.27, 1.23, 1.97)

    # ══ RECIBIDOR (techo 2,30) ══════════════════════════════════════════════
    h.box(0.35, 2.54, 0.69, 4.31, 0.20, 0.90, "rec_zapatero", roble_mel,
          bevel=0.006)
    for k in range(4):
        z0 = 2.56 + k * 0.4325
        h.box(0.69, z0 + 0.003, 0.702, z0 + 0.4295, 0.22, 0.88,
              f"rec_zapatero_puerta_{k}", roble_mel, bevel=0.004)
    h.box(0.37, 2.58, 0.67, 4.27, 0.19, 0.20, "rec_led_zapatero", led)
    _disco(h, "rec_espejo", espejo, 0.35, 3.42, 1.55, 0.40, 0.012, "E")

    # ══ LAVADERO (techo 2,46) ═══════════════════════════════════════════════
    h.box(-1.16, 3.70, 0.08, 4.30, 0.88, 0.90, "lav_encimera", dekton,
          bevel=0.004)
    h.box(-1.16, 3.70, 0.08, 3.72, 0.83, 0.88, "lav_copete_f", dekton)
    h.box(-1.16, 3.70, -1.14, 4.30, 0.83, 0.88, "lav_copete_i", dekton)
    h.box(0.06, 3.70, 0.08, 4.30, 0.83, 0.88, "lav_copete_d", dekton)
    h.box(-1.14, 3.72, -0.54, 4.28, 0.0, 0.85, "lav_lavadora", blanco_laca,
          bevel=0.006)
    h.box(-0.52, 3.72, 0.08, 4.28, 0.0, 0.85, "lav_secadora", blanco_laca,
          bevel=0.006)
    _disco(h, "lav_lavadora_puerta", pantalla, -0.84, 3.715, 0.42, 0.24,
           0.015, "N")
    _disco(h, "lav_secadora_puerta", pantalla, -0.22, 3.715, 0.42, 0.24,
           0.015, "N")
    h.box(-1.16, 2.55, -1.11, 2.90, 1.60, 2.20, "lav_calentador",
          blanco_laca, bevel=0.006)

    # ══ VESTIDOR (techo 2,30) ═══════════════════════════════════════════════
    h.box(1.86, -3.24, 3.50, -2.64, 0.0, 2.30, "ves_a01_cuerpo", roble_mel,
          bevel=0.008)
    for k in range(4):
        x0 = 1.88 + k * 0.405
        h.box(x0 + 0.003, -2.64, x0 + 0.402, -2.628, 0.04, 2.26,
              f"ves_a01_puerta_{k}", roble_mel, bevel=0.004)
        if k:
            h.box(x0 - 0.012, -2.652, x0 + 0.012, -2.64, 1.00, 1.60,
                  f"ves_a01_tirador_{k}", metal_negro, bevel=0.0)
    h.box(3.50, -2.64, 4.11, -1.32, 0.0, 2.30, "ves_a02_cuerpo", roble_mel,
          bevel=0.008)
    for k in range(3):
        z0 = -2.64 + k * 0.44
        h.box(3.488, z0 + 0.003, 3.50, z0 + 0.437, 0.04, 2.26,
              f"ves_a02_puerta_{k}", roble_mel, bevel=0.004)
        if k:
            h.box(3.476, z0 - 0.012, 3.488, z0 + 0.012, 1.00, 1.60,
                  f"ves_a02_tirador_{k}", metal_negro, bevel=0.0)
    h.box(3.50, -2.91, 4.11, -2.64, 0.0, 2.30, "ves_relleno", roble_mel,
          bevel=0.006)

    # ══ DORMITORIO PRINCIPAL (techo 2,46) ═══════════════════════════════════
    h.box(4.11, -2.91, 4.13, -1.32, 0.0, 2.30, "dp_panelado", roble_mel)
    h.box(4.11, -3.18, 4.13, -2.91, 0.0, 2.30, "dp_est_fondo", roble_mel)
    h.box(4.11, -3.18, 4.43, -3.155, 0.0, 2.30, "dp_est_lat_n", roble_mel)
    h.box(4.11, -2.925, 4.43, -2.91, 0.0, 2.30, "dp_est_lat_s", roble_mel)
    for k, hh in enumerate((0.40, 0.85, 1.30, 1.75)):
        h.box(4.13, -3.155, 4.43, -2.925, hh, hh + 0.04,
              f"dp_est_balda_{k}", roble_mel, bevel=0.004)
    h.box(4.13, -3.155, 4.43, -2.925, 2.26, 2.30, "dp_est_top", roble_mel)
    h.box(4.40, -3.155, 4.43, -3.14, 0.30, 2.00, "dp_est_led", led)
    # cabecero de listones (una sola malla) y cama 1.80×2.00
    h.box(3.82, -3.24, 7.84, -3.18, 0.0, 1.20, "dp_cabecero", roble_mel)
    _multi(h, [(3.82 + k * 0.05, -3.18, 3.82 + k * 0.05 + 0.03, -3.16,
                0.0, 1.20) for k in range(81) if 3.82 + k * 0.05 + 0.03 <= 7.84],
           "dp_listones_cabecero", roble_mel)
    h.box(4.88, -3.18, 6.68, -1.18, 0.12, 0.30, "dp_cama", roble_mel,
          bevel=0.02)
    h.box(4.92, -3.14, 6.64, -1.22, 0.30, 0.52, "dp_colchon", lino,
          bevel=0.03)
    h.box(4.90, -2.50, 6.66, -1.22, 0.52, 0.58, "dp_manta", m["colcha"],
          bevel=0.02)
    for k, x in enumerate((5.07, 5.93)):
        h.box(x, -3.06, x + 0.56, -2.72, 0.52, 0.64, f"dp_almohada_{k}",
              lino, bevel=0.05)
    for k, x in enumerate((4.43, 6.72)):
        h.box(x, -3.18, x + 0.44, -2.78, 0.0, 0.50, f"dp_mesita_{k}",
              travertino, bevel=0.01)
    for k, x in enumerate((4.62, 6.94)):
        h.cylinder(x, -2.98, 0.005, 1.30, 2.46, f"dp_cable_{k}", negro_mate,
                   n=6)
        h.cylinder(x, -2.98, 0.08, 1.10, 1.30, f"dp_colgante_{k}",
                   travertino, n=20)
    h.box(7.50, -2.76, 7.85, -1.05, 0.0, 0.45, "dp_banco", roble_mel,
          bevel=0.01)

    # ══ DORMITORIO 3 (noroeste, techo 2,46) ═════════════════════════════════
    h.box(-4.71, -3.18, -4.11, -1.54, 0.0, 2.30, "d3_a04_cuerpo", roble_mel,
          bevel=0.008)
    for k in range(4):
        z0 = -3.18 + k * 0.41
        h.box(-4.722, z0 + 0.003, -4.71, z0 + 0.407, 0.04, 2.26,
              f"d3_a04_puerta_{k}", roble_mel, bevel=0.004)
        if k:
            h.box(-4.734, z0 - 0.012, -4.722, z0 + 0.012, 1.00, 1.60,
                  f"d3_a04_tirador_{k}", metal_negro, bevel=0.0)
    # E02: estantería trapezoidal arrimada al muro oeste inclinado
    for k, hh in enumerate((1.10, 1.60)):
        h.poly_prism([(-7.94, -3.16), (-7.35, -3.16), (-7.35, -0.94),
                      (-7.44, -0.94)], hh, hh + 0.04,
                     f"d3_e02_balda_{k}", roble_mel)
    h.box(-7.37, -3.16, -7.35, -0.94, 0.0, 2.10, "d3_e02_frente",
          roble_mel, bevel=0.004)
    h.box(-7.37, -3.16, -7.35, -3.13, 0.0, 2.10, "d3_e02_lat_n", roble_mel)
    h.box(-7.37, -0.97, -7.35, -0.94, 0.0, 2.10, "d3_e02_lat_s", roble_mel)
    # cama nido con cabecero al norte
    h.box(-7.30, -2.50, -6.50, -0.62, 0.02, 0.10, "d3_cama_nido", roble_mel)
    h.box(-7.35, -2.58, -6.45, -0.58, 0.10, 0.28, "d3_cama", roble_mel,
          bevel=0.02)
    h.box(-7.31, -2.54, -6.49, -0.62, 0.28, 0.46, "d3_colchon", lino,
          bevel=0.03)
    h.box(-7.35, -2.58, -6.45, -2.52, 0.0, 0.80, "d3_cabecero", roble_mel,
          bevel=0.01)
    h.box(-7.33, -2.05, -6.47, -0.62, 0.46, 0.52, "d3_manta", m["colcha"],
          bevel=0.02)
    h.box(-7.10, -2.52, -6.70, -2.22, 0.46, 0.58, "d3_almohada", lino,
          bevel=0.05)
    # escritorio bajo la V08 y silla
    h.box(-7.35, -3.16, -5.25, -2.59, 0.72, 0.75, "d3_escritorio",
          roble_mel, bevel=0.008)
    h.box(-7.35, -3.16, -7.29, -2.59, 0.0, 0.72, "d3_escritorio_pie_i",
          roble_mel)
    h.box(-5.31, -3.16, -5.25, -2.59, 0.0, 0.72, "d3_escritorio_pie_d",
          roble_mel)
    _silla(h, tejido_claro, roble, -6.04, -2.62, -5.72, -2.18, "S",
           "d3_silla")

    # ══ DORMITORIO 2 · biblioteca de cerezo trasladada del estudio ══════════
    # (techo 2,46). Composición del estudio reimplantada: bajos en L (sur bajo
    # la ventana V07 + tramo en el muro norte), estantería alta A en el muro
    # este (arranca en z=0,70: libre del barrido de P06 y de la banda de V07),
    # península con pie metálico, estantería B girada al muro norte y silla
    # al sur de la península (deja 0,90 m de paso delante de la estantería A).
    # El estudio queda sin amueblar.
    h.box(-5.53, 2.43, -3.94, 2.88, 0.08, 0.72, "d2_bajos_sur", cerezo,
          bevel=0.006)
    h.box(-5.53, 2.43, -3.94, 2.88, 0.72, 0.75, "d2_bajos_sur_tapa",
          cerezo, bevel=0.004)
    h.box(-5.48, 2.48, -3.99, 2.83, 0.0, 0.08, "d2_bajos_sur_zocalo",
          cerezo)
    for k in range(2):
        x0 = -5.51 + k * 0.45
        h.box(x0 + 0.003, 2.418, x0 + 0.447, 2.43, 0.10, 0.70,
              f"d2_bajos_sur_puerta_{k}", cerezo, bevel=0.004)
    for k in range(4):
        h.box(-4.63, 2.418, -3.96, 2.43, 0.10 + k * 0.155,
              0.10 + k * 0.155 + 0.145, f"d2_bajos_sur_cajon_{k}", cerezo,
              bevel=0.004)
    # tramo oeste de los bajos, girado al muro norte (misma pieza que en L)
    h.box(-5.68, -0.41, -4.55, 0.04, 0.08, 0.72, "d2_bajos_norte", cerezo,
          bevel=0.006)
    h.box(-5.68, -0.41, -4.55, 0.04, 0.72, 0.75, "d2_bajos_norte_tapa",
          cerezo, bevel=0.004)
    for k, (xa, xb) in enumerate(((-5.627, -5.113), (-5.107, -4.593))):
        h.box(xa, 0.028, xb, 0.04, 0.10, 0.70,
              f"d2_bajos_norte_puerta_{k}", cerezo, bevel=0.004)
    # estantería alta A contra el muro este, con armario bajo en la calle central
    h.box(-3.68, 0.70, -3.66, 2.15, 0.0, 2.25, "d2_a_fondo", cerezo)
    for k, zc in enumerate((0.70, 1.15, 1.65, 2.15)):
        h.box(-3.94 if k in (0, 3) else -3.95, zc - 0.0125,
              -3.66, zc + 0.0125, 0.0, 2.25, f"d2_a_costado_{k}", cerezo)
    h.box(-3.92, 1.175, -3.68, 1.625, 0.0, 0.74, "d2_a_armario", cerezo,
          bevel=0.006)
    h.box(-3.94, 1.16, -3.66, 1.64, 0.74, 0.77, "d2_a_encimera", cerezo,
          bevel=0.004)
    for k in range(5):
        hh = 0.80 + k * 0.33
        h.box(-3.94, 0.70, -3.66, 2.15, hh, hh + 0.025,
              f"d2_a_balda_{k}", cerezo)
    # mesa península de extremo redondeado con pie metálico
    h.box(-4.94, 0.45, -3.94, 1.05, 0.72, 0.75, "d2_peninsula", cerezo,
          bevel=0.004)
    h.cylinder(-4.94, 0.75, 0.30, 0.72, 0.75, "d2_peninsula_redondeo",
               cerezo, n=36)
    h.cylinder(-4.82, 0.75, 0.04, 0.02, 0.72, "d2_peninsula_pie",
               metal_negro, n=16)
    h.cylinder(-4.82, 0.75, 0.16, 0.0, 0.02, "d2_peninsula_base",
               metal_negro, n=28)
    # estantería alta B girada al muro norte (mismo desarrollo, 1,30 m)
    h.box(-7.00, -0.43, -5.70, -0.41, 0.0, 2.30, "d2_b_fondo", cerezo)
    for k, xc in enumerate((-7.00, -6.5667, -6.1333, -5.70)):
        alto = 2.40 if k == 1 else 2.30
        h.box(xc - 0.0125, -0.41, xc + 0.0125, -0.15, 0.0, alto,
              f"d2_b_costado_{k}", cerezo)
        if k == 1:
            h.box(xc - 0.0125, -0.41, xc + 0.0125, -0.15, 2.30, 2.40,
                  f"d2_b_sobre_{k}", cerezo)
    for k in range(7):
        hh = 0.30 + k * 0.30
        h.box(-7.00, -0.41, -5.70, -0.15, hh, hh + 0.025,
              f"d2_b_balda_{k}", cerezo)
    _silla(h, tejido_claro, roble, -4.71, 1.60, -4.39, 2.04, "S",
           "d2_silla")

    # ══ ESTUDIO · sin amueblar (biblioteca trasladada al dormitorio 2) ═══

    # ══ BAÑO 2 · con bañera (oeste, techo 2,30) ═════════════════════════════
    # bañera de porcelana en el hueco de obra: base y faldón alicatados
    _multi(h, [(-3.97, -3.16, -3.31, -1.56, 0.0, 0.10),
               (-3.36, -3.16, -3.31, -1.56, 0.10, 0.55)],
           "b2_banera", travertino_porc)
    _loft(h, "b2_banera_seno", porcelana, -3.665, -2.36, 0.305, 0.80,
          [(9, .10), (.005, .10, 12), (.005, .53, 12), (0, .535, 12),
           (0, .55, 12), (.055, .55, 5), (.065, .54, 5), (.075, .45, 5),
           (.09, .20, 5), (.13, .145, 5), (9, .14)], n=48)
    # termostática mural a 0,80 (cobre), caño bajo y ducha de mano con flexo
    h.box(-3.99, -2.52, -3.975, -2.28, 0.76, 0.84, "b2_grifo", cobre,
          bevel=0.004)
    for k, z in enumerate((-2.47, -2.33)):
        h.barra((-3.975, z, 0.80), (-3.94, z, 0.80), 0.024,
                f"b2_grifo_mando_{k}", cobre, n=16)
    _tubo(h, "b2_grifo_pico", cobre,
          [(-3.975, -2.40, 0.66), (-3.92, -2.40, 0.66), (-3.86, -2.40, 0.62)],
          0.011)
    h.barra((-3.975, -2.40, 1.00), (-3.975, -2.40, 1.50), 0.008,
            "b2_ducha_barra", cromo, n=8)
    h.barra((-3.955, -2.40, 1.30), (-3.90, -2.40, 1.24), 0.013, "b2_ducha_mano",
            cromo, n=10)
    h.barra((-3.90, -2.40, 1.24), (-3.885, -2.40, 1.22), 0.04, "b2_ducha_cabezal",
            cromo, n=16)
    _tubo(h, "b2_ducha_flexo", cromo,
          [(-3.975, -2.30, 0.70), (-3.90, -2.28, 0.78), (-3.88, -2.30, 0.95),
           (-3.93, -2.36, 1.15), (-3.955, -2.40, 1.28)], 0.008, n=8)
    h.box(-3.31, -3.16, -3.29, -2.44, 0.55, 2.00, "b2_mampara",
          vidrio_acido)
    # inodoro de suelo con cisterna
    _loft(h, "b2_cisterna", porcelana, -2.905, -3.09, 0.175, 0.07,
          [(9, .40), (0, .40), (0, .85), (.01, .86), (9, .86)], e=8, n=32)
    h.cylinder(-2.905, -3.09, 0.025, 0.86, 0.868, "b2_pulsador", cromo, n=18)
    _loft(h, "b2_wc", porcelana, -2.905, -2.81, 0.16, 0.21,
          [(9, 0.0), (0, 0.0, None, 0.62), (0, 0.15, None, 0.60),
           (0, 0.28, None, 0.85), (0, 0.37, None, 1.0), (0, 0.40, None, 1.0),
           (0.03, 0.407, None, 1.0), (9, 0.407)],
          e=2.4, frente=1, taper=0.15, e_atras=8)
    # mueble con lavabo de resina integrado (seno bajo la encimera)
    h.box(-1.75, -2.94, -1.32, -1.56, 0.30, 0.74, "b2_mueble", roble_mel,
          bevel=0.006)
    _multi(h, [(-1.75, -2.94, -1.32, -2.412, 0.74, 0.86),
               (-1.75, -2.068, -1.32, -1.56, 0.74, 0.86),
               (-1.75, -2.412, -1.632, -2.068, 0.74, 0.86),
               (-1.408, -2.412, -1.32, -2.068, 0.74, 0.86)],
           "b2_mueble_alto", roble_mel)
    for k, (z0, z1) in enumerate(((-2.90, -2.26), (-2.24, -1.60))):
        h.box(-1.762, z0, -1.75, z1, 0.32, 0.84, f"b2_mueble_cajon_{k}",
              roble_mel, bevel=0.004)
    _multi(h, [(-1.77, -2.94, -1.30, -2.40, 0.86, 0.88),
               (-1.77, -2.08, -1.30, -1.56, 0.86, 0.88),
               (-1.77, -2.40, -1.62, -2.08, 0.86, 0.88),
               (-1.42, -2.40, -1.30, -2.08, 0.86, 0.88)],
           "b2_encimera", resina, bevel=0.002)
    _loft(h, "b2_seno", resina, -1.52, -2.24, 0.10, 0.16,
          [(9, .748), (-.012, .748), (-.012, .86), (0, .86), (0, .775),
           (.02, .758), (9, .758)], e=5, n=36)
    # grifo mural del lavabo: roseta, caño y maneta
    _disco(h, "b2_grifo_roseta", cromo, -1.305, -2.24, 1.05, 0.03, 0.012, "O")
    _tubo(h, "b2_grifo_lavabo", cromo,
          [(-1.31, -2.24, 1.06), (-1.40, -2.24, 1.065), (-1.46, -2.24, 1.05),
           (-1.50, -2.24, 1.02)], 0.011)
    h.barra((-1.32, -2.24, 1.12), (-1.40, -2.24, 1.15), 0.007,
            "b2_grifo_maneta", cromo, n=8)
    h.box(-1.75, -2.92, -1.34, -1.58, 0.29, 0.30, "b2_led", led)
    h.box(-1.33, -2.94, -1.32, -1.54, 1.20, 2.10, "b2_espejo", espejo)
    h.box(-1.32, -2.94, -1.30, -1.54, 2.10, 2.12, "b2_led_espejo", led)

    # ══ BAÑO 1 · con ducha (este, techo 2,30) ═══════════════════════════════
    h.box(-0.90, -3.06, -0.12, -1.56, 0.0, 0.02, "b1_plato",
          travertino_porc)
    # rociador de techo (cuadrado de 0,30 a 2,20) con brazo y roseta
    h.cylinder(-0.45, -2.25, 0.035, 2.29, 2.30, "b1_rociador_roseta", cromo,
               n=18)
    h.barra((-0.45, -2.25, 2.29), (-0.45, -2.25, 2.215), 0.011,
            "b1_rociador_brazo", cromo, n=10)
    _loft(h, "b1_rociador", cromo, -0.45, -2.25, 0.15, 0.15,
          [(9, 2.200), (0, 2.200, 10), (0, 2.212, 10), (9, 2.212)], e=10, n=40)
    # monomando de ducha en la pared oeste
    h.box(-0.92, -2.45, -0.905, -2.25, 1.02, 1.12, "b1_grifo_ducha", cobre,
          bevel=0.004)
    for k, z in enumerate((-2.40, -2.30)):
        h.barra((-0.905, z, 1.07), (-0.875, z, 1.07), 0.022,
                f"b1_grifo_mando_{k}", cobre, n=16)
    h.box(-0.14, -3.06, -0.12, -2.49, 0.0, 2.00, "b1_mampara",
          vidrio_acido)
    # inodoro suspendido: parte superior a 0,40 (spec) y placa de accionamiento
    _loft(h, "b1_wc", porcelana, 0.315, -2.805, 0.175, 0.255,
          [(9, .12), (0, .12, None, .80), (0, .20, None, .95),
           (0, .375, None, 1.0), (-.004, .380, None, 1.0),
           (-.004, .386, None, 1.0), (.03, .405, None, 1.0), (9, .405)],
          e=2.4, frente=1, taper=0.15, e_atras=10)
    h.box(0.19, -3.080, 0.44, -3.072, 0.92, 1.08, "b1_pulsador", cobre,
          bevel=0.003)
    h.box(-0.12, -3.24, 0.76, -3.08, 1.20, 2.31, "b1_armario", laca,
          bevel=0.006)
    for k, (x0, x1) in enumerate(((-0.10, 0.31), (0.33, 0.74))):
        h.box(x0, -3.08, x1, -3.068, 1.22, 2.29,
              f"b1_armario_puerta_{k}", laca, bevel=0.004)
    h.box(0.76, -3.21, 1.73, -2.78, 0.30, 0.74, "b1_mueble", roble_mel,
          bevel=0.006)
    _multi(h, [(0.76, -3.21, 1.73, -3.115, 0.74, 0.86),
               (0.76, -2.785, 1.73, -2.78, 0.74, 0.86),
               (0.76, -3.115, 1.085, -2.785, 0.74, 0.86),
               (1.415, -3.115, 1.73, -2.785, 0.74, 0.86)],
           "b1_mueble_alto", roble_mel)
    for k, (x0, x1) in enumerate(((0.78, 1.23), (1.25, 1.71))):
        h.box(x0, -2.78, x1, -2.768, 0.32, 0.84, f"b1_mueble_cajon_{k}",
              roble_mel, bevel=0.004)
    _multi(h, [(0.76, -3.23, 1.73, -3.10, 0.86, 0.88),
               (0.76, -2.80, 1.73, -2.76, 0.86, 0.88),
               (0.76, -3.10, 1.10, -2.80, 0.86, 0.88),
               (1.40, -3.10, 1.73, -2.80, 0.86, 0.88)],
           "b1_encimera", resina, bevel=0.002)
    _loft(h, "b1_seno", resina, 1.25, -2.95, 0.15, 0.15,
          [(9, .748), (-.012, .748), (-.012, .86), (0, .86), (0, .775),
           (.02, .758), (9, .758)], e=5, n=36)
    # grifo mural del lavabo (bajo el espejo, que empieza a 1,20)
    _disco(h, "b1_grifo_roseta", cromo, 1.25, -3.225, 1.05, 0.03, 0.012, "S")
    _tubo(h, "b1_grifo", cromo,
          [(1.25, -3.225, 1.05), (1.25, -3.10, 1.06), (1.25, -3.02, 1.05),
           (1.25, -2.98, 1.02)], 0.011)
    h.box(0.78, -3.19, 1.71, -2.80, 0.29, 0.30, "b1_led", led)
    h.box(0.78, -3.21, 1.71, -3.19, 1.20, 2.31, "b1_espejo", espejo)

    # ══ BALCÓN (terraza) ════════════════════════════════════════════════════
    # Sin barandilla propia: se usa la exterior del edificio (build_balcones);
    # la interior duplicada se retiró. Solo la maceta, pegada al lateral norte.
    if not h.cargar_asset("potted_plant_02", 0.85, 8.60, 0.30, ang=130):
        h.cylinder(8.60, 0.30, 0.16, 0.0, 0.35, "tz_maceta", m["maceta"],
                   n=18)
        h.sphere(8.60, 0.30, 0.62, 0.20, "tz_planta", m["planta"], seg=12,
                 ring=6, sy=0.85)
