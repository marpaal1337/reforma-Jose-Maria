#!/usr/bin/env python3
"""Build the interactive tabbed dashboard from existing index.html + new reports."""

import os, json, re, base64

BASE = "/home/mpalaciosa/dev/reforma-Jose-Maria"

# ── Read existing index.html ──
with open(f"{BASE}/index.html", "r", encoding="utf-8") as f:
    ORIG = f.read()

# ── Read presupuestos.json for data ──
with open(f"{BASE}/data/presupuestos.json", "r", encoding="utf-8") as f:
    PRESUPUESTOS = json.load(f)

# ── Read new reports ──
report_texts = {}
reports_dir = f"{BASE}/informes"
for fname in sorted(os.listdir(reports_dir)):
    if fname.endswith(".md") and not fname.startswith("."):
        with open(f"{reports_dir}/{fname}", "r", encoding="utf-8") as f:
            report_texts[fname] = f.read()

# ── Extract existing body content sections ──
# We need to preserve the core: header, kpis, sections, tables, js, svg, images
# Strategy: extract the key building blocks from ORIG and reassemble

# Extract everything between <style> and </html> (CSS + HTML + JS)
style_start = ORIG.find("<style>")
style_end = ORIG.find("</style>", style_start) + 8
existing_css = ORIG[style_start:style_end]

# Extract JS (everything between last <script> and </html>)
script_start = ORIG.rfind("<script>")
script_end = ORIG.rfind("</script>")
existing_js = ORIG[script_start:script_end + 9]

# Extract the body content
body_start = ORIG.find("<header", ORIG.find("<body"))
body_end = ORIG.rfind("</body>")
body_html = ORIG[body_start:body_end]

# ── Build sidebar HTML ──
SIDEBAR = '''<nav id="sidebar" role="navigation">
  <div class="sb-brand">
    <div class="sb-logo">R</div>
    <div class="sb-title">Reforma</div>
    <div class="sb-sub">J.M. Mortés</div>
  </div>
  <div class="sb-nav">
    <button class="sb-btn active" data-module="dashboard" title="Dashboard">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
      <span>Dashboard</span>
    </button>
    <button class="sb-btn" data-module="presupuestos" title="Presupuestos">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
      <span>Presupuestos</span>
    </button>
    <button class="sb-btn" data-module="comparativas" title="Comparativas">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
      <span>Comparativas</span>
    </button>
    <button class="sb-btn" data-module="planos" title="Planos">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
      <span>Planos</span>
    </button>
    <button class="sb-btn" data-module="escenarios" title="Escenarios">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
      <span>Escenarios</span>
    </button>
    <button class="sb-btn" data-module="fases" title="Fases">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
      <span>Fases</span>
    </button>
    <button class="sb-btn" data-module="calidad" title="Calidad">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      <span>Calidad</span>
    </button>
    <button class="sb-btn" data-module="documentacion" title="Documentación">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
      <span>Docs</span>
    </button>
  </div>
  <div class="sb-footer">
    <button class="sb-btn" id="theme-btn" title="Tema">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      <span>Tema</span>
    </button>
  </div>
</nav>
'''

# ── Build modules from existing sections ──
# Section 1: Dashboard (header + kpis + contexto + checklist + alerts)
# Section 2: Presupuestos (trade cards + table)
# etc.

# Extract the header + kpis + proyecto section
def extract_section(start_marker, end_marker=None):
    s = body_html.find(start_marker)
    if s == -1:
        return ""
    if end_marker:
        e = body_html.find(end_marker, s)
        if e == -1:
            return body_html[s:]
        return body_html[s:e]
    return body_html[s:]

