#!/usr/bin/env python3
"""
Genera tour3d.html: visor de panoramas 360 del tour de la reforma.

Requiere:
  - renders/panos/*.jpg  (generados con scripts/generar_blender.py + render_blender.py)
  - data/camaras.json    (posición, rumbo y nombre de cada panorama)
  - data/planos3d.json   (miniplano: rect de la textura)
  - libs/three.min.js

Uso:
    python3 scripts/generar_tour3d.py
"""
from __future__ import annotations

import base64
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAM = json.loads((ROOT / "data" / "camaras.json").read_text(encoding="utf-8"))
PLAN = json.loads((ROOT / "data" / "planos3d.json").read_text(encoding="utf-8"))
THREE = (ROOT / "libs" / "three.min.js").read_text(encoding="utf-8")
OUT = ROOT / "tour3d.html"

PANOS = CAM["panos"]
PDF = "renders/panos"
TEX = PLAN["textura"]["rect_m"]
TEXTURA_JPG = ROOT / "data" / "imagenes" / "planta_textura.jpg"

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Tour 360 · Reforma José María Mortés Lerma</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Tour virtual 360 de la reforma: panoramas generados con Blender a partir del plano PE.A.02.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --paper:#FAF7F2; --ink:#1A1A1A; --ink-2:#3D3D3D; --muted:#6B6B6B;
  --line:#E0DAD0; --accent:#B5651D; --accent-2:#8C4D14;
  --panel:rgba(250,247,242,.88); --shadow:0 18px 50px -18px rgba(0,0,0,.55);
  --serif:'Source Serif 4',Georgia,serif; --sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
}
*{box-sizing:border-box}
html,body{height:100%;margin:0;overflow:hidden;background:#0e0d0b;font-family:var(--sans);color:var(--ink)}
canvas{display:block;touch-action:none;cursor:grab}
canvas.drag{cursor:grabbing}
.micro{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.num{font-family:var(--serif);font-variant-numeric:tabular-nums}

header{position:fixed;top:0;left:0;right:0;z-index:20;padding:14px 18px;display:flex;
  justify-content:space-between;align-items:flex-start;gap:12px;pointer-events:none;
  background:linear-gradient(rgba(12,11,9,.62),transparent)}
.title{pointer-events:auto}
.title .eyebrow{color:#D8CFBF}
h1{font-family:var(--serif);font-size:clamp(16px,2vw,22px);margin:3px 0 0;color:#F6F2EA;font-weight:600;letter-spacing:-.01em}
.title p{margin:2px 0 0;font-size:11px;color:#BDB3A3}
.actions{display:flex;gap:8px;pointer-events:auto;flex-wrap:wrap;justify-content:flex-end}
.btn{border:1px solid rgba(246,242,234,.28);background:rgba(20,18,15,.42);color:#F6F2EA;
  font:600 11px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;padding:9px 12px;
  border-radius:999px;cursor:pointer;backdrop-filter:blur(8px);transition:.22s;white-space:nowrap}
.btn:hover{border-color:var(--accent);color:#fff;background:rgba(181,101,29,.35)}
.btn[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}

#hud{position:fixed;left:18px;bottom:132px;z-index:20;display:flex;flex-direction:column;gap:10px;
  pointer-events:none;max-width:min(300px,64vw)}
#plano{pointer-events:auto;background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:10px;box-shadow:var(--shadow);position:relative}
#plano .mapa{position:relative}
#plano img{display:block;width:100%;border-radius:8px}
#plano .pt{position:absolute;width:13px;height:13px;margin:-7px 0 0 -7px;border-radius:50%;
  border:2px solid #fff;background:var(--accent-2);cursor:pointer;box-shadow:0 1px 5px rgba(0,0,0,.4);
  transition:transform .2s}
#plano .pt:hover{transform:scale(1.25)}
#plano .pt.on{background:var(--accent);transform:scale(1.35)}
#plano .cap{display:flex;justify-content:space-between;align-items:baseline;margin:6px 2px 0}
#plano .cap b{font:600 11.5px var(--sans)}
#hint{pointer-events:auto;background:var(--panel);border:1px solid var(--line);border-radius:999px;
  padding:8px 13px;box-shadow:var(--shadow);font-size:11px;color:var(--muted);line-height:1.45}
.solo-mov{display:none}
@media (max-width:820px){ .solo-desk{display:none} .solo-mov{display:inline} }
kbd{font:600 10px var(--sans);background:rgba(0,0,0,.07);border-radius:4px;padding:2px 5px;color:var(--ink-2)}

#marcas{position:fixed;inset:0;z-index:12;overflow:hidden;pointer-events:none}
.marca{position:absolute;transform:translate(-50%,-50%);pointer-events:auto;cursor:pointer;
  display:flex;flex-direction:column;align-items:center;gap:4px;transition:opacity .25s}
.marca .aro{width:44px;height:44px;border-radius:50%;border:2px solid rgba(255,255,255,.92);
  background:rgba(20,18,15,.32);backdrop-filter:blur(3px);display:grid;place-items:center;
  box-shadow:0 6px 20px -6px rgba(0,0,0,.7);transition:.2s}
.marca:hover .aro{background:var(--accent);border-color:#fff;transform:scale(1.08)}
.marca .aro svg{width:19px;height:19px}
.marca span{font:600 10.5px/1.2 var(--sans);color:#fff;text-shadow:0 1px 4px rgba(0,0,0,.85);
  background:rgba(18,16,14,.45);padding:3px 8px;border-radius:999px;white-space:nowrap}

#tira{position:fixed;left:0;right:0;bottom:0;z-index:18;padding:12px 18px 90px;
  display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;pointer-events:none}
#tira::-webkit-scrollbar{display:none}
#tira button{pointer-events:auto;border:1px solid rgba(246,242,234,.22);background:rgba(20,18,15,.45);
  color:#EFE9DC;font:500 11.5px/1 var(--sans);padding:9px 13px;border-radius:999px;cursor:pointer;
  backdrop-filter:blur(8px);transition:.2s;white-space:nowrap}
#tira button.on{background:var(--paper);color:var(--ink);border-color:var(--paper)}

#fade{position:fixed;inset:0;background:#0e0d0b;opacity:0;pointer-events:none;transition:opacity .28s;z-index:30}
#load{position:fixed;inset:0;z-index:40;display:grid;place-items:center;background:#141210;color:#F6F2EA;
  transition:opacity .5s .1s,visibility .5s .1s}
#load.done{opacity:0;visibility:hidden}
#load .box{text-align:center;max-width:320px;padding:0 20px}
#load h2{font-family:var(--serif);font-size:20px;margin:0 0 8px;font-weight:600}
#load p{font-size:12px;color:#BDB3A3;margin:0 0 14px}
.bar{height:3px;background:rgba(255,255,255,.14);border-radius:99px;overflow:hidden}
.bar i{display:block;height:100%;width:0;background:var(--accent);transition:width .3s}
#fallback{display:none;position:absolute;inset:0;z-index:50;place-items:center;background:var(--paper);text-align:left;padding:24px;overflow:auto}
#fallback .fb-box{max-width:560px;margin:auto}
#fallback h2{font-family:var(--serif);font-size:24px;margin:0 0 8px}
#fallback .fb-why{font-size:12px;color:var(--warn,#B5410F);margin:0 0 14px;min-height:1em;word-break:break-word}
#fallback .fb-steps{font-size:13.5px;line-height:1.6;color:var(--ink-2);padding-left:20px;margin:0 0 16px}
#fallback .fb-steps li{margin-bottom:8px}
#fallback code{background:rgba(0,0,0,.06);border-radius:4px;padding:1px 5px;font-size:12.5px}
#fallback .fb-alt{font-size:12px;color:var(--muted)}
#fallback a{color:var(--accent-2)}
#fallback a{color:var(--accent-2)}

@media (max-width:820px){
  header{flex-direction:column;gap:8px;padding:10px 12px}
  .actions{justify-content:flex-start;overflow-x:auto;max-width:100%;flex-wrap:nowrap;scrollbar-width:none}
  .actions::-webkit-scrollbar{display:none}
  #hud{left:8px;bottom:104px;max-width:min(165px,44vw)}
  #plano{padding:6px;border-radius:12px}
  #plano .cap b{font-size:10.5px}
  #hint{padding:6px 10px;font-size:10px}
  #tira{padding:6px 8px 58px}
  #tira button{padding:8px 11px;font-size:10.5px}
  #tira{padding:8px 10px 64px}
  .title p{display:none}
}
@media (prefers-reduced-motion:reduce){*{transition-duration:.01ms!important}}
</style>
</head>
<body>
<canvas id="c" aria-label="Tour 360 de la vivienda"></canvas>
<div id="marcas"></div>

<header>
  <div class="title">
    <div class="eyebrow micro">SOFIA PALACIOS · PE.A.02 · Tour 360</div>
    <h1>Reforma José María Mortés Lerma</h1>
    <p>Panoramas renderizados con Blender · geometría del plano a escala 1:50 · __FECHA__</p>
  </div>
  <div class="actions">
    <button class="btn" id="b-giro" aria-pressed="false">Girar</button>
    <button class="btn" id="b-full">Pantalla completa</button>
    <a class="btn" href="render3d.html">Vista 3D</a>
    <a class="btn" href="planos.html">Planos 2D</a>
  </div>
</header>

<div id="hud">
  <div id="plano">
    <div class="mapa">
      <img id="mini" src="__TEXTURA__" alt="Planta de la vivienda">
    </div>
    <div class="cap"><b id="cuarto">—</b><span class="micro" id="pos">—</span></div>
  </div>
  <div id="hint">
    <span class="solo-desk"><kbd>Arrastrar</kbd> mirar · <kbd>Rueda</kbd> zoom · <kbd>←</kbd><kbd>→</kbd> estancias · <kbd>Espacio</kbd> girar</span>
    <span class="solo-mov">Arrastra para mirar · Pellizca para zoom</span>
  </div>
</div>

<div id="tira"></div>
<div id="fade"></div>

<div id="load">
  <div class="box">
    <h2>Tour 360</h2>
    <p>Cargando panoramas del primer recorrido…</p>
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

<script>__THREE__</script>
<script>
"use strict";
const PANOS = __PANOS__;
const TEX_RECT = __TEX_RECT__;
const SRC = i => PANOS[i].src;

let renderer, scene, camera, sphere, mat, tex = null, actual = -1, giro = false;
let yaw = 0, pitch = 0, yawT = 0, pitchT = 0, fovT = 75, arrancado = false;
const $ = s => document.querySelector(s);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const R = 120;

try{
  renderer = new THREE.WebGLRenderer({canvas:$("#c"), antialias:true});
}catch(e){
  $("#load").classList.add("done");
  $("#fallback").style.display = "grid";
  const w = $("#fb-why");
  if(w) w.textContent = "Detalle técnico: " + (e && e.message ? e.message : "no se pudo crear el contexto WebGL");
  throw e;
}
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
scene = new THREE.Scene();
camera = new THREE.PerspectiveCamera(75, 1, 0.1, 500);
sphere = new THREE.Mesh(
  new THREE.SphereGeometry(R, 64, 40),
  new THREE.MeshBasicMaterial({side: THREE.BackSide, toneMapped: false})
);
mat = sphere.material;
scene.add(sphere);

/* ── marcadores a otras estancias ── */
function vecinos(i){
  const p = PANOS[i];
  return PANOS.map((q, j) => {
    if (j === i) return null;
    const dx = q.x - p.x, dz = q.z - p.z;
    return {j, dx, dz, d: Math.hypot(dx, dz)};
  }).filter(v => v && v.d < 9).sort((a, b) => a.d - b.d).slice(0, 5);
}

const icono = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2"><path d="M5 12h13M12 5l7 7-7 7"/></svg>';
function pintarMarcas(){
  const cont = $("#marcas");
  cont.innerHTML = "";
  const p = PANOS[actual];
  vecinos(actual).forEach(v => {
    const q = PANOS[v.j];
    const el = document.createElement("div");
    el.className = "marca";
    el.innerHTML = `<div class="aro">${icono}</div><span>${q.nombre}</span>`;
    el.addEventListener("click", () => ir(v.j));
    el.userData = v;
    cont.appendChild(el);
  });
  actualizarMarcas();
}
const v3 = new THREE.Vector3();
function actualizarMarcas(){
  document.querySelectorAll(".marca").forEach(el => {
    const v = el.userData;
    v3.set(v.dx, 0, v.dz).normalize().multiplyScalar(R * 0.92);
    const detras = v3.clone().sub(camera.position).dot(dirCamara()) < 0;
    v3.project(camera);
    const x = (v3.x * 0.5 + 0.5) * innerWidth, y = (-v3.y * 0.5 + 0.5) * innerHeight;
    const fuera = v3.z > 1 || x < 30 || x > innerWidth - 30 || y < 70 || y > innerHeight - 90;
    el.style.opacity = (detras || fuera) ? 0 : 1;
    el.style.pointerEvents = (detras || fuera) ? "none" : "auto";
    el.style.left = x + "px";
    el.style.top = y + "px";
  });
}
const vDir = new THREE.Vector3();
function dirCamara(){ camera.getWorldDirection(vDir); return vDir; }

/* ── navegación ── */
/* Nota: cargamos los panoramas con <img> sin crossOrigin y creamos la textura a
   mano. Con THREE.TextureLoader (crossOrigin='anonymous') el navegador bloquea
   las imágenes al abrir el visor con file:// y la pantalla queda en negro. */
function cargarPano(i, cb){
  const img = new Image();
  img.decoding = "async";
  img.onload = () => {
    const t = new THREE.Texture(img);
    t.needsUpdate = true;
    t.encoding = THREE.sRGBEncoding;
    t.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    cb(t);
  };
  img.onerror = () => cb(null);
  img.src = SRC(i);
}
function errorPanos(msg){
  const el = $("#load");
  el.classList.remove("done");
  el.querySelector("h2").textContent = "No se pueden cargar los panoramas";
  el.querySelector("p").innerHTML = msg;
  el.querySelector(".bar").style.display = "none";
}
function ir(i, deGolpe){
  if (i === actual || i < 0 || i >= PANOS.length) return;
  const aplicar = () => {
    cargarPano(i, t => {
      if (!t){
        errorPanos("No se ha podido cargar el panorama <b>" + (PANOS[i].file || PANOS[i].id) + "</b>.");
        return;
      }
      if (tex) tex.dispose();
      tex = t;
      mat.map = t;
      mat.needsUpdate = true;
      const a = PANOS[i].yaw * Math.PI / 180;
      sphere.rotation.y = -a;
      yawT = yaw = -(a + Math.PI / 2);
      pitchT = pitch = 0;
      actual = i;
      pintarMarcas();
      pintarTira();
      actualizarMini();
      if (!deGolpe) $("#fade").style.opacity = 0;
    });
  };
  if (deGolpe || reduce){
    aplicar();
  } else {
    $("#fade").style.opacity = 1;
    setTimeout(aplicar, 290);
  }
}

/* ── tira de estancias ── */
function pintarTira(){
  document.querySelectorAll("#tira button").forEach((b, i) =>
    b.classList.toggle("on", i === actual));
}
function actualizarMini(){
  $("#cuarto").textContent = PANOS[actual].nombre;
  const p = PANOS[actual];
  $("#pos").textContent = `${p.x.toFixed(1)} m · z ${p.z.toFixed(1)} m`;
  document.querySelectorAll("#plano .pt").forEach((el, i) =>
    el.classList.toggle("on", i === actual));
}
const mini = $("#mini");
function montarMini(){
  const cont = document.querySelector("#plano .mapa");
  const n = PANOS.length;
  const iw = mini.naturalWidth || 1, ih = mini.naturalHeight || 1;
  const [x0, z0, x1, z1] = TEX_RECT;
  PANOS.forEach((p, i) => {
    const el = document.createElement("div");
    el.className = "pt";
    const u = (p.x - x0) / (x1 - x0);
    const v = (p.z - z0) / (z1 - z0);
    el.style.left = (u * 100) + "%";
    el.style.top = (v * 100) + "%";
    el.title = p.nombre;
    el.addEventListener("click", () => ir(i));
    cont.appendChild(el);
  });
}
function montarTira(){
  const t = $("#tira");
  PANOS.forEach((p, i) => {
    const b = document.createElement("button");
    b.textContent = p.nombre;
    b.addEventListener("click", () => ir(i));
    t.appendChild(b);
  });
  pintarTira();
}

/* ── controles ── */
const cvs = $("#c");
let drag = null;
cvs.addEventListener("pointerdown", e => {
  cvs.setPointerCapture(e.pointerId);
  drag = {x: e.clientX, y: e.clientY};
  cvs.classList.add("drag");
  giro && setGiro(false);
});
cvs.addEventListener("pointermove", e => {
  if (!drag) return;
  yawT -= (e.clientX - drag.x) * 0.0032;
  pitchT = Math.min(Math.max(pitchT + (e.clientY - drag.y) * 0.0032, -1.30), 1.30);
  drag = {x: e.clientX, y: e.clientY};
});
addEventListener("pointerup", () => { drag = null; cvs.classList.remove("drag"); });
cvs.addEventListener("wheel", e => {
  e.preventDefault();
  fovT = Math.min(Math.max(fovT + Math.sign(e.deltaY) * 4, 32), 100);
}, {passive: false});
let pin = null, toques = new Map();
cvs.addEventListener("touchstart", e => {
  for (const t of e.changedTouches) toques.set(t.identifier, {x: t.clientX, y: t.clientY});
  if (toques.size === 2){
    const [a, b] = [...toques.values()];
    pin = {d: Math.hypot(a.x - b.x, a.y - b.y), fov: fovT};
  }
}, {passive: true});
cvs.addEventListener("touchmove", e => {
  if (toques.size === 2 && pin){
    for (const t of e.changedTouches) toques.set(t.identifier, {x: t.clientX, y: t.clientY});
    const [a, b] = [...toques.values()];
    const d = Math.hypot(a.x - b.x, a.y - b.y);
    fovT = Math.min(Math.max(pin.fov * pin.d / d, 32), 100);
  }
}, {passive: true});
cvs.addEventListener("touchend", e => {
  for (const t of e.changedTouches) toques.delete(t.identifier);
  if (toques.size < 2) pin = null;
}, {passive: true});

function setGiro(v){
  giro = v;
  $("#b-giro").setAttribute("aria-pressed", String(v));
}
$("#b-giro").addEventListener("click", () => setGiro(!giro));
$("#b-full").addEventListener("click", () => {
  document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
});
addEventListener("keydown", e => {
  const k = e.key;
  if (k === "ArrowLeft") yawT += 0.12;
  else if (k === "ArrowRight") yawT -= 0.12;
  else if (k === "ArrowUp") pitchT = Math.min(pitchT + 0.08, 1.30);
  else if (k === "ArrowDown") pitchT = Math.max(pitchT - 0.08, -1.30);
  else if (k === "PageDown") ir(actual + 1);
  else if (k === "PageUp") ir(actual - 1);
  else if (k === " "){ e.preventDefault(); setGiro(!giro); }
});

/* ── bucle ── */
function tick(){
  requestAnimationFrame(tick);
  if (giro) yawT += 0.0016;
  const k = reduce ? 1 : 0.14;
  yaw += (yawT - yaw) * k;
  pitch += (pitchT - pitch) * k;
  camera.rotation.set(pitch, yaw, 0, "YXZ");
  if (Math.abs(camera.fov - fovT) > 0.05){
    camera.fov += (fovT - camera.fov) * k;
    camera.updateProjectionMatrix();
  }
  actualizarMarcas();
  renderer.render(scene, camera);
}
function resize(){
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight, false);
}
addEventListener("resize", resize);
resize();
montarMini();
montarTira();
requestAnimationFrame(tick);

