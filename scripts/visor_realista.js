/* ══ Modo Realista ═══════════════════════════════════════════════════════════
   Interior con la luz de Cycles horneada (lightmaps) y las texturas PBR del
   render, y la ciudad real (OSM) alrededor, a la altura del 7º piso.
   Recursos: scripts/hornear_visor.py -> data/visor/ (inyectados por
   scripts/generar_visor3d.py). Coordenadas Three.js: x = X, y = Z, z = -Y de
   Blender; el suelo de la calle está en REAL.info.suelo.y. El JSON viaja en
   una etiqueta de datos inerte (no se parsea como JS). */
const REAL = (() => {
  const el = document.getElementById("d-real");
  if(!el) return null;
  const txt = el.textContent;
  el.remove();   // el JSON ya no hace falta en la página
  try{ return JSON.parse(txt); }
  catch(e){ console.warn("Realista: JSON ilegible", e); return null; }
})();
let realListo = false;   // `realista` se declara al principio del script
const gReal = new THREE.Group(), gCiudad = new THREE.Group();
gReal.visible = gCiudad.visible = false;
scene.add(gReal, gCiudad);
renderer.localClippingEnabled = true;
const planoCorte = new THREE.Plane(new THREE.Vector3(0, -1, 0), 99);  // recorta y > constante
const ocultarEnOrbita = [];
const lucesMaqueta = [];
scene.traverse(o => { if(o.isLight) lucesMaqueta.push([o, o.intensity]); });
const PLANTA_ED = 2.95, BAJO_ED = 4.0;

/* Curva AgX (la vista «AgX - Base Contrast» de Cycles) para el modo Realista */
THREE.ShaderChunk.tonemapping_pars_fragment = THREE.ShaderChunk.tonemapping_pars_fragment.replace(
  "vec3 CustomToneMapping( vec3 color ) { return color; }", `
vec3 agxContraste( vec3 x ){
  vec3 x2 = x * x; vec3 x4 = x2 * x2;
  return 15.5 * x4 * x2 - 40.14 * x4 * x + 31.96 * x4 - 6.868 * x2 * x + 0.4298 * x2 + 0.1191 * x - 0.00232;
}
vec3 CustomToneMapping( vec3 color ){
  const mat3 entrada = mat3( 0.842479062253094, 0.0423282422610123, 0.0423756549057051,
                             0.0784335999999992, 0.878468636469772, 0.0784336,
                             0.0792237451477643, 0.0791661274605434, 0.879142973793104 );
  const mat3 salida = mat3( 1.19687900512017, -0.0528968517574562, -0.0529716355144438,
                            -0.0980208811401368, 1.15190312990417, -0.0980434501171241,
                            -0.0990297440797205, -0.0989611768448433, 1.15107367264116 );
  const float evMin = -12.47393, evMax = 4.026069;
  color = entrada * max( color * toneMappingExposure, vec3( 1e-10 ) );
  color = clamp( log2( color ), evMin, evMax );
  color = agxContraste( ( color - evMin ) / ( evMax - evMin ) );
  return pow( max( salida * color, vec3( 0.0 ) ), vec3( 2.2 ) );
}`);

/* la lightmap ya contiene toda la luz difusa: fuera la irradiancia del entorno */
function sinIrradianciaIBL(sh){
  sh.fragmentShader = sh.fragmentShader.replace("#include <lights_fragment_maps>",
    THREE.ShaderChunk.lights_fragment_maps.replace("iblIrradiance += getIBLIrradiance( geometry.normal );", ""));
}