# Let's build the modules
# 1. Dashboard
dashboard_sections = []
# Header
hs = body_html.find("<header")
he = body_html.find("</header>", hs) + 9
dashboard_sections.append(body_html[hs:he])
# KPI
ks = body_html.find('<div class="kpis">')
ke = body_html.find('</div>', ks)
ke = body_html.find('</div>', ke + 5) + 6
dashboard_sections.append(body_html[ks:ke])
# Proyecto section
ps = body_html.find('<section>', ke)
pe = body_html.find('</section>', ps) + 10
dashboard_sections.append(body_html[ps:pe])
# Checklist + alerts
cs = body_html.find('Checklist')
ce = body_html.find('</section>', cs) + 10
dashboard_sections.append(body_html[cs:ce])
# Alerts
al = body_html.find('<div class="alerts"')
ae = body_html.find('</div>', al)
ae = body_html.find('</div>', ae + 5) + 6
dashboard_sections.append(body_html[al:ae])
# Datos abiertos section
ds = body_html.find('Datos abiertos')
de = body_html.find('</section>', ds) + 10
dashboard_sections.append(body_html[ds:de])

DASHBOARD_HTML = '\n'.join(dashboard_sections)

# 2. Presupuestos: Por oficio section + Tabla global
ps = body_html.find('Por oficio')
pe = body_html.find('</section>', ps) + 10
TRADE_CARDS = body_html[ps:pe]

# Full table section
ts = body_html.find('id="tbl-main"')
# Find the section containing this table
ts_section = body_html.rfind('<section', 0, ts)
te_section = body_html.find('</section>', ts) + 10
FULL_TABLE = body_html[ts_section:te_section]

# Cyss comparison section
cyss_start = body_html.find('Cyss v1 vs v2')
cyss_end = body_html.find('</section>', cyss_start) + 10
CYSS_COMP = body_html[cyss_start:cyss_end]

# Visual charts section
vs_start = body_html.find('Comparativa visual')
vs_end = body_html.find('</section>', vs_start) + 10
VISUAL_CHARTS = body_html[vs_start:vs_end]

# Cyss breakdown section
cyss2_start = body_html.find('Desglose de Cyss v2.0')
cyss2_end = body_html.find('</section>', cyss2_start) + 10
CYSS_BREAKDOWN = body_html[cyss2_start:cyss2_end]

PRESUPUESTOS_HTML = TRADE_CARDS + '\n' + FULL_TABLE

COMPARATIVAS_HTML = CYSS_COMP + '\n' + VISUAL_CHARTS + '\n' + CYSS_BREAKDOWN

# 3. Planos section
plv_start = body_html.find('id="plv-stage"')
plv_section_start = body_html.rfind('<section', 0, plv_start)
plv_section_end = body_html.find('</section>', plv_section_start) + 10
PLANOS_HTML = body_html[plv_section_start:plv_section_end]

# 4. Escenarios section
esc_start = body_html.find('Escenarios económicos')
esc_end = body_html.find('</section>', esc_start) + 10
ESCENARIOS_HTML = body_html[esc_start:esc_end]

# 5. Fases section
fas_start = body_html.find('Fases de ejecución')
fas_end = body_html.find('</section>', fas_start) + 10
FASES_HTML = body_html[fas_start:fas_end]

