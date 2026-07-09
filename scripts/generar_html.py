#!/usr/bin/env python3
"""
Genera index.html autocontenido (sin CDN, sin build) con un dashboard
interactivo de la reforma.

Diseño: paleta sobria (papel, tinta, acento terracota), tipografía
serif para cifras, sistema para UI. Tablas ordenables y filtrables.
Gráficos en SVG hechos a mano. Visor de PDF embebido.
"""
from __future__ import annotations

import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PRES = json.loads((DATA / "presupuestos.json").read_text(encoding="utf-8"))
EXCEL = json.loads((DATA / "excel.json").read_text(encoding="utf-8"))
OUT = ROOT / "index.html"

CSS = r"""
:root {
  --paper: #FAF7F2;
  --paper-2: #F5F1EA;
  --ink: #1A1A1A;
  --ink-2: #3D3D3D;
  --muted: #6B6B6B;
  --line: #E0DAD0;
  --accent: #B5651D;
  --accent-2: #8C4D14;
  --warn: #B5410F;
  --good: #4A6B2E;
  --serif: 'Source Serif 4', 'Source Serif Pro', Georgia, 'Times New Roman', serif;
  --sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
[data-theme="dark"] {
  --paper: #1A1815;
  --paper-2: #252220;
  --ink: #F2EFE8;
  --ink-2: #D9D4CA;
  --muted: #9B968A;
  --line: #3D3933;
  --accent: #D88B4D;
  --accent-2: #E5A870;
  --warn: #E07A4A;
  --good: #8FB059;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: var(--paper); color: var(--ink); font-family: var(--sans); font-size: 15px; line-height: 1.5; }
body { max-width: 1280px; margin: 0 auto; padding: 32px 40px 96px; }
header.top {
  display: flex; justify-content: space-between; align-items: flex-end;
  border-bottom: 2px solid var(--ink);
  padding-bottom: 16px; margin-bottom: 32px;
}
header.top h1 { font-family: var(--serif); font-size: 36px; font-weight: 600; letter-spacing: -0.02em; }
header.top .sub { color: var(--muted); font-size: 13px; margin-top: 4px; }
header.top .actions { display: flex; gap: 8px; }
button.btn {
  background: var(--paper-2); color: var(--ink); border: 1px solid var(--line);
  padding: 6px 14px; font: inherit; font-size: 13px; cursor: pointer; border-radius: 2px;
}
button.btn:hover { background: var(--line); }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 40px; }
.kpi { background: var(--paper-2); border: 1px solid var(--line); padding: 18px 20px; border-radius: 2px; }
.kpi .label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 6px; }
.kpi .value { font-family: var(--serif); font-size: 28px; font-variant-numeric: tabular-nums; letter-spacing: -0.01em; }
.kpi .delta { font-size: 12px; color: var(--muted); margin-top: 4px; }
section { margin-bottom: 48px; }
section > h2 { font-family: var(--serif); font-size: 22px; margin-bottom: 16px; border-bottom: 1px solid var(--line); padding-bottom: 8px; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.card { background: var(--paper-2); border: 1px solid var(--line); padding: 16px 18px; border-radius: 2px; }
.card h3 { font-family: var(--serif); font-size: 16px; margin-bottom: 8px; }
.card .meta { font-size: 12px; color: var(--muted); margin-bottom: 10px; }
.card .range { font-family: var(--serif); font-size: 14px; font-variant-numeric: tabular-nums; }
.card .reco { margin-top: 10px; font-size: 12px; padding: 4px 8px; background: var(--paper); border-left: 2px solid var(--accent); border-radius: 1px; }
.card.empty { opacity: 0.55; }
.card.empty .range { color: var(--muted); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 9px 12px; border-bottom: 1px solid var(--line); background: var(--paper); }
th { background: var(--paper-2); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ink-2); cursor: pointer; user-select: none; }
th:hover { background: var(--line); }
th .arrow { opacity: 0.4; margin-left: 4px; font-size: 10px; }
th.sorted .arrow { opacity: 1; color: var(--accent); }
td.num { text-align: right; font-variant-numeric: tabular-nums; font-family: var(--serif); }
tbody tr:nth-child(even) td { background: var(--paper-2); }
[data-theme="dark"] tbody tr:nth-child(even) td { background: #252220; }
tr:hover td { background: var(--line); }
.tag { display: inline-block; padding: 2px 7px; border-radius: 2px; font-size: 11px; font-weight: 500; }
.tag.cyss { background: #E8DCC8; color: #5C3D14; }
.tag.vigente { background: #D4E2C8; color: #2E4A1A; }
.tag.borrador { background: #E8D5C8; color: #7A3A14; }
.tag.legacy { background: #D8D8D8; color: #555; }
.tag.warn { background: #F0D5C8; color: #8C3A14; }
[data-theme="dark"] .tag.cyss { background: #5C4A2E; color: #E8D5B0; }
[data-theme="dark"] .tag.vigente { background: #2E4A1A; color: #D4E2C8; }
[data-theme="dark"] .tag.borrador { background: #7A4A2E; color: #E8D5B0; }
[data-theme="dark"] .tag.legacy { background: #3D3933; color: #B8B0A0; }
[data-theme="dark"] .tag.warn { background: #7A3A14; color: #F0D5B0; }
.controls { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.controls input, .controls select { background: var(--paper); color: var(--ink); border: 1px solid var(--line); padding: 5px 10px; font: inherit; font-size: 13px; border-radius: 2px; }
.controls input { min-width: 200px; }
.controls label { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted); }
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
@media (max-width: 900px) { .chart-row { grid-template-columns: 1fr; } .kpis { grid-template-columns: 1fr 1fr; } }
svg { display: block; max-width: 100%; }
.timeline { position: relative; padding-left: 20px; border-left: 2px solid var(--line); }
.timeline .event { position: relative; padding: 6px 0 6px 16px; }
.timeline .event::before { content: ''; position: absolute; left: -7px; top: 14px; width: 12px; height: 12px; background: var(--accent); border: 2px solid var(--paper); border-radius: 50%; }
.timeline .event .when { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.timeline .event .what { font-size: 14px; }
.alerts { background: var(--paper-2); border-left: 3px solid var(--warn); padding: 16px 20px; border-radius: 2px; }
.alerts h3 { color: var(--warn); font-family: var(--serif); font-size: 16px; margin-bottom: 8px; }
.alerts ul { margin-left: 20px; }
.alerts li { margin: 4px 0; }
footer { margin-top: 64px; padding-top: 16px; border-top: 1px solid var(--line); font-size: 12px; color: var(--muted); }
.legend { display: flex; gap: 14px; font-size: 11px; color: var(--muted); margin-top: 8px; flex-wrap: wrap; }
.legend span { display: inline-flex; align-items: center; gap: 4px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; }
.ctx-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px; }
.ctx-item { background: var(--paper-2); border: 1px solid var(--line); padding: 14px 16px; border-radius: 2px; text-align: center; }
.ctx-item .ctx-val { font-family: var(--serif); font-size: 24px; font-weight: 600; display: block; color: var(--accent); }
.ctx-item .ctx-label { font-size: 12px; color: var(--muted); }
.scenarios { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 12px; }
.scenario { background: var(--paper-2); border: 1px solid var(--line); padding: 18px 20px; border-radius: 2px; position: relative; }
.scenario.scenario-rec { border-color: var(--accent); border-width: 2px; }
.scenario h3 { font-family: var(--serif); font-size: 15px; margin-bottom: 6px; }
.scenario .scenario-price { font-family: var(--serif); font-size: 26px; font-variant-numeric: tabular-nums; color: var(--accent); margin-bottom: 8px; }
.scenario p { font-size: 13px; color: var(--ink-2); margin-bottom: 8px; }
.scenario .risk { font-size: 11px; padding: 3px 8px; border-radius: 2px; display: inline-block; }
.risk-low { background: #D4E2C8; color: #2E4A1A; }
.risk-med { background: #F0E0C8; color: #8C6B14; }
.risk-high { background: #F0D5C8; color: #8C3A14; }
[data-theme="dark"] .risk-low { background: #2E4A1A; color: #D4E2C8; }
[data-theme="dark"] .risk-med { background: #5C4A2E; color: #F0E0C8; }
[data-theme="dark"] .risk-high { background: #5C2A1A; color: #F0D5C8; }
.phases { display: flex; flex-direction: column; gap: 6px; padding: 4px 0; }
.phase-row { display: flex; align-items: center; gap: 16px; }
.phase-label { min-width: 140px; font-size: 12px; flex-shrink: 0; }
.phase-label strong { display: block; font-family: var(--serif); font-size: 14px; }
.phase-label .meta { font-size: 11px; color: var(--muted); }
.phase-track { flex: 1; height: 28px; background: var(--paper); border-radius: 2px; position: relative; overflow: visible; }
.phase-bar { height: 28px; background: var(--accent); border-radius: 2px; position: absolute; top: 0; display: flex; align-items: center; justify-content: center; min-width: 40px; }
.phase-bar span { font-size: 10px; color: #fff; font-weight: 600; white-space: nowrap; padding: 0 6px; }
.phase-bar.dep { background: var(--accent-2); }
.phase-bar.par { background: var(--good); }
.phase-bar.rem { background: var(--muted); }
.dq-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.dq-card { background: var(--paper-2); border: 1px solid var(--line); border-left: 3px solid var(--warn); padding: 14px 16px; border-radius: 2px; }
.dq-card h4 { font-family: var(--serif); font-size: 14px; margin-bottom: 6px; }
.dq-card ul { margin-left: 16px; font-size: 13px; }
.dq-card li { margin: 3px 0; }
.dq-card .dq-note { font-size: 12px; color: var(--warn); margin-top: 6px; }
.dq-card.encimera { border-left-color: var(--accent); }
.dq-card.encimera .dq-note { color: var(--accent); }
.pay-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; }
.pay-item { background: var(--paper-2); border: 1px solid var(--line); padding: 14px 16px; border-radius: 2px; text-align: center; }
.pay-item .pay-pct { font-family: var(--serif); font-size: 24px; font-weight: 600; color: var(--accent); }
.pay-item .pay-label { font-size: 12px; color: var(--muted); margin-top: 4px; }
.pay-item .pay-eur { font-size: 13px; font-family: var(--serif); margin-top: 4px; color: var(--ink); }
td.neg { color: var(--good); }
td.pos { color: var(--warn); }
@media (max-width: 700px) { .ctx-grid { grid-template-columns: repeat(2, 1fr); } .scenarios { grid-template-columns: 1fr; } .phase-label { min-width: 100px; font-size: 11px; } .phase-label strong { font-size: 12px; } .pay-grid { grid-template-columns: repeat(2, 1fr); } }
@media print {
  body { padding: 16px; max-width: none; font-size: 11px; }
  .actions, .controls { display: none; }
  section { break-inside: avoid; page-break-inside: avoid; }
  table { font-size: 10px; }
  th { background: #EEE; }
}
"""

