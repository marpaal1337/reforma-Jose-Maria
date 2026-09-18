#!/usr/bin/env python3
"""
Genera render3d.html: visor 3D autocontenido (Three.js incluido, sin build)
a partir de data/planos3d.json, data/imagenes/planta_textura.jpg,
data/mobiliario.glb y data/texturas/*.jpg.

Requiere: libs/three.min.js y libs/GLTFLoader.js (ver AGENTS.md)

Uso:
    python3 scripts/generar_visor3d.py            # autocontenido (base64)
    python3 scripts/generar_visor3d.py --no-embed # carga data/mobiliario.glb
                                                  # (requiere servidor local: file:// bloquea fetch/CORS)
"""
from __future__ import annotations

import base64
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "render3d.html"
THREE = ROOT / "libs" / "three.min.js"
GLTF = ROOT / "libs" / "GLTFLoader.js"
GLB = DATA / "mobiliario.glb"
EMBED = "--no-embed" not in sys.argv

PLAN = json.loads((DATA / "planos3d.json").read_text(encoding="utf-8"))
TEX_B64 = base64.b64encode((DATA / "imagenes" / "planta_textura.jpg").read_bytes()).decode("ascii")

# texturas de acabados que usa la geometría del visor (muros y suelos)
TEXTURAS_VISOR = ("suelo_madera", "azulejo", "terraza", "muro")


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


if not THREE.exists():
    raise SystemExit("Falta libs/three.min.js (ver AGENTS.md: cómo regenerar el visor 3D)")
if not GLTF.exists():
    raise SystemExit("Falta libs/GLTFLoader.js (descargar de three r147, ver AGENTS.md)")

TEXTURAS_JS = {
    n: ("data:image/jpeg;base64," + b64(DATA / "texturas" / f"{n}.jpg")) if EMBED
       else f"data/texturas/{n}.jpg"
    for n in TEXTURAS_VISOR if (DATA / "texturas" / f"{n}.jpg").exists()
}
MOB_B64 = b64(GLB) if (GLB.exists() and EMBED) else ""
MOB_SRC = "" if EMBED else "data/mobiliario.glb"

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Render 3D · Reforma José María Mortés Lerma</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Modelo 3D interactivo de la reforma, generado automáticamente del plano de distribución PE.A.02 (SOFIA PALACIOS arquitectura).">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --paper:#FAF7F2; --paper-2:#F5F1EA; --ink:#1A1A1A; --ink-2:#3D3D3D;
  --muted:#6B6B6B; --line:#E0DAD0; --accent:#B5651D; --accent-2:#8C4D14;
  --good:#4A6B2E; --panel:rgba(250,247,242,.86); --shadow:0 18px 50px -18px rgba(40,32,24,.35);
  --serif:'Source Serif 4',Georgia,'Times New Roman',serif;
  --sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
}
*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;font-family:var(--sans);color:var(--ink);background:
    radial-gradient(120% 90% at 78% 8%, #FFFDF8 0%, #F6F2EA 42%, #EAE4D6 100%);
  overflow:hidden;-webkit-font-smoothing:antialiased;
}
#app{position:fixed;inset:0}
canvas{display:block;touch-action:none}
.micro{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.num{font-family:var(--serif);font-variant-numeric:tabular-nums}

/* ── cabecera ── */
header{
  position:absolute;top:0;left:0;right:0;display:flex;justify-content:space-between;
  align-items:flex-start;padding:18px 20px;pointer-events:none;z-index:20;gap:12px;
}
.title-block{pointer-events:auto;max-width:52ch}
.title-block .eyebrow{display:flex;align-items:center;gap:8px}
.title-block .eyebrow::before{content:"";width:22px;height:1px;background:var(--accent)}
h1{
  font-family:var(--serif);font-weight:600;font-size:clamp(19px,2.4vw,27px);
  line-height:1.12;margin:6px 0 4px;letter-spacing:-.01em;
}
.title-block p{margin:0;font-size:12px;color:var(--muted)}
.title-block p b{color:var(--ink-2);font-weight:500}
.toolbar{display:flex;gap:8px;align-items:center;pointer-events:auto;flex-wrap:wrap;justify-content:flex-end}
.seg{display:flex;background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:3px;box-shadow:var(--shadow);backdrop-filter:blur(10px)}
.seg button{
  border:0;background:transparent;font:600 11.5px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;
  color:var(--muted);padding:8px 14px;border-radius:999px;cursor:pointer;transition:.25s;
}
.seg button[aria-pressed="true"]{background:var(--ink);color:#fff}
.btn{
  display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line);background:var(--panel);
  color:var(--ink-2);font:600 11.5px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;
  padding:9px 13px;border-radius:999px;cursor:pointer;box-shadow:var(--shadow);backdrop-filter:blur(10px);
  transition:.25s;white-space:nowrap;
}
.btn:hover{border-color:var(--accent);color:var(--accent-2)}
.btn[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:#fff}
.btn svg{width:13px;height:13px;flex:none}

/* ── panel lateral ── */
aside{
  position:absolute;top:96px;left:20px;width:270px;z-index:18;
  background:var(--panel);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);
  backdrop-filter:blur(12px);overflow:hidden;transition:transform .45s cubic-bezier(.22,.8,.28,1),opacity .3s;
}
aside.hidden{transform:translateX(-118%);opacity:0}
.panel-head{display:flex;justify-content:space-between;align-items:center;padding:14px 16px 10px;border-bottom:1px solid var(--line)}
.panel-head h2{font-family:var(--serif);font-size:15px;margin:0;font-weight:600}
.panel-scroll{max-height:min(52vh,520px);overflow:auto;overscroll-behavior:contain}
.ctl{padding:12px 16px;border-bottom:1px solid var(--line)}
.ctl label{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:7px}
.ctl output{font-family:var(--serif);font-size:13px;color:var(--accent-2);text-transform:none;letter-spacing:0}
input[type=range]{width:100%;accent-color:var(--accent);height:18px}
.rooms{list-style:none;margin:0;padding:6px}
.rooms button{
  width:100%;display:grid;grid-template-columns:14px 1fr auto;gap:10px;align-items:center;
  background:transparent;border:0;border-radius:10px;padding:8px 9px;cursor:pointer;text-align:left;
  font:500 12.5px/1.25 var(--sans);color:var(--ink-2);transition:.18s;
}
.rooms button:hover,.rooms button:focus-visible{background:rgba(181,101,29,.09);outline:none}
.rooms button[aria-current="true"]{background:var(--ink);color:#fff}
.rooms button[aria-current="true"] .m2{color:#EDE6DA}
.swatch{width:12px;height:12px;border-radius:4px;border:1px solid rgba(0,0,0,.12)}
.m2{font-family:var(--serif);font-size:12.5px;color:var(--muted);white-space:nowrap}
.panel-foot{padding:10px 16px 14px;display:flex;justify-content:space-between;gap:8px}
.panel-foot .micro{text-transform:none;letter-spacing:.02em;font-weight:500}
.panel-foot .total{font-family:var(--serif);font-size:13px}

/* ── ficha de estancia ── */
#card{
  position:absolute;right:20px;top:96px;width:264px;z-index:19;
  background:var(--panel);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);
  backdrop-filter:blur(12px);padding:16px 18px 18px;transform:translateY(-8px);opacity:0;pointer-events:none;
  transition:.32s cubic-bezier(.22,.8,.28,1);
}
#card.show{transform:none;opacity:1;pointer-events:auto}
#card .close{position:absolute;top:10px;right:10px;border:0;background:transparent;cursor:pointer;color:var(--muted);font-size:16px;line-height:1;padding:6px}
#card .close:hover{color:var(--accent-2)}
#card .swatch-lg{width:26px;height:26px;border-radius:8px;border:1px solid rgba(0,0,0,.12);margin-bottom:10px}
#card h3{font-family:var(--serif);font-size:19px;margin:0 0 2px;font-weight:600}
#card .sub{font-size:11.5px;color:var(--muted);margin-bottom:14px}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px 12px;border-top:1px solid var(--line);padding-top:12px}
.stats div span{display:block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:3px}
.stats div b{font-family:var(--serif);font-weight:600;font-size:16px}
#card .note{margin:12px 0 0;font-size:10.5px;line-height:1.5;color:var(--muted)}
#card .render{display:none;margin:0 0 12px;border:1px solid var(--line);border-radius:10px;overflow:hidden}
#card .render img{display:block;width:100%;height:124px;object-fit:cover}
#card .render figcaption{font-size:10px;color:var(--muted);padding:5px 8px;background:rgba(0,0,0,.025)}
.thumbs{display:none;gap:6px;margin:0 0 12px}
.thumbs.on{display:flex}
.thumbs button{width:58px;height:35px;padding:0;border:1px solid var(--line);border-radius:7px;overflow:hidden;background:none;cursor:pointer;transition:.2s}
.thumbs button img{width:100%;height:100%;object-fit:cover;display:block;opacity:.7}
.thumbs button[aria-pressed="true"]{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
.thumbs button[aria-pressed="true"] img{opacity:1}

#galeria{position:fixed;inset:0;z-index:60;overflow:auto;padding:76px 24px 48px;
  background:rgba(26,24,20,.88);backdrop-filter:blur(7px)}
#galeria[hidden]{display:none}
#galeria .gal-head{position:fixed;top:0;left:0;right:0;display:flex;justify-content:space-between;
  align-items:center;padding:16px 22px;color:#F5F1EA;background:linear-gradient(rgba(20,18,15,.75),transparent)}
#galeria h2{font-family:var(--serif);font-size:21px;margin:0;font-weight:600}
#galeria .gal-sub{font-size:11px;color:#C9BFAD;margin-top:2px}
#galeria .close{border:1px solid rgba(245,241,234,.35);background:transparent;color:#F5F1EA;
  width:34px;height:34px;border-radius:50%;cursor:pointer;font-size:15px}
