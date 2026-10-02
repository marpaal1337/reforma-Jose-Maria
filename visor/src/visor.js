"use strict";
const PLAN = __DATA__;
const TEX_SRC = "data:image/jpeg;base64,__TEXTURE__";
const ENV_SRC = "__ENV_SRC__";
const TEXTURAS_SRC = __TEXTURAS_JS__;
const MOBILIARIO_B64 = leerBlob("d-mob");
const MOBILIARIO_SRC = "__MOB_SRC__";
function leerBlob(id){
  const el = document.getElementById(id);
  if(!el) return "";
  const txt = el.textContent.trim();
  el.remove();   // el bloque ya no hace falta en la página
  return txt;
}

/* ── paleta de estancias ── */
const STYLE = {
  "dorm-principal": {c:0xC07A4E, label:"Dormitorio principal"},
  "dorm-2":         {c:0x7E9DB8, label:"Dormitorio 2"},
  "dorm-3":         {c:0xB08D9A, label:"Dormitorio 3"},
  "vestidor":       {c:0xC9B072, label:"Vestidor"},
  "bano-1":         {c:0x6FA8A0, label:"Baño 1 (ducha)"},
  "bano-2":         {c:0x8FAEC4, label:"Baño 2 (bañera)"},
  "cocina":         {c:0x9CB48A, label:"Cocina"},
  "salon":          {c:0xD89A50, label:"Salón · comedor"},
  "estudio":        {c:0xB58BB0, label:"Estudio"},
  "pasillo":        {c:0xBFBAAD, label:"Pasillo"},
  "recibidor":      {c:0xC4A87E, label:"Recibidor"},
  "lavadero":       {c:0x9FB3A6, label:"Lavadero"},
  "terraza":        {c:0xA97A4E, label:"Balcón"}
};
const ZONES = PLAN.estancias.filter(e => STYLE[e.id]);

/* renders y documentación en data/reales/ (aportados por el cliente) */
const RENDERS = {
  "salon": [
    {src:"data/reales/salon-render.jpeg",        cap:"Salón · ventanal a terraza"},
    {src:"data/reales/salon2-render.jpeg",       cap:"Salón · pilar visto y mueble de TV"},
    {src:"data/reales/salon-cocina_render.jpeg", cap:"Salón-comedor · cocina al fondo"}
  ],
  "cocina": [
    {src:"data/reales/cocina-render.jpeg",       cap:"Cocina · isla de piedra"},
    {src:"data/reales/salon-cocina_render.jpeg", cap:"Cocina · vista al comedor"}
  ],
  "dorm-principal": [{src:"data/reales/dormitorio-principal-render.jpeg", cap:"Dormitorio principal · armario y cabecero de listones"}],
  "bano-2": [{src:"data/reales/baño-principal-render.jpeg", cap:"Baño · bañera y revestimiento pétreo"}]
};
const INTERIOR = ZONES.filter(e => e.id !== "terraza");
const PANEL_ZONAS = INTERIOR.concat(ZONES.filter(e => e.id === "terraza"));
const AREA_INT = INTERIOR.reduce((s,e)=>s+e.area,0);

/* ── utilidades ── */
const $ = s => document.querySelector(s);
const COARSE = matchMedia("(pointer:coarse)").matches;
const esMovil = () => COARSE || innerWidth <= 860;
function syncMovil(){ document.body.classList.toggle("movil", esMovil()); }
syncMovil();
let toastTO = 0;
function toast(msg, ms=3400){
  const el = $("#toast");
  el.textContent = msg;
  el.classList.add("on");
  clearTimeout(toastTO);
  toastTO = setTimeout(()=>el.classList.remove("on"), ms);
}
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
let realista = false;   // modo Realista (ver visor/src/realista.js)
const fmt = (v,d=1) => v.toLocaleString("es-ES",{minimumFractionDigits:d,maximumFractionDigits:d});

function shapeFrom(pts){
  const s = new THREE.Shape();
  pts.forEach(([x,z],i)=> i ? s.lineTo(x,-z) : s.moveTo(x,-z));
  s.closePath();
  return s;
}