JS = r"""
(function () {
  var tables = {};

  function setupTable(tid) {
    var t = document.getElementById(tid);
    if (!t) return;
    var tbody = t.tBodies[0];
    var headers = t.tHead.rows[0].cells;
    var state = { col: -1, asc: true };
    tables[tid] = state;
    Array.from(headers).forEach(function (th, i) {
      var arrow = th.querySelector('.arrow');
      if (!arrow) { arrow = document.createElement('span'); arrow.className = 'arrow'; th.appendChild(arrow); }
      th.addEventListener('click', function () {
        if (state.col === i) { state.asc = !state.asc; } else { state.col = i; state.asc = true; }
        var rows = Array.from(tbody.rows);
        rows.sort(function (a, b) {
          var av = (a.cells[i].dataset && a.cells[i].dataset.v != null) ? a.cells[i].dataset.v : a.cells[i].textContent.trim();
          var bv = (b.cells[i].dataset && b.cells[i].dataset.v != null) ? b.cells[i].dataset.v : b.cells[i].textContent.trim();
          var an = parseFloat(av), bn = parseFloat(bv);
          if (!isNaN(an) && !isNaN(bn)) return state.asc ? an - bn : bn - an;
          return state.asc ? String(av).localeCompare(String(bv), 'es') : String(bv).localeCompare(String(av), 'es');
        });
        rows.forEach(function (r) { tbody.appendChild(r); });
        Array.from(headers).forEach(function (h, j) {
          h.classList.toggle('sorted', j === i);
          var a = h.querySelector('.arrow');
          if (a) a.textContent = (j === i) ? (state.asc ? '\u25B2' : '\u25BC') : '';
        });
      });
    });
  }

  // ---- Filter ----
  function applyFilter() {
    var txt = (document.getElementById('f-q').value || '').toLowerCase();
    var of = document.getElementById('f-of').value;
    var est = document.getElementById('f-est').value;
    var tbody = document.getElementById('tbl-main').tBodies[0];
    Array.from(tbody.rows).forEach(function (tr) {
      var text = tr.textContent.toLowerCase();
      var ofOk = !of || tr.dataset.oficio === of;
      var estOk = !est || tr.dataset.estado === est;
      var txtOk = !txt || text.indexOf(txt) !== -1;
      tr.style.display = (ofOk && estOk && txtOk) ? '' : 'none';
    });
    updateCount();
  }

  function updateCount() {
    var el = document.getElementById('f-count');
    if (!el) return;
    var tbody = document.getElementById('tbl-main').tBodies[0];
    var n = Array.from(tbody.rows).filter(function (r) { return r.style.display !== 'none'; }).length;
    var tot = tbody.rows.length;
    el.textContent = n + ' / ' + tot;
  }

  function initFilters() {
    var ids = ['f-q', 'f-of', 'f-est'];
    ids.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener('input', applyFilter);
    });
    var resetBtn = document.getElementById('f-reset');
    if (resetBtn) resetBtn.addEventListener('click', function () {
      var q = document.getElementById('f-q');
      var o = document.getElementById('f-of');
      var e = document.getElementById('f-est');
      if (q) q.value = '';
      if (o) o.value = '';
      if (e) e.value = '';
      applyFilter();
    });
    updateCount();
  }

  // ---- Theme ----
  function initTheme() {
    var saved = localStorage.getItem('theme');
    if (saved) document.documentElement.dataset.theme = saved;
    var btn = document.getElementById('theme');
    if (btn) btn.addEventListener('click', function () {
      var cur = document.documentElement.dataset.theme;
      var next = cur === 'dark' ? '' : 'dark';
      if (next) document.documentElement.dataset.theme = next;
      else document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('theme', next);
    });
  }

  // ---- Init ----
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      setupTable('tbl-main');
      setupTable('tbl-cap');
      initFilters();
      initTheme();
    });
  } else {
    setupTable('tbl-main');
    setupTable('tbl-cap');
    initFilters();
    initTheme();
  }
})();
"""


