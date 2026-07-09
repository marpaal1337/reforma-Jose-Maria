#!/usr/bin/env python3
"""Embed planos PNGs as base64 data URIs directly into index.html,
adding a professional-grade before/after image comparison viewer."""

import base64, json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(HERE, 'index.html')
PLANOS_DIR = os.path.join(HERE, 'Planos')

with open(os.path.join(PLANOS_DIR, 'estado inicial.png'), 'rb') as f:
    inicial_b64 = base64.b64encode(f.read()).decode()
with open(os.path.join(PLANOS_DIR, 'distribución.png'), 'rb') as f:
    dist_b64 = base64.b64encode(f.read()).decode()

VIEWER_HTML = f'''
<section class="collapsed">
  <h2>Planos interactivos <span class="coll-arrow"></span></h2>
  <div class="plv">
    <div class="plv-toolbar">
      <div class="plv-tabs" role="tablist">
        <button class="plv-tab active" role="tab" aria-selected="true" data-plv="inicial">Estado inicial</button>
        <button class="plv-tab" role="tab" aria-selected="false" data-plv="distribucion">Distribución</button>
        <button class="plv-tab" role="tab" aria-selected="false" data-plv="lateral">Lateral</button>
        <button class="plv-tab" role="tab" aria-selected="false" data-plv="superposicion">Superposición</button>
      </div>
      <div class="plv-toolbar-right">
        <div class="plv-opacity-group" id="plv-opacity-group" style="display:none">
          <label>Opacidad</label>
          <input type="range" id="plv-opacity" min="0" max="1" step="0.05" value="0.6">
          <span class="plv-opacity-val" id="plv-opacity-val">60%</span>
        </div>
        <div class="plv-zoom-badge" id="plv-zoom-badge">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35M11 8v6M8 11h6"/></svg>
          <span id="plv-zoom-pct">100%</span>
        </div>
      </div>
    </div>
    <div class="plv-stage" id="plv-stage">
      <div class="plv-img-wrap" id="plv-wrap-inicial">
        <img src="data:image/png;base64,{inicial_b64}" alt="Estado inicial" class="plv-img" id="plv-img-inicial" draggable="false">
      </div>
      <div class="plv-img-wrap" id="plv-wrap-dist">
        <img src="data:image/png;base64,{dist_b64}" alt="Distribución" class="plv-img" id="plv-img-dist" draggable="false">
      </div>
      <div class="plv-handle" id="plv-handle">
        <div class="plv-handle-line"></div>
        <div class="plv-handle-ring">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 6l-7 7 7 7"/>
            <path d="M8 6l7 7-7 7"/>
          </svg>
        </div>
      </div>
      <div class="plv-label plv-label-left" id="plv-label-left">Estado inicial</div>
      <div class="plv-label plv-label-right" id="plv-label-right">Distribución</div>
    </div>
    <div class="plv-footer">
      <span>Plano <em>estado inicial</em> (PEA.01) y <em>distribución</em> (PEA.02) escala 1:50. Arrastra el separador en modo Lateral.</span>
      <a href="planos.html">Visor completo &#x2197;</a>
    </div>
  </div>
</section>
'''