#galeria .close:hover{background:rgba(245,241,234,.12)}
#galeria .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;max-width:1180px;margin:0 auto}
#galeria figure{margin:0;background:var(--paper);border-radius:12px;overflow:hidden;cursor:zoom-in;
  box-shadow:0 18px 44px -20px rgba(0,0,0,.6);transition:transform .3s}
#galeria figure:hover{transform:translateY(-3px)}
#galeria figure.zoom{grid-column:1/-1;cursor:zoom-out}
#galeria img{display:block;width:100%;height:auto}
#galeria figure.zoom img{max-height:74vh;width:auto;max-width:100%;margin:0 auto}
#galeria figcaption{padding:9px 12px;font-size:11.5px;color:var(--ink-2);font-family:var(--sans)}
#galeria figcaption b{font-family:var(--serif);font-weight:600;color:var(--ink)}

/* ── etiquetas 3D ── */
#labels{position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:10}
.label{
  position:absolute;transform:translate(-50%,-100%);white-space:nowrap;
  background:rgba(250,247,242,.9);border:1px solid var(--line);border-radius:999px;
  padding:5px 11px 6px;box-shadow:0 8px 24px -12px rgba(40,32,24,.4);
  backdrop-filter:blur(6px);transition:opacity .25s;
}
.label b{font-family:var(--serif);font-weight:600;font-size:12.5px}
.label i{font-style:normal;color:var(--muted);font-size:11px;margin-left:5px}
.label.sel{background:var(--ink);border-color:var(--ink);color:#fff}
.label.sel i{color:#CFC6B6}

/* ── pie ── */
footer{
  position:absolute;bottom:0;left:0;right:0;display:flex;justify-content:space-between;gap:14px;
  padding:14px 20px;pointer-events:none;z-index:16;align-items:flex-end;
}
.hint{pointer-events:auto;background:var(--panel);border:1px solid var(--line);border-radius:999px;
  padding:8px 14px;box-shadow:var(--shadow);backdrop-filter:blur(10px);font-size:11px;color:var(--muted)}
.hint kbd{font:600 10px var(--sans);background:rgba(0,0,0,.06);border-radius:4px;padding:2px 5px;color:var(--ink-2)}
body.libre #c{cursor:crosshair}
body.libre.pointerlock #c{cursor:none}
#stick{position:absolute;left:16px;bottom:74px;width:108px;height:108px;border-radius:50%;
  border:1px solid var(--line);background:var(--panel);box-shadow:var(--shadow);backdrop-filter:blur(10px);
  z-index:22;display:none;touch-action:none;pointer-events:none}
#stick.on{display:block}
#stick i{position:absolute;left:50%;top:50%;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;
  background:var(--ink);opacity:.85;pointer-events:none}
#stick::after{content:"mover";position:absolute;left:50%;bottom:-18px;transform:translateX(-50%);
  font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.credit{text-align:right;font-size:10.5px;color:var(--muted);line-height:1.55;max-width:38ch}
.credit b{color:var(--ink-2);font-weight:500}
.credit a{color:var(--accent-2)}
.btn{text-decoration:none}

/* ── carga / avisos ── */
#loader{position:absolute;inset:0;display:grid;place-items:center;z-index:40;background:var(--paper);
  transition:opacity .6s .15s,visibility .6s .15s}
#loader.done{opacity:0;visibility:hidden}
#loader .box{text-align:center;max-width:340px;padding:0 24px}
#loader h2{font-family:var(--serif);font-size:22px;margin:0 0 6px;font-weight:600}
#loader p{font-size:12px;color:var(--muted);margin:0 0 18px}
.bar{height:3px;background:var(--line);border-radius:99px;overflow:hidden}
.bar i{display:block;height:100%;width:0;background:var(--accent);transition:width .4s}
#fallback{display:none;position:absolute;inset:0;z-index:50;place-items:center;background:var(--paper);text-align:left;padding:24px;overflow:auto}
#fallback .fb-box{max-width:560px;margin:auto}
#fallback h2{font-family:var(--serif);font-size:24px;margin:0 0 8px}
#fallback .fb-why{font-size:12px;color:var(--warn,#B5410F);margin:0 0 14px;min-height:1em;word-break:break-word}
#fallback .fb-steps{font-size:13.5px;line-height:1.6;color:var(--ink-2);padding-left:20px;margin:0 0 16px}
#fallback .fb-steps li{margin-bottom:8px}
#fallback code{background:rgba(0,0,0,.06);border-radius:4px;padding:1px 5px;font-size:12.5px}
#fallback .fb-alt{font-size:12px;color:var(--muted)}
#fallback a{color:var(--accent-2)}
#fallback h2{font-family:var(--serif);font-size:24px}
#fallback a{color:var(--accent-2)}