def fmt_eur(n) -> str:
    if n is None:
        return "—"
    return f"{n:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def total(r) -> float | None:
    for k in ("total_con_iva", "total_ejecucion_material",
              "total_calculado_con_iva", "total_calculado_sin_iva"):
        v = r.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def sin_iva(r) -> float | None:
    for k in ("total_sin_iva", "total_ejecucion_material",
              "total_calculado_sin_iva", "base_imponible"):
        v = r.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def estado_para(r) -> str:
    """Clasifica el estado: vigente | borrador | legacy | cyss | sofia."""
    arch = r.get("archivo", "").lower()
    if "proyecto sofia" in arch or r.get("cliente_cabecera") == "SOFIA":
        return "sofia"
    if "Contratista general" in r.get("oficio", ""):
        return "cyss"
    if r.get("formato") == "desconocido":
        return "legacy"
    if r.get("valido_hasta"):
        # Poveda: caducado en 2025-11-16
        return "borrador"
    return "vigente"


# ---- Charts en SVG ----

def svg_pie(slices: list[tuple[str, float, str]], size=320) -> str:
    """Donut chart. slices: [(label, value, color), ...]"""
    import math
    total = sum(s[1] for s in slices) or 1
    cx, cy, r = size / 2, size / 2, size / 2 - 10
    r_in = r * 0.55
    out = [f'<svg viewBox="0 0 {size} {size + 60}" xmlns="http://www.w3.org/2000/svg">']
    angle = -90.0
    for label, val, color in slices:
        if val <= 0: continue
        frac = val / total
        a_end = angle + frac * 360
        large = 1 if frac > 0.5 else 0
        def pt(rad, deg):
            ra = math.radians(deg)
            return cx + rad * math.cos(ra), cy + rad * math.sin(ra)
        x1o, y1o = pt(r, angle)
        x2o, y2o = pt(r, a_end)
        x1i, y1i = pt(r_in, a_end)
        x2i, y2i = pt(r_in, angle)
        d = (f"M {x1o:.2f} {y1o:.2f} "
             f"A {r} {r} 0 {large} 1 {x2o:.2f} {y2o:.2f} "
             f"L {x1i:.2f} {y1i:.2f} "
             f"A {r_in} {r_in} 0 {large} 0 {x2i:.2f} {y2i:.2f} Z")
        out.append(f'<path d="{d}" fill="{color}" />')
        angle = a_end
    out.append(
        f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" '
        f'font-family="Source Serif 4, Georgia, serif" font-size="22" '
        f'font-weight="600" fill="var(--ink)">{fmt_eur(total)}</text>'
    )
    out.append(
        f'<text x="{cx}" y="{cy + 14}" text-anchor="middle" '
        f'font-size="10" fill="var(--muted)">total proyecto</text>'
    )
    out.append('</svg>')
    legend = '<div class="legend">'
    for label, val, color in slices:
        pct = val / total * 100
        legend += f'<span><i style="background:{color}"></i>{html.escape(label)} · {pct:.1f}%</span>'
    legend += '</div>'
    return "\n".join(out) + legend


