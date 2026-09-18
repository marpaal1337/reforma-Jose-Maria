#!/usr/bin/env python3
"""
Genera render3d.html: visor 3D autocontenido (Three.js incluido, sin build)
a partir de data/planos3d.json y data/imagenes/planta_textura.jpg.

Requiere: libs/three.min.js (descargar una vez, ver AGENTS.md)

Uso:
    python3 scripts/generar_visor3d.py
"""
from __future__ import annotations

import base64
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "render3d.html"
THREE = ROOT / "libs" / "three.min.js"

PLAN = json.loads((DATA / "planos3d.json").read_text(encoding="utf-8"))
TEX_B64 = base64.b64encode((DATA / "imagenes" / "planta_textura.jpg").read_bytes()).decode("ascii")

if not THREE.exists():
    raise SystemExit("Falta libs/three.min.js (ver AGENTS.md: cómo regenerar el visor 3D)")

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
#fallback{display:none;position:absolute;inset:0;z-index:50;place-items:center;background:var(--paper);text-align:center;padding:24px}
#fallback h2{font-family:var(--serif);font-size:24px}
#fallback a{color:var(--accent-2)}

@media (max-width:860px){
  header{flex-direction:column;gap:8px;padding:12px}
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
      <button class="btn" id="b-labels" aria-pressed="true">Etiquetas</button>
      <button class="btn" id="b-galeria">Galería</button>
      <a class="btn" href="tour3d.html">Tour 360</a>
      <button class="btn" id="b-panel" aria-pressed="true">Panel</button>
      <button class="btn" id="b-export">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v12m0 0 4-4m-4 4-4-4M5 21h14"/></svg>
        PNG
      </button>
      <button class="btn" id="b-planta">Planta</button>
      <button class="btn" id="b-reset">Vista general</button>
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
      <kbd>Arrastrar</kbd> orbitar · <kbd>Rueda</kbd> zoom · <kbd>Botón derecho</kbd> desplazar · <kbd>1</kbd>/<kbd>2</kbd> modo · <kbd>L</kbd> etiquetas · <kbd>P</kbd> planta · <kbd>R</kbd> vista
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
    <div>
      <h2>Tu navegador no puede mostrar WebGL</h2>
      <p>Puedes seguir consultando la reforma en el visor 2D <a href="planos.html">planos.html</a> o en el panel <a href="index.html">index.html</a>.</p>
    </div>
  </div>
</div>

<script>__THREE__</script>
<script>
"use strict";
const PLAN = __DATA__;
const TEX_SRC = "data:image/jpeg;base64,__TEXTURE__";
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
scene.add(gMuros, gSuelo, gZonas, gAlicatados, gLineas);

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
function applyCamera(snap){
  if(snap){ ctrl.target.copy(ctrl.target2); ctrl.theta=ctrl.theta2; ctrl.phi=ctrl.phi2; ctrl.dist=ctrl.dist2; }
  const sp = new THREE.Spherical(ctrl.dist, ctrl.phi, ctrl.theta);
  camera.position.setFromSpherical(sp).add(ctrl.target);
  camera.lookAt(ctrl.target);
}
function flyTo(o){
  ctrl.target2.set(o.x??ctrl.target.x, o.y??0, o.z??ctrl.target.z);
  ctrl.theta2 = o.theta ?? ctrl.theta;
  ctrl.phi2 = Math.min(Math.max(o.phi ?? ctrl.phi, 0.12), 1.5);
  ctrl.dist2 = o.dist ?? ctrl.dist;
}

/* órbita propia (ratón + táctil) */
const cvs = $("#c");
let drag = null, downAt = null;
cvs.addEventListener("pointerdown", e=>{
  cvs.setPointerCapture(e.pointerId);
  drag = {x:e.clientX, y:e.clientY, pan:(e.button===2||e.shiftKey)};
  downAt = {x:e.clientX, y:e.clientY};
});
cvs.addEventListener("pointermove", e=>{
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
addEventListener("pointerup", ()=>{ drag=null; });
cvs.addEventListener("contextmenu", e=>e.preventDefault());
cvs.addEventListener("wheel", e=>{
  e.preventDefault();
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
  if(drag) return;
  const hit = pick(e);
  if(hit !== hovered){
    if(hovered) hovered.material.emissiveIntensity = 0;
    hovered = hit;
    if(hovered) hovered.material.emissiveIntensity = 0.22;
    cvs.style.cursor = hovered ? "pointer" : "grab";
  }
});
cvs.addEventListener("pointerup", e=>{
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
if(innerWidth < 860){ $("#panel").classList.add("hidden"); $("#b-panel").setAttribute("aria-pressed","false"); }
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
  select(null);
  const d = fitDist(VIEW0.phi, VIEW0.theta);
  flyTo({x:0,z:0.6,theta:VIEW0.theta,phi:VIEW0.phi,dist:d});
}
$("#b-planta").addEventListener("click", ()=>{
  select(null);
  flyTo({x:0,z:0.6,theta:0,phi:0.02,dist:fitDist(0.02,0)});
});
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
  if(e.target.tagName==="INPUT") return;
  const k = e.key.toLowerCase();
  if(k==="1") setMode("plan");
  else if(k==="2") setMode("zonas");
  else if(k==="l") $("#b-labels").click();
  else if(k==="r") $("#b-reset").click();
  else if(k==="p") $("#b-planta").click();
  else if(k==="g") abrirGaleria();
  else if(k==="e") exportPNG();
  else if(k==="escape"){ select(null); cerrarGaleria(); }
});

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
let intro = 0, ready = false;
function tick(t){
  requestAnimationFrame(tick);
  if(drag && !drag.pan) cvs.style.cursor="grabbing";
  const k = reduceMotion ? 1 : 0.12;
  ctrl.target.lerp(ctrl.target2, k);
  ctrl.theta += (ctrl.theta2-ctrl.theta)*k;
  ctrl.phi += (ctrl.phi2-ctrl.phi)*k;
  ctrl.dist += (ctrl.dist2-ctrl.dist)*k;
  applyCamera(false);
  sun.target.position.set(ctrl.target.x, 0, ctrl.target.z);
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
}
addEventListener("resize", resize);
resize();
applyCamera(true);
setMode("plan");

/* ── carga ── */
const bar = $("#loadbar");
bar.style.width = "30%";
new THREE.TextureLoader().load(TEX_SRC, tex=>{
  bar.style.width = "75%";
  buildFloor(tex);
  renderer.compile(scene, camera);
  bar.style.width = "100%";
  requestAnimationFrame(()=>{
    $("#loader").classList.add("done");
    setWallHeight(reduceMotion ? ALTURA : 0);
    intro = reduceMotion ? 1 : 0;
    ready = true;
  });
}, undefined, ()=>{
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
        .replace("__TEXTURE__", TEX_B64)
        .replace("__DATA__", json.dumps(PLAN, ensure_ascii=False, separators=(",", ":")))
        .replace("__FECHA__", date.today().strftime("%d/%m/%Y"))
        .replace("__PTM__", f"{PLAN['pt_por_m']:.2f}".replace(".", ","))
        .replace("__COSTE__", f"{COSTE:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        .replace("__COSTE_NUM__", f"{COSTE:.2f}"))
OUT.write_text(html, encoding="utf-8")
print(f"escrito {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1024:.0f} KB)")