# ── New CALIDAD module content ──
CALIDAD_HTML = '''<section><h2>🔍 Control de Calidad — Plan de Inspección</h2>
<div class="module-intro">Resumen ejecutivo de los informes de Arquitecto Técnico y Director de Ejecución. 90+ puntos de control, 7 checklists de materiales, y protocolo de pruebas finales.</div>
<div class="calidad-grid">
<div class="calidad-card">
  <h3>⚠ Hallazgos críticos del Aparejador</h3>
  <ul>
    <li><strong>Capa faltante más grave:</strong> Base de mortero ligero bajo pavimento eliminada en Cyss v2.0 — 1.413 € no presupuestados</li>
    <li><strong>Comodines más urgentes:</strong> Casoneto (3.780 vs 90 €) y Picado pilar (2.400 vs 220 €) en presupuesto Toni</li>
    <li><strong>Material sin especificar:</strong> Pavimento, azulejo, ventanas, herrajes — sin marca ni modelo en varios presupuestos</li>
    <li><strong>Adhesivo C1:</strong> Insuficiente para formato 60×120; mínimo C2 recomendado</li>
  </ul>
</div>
<div class="calidad-card">
  <h3>✅ Sistemas constructivos</h3>
  <ul>
    <li><strong>Tabiquería pladur:</strong> Alta calidad, 2+1 placas con lana mineral (55-58 dB aislamiento)</li>
    <li><strong>Climatización:</strong> Mitsubishi — equipo de primera calidad</li>
    <li><strong>Impermeabilización de balcón:</strong> Pendiente de verificar en presupuesto</li>
  </ul>
</div>
<div class="calidad-card">
  <h3>📋 No Conformidades</h3>
  <table>
    <tr><th>NC</th><th>Descripción</th><th>Gravedad</th><th>Acción</th></tr>
    <tr><td>NC-01</td><td>Partidas con '?' en Toni 472</td><td class="tag warn">Alta</td><td>Solicitar desglose antes de firmar</td></tr>
    <tr><td>NC-02</td><td>Encimeras no presupuestadas en Cyss</td><td class="tag warn">Alta</td><td>Solicitar oferta a marmolista</td></tr>
    <tr><td>NC-03</td><td>Base niveladora pavimento eliminada v2.0</td><td class="tag warn">Alta</td><td>Confirmar con Cyss</td></tr>
    <tr><td>NC-04</td><td>Valenzuela sin fecha de validez</td><td class="tag">Baja</td><td>Confirmar precio vigente</td></tr>
    <tr><td>NC-05</td><td>Adhesivo C1 vs C2 para 60×120</td><td class="tag">Media</td><td>Especificar C2 en pedido</td></tr>
  </table>
</div>
<div class="calidad-card">
  <h3>🔬 Puntos de Inspección por Fase</h3>
  <table>
    <tr><th>Fase</th><th>Control</th><th>Criterio</th></tr>
    <tr><td>Demolición</td><td>Replanteo de huecos</td><td>Coincide con planos</td></tr>
    <tr><td>Albañilería</td><td>Tabiquería</td><td>Planeidad ±3 mm en 2 m</td></tr>
    <tr><td>Fontanería</td><td>Prueba presión</td><td>6 bar ≥ 30 min sin pérdida</td></tr>
    <tr><td>Electricidad</td><td>Aislamiento</td><td>&gt; 1 MΩ</td></tr>
    <tr><td>Pladur</td><td>Estructura metálica</td><td>Separación ≤ 60 cm</td></tr>
    <tr><td>Pavimentos</td><td>Juntas y nivelación</td><td>±2 mm en 2 m</td></tr>
    <tr><td>Carpintería</td><td>Holguras y ajustes</td><td>&lt; 3 mm</td></tr>
  </table>
</div>
<div class="calidad-card">
  <h3>🧪 Protocolo Pruebas Finales</h3>
  <ul>
    <li>Estanqueidad de ventanas</li>
    <li>Presión y caudal fontanería (todos los puntos)</li>
    <li>Eléctrica: diferenciales, toma de tierra, todos los enchufes</li>
    <li>Climatización: temperatura por estancia</li>
    <li>Cocina: electrodomésticos, encimera, campana</li>
    <li>Baños: desagües, cisternas, grifería</li>
    <li>Carpintería: apertura/cierre de puertas y armarios</li>
  </ul>
</div>
<div class="calidad-card">
  <h3>📦 Checklist Recepción de Materiales</h3>
  <table>
    <tr><th>Material</th><th>Proveedor</th><th>Verificar</th></tr>
    <tr><td>Ventanas</td><td>Nacher</td><td>Modelo SOFIA, cotas, color, herrajes</td></tr>
    <tr><td>Cocina</td><td>Valenzuela</td><td>Muebles, encimera, electrodomésticos</td></tr>
    <tr><td>Armarios</td><td>Valenzuela</td><td>Mediciones, puertas, guías, cajones</td></tr>
    <tr><td>Puertas</td><td>Valenzuela</td><td>Bloque, manetas, condena</td></tr>
    <tr><td>Pavimento</td><td>Cyss</td><td>Formato, lote, cantidad, sin fisuras</td></tr>
    <tr><td>Encimeras</td><td>Pendiente</td><td>DEKTON Marmorio, SILESTONE</td></tr>
  </table>
</div>
</div>
</section>
'''