CSS_BLOCK = '''
.plv {
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin: 12px 0;
}
[data-theme="dark"] .plv {
  box-shadow: 0 1px 4px rgba(0,0,0,0.25);
}
.plv-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--line);
  flex-wrap: wrap;
}
.plv-tabs {
  display: flex;
  gap: 2px;
  background: var(--paper);
  padding: 3px;
  border-radius: 999px;
  border: 1px solid var(--line);
}
.plv-tab {
  background: transparent;
  color: var(--muted);
  border: none;
  padding: 5px 14px;
  font: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 999px;
  transition: background 0.2s ease, color 0.2s ease;
  white-space: nowrap;
}
.plv-tab:hover { color: var(--ink); background: rgba(128,128,128,0.08); }
.plv-tab.active { background: var(--accent); color: #fff; }
.plv-toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.plv-opacity-group {
  display: none;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
}
.plv-opacity-group label { white-space: nowrap; font-size: 11px; }
.plv-opacity-group input[type="range"] {
  width: 80px;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--line);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}
.plv-opacity-group input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}
.plv-opacity-group input[type="range"]::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}
.plv-opacity-val {
  min-width: 32px;
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
}
.plv-zoom-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--muted);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}
.plv-zoom-badge.visible { opacity: 1; }
.plv-stage {
  position: relative;
  overflow: hidden;
  background: #e8e4de;
  max-height: 75vh;
  cursor: grab;
  touch-action: none;
}
[data-theme="dark"] .plv-stage { background: #2a2723; }
.plv-stage.grabbing { cursor: grabbing; }
.plv-img-wrap {
  transform-origin: 0 0;
  line-height: 0;
  will-change: transform;
}
.plv-img {
  display: block;
  width: 100%;
  height: auto;
  user-select: none;
  -webkit-user-drag: none;
  pointer-events: none;
  transition: opacity 0.35s ease;
}
#plv-wrap-inicial { position: relative; z-index: 1; }
#plv-wrap-dist { position: absolute; top: 0; left: 0; z-index: 2; width: 100%; height: 100%; }
#plv-handle {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 28px;
  margin-left: -14px;
  z-index: 4;
  cursor: col-resize;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}
#plv-handle.visible { opacity: 1; pointer-events: auto; }
.plv-handle-line {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 2px;
  background: rgba(255,255,255,0.85);
  transform: translateX(-50%);
  box-shadow: 0 0 6px rgba(0,0,0,0.2);
}
.plv-handle-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 44px;
  height: 44px;
  background: #fff;
  border: 3px solid var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2), 0 0 0 4px rgba(255,255,255,0.25);
  color: var(--accent);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
#plv-handle:hover .plv-handle-ring { transform: translate(-50%,-50%) scale(1.08); box-shadow: 0 4px 16px rgba(0,0,0,0.28); }
#plv-handle:active .plv-handle-ring { transform: translate(-50%,-50%) scale(0.95); }
.plv-label {
  position: absolute;
  bottom: 16px;
  padding: 5px 12px;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  color: #fff;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border-radius: 5px;
  z-index: 5;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease 0.15s;
}
.plv-label.visible { opacity: 1; }
.plv-label-left { left: 16px; }
.plv-label-right { right: 16px; }
.plv-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 8px 14px;
  font-size: 12px;
  color: var(--muted);
  border-top: 1px solid var(--line);
}
.plv-footer a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  white-space: nowrap;
}
.plv-footer a:hover { text-decoration: underline; }
'''