def svg_barras_por_contratista(por_grupo: dict[str, list[tuple[str, float, str]]],
                               width=520, height=320) -> str:
    """por_grupo: {oficio: [(contratista, total, estado), ...]}"""
    # Solo oficios con >= 2 contratistas comparables
    grupos = {o: v for o, v in por_grupo.items() if len(v) >= 2 and all(t[1] for t in v)}
    if not grupos:
        return "<p class='meta'>Sin datos comparables.</p>"
    # Altura proporcional
    row_h = 28
    label_w = 180
    bar_max_w = width - label_w - 100
    rows = []
    max_val = 0
    for oficio, items in grupos.items():
        for contr, t, est in items:
            max_val = max(max_val, t)
    if max_val == 0:
        return "<p class='meta'>Sin datos comparables.</p>"
    total_h = sum(20 + len(v) * row_h for v in grupos.values()) + 20
    out = [f'<svg viewBox="0 0 {width} {total_h}" xmlns="http://www.w3.org/2000/svg" style="font-family: Inter, sans-serif; font-size: 11px;">']
    y = 10
    colors = {"vigente": "#B5651D", "borrador": "#D4A373", "legacy": "#9B968A",
              "cyss": "#3D5A80", "sofia": "#C77B5C"}
    for oficio, items in grupos.items():
        out.append(f'<text x="0" y="{y + 11}" font-family="Source Serif 4, serif" font-size="13" font-weight="600" fill="var(--ink)">{html.escape(oficio)}</text>')
        y += 20
        for contr, t, est in items:
            bar_w = (t / max_val) * bar_max_w
            color = colors.get(est, "#888")
            out.append(f'<text x="0" y="{y + 13}" fill="var(--muted)">{html.escape(contr[:40])}</text>')
            out.append(f'<rect x="{label_w}" y="{y}" width="{bar_w:.1f}" height="18" fill="{color}" rx="1"/>')
            out.append(f'<text x="{label_w + bar_w + 6:.1f}" y="{y + 13}" font-family="Source Serif 4, serif" fill="var(--ink)">{fmt_eur(t)}</text>')
            y += row_h
        y += 6
    out.append('</svg>')
    return "\n".join(out)


def build_project_context() -> str:
    return """
<section>
  <h2>Proyecto</h2>
  <div class="ctx-grid">
    <div class="ctx-item"><span class="ctx-val">~90</span> <span class="ctx-label">m² superficie</span></div>
    <div class="ctx-item"><span class="ctx-val">9</span> <span class="ctx-label">estancias</span></div>
    <div class="ctx-item"><span class="ctx-val">88,3</span> <span class="ctx-label">m² pavimento</span></div>
    <div class="ctx-item"><span class="ctx-val">93,4</span> <span class="ctx-label">m² falso techo</span></div>
    <div class="ctx-item"><span class="ctx-val">2</span> <span class="ctx-label">baños</span></div>
    <div class="ctx-item"><span class="ctx-val">~90</span> <span class="ctx-label">m² climatización</span></div>
    <div class="ctx-item"><span class="ctx-val">10</span> <span class="ctx-label">oficios</span></div>
    <div class="ctx-item"><span class="ctx-val">14</span> <span class="ctx-label">documentos</span></div>
  </div>
  <p class="meta" style="margin-top: 8px; color: var(--muted); font-size: 12px;">Según planos <em>estado inicial</em> (PEA.01) y <em>distribución</em> (PEA.02) escala 1:50. Ver <code>informes/ANALISIS_PLANOS.md</code>.</p>
</section>"""


def build_scenarios(excel: dict, total_cyss: float) -> str:
    col_b = 70846
    col_c = 79469
    diff_sc = col_c - total_cyss
    diff_cb = col_c - col_b
    return f"""
<section>
  <h2>Escenarios económicos</h2>
  <div class="scenarios">
    <div class="scenario scenario-rec">
      <h3>Cyss v2.0 (contratista general)</h3>
      <div class="scenario-price">{fmt_eur(total_cyss)}</div>
      <p>Cyss coordina todos los oficios. Riesgo de deriva mínimo. Incluye dirección de obra simplificada, IVA 10%.</p>
      <div class="risk risk-low">Riesgo bajo · coordinación incluida</div>
    </div>
    <div class="scenario">
      <h3>Gestión directa (col. B Excel)</h3>
      <div class="scenario-price">{fmt_eur(total_cyss - col_b)}</div>
      <p>Subcontratas directas sin Cyss. Ahorro estimado con precios de 2025. Requiere coordinación propia. Diferencia vs Cyss: {fmt_eur(col_b - total_cyss)}.</p>
      <div class="risk risk-med">Riesgo medio · coordinación a cargo del cliente</div>
    </div>
    <div class="scenario">
      <h3>Autogestión (col. C Excel)</h3>
      <div class="scenario-price">{fmt_eur(col_c)}</div>
      <p>Escenario alternativo con precios actualizados. Máximo coste. Diferencia vs Cyss: {fmt_eur(col_c - total_cyss)} ({((col_c/total_cyss)-1)*100:+.0f}%).</p>
      <div class="risk risk-high">Riesgo alto · máximo coste y carga de gestión</div>
    </div>
  </div>
  <p class="meta" style="margin-top: 8px; color: var(--muted); font-size: 12px;">Datos del Excel de planificación (Sofia Palacios). Col. B = 70.846 € (subcontratas directas), Col. C = 79.469 € (escenario alternativo). Ver <code>informes/CRUCE_CON_EXCEL.md</code>.</p>
</section>"""