@media (max-width:860px){
  header{flex-direction:column;gap:6px;padding:10px 12px}
  .title-block .eyebrow{font-size:9px}
  h1{font-size:17.5px;margin:2px 0 0}
  .label{padding:3px 8px 4px}
  .label b{font-size:10.5px}
  .label i{font-size:9.5px;margin-left:4px}
  aside{max-height:40vh}
  .ctl{padding:9px 14px}
  .rooms button{padding:7px 9px;font-size:12px}
  #card{padding:14px 16px 16px}
  .stats div b{font-size:15px}
  .title-block .eyebrow::before{width:14px}
  h1{font-size:19px;margin:3px 0 0;max-width:26ch}
  .title-block p{display:none}
  .toolbar{justify-content:flex-start;flex-wrap:nowrap;overflow-x:auto;max-width:100%;
    scrollbar-width:none;padding-bottom:2px;-webkit-overflow-scrolling:touch}
  .toolbar::-webkit-scrollbar{display:none}
  .seg button,.btn{padding:7px 11px;font-size:10.5px}
  aside{top:auto;bottom:12px;left:12px;right:12px;width:auto;max-height:46vh}
  aside.hidden{transform:translateY(130%)}
  #card{right:12px;left:12px;top:auto;bottom:12px;width:auto}
  .hint{display:none}
  footer{padding:8px 12px}
  .credit{display:none}
}
@media (prefers-reduced-motion:reduce){
  *{transition-duration:.01ms!important;animation-duration:.01ms!important}
}
</style>
</head>
<body>
<div id="app">
  <canvas id="c" aria-label="Modelo 3D de la vivienda"></canvas>
  <div id="labels"></div>
  <div id="stick" aria-hidden="true"><i></i></div>

  <header>
    <div class="title-block">
      <div class="eyebrow micro">SOFIA PALACIOS · Plano PE.A.02 · Junio/25</div>
      <h1>Reforma José María Mortés Lerma</h1>
      <p>C/ José María Mortés Lerma, 2 · 7º pta 28 · 46018 Valencia &nbsp;·&nbsp; <b>Modelo 3D generado del plano de distribución a escala 1:50</b></p>
    </div>
    <div class="toolbar">
      <div class="seg" role="group" aria-label="Modo de suelo">
        <button id="m-plan" aria-pressed="true">Plano</button>
        <button id="m-zonas" aria-pressed="false">Zonas</button>
      </div>
      <div class="seg" role="group" aria-label="Modo de cámara">
        <button id="c-orbita" aria-pressed="true">Órbita</button>
        <button id="c-caminar" aria-pressed="false">Caminar</button>
        <button id="c-vuelo" aria-pressed="false">Vuelo</button>
      </div>
      <button class="btn" id="b-labels" aria-pressed="true">Etiquetas</button>
      <button class="btn" id="b-galeria">Galería</button>
      <a class="btn" href="tour3d.html">Tour 360</a>
      <button class="btn" id="b-panel" aria-pressed="true">Panel</button>
      <button class="btn" id="b-export">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v12m0 0 4-4m-4 4-4-4M5 21h14"/></svg>
        PNG
      </button>
      <button class="btn" id="b-planta">Planta</button>
      <button class="btn" id="b-reset" title="Vista general">Vista</button>
    </div>
  </header>

  <aside id="panel">
    <div class="panel-head">
      <h2>Estancias</h2>
      <span class="micro" id="panel-count"></span>
    </div>
    <div class="panel-scroll">
      <div class="ctl">
        <label class="micro" for="s-altura">Altura de muros <output id="o-altura">2,60 m</output></label>
        <input id="s-altura" type="range" min="0" max="2.6" step="0.05" value="2.6">
      </div>
      <div class="ctl">
        <label class="micro" for="s-sol">Posición del sol <output id="o-sol">140°</output></label>
        <input id="s-sol" type="range" min="0" max="359" step="1" value="140">
      </div>
      <ul class="rooms" id="rooms"></ul>
    </div>
    <div class="panel-foot">
      <span class="micro">Superficie interior medida</span>
      <span class="total num" id="total">—</span>
    </div>
  </aside>

  <section id="card" aria-live="polite">
    <button class="close" id="card-close" aria-label="Cerrar ficha">✕</button>
    <div class="swatch-lg" id="card-color"></div>
    <h3 id="card-name">—</h3>
    <div class="sub" id="card-sub">—</div>
    <figure class="render" id="card-render">
      <img id="card-render-img" alt="">
      <figcaption id="card-render-cap"></figcaption>
    </figure>
    <div class="thumbs" id="card-thumbs"></div>
    <div class="stats">
      <div><span>Superficie</span><b id="card-area" class="num">—</b></div>
      <div><span>% útil</span><b id="card-share" class="num">—</b></div>
      <div><span>Zona de uso</span><b id="card-zona">—</b></div>
      <div><span>Coste orientativo</span><b id="card-cost" class="num">—</b></div>
    </div>
    <p class="note" id="card-note"></p>
  </section>

  <div id="galeria" hidden>
    <div class="gal-head">
      <div>
        <h2>Ambientación y documentación</h2>
        <div class="gal-sub" id="gal-sub"></div>
      </div>
      <button class="close" id="gal-close" aria-label="Cerrar galería">✕</button>
    </div>
    <div class="grid" id="gal-grid"></div>
  </div>

  <footer>
    <div class="hint">
      <span id="hint-orbita"><kbd>Arrastrar</kbd> orbitar · <kbd>Rueda</kbd> zoom · <kbd>Botón derecho</kbd> desplazar · <kbd>1</kbd>/<kbd>2</kbd> modo · <kbd>L</kbd> etiquetas · <kbd>P</kbd> planta · <kbd>R</kbd> vista · <kbd>C</kbd>/<kbd>V</kbd> caminar/vuelo</span>
      <span id="hint-libre" hidden><kbd>WASD</kbd> mover · <kbd>Ratón</kbd> mirar · <kbd>Shift</kbd> correr · <kbd>Espacio</kbd>/<kbd>Q</kbd> subir/bajar · <kbd>Esc</kbd> salir</span>
    </div>
    <div class="credit">
      <b>__FECHA__</b> · geometría vectorial del PDF (escala exacta 1:50, __PTM__ pt/m).<br>
      Superficies medidas del plano; coste orientativo = reparto proporcional del presupuesto Cyss v2.0 (__COSTE__ €).
      Consulta el detalle en <a href="index.html">index.html</a> y el alzado 2D en <a href="planos.html">planos.html</a>.
    </div>
  </footer>

  <div id="loader">
    <div class="box">
      <h2>Construyendo el modelo</h2>
      <p>Extruyendo muros y estancias desde el plano vectorial…</p>
      <div class="bar"><i id="loadbar"></i></div>
    </div>
  </div>
  <div id="fallback">
    <div class="fb-box">
      <h2>Tu navegador no puede mostrar WebGL</h2>
      <p id="fb-why" class="fb-why"></p>
      <ol class="fb-steps">
        <li><b>Chrome / Edge:</b> Ajustes → Sistema → activa «Usar aceleración gráfica cuando esté disponible» y reinicia. Comprueba el motivo en <code>chrome://gpu</code>.</li>
        <li><b>Firefox:</b> en <code>about:config</code> pon <code>webgl.disabled</code> = <code>false</code>; si sigue, <code>webgl.force-enabled</code> = <code>true</code>. Mira <code>about:support</code> → Graphics.</li>
        <li><b>Sin GPU / VM / escritorio remoto:</b> en Chrome ≥137 arranca con <code>--enable-unsafe-swiftshader</code>; en Firefox prueba <code>LIBGL_ALWAYS_SOFTWARE=1 firefox</code>.</li>
        <li>Actualiza el navegador y los drivers de la gráfica (<code>libgl1-mesa-dri</code> en Linux) y comprueba en <a href="https://get.webgl.org/" target="_blank" rel="noopener">get.webgl.org</a>.</li>
      </ol>
      <p><button class="btn" type="button" onclick="location.reload()">Reintentar</button></p>
      <p class="fb-alt">Mientras tanto: <a href="render3d.html">vista 3D</a> · <a href="planos.html">planos 2D</a> · <a href="index.html">presupuestos</a></p>
    </div>
  </div>
</div>

<script>__THREE__</script>
<script>__GLTFLOADER__</script>
<script>
"use strict";
const PLAN = __DATA__;
const TEX_SRC = "data:image/jpeg;base64,__TEXTURE__";
const TEXTURAS_SRC = __TEXTURAS_JS__;
const MOBILIARIO_B64 = "__MOB_B64__";
const MOBILIARIO_SRC = "__MOB_SRC__";
const COSTE_TOTAL = __COSTE_NUM__;

/* ── paleta de estancias ── */
const STYLE = {
  "dorm-principal": {c:0xC07A4E, label:"Dormitorio principal"},
  "dorm-1":         {c:0x8FA37E, label:"Dormitorio 1"},
  "dorm-2":         {c:0x7E9DB8, label:"Dormitorio 2"},
  "dorm-3":         {c:0xB08D9A, label:"Dormitorio 3"},
  "bano-1":         {c:0x6FA8A0, label:"Baño 1"},
  "bano-2":         {c:0x8FAEC4, label:"Baño 2"},
  "salon":          {c:0xD89A50, label:"Salón · comedor · cocina"},
  "pasillo":        {c:0xBFBAAD, label:"Pasillo"},
  "recibidor":      {c:0xC4A87E, label:"Recibidor"},
  "terraza":        {c:0xA97A4E, label:"Terraza"}
};
const ZONES = PLAN.estancias.filter(e => STYLE[e.id]);

/* renders y documentación en data/reales/ (aportados por el cliente) */
const RENDERS = {
  "salon": [
    {src:"data/reales/salon-render.jpeg",        cap:"Salón · ventanal a terraza"},
    {src:"data/reales/salon2-render.jpeg",       cap:"Salón · pilar visto y mueble de TV"},
    {src:"data/reales/salon-cocina_render.jpeg", cap:"Salón-comedor · cocina al fondo"},
    {src:"data/reales/cocina-render.jpeg",       cap:"Cocina · península de piedra"}
  ],
  "dorm-principal": [{src:"data/reales/dormitorio-principal-render.jpeg", cap:"Dormitorio principal · armario y cabecero de listones"}],
  "bano-1": [{src:"data/reales/baño-principal-render.jpeg", cap:"Baño · bañera y revestimiento pétreo"}],
  "bano-2": [{src:"data/reales/baño-principal-render.jpeg", cap:"Baño · bañera y revestimiento pétreo"}]
};
const GALERIA = [
  ...RENDERS["salon"],
  ...RENDERS["dorm-principal"],
  ...RENDERS["bano-1"],
  {src:"data/imagenes/plano_aires_recorte.jpg", cap:"Plano de conductos de clima marcado por el instalador (otra versión de distribución: cocina 12,9 m² y vestidor 6,2 m²)", tag:"Obra"},
  {src:"data/reales/grua al 7º piso.jpeg", cap:"Medios auxiliares: plataforma articulada en fachada para el 7º piso", tag:"Obra"}
];
const INTERIOR = ZONES.filter(e => e.id !== "terraza");
const AREA_INT = INTERIOR.reduce((s,e)=>s+e.area,0);