/* ── escena ── */
let renderer, scene, camera;
try{
  renderer = new THREE.WebGLRenderer({canvas:$("#c"),antialias:true,alpha:true});
}catch(e){
  $("#loader").classList.add("done");
  $("#fallback").style.display="grid";
  const w = $("#fb-why");
  if(w) w.textContent = "Detalle técnico: " + (e && e.message ? e.message : "no se pudo crear el contexto WebGL");
  throw e;
}
/* resolución adaptativa: 1 mientras la cámara se mueve, completa al parar */
const PR_MAX = Math.min(devicePixelRatio, COARSE ? 1.5 : 2);
let prActual = PR_MAX;
function setPixelRatio(pr){
  if(Math.abs(pr-prActual) < 1e-6) return;
  prActual = pr;
  renderer.setPixelRatio(pr);
}
renderer.setPixelRatio(PR_MAX);
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.92;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;
renderer.shadowMap.needsUpdate = true;

/* bucle bajo demanda: sólo se dibuja cuando algo cambia (cámara, teclas,
   sol, selección…). En reposo la GPU queda a cero. */
let rafId = 0;
function pedirFrame(){ if(!rafId) rafId = requestAnimationFrame(tick); }

scene = new THREE.Scene();
const FAR_CIUDAD = 5000;   // modo Realista: la ciudad OSM (el cielo a 0,9·far)
camera = new THREE.PerspectiveCamera(38, 1, 0.1, 300);
camera.position.set(12,14,16);

/* entorno para reflejos PBR (el HDRI reducido del render; si no, degradado) */
const pmrem = new THREE.PMREMGenerator(renderer);
function aplicarEntorno(tex){
  tex.mapping = THREE.EquirectangularReflectionMapping;
  const vieja = scene.environment;
  scene.environment = pmrem.fromEquirectangular(tex).texture;
  if(vieja && vieja.dispose) vieja.dispose();
  if(tex.dispose) tex.dispose();
}
const envCanvas = document.createElement("canvas");
envCanvas.width = 64; envCanvas.height = 32;
const ectx = envCanvas.getContext("2d");
const grad = ectx.createLinearGradient(0, 0, 0, 32);
grad.addColorStop(0, "#e8eef3"); grad.addColorStop(0.48, "#f7f2e8"); grad.addColorStop(1, "#a89c89");
ectx.fillStyle = grad; ectx.fillRect(0, 0, 64, 32);
aplicarEntorno(new THREE.CanvasTexture(envCanvas));
if(ENV_SRC){
  const img = new Image();
  img.onload = ()=>{ const t = new THREE.Texture(img); t.needsUpdate = true; aplicarEntorno(t); };
  img.onerror = ()=>{ /* se queda el degradado */ };
  img.src = ENV_SRC;
}

/* luces */
const hemi = new THREE.HemisphereLight(0xFFFDF6, 0xCFC6B6, 0.66);
scene.add(hemi);
/* shadowMap.autoUpdate=false: el mapa de sombras sólo se recalcula cuando
   se mueve el sol o cambia el mobiliario visible */
let sombrasSucias = true;
const sun = new THREE.DirectionalLight(0xFFF2DE, 0.92);
sun.castShadow = true;
sun.shadow.mapSize.set(COARSE?1024:2048, COARSE?1024:2048);
sun.shadow.camera.near = 1; sun.shadow.camera.far = 70;
sun.shadow.camera.left = -14; sun.shadow.camera.right = 14;
sun.shadow.camera.top = 14; sun.shadow.camera.bottom = -14;
sun.shadow.bias = -0.0006;
sun.shadow.normalBias = 0.03;
sun.shadow.camera.updateProjectionMatrix();
scene.add(sun, sun.target);
/* el sol no sigue a la cámara: se centra en la vivienda */
const SOMBRA_C = new THREE.Vector3(
  (PLAN.bounds.x0 + PLAN.bounds.x1) / 2, 0, (PLAN.bounds.z0 + PLAN.bounds.z1) / 2);
function orientarSol(angDeg){
  const rad = angDeg*Math.PI/180;
  sun.position.set(SOMBRA_C.x + Math.cos(rad)*16, 15, SOMBRA_C.z + Math.sin(rad)*16);
  sun.target.position.copy(SOMBRA_C);
  sun.target.updateMatrixWorld();
  sombrasSucias = true;
  pedirFrame();
}
orientarSol(140);
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