def build_phases() -> str:
    phases = [
        ("00", "Demolición", "Demolición, Albañilería", "1 sem", "", "dep"),
        ("01", "Albañilería", "Albañilería", "2 sem", "00", "dep"),
        ("02", "Instalaciones", "Fontanería, Electricidad, Clima", "2 sem", "01", "dep"),
        ("03", "Pladur", "Pladur", "1-2 sem", "02", "dep"),
        ("04", "Carpintería int.", "Valenzuela (armarios, cocina, puertas)", "8 sem*", "03", "dep"),
        ("05", "Acabados", "Pavimentos, alicatados, pintura", "2 sem", "04", "dep"),
        ("06", "Ventanas", "Ventanas Nacher", "1 sem", "00", "par"),
        ("07", "Encimeras", "Marmolista", "1 sem", "04", "par"),
        ("08", "Remates", "Limpieza, retoques", "1 sem", "05-07", "rem"),
    ]
    rows = []
    for num, name, off, dur, dep, cls in phases:
        rows.append(f"""
  <div class="phase-row">
    <div class="phase-label"><strong>{num} · {name}</strong><span class="meta">{off}</span></div>
    <div class="phase-track"><div class="phase-bar {cls}" style="width:{(int(dur[0]) if dur[0].isdigit() else 2)*4 + (4 if '8' in dur else 0)}%"><span>{dur}</span></div></div>
  </div>""")
    return f"""
<section>
  <h2>Fases de ejecución</h2>
  <div class="phases">
    {''.join(rows)}
  </div>
  <p class="meta" style="margin-top: 12px; color: var(--muted); font-size: 12px;">
    * Carpintería interior: 8 semanas de plazo de fabricación (pedir lo antes posible).
    <span style="display:inline-block; width:12px; height:12px; background:var(--accent); border-radius:2px; vertical-align:middle; margin-left:12px;"></span> secuencial
    <span style="display:inline-block; width:12px; height:12px; background:var(--good); border-radius:2px; vertical-align:middle; margin-left:8px;"></span> paralelo
    <span style="display:inline-block; width:12px; height:12px; background:var(--muted); border-radius:2px; vertical-align:middle; margin-left:8px;"></span> remate
  </p>
</section>"""


def build_cyss_comparison(v1: dict | None, v2: dict | None) -> str:
    if not v1 or not v2 or not v1.get("capitulos") or not v2.get("capitulos"):
        return ""
    v1_map = {c["capitulo"]: c["euros"] for c in v1["capitulos"]}
    v2_map = {c["capitulo"]: c["euros"] for c in v2["capitulos"]}
    caps_order = ["01", "02", "03", "04", "05", "06", "13", "14"]
    rows = []
    total_v1 = 0
    total_v2 = 0
    for cap in caps_order:
        v1v = v1_map.get(cap, 0)
        v2v = v2_map.get(cap, 0)
        total_v1 += v1v
        total_v2 += v2v
        diff = v2v - v1v
        pct = (diff / v1v * 100) if v1v else 0
        cls = "neg" if diff < 0 else ("pos" if diff > 0 else "")
        arrow = "▼" if diff < 0 else ("▲" if diff > 0 else "—")
        rows.append(f"""
<tr>
  <td>{cap} {html.escape(v2.get("capitulos", [{}])[caps_order.index(cap)]["nombre"] if caps_order.index(cap) < len(v2["capitulos"]) else "")}</td>
  <td class="num">{fmt_eur(v1v)}</td>
  <td class="num">{fmt_eur(v2v)}</td>
  <td class="num {cls}">{arrow} {fmt_eur(abs(diff))}</td>
  <td class="num {cls}">{pct:+.1f}%</td>
</tr>""")
    diff_t = total_v2 - total_v1
    cls_t = "neg" if diff_t < 0 else ("pos" if diff_t > 0 else "")
    return f"""
<section>
  <h2>Cyss v1 vs v2.0 — evolución del presupuesto general</h2>
  <table>
    <thead><tr><th>Capítulo</th><th class="num">v1 (€)</th><th class="num">v2.0 (€)</th><th class="num">Δ €</th><th class="num">Δ %</th></tr></thead>
    <tbody>{''.join(rows)}
<tr style="font-weight:600;">
  <td>TOTAL</td>
  <td class="num">{fmt_eur(total_v1)}</td>
  <td class="num">{fmt_eur(total_v2)}</td>
  <td class="num {cls_t}">{'▼' if diff_t < 0 else '▲' if diff_t > 0 else '—'} {fmt_eur(abs(diff_t))}</td>
  <td class="num {cls_t}">{(diff_t/total_v1)*100:+.1f}%</td>
</tr></tbody>
  </table>
  <p class="meta" style="margin-top: 8px; color: var(--muted); font-size: 12px;">v1: 17-10-2025 · v2.0: 04-06-2026. El trasvase Albañilería → Pladur (-38.9% / +119.1%) es el principal cambio. Total neto: -3.0%. Ver <code>informes/COMPARATIVA_CYSS.md</code>.</p>
</section>"""