/* ── utilidades ── */
const $ = s => document.querySelector(s);
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const fmt = (v,d=1) => v.toLocaleString("es-ES",{minimumFractionDigits:d,maximumFractionDigits:d});
const eur = v => v.toLocaleString("es-ES",{style:"currency",currency:"EUR",maximumFractionDigits:0});

function shapeFrom(pts){
  const s = new THREE.Shape();
  pts.forEach(([x,z],i)=> i ? s.lineTo(x,-z) : s.moveTo(x,-z));
  s.closePath();
  return s;
}

/* ── escena ── */
let renderer, scene, camera;
try{
  renderer = new THREE.WebGLRenderer({canvas:$("#c"),antialias:true,alpha:true,preserveDrawingBuffer:true});
}catch(e){
  $("#loader").classList.add("done");
  $("#fallback").style.display="grid";
  const w = $("#fb-why");
  if(w) w.textContent = "Detalle técnico: " + (e && e.message ? e.message : "no se pudo crear el contexto WebGL");
  throw e;
}
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.92;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

scene = new THREE.Scene();
camera = new THREE.PerspectiveCamera(38, 1, 0.1, 300);
camera.position.set(12,14,16);

/* entorno suave para reflejos PBR (metales como cobre, aluminio o espejos) */
const pmrem = new THREE.PMREMGenerator(renderer);
const envCanvas = document.createElement("canvas");
envCanvas.width = 64; envCanvas.height = 32;
const ectx = envCanvas.getContext("2d");
const grad = ectx.createLinearGradient(0, 0, 0, 32);
grad.addColorStop(0, "#e8eef3"); grad.addColorStop(0.48, "#f7f2e8"); grad.addColorStop(1, "#a89c89");
ectx.fillStyle = grad; ectx.fillRect(0, 0, 64, 32);
const envTex = new THREE.CanvasTexture(envCanvas);
envTex.mapping = THREE.EquirectangularReflectionMapping;
scene.environment = pmrem.fromEquirectangular(envTex).texture;
envTex.dispose(); pmrem.dispose();

/* luces */
const hemi = new THREE.HemisphereLight(0xFFFDF6, 0xCFC6B6, 0.66);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xFFF2DE, 0.92);
sun.position.set(-8,16,10);
sun.castShadow = true;
sun.shadow.mapSize.set(2048,2048);
sun.shadow.camera.near = 1; sun.shadow.camera.far = 70;
sun.shadow.camera.left = -14; sun.shadow.camera.right = 14;
sun.shadow.camera.top = 14; sun.shadow.camera.bottom = -14;
sun.shadow.bias = -0.0006;
sun.shadow.normalBias = 0.03;
sun.shadow.camera.updateProjectionMatrix();
scene.add(sun);
scene.add(new THREE.DirectionalLight(0xDCE6F0, 0.3).translateX(10).translateY(6).translateZ(-12));

/* suelo de sombra (la maqueta flota sobre el degradado de la página) */
const shadowMat = new THREE.ShadowMaterial({opacity:0.16});
const ground = new THREE.Mesh(new THREE.PlaneGeometry(70,70), shadowMat);
ground.rotation.x = -Math.PI/2;
ground.position.y = -0.02;
ground.receiveShadow = true;
scene.add(ground);

/* ── grupos ── */
const gMuros = new THREE.Group();
const gSuelo = new THREE.Group();      // textura del plano
const gZonas = new THREE.Group();      // colores por estancia
const gAlicatados = new THREE.Group();
const gLineas = new THREE.Group();
const gMob = new THREE.Group();        // mobiliario (GLB de Blender)
scene.add(gMuros, gSuelo, gZonas, gAlicatados, gLineas, gMob);

const matMuro = new THREE.MeshStandardMaterial({color:0xF7F4ED, roughness:0.93, metalness:0});
const matTabique = new THREE.MeshStandardMaterial({color:0xF2EEE4, roughness:0.95, metalness:0});
const matTapa = new THREE.MeshStandardMaterial({color:0xE4DDD0, roughness:0.95, metalness:0});
const matTapaTab = new THREE.MeshStandardMaterial({color:0xDFD8CA, roughness:0.95, metalness:0});
const matVidrio = new THREE.MeshStandardMaterial({color:0xBFD6DE, roughness:0.12, metalness:0.05,
  transparent:true, opacity:0.3, side:THREE.DoubleSide, depthWrite:false});
const matLinea = new THREE.LineBasicMaterial({color:0x2B2B28, transparent:true, opacity:0.32});
const ALTURA = PLAN.altura_muro;

function addWall(poly, tipo, altura){
  const geo = new THREE.ExtrudeGeometry(shapeFrom(poly), {depth:altura, bevelEnabled:false});
  geo.rotateX(-Math.PI/2);
  const mat = tipo === "vidrio" ? matVidrio : (tipo === "estructural" ? matMuro : matTabique);
  const tapa = tipo === "estructural" ? matTapa : matTapaTab;
  const mesh = new THREE.Mesh(geo, tipo === "vidrio" ? mat : [tapa, mat]);
  mesh.castShadow = tipo !== "vidrio";
  mesh.receiveShadow = true;
  mesh.userData.tipo = tipo;
  gMuros.add(mesh);
  const line = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 24), matLinea);
  line.userData.wall = mesh;
  gLineas.add(line);
  return mesh;
}

/* muros: se guardan las geometrías para poder "crecer" en la intro */
let wallMeshes = [];
PLAN.muros.forEach(w => wallMeshes.push({def:w, mesh:addWall(w.pts, w.tipo, ALTURA),
  mat:(w.tipo==="vidrio"?matVidrio:(w.tipo==="estructural"?matMuro:matTabique))}));

/* helpers de suelo con UV del recorte del plano */
const texRect = PLAN.textura.rect_m;               // [x0,z0,x1,z1]
const texW = texRect[2]-texRect[0], texH = texRect[3]-texRect[1];
function applyPlanUV(geo){
  const pos = geo.attributes.position;
  const uv = new Float32Array(pos.count*2);
  for(let i=0;i<pos.count;i++){
    const x = pos.getX(i), z = pos.getZ(i);
    uv[i*2]   = (x - texRect[0]) / texW;
    uv[i*2+1] = 1 - (z - texRect[1]) / texH;
  }
  geo.setAttribute("uv", new THREE.BufferAttribute(uv,2));
}

let planTexture = null;
const floorMeshes = [];
function buildFloor(texture){
  planTexture = texture;
  {/* huella del edificio */}
  const geo = new THREE.ShapeGeometry(shapeFrom(PLAN.huella));
  geo.rotateX(-Math.PI/2);
  applyPlanUV(geo);
  const mat = new THREE.MeshStandardMaterial({map:texture, roughness:0.96, metalness:0});
  const m = new THREE.Mesh(geo, mat);
  m.position.y = 0;
  m.receiveShadow = true;
  gSuelo.add(m); floorMeshes.push(m);
  {/* terraza */}
  const ter = ZONES.find(z=>z.id==="terraza");
  if(ter){
    const g2 = new THREE.ShapeGeometry(shapeFrom(ter.pts));
    g2.rotateX(-Math.PI/2);
    applyPlanUV(g2);
    const m2 = new THREE.Mesh(g2, mat);
    m2.receiveShadow = true;
    gSuelo.add(m2); floorMeshes.push(m2);
  }
  texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  texture.encoding = THREE.sRGBEncoding;
}

/* zonas */
const zoneMeshes = [];
const zoneOutlines = {};
const SUELO_ZONA = id => id==="terraza" ? {tex:"terraza", escala:1.15}
  : id.indexOf("bano")===0 ? {tex:"azulejo", escala:1.0}
  : {tex:"suelo_madera", escala:1.7};
ZONES.forEach(z=>{
  const st = STYLE[z.id];
  const geo = new THREE.ShapeGeometry(shapeFrom(z.pts));
  geo.rotateX(-Math.PI/2);
  const mat = new THREE.MeshStandardMaterial({color:st.c, roughness:0.95, metalness:0,
    side:THREE.DoubleSide, emissive:new THREE.Color(st.c), emissiveIntensity:0});
  const m = new THREE.Mesh(geo, mat);
  m.position.y = 0.015;
  m.receiveShadow = true;
  m.userData.zone = z;
  gZonas.add(m); zoneMeshes.push(m);
  {/* contorno */}
  const outline = new THREE.LineLoop(
    new THREE.BufferGeometry().setFromPoints(ptsToVec3(z.pts, 0.02)),
    new THREE.LineBasicMaterial({color:0x2B2B28, transparent:true, opacity:0.28}));
  outline.position.y = 0.005;
  gZonas.add(outline);
  zoneOutlines[z.id] = outline;
});
function ptsToVec3(pts, y){ return pts.map(([x,z])=>new THREE.Vector3(x,y,z)); }