let pendientes = PANOS.length, listos = 0;
const pre = {};
$("#loadbar").style.width = "8%";
PANOS.forEach((p, i) => {
  const im = new Image();
  im.onload = () => { pre[i] = true; listos++; avanza(); };
  im.onerror = () => { pre[i] = false; listos++; avanza(); };
  im.src = p.src;
});
function avanza(){
  {
    listos = listos;
    $("#loadbar").style.width = (8 + 92 * listos / pendientes) + "%";
    if (listos === pendientes && !arrancado){
      arrancado = true;
      const ok = Object.values(pre).filter(Boolean).length;
      if (ok === 0){
        errorPanos("No se ha podido cargar ningún panorama." + (PANOS[0].src.indexOf("data:") === 0 ? "" :
          "<br>Abre <b>tour3d.html</b> desde la carpeta del proyecto (junto a " +
          "<b>renders/panos/</b>) o usa la versión autocontenida."));
        return;
      }
      $("#load").classList.add("done");
      ir(0, true);
    }
  }
}
</script>
</body>
</html>
"""

EMBEBER = "--no-embed" not in sys.argv


def url_pano(pid: str) -> str:
    f = ROOT / PDF / f"{pid}.jpg"
    if not EMBEBER:
        return f"{PDF}/{pid}.jpg"
    if not f.exists():
        raise SystemExit(f"Falta {f} (genera antes los panoramas)")
    return "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode("ascii")


PANOS_JS = json.dumps(
    [{"id": p["id"], "nombre": p["nombre"], "x": p["x"], "z": p["z"], "yaw": p["yaw"],
      "file": f"{PDF}/{p['id']}.jpg", "src": url_pano(p["id"])} for p in PANOS],
    ensure_ascii=False, separators=(",", ":"))

TEXTURA_SRC = ("data:image/jpeg;base64," + base64.b64encode(TEXTURA_JPG.read_bytes()).decode("ascii")
               if EMBEBER else "data/imagenes/planta_textura.jpg")

html = (HTML
        .replace("__THREE__", THREE)
        .replace("__PANOS__", PANOS_JS)
        .replace("__TEXTURA__", TEXTURA_SRC)
        .replace("__TEX_RECT__", json.dumps(TEX))
        .replace("__FECHA__", date.today().strftime("%d/%m/%Y")))
OUT.write_text(html, encoding="utf-8")
print(f"escrito {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1024:.0f} KB)")