def build_data_quality(pres: list[dict]) -> str:
    toni472 = next((r for r in pres if "472" in r.get("archivo", "")), None)
    items_sin_precio = []
    if toni472:
        for sec in toni472.get("secciones", []):
            for p in sec.get("partidas", []):
                if p.get("importe") is None:
                    items_sin_precio.append(p["descripcion"])
    return f"""
<section>
  <h2>Datos abiertos y riesgos</h2>
  <div class="dq-grid">
    <div class="dq-card">
      <h4>Toni 472 — 5 partidas sin cerrar</h4>
      <ul>
        {''.join(f'<li>{html.escape(d)}</li>' for d in items_sin_precio)}
      </ul>
      <div class="dq-note">⚠ Pedir a Toni que cierre los importes antes de comparar con Cyss</div>
    </div>
    <div class="dq-card encimera">
      <h4>Encimeras no presupuestadas</h4>
      <p style="font-size:13px;">DEKTON Marmorio + SILESTONE Charcoal Soapstone no aparecen en Cyss v2.0. Pueden suponer 2.000–4.000 € adicionales.</p>
      <div class="dq-note">⚠ Pedir oferta a marmolista</div>
    </div>
    <div class="dq-card">
      <h4>Poveda — oferta caducada</h4>
      <p style="font-size:13px;">Presupuesto de electricidad válido hasta 16-11-2025. Superado por Paracon (más reciente y más barato).</p>
      <div class="dq-note">→ Descartar Poveda</div>
    </div>
  </div>
</section>"""


def build_payments(pres: list[dict]) -> str:
    paracon = next((r for r in pres if "Paracon" in r.get("contratista", "")), None)
    if not paracon:
        return ""
    total_p = paracon.get("total_con_iva", 6056.05)
    hitos = paracon.get("forma_de_pago", [])
    if not hitos:
        return ""
    items = []
    total_pct = 0
    for h in hitos:
        pct = h.get("pct", 0)
        eur = total_p * pct / 100
        total_pct += pct
        items.append(f"""
  <div class="pay-item">
    <div class="pay-pct">{pct}%</div>
    <div class="pay-label">{html.escape(h.get("hito", ""))}</div>
    <div class="pay-eur">{fmt_eur(eur)}</div>
  </div>""")
    # remaining
    restante = 100 - total_pct
    if restante > 0:
        items.append(f"""
  <div class="pay-item">
    <div class="pay-pct">{restante}%</div>
    <div class="pay-label">Finalización</div>
    <div class="pay-eur">{fmt_eur(total_p * restante / 100)}</div>
  </div>""")
    return f"""
<section>
  <h2>Plan de pagos — Paracon (electricidad)</h2>
  <div class="pay-grid">
    {''.join(items)}
  </div>
  <p class="meta" style="margin-top: 8px; color: var(--muted); font-size: 12px;">Sobre <strong>{fmt_eur(total_p)}</strong> IVA incl. · <strong>{total_pct + restante}%</strong> distribuido en {len(hitos) + (1 if restante > 0 else 0)} hitos. Solo Paracon tiene condiciones de pago detalladas en los PDFs extraídos.</p>
</section>"""