/* alicatados (baños/cocina) */
PLAN.alicatados.forEach(a=>{
  const geo = new THREE.ShapeGeometry(shapeFrom(a.pts));
  geo.rotateX(-Math.PI/2);
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({color:0x7FA8B8, roughness:0.7,
    transparent:true, opacity:0.18, side:THREE.DoubleSide, depthWrite:false}));
  m.position.y = 0.03;
  gAlicatados.add(m);
});

/* modo */
let mode = "plan";
function setMode(m){
  mode = m;
  gSuelo.visible = (m==="plan");
  gZonas.visible = (m==="zonas");
  gAlicatados.visible = (m==="zonas");
  $("#m-plan").setAttribute("aria-pressed", String(m==="plan"));
  $("#m-zonas").setAttribute("aria-pressed", String(m==="zonas"));
}

/* ── etiquetas ── */
const labelEls = {};
ZONES.forEach(z=>{
  const el = document.createElement("div");
  el.className = "label";
  el.innerHTML = `<b>${STYLE[z.id].label}</b><i>${fmt(z.area)} m²</i>`;
  el.addEventListener("click", ()=>select(z.id));
  $("#labels").appendChild(el);
  labelEls[z.id] = el;
});
let labelsOn = true;

/* ── interacción ── */
const BOUNDS = (()=>{
  let x0=1e9,x1=-1e9,z0=1e9,z1=-1e9;
  ZONES.forEach(z=>z.pts.forEach(([x,zz])=>{
    x0=Math.min(x0,x); x1=Math.max(x1,x); z0=Math.min(z0,zz); z1=Math.max(z1,zz);
  }));
  return {x0,x1,z0,z1,w:x1-x0,d:z1-z0,cx:(x0+x1)/2,cz:(z0+z1)/2};
})();
function fitDist(phi, theta){
  const vFov = camera.fov*Math.PI/180;
  const hFov = 2*Math.atan(Math.tan(vFov/2)*camera.aspect);
  const ct = Math.abs(Math.cos(theta)), st = Math.abs(Math.sin(theta));
  const ww = BOUNDS.w*ct + BOUNDS.d*st + 2.4;
  const hh = (BOUNDS.w*st + BOUNDS.d*ct)*Math.cos(phi) + ALTURA*Math.sin(phi) + 1.8;
  return Math.max((ww/2)/Math.tan(hFov/2), (hh/2)/Math.tan(vFov/2)) * 1.05;
}
const VIEW0 = {theta:0.52, phi:0.74};
const D0 = fitDist(VIEW0.phi, VIEW0.theta);
const ctrl = {
  target:new THREE.Vector3(0,0,0.6), theta:VIEW0.theta, phi:VIEW0.phi, dist:D0,
  target2:new THREE.Vector3(0,0,0.6), theta2:VIEW0.theta, phi2:VIEW0.phi, dist2:D0
};
let interactuado = false;
function vistaInicial(){
  const retrato = innerHeight > innerWidth * 1.05;
  const theta = VIEW0.theta + (retrato ? Math.PI / 2 : 0);
  const phi = retrato ? 0.58 : VIEW0.phi;
  return {theta, phi, dist: fitDist(phi, theta)};
}
function aplicarVistaInicial(){
  const v = vistaInicial();
  ctrl.theta = ctrl.theta2 = v.theta;
  ctrl.phi = ctrl.phi2 = v.phi;
  ctrl.dist = ctrl.dist2 = v.dist;
  ctrl.target.set(0, 0, 0.6);
  ctrl.target2.copy(ctrl.target);
  interactuado = false;
}
function applyCamera(snap){
  if(snap){ ctrl.target.copy(ctrl.target2); ctrl.theta=ctrl.theta2; ctrl.phi=ctrl.phi2; ctrl.dist=ctrl.dist2; }
  const sp = new THREE.Spherical(ctrl.dist, ctrl.phi, ctrl.theta);
  camera.position.setFromSpherical(sp).add(ctrl.target);
  camera.lookAt(ctrl.target);
}
function flyTo(o){
  interactuado = true;
  ctrl.target2.set(o.x??ctrl.target.x, o.y??0, o.z??ctrl.target.z);
  ctrl.theta2 = o.theta ?? ctrl.theta;
  ctrl.phi2 = Math.min(Math.max(o.phi ?? ctrl.phi, 0.12), 1.5);
  ctrl.dist2 = o.dist ?? ctrl.dist;
}

/* ── cámara libre: caminar (con colisiones) y vuelo ── */
const SEGS = [];
PLAN.muros.forEach(w=>{
  const p = w.pts;
  for(let i=0;i<p.length;i++){
    const a=p[i], b=p[(i+1)%p.length];
    SEGS.push([a[0],a[1],b[0],b[1]]);
  }
});
const free = {pos:new THREE.Vector3(), yaw:0, pitch:0, vel:new THREE.Vector3()};
const keys = new Set();
let techoGLB = null;   // el forjado del GLB se oculta en órbita (vista de maqueta)
const EYE = 1.62, RADIO = 0.30, V_WALK = 2.6, V_RUN = 5.0, V_FLY = 4.4, V_FLY_RUN = 9.0;
const joy = {x:0, y:0};
let camMode = "orbita";
const clampPitch = v => Math.min(Math.max(v, -1.45), 1.45);

function colisionar(p){
  for(let it=0; it<3; it++){
    let tocado = false;
    for(let i=0;i<SEGS.length;i++){
      const s=SEGS[i], ax=s[0],az=s[1],bx=s[2],bz=s[3];
      const dx=bx-ax, dz=bz-az;
      const L2=dx*dx+dz*dz || 1e-9;
      let t=((p.x-ax)*dx+(p.z-az)*dz)/L2;
      t=t<0?0:(t>1?1:t);
      const qx=ax+dx*t, qz=az+dz*t;
      let ex=p.x-qx, ez=p.z-qz;
      let d=Math.hypot(ex,ez);
      if(d<RADIO){
        if(d<1e-5){ ex=dz; ez=-dx; d=Math.hypot(ex,ez)||1; }
        p.x=qx+ex/d*RADIO; p.z=qz+ez/d*RADIO; tocado=true;
      }
    }
    if(!tocado) break;
  }
  p.x=Math.max(BOUNDS.x0-0.3,Math.min(BOUNDS.x1+0.3,p.x));
  p.z=Math.max(BOUNDS.z0-0.3,Math.min(BOUNDS.z1+0.3,p.z));
}

function dentroDeHuella(x, z){
  const pts = PLAN.huella;
  let dentro = false;
  for(let i=0, j=pts.length-1; i<pts.length; j=i++){
    const xi=pts[i][0], zi=pts[i][1], xj=pts[j][0], zj=pts[j][1];
    if(((zi>z)!==(zj>z)) && (x < (xj-xi)*(z-zi)/(zj-zi)+xi)) dentro = !dentro;
  }
  return dentro;
}

function setCamMode(m){
  if(m===camMode) return;
  camMode = m;
  if(m==="orbita"){
    const fwd=camera.getWorldDirection(new THREE.Vector3());
    ctrl.target2.copy(camera.position).addScaledVector(fwd, Math.max(5, ctrl.dist*0.45));
    const sp=new THREE.Spherical().setFromVector3(camera.position.clone().sub(ctrl.target2));
    ctrl.dist2=Math.max(3.5,sp.radius); ctrl.theta2=sp.theta; ctrl.phi2=clampPitch(sp.phi);
    if(document.pointerLockElement) document.exitPointerLock();
    $("#stick").classList.remove("on");
    camera.fov=38;
  }else{
    const fuera = !dentroDeHuella(camera.position.x, camera.position.z);
    if(fuera){
      free.pos.set(4.9, EYE, 1.6);
      free.yaw = Math.PI*0.78;
      free.pitch = 0;
    }else{
      free.pos.copy(camera.position);
      const fwd=camera.getWorldDirection(new THREE.Vector3());
      free.yaw=Math.atan2(-fwd.x,-fwd.z);
      free.pitch=Math.asin(Math.min(1,Math.max(-1,fwd.y)));
    }
    if(m==="caminar") free.pos.y=EYE;
    free.vel.set(0,0,0);
    camera.fov=62;
    if(matchMedia("(pointer:coarse)").matches) $("#stick").classList.add("on");
  }
  camera.updateProjectionMatrix();
  document.body.classList.toggle("libre", m!=="orbita");
  ["orbita","caminar","vuelo"].forEach(k=>$("#c-"+k)
    .setAttribute("aria-pressed", String(k===camMode)));
  $("#hint-orbita").hidden = m!=="orbita";
  $("#hint-libre").hidden = m==="orbita";
  interactuado = true;
}