# ── New DOCUMENTACIÓN module content ──
def md_to_html(md_text):
    """Quick markdown to HTML conversion for summaries."""
    html = md_text
    # Headers
    html = re.sub(r'^### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    # Lists
    html = re.sub(r'^\- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^\* (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    # Tables (simple)
    html = re.sub(r'\|(.+)\|', lambda m: '<tr>' + ''.join(f'<td>{c.strip()}</td>' for c in m.group(1).split('|')) + '</tr>', html)
    # Paragraphs
    html = re.sub(r'\n\n', r'</p><p>', html)
    html = f'<p>{html}</p>'
    # Clean up
    html = html.replace('</p><p><h', '<h').replace('</h', '</h')
    return html

DOCS_HTML = '''<section><h2>📚 Documentación del Proyecto</h2>
<div class="module-intro">20 informes generados por 5 roles profesionales. Todos los archivos están en <code>informes/</code>.</div>
<div class="docs-grid">
'''

# List all reports
for fname in sorted(report_texts.keys()):
    if fname.endswith(".md"):
        size = len(report_texts[fname])
        # Extract first meaningful line as description
        lines = report_texts[fname].split('\n')
        desc = ''
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('_') and not line.startswith('-') and len(line) > 20:
                desc = line[:200]
                break
        if not desc:
            desc = f"Informe de {fname.replace('_', ' ').replace('.md', '')}"
        
        DOCS_HTML += f'''<div class="doc-card">
  <div class="doc-icon">📄</div>
  <div class="doc-info">
    <h3>{fname.replace('.md', '').replace('_', ' / ')}</h3>
    <p>{desc}{'...' if len(desc) >= 200 else ''}</p>
    <span class="doc-meta">{size // 1000} KB</span>
  </div>
</div>
'''

DOCS_HTML += '''
</div>

<h2>📋 Informes Previos</h2>
<div class="docs-grid">
'''

# Legacy reports (non-role-specific)
for fname in sorted(report_texts.keys()):
    if not any(fname.startswith(p) for p in ['ARQUITECTO', 'APAREJADOR', 'PM_', 'ANALISTA', 'DO_']):
        size = len(report_texts[fname])
        lines = report_texts[fname].split('\n')
        desc = ''
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('_') and len(line) > 20:
                desc = line[:200]
                break
        DOCS_HTML += f'''<div class="doc-card">
  <div class="doc-icon">📋</div>
  <div class="doc-info">
    <h3>{fname.replace('.md', '').replace('_', ' / ')}</h3>
    <p>{desc}{'...' if len(desc) >= 200 else ''}</p>
    <span class="doc-meta">{size // 1000} KB</span>
  </div>
</div>
'''

DOCS_HTML += '</div></section>'

# ── New sidebar CSS ──
SIDEBAR_CSS = '''
/* ════════════════════════════════════════════
   SIDEBAR + MODULE LAYOUT
   ════════════════════════════════════════════ */
html, body { 
  margin: 0; padding: 0; min-height: 100vh; overflow: hidden;
  font-family: var(--sans); font-size: 15px; line-height: 1.5; 
  background: var(--paper); color: var(--ink); 
}
body { display: flex; }

/* Sidebar */
#sidebar {
  width: 64px; min-width: 64px; height: 100vh;
  display: flex; flex-direction: column;
  background: var(--paper-2); border-right: 1px solid var(--line);
  z-index: 100; overflow: hidden; position: fixed; left: 0; top: 0;
}
.sb-brand {
  padding: 12px 0; text-align: center; border-bottom: 1px solid var(--line);
}
.sb-logo {
  width: 32px; height: 32px; margin: 0 auto 4px;
  background: var(--accent); color: var(--paper);
  border-radius: 6px; font-family: var(--serif); font-size: 18px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.sb-title { font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }
.sb-sub { font-size: 8px; color: var(--muted); }
.sb-nav { flex: 1; display: flex; flex-direction: column; gap: 2px; padding: 8px 4px; overflow-y: auto; }
.sb-footer { border-top: 1px solid var(--line); padding: 4px; }
.sb-btn {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  background: none; border: none; color: var(--muted); cursor: pointer;
  padding: 8px 4px; border-radius: 6px; font-size: 9px; transition: all .15s;
  font-family: inherit; width: 100%;
}
.sb-btn:hover { background: var(--line); color: var(--ink); }
.sb-btn.active { background: var(--accent); color: var(--paper); }
.sb-btn.active svg { stroke: var(--paper); }
.sb-btn span { white-space: nowrap; }

/* Main content area */
#main {
  margin-left: 64px; width: calc(100vw - 64px); height: 100vh;
  overflow: hidden; position: relative;
}
.module {
  display: none; width: 100%; height: 100vh; overflow-y: auto;
  padding: 28px 32px 48px;
}
.module.active { display: block; }

/* Module headers */
.module > section > h2:first-child {
  font-family: var(--serif); font-size: 24px; font-weight: 600;
  border-bottom: 2px solid var(--ink);
  padding-bottom: 12px; margin-bottom: 20px; margin-top: 0;
}
.module-intro {
  background: var(--paper-2); border: 1px solid var(--line);
  padding: 12px 16px; border-radius: 4px; margin-bottom: 24px;
  font-size: 14px; color: var(--ink-2);
}

/* Dashboard KPIs */
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.kpi { background: var(--paper-2); border: 1px solid var(--line); padding: 14px 16px; border-radius: 4px; }
.kpi .label { font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
.kpi .value { font-family: var(--serif); font-size: 24px; font-variant-numeric: tabular-nums; }
.kpi .delta { font-size: 11px; color: var(--muted); }

/* Cards grid */
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; }
.card { background: var(--paper-2); border: 1px solid var(--line); padding: 14px 16px; border-radius: 4px; }

/* Tables */
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--line); background: var(--paper); }
th { background: var(--paper-2); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .04em; cursor: pointer; user-select: none; }
th:hover { background: var(--line); }

/* Tags */
.tag { display: inline-block; padding: 2px 6px; border-radius: 2px; font-size: 10px; font-weight: 500; }
.tag.warn { background: var(--warn); color: var(--paper); }

/* Alerts */
.alerts { background: var(--paper-2); border: 1px solid var(--line); padding: 16px; border-radius: 4px; margin: 16px 0; }
.alerts h3 { font-family: var(--serif); font-size: 16px; margin-bottom: 8px; }
.alerts ul { padding-left: 20px; }
.alerts li { margin-bottom: 4px; }

/* Planos viewer preserved */
.plv { display: flex; flex-direction: column; height: calc(100vh - 120px); }
.plv-stage { flex: 1; position: relative; overflow: hidden; background: var(--paper-2); border: 1px solid var(--line); }
.plv-toolbar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 8px; }
.plv-tabs { display: flex; gap: 4px; }
.plv-tab { padding: 6px 14px; font-size: 12px; border: 1px solid var(--line); background: var(--paper); cursor: pointer; border-radius: 4px; }
.plv-tab.active { background: var(--accent); color: var(--paper); border-color: var(--accent); }

/* Calidad grid */
.calidad-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; }
.calidad-card { background: var(--paper-2); border: 1px solid var(--line); padding: 16px; border-radius: 4px; }
.calidad-card h3 { font-family: var(--serif); font-size: 15px; margin-bottom: 10px; }
.calidad-card ul { padding-left: 18px; }
.calidad-card li { margin-bottom: 4px; font-size: 13px; }
.calidad-card table { font-size: 11px; }

/* Doc grid */
.docs-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; margin-bottom: 24px; }
.doc-card { display: flex; gap: 12px; background: var(--paper-2); border: 1px solid var(--line); padding: 12px 14px; border-radius: 4px; cursor: pointer; }
.doc-card:hover { border-color: var(--accent); }
.doc-icon { font-size: 24px; flex-shrink: 0; }
.doc-info h3 { font-family: var(--serif); font-size: 13px; margin-bottom: 4px; }
.doc-info p { font-size: 12px; color: var(--ink-2); margin-bottom: 4px; }
.doc-meta { font-size: 10px; color: var(--muted); }

/* Controls */
.controls { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.controls input, .controls select { background: var(--paper); border: 1px solid var(--line); padding: 5px 8px; font: inherit; font-size: 12px; border-radius: 4px; color: var(--ink); }

/* Planos overrides from original */
.plv-img-wrap { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
.plv-img-wrap img { width: 100%; height: 100%; object-fit: contain; }

/* Responsive */
@media (max-width: 768px) {
  #sidebar { width: 48px; min-width: 48px; }
  .sb-btn span { display: none; }
  #main { margin-left: 48px; width: calc(100vw - 48px); }
  .module { padding: 16px; }
  .kpis { grid-template-columns: 1fr 1fr; }
  .calidad-grid { grid-template-columns: 1fr; }
}
'''

# ── Tab switching JS ──
TAB_JS = '''
// ── Tab Navigation ──
(function() {
  var modules = document.querySelectorAll('.module');
  var sidebarBtns = document.querySelectorAll('.sb-btn[data-module]');
  
  function switchModule(name) {
    modules.forEach(function(m) { m.classList.remove('active'); });
    var target = document.querySelector('.module[data-module="' + name + '"]');
    if (target) target.classList.add('active');
    
    sidebarBtns.forEach(function(b) { b.classList.remove('active'); });
    var btn = document.querySelector('.sb-btn[data-module="' + name + '"]');
    if (btn) btn.classList.add('active');
  }
  
  sidebarBtns.forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      switchModule(this.getAttribute('data-module'));
    });
  });
  
  // Theme toggle
  document.getElementById('theme-btn').addEventListener('click', function() {
    var html = document.documentElement;
    var isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? '' : 'dark');
    localStorage.setItem('theme', isDark ? '' : 'dark');
  });
  
  // Restore theme
  var saved = localStorage.getItem('theme');
  if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
})();
'''

# ── Build the new HTML ──
NEW_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reforma José María Mortés Lerma — Dashboard Completo</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
%(existing_css)s
%(sidebar_css)s
  </style>
</head>
<body>
%(sidebar)s

<div id="main">
  <div class="module active" data-module="dashboard">
%(dashboard)s
  </div>

  <div class="module" data-module="presupuestos">
    <section><h2>📋 Presupuestos</h2><div class="module-intro">Comparativa global de todos los oficios y tabla detallada con 27+ registros.</div></section>
%(presupuestos)s
  </div>

  <div class="module" data-module="comparativas">
    <section><h2>🔍 Comparativas</h2><div class="module-intro">Comparativa Cyss v1 vs v2.0, desglose por capítulo, y gráficos comparativos visuales.</div></section>
%(comparativas)s
  </div>

  <div class="module" data-module="planos">
    <section><h2>📐 Planos Interactivos</h2><div class="module-intro">Comparativa visual entre estado inicial y distribución reformada. Arrastra el separador en modo Lateral.</div></section>
%(planos)s
  </div>

  <div class="module" data-module="escenarios">
    <section><h2>💰 Escenarios Económicos</h2><div class="module-intro">Tres escenarios: Cyss completo, híbrido, y autogestión. Incluye costes ocultos (electrodomésticos, licencias, tasas).</div></section>
%(escenarios)s
  </div>

  <div class="module" data-module="fases">
    <section><h2>📅 Fases de Ejecución</h2><div class="module-intro">Planificación detallada con 12 fases, ruta crítica, hitos de pago y análisis de riesgos.</div></section>
%(fases)s
  </div>

  <div class="module" data-module="calidad">
%(calidad)s
  </div>

  <div class="module" data-module="documentacion">
%(documentacion)s
  </div>
</div>

<script>
%(existing_js)s

%(tab_js)s
</script>
</body>
</html>
'''

# Fill template
html = NEW_HTML % {
    'existing_css': existing_css,
    'sidebar_css': SIDEBAR_CSS,
    'sidebar': SIDEBAR,
    'dashboard': DASHBOARD_HTML,
    'presupuestos': PRESUPUESTOS_HTML,
    'comparativas': COMPARATIVAS_HTML,
    'planos': PLANOS_HTML,
    'escenarios': ESCENARIOS_HTML,
    'fases': FASES_HTML,
    'calidad': CALIDAD_HTML,
    'documentacion': DOCS_HTML,
    'existing_js': existing_js,
    'tab_js': TAB_JS,
}

# Write output
out_path = f"{BASE}/index.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"✅ Written {out_path} ({len(html)} bytes)")