def main() -> None:
    hoy = datetime.now().strftime("%Y-%m-%d")

    # Cyss v2.0
    v2 = next((r for r in PRES if r["archivo"] == "Contratista general__Cyss_v2.0_resumen.txt"), None)
    v1 = next((r for r in PRES if r["archivo"] == "Contratista general__Cyss_v1_resumen.txt"), None)
    total_cyss = v2["total_con_iva"] if v2 else 0

    # Subcontratas
    subs = []
    for r in PRES:
        if r.get("formato") == "desconocido": continue
        if "Contratista general" in r.get("oficio", ""): continue
        if r.get("archivo", "").endswith("_myp.txt"): continue
        if "PROYECTO SOFIA" in r["archivo"]: continue
        t = total(r)
        if t:
            subs.append((r["oficio"], r.get("contratista", "?"), t, r.get("fecha"), estado_para(r)))
    total_subs = sum(s[2] for s in subs)

    # Por oficio (para tarjetas)
    por_oficio: dict[str, list] = defaultdict(list)
    for r in PRES:
        if r.get("formato") == "desconocido":
            por_oficio[r["oficio"]].append({"legacy": True, "r": r})
            continue
        if "Contratista general" in r.get("oficio", ""): continue
        t = total(r)
        est = estado_para(r)
        por_oficio[r["oficio"]].append({
            "contratista": r.get("contratista", "?"),
            "total": t,
            "estado": est,
            "r": r,
        })

    # ---- KPIs ----
    kpis = f"""
<div class="kpis">
  <div class="kpi">
    <div class="label">Cyss v2.0 (general)</div>
    <div class="value">{fmt_eur(total_cyss)}</div>
    <div class="delta">04-06-2026 · IVA incl.</div>
  </div>
  <div class="kpi">
    <div class="label">Suma subcontratas</div>
    <div class="value">{fmt_eur(total_subs)}</div>
    <div class="delta">{len(subs)} ofertas independientes</div>
  </div>
  <div class="kpi">
    <div class="label">Δ gestión directa</div>
    <div class="value">{fmt_eur(total_cyss - total_subs)}</div>
    <div class="delta">Cyss − subcontratas</div>
  </div>
  <div class="kpi">
    <div class="label">vs Cyss v1 (oct 2025)</div>
    <div class="value">{fmt_eur((v2['total_con_iva'] - v1['total_con_iva']) if v1 and v2 else 0)}</div>
    <div class="delta">{(v2['total_con_iva']/v1['total_con_iva']-1)*100:+.1f}% en 8 meses</div>
  </div>
</div>
"""

    # ---- Tarjetas por oficio ----
    cards = []
    # Mapeo a capítulos Cyss (para tarjetas de oficios integrados)
    caps = {c["nombre"].strip().split()[0]: (c["nombre"].strip(), c["euros"]) for c in (v2.get("capitulos", []) if v2 else [])}
    nombre_caps = {
        "DEMOLICIÓN": "Demolición",
        "ALBAÑILERÍA": "Albañilería",
        "PLADUR": "Pladur",
        "INSTALACIÓN": None,  # múltiples
        "ILUMINACIÓN": "Iluminación",
        "VARIOS": "Varios",
    }
    # Construir tarjetas
    for oficio in ["Albañilería", "Carpintería exterior", "Carpintería interior",
                   "Clima", "Demolición", "Detalle baños", "Electricidad",
                   "Encimeras", "Fontanería", "Pladur"]:
        items = por_oficio.get(oficio, [])
        ofertas = [it for it in items if it.get("total") is not None]
        if ofertas:
            ts = [o["total"] for o in ofertas]
            mn, mx = min(ts), max(ts)
            rango = f"{fmt_eur(mn)} – {fmt_eur(mx)}" if mn != mx else fmt_eur(mn)
        else:
            rango = "—"
        # Recomendación rápida
        reco = ""
        if oficio == "Electricidad":
            reco = "Paracon (más reciente, financia en 4 hitos)"
        elif oficio == "Albañilería" and any("Toni" in (o.get("contratista") or "") for o in ofertas):
            tono = next((o for o in ofertas if "Toni" in (o.get("contratista") or "")), None)
            if tono: reco = f"Validar {tono['contratista']} vs Cyss (Toni +28%)"
        elif oficio == "Encimeras":
            reco = "⚠ No en Cyss v2.0 · pedir oferta a marmolista"
        elif oficio == "Carpintería interior" and any("Valenzuela" in (o.get("contratista") or "") for o in ofertas):
            reco = "Aceptar (3 oficios, 8 sem. de plazo)"
        elif oficio == "Fontanería":
            reco = "Cubierto por David Barat (vía Cyss)"
        elif oficio == "Clima":
            reco = "Cubierto por David Barat (vía Cyss)"
        card_class = "card" if ofertas else "card empty"
        cards.append(f"""
<div class="{card_class}">
  <h3>{oficio}</h3>
  <div class="meta">{len(ofertas)} oferta(s) con importe</div>
  <div class="range">{rango}</div>
  {f'<div class="reco">{reco}</div>' if reco else ''}
</div>
""")
    cards_html = '<div class="cards">' + "\n".join(cards) + '</div>'

    # ---- Tabla principal ----
    filas = []
    for r in PRES:
        if r.get("archivo", "").endswith("_myp.txt"): continue
        if "Planos" in r.get("oficio", ""): continue
        arch = r["archivo"].replace("__", "/").replace(".txt", ".pdf")
        contr = r.get("contratista", "—")
        oficio = r.get("oficio", "?")
        np = r.get("num_presupuesto") or r.get("num_borrador") or "—"
        fecha = r.get("fecha") or "—"
        t = total(r)
        s = sin_iva(r)
        est = estado_para(r)
        est_label = {"vigente": "vigente", "borrador": "borrador", "legacy": "legacy",
                     "cyss": "Cyss", "sofia": "otro proyecto"}.get(est, est)
        pdf_rel = arch
        filas.append(f"""
<tr data-oficio="{html.escape(oficio)}" data-estado="{html.escape(est)}">
  <td>{html.escape(oficio)}</td>
  <td>{html.escape(contr)}</td>
  <td>{html.escape(str(np))}</td>
  <td>{html.escape(str(fecha))}</td>
  <td class="num" data-v="{s if s is not None else ''}">{fmt_eur(s)}</td>
  <td class="num" data-v="{t if t is not None else ''}"><strong>{fmt_eur(t)}</strong></td>
  <td><span class="tag {est}">{est_label}</span></td>
  <td><a href="{html.escape(pdf_rel)}" target="_blank">PDF</a></td>
</tr>""")
    oficios_unicos = sorted({r.get("oficio", "?") for r in PRES
                            if not r.get("archivo", "").endswith("_myp.txt")
                            and "Planos" not in r.get("oficio", "")})
    tabla = f"""
<div class="controls">
  <input id="f-q" placeholder="Buscar...">
  <select id="f-of"><option value="">— todos los oficios —</option>
    {''.join(f'<option value="{html.escape(o)}">{html.escape(o)}</option>' for o in oficios_unicos)}
  </select>
  <select id="f-est"><option value="">— todos los estados —</option>
    <option value="vigente">Vigentes</option>
    <option value="borrador">Borradores</option>
    <option value="legacy">Legacy</option>
    <option value="cyss">Cyss (general)</option>
    <option value="sofia">Otro proyecto</option>
  </select>
  <button id="f-reset" class="btn">Reset</button>
  <span style="margin-left:auto; color: var(--muted); font-size: 12px;">mostrando <span id="f-count">0</span></span>
</div>
<table id="tbl-main">
  <thead>
    <tr><th>Oficio<span class="arrow"></span></th><th>Contratista<span class="arrow"></span></th>
        <th>Nº<span class="arrow"></span></th><th>Fecha<span class="arrow"></span></th>
        <th class="num">Base (sin IVA)<span class="arrow"></span></th>
        <th class="num">Total (IVA incl.)<span class="arrow"></span></th>
        <th>Estado<span class="arrow"></span></th>
        <th>Doc</th></tr>
  </thead>
  <tbody>{''.join(filas)}</tbody>
</table>
"""

    # ---- Gráficos ----
    # Pie: % por capítulo Cyss
    slices = []
    palette = ["#B5651D", "#8C4D14", "#3D5A80", "#5B8C5A", "#A35D5D", "#C9943D", "#6B6B6B", "#8E7B95"]
    if v2 and v2.get("capitulos"):
        for i, c in enumerate(v2["capitulos"]):
            slices.append((f"{c['capitulo']} {c['nombre']}", c["euros"], palette[i % len(palette)]))
    pie = svg_pie(slices)

    # Barras: comparativa de subcontratas en oficios con varios presupuestos
    por_grupo = {}
    for oficio, items in por_oficio.items():
        entries = []
        for it in items:
            if it.get("legacy"): continue
            t = it.get("total")
            if t: entries.append((it.get("contratista", "?"), t, it.get("estado", "?")))
        if entries:
            por_grupo[oficio] = entries
    barras = svg_barras_por_contratista(por_grupo)

    # ---- Tabla capítulos Cyss ----
    if v2:
        cap_filas = []
        for c in v2["capitulos"]:
            cap_filas.append(f"""
<tr>
  <td>{c['capitulo']} {html.escape(c['nombre'])}</td>
  <td class="num" data-v="{c['euros']}">{fmt_eur(c['euros'])}</td>
  <td class="num" data-v="{c['porcentaje']}">{c['porcentaje']:.2f}%</td>
</tr>""")
        cap_total = f"""
<tr style="font-weight:600; background: var(--paper-2);">
  <td>TOTAL ejecución material</td>
  <td class="num">{fmt_eur(v2.get('total_ejecucion_material'))}</td>
  <td class="num">100%</td>
</tr>
<tr>
  <td>IVA 10%</td>
  <td class="num">{fmt_eur(v2.get('importe_iva'))}</td>
  <td></td>
</tr>
<tr style="font-weight:600;">
  <td>TOTAL con IVA</td>
  <td class="num">{fmt_eur(v2.get('total_con_iva'))}</td>
  <td></td>
</tr>"""
        tabla_caps = f"""
<table id="tbl-cap">
  <thead><tr><th>Capítulo</th><th class="num">€ sin IVA</th><th class="num">%</th></tr></thead>
  <tbody>{''.join(cap_filas)}{cap_total}</tbody>
</table>
"""
    else:
        tabla_caps = ""

    # ---- Timeline ----
    eventos = []
    for r in PRES:
        f = r.get("fecha")
        if not f: continue
        if "Planos" in r.get("oficio", ""): continue
        if r.get("archivo", "").endswith("_myp.txt"): continue
        eventos.append((f, r.get("oficio", "?"), r.get("contratista", "?"), r))
    eventos.sort()
    timeline = ['<div class="timeline">']
    for f, of, co, r in eventos:
        t = total(r)
        timeline.append(f"""
<div class="event">
  <div class="when">{f}</div>
  <div class="what"><strong>{html.escape(of)}</strong> — {html.escape(co[:40])} · {fmt_eur(t) if t else '—'}</div>
</div>""")
    timeline.append("</div>")

    # ---- Alertas ----
    alertas = [
        "Pedir a Toni que cierre las 5 partidas con '?' en el presupuesto 472 (albañilería).",
        "Pedir oferta de encimeras (DEKTON + SILESTONE) — no están en Cyss v2.0.",
        "Aceptar Paracon para electricidad (más reciente, más barato, financia en 4 hitos).",
        "Verificar que Cyss v2.0 cap. 03 (Pladur) incluye todo lo que estaba en cap. 02 de v1 (yeso, alicatado, pintura).",
        "Pedir oferta desglosada de fontanería a David Barat (limpio, sin ayudas de albañilería) para comparar con Cyss cap. 05.",
    ]
    alertas_html = f"""
<div class="alerts">
  <h3>Acciones recomendadas</h3>
  <ul>{''.join(f'<li>{a}</li>' for a in alertas)}</ul>
</div>
"""

    # ---- Nuevas secciones ----
    contexto_html = build_project_context()
    scenarios_html = build_scenarios(EXCEL, total_cyss)
    phases_html = build_phases()
    cyss_comp_html = build_cyss_comparison(v1, v2)
    dq_html = build_data_quality(PRES)
    pay_html = build_payments(PRES)

    # ---- HTML completo ----
    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reforma José María Mortés Lerma — dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap">
  <style>{CSS}</style>