function moverLibre(dt){
  const correr = keys.has("shift");
  let f=0, s=0;
  if(keys.has("w")||keys.has("arrowup")) f+=1;
  if(keys.has("s")||keys.has("arrowdown")) f-=1;
  if(keys.has("d")||keys.has("arrowright")) s+=1;
  if(keys.has("a")||keys.has("arrowleft")) s-=1;
  f+=-joy.y; s+=joy.x;
  f=Math.max(-1,Math.min(1,f)); s=Math.max(-1,Math.min(1,s));
  const cy=Math.cos(free.yaw), sy=Math.sin(free.yaw);
  const dir=new THREE.Vector3();
  const right=new THREE.Vector3(cy,0,-sy);
  if(camMode==="vuelo"){
    const cp=Math.cos(free.pitch), sp=Math.sin(free.pitch);
    dir.addScaledVector(new THREE.Vector3(-sy*cp, sp, -cy*cp), f);
    dir.addScaledVector(right, s);
    if(keys.has(" ")||keys.has("e")) dir.y+=1;
    if(keys.has("q")) dir.y-=1;
  }else{
    dir.addScaledVector(new THREE.Vector3(-sy,0,-cy), f);
    dir.addScaledVector(right, s);
  }
  if(dir.lengthSq()>0) dir.normalize();
  const vmax = camMode==="vuelo" ? (correr?V_FLY_RUN:V_FLY) : (correr?V_RUN:V_WALK);
  free.vel.lerp(dir.multiplyScalar(vmax), 1-Math.pow(0.0008, dt));
  free.pos.addScaledVector(free.vel, dt);
  if(camMode==="caminar"){
    colisionar(free.pos);
    free.pos.y=EYE;
  }
  camera.position.copy(free.pos);
  camera.rotation.order="YXZ";
  camera.rotation.set(free.pitch, free.yaw, 0);
}

/* ratón: pointer lock en modo libre */
$("#c").addEventListener("click", e=>{
  if(camMode!=="orbita" && e.pointerType==="mouse" && !document.pointerLockElement)
    $("#c").requestPointerLock();
});
document.addEventListener("pointerlockchange", ()=>{
  document.body.classList.toggle("pointerlock", !!document.pointerLockElement);
});
document.addEventListener("mousemove", e=>{
  if(document.pointerLockElement!==$("#c")) return;
  free.yaw -= e.movementX*0.0021;
  free.pitch = clampPitch(free.pitch - e.movementY*0.0021);
});

/* táctil en modo libre: mitad izquierda = joystick, derecha = mirar */
const stick = $("#stick"), stickKnob = stick.querySelector("i");
let stickId = null, lookId = null;
function stickMove(e){
  const r = stick.getBoundingClientRect();
  const cx = r.left+r.width/2, cy = r.top+r.height/2;
  const max = r.width/2;
  joy.x = Math.max(-1,Math.min(1,(e.clientX-cx)/max));
  joy.y = Math.max(-1,Math.min(1,(e.clientY-cy)/max));
  stickKnob.style.transform = `translate(${joy.x*max*0.6}px,${joy.y*max*0.6}px)`;
}
function stickReset(){ joy.x=joy.y=0; stickKnob.style.transform=""; stickId=null; }

/* órbita propia (ratón + táctil) */
const cvs = $("#c");
let drag = null, downAt = null, lookLast = null;
cvs.addEventListener("pointerdown", e=>{
  if(camMode==="orbita"){
    cvs.setPointerCapture(e.pointerId);
    drag = {x:e.clientX, y:e.clientY, pan:(e.button===2||e.shiftKey)};
    downAt = {x:e.clientX, y:e.clientY};
    interactuado = true;
    return;
  }
  if(e.pointerType!=="touch") return;   // ratón: pointer lock al hacer clic
  cvs.setPointerCapture(e.pointerId);
  if(e.clientX < innerWidth*0.45 && stickId===null){
    stickId = e.pointerId;
    const s = 108;
    stick.style.left = (e.clientX-s/2)+"px";
    stick.style.top = (e.clientY-s/2)+"px";
    stick.style.bottom = "auto";
    stickMove(e);
  }else if(lookId===null){
    lookId = e.pointerId;
    lookLast = {x:e.clientX, y:e.clientY};
  }
});
cvs.addEventListener("pointermove", e=>{
  if(camMode!=="orbita"){
    if(e.pointerId===stickId) stickMove(e);
    else if(e.pointerId===lookId && lookLast){
      free.yaw -= (e.clientX-lookLast.x)*0.005;
      free.pitch = clampPitch(free.pitch - (e.clientY-lookLast.y)*0.005);
      lookLast = {x:e.clientX, y:e.clientY};
    }
    return;
  }
  if(!drag) return;
  const dx = e.clientX-drag.x, dy = e.clientY-drag.y;
  drag.x = e.clientX; drag.y = e.clientY;
  if(drag.pan){
    const scale = ctrl.dist * 0.0011;
    const right = new THREE.Vector3().setFromMatrixColumn(camera.matrix,0);
    const up = new THREE.Vector3().setFromMatrixColumn(camera.matrix,1);
    ctrl.target2.addScaledVector(right,-dx*scale).addScaledVector(up,dy*scale);
  }else{
    ctrl.theta2 -= dx*0.0055;
    ctrl.phi2 = Math.min(Math.max(ctrl.phi2 - dy*0.0045, 0.12), 1.5);
  }
});
addEventListener("pointerup", e=>{
  if(e.pointerId===stickId) stickReset();
  if(e.pointerId===lookId){ lookId=null; lookLast=null; }
  drag=null;
});
cvs.addEventListener("contextmenu", e=>e.preventDefault());
cvs.addEventListener("wheel", e=>{
  e.preventDefault();
  if(camMode!=="orbita") return;
  interactuado = true;
  ctrl.dist2 = Math.min(Math.max(ctrl.dist2 * (1 + Math.sign(e.deltaY)*0.09), 3.5), 70);
},{passive:false});

/* táctil: pinch */
let touches = new Map(), pinch0 = null;
cvs.addEventListener("touchstart", e=>{
  for(const t of e.changedTouches) touches.set(t.identifier,{x:t.clientX,y:t.clientY});
  if(touches.size===2){
    const [a,b] = [...touches.values()];
    pinch0 = {d:Math.hypot(a.x-b.x,a.y-b.y), dist:ctrl.dist2};
  }
},{passive:true});
cvs.addEventListener("touchmove", e=>{
  if(touches.size===2 && pinch0){
    for(const t of e.changedTouches) touches.set(t.identifier,{x:t.clientX,y:t.clientY});
    const [a,b] = [...touches.values()];
    const d = Math.hypot(a.x-b.x,a.y-b.y);
    ctrl.dist2 = Math.min(Math.max(pinch0.dist * pinch0.d/d, 3.5), 70);
  }
},{passive:true});
cvs.addEventListener("touchend", e=>{
  for(const t of e.changedTouches) touches.delete(t.identifier);
  if(touches.size<2) pinch0 = null;
},{passive:true});

/* raycast */
const ray = new THREE.Raycaster();
const ndc = new THREE.Vector2();
let hovered = null;
function pick(e){
  const r = cvs.getBoundingClientRect();
  ndc.x = ((e.clientX-r.left)/r.width)*2-1;
  ndc.y = -((e.clientY-r.top)/r.height)*2+1;
  ray.setFromCamera(ndc, camera);
  const hits = ray.intersectObjects(zoneMeshes, false);
  return hits.length ? hits[0].object : null;
}
cvs.addEventListener("pointermove", e=>{
  if(drag || camMode!=="orbita") return;
  const hit = pick(e);
  if(hit !== hovered){
    if(hovered) hovered.material.emissiveIntensity = 0;
    hovered = hit;
    if(hovered) hovered.material.emissiveIntensity = 0.22;
    cvs.style.cursor = hovered ? "pointer" : "grab";
  }
});
cvs.addEventListener("pointerup", e=>{
  if(camMode!=="orbita") return;
  const wasDrag = drag, at = downAt;
  downAt = null;
  if(!wasDrag || wasDrag.pan || e.button!==0 || !at) return;
  if(Math.hypot(e.clientX-at.x, e.clientY-at.y) > 6) return;
  if(e.target !== cvs) return;
  const hit = pick(e);
  if(hit) select(hit.userData.zone.id);
});