JS_BLOCK = '''
  function initPlv() {
    var stage = document.getElementById('plv-stage');
    if (!stage) return;

    var wrapIni = document.getElementById('plv-wrap-inicial');
    var wrapDist = document.getElementById('plv-wrap-dist');
    var handle = document.getElementById('plv-handle');
    var handleRing = handle.querySelector('.plv-handle-ring');
    var opacityGroup = document.getElementById('plv-opacity-group');
    var opacitySlider = document.getElementById('plv-opacity');
    var opacityVal = document.getElementById('plv-opacity-val');
    var zoomBadge = document.getElementById('plv-zoom-badge');
    var zoomPct = document.getElementById('plv-zoom-pct');
    var labelLeft = document.getElementById('plv-label-left');
    var labelRight = document.getElementById('plv-label-right');

    var mode = 'inicial';
    var scale = 1, offX = 0, offY = 0;
    var dragging = false, hDrag = false;
    var dragAnchor = {x: 0, y: 0};
    var zoomTimer = null;

    function apply() {
      var t = 'translate(' + offX + 'px,' + offY + 'px) scale(' + scale + ')';
      wrapIni.style.transform = t;
      wrapDist.style.transform = t;
      showZoom();
    }

    function showZoom() {
      zoomPct.textContent = Math.round(scale * 100) + '%';
      zoomBadge.classList.add('visible');
      clearTimeout(zoomTimer);
      zoomTimer = setTimeout(function () { zoomBadge.classList.remove('visible'); }, 1400);
    }

    /* ---- Pan ---- */
    stage.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      dragging = true;
      dragAnchor.x = e.clientX - offX;
      dragAnchor.y = e.clientY - offY;
      stage.classList.add('grabbing');
    });
    window.addEventListener('mousemove', function (e) {
      if (dragging) {
        offX = e.clientX - dragAnchor.x;
        offY = e.clientY - dragAnchor.y;
        apply();
      }
      if (hDrag && mode === 'lateral') {
        var r = stage.getBoundingClientRect();
        var x = Math.max(0, Math.min(r.width, e.clientX - r.left));
        var pct = (x / r.width) * 100;
        wrapDist.style.clipPath = 'inset(0 ' + (100 - pct) + '% 0 0)';
        handle.style.left = pct + '%';
      }
    });
    window.addEventListener('mouseup', function () {
      dragging = false; hDrag = false;
      stage.classList.remove('grabbing');
    });

    /* ---- Zoom ---- */
    stage.addEventListener('wheel', function (e) {
      e.preventDefault();
      var d = e.deltaY > 0 ? 0.9 : 1.1;
      var ns = Math.max(0.25, Math.min(5, scale * d));
      var r = stage.getBoundingClientRect();
      var mx = e.clientX - r.left, my = e.clientY - r.top;
      offX = mx - (mx - offX) * (ns / scale);
      offY = my - (my - offY) * (ns / scale);
      scale = ns;
      apply();
    }, { passive: false });

    stage.addEventListener('dblclick', function () {
      scale = 1; offX = 0; offY = 0; apply();
    });

    /* ---- Tab switching ---- */
    document.querySelectorAll('.plv-tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        document.querySelectorAll('.plv-tab').forEach(function (t) {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
        });
        this.classList.add('active');
        this.setAttribute('aria-selected', 'true');
        mode = this.dataset.plv;

        var ini = document.getElementById('plv-img-inicial');
        var dist = document.getElementById('plv-img-dist');
        ini.style.opacity = 1;
        dist.style.opacity = 1;
        handle.classList.remove('visible');
        labelLeft.classList.remove('visible');
        labelRight.classList.remove('visible');
        wrapDist.style.clipPath = '';
        opacityGroup.style.display = 'none';

        if (mode === 'inicial') {
          dist.style.opacity = 0;
        } else if (mode === 'distribucion') {
          ini.style.opacity = 0;
        } else if (mode === 'lateral') {
          var r = stage.getBoundingClientRect();
          var pct = 50;
          wrapDist.style.clipPath = 'inset(0 50% 0 0)';
          handle.style.left = '50%';
          handle.classList.add('visible');
          labelLeft.classList.add('visible');
          labelRight.classList.add('visible');
        } else if (mode === 'superposicion') {
          opacityGroup.style.display = 'flex';
          var v = parseFloat(opacitySlider.value) || 0.6;
          ini.style.opacity = 1 - v;
          dist.style.opacity = v;
          if (opacityVal) opacityVal.textContent = Math.round(v * 100) + '%';
        }

        scale = 1; offX = 0; offY = 0; apply();
      });
    });

    /* ---- Opacity slider ---- */
    if (opacitySlider) {
      opacitySlider.addEventListener('input', function () {
        var v = parseFloat(this.value);
        if (mode === 'superposicion') {
          document.getElementById('plv-img-inicial').style.opacity = 1 - v;
          document.getElementById('plv-img-dist').style.opacity = v;
        }
        if (opacityVal) opacityVal.textContent = Math.round(v * 100) + '%';
      });
    }

    /* ---- Handle drag (mouse) ---- */
    handle.addEventListener('mousedown', function (e) {
      e.stopPropagation();
      hDrag = true;
    });

    /* ---- Touch support ---- */
    var touchData = { x: 0, y: 0 };
    stage.addEventListener('touchstart', function (e) {
      if (e.touches.length === 1) {
        touchData.x = e.touches[0].clientX - offX;
        touchData.y = e.touches[0].clientY - offY;
      }
    });
    stage.addEventListener('touchmove', function (e) {
      if (e.touches.length !== 1) return;
      var t = e.touches[0];
      if (hDrag && mode === 'lateral') {
        e.preventDefault();
        var r = stage.getBoundingClientRect();
        var x = Math.max(0, Math.min(r.width, t.clientX - r.left));
        var pct = (x / r.width) * 100;
        wrapDist.style.clipPath = 'inset(0 ' + (100 - pct) + '% 0 0)';
        handle.style.left = pct + '%';
      } else if (!hDrag) {
        e.preventDefault();
        offX = t.clientX - touchData.x;
        offY = t.clientY - touchData.y;
        apply();
      }
    }, { passive: false });
    stage.addEventListener('touchend', function () { hDrag = false; });
    handle.addEventListener('touchstart', function (e) {
      e.stopPropagation();
      hDrag = true;
    });
  }
'''

