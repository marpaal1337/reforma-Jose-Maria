#!/usr/bin/env python3
"""
Parsea los .txt extraídos a data/presupuestos.json (anidado) y
data/presupuestos.csv (plano). Detecta formato por nombre y aplica
regex/heurísticas específicas.

Uso:
    python3 scripts/parsear_presupuestos.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TXT_DIR = ROOT / "data" / "texto"
JSON_OUT = ROOT / "data" / "presupuestos.json"
CSV_OUT = ROOT / "data" / "presupuestos.csv"

# -------- utilidades comunes --------

# Cifras en español: "1.234,56" o "1234.56" o "1234,56"
_NUM = re.compile(r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+[.,]\d+|\d+)")
_MONEY = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+)[,.](\d{2})(?!\d)")


def _clean_text(text: str) -> str:
    """Normaliza caracteres PUA / weird que pdfplumber deja al decodificar
    fuentes CID incrustadas. Reemplaza por equivalentes legibles."""
    repl = {
        "": "-",  # U+F0AD
        "": " ",  # U+F020
        "": "•",
        "": "■",
        "": "(",
        "": ")",
        "": "►",
        "": "▼",
        "": "◄",
        "": "€",
        "": "0",
        "": "1",
        "": "2",
        "": "3",
        "": "4",
        "": "5",
        "": "6",
        "": "7",
        "": "8",
        "": "9",
        "": ",",
        "": "-",
        "": "%",
        "": "&",
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def to_float(s: str | None) -> float | None:
    if s is None:
        return None
    s = s.strip()
    if not s or s in {"?", "-", "—"}:
        return None
    # Quitar símbolo €
    s = s.replace("€", "").strip()
    # Si tiene formato español con miles: 1.234,56 -> 1234.56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # Decimales sin miles: 1234,56 -> 1234.56 ; pero también "1,5" -> 1.5
        # Distinguir: si la parte tras la coma tiene 1-2 dígitos y la anterior parece tener
        # miles implícitos, lo dejamos. Aquí asumimos que una sola coma es decimal.
        # PERO si son varios grupos "1,2,3" lo dejamos como está (no es dinero).
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2 and re.fullmatch(r"\d+", parts[0]):
            s = parts[0] + "." + parts[1]
        else:
            s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_date(s: str | None) -> str | None:
    """Devuelve fecha en ISO (YYYY-MM-DD) o None."""
    if not s:
        return None
    s = s.strip()
    # dd/mm/yyyy
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    # dd-mm-yyyy
    m = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    # "17 de octubre de 2025"
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12,
    }
    m = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})", s, re.I)
    if m:
        d, mes, y = m.groups()
        mes_n = meses.get(mes.lower())
        if mes_n:
            return f"{y}-{mes_n:02d}-{int(d):02d}"
    # "Junio25" -> 2025-06
    m = re.search(r"([A-Za-záéíóú]+)(\d{2,4})", s)
    if m:
        mes_name, y = m.groups()
        mes_n = meses.get(mes_name.lower())
        if mes_n:
            yi = int(y)
            if yi < 100:
                yi = 2000 + yi
            return f"{yi}-{mes_n:02d}-01"
    return None


# -------- detectores por oficio --------

def _file_to_oficio(filename: str) -> str:
    base = filename.split("__", 1)[0]
    return base


def _file_to_contratista(filename: str) -> str:
    stem = filename.split("__", 1)[-1].rsplit(".", 1)[0]
    # Quitar sufijos comunes
    for suf in [
        "_PPTO JOSE MARIA MARTES LERMA",
        "_PRESUPUESTO NUMERO 472 REFORMA CALLE JOSE MARIA LERMA N 2 PTA 28",
        "_PRESUPUESTO NUMERO 468 PROYECTO SOFIA",
        "_Presupuesto 1-000022 DEF",
        "_Presupuesto 1-000079",
        "_Presupuesto 1-000084",
        "_Presupuesto borrador 2025-11-06",
        "_2026-7 TONI AMORES",
    ]:
        if stem.endswith(suf):
            stem = stem[: -len(suf)]
            break
    return stem.strip()


# -------- parsers específicos --------

def parse_cyss_myp(text: str, file: str) -> dict:
    """Cyss *_myp.pdf: presupuesto con capítulos DSM010c / etc."""
    rec: dict[str, Any] = {
        "archivo": file,
        "formato": "cyss_myp",
        "moneda": "EUR",
        "iva_incluido": True,
    }
    # Fecha en cabecera
    m = re.search(r"(\d{1,2}\s+de\s+[a-záéíóú]+\s+de\s+\d{4})", text, re.I)
    if m:
        rec["fecha"] = parse_date(m.group(1))
    # TOTAL al final
    m = re.search(r"TOTAL\.{5,}\s*([\d\.,]+)", text)
    if m:
        rec["total_ejecucion_material"] = to_float(m.group(1))
    # IVA
    m = re.search(r"(\d{1,2}(?:[.,]\d+)?)%\s*I\.?V\.?A\.?\.{5,}\s*([\d\.,]+)", text)
    if m:
        rec["iva_pct"] = to_float(m.group(1))
        rec["importe_iva"] = to_float(m.group(2))
    # Total presupuesto
    m = re.search(r"TOTAL PRESUPUESTO (?:CONTRATA|GENERAL)\s+([\d\.,]+)", text)
    if m:
        rec["total_con_iva"] = to_float(m.group(1))
    # Partidas
    capitulos: dict[str, list[dict]] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^CAPÍTULO\s+(\d+)\s+(.+)$", line)
        if m:
            current = f"{m.group(1)} {m.group(2).strip()}"
            capitulos.setdefault(current, [])
            continue
        m = re.match(r"^TOTAL CAPÍTULO\s+(\d+)\s+(.+?)\.+\s*([\d\.,]+)", line)
        if m and current:
            capitulos[current + " [TOTAL]"] = [{
                "total_capitulo": to_float(m.group(3)),
            }]
            current = None
            continue
        # Línea de partida típica: "DSM010c Ud Demolición de cocina completa."
        m = re.match(
            r"^([A-Z]{2,3}\d{3}[a-z]?)\s+(Ud|m²|m|pa|h)\s+(.+?)$",
            line,
        )
        if m and current is not None:
            capitulos[current].append({
                "codigo": m.group(1),
                "unidad": m.group(2),
                "descripcion_corta": m.group(3)[:80],
            })
    rec["capitulos"] = capitulos
    return rec


def parse_cyss_resumen(text: str, file: str) -> dict:
    """Cyss *_resumen.pdf: tabla CAPITULO / EUROS / %."""
    rec: dict[str, Any] = {
        "archivo": file,
        "formato": "cyss_resumen",
        "moneda": "EUR",
        "iva_incluido": True,
    }
    m = re.search(r"(\d{1,2}\s+de\s+[a-záéíóú]+\s+de\s+\d{4})", text, re.I)
    if m:
        rec["fecha"] = parse_date(m.group(1))
    lineas_cap: list[dict] = []
    for line in text.splitlines():
        m = re.match(r"^(\d{2,3})\s+([A-ZÁÉÍÓÚÑ/ ]+?)\.+\s*([\d\.,]+)\s+(\d+[.,]\d+)", line)
        if m:
            num, nombre, euros, pct = m.groups()
            lineas_cap.append({
                "capitulo": num,
                "nombre": nombre.strip(),
                "euros": to_float(euros),
                "porcentaje": to_float(pct),
            })
    rec["capitulos"] = lineas_cap
    m = re.search(r"TOTAL EJECUCIÓN MATERIAL\s+([\d\.,]+)", text)
    if m:
        rec["total_ejecucion_material"] = to_float(m.group(1))
    m = re.search(r"(\d{1,2}(?:[.,]\d+)?)%\s*I\.?V\.?A\.?\.+\s*([\d\.,]+)", text)
    if m:
        rec["iva_pct"] = to_float(m.group(1))
        rec["importe_iva"] = to_float(m.group(2))
    m = re.search(r"TOTAL PRESUPUESTO (?:CONTRATA|GENERAL)\s+([\d\.,]+)", text)
    if m:
        rec["total_con_iva"] = to_float(m.group(1))
    m = re.search(r"a\s+(\d{1,2}/\d{1,2}/\d{4})", text)
    if m and "fecha" not in rec:
        rec["fecha"] = parse_date(m.group(1))
    return rec


def parse_toni(text: str, file: str) -> dict:
    """Toni presupuesto. Formato tipo:
       CLIENTE: SOFIA FECHA PRESUPUESTO *: 09-11-2025
       DEMOLICION
       – 1.1 DEMOLICION COCINA 650€
       – 1.6 LEVANTADO PAVIMENTO
       150€
    No tiene total escrito, hay que sumarlo."""
    rec: dict[str, Any] = {
        "archivo": file,
        "formato": "toni_lista",
        "moneda": "EUR",
        "iva_incluido": False,
        "nota": "Total no escrito en el PDF; se calcula como suma de las partidas con importe.",
    }
    m = re.search(r"CLIENTE:\s*(\S+)\s+FECHA PRESUPUESTO\s*\*?:\s*(\S+)", text)
    if m:
        rec["cliente_cabecera"] = m.group(1).strip()
        rec["fecha"] = parse_date(m.group(2))
    secciones: list[dict] = []
    seccion_actual: dict | None = None
    partida_pendiente: dict | None = None
    suma = 0.0
    partidas_contadas = 0
    partidas_con_importe = 0
    # Pre-pass: juntar líneas partidas (importe en línea siguiente) en tokens
    # luego aplicar reglas.
    # Estrategia: detectar cabecera de sección SOLO si la línea siguiente empieza por "–"/"-" + número.
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        ls = lines[i].strip()
        # Cabecera de sección: línea en mayúsculas sola (sin "–" ni número)
        es_seccion = (
            ls
            and ls.isupper()
            and not ls.startswith("–") and not ls.startswith("-")
            and not re.match(r"^[\d.,]+$", ls)
            and len(ls) > 2 and len(ls) < 40
            and "€" not in ls
            and ":" not in ls
            and "CLIENTE" not in ls
            and "PRESUPUESTO" not in ls
            and "TRABAJOS" not in ls
            and "Paterna" not in ls
            and "NOTA" not in ls
            and "CUALQUIER" not in ls
            and "REALIZARAN" not in ls
            and "VALORACION" not in ls
            and "FALTARIA" not in ls
            and "REGATAS" not in ls
            and "ALICATADA" not in ls
            and "ENLUCIDA" not in ls
            and "RODAPIE" not in ls
            and "RELLENAR" not in ls
            and "MAESTREAR" not in ls
            and "CONTENEDORES" not in ls
        )
        if es_seccion:
            # Mirar la siguiente línea no vacía
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            siguiente = lines[j].strip() if j < len(lines) else ""
            # Es sección real si la siguiente línea empieza por "–"/"-" + número
            if re.match(r"^[–-]\s*[\d.,']+", siguiente):
                if seccion_actual:
                    secciones.append(seccion_actual)
                seccion_actual = {"nombre": ls.strip(), "partidas": []}
                partida_pendiente = None
                i += 1
                continue
        if seccion_actual is None:
            i += 1
            continue
        # Partida: "– 1.1 DEMOLICION COCINA 650€"
        m = re.match(
            r"^[–-]\s*([\d.,']+)\s+(.+?)\s+(\d{1,3}(?:[.,]\d{3})*|\d+)\s*€\s*$", ls
        )
        if m:
            num, desc, imp = m.groups()
            imp_f = to_float(imp)
            if imp_f is not None:
                suma += imp_f
                partidas_con_importe += 1
            partidas_contadas += 1
            seccion_actual["partidas"].append({
                "num": num, "descripcion": desc.strip(), "importe": imp_f,
            })
            partida_pendiente = None
            i += 1
            continue
        # Partida sin importe: "– 1.6 LEVANTADO PAVIMENTO" (importe en la línea sig)
        m = re.match(r"^[–-]\s*([\d.,']+)\s+(.+?)\s*$", ls)
        if m and "€" not in ls and "TOTAL" not in ls.upper():
            num, desc = m.groups()
            seccion_actual["partidas"].append({
                "num": num, "descripcion": desc.strip(), "importe": None,
            })
            partida_pendiente = seccion_actual["partidas"][-1]
            partidas_contadas += 1
            i += 1
            continue
        # Importe suelto
        m = re.match(r"^(\d{1,3}(?:[.,]\d{3})+|\d+)\s*€?\s*$", ls)
        if m and partida_pendiente is not None:
            imp = to_float(m.group(1))
            if imp is not None:
                partida_pendiente["importe"] = imp
                suma += imp
                partidas_con_importe += 1
            partida_pendiente = None
        i += 1
    if seccion_actual:
        secciones.append(seccion_actual)
    rec["secciones"] = secciones
    rec["total_calculado_sin_iva"] = round(suma, 2) if suma else None
    if suma:
        rec["total_calculado_con_iva"] = round(suma * 1.21, 2)
    rec["n_partidas"] = partidas_contadas
    rec["n_partidas_con_importe"] = partidas_con_importe
    return rec


def parse_david_barat(text: str, file: str) -> dict:
    """David Barat. Formato:
       Presupuesto 1 000084 1 17/11/2025
       ...
       1 6.177,10 6.177,10 6.177,10
       TIPO IMPORTE DESCUENTO PRONTO PAGO PORTES FINANCIACIÓN BASE I.V.A. R.E.
       21,00 6.177,10 6.177,10 1.297,19
       10,00
       4,00
       OBSERVACIONES: TOTAL: 7.474,29"""
    rec: dict[str, Any] = {
        "archivo": file,
        "formato": "david_barat",
        "moneda": "EUR",
        "iva_incluido": True,
    }
    m = re.search(r"Presupuesto\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d{1,2}/\d{1,2}/\d{4})", text)
    if m:
        rec["num_presupuesto"] = m.group(2)
        rec["fecha"] = parse_date(m.group(4))
    # Partidas: "<cant> <precio_unidad> <subtotal> <dto> <total>"
    # Filtrar las líneas que están antes de "TIPO IMPORTE" (cabecera de totales)
    cut = text.find("TIPO IMPORTE")
    body = text if cut == -1 else text[:cut]
    partidas: list[dict] = []
    for m in re.finditer(
        r"^\s*(\d+(?:[.,]\d+)?)\s+(\d{1,3}(?:\.\d{3})*,\d{2})\s+(\d{1,3}(?:\.\d{3})*,\d{2})\s+(\d{1,3}(?:\.\d{3})*,\d{2})(?:\s+(\d{1,3}(?:\.\d{3})*,\d{2}))?",
        body, re.M,
    ):
        cant, pu, sub, total, *rest = m.groups()
        partidas.append({
            "cantidad": to_float(cant),
            "precio_unitario": to_float(pu),
            "subtotal": to_float(sub),
            "total": to_float(total),
        })
    rec["partidas"] = partidas
    # BASE / IVA / TOTAL — buscar tras "TIPO IMPORTE"
    after = text[cut:] if cut != -1 else text
    m = re.search(r"BASE\s+([\d\.,]+)", after)
    if m:
        rec["base_imponible"] = to_float(m.group(1))
    m = re.search(r"TOTAL:\s*([\d\.,]+)", after)
    if m:
        rec["total_con_iva"] = to_float(m.group(1))
    return rec


def parse_poveda(text: str, file: str) -> dict:
    """Poveda borrador: tabla CONCEPTO CANTIDAD PRECIO S/I IVA SUBTOTAL S/I."""
    rec: dict[str, Any] = {
        "archivo": file,
        "formato": "poveda",
        "moneda": "EUR",
        "iva_incluido": True,
    }
    m = re.search(r"Presupuesto\s*\n\s*Borrador\s*#\s*(\d+)\s+(\d{2}/\d{2}/\d{4})", text)
    if m:
        rec["num_borrador"] = m.group(1)
        rec["fecha"] = parse_date(m.group(2))
    # Líneas: "<CONCEPTO> <cant> unidad <precio> € <iva>% <subtotal> €"
    lineas = []
    for m in re.finditer(
        r"([A-ZÁÉÍÓÚÑ/ ()0-9.,-]{6,}?)\s+(\d+)\s+unidad\s+([\d\.,]+)\s*€\s+(\d+)\s*%\s+([\d\.,]+)\s*€",
        text,
    ):
        concepto, cant, precio, iva, sub = m.groups()
        lineas.append({
            "concepto": concepto.strip(),
            "cantidad": int(cant),
            "precio_unitario": to_float(precio),
            "iva_pct": int(iva),
            "subtotal": to_float(sub),
        })
    rec["partidas"] = lineas
    m = re.search(r"Base imponible\s+([\d\.,]+)\s*€", text)
    if m:
        rec["base_imponible"] = to_float(m.group(1))
    # La línea final: "IVA 21% (5.291,00 €) 1.111,11 €" + línea siguiente "6.402,11 €"
    m = re.search(r"IVA\s+(\d+)\s*%\s*\([^)]+\)\s*([\d\.,]+)\s*€\s*\n\s*([\d\.,]+)\s*€", text)
    if m:
        rec["iva_pct"] = int(m.group(1))
        rec["importe_iva"] = to_float(m.group(2))
        rec["total_con_iva"] = to_float(m.group(3))
    m = re.search(r"válido hasta el\s+(\d{1,2}/\d{1,2}/\d{4})", text)
    if m:
        rec["valido_hasta"] = parse_date(m.group(1))
    return rec


def parse_paracon(text: str, file: str) -> dict:
    """Paracon: lista de estancias con mecanismos. Total al final."""
    rec: dict[str, Any] = {
        "archivo": file,
        "formato": "paracon_estancias",
        "moneda": "EUR",
        "iva_incluido": True,
    }
    m = re.search(r"FECHA:\s*(\d{1,2}/\d{1,2}/\d{4})", text)
    if m:
        rec["fecha"] = parse_date(m.group(1))
    m = re.search(r"PRESUP:\s*(\S+)", text)
    if m:
        rec["num_presupuesto"] = m.group(1).strip()
    m = re.search(r"NOMBRE:\s*(.+?)\s+PRESUP", text)
    if m:
        rec["cliente_cabecera"] = m.group(1).strip()
    # Estancias
    estancias: list[dict] = []
    estancia = None
    for line in text.splitlines():
        ls = line.strip()
        m = re.match(r"^([A-ZÁÉÍÓÚ ]+):\s*Cantidad:\s*$", ls)
        if m and "PRESUPUESTO" not in ls:
            estancia = {"estancia": m.group(1).strip(), "mecanismos": []}
            estancias.append(estancia)
            continue
        if estancia is not None:
            m = re.match(r"^([A-Za-záéíóú ]+?)\s+(\d+)\s*$", ls)
            if m:
                estancia["mecanismos"].append({
                    "tipo": m.group(1).strip(),
                    "cantidad": int(m.group(2)),
                })
    rec["estancias"] = estancias
    m = re.search(r"BASE:\s*([\d\.,]+)", text)
    if m:
        rec["base_imponible"] = to_float(m.group(1))
    m = re.search(r"IVA:\s*([\d\.,]+)", text)
    if m:
        rec["importe_iva"] = to_float(m.group(1))
    m = re.search(r"TOTAL:\s*([\d\.,]+)", text)
    if m:
        rec["total_con_iva"] = to_float(m.group(1))
    # Forma de pago
    pagos = []
    for m in re.finditer(r"(\d+)%\s+(.+?)\n", text):
        pagos.append({"pct": int(m.group(1)), "hito": m.group(2).strip()})
    if pagos:
        rec["forma_de_pago"] = pagos
    return rec


def parse_nacher(text: str, file: str) -> dict:
    """Ventanas Nacher. Presupuesto 1040/1. Subtotales 'Suma y sigue' y TOTAL al final."""
    rec: dict[str, Any] = {
        "archivo": file,
        "formato": "nacher_ventanas",
        "moneda": "EUR",
        "iva_incluido": True,
    }
    m = re.search(r"PRESUPUESTO\s+(\S+)", text)
    if m:
        rec["num_presupuesto"] = m.group(1).strip()
    m = re.search(r"Fecha solicitud\s*:\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})", text)
    if m:
        rec["fecha"] = parse_date(m.group(1).replace(".", "/").replace("-", "/"))
    ventanas: list[dict] = []
    # Patrón: "Pos. N - <ID>" luego varias líneas, luego "UDS: <n> <importe> <total>"
    for m in re.finditer(
        r"Pos\.\s+(\d+)\s+-\s+(\S+)\s*\n"
        r"([\s\S]+?)"
        r"UDS:\s+(\d+(?:[.,]\d+)?)\s+([\d\.,]+)\s+([\d\.,]+)",
        text,
    ):
        pos, idv, cuerpo, uds, imp, total = m.groups()
        # Primera línea del cuerpo suele ser la descripción corta
        primera = cuerpo.strip().split("\n", 1)[0].strip()
        ventanas.append({
            "pos": int(pos),
            "id": idv,
            "descripcion_corta": primera[:120],
            "uds": to_float(uds),
            "importe_unitario": to_float(imp),
            "importe_total": to_float(total),
        })
    rec["ventanas"] = ventanas
    m = re.search(r"SubTotal\s+([\d\.,]+)", text)
    if m:
        rec["subtotal"] = to_float(m.group(1))
    m = re.search(r"Base Imponible en €\s+([\d\.,]+)", text)
    if m:
        rec["base_imponible"] = to_float(m.group(1))
    m = re.search(r"I\.V\.A\.\s*\((\d+[.,]\d+)%\)\s+([\d\.,]+)", text)
    if m:
        rec["iva_pct"] = to_float(m.group(1))
        rec["importe_iva"] = to_float(m.group(2))
    m = re.search(r"TOTAL en €\s+([\d\.,]+)", text)
    if m:
        rec["total_con_iva"] = to_float(m.group(1))
    return rec


def parse_valenzuela(text: str, file: str) -> dict:
    """Valenzuela (armarios / cocina / puertas). Formato:
       PPTO. JOSE MARIA MORTES LERMA 05-11-2025
       ARMARIOS:
       - <concepto>……<precio>€
       Total armarios…………..<subtotal>€ más IVA = <total_con_iva> €
    """
    rec: dict[str, Any] = {
        "archivo": file,
        "formato": "valenzuela",
        "moneda": "EUR",
        "iva_incluido": True,
    }
    m = re.search(r"PPTO\.?\s+JOSE MARIA\s+\w+\s+\w+\s+(\d{2}-\d{2}-\d{4})", text)
    if m:
        rec["fecha"] = parse_date(m.group(1))
    # Subsección: la primera línea en mayúsculas
    m = re.match(r"^([A-ZÁÉÍÓÚ ]+):\s*$", text.strip().split("\n")[1].strip() if "\n" in text else "")
    seccion = m.group(1).strip() if m else ""
    rec["seccion"] = seccion
    partidas: list[dict] = []
    for line in text.splitlines():
        ls = line.strip()
        # Partida: "ARMARIO PRINCIPAL 1,64ML MELAMINA 6 cajones, ... 2.115,57€"
        m = re.match(r"^[-–]?\s*(.+?)\s*[\.…]+\s*([\d\.]+,\d{2})\s*€\s*$", ls)
        if m:
            desc, imp = m.groups()
            partidas.append({"descripcion": desc.strip(), "importe": to_float(imp)})
        # "Total armarios…………..12.691,31€ más IVA = 15.356,49 €"
    m = re.search(
        r"(?:Total|Precio)\s+([a-záéíóú ]+?)\s*[\.…]+\s*([\d\.]+,\d{2})\s*€?\s*m[áa]s\s+IVA\s*=\s*([\d\.]+,\d{2})\s*€",
        text, re.I,
    )
    if m:
        rec["total_sin_iva"] = to_float(m.group(2))
        rec["total_con_iva"] = to_float(m.group(3))
    rec["partidas"] = partidas
    # Suma de comprobación
    if partidas:
        rec["suma_partidas"] = round(sum(p["importe"] or 0 for p in partidas), 2)
    # Plazo (semanas)
    m = re.search(r"antes de\s+(\d+)\s+semanas", text)
    if m:
        rec["plazo_minimo_semanas"] = int(m.group(1))
    return rec


# -------- dispatcher --------

PARSERS = [
    ("Contratista general__Cyss_v1_myp", parse_cyss_myp),
    ("Contratista general__Cyss_v2.0_myp", parse_cyss_myp),
    ("Contratista general__Cyss_v1_resumen", parse_cyss_resumen),
    ("Contratista general__Cyss_v2.0_resumen", parse_cyss_resumen),
    ("Albañilería__Toni_", parse_toni),
    ("Fontanería__David Barat_", parse_david_barat),
    ("Clima__David Barat_", parse_david_barat),
    ("Electricidad__Poveda_", parse_poveda),
    ("Electricidad__Paracon_", parse_paracon),
    ("Carpintería exterior__Ventanas Nacher_", parse_nacher),
    ("Carpintería interior__Valenzuela_", parse_valenzuela),
]


def dispatch(filename: str) -> str:
    for prefix, _ in PARSERS:
        if filename.startswith(prefix):
            return prefix
    return ""


def main() -> int:
    files = sorted(TXT_DIR.glob("*.txt"))
    out: list[dict] = []
    csv_rows: list[dict] = []

    for f in files:
        text = _clean_text(f.read_text(encoding="utf-8"))
        pref = dispatch(f.name)
        parser = next((p for k, p in PARSERS if k == pref), None)
        if not parser:
            print(f"WARN sin parser: {f.name}", file=sys.stderr)
            rec = {"archivo": f.name, "formato": "desconocido"}
        else:
            try:
                rec = parser(text, f.name)
            except Exception as e:
                print(f"ERR {f.name}: {e}", file=sys.stderr)
                rec = {"archivo": f.name, "formato": "error", "error": str(e)}
        rec["oficio"] = _file_to_oficio(f.name)
        rec["contratista"] = _file_to_contratista(f.name)
        out.append(rec)
        # CSV plano
        csv_rows.append({
            "oficio": rec.get("oficio"),
            "contratista": rec.get("contratista"),
            "archivo": rec.get("archivo"),
            "formato": rec.get("formato"),
            "fecha": rec.get("fecha"),
            "total_con_iva": rec.get("total_con_iva"),
            "total_sin_iva": rec.get("total_sin_iva"),
            "total_ejecucion_material": rec.get("total_ejecucion_material"),
            "total_calculado_sin_iva": rec.get("total_calculado_sin_iva"),
            "importe_iva": rec.get("importe_iva"),
            "iva_pct": rec.get("iva_pct"),
            "base_imponible": rec.get("base_imponible"),
            "num_presupuesto": rec.get("num_presupuesto"),
            "num_borrador": rec.get("num_borrador"),
            "cliente_cabecera": rec.get("cliente_cabecera"),
        })

    JSON_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK {len(out)} registros -> {JSON_OUT}")

    if csv_rows:
        with CSV_OUT.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
            w.writeheader()
            w.writerows(csv_rows)
        print(f"OK {len(csv_rows)} filas -> {CSV_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