/* ── selección / ficha ── */
let selected = null;
function select(id){
  selected = id;
  const z = ZONES.find(x=>x.id===id);
  ZONES.forEach(x=>{
    labelEls[x.id].classList.toggle("sel", x.id===id);
    $("#rooms").querySelector(`[data-id="${x.id}"]`)?.setAttribute("aria-current", String(x.id===id));
  });
  zoneMeshes.forEach(m=>{
    const on = m.userData.zone.id===id;
    m.material.emissiveIntensity = on?0.25:(hovered===m?0.22:0);
    m.position.y = on?0.05:0.015;
    if(zoneOutlines[m.userData.zone.id]) zoneOutlines[m.userData.zone.id].position.y = on?0.045:0.005;
  });
  const card = $("#card");
  if(!z){ card.classList.remove("show"); return; }
  const rs = RENDERS[z.id] || [];
  const fig = $("#card-render"), strip = $("#card-thumbs");
  strip.innerHTML = "";
  if(rs.length){
    fig.style.display = "block";
    setCardRender(rs[0]);
    rs.forEach((r,i)=>{
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-pressed", String(i===0));
      b.innerHTML = `<img src="${r.src}" alt="${r.cap}" loading="lazy">`;
      b.addEventListener("click", ()=>{
        setCardRender(r);
        strip.querySelectorAll("button").forEach((x,j)=>x.setAttribute("aria-pressed", String(j===i)));
      });
      strip.appendChild(b);
    });
    strip.classList.toggle("on", rs.length>1);
  }else{
    fig.style.display = "none";
    strip.classList.remove("on");
  }
  const st = STYLE[z.id];
  $("#card-color").style.background = `#${st.c.toString(16).padStart(6,"0")}`;
  $("#card-name").textContent = st.label;
  $("#card-sub").textContent = z.manual ? "Exterior · no computa en la superficie útil" :
    (z.area > 12 ? "Estancia principal" : z.area > 5 ? "Estancia" : "Estancia auxiliar");
  $("#card-area").textContent = fmt(z.area)+" m²";
  $("#card-share").textContent = z.id==="terraza" ? "—" : fmt(z.area/AREA_INT*100)+" %";
  const pct = z.area/AREA_INT;
  $("#card-cost").textContent = z.id==="terraza" ? "—" : eur(pct*COSTE_TOTAL);
  $("#card-zona").textContent = ZONA_USO[z.id] ?? "—";
  $("#card-note").textContent = "Superficie medida sobre el plano (escala 1:50). Coste orientativo: reparto proporcional del presupuesto Cyss v2.0 entre las estancias interiores; el desglose real está en index.html.";
  card.classList.add("show");
  const box = zoneBounds(z.pts);
  const d = Math.max(box.w, box.h);
  flyTo({x:box.cx, z:box.cz, dist: Math.max(8, d*1.7), phi:0.62});
}
$("#card-close").addEventListener("click", ()=>{ selected=null; select(null); });
/* zona de uso por estancia */
const ZONA_USO = {"dorm-principal":"Noche","dorm-1":"Noche","dorm-2":"Noche","dorm-3":"Noche",
  "bano-1":"Servicio","bano-2":"Servicio","salon":"Día","pasillo":"Circulación",
  "recibidor":"Circulación","terraza":"Exterior"};

function setCardRender(r){
  const img = $("#card-render-img");
  img.src = r.src;
  img.alt = r.cap;
  img.onerror = ()=>{ img.parentElement.style.display = "none"; };
  $("#card-render-cap").textContent = r.cap;
}

function zoneBounds(pts){
  const xs = pts.map(p=>p[0]), zs = pts.map(p=>p[1]);
  const x0=Math.min(...xs), x1=Math.max(...xs), z0=Math.min(...zs), z1=Math.max(...zs);
  return {x0,x1,z0,z1,w:x1-x0,h:z1-z0,cx:(x0+x1)/2,cz:(z0+z1)/2};
}

/* ── panel: lista de estancias ── */
const list = $("#rooms");
INTERIOR.slice().sort((a,b)=>b.area-a.area).forEach(z=>{
  const st = STYLE[z.id];
  const li = document.createElement("li");
  li.innerHTML = `<button data-id="${z.id}">
    <span class="swatch" style="background:#${st.c.toString(16).padStart(6,"0")}"></span>
    <span>${st.label}</span><span class="m2">${fmt(z.area)} m²</span></button>`;
  li.querySelector("button").addEventListener("click", ()=>select(z.id));
  list.appendChild(li);
});
$("#panel-count").textContent = `${INTERIOR.length} estancias`;
if(innerWidth < 860){
  $("#panel").classList.add("hidden");
  $("#b-panel").setAttribute("aria-pressed","false");
  labelsOn = false;
  $("#b-labels").setAttribute("aria-pressed","false");
}
$("#total").textContent = fmt(AREA_INT)+" m²";

/* ── controles ── */
$("#m-plan").addEventListener("click", ()=>setMode("plan"));
$("#m-zonas").addEventListener("click", ()=>setMode("zonas"));
$("#b-labels").addEventListener("click", e=>{
  labelsOn = !labelsOn;
  e.currentTarget.setAttribute("aria-pressed", String(labelsOn));
});
$("#b-panel").addEventListener("click", e=>{
  const aside = $("#panel");
  aside.classList.toggle("hidden");
  e.currentTarget.setAttribute("aria-pressed", String(!aside.classList.contains("hidden")));
});
$("#b-reset").addEventListener("click", ()=>resetView());
function resetView(){
  setCamMode("orbita");
  select(null);
  const v = vistaInicial();
  flyTo({x:0,z:0.6,theta:v.theta,phi:v.phi,dist:v.dist});
}
$("#b-planta").addEventListener("click", ()=>{
  setCamMode("orbita");
  select(null);
  const retrato = innerHeight > innerWidth * 1.05;
  const theta = retrato ? Math.PI / 2 : 0;
  flyTo({x:0,z:0.6,theta,phi:0.02,dist:fitDist(0.02, theta)});
});
$("#c-orbita").addEventListener("click", ()=>setCamMode("orbita"));
$("#c-caminar").addEventListener("click", ()=>setCamMode("caminar"));
$("#c-vuelo").addEventListener("click", ()=>setCamMode("vuelo"));
$("#s-altura").addEventListener("input", e=>{
  const h = parseFloat(e.target.value);
  $("#o-altura").textContent = fmt(h,2).replace(".",",")+" m";
  setWallHeight(h);
});
$("#s-sol").addEventListener("input", e=>{
  const a = parseInt(e.target.value,10);
  $("#o-sol").textContent = a+"°";
  const rad = a*Math.PI/180;
  sun.position.set(Math.cos(rad)*16, 15, Math.sin(rad)*16);
});
$("#b-export").addEventListener("click", exportPNG);
let galeriaConstruida = false;
function abrirGaleria(){
  const g = $("#galeria");
  if(!galeriaConstruida){
    const grid = $("#gal-grid");
    GALERIA.forEach(item=>{
      const fig = document.createElement("figure");
      fig.innerHTML = `<img src="${item.src}" alt="${item.cap}" loading="lazy"><figcaption><b>${item.tag || "Render"}</b> · ${item.cap}</figcaption>`;
      fig.querySelector("img").addEventListener("error", ()=>fig.remove());
      fig.addEventListener("click", ()=>fig.classList.toggle("zoom"));
      grid.appendChild(fig);
    });
    $("#gal-sub").textContent = "Renders de ambientación, plano de conductos y medios auxiliares · " + GALERIA.length + " imágenes";
    galeriaConstruida = true;
  }
  g.hidden = false;
}
function cerrarGaleria(){ $("#galeria").hidden = true; }
$("#b-galeria").addEventListener("click", abrirGaleria);
$("#gal-close").addEventListener("click", cerrarGaleria);
$("#galeria").addEventListener("click", e=>{ if(e.target === $("#galeria")) cerrarGaleria(); });
addEventListener("keydown", e=>{
  const k = e.key.toLowerCase();
  if(["w","a","s","d","q","e","shift"," ","arrowup","arrowdown","arrowleft","arrowright"].includes(k)){
    if(camMode!=="orbita" && !(e.target.tagName==="INPUT")){
      keys.add(k);
      e.preventDefault();
    }
  }
  if(e.key==="Escape" && document.pointerLockElement) document.exitPointerLock();
  if(e.target.tagName==="INPUT") return;
  if(k==="o") setCamMode("orbita");
  else if(k==="c" && !e.ctrlKey && !e.metaKey) setCamMode("caminar");
  else if(k==="v") setCamMode("vuelo");
  if(camMode!=="orbita"){
    if(k==="l") $("#b-labels").click();
    return;
  }
  if(k==="1") setMode("plan");
  else if(k==="2") setMode("zonas");
  else if(k==="l") $("#b-labels").click();
  else if(k==="r") $("#b-reset").click();
  else if(k==="p") $("#b-planta").click();
  else if(k==="g") abrirGaleria();
  else if(k==="e") exportPNG();
  else if(k==="escape"){ select(null); cerrarGaleria(); }
});
addEventListener("keyup", e=>keys.delete(e.key.toLowerCase()));