# Read current index.html
with open(INDEX, 'r', encoding='utf-8') as f:
    html = f.read()

# Remove ANY existing planos section (old or duplicate) by matching the heading
old_section = '<section class="collapsed">\n  <h2>Planos interactivos'
while True:
    idx = html.find(old_section)
    if idx < 0:
        break
    end = html.find('</section>', idx)
    html = html[:idx] + html[end + 11:]

# Remove old plv CSS (exact match of the old block)
old_css = [
    '.plv { margin: 8px 0; }',
    '.plv-tabs { display:flex; gap:4px; margin-bottom:8px; flex-wrap:wrap; align-items:center; }',
    '.plv-tab { background:var(--paper-2); color:var(--ink); border:1px solid var(--line); padding:4px 12px; font:inherit; font-size:12px; cursor:pointer; border-radius:2px; }',
    '.plv-tab.active { background:var(--accent); color:#fff; border-color:var(--accent); }',
    '.plv-opacity { display:inline-flex; align-items:center; gap:6px; font-size:11px; color:var(--muted); margin-left:auto; }',
    '.plv-opacity input[type="range"] { width:80px; accent-color:var(--accent); }',
    '.plv-stage { position:relative; overflow:hidden; background:var(--paper-2); border:1px solid var(--line); border-radius:2px; max-height:70vh; cursor:grab; }',
    '.plv-stage:active { cursor:grabbing; }',
    '.plv-img-wrap { line-height:0; }',
    '.plv-img { display:block; max-width:100%; height:auto; user-select:none; -webkit-user-drag:none; }',
    '#plv-wrap-inicial { position:relative; z-index:1; }',
    '#plv-wrap-dist { position:absolute; top:0; left:0; z-index:2; }',
    '#plv-handle { position:absolute; top:0; bottom:0; width:4px; background:var(--accent); z-index:3; cursor:col-resize; display:none; margin-left:-2px; }',
    '#plv-handle::after { content:\'\'; position:absolute; top:50%; left:50%; width:20px; height:20px; background:var(--accent); border-radius:50%; transform:translate(-50%,-50%); }',
]
old_css_block = '\n'.join(old_css)
if old_css_block in html:
    html = html.replace(old_css_block + '\n', '')

# Remove old initPlv JS function
old_js_marker = '  // ---- Embedded planos viewer ----'
idx = html.find(old_js_marker)
if idx >= 0:
    end = html.find('  // ---- Init ----', idx)
    if end < 0:
        end = html.find('    function runInit()', idx)
    html = html[:idx] + html[end:]

# Inject new planos viewer after checklist (before escenarios)
marker = '</section>\n\n<section>\n  <h2>Escenarios económicos</h2>'
html = html.replace(marker, VIEWER_HTML + '\n' + marker)

# Inject new CSS (before @media print)
css_marker = '@media print {'
html = html.replace(css_marker, CSS_BLOCK + '\n' + css_marker)

# Inject new JS (before initDownloads call, after initChecklist)
js_marker = '    initDownloads();'
if 'initPlv();' not in html:
    html = html.replace(js_marker, js_marker + '\n    initPlv();')

# Inject new JS function (before runInit)
func_marker = '    function runInit() {'
if JS_BLOCK not in html:
    html = html.replace(func_marker, JS_BLOCK + '\n  ' + func_marker)

with open(INDEX, 'w', encoding='utf-8') as f:
    f.write(html)

# Also write the base64 JSON for reference
with open(os.path.join(HERE, 'data', 'planos_b64.json'), 'w') as f:
    json.dump({'estado inicial': inicial_b64, 'distribución': dist_b64}, f)

print('Done. index.html updated with embedded planos viewer.')
print(f'estado inicial: {len(inicial_b64)} chars base64')
print(f'distribución: {len(dist_b64)} chars base64')