/* Muros fusionados por tipo (estructural/tabique/vidrio → 3 mallas) y los
   contornos en un solo LineSegments, en vez de una malla y un contorno por
   muro (~180 draw calls menos). Altura fija de 2,60 m. */
function geoFusionada(geos){
  let nCap = 0, nLado = 0;
  geos.forEach(g => g.groups.forEach(gr => {
    if(gr.materialIndex === 0) nCap += gr.count; else nLado += gr.count;
  }));
  const pos = new Float32Array((nCap+nLado)*3);
  const nor = new Float32Array((nCap+nLado)*3);
  const uv = new Float32Array((nCap+nLado)*2);
  let vc = 0, vl = nCap;
  geos.forEach(g => g.groups.forEach(gr => {
    const dst = gr.materialIndex === 0 ? vc : vl;
    pos.set(g.attributes.position.array.subarray(gr.start*3, (gr.start+gr.count)*3), dst*3);
    nor.set(g.attributes.normal.array.subarray(gr.start*3, (gr.start+gr.count)*3), dst*3);
    uv.set(g.attributes.uv.array.subarray(gr.start*2, (gr.start+gr.count)*2), dst*2);
    if(gr.materialIndex === 0) vc += gr.count; else vl += gr.count;
  }));
  const fusion = new THREE.BufferGeometry();
  fusion.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  fusion.setAttribute("normal", new THREE.BufferAttribute(nor, 3));
  fusion.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
  fusion.addGroup(0, nCap, 0);
  if(nLado) fusion.addGroup(nCap, nLado, 1);
  return fusion;
}
const MATERIAL_MURO = {
  estructural: [matTapa, matMuro], tabique: [matTapaTab, matTabique], vidrio: [matVidrio],
};
{
  const porTipo = {estructural: [], tabique: [], vidrio: []};
  const contornos = [];
  PLAN.muros.forEach(w => {
    const geo = new THREE.ExtrudeGeometry(shapeFrom(w.pts), {depth:ALTURA, bevelEnabled:false});
    geo.rotateX(-Math.PI/2);
    (porTipo[w.tipo] || porTipo.tabique).push(geo);
    contornos.push(new THREE.EdgesGeometry(geo, 24).attributes.position.array);
  });
  ["estructural", "tabique", "vidrio"].forEach(tipo => {
    const geos = porTipo[tipo];
    if(!geos.length) return;
    const geo = geoFusionada(geos);
    if(tipo === "vidrio"){ geo.clearGroups(); geo.addGroup(0, geo.attributes.position.count, 0); }
    const mesh = new THREE.Mesh(geo, MATERIAL_MURO[tipo]);
    mesh.castShadow = tipo !== "vidrio";
    mesh.receiveShadow = true;
    gMuros.add(mesh);
  });
  const n = contornos.reduce((s,a)=>s+a.length, 0);
  const arr = new Float32Array(n);
  let o = 0;
  contornos.forEach(a => { arr.set(a, o); o += a.length; });
  const gl = new THREE.BufferGeometry();
  gl.setAttribute("position", new THREE.BufferAttribute(arr, 3));
  gLineas.add(new THREE.LineSegments(gl, matLinea));
}

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
  : id.indexOf("bano")===0 ? {tex:"travertino_porc", escala:1.0}
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
  gSuelo.visible = (m==="plan") && !realista;
  gZonas.visible = (m==="zonas") && !realista;
  gAlicatados.visible = (m==="zonas") && !realista;
  $("#m-plan").setAttribute("aria-pressed", String(m==="plan"));
  $("#m-zonas").setAttribute("aria-pressed", String(m==="zonas"));
  $("#mb-suelo-txt").textContent = m==="plan" ? "Plano" : "Zonas";
  $("#mb-suelo").setAttribute("aria-pressed", String(m==="zonas"));
  pedirFrame();
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
const _look = new THREE.Vector3();
function applyCamera(snap){
  if(snap){ ctrl.target.copy(ctrl.target2); ctrl.theta=ctrl.theta2; ctrl.phi=ctrl.phi2; ctrl.dist=ctrl.dist2; }
  const sp = new THREE.Spherical(ctrl.dist, ctrl.phi, ctrl.theta);
  camera.position.setFromSpherical(sp).add(ctrl.target);
  /* con la ficha abierta en móvil, sube la estancia sobre la hoja */
  const desvio = (esMovil() && $("#card").classList.contains("show")) ? ctrl.dist*0.17 : 0;
  _look.set(ctrl.target.x, ctrl.target.y - desvio, ctrl.target.z);
  camera.lookAt(_look);
}
function flyTo(o){
  interactuado = true;
  ctrl.target2.set(o.x??ctrl.target.x, o.y??0, o.z??ctrl.target.z);
  ctrl.theta2 = o.theta ?? ctrl.theta;
  ctrl.phi2 = Math.min(Math.max(o.phi ?? ctrl.phi, 0.12), 1.5);
  ctrl.dist2 = o.dist ?? ctrl.dist;
  pedirFrame();
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
/* colisiones con el mobiliario: huellas convexas en planta generadas por
   scripts/revisar_mobiliario.py (data/colisiones.json). El mobiliario está
   siempre visible, así que todas las huellas están activas. */
const COLISIONES = __COLISIONES__;
const RADIO_MOB = 0.26;   // algo menor que el de los muros: pasos más cómodos
function empujarPoligono(p, pts){
  let mejor = 1e9, mx = 0, mz = 0, dentro = false;
  for(let i=0, j=pts.length-1; i<pts.length; j=i++){
    const ax=pts[j][0], az=pts[j][1], bx=pts[i][0], bz=pts[i][1];
    const ex=bx-ax, ez=bz-az;
    const L2=ex*ex+ez*ez || 1e-9;
    let t=((p.x-ax)*ex+(p.z-az)*ez)/L2;
    t=t<0?0:(t>1?1:t);
    const qx=ax+ex*t, qz=az+ez*t;
    const d=Math.hypot(p.x-qx, p.z-qz);
    if(d<mejor){ mejor=d; mx=qx; mz=qz; }
    if(((az>p.z)!==(bz>p.z)) && (p.x < (bx-ax)*(p.z-az)/(bz-az)+ax)) dentro = !dentro;
  }
  if(!dentro && mejor >= RADIO_MOB) return false;
  let ex=p.x-mx, ez=p.z-mz;
  if(dentro){ ex=-ex; ez=-ez; }
  let d=Math.hypot(ex, ez);
  if(d<1e-5){ ex=p.x-pts[0][0]; ez=p.z-pts[0][1]; d=Math.hypot(ex, ez)||1; }
  p.x = mx + ex/d*RADIO_MOB;
  p.z = mz + ez/d*RADIO_MOB;
  return true;
}
const free = {pos:new THREE.Vector3(), yaw:0, pitch:0, vel:new THREE.Vector3()};
const keys = new Set();
let techosGLB = [];   // forjados y falsos del GLB: ocultos en órbita (maqueta)
const EYE = 1.62, RADIO = 0.30, V_WALK = 2.6, V_RUN = 5.0, V_FLY = 4.4, V_FLY_RUN = 9.0;
const joy = {x:0, y:0};
let camMode = "orbita";
const CAM_TXT = {orbita:"Órbita", caminar:"Caminar", vuelo:"Vuelo"};
const CAM_ORDEN = ["orbita","caminar","vuelo"];
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
    for(let i=0;i<COLISIONES.length;i++){
      const c=COLISIONES[i];
      const dx=p.x-c.c[0], dz=p.z-c.c[1], rr=c.r+RADIO_MOB;
      if(dx*dx+dz*dz > rr*rr) continue;
      if(empujarPoligono(p, c.p)) tocado=true;
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

let orbitGuardada = null;
/* near/far según el modo (sin logarithmicDepthBuffer): órbita = maqueta
   entera, caminar/vuelo = interior, Realista = interior + ciudad a 5 km */
function configurarCamara(){
  if(realista){ camera.near = 0.08; camera.far = FAR_CIUDAD; }
  else if(camMode === "orbita"){ camera.near = 0.1; camera.far = 300; }
  else { camera.near = 0.08; camera.far = 250; }
  camera.updateProjectionMatrix();
}
function setCamMode(m){
  if(m===camMode) return;
  if(m!=="orbita" && camMode==="orbita")
    orbitGuardada = {target:ctrl.target2.clone(), theta:ctrl.theta2, phi:ctrl.phi2, dist:ctrl.dist2};
  camMode = m;
  if(m==="orbita"){
    if(orbitGuardada && dentroDeHuella(camera.position.x, camera.position.z)){
      /* si venimos de caminar por dentro, recupera la vista general anterior */
      ctrl.target2.copy(orbitGuardada.target);
      ctrl.theta2=orbitGuardada.theta; ctrl.phi2=orbitGuardada.phi; ctrl.dist2=orbitGuardada.dist;
    }else{
      const fwd=camera.getWorldDirection(new THREE.Vector3());
      ctrl.target2.copy(camera.position).addScaledVector(fwd, Math.max(5, ctrl.dist*0.45));
      const sp=new THREE.Spherical().setFromVector3(camera.position.clone().sub(ctrl.target2));
      ctrl.dist2=Math.max(3.5,sp.radius); ctrl.theta2=sp.theta; ctrl.phi2=clampPitch(sp.phi);
    }
    orbitGuardada = null;
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
  configurarCamara();
  document.body.classList.toggle("libre", m!=="orbita");
  ["orbita","caminar","vuelo"].forEach(k=>$("#c-"+k)
    .setAttribute("aria-pressed", String(k===camMode)));
  $("#hint-orbita").hidden = m!=="orbita";
  $("#hint-libre").hidden = m==="orbita";
  $("#mb-cam-txt").textContent = CAM_TXT[m];
  $("#mb-cam").setAttribute("aria-pressed", String(m!=="orbita"));
  $("#mb-cam").setAttribute("aria-label", "Cámara: "+CAM_TXT[m]);
  if(esMovil() && m!=="orbita")
    toast(m==="caminar" ? "Joystick para caminar · arrastra a la derecha para mirar"
                        : "Joystick para volar · toca «Cámara» para volver a Órbita");
  interactuado = true;
  pedirFrame();
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
  pedirFrame();
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
  pedirFrame();
}
function stickReset(){ joy.x=joy.y=0; stickKnob.style.transform=""; stickId=null; stick.classList.remove("act"); }
/* el propio joystick también se puede agarrar directamente */
stick.addEventListener("pointerdown", e=>{
  if(camMode==="orbita" || stickId!==null) return;
  e.preventDefault();
  stick.setPointerCapture(e.pointerId);
  stickId = e.pointerId;
  stick.classList.add("act");
  navigator.vibrate && navigator.vibrate(8);
  stickMove(e);
});
stick.addEventListener("pointermove", e=>{
  if(e.pointerId===stickId) stickMove(e);
});

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
    const s = stick.getBoundingClientRect().width || 124;
    stick.style.left = (e.clientX-s/2)+"px";
    stick.style.top = (e.clientY-s/2)+"px";
    stick.style.bottom = "auto";
    stick.classList.add("act");
    navigator.vibrate && navigator.vibrate(8);
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
      pedirFrame();
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
  pedirFrame();
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
  pedirFrame();
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
    pedirFrame();
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
    pedirFrame();
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
  pedirFrame();
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
  if(!z){ card.classList.remove("show"); actualizarScrim(); return; }
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
  $("#card-zona").textContent = ZONA_USO[z.id] ?? "—";
  $("#card-note").textContent = "Superficie medida sobre el plano (escala 1:50).";
  card.classList.add("show");
  if(esMovil()){
    cerrarPanel();
    navigator.vibrate && navigator.vibrate(10);
  }
  actualizarScrim();
  if(camMode!=="orbita") setCamMode("orbita");
  const box = zoneBounds(z.pts);
  const d = Math.max(box.w, box.h);
  flyTo({x:box.cx, z:box.cz, dist: Math.max(8, d*1.7), phi:0.62});
}
$("#card-close").addEventListener("click", ()=>{ selected=null; select(null); });
/* zona de uso por estancia */
const ZONA_USO = {"dorm-principal":"Noche","dorm-2":"Noche","dorm-3":"Noche",
  "vestidor":"Noche","bano-1":"Servicio","bano-2":"Servicio","cocina":"Día",
  "salon":"Día","estudio":"Día · trabajo","pasillo":"Circulación",
  "recibidor":"Circulación","lavadero":"Servicio","terraza":"Exterior"};

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
PANEL_ZONAS.slice().sort((a,b)=>b.area-a.area).forEach(z=>{
  const st = STYLE[z.id];
  const li = document.createElement("li");
  li.innerHTML = `<button data-id="${z.id}">
    <span class="swatch" style="background:#${st.c.toString(16).padStart(6,"0")}"></span>
    <span>${st.label}</span><span class="m2">${fmt(z.area)} m²</span></button>`;
  li.querySelector("button").addEventListener("click", ()=>select(z.id));
  list.appendChild(li);
});
$("#panel-count").textContent = `${PANEL_ZONAS.length} estancias`;
if(esMovil()){
  $("#panel").classList.add("hidden");
  $("#b-panel").setAttribute("aria-pressed","false");
  $("#mb-estancias").setAttribute("aria-expanded","false");
  labelsOn = false;
  $("#b-labels").setAttribute("aria-pressed","false");
  $("#mb-labels").setAttribute("aria-pressed","false");
}
$("#total").textContent = fmt(AREA_INT)+" m²";

/* ── controles ── */
function setLabels(on){
  labelsOn = on;
  $("#b-labels").setAttribute("aria-pressed", String(on));
  $("#mb-labels").setAttribute("aria-pressed", String(on));
  pedirFrame();
}
$("#m-plan").addEventListener("click", ()=>setMode("plan"));
$("#m-zonas").addEventListener("click", ()=>setMode("zonas"));
$("#b-labels").addEventListener("click", ()=>setLabels(!labelsOn));
$("#mb-labels").addEventListener("click", ()=>setLabels(!labelsOn));
$("#mb-suelo").addEventListener("click", ()=>setMode(mode==="plan" ? "zonas" : "plan"));
$("#mb-cam").addEventListener("click", ()=>{
  const i = CAM_ORDEN.indexOf(camMode);
  setCamMode(CAM_ORDEN[(i+1)%CAM_ORDEN.length]);
});

/* hojas móviles: panel de estancias y ficha de estancia */
const scrim = $("#scrim");
function actualizarScrim(){
  const panelAbierto = !$("#panel").classList.contains("hidden");
  /* la ficha no es modal: queda sobre la barra y deja girar el modelo */
  const modal = esMovil() && panelAbierto;
  scrim.classList.toggle("on", modal);
  document.body.classList.toggle("sheet-open", modal);
  $("#mb-estancias").setAttribute("aria-expanded", String(panelAbierto));
  $("#b-panel").setAttribute("aria-pressed", String(panelAbierto));
}
function abrirPanel(){
  $("#panel").classList.remove("hidden");
  actualizarScrim();
}
function cerrarPanel(){
  $("#panel").classList.add("hidden");
  actualizarScrim();
}
function togglePanel(){ $("#panel").classList.contains("hidden") ? abrirPanel() : cerrarPanel(); }
$("#b-panel").addEventListener("click", togglePanel);
$("#mb-estancias").addEventListener("click", togglePanel);
scrim.addEventListener("click", cerrarPanel);
/* asa: arrastrar hacia abajo para cerrar */
function hojaArrastrable(hoja, cerrar){
  const grip = hoja.querySelector(".grip");
  if(!grip) return;
  let id=null, y0=0, dy=0, t0=0;
  grip.addEventListener("pointerdown", e=>{
    if(e.button!==0) return;
    id=e.pointerId; y0=e.clientY; dy=0; t0=performance.now();
    grip.setPointerCapture(id);
    hoja.style.transition="none";
  });
  grip.addEventListener("pointermove", e=>{
    if(e.pointerId!==id) return;
    dy=Math.max(0, e.clientY-y0);
    hoja.style.transform=`translateY(${dy}px)`;
  });
  const fin = e=>{
    if(e.pointerId!==id) return;
    id=null;
    hoja.style.transition=""; hoja.style.transform="";
    if(dy>80 || (dy>24 && dy/(performance.now()-t0)>0.55)) cerrar();
    dy=0;
  };
  grip.addEventListener("pointerup", fin);
  grip.addEventListener("pointercancel", fin);
}
hojaArrastrable($("#panel"), cerrarPanel);
hojaArrastrable($("#card"), ()=>select(null));

/* hoja de acciones «Más» */
const actions = $("#actions");
function abrirAcciones(){ actions.hidden=false; $("#mb-more").setAttribute("aria-expanded","true"); }
function cerrarAcciones(){ actions.hidden=true; $("#mb-more").setAttribute("aria-expanded","false"); }
$("#mb-more").addEventListener("click", abrirAcciones);
$("#actions-scrim").addEventListener("click", cerrarAcciones);
hojaArrastrable(actions.querySelector(".sheet"), cerrarAcciones);
actions.querySelectorAll("[data-act]").forEach(b=>b.addEventListener("click", ()=>{
  const act = b.dataset.act;
  cerrarAcciones();
  if(act==="vista") $("#b-reset").click();
  else if(act==="planta") $("#b-planta").click();
  else if(act==="png") exportPNG();
  else if(act==="ayuda") abrirCoach();
}));

/* guía de primer uso */
const coach = $("#coach");
let coachVisto = false;
try{ coachVisto = localStorage.getItem("r3d_coach")==="1"; }catch(e){}
function abrirCoach(){ coach.hidden=false; }
function cerrarCoach(){
  coach.hidden=true;
  try{ localStorage.setItem("r3d_coach","1"); }catch(e){}
}
$("#coach-ok").addEventListener("click", cerrarCoach);
$("#coach-mas").addEventListener("click", ()=>{
  const ex = $("#coach-extra");
  ex.hidden = !ex.hidden;
  $("#coach-mas").textContent = ex.hidden ? "Más ayuda" : "Menos ayuda";
});
$("#b-help").addEventListener("click", abrirCoach);
coach.addEventListener("click", e=>{ if(e.target===coach) cerrarCoach(); });

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
$("#b-export").addEventListener("click", exportPNG);
addEventListener("keydown", e=>{
  const k = e.key.toLowerCase();
  if(["w","a","s","d","q","e","shift"," ","arrowup","arrowdown","arrowleft","arrowright"].includes(k)){
    if(camMode!=="orbita" && !(e.target.tagName==="INPUT")){
      keys.add(k);
      e.preventDefault();
      pedirFrame();
    }
  }
  if(e.key==="Escape"){
    if(document.pointerLockElement){ document.exitPointerLock(); return; }
    if(!actions.hidden){ cerrarAcciones(); return; }
    if(!coach.hidden){ cerrarCoach(); return; }
    if(!$("#panel").classList.contains("hidden")){ cerrarPanel(); return; }
    if($("#card").classList.contains("show")){ select(null); return; }
    if(camMode!=="orbita"){ setCamMode("orbita"); return; }
  }
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
  else if(k==="e") exportPNG();
});
addEventListener("keyup", e=>{ keys.delete(e.key.toLowerCase()); pedirFrame(); });

/* exportar PNG a 2x (en móvil usa la hoja de compartir si está disponible) */
function descargar(blob, nombre){
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = nombre;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(url), 4000);
}
function exportPNG(){
  const w = innerWidth, h = innerHeight;
  const pr = prActual;
  setPixelRatio(PR_MAX*2);
  renderer.setSize(w, h, false);
  renderer.render(scene, camera);
  const nombre = "render3d_reforma_vivienda_"+new Date().toISOString().slice(0,10)+".png";
  renderer.domElement.toBlob(blob=>{
    setPixelRatio(pr);
    renderer.setSize(w, h, false);
    pedirFrame();   // vuelve a pintar a la resolución normal
    if(!blob){ toast("No se pudo generar la imagen"); return; }
    const file = new File([blob], nombre, {type:"image/png"});
    if(esMovil() && navigator.canShare && navigator.canShare({files:[file]})){
      navigator.share({files:[file], title:"Reforma vivienda Valencia"})
        .catch(err=>{ if(!err || err.name!=="AbortError") descargar(blob, nombre); });
    }else{
      descargar(blob, nombre);
      if(esMovil()) toast("Imagen guardada en Descargas", 2600);
    }
  }, "image/png");
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

/* ── bucle bajo demanda ── */
/* `intro` queda fijo en 1: la altura de muros ya no se anima (2,60 m) */
let intro = 1, ready = false, maquetaLista = false, prevT = 0, ultimoAnimando = false;
window.__visor = {scene, camera, renderer, gMob, free, setCamMode, pedirFrame, colisionar,
  get modo(){ return camMode; }, get listo(){ return ready; },
  get realista(){ return realista; }, get maquetaLista(){ return maquetaLista; },
  get intro(){ return intro; }, get animando(){ return ultimoAnimando; },
  get colisiones(){ return COLISIONES.length; }, setRealista};

/* indicador opcional ?perf (fps reales en una máquina con GPU) */
const PERF = /(?:^|[?&])perf(?:=1)?(?:&|$)/.test(location.search);
if(PERF) $("#perf").hidden = false;
let perfT = 0, fpsSuave = 0;
function actualizarPerf(t){
  const ms = perfT ? t-perfT : 0;
  perfT = t;
  if(ms > 0){ const fps = 1000/ms; fpsSuave = fpsSuave ? fpsSuave*0.9 + fps*0.1 : fps; }
  const i = renderer.info;
  $("#perf").textContent =
    `${fpsSuave ? fpsSuave.toFixed(0) : "—"} fps · ${ms ? ms.toFixed(1) : "—"} ms · PR ${renderer.getPixelRatio().toFixed(1)}\n`+
    `${i.render.calls} draws · ${(i.render.triangles/1000).toFixed(1)}k tris · ${i.programs ? i.programs.length : 0} programas\n`+
    `${i.memory.geometries} geometrías · ${i.memory.textures} texturas`;
}
function tick(t){
  rafId = 0;
  const dt = prevT ? Math.min(0.05, (t-prevT)/1000) : 0.016;
  prevT = t;
  let animando = false;
  if(drag && !drag.pan) cvs.style.cursor="grabbing";
  if(camMode==="orbita"){
    const k = reduceMotion ? 1 : 0.12;
    const d = Math.abs(ctrl.theta2-ctrl.theta) + Math.abs(ctrl.phi2-ctrl.phi)
            + Math.abs(ctrl.dist2-ctrl.dist) + ctrl.target.distanceTo(ctrl.target2);
    if(d > 1e-4){
      ctrl.target.lerp(ctrl.target2, k);
      ctrl.theta += (ctrl.theta2-ctrl.theta)*k;
      ctrl.phi += (ctrl.phi2-ctrl.phi)*k;
      ctrl.dist += (ctrl.dist2-ctrl.dist)*k;
      animando = true;
    }else if(d > 0){
      ctrl.target.copy(ctrl.target2); ctrl.theta = ctrl.theta2;
      ctrl.phi = ctrl.phi2; ctrl.dist = ctrl.dist2;
    }
    applyCamera(false);
  }else{
    moverLibre(dt);
    if(!keys.size && !drag && Math.abs(joy.x)+Math.abs(joy.y) < 0.01 && free.vel.lengthSq() < 1e-5)
      free.vel.set(0,0,0);
    animando = keys.size > 0 || !!drag || Math.abs(joy.x)+Math.abs(joy.y) > 0.01
            || free.vel.lengthSq() > 1e-5;
  }
  if(techosGLB.length){
    /* histéresis: muestra bajo 2,40 y oculta sobre 2,50 (sin parpadeo) */
    const y = camera.position.y;
    const ver = y < 2.40 ? true : (y > 2.50 ? false : techosGLB[0].visible);
    if(ver !== techosGLB[0].visible){ techosGLB.forEach(o => o.visible = ver); sombrasSucias = true; }
  }
  actualizarRealista();
  setPixelRatio(animando ? 1 : PR_MAX);
  camera.updateMatrixWorld();   // si no, las etiquetas usan la cámara del fotograma anterior
  updateLabels();
  if(sombrasSucias && ready){ renderer.shadowMap.needsUpdate = true; sombrasSucias = false; }
  renderer.render(scene, camera);
  if(PERF) actualizarPerf(t);
  ultimoAnimando = animando;
  /* al parar el bucle, el siguiente arranque no debe calcular dt con el tiempo dormido */
  if(!animando) prevT = 0;
  if(animando) pedirFrame();
}
function resize(){
  camera.aspect = innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight, false);
  syncMovil();
  actualizarScrim();
  setLabels(labelsOn);
  setMode(mode);
  if(!interactuado) aplicarVistaInicial();
  pedirFrame();
}
addEventListener("resize", resize);
addEventListener("orientationchange", ()=>setTimeout(()=>{ resize(); }, 260));
resize();
aplicarVistaInicial();
applyCamera(true);
setMode("plan");