function setWallHeight(h){
  wallMeshes.forEach(({mesh, def})=>{
    const base = def.tipo==="vidrio" ? Math.min(PLAN.altura_vidrio, h) : h;
    mesh.scale.y = Math.max(base, 0.0001)/ALTURA;
  });
}

/* exportar PNG a 2x */
function exportPNG(){
  const w = innerWidth, h = innerHeight;
  const pr = Math.min(devicePixelRatio, 2);
  renderer.setPixelRatio(pr*2);
  renderer.setSize(w, h, false);
  renderer.render(scene, camera);
  const url = renderer.domElement.toDataURL("image/png");
  renderer.setPixelRatio(pr);
  renderer.setSize(w, h, false);
  const a = document.createElement("a");
  a.href = url;
  a.download = "render3d_reforma_Mortes_"+new Date().toISOString().slice(0,10)+".png";
  a.click();
}

/* ── etiquetas en pantalla ── */
const v = new THREE.Vector3();
function updateLabels(){
  ZONES.forEach(z=>{
    const el = labelEls[z.id];
    if(!labelsOn){ el.style.opacity = 0; return; }
    v.set(z.centro[0], 0.75, z.centro[1]).project(camera);
    const behind = v.z > 1;
    const x = (v.x*0.5+0.5)*innerWidth, y = (-v.y*0.5+0.5)*innerHeight;
    const off = behind || x<40 || x>innerWidth-40 || y<60 || y>innerHeight-40;
    el.style.opacity = off ? 0 : 1;
    el.style.left = x+"px";
    el.style.top = y+"px";
  });
}

/* ── bucle ── */
let intro = 0, ready = false, prevT = 0;
function tick(t){
requestAnimationFrame(tick);
window.__visor = {scene, camera, renderer, gMob, free, setCamMode,
  get modo(){ return camMode; }, get listo(){ return ready; }};

  const dt = prevT ? Math.min(0.05, (t-prevT)/1000) : 0.016;
  prevT = t;
  if(drag && !drag.pan) cvs.style.cursor="grabbing";
  if(camMode==="orbita"){
    const k = reduceMotion ? 1 : 0.12;
    ctrl.target.lerp(ctrl.target2, k);
    ctrl.theta += (ctrl.theta2-ctrl.theta)*k;
    ctrl.phi += (ctrl.phi2-ctrl.phi)*k;
    ctrl.dist += (ctrl.dist2-ctrl.dist)*k;
    applyCamera(false);
  }else{
    moverLibre(dt);
  }
  if(techoGLB) techoGLB.visible = camera.position.y < 2.45;
  sun.target.position.set(camera.position.x, 0, camera.position.z);
  sun.target.updateMatrixWorld();
  updateLabels();
  renderer.render(scene, camera);
  if(ready && intro < 1){
    intro = Math.min(1, intro + 0.012);
    const e = 1 - Math.pow(1-intro, 3);
    setWallHeight(ALTURA*e);
    if(intro===1) $("#s-altura").value = ALTURA;
  }
}
function resize(){
  camera.aspect = innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight, false);
  if(!interactuado) aplicarVistaInicial();
}
addEventListener("resize", resize);
resize();
aplicarVistaInicial();
applyCamera(true);
setMode("plan");

/* ── carga ── */
const bar = $("#loadbar");
const TEXTURA = {};
const texLoader = new THREE.TextureLoader();
function prepararTex(t){
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.encoding = THREE.sRGBEncoding;
  t.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  return t;
}
function cargarTextura(src){
  return new Promise(res=>texLoader.load(src, t=>res(prepararTex(t)), undefined, ()=>res(null)));
}
function aplicarTexturas(){
  zoneMeshes.forEach(m=>{
    const conf = SUELO_ZONA(m.userData.zone.id);
    const base = TEXTURA[conf.tex];
    if(!base) return;
    const t = base.clone();
    t.needsUpdate = true;
    t.repeat.set(1/conf.escala, 1/conf.escala);
    m.material.map = t;
    m.material.color.set(0xffffff);
    m.material.needsUpdate = true;
  });
  if(TEXTURA.muro){
    [matMuro, matTabique].forEach((m,i)=>{
      const t = TEXTURA.muro.clone();
      t.needsUpdate = true;
      t.repeat.set(1/2.2, 1/2.2);
      m.map = t;
      m.color.set(i ? 0xF7F3EB : 0xFCF9F3);
      m.needsUpdate = true;
    });
  }
}
function base64AB(b64){
  const bin = atob(b64), buf = new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
}
function cargarMobiliario(){
  if(typeof THREE.GLTFLoader !== "function" || (!MOBILIARIO_B64 && !MOBILIARIO_SRC))
    return Promise.resolve(null);
  return new Promise(res=>{
    const onLoad = g=>{
      const petos = [];
      g.scene.traverse(o=>{
        if(!o.isMesh) return;
        o.castShadow = true;
        o.receiveShadow = true;
        if(o.name.indexOf("peto_")===0) petos.push(o);
        if(o.name === "suelo") o.visible = false;   // el visor pinta sus suelos
        if(o.name === "techo") techoGLB = o;
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        mats.forEach(mt=>{
          if(mt.map) mt.map.encoding = THREE.sRGBEncoding;
          if(mt.transparent){
            mt.depthWrite = false;
            mt.side = THREE.DoubleSide;
            if(mt.opacity < 0.2) mt.opacity = 0.22;
          }
        });
      });
      /* los petos de terraza no están en el plano: colisionar con su caja */
      petos.forEach(o=>{
        const b = new THREE.Box3().setFromObject(o);
        const x0=b.min.x, x1=b.max.x, z0=b.min.z, z1=b.max.z;
        SEGS.push([x0,z0,x1,z0],[x1,z0,x1,z1],[x1,z1,x0,z1],[x0,z1,x0,z0]);
      });
      gMob.add(g.scene);
      res(g);
    };
    const onErr = err=>{ console.warn("No se pudo cargar el mobiliario:", err); res(null); };
    const loader = new THREE.GLTFLoader();
    if(MOBILIARIO_B64) loader.parse(base64AB(MOBILIARIO_B64), "", onLoad, onErr);
    else loader.load(MOBILIARIO_SRC, onLoad, undefined, onErr);
  });
}
const tareas = [
  cargarTextura(TEX_SRC).then(t=>{ if(t){ TEXTURA.plano = t; buildFloor(t); } }),
  ...Object.entries(TEXTURAS_SRC).map(([n,src])=>cargarTextura(src).then(t=>{ if(t) TEXTURA[n] = t; })),
  cargarMobiliario()
];
bar.style.width = "35%";
Promise.all(tareas).then(()=>{
  aplicarTexturas();
  bar.style.width = "90%";
  renderer.compile(scene, camera);
  bar.style.width = "100%";
  requestAnimationFrame(()=>{
    $("#loader").classList.add("done");
    setWallHeight(reduceMotion ? ALTURA : 0);
    intro = reduceMotion ? 1 : 0;
    ready = true;
  });
}).catch(err=>{
  console.warn(err);
  bar.style.width = "100%";
  $("#loader").classList.add("done");
});
requestAnimationFrame(tick);
</script>
</body>
</html>
"""

COSTE = 56677.94
html = (HTML
        .replace("__THREE__", THREE.read_text(encoding="utf-8"))
        .replace("__GLTFLOADER__", GLTF.read_text(encoding="utf-8"))
        .replace("__TEXTURAS_JS__", json.dumps(TEXTURAS_JS, ensure_ascii=False, separators=(",", ":")))
        .replace("__MOB_B64__", MOB_B64)
        .replace("__MOB_SRC__", MOB_SRC)
        .replace("__TEXTURE__", TEX_B64)
        .replace("__DATA__", json.dumps(PLAN, ensure_ascii=False, separators=(",", ":")))
        .replace("__FECHA__", date.today().strftime("%d/%m/%Y"))
        .replace("__PTM__", f"{PLAN['pt_por_m']:.2f}".replace(".", ","))
        .replace("__COSTE__", f"{COSTE:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        .replace("__COSTE_NUM__", f"{COSTE:.2f}"))
OUT.write_text(html, encoding="utf-8")
print(f"escrito {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1024:.0f} KB)")