</head>
<body>

<header class="top">
  <div>
    <h1>Reforma José María Mortés Lerma</h1>
    <div class="sub">C/ José María Mortes Lerma 2, 7º PTA 28 · 46018 Valencia · informe generado el {hoy}</div>
  </div>
  <div class="actions">
    <button id="theme" class="btn" title="Cambiar tema">◐ Tema</button>
    <button class="btn" onclick="window.print()" title="Imprimir o guardar como PDF">⎙ Imprimir</button>
  </div>
</header>

{contexto_html}

{kpis}

{scenarios_html}

<section>
  <h2>Por oficio</h2>
  {cards_html}
</section>

{phases_html}

{alertas_html}

{dq_html}

<section>
  <h2>Tabla global de presupuestos</h2>
  {tabla}
</section>

{cyss_comp_html}

<section>
  <h2>Comparativa visual</h2>
  <div class="chart-row">
    <div>
      <h3 style="font-family: var(--serif); font-size: 16px; margin-bottom: 8px;">% por capítulo · Cyss v2.0</h3>
      {pie}
    </div>
    <div>
      <h3 style="font-family: var(--serif); font-size: 16px; margin-bottom: 8px;">Subcontratas por oficio (cuando hay comparativa)</h3>
      {barras}
    </div>
  </div>
</section>

<section>
  <h2>Desglose de Cyss v2.0 (contratista general)</h2>
  {tabla_caps}
  <p class="meta" style="margin-top: 12px; color: var(--muted); font-size: 12px;">
    Movimientos clave desde v1: Albañilería baja de 22.700 € a 13.880 € (-39%) porque se mueve a Pladur, que sube de 4.767 € a 10.448 € (+119%). Demolición +27%. Total neto: −1.760 € (−3%).
  </p>
</section>

<section>
  <h2>Cronología de presupuestos</h2>
  {''.join(timeline)}
</section>

{pay_html}

<footer>
  <p>Documento generado automáticamente. Datos extraídos de los PDFs con <code>pdfplumber</code>. Parsers en <code>scripts/</code>. Hallazgos completos en <code>informes/</code>.</p>
  <p>Total calculado incluye IVA cuando está disponible. Cuando un PDF no muestra el total escrito, se calcula sumando las partidas (marcado en el campo "Estado" del JSON).</p>
</footer>

<script>{JS}</script>
</body>
</html>
"""
    OUT.write_text(html_doc, encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"OK -> {OUT}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