function texDesde(src, flipY=true, srgb=true){
  return new Promise(res=>{
    if(!src){ res(null); return; }
    const img = new Image();
    img.onload = ()=>{
      const t = new THREE.Texture(img);
      t.flipY = flipY;
      if(srgb) t.encoding = THREE.sRGBEncoding;
      t.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
      t.needsUpdate = true;
      res(t);
    };
    img.onerror = ()=>res(null);
    img.src = src;
  });
}
function envDesde(t){
  t.mapping = THREE.EquirectangularReflectionMapping;
  t.needsUpdate = true;
  return pmrem.fromEquirectangular(t).texture;
}
function rng(sem){ return ()=>{ sem |= 0; sem = sem + 0x6D2B79F5 | 0;
  let t = Math.imul(sem ^ sem >>> 15, 1 | sem); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
  return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

/* ── fachadas: retícula de ventanas como el material de Blender ── */
const PALETA = [[0.60,0.38,0.27],[0.63,0.53,0.41],[0.72,0.68,0.61],[0.64,0.46,0.40],
                [0.60,0.47,0.27],[0.38,0.17,0.11],[0.53,0.51,0.49]];
const CUBIERTAS = [[0.42,0.19,0.14],[0.50,0.30,0.25],[0.55,0.54,0.50],[0.46,0.24,0.18]];
function matFachada(propio){
  const i = REAL.info, s = i.sol, c = i.cielo;
  const senSol = Math.max(0, s.dir[1]);
  const uni = {
    uSol: {value: new THREE.Vector3(...s.dir).normalize()},
    uSolE: {value: new THREE.Color().setRGB(s.color[0]*s.E, s.color[1]*s.E, s.color[2]*s.E)},
    uCielo: {value: new THREE.Color().setRGB(c.color[0]*c.E_up, c.color[1]*c.E_up, c.color[2]*c.E_up)},
    uSuelo: {value: 0.3*(s.E*senSol + c.E_up)},
    uHorizonte: {value: new THREE.Color().setRGB(...c.horizonte)},
    uNiebla: {value: 0.0009},
    uClipY: {value: 1e9},
    uVFlip: {value: propio ? 1 : 0},
    uPaleta: {value: PALETA.map(p=>new THREE.Vector3(...p))},
    uCubiertas: {value: CUBIERTAS.map(p=>new THREE.Vector3(...p))}
  };
  return new THREE.ShaderMaterial({
    uniforms: uni, side: THREE.DoubleSide,
    vertexShader: `
      #include <common>
      attribute float aSem;
      attribute float aTecho;
      attribute float aTop;
      uniform float uVFlip;
      varying vec2 vUv; varying float vSem; varying float vTecho; varying float vTop;
      varying vec3 vN; varying vec3 vPos;
      void main(){
        vUv = vec2(uv.x, mix(uv.y, 1.0 - uv.y, uVFlip));
        vSem = aSem;
        vTop = aTop;
        vN = normalize(mat3(modelMatrix) * normal);
        vTecho = max(aTecho, step(0.9, vN.y));
        vec4 w = modelMatrix * vec4(position, 1.0);
        vPos = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
      }`,
    fragmentShader: `
      #include <common>
      uniform vec3 uSol; uniform vec3 uSolE; uniform vec3 uCielo; uniform float uSuelo;
      uniform vec3 uHorizonte; uniform float uNiebla; uniform float uClipY; uniform float uVFlip;
      uniform vec3 uPaleta[7]; uniform vec3 uCubiertas[4];
      varying vec2 vUv; varying float vSem; varying float vTecho; varying float vTop;
      varying vec3 vN; varying vec3 vPos;
      float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
      vec3 palI(int i){ vec3 c = uPaleta[0];
        for(int k = 1; k < 7; k++) if(k == i) c = uPaleta[k];
        return c; }
      vec3 cubierta(float s){ int i = int(clamp(floor(s * 4.0), 0.0, 3.0));
        vec3 c = uCubiertas[0];
        for(int k = 1; k < 4; k++) if(k == i) c = uCubiertas[k];
        return c; }
      void main(){
        if(vPos.y > uClipY) discard;
        const float P = ${PLANTA_ED.toFixed(2)}, B = ${BAJO_ED.toFixed(2)}, ANCHO = 3.1, JUNTA = 0.8;
        vec3 Nf = normalize(vN) * (gl_FrontFacing ? 1.0 : -1.0);
        vec3 Vv = normalize(cameraPosition - vPos);
        float propio = uVFlip;
        vec3 alb; vec3 emis = vec3(0.0);
        if(vTecho > 0.5){
          /* cubierta: teja/grava con dos escalas de grano + hileras */
          vec3 cb = cubierta(vSem);
          cb = mix(vec3(dot(cb, vec3(0.3333))), cb, 0.85);
          float g1 = h21(floor(vPos.xz * 2.3) + floor(vSem * 997.0 + 0.5));
          float g2 = h21(floor(vPos.xz * 0.55) + floor(vSem * 57.0 + 0.5));
          float hilera = 0.90 + 0.10 * step(0.5, fract((vPos.x + vPos.z) * 1.35 + g1 * 0.6));
          alb = cb * (0.60 + 0.40 * g1) * (0.90 + 0.10 * g2) * hilera;
        }else{
          /* paleta continua en el espacio de semillas: los edificios con
             semilla vecina comparten tono (sin saltos entre tramos) */
          float sb = clamp(vSem * 7.0 - 0.5, 0.0, 6.0);
          float ft = smoothstep(0.30, 0.70, fract(sb));
          vec3 base = mix(palI(int(floor(sb))), palI(min(int(floor(sb)) + 1, 6)), ft);
          base = mix(base, vec3(0.60, 0.47, 0.35), 0.32);
          float vp = vUv.y - (B - P);
          /* semilla entera: el varying interpolado varía en el último bit y el
             hash lo amplifica (ruido píxel a píxel dentro de cada ventana) */
          float sem = floor(vSem * 997.0 + 0.5);
          vec2 celda = floor(vec2(vUv.x / ANCHO, vp / P));
          vec2 f = vec2(fract(vUv.x / ANCHO) * ANCHO, fract(vp / P) * P);
          float rnd = h21(celda + vec2(sem * 0.131, sem * 0.293));
          float vr = f.y / P;
          float planta = floor(vp / P);
          float cal = h21(vec2(sem * 3.1 + planta * 0.37, planta * 1.7 + sem));
          vec3 revoco = base * (0.95 + 0.10 * cal);
          revoco.r *= 1.0 + 0.06 * (cal - 0.5);
          revoco *= 0.96 + 0.08 * h21(floor(vUv * vec2(6.0, 9.0)) + sem);
          revoco *= 1.0 + 0.06 * sin(vPos.x * 0.33 + vPos.y * 0.17)
                             * sin(vPos.z * 0.29 - vPos.y * 0.11);
          float fr = fract(vp / P);
          revoco *= 0.90 + 0.10 * smoothstep(0.0, 0.12, fr);
          float dTop = vTop - vUv.y;
          revoco *= 1.0 - 0.32 * (1.0 - smoothstep(0.0, 0.5, dTop)) * step(0.5, vTop);
          float muro = (f.x < JUNTA || f.x > ANCHO - JUNTA || f.y < JUNTA || f.y > P - JUNTA) ? 1.0 : 0.0;
          /* persiana con lamas horizontales y guías laterales en sombra */
          float umbral = 0.73 - rnd * 0.42;
          float pers = (1.0 - muro) * step(umbral, vr);
          vec3 colP = fract(rnd * 5.3) > 0.55 ? vec3(0.68, 0.67, 0.64) : vec3(0.52, 0.46, 0.36);
          float lama = 0.74 + 0.26 * step(0.42, fract(vr * P / 0.055 + rnd));
          float guia = smoothstep(0.0, 0.09, f.x) * smoothstep(0.0, 0.09, ANCHO - f.x);
          colP *= lama * (0.68 + 0.32 * guia);
          vec3 hueco = mix(vec3(0.016, 0.02, 0.026), colP, pers);
          /* vidrio con reflejo de cielo/horizonte según ángulo (fresnel) */
          vec3 R = reflect(-Vv, Nf);
          vec3 cieloRefl = mix(uHorizonte, uCielo * 0.55, smoothstep(-0.05, 0.55, R.y));
          float tinte = 0.60 + 0.90 * fract(rnd * 7.31);
          cieloRefl = mix(cieloRefl, uCielo * 0.55, fract(rnd * 3.13) * 0.55);
          float calido = step(0.80, fract(rnd * 3.77));
          vec3 interior = mix(vec3(0.020, 0.026, 0.036), vec3(0.11, 0.075, 0.042), calido);
          float fres = mix(0.55, 1.0, pow(1.0 - max(dot(Nf, Vv), 0.0), 2.0));
          float mVid = (1.0 - muro) * (1.0 - pers);
          vec3 vid = mix(interior, cieloRefl * tinte, clamp(fres * (0.70 + 0.30 * tinte), 0.0, 1.0));
          vid += uSolE * pow(max(dot(R, uSol), 0.0), 60.0) * 0.020;
          /* balcón: antepecho + barrotes + pasamanos en la mitad baja */
          float balc = step(0.58, h21(vec2(sem * 1.71 + 3.0, celda.x * 1.37 + celda.y * 0.73)));
          float enBajo = (1.0 - muro) * (1.0 - pers) * balc * step(vr, 0.55) * step(JUNTA / P, vr);
          vec3 ant = revoco * 0.45;
          float barrote = step(fract(f.x / 0.30), 0.13);
          float pasam = 1.0 - smoothstep(0.015, 0.055, abs(vr - 0.55) * P);
          vec3 colB = mix(ant, vec3(0.030, 0.030, 0.035), max(barrote * 0.9, pasam));
          alb = mix(mix(hueco, revoco, muro), colB, enBajo);
          emis = vid * mVid * (1.0 - enBajo);
          /* base: degradado en los ~2 primeros metros (no en el propio) */
          float tb = (1.0 - smoothstep(0.0, 2.0, vUv.y)) * (1.0 - propio);
          alb = mix(alb, revoco * 0.30 + vec3(0.015), tb * 0.9);
          emis *= 1.0 - tb * 0.6;
        }
        float cielo = 0.5 + 0.5 * Nf.y;
        /* el sol directo (E=14) lo lava todo: se comprime solo ese término */
        vec3 Esol = uSolE * max(dot(Nf, uSol), 0.0);
        Esol = Esol / (1.0 + dot(Esol, vec3(0.3333)) * 0.50);
        vec3 E = Esol + uCielo * cielo + vec3(uSuelo) * (1.0 - cielo);
        vec3 col = alb * E * RECIPROCAL_PI;
        col = col / (1.0 + col * 0.15);
        col += emis;
        float d = length(vPos - cameraPosition);
        col = mix(col, uHorizonte, 1.0 - exp(-d * uNiebla));
        gl_FragColor = vec4(col, 1.0);
        #include <tonemapping_fragment>
        #include <encodings_fragment>
      }`
  });
}

function construirEdificios(){
  const Y0 = REAL.info.suelo.y, azar = rng(3);
  const pos = [], nor = [], uv = [], sem = [], tec = [], top = [];
  function v(x, y, z, n, u, w, s, t, h){ pos.push(x, y, z); nor.push(...n); uv.push(u, w); sem.push(s); tec.push(t); top.push(h); }
  REAL.edificios.forEach(([pts0, p])=>{
    p = p || 3;
    /* OSM trae contornos duplicados o solapados: cada edificio se encoge unos
       milímetros distintos para que no compitan en profundidad (moteado) */
    const cx = pts0.reduce((a, q) => a + q[0], 0) / pts0.length;
    const cy = pts0.reduce((a, q) => a + q[1], 0) / pts0.length;
    const k = 0.004 + 0.03 * azar();
    const pts = pts0.map(([x, y]) => { const d = Math.hypot(cx - x, cy - y) || 1;
      return [x + (cx - x) / d * k, y + (cy - y) / d * k]; });
    const h = p >= 3 ? BAJO_ED + (p - 1) * PLANTA_ED + 1.0 : p * 3.4;
    const s = 0.15 + 0.85 * azar();
    let acc = 0;
    for(let i = 0; i < pts.length; i++){
      const [ax, ay] = pts[i], [bx, by] = pts[(i + 1) % pts.length];
      const L = Math.hypot(bx - ax, by - ay);
      if(L < 0.01) continue;
      const n = [(by - ay) / L, 0, (bx - ax) / L];        // (dy, -dx) de Blender -> Three
      const A0 = [ax, Y0, -ay], B0 = [bx, Y0, -by], B1 = [bx, Y0 + h, -by], A1 = [ax, Y0 + h, -ay];
      [[A0, acc, 0], [B0, acc + L, 0], [B1, acc + L, h], [A0, acc, 0], [B1, acc + L, h], [A1, acc, h]]
        .forEach(([q, u, w]) => v(q[0], q[1], q[2], n, u, w, s, 0, h));
      acc += L;
    }
    const tri = THREE.ShapeUtils.triangulateShape(pts.map(q => new THREE.Vector2(q[0], q[1])), []);
    tri.forEach(t => t.forEach(k => v(pts[k][0], Y0 + h, -pts[k][1], [0, 1, 0], pts[k][0], pts[k][1], s, 1, h)));
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("normal", new THREE.Float32BufferAttribute(nor, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute("aSem", new THREE.Float32BufferAttribute(sem, 1));
  g.setAttribute("aTecho", new THREE.Float32BufferAttribute(tec, 1));
  g.setAttribute("aTop", new THREE.Float32BufferAttribute(top, 1));
  const m = new THREE.Mesh(g, matFachada(false));
  m.frustumCulled = false;
  gCiudad.add(m);
}

function planoSuelo(tex, conf, dy){
  const [x0, z0, x1, z1] = conf.rect, y = REAL.info.suelo.y + dy;
  const g = new THREE.BufferGeometry();
  /* UV de Blender: v crece hacia +Y (= -z en Three) */
  g.setAttribute("position", new THREE.Float32BufferAttribute(
    [x0, y, z1,  x1, y, z1,  x1, y, z0,  x0, y, z1,  x1, y, z0,  x0, y, z0], 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(
    [0, 0,  1, 0,  1, 1,  0, 0,  1, 1,  0, 1], 2));
  const m = new THREE.MeshBasicMaterial({map: tex, fog: true, side: THREE.DoubleSide});
  m.color.setRGB(conf.K, conf.K, conf.K);
  const mesh = new THREE.Mesh(g, m);
  mesh.renderOrder = -2;
  gCiudad.add(mesh);
}

function construirArboles(lado, planta){
  const A = REAL.info.arbol, lista = REAL.info.arboles || [];
  if(!A || !lista.length || !lado) return;
  const Y0 = REAL.info.suelo.y;
  const gl = new THREE.PlaneGeometry(1, 1);
  gl.translate(0, 0.5, 0);
  const gl2 = gl.clone().rotateY(Math.PI / 2);
  const gCruz = new THREE.BufferGeometry();
  const a = gl.toNonIndexed(), b = gl2.toNonIndexed();
  ["position", "uv"].forEach(k => {
    const arr = new Float32Array(a.attributes[k].array.length * 2);
    arr.set(a.attributes[k].array); arr.set(b.attributes[k].array, a.attributes[k].array.length);
    gCruz.setAttribute(k, new THREE.BufferAttribute(arr, a.attributes[k].itemSize));
  });
  const mLado = new THREE.MeshBasicMaterial({map: lado, alphaTest: 0.45, side: THREE.DoubleSide});
  const iLado = new THREE.InstancedMesh(gCruz, mLado, lista.length);
  let iPlanta = null;
  if(planta){
    const gp = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
    iPlanta = new THREE.InstancedMesh(gp, new THREE.MeshBasicMaterial(
      {map: planta, alphaTest: 0.45, side: THREE.DoubleSide}), lista.length);
  }
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
  lista.forEach(([x, z, h, w, rot], i) => {
    const s = h / A.alto, sxy = w / A.ancho;
    e.set(0, rot, 0); q.setFromEuler(e);
    M.compose(new THREE.Vector3(x, Y0 - A.z_base * s, z), q,
              new THREE.Vector3(A.lado * sxy, A.lado * s, A.lado * sxy));
    iLado.setMatrixAt(i, M);
    if(iPlanta){
      M.compose(new THREE.Vector3(x, Y0 + h * 0.8, z), q,
                new THREE.Vector3(A.lado * sxy, 1, A.lado * sxy));
      iPlanta.setMatrixAt(i, M);
    }
  });
  gCiudad.add(iLado);
  if(iPlanta) gCiudad.add(iPlanta);
}

let cieloMesh = null, nieblaReal = null, matPropio = null;
const mostrarEnOrbita = [];

/* tapa de sección sobre el edificio propio en la vista de maqueta (órbita),
   donde su volumen se recorta a la cota del suelo del piso */
function construirTapas(){
  (REAL.propios || []).forEach(pts => {
    const tri = THREE.ShapeUtils.triangulateShape(pts.map(q => new THREE.Vector2(q[0], q[1])), []);
    const pos = [], nor = [], uv = [], sem = [], tec = [], top = [];
    tri.forEach(t => t.forEach(k => { pos.push(pts[k][0], -0.035, -pts[k][1]); nor.push(0, 1, 0);
      uv.push(pts[k][0], pts[k][1]); sem.push(0.55); tec.push(1); top.push(0); }));
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("normal", new THREE.Float32BufferAttribute(nor, 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    g.setAttribute("aSem", new THREE.Float32BufferAttribute(sem, 1));
    g.setAttribute("aTecho", new THREE.Float32BufferAttribute(tec, 1));
    g.setAttribute("aTop", new THREE.Float32BufferAttribute(top, 1));
    const m = new THREE.Mesh(g, matFachada(false));
    m.visible = false;
    mostrarEnOrbita.push(m);
    gCiudad.add(m);
  });
}
function prepararInterior(g, LM, envInt, envCielo){
  const I = REAL.info, cache = {};
  const conv = (mt, lm) => {
    const k = mt.uuid + "|" + (lm || "");
    if(cache[k]) return cache[k];
    const m = mt.clone();
    if(lm && LM[lm]){
      m.lightMap = LM[lm];
      m.lightMapIntensity = I.K[lm] * Math.PI;
      m.onBeforeCompile = sinIrradianciaIBL;
    }
    const vidrio = m.transparent && m.opacity < 0.4;
    m.envMap = vidrio ? envCielo : envInt;
    m.envMapIntensity = vidrio ? I.cielo.K : I.reflejo.K;
    m.fog = false;
    m.clippingPlanes = [planoCorte];
    if(m.transparent){ m.depthWrite = false; m.side = THREE.DoubleSide; }
    if(m.map) m.map.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    return (cache[k] = m);
  };
  const subir = (o, f) => { for(let p = o; p; p = p.parent){ const r = f(p); if(r) return r; } return null; };
  g.scene.traverse(o=>{
    if(!o.isMesh) return;
    const n = subir(o, p => /^(ext_|techo|dl_disco)/.test(p.name || "") ? p.name : null) || o.name || "";
    if(n.indexOf("ext_propio") === 0){
      o.material = matPropio || (matPropio = matFachada(true));
      return;
    }
    const lm = subir(o, p => p.userData && p.userData.lm);
    o.material = Array.isArray(o.material) ? o.material.map(m => conv(m, lm)) : conv(o.material, lm);
    if(n === "techo" || n.indexOf("ext_voladizo") === 0 || n.indexOf("dl_disco") === 0) ocultarEnOrbita.push(o);
  });
  gReal.add(g.scene);
  /* barandilla y petos de la terraza: colisión en el paseo */
  SEGS.push([9.40, -0.50, 9.40, 3.42], [8.23, -0.50, 9.40, -0.50], [8.23, 3.42, 9.40, 3.42]);
}

function cargarRealista(){
  if(!REAL) return Promise.resolve(false);
  const I = REAL.info;
  const lms = Object.entries(REAL.lm).map(([k, src]) => texDesde(src, false).then(t => [k, t]));
  return Promise.all([
    Promise.all(lms),
    texDesde(REAL.cielo), texDesde(REAL.reflejo),
    texDesde(REAL.suelo.cerca), texDesde(REAL.suelo.lejos),
    texDesde(REAL.arbol && REAL.arbol.lado), texDesde(REAL.arbol && REAL.arbol.planta),
    new Promise(res => bytesDeB64(REAL.glb).then(buf => {
      if(!buf){ res(null); return; }
      new THREE.GLTFLoader().parse(buf, "", res, err => {
        console.warn("GLB realista:", err); res(null); });
    }))
  ]).then(([lmsOk, cielo, reflejo, sCerca, sLejos, aLado, aPlanta, glb]) => {
    if(!glb || !cielo) return false;
    const LM = Object.fromEntries(lmsOk.filter(([, t]) => t));
    const envCielo = envDesde(cielo.clone());
    const envInt = reflejo ? envDesde(reflejo) : envCielo;
    prepararInterior(glb, LM, envInt, envCielo);
    construirEdificios();
    construirTapas();
    if(sLejos) planoSuelo(sLejos, I.suelo.lejos, 0.0);
    if(sCerca) planoSuelo(sCerca, I.suelo.cerca, 0.03);
    construirArboles(aLado, aPlanta);
    const gs = new THREE.SphereGeometry(FAR_CIUDAD*0.9, 64, 32);
    gs.scale(-1, 1, 1);
    const ms = new THREE.MeshBasicMaterial({map: cielo, fog: false, depthWrite: false});
    ms.color.setRGB(I.cielo.K, I.cielo.K, I.cielo.K);
    cieloMesh = new THREE.Mesh(gs, ms);
    cieloMesh.rotation.y = Math.PI;
    cieloMesh.renderOrder = -10;
    cieloMesh.frustumCulled = false;
    gCiudad.add(cieloMesh);
    nieblaReal = new THREE.FogExp2(new THREE.Color().setRGB(...I.cielo.horizonte), 0.0009);
    realListo = true;
    return true;
  });
}

/* Calibración de exposición del modo Realista contra los stills Cycles
   (s1–s4 a 128 muestras, misma cámara y fov). Barrido de exposición medido
   con capturas reales: el mejor ajuste global está en EV 0,90 (error <0,2 EV
   por vista) frente al EV 2,30 que resultaba de usar `exposicion` tal cual;
   sin compensar el visor salía +0,3/+0,6 EV. Compensa que la curva AgX de
   Blender y la aproximación de este script no coinciden. */
const AJUSTE_EXPOSICION = -1.35;

function setRealista(on){
  if(on && !realListo) on = false;
  realista = on;
  gReal.visible = gCiudad.visible = on;
  gMuros.visible = gLineas.visible = gMob.visible = !on;
  ground.visible = !on;
  lucesMaqueta.forEach(([l, i]) => l.intensity = on ? 0 : i);
  renderer.toneMapping = on ? THREE.CustomToneMapping : THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = on ? Math.pow(2, REAL.info.exposicion + AJUSTE_EXPOSICION) : 0.92;
  scene.fog = on ? nieblaReal : null;
  /* la luz del Realista ya viene horneada: sin sombras dinámicas */
  renderer.shadowMap.enabled = !on;
  if(!on) sombrasSucias = true;
  configurarCamara();
  scene.traverse(o => { if(o.material) (Array.isArray(o.material) ? o.material : [o.material])
    .forEach(m => m.needsUpdate = true); });
  setMode(mode);
  $("#b-real").setAttribute("aria-pressed", String(on));
  document.body.classList.toggle("realista", on);
  pedirFrame();
}

function actualizarRealista(){
  if(!realista) return;
  if(cieloMesh) cieloMesh.position.copy(camera.position);
  const orb = camMode === "orbita";
  ocultarEnOrbita.forEach(o => o.visible = !orb);
  mostrarEnOrbita.forEach(o => o.visible = orb);
  if(matPropio) matPropio.uniforms.uClipY.value = orb ? -0.03 : 1e9;
}

$("#b-real").addEventListener("click", () => {
  if(!realListo){ toast("El modo realista no está disponible en este archivo"); return; }
  setRealista(!realista);
  toast(realista ? "Realista: luz de Cycles horneada y la ciudad real a la altura del 7º"
                 : "Maqueta: planta con acabados y sol interactivo");
});
