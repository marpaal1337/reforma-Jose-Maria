/* ══ Modo Realista ═══════════════════════════════════════════════════════════
   Interior con la luz de Cycles horneada (lightmaps) y las texturas PBR del
   render, y la ciudad real (OSM) alrededor, a la altura del 7º piso.
   Es el modo por defecto y único del visor (sin conmutador); si falta el
   horneado se cae a la maqueta. En RV se fuerza la maqueta por rendimiento.
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

/* ── fachadas: revoco / ladrillo, huecos, balcones, bajos y cubiertas ──
   Todo el albedo es procedural (sin texturas): la luz es analítica (sol + cielo)
   porque los edificios ocupan miles de m². Referencias: fotos y Street View de
   la avenida (revoco pétreo con juntas de panel, ladrillo caravista en ~40 %,
   bajos comerciales, azoteas de baldosín rojizo con peto y casetas). */
const PALETA = [[0.68,0.36,0.21],[0.72,0.64,0.50],[0.78,0.76,0.71],[0.70,0.56,0.36],
                [0.68,0.50,0.44],[0.62,0.62,0.60],[0.58,0.34,0.24]];
const CUBIERTAS = [[0.40,0.17,0.11],[0.46,0.22,0.15],[0.36,0.15,0.10],[0.44,0.24,0.17]];
/* revoco de las piezas horneadas del propio (losas de balcón…): el lightmap solo
   lleva la iluminación, el color se ajusta aquí contra las fotos de la fachada */
const REVOCO_HORNEADO = [0.66, 0.38, 0.25];
const TIENDAS = [[0.55,0.07,0.05],[0.05,0.10,0.32],[0.08,0.26,0.12],
                 [0.78,0.76,0.70],[0.62,0.22,0.05],[0.10,0.32,0.36]];
const PETO_ED = 1.05;                      // peto de coronación sobre la cubierta
const Z_CUB_PROPIO = 2.95;                 // cubierta del propio sobre el suelo del piso
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
    uCubV: {value: propio ? (-i.suelo.y + Z_CUB_PROPIO) : 1e9},
    uPaleta: {value: PALETA.map(p=>new THREE.Vector3(...p))},
    uCubiertas: {value: CUBIERTAS.map(p=>new THREE.Vector3(...p))},
    uTiendas: {value: TIENDAS.map(p=>new THREE.Vector3(...p))}
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
      uniform float uCubV;
      uniform vec3 uPaleta[7]; uniform vec3 uCubiertas[4]; uniform vec3 uTiendas[6];
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
      vec3 palTienda(float s){
        int i = int(clamp(floor(h21(vec2(s * 1.7 + 3.0, 9.0)) * 6.0), 0.0, 5.0));
        vec3 c = uTiendas[0];
        for(int k = 1; k < 6; k++) if(k == i) c = uTiendas[k];
        return c; }
      /* 1 dentro de una línea de ancho w (m) cada 'per' m; se difumina al alejarse */
      float linea(float x, float per, float w){
        float f = fract(x / per) * per;
        float d = min(f, per - f);
        float fw = max(fwidth(x), 1e-4);
        float vis = 1.0 - smoothstep(0.06, 0.20, fw);
        return (1.0 - smoothstep(w * 0.5, w * 0.5 + max(fw, 0.004), d)) * vis;
      }
      /* ladrillo caravista a soga: pieza de 0,24 × 0,075 con llaga de 1 cm */
      vec3 ladrillo(vec2 p, float sem){
        float fila = floor(p.y / 0.075);
        float u = p.x + 0.12 * mod(fila, 2.0);
        vec2 cel = vec2(floor(u / 0.24), fila);
        vec2 f = vec2(fract(u / 0.24) * 0.24, fract(p.y / 0.075) * 0.075);
        float h = h21(cel * 0.37 + sem * 0.013);
        vec3 c = mix(vec3(0.40, 0.17, 0.10), vec3(0.48, 0.25, 0.16), h);
        c = mix(c, vec3(0.30, 0.16, 0.11), step(0.90, fract(h * 13.7)));
        float junta = max(max(step(f.x, 0.01), step(0.23, f.x)), max(step(f.y, 0.01), step(0.065, f.y)));
        vec3 col = mix(c, vec3(0.52, 0.49, 0.44), junta);
        float fw = max(fwidth(p.x), fwidth(p.y));
        return mix(col, vec3(0.43, 0.22, 0.15), smoothstep(0.02, 0.07, fw));
      }
      void main(){
        if(vPos.y > uClipY) discard;
        const float P = ${PLANTA_ED.toFixed(2)}, B = ${BAJO_ED.toFixed(2)}, ANCHO = 3.1, JUNTA = 0.8, JX = 1.0, PETO = ${PETO_ED.toFixed(2)};
        vec3 Nf = normalize(vN) * (gl_FrontFacing ? 1.0 : -1.0);
        vec3 Vv = normalize(cameraPosition - vPos);
        float propio = uVFlip;
        float sem = floor(vSem * 997.0 + 0.5);
        vec3 alb; vec3 emis = vec3(0.0); float ao = 1.0;
        if(vTecho > 2.5){
          /* tapa de sección del edificio propio (órbita): hormigón neutro */
          alb = vec3(0.56, 0.54, 0.51) * (0.95 + 0.05 * h21(floor(vPos.xz * 2.0)));
        }else if(vTecho > 1.5){
          /* casetas de escalera y ascensor */
          alb = vec3(0.82, 0.81, 0.77) * (0.94 + 0.06 * h21(floor(vPos.xz * 3.0)));
        }else if(vTecho > 0.5){
          /* azotea: baldosín cerámico rojizo de 0,20 m, algo de grava y cubiertas blancas */
          vec2 q = vPos.xz / 0.20;
          vec2 cel = floor(q), fr = fract(q);
          vec3 cb = cubierta(propio > 0.5 ? 0.0 : vSem);
          float pieza = h21(cel + sem * 0.011);
          vec3 tile = cb * (0.88 + 0.24 * pieza);
          float dj = min(min(fr.x, 1.0 - fr.x), min(fr.y, 1.0 - fr.y));
          float fw = max(fwidth(q.x), fwidth(q.y));
          float junta = (1.0 - smoothstep(0.02, 0.05, dj)) * (1.0 - smoothstep(0.15, 0.55, fw));
          tile = mix(tile, vec3(0.62, 0.55, 0.48), junta);
          float rt = propio > 0.5 ? 0.5 : h21(vec2(sem * 0.77 + 1.3, 4.1));
          vec3 grava = vec3(0.50, 0.49, 0.46) * (0.90 + 0.20 * h21(floor(vPos.xz * 8.0)));
          tile = rt < 0.20 ? grava : (rt > 0.92 ? vec3(0.72, 0.71, 0.68) : tile);
          alb = tile * (0.85 + 0.15 * h21(floor(vPos.xz * 0.7) + sem));
        }else{
          float u = vUv.x, v = vUv.y;
          float vt = propio > 0.5 ? uCubV + PETO : vTop;
          /* revoco de la paleta continua; ladrillo caravista en ~40 % de los vecinos */
          float sb = clamp(vSem * 7.0 - 0.5, 0.0, 6.0);
          float ft = smoothstep(0.30, 0.70, fract(sb));
          vec3 base = mix(palI(int(floor(sb))), palI(min(int(floor(sb)) + 1, 6)), ft);
          base = mix(base, vec3(0.60, 0.47, 0.35), 0.10 * (1.0 - propio));
          float ladr = (1.0 - propio) * step(0.60, h21(vec2(sem * 0.71 + 0.3, 5.3)));
          float vp = v - (B - P);
          vec2 celda = floor(vec2(u / ANCHO, vp / P));
          vec2 f = vec2(fract(u / ANCHO) * ANCHO, fract(vp / P) * P);
          float rnd = h21(celda + vec2(sem * 0.131, sem * 0.293));
          float vr = f.y / P;
          float planta = floor(vp / P);
          float cal = h21(vec2(sem * 3.1 + planta * 0.37, planta * 1.7 + sem));
          vec3 revoco = base * (0.95 + 0.10 * cal);
          revoco *= 0.96 + 0.08 * h21(floor(vUv * vec2(6.0, 9.0)) + sem);
          revoco *= 1.0 + 0.06 * sin(vPos.x * 0.33 + vPos.y * 0.17)
                             * sin(vPos.z * 0.29 - vPos.y * 0.11);
          /* grano del revoco pétreo (se pierde con la distancia) */
          float gr = h21(floor(vec2(u, v) * 55.0));
          revoco *= 1.0 + (gr - 0.5) * 0.14 * (1.0 - smoothstep(0.02, 0.08, fwidth(u)));
          /* juntas de panel: cada 1,5 m y a media planta */
          float jp = max(linea(u, 1.5, 0.012), linea(vp, P * 0.5, 0.012));
          revoco *= 1.0 - 0.28 * jp;
          float fr = fract(vp / P);
          revoco *= 0.90 + 0.10 * smoothstep(0.0, 0.12, fr);
          vec3 pared = mix(revoco, ladrillo(vec2(u, v), sem) * (0.95 + 0.10 * cal), ladr);
          /* canto de forjado de hormigón en los edificios de ladrillo */
          pared = mix(pared, vec3(0.60, 0.58, 0.54), ladr * step(P - 0.28, f.y));
          float dTop = vt - v;
          pared *= 1.0 - 0.30 * (1.0 - smoothstep(0.0, 0.5, dTop)) * step(0.5, vt - PETO);
          float enPeto = step(vt - PETO, v);
          float bajo = 1.0 - step(B, v);
          float muro = (f.x < JX || f.x > ANCHO - JX || f.y < JUNTA || f.y > P - JUNTA) ? 1.0 : 0.0;
          muro = max(muro, max(enPeto, bajo));
          /* persiana con lamas horizontales y guías laterales en sombra */
          float umbral = 0.73 - rnd * 0.42;
          float pers = (1.0 - muro) * step(umbral, vr);
          float tp = fract(rnd * 5.3);
          vec3 colP = tp > 0.92 ? vec3(0.16, 0.22, 0.16) : (tp > 0.45 ? vec3(0.42, 0.41, 0.38) : vec3(0.42, 0.36, 0.26));
          float lama = 0.74 + 0.26 * step(0.42, fract(vr * P / 0.055 + rnd));
          float guia = smoothstep(JX, JX + 0.09, f.x) * smoothstep(JX, JX + 0.09, ANCHO - f.x);
          colP *= lama * (0.68 + 0.32 * guia);
          vec3 hueco = mix(vec3(0.016, 0.02, 0.026), colP, pers);
          /* marco de carpintería bronce alrededor del hueco */
          float dm = min(min(f.x - JX, ANCHO - JX - f.x), min(f.y - JUNTA, P - JUNTA - f.y));
          hueco = mix(vec3(0.15, 0.10, 0.065), hueco, smoothstep(0.03, 0.07, dm));
          /* vidrio con reflejo de cielo/horizonte según ángulo (fresnel) */
          vec3 R = reflect(-Vv, Nf);
          vec3 cieloRefl = mix(uHorizonte, uCielo * 0.55, smoothstep(-0.05, 0.55, R.y));
          float tinte = 0.60 + 0.90 * fract(rnd * 7.31);
          cieloRefl = mix(cieloRefl, uCielo * 0.55, fract(rnd * 3.13) * 0.55);
          float calido = step(0.80, fract(rnd * 3.77));
          vec3 interior = mix(vec3(0.020, 0.026, 0.036), vec3(0.11, 0.075, 0.042), calido);
          float fres = mix(0.55, 1.0, pow(1.0 - max(dot(Nf, Vv), 0.0), 2.0));
          float mVid = (1.0 - muro) * (1.0 - pers);
          vec3 vid = mix(interior, cieloRefl * tinte * 0.55, clamp(fres * (0.70 + 0.30 * tinte), 0.0, 1.0));
          vid += uSolE * pow(max(dot(R, uSol), 0.0), 60.0) * 0.020;
          /* balcones pintados en los vecinos: corridos, por columnas o sin balcón */
          float estilo = h21(vec2(sem * 0.37 + 2.1, 8.2));
          float hayB = (1.0 - propio) * (1.0 - bajo) * (estilo < 0.35 ? 1.0
                       : (estilo < 0.75 ? step(0.45, h21(vec2(sem * 1.71 + 3.0, celda.x * 1.37))) : 0.0));
          /* cara frontal del cuerpo de balcones del propio: balconera de vidrio */
          float bay = propio * step(8.2, vPos.x) * step(0.9, Nf.x) * (1.0 - bajo) * (1.0 - enPeto);
          float pasam = 1.0 - smoothstep(0.015, 0.055, abs(vr - 0.34) * P);
          float barrote = step(fract(f.x / 0.30), 0.13);
          float enB = hayB * (1.0 - muro) * step(vr, 0.34);
          vec3 colB = mix(revoco * 0.55, vec3(0.030, 0.030, 0.035), max(barrote * 0.9, pasam));
          alb = mix(mix(hueco, pared, muro), colB, enB);
          float losa = hayB * step(P - 0.45, f.y);            // canto de la losa del balcón
          alb = mix(alb, revoco * 0.92, losa * (1.0 - enB));
          emis = vid * mVid * (1.0 - enB);
          /* balconera de vidrio (cara del cuerpo de balcones del propio) */
          float dv = step(0.35, f.x) * step(f.x, ANCHO - 0.35) * step(0.10, f.y) * step(f.y, 2.25);
          float mullion = step(abs(f.x - ANCHO * 0.5), 0.03);
          alb = mix(alb, mix(vec3(0.02, 0.025, 0.03), vec3(0.12, 0.08, 0.05), mullion), bay * dv);
          emis = mix(emis, vid * (1.0 - mullion), bay * dv);
          /* toldos, equipos de A/A: variedad de color y densidad */
          float vent = (1.0 - muro) * (1.0 - propio);
          float hayT = step(0.22, rnd) * step(rnd, 0.58);
          float bt = step(0.60, vr) * step(vr, 0.72);
          float tt = fract(rnd * 7.7);
          vec3 colT = tt > 0.66 ? vec3(0.16, 0.30, 0.18) : (tt > 0.33 ? vec3(0.82, 0.78, 0.67) : vec3(0.72, 0.66, 0.52));
          colT *= 0.90 + 0.10 * step(0.5, fract(f.x / 0.14));
          alb = mix(alb, colT, vent * hayT * bt);
          float st = vent * hayT * step(0.585, vr) * step(vr, 0.605);
          alb = mix(alb, vec3(0.30, 0.28, 0.24), st);
          float hayA = step(0.05, rnd) * step(rnd, 0.40);
          float aa = vent * hayA * step(2.15, f.x) * step(f.x, 2.65) * step(0.30, vr) * step(vr, 0.40);
          alb = mix(alb, fract(vr * 60.0) > 0.5 ? vec3(0.76, 0.76, 0.74) : vec3(0.62, 0.62, 0.60), aa);
          /* bajos comerciales: aplacado, escaparates, cierres, rótulos y portal */
          float modu = floor(u / 3.1);
          float rb = h21(vec2(modu * 1.31 + sem * 0.017, 7.7));
          float fx = fract(u / 3.1) * 3.1;
          float tipoA = h21(vec2(sem * 0.53 + 1.9, 2.3));
          vec3 aplac = tipoA < 0.5 ? vec3(0.10, 0.10, 0.11)
                     : (tipoA < 0.8 ? vec3(0.55, 0.52, 0.47) : revoco);
          aplac *= 0.94 + 0.06 * h21(floor(vec2(u / 0.6, v / 0.4)));
          vec3 bj = aplac;
          float esc = step(rb, 0.70) * step(0.25, fx) * step(fx, 2.85) * step(0.35, v) * step(v, 3.0);
          float cierre = step(0.70, rb) * step(rb, 0.90) * step(0.15, fx) * step(fx, 2.95) * step(v, 3.1);
          float portal = step(0.90, rb) * step(0.55, fx) * step(fx, 2.45) * step(v, 2.7);
          bj = mix(bj, vec3(0.020, 0.026, 0.038), esc);
          bj = mix(bj, vec3(0.45, 0.46, 0.47) * (0.80 + 0.20 * step(0.5, fract(v / 0.08))), cierre);
          bj = mix(bj, vec3(0.42, 0.19, 0.15), step(0.90, rb) * step(0.35, fx) * step(fx, 2.65) * step(v, 2.9) * (1.0 - portal));
          bj = mix(bj, vec3(0.02, 0.025, 0.03), portal);
          float rotulo = step(rb, 0.70) * step(0.35, h21(vec2(modu * 2.7 + sem * 0.019, 3.3))) * step(3.05, v) * step(v, 3.65);
          bj = mix(bj, palTienda(sem + modu), rotulo * 0.95);
          alb = mix(alb, bj, bajo);
          emis = mix(emis * (1.0 - enB), vec3(0.0), bajo);
          emis += vec3(0.015, 0.02, 0.03) * bajo * esc;
          /* oclusión aproximada: la calle sombrea las plantas bajas */
          ao = mix(0.62, 1.0, smoothstep(0.0, 14.0, v));
        }
        float cielo = 0.5 + 0.5 * Nf.y;
        /* el sol directo (E=14) lo lava todo: se comprime solo ese término */
        vec3 Esol = uSolE * max(dot(Nf, uSol), 0.0);
        Esol = Esol / (1.0 + dot(Esol, vec3(0.3333)) * 0.50);
        vec3 E = (Esol + uCielo * cielo + vec3(uSuelo) * (1.0 - cielo)) * ao * 1.15;
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

/* área con signo de un contorno (x, y) de Blender */
function areaPoli(p){ let a = 0;
  for(let i = 0; i < p.length; i++){ const [x1, y1] = p[i], [x2, y2] = p[(i + 1) % p.length];
    a += x1 * y2 - x2 * y1; }
  return a / 2; }
function dentroPoli(x, y, p){ let c = false;
  for(let i = 0, j = p.length - 1; i < p.length; j = i++)
    if((p[i][1] > y) !== (p[j][1] > y) &&
       x < (p[j][0] - p[i][0]) * (y - p[i][1]) / (p[j][1] - p[i][1]) + p[i][0]) c = !c;
  return c; }
function holguraPoli(x, y, p){ let d = 1e9;
  for(let i = 0; i < p.length; i++){ const [ax, ay] = p[i], [bx, by] = p[(i + 1) % p.length];
    const dx = bx - ax, dy = by - ay, L2 = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / L2));
    d = Math.min(d, Math.hypot(x - ax - t * dx, y - ay - t * dy)); }
  return d; }

function construirEdificios(){
  const Y0 = REAL.info.suelo.y, azar = rng(3);
  const pos = [], nor = [], uv = [], sem = [], tec = [], top = [];
  function v(x, y, z, n, u, w, s, t, h){ pos.push(x, y, z); nor.push(...n); uv.push(u, w); sem.push(s); tec.push(t); top.push(h); }
  /* caja de azotea (caseta): 4 muros y tapa; t = 2 => shader de caseta blanca */
  function caja(cx, cy, ex, ey, ang, z0, z1, s){
    const c = Math.cos(ang), sn = Math.sin(ang);
    const P = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([a, b]) => {
      const x = a * ex / 2, y = b * ey / 2; return [cx + x * c - y * sn, cy + x * sn + y * c]; });
    for(let i = 0; i < 4; i++){
      const [ax, ay] = P[i], [bx, by] = P[(i + 1) % 4];
      const L = Math.hypot(bx - ax, by - ay) || 1, n = [(by - ay) / L, 0, (bx - ax) / L];
      const A0 = [ax, z0, -ay], B0 = [bx, z0, -by], B1 = [bx, z1, -by], A1 = [ax, z1, -ay];
      [A0, B0, B1, A0, B1, A1].forEach(q => v(q[0], q[1], q[2], n, 0, 0, s, 2, z1 - z0));
    }
    [[0, 1, 2], [0, 2, 3]].forEach(t => t.forEach(k => v(P[k][0], z1, -P[k][1], [0, 1, 0], 0, 0, s, 2, z1 - z0)));
  }
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
    const peto = p >= 3 ? 1.0 : 0.0;          // la cubierta baja un metro: peto perimetral
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
    tri.forEach(t => t.forEach(k => v(pts[k][0], Y0 + h - peto, -pts[k][1], [0, 1, 0], pts[k][0], pts[k][1], s, 1, h)));
    /* casetas de escalera y ascensor (edificios altos y grandes) */
    if(p >= 4 && Math.abs(areaPoli(pts)) >= 100){
      const az = azar(), az2 = azar();
      let best = null, bl = 0;
      for(let i = 0; i < pts.length; i++){
        const [ax, ay] = pts[i], [bx, by] = pts[(i + 1) % pts.length], L = Math.hypot(bx - ax, by - ay);
        if(L > bl){ bl = L; best = Math.atan2(by - ay, bx - ax); } }
      const gx = cx + (az - 0.5) * 6, gy = cy + (az2 - 0.5) * 6;
      const [qx, qy] = dentroPoli(gx, gy, pts) ? [gx, gy] : [cx, cy];
      if(dentroPoli(qx, qy, pts) && holguraPoli(qx, qy, pts) > 3.0){
        const zb = Y0 + h - peto;
        caja(qx, qy, 3.4, 3.6, best, zb, zb + 2.7, s);
        if(az > 0.5 && holguraPoli(qx + 4.2, qy, pts) > 2.0 && dentroPoli(qx + 4.2, qy, pts))
          caja(qx + 4.2, qy, 1.9, 1.9, best, zb, zb + 3.4, s);
      }
    }
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


/* ── vida de calle: coches aparcados, farolas y contenedores ──
   Las posiciones las exporta hornear_visor.py (mismos objetos que proyectan su
   sombra en el suelo horneado). Cada tipo es una malla instanciada. */
function matSolido(doble){
  const i = REAL.info, s = i.sol, c = i.cielo;
  const senSol = Math.max(0, s.dir[1]);
  return new THREE.ShaderMaterial({
    side: doble ? THREE.DoubleSide : THREE.FrontSide,
    uniforms: {
      uSol: {value: new THREE.Vector3(...s.dir).normalize()},
      uSolE: {value: new THREE.Color().setRGB(s.color[0]*s.E, s.color[1]*s.E, s.color[2]*s.E)},
      uCielo: {value: new THREE.Color().setRGB(c.color[0]*c.E_up, c.color[1]*c.E_up, c.color[2]*c.E_up)},
      uSuelo: {value: 0.3*(s.E*senSol + c.E_up)},
      uHorizonte: {value: new THREE.Color().setRGB(...c.horizonte)},
      uNiebla: {value: 0.0009}
    },
    vertexShader: `
      #include <common>
      attribute float aTipo;
      varying vec3 vN; varying vec3 vPos; varying vec3 vCol; varying float vTipo;
      void main(){
        vec3 nrm = normal; vec4 lp = vec4(position, 1.0);
        #ifdef USE_INSTANCING
          lp = instanceMatrix * lp;
          nrm = mat3(instanceMatrix) * nrm;
        #endif
        vec4 w = modelMatrix * lp;
        vPos = w.xyz;
        vN = normalize(mat3(modelMatrix) * nrm);
        #ifdef USE_INSTANCING_COLOR
          vCol = instanceColor;
        #else
          vCol = vec3(0.5);
        #endif
        vTipo = aTipo;
        gl_Position = projectionMatrix * viewMatrix * w;
      }`,
    fragmentShader: `
      #include <common>
      uniform vec3 uSol; uniform vec3 uSolE; uniform vec3 uCielo; uniform float uSuelo;
      uniform vec3 uHorizonte; uniform float uNiebla;
      varying vec3 vN; varying vec3 vPos; varying vec3 vCol; varying float vTipo;
      void main(){
        vec3 N = normalize(vN) * (gl_FrontFacing ? 1.0 : -1.0);
        vec3 Vv = normalize(cameraPosition - vPos);
        /* tipo 0 pintura, 1 cristal, 2 goma, 3 metal oscuro, 4 color de instancia, 5 tronco */
        vec3 alb = vTipo < 0.5 ? vCol : (vTipo < 1.5 ? vec3(0.02, 0.03, 0.04)
                 : (vTipo < 2.5 ? vec3(0.025) : (vTipo < 3.5 ? vec3(0.10, 0.11, 0.11)
                 : (vTipo < 4.5 ? vCol * 0.55 : vec3(0.22, 0.17, 0.11)))));
        float cielo = 0.5 + 0.5 * N.y;
        vec3 Esol = uSolE * max(dot(N, uSol), 0.0);
        Esol = Esol / (1.0 + dot(Esol, vec3(0.3333)) * 0.50);
        vec3 E = Esol + uCielo * cielo + vec3(uSuelo) * (1.0 - cielo);
        vec3 col = alb * E * RECIPROCAL_PI;
        /* brillo de cielo (fresnel) en pintura y cristal */
        float fr = pow(1.0 - max(dot(N, Vv), 0.0), 3.0);
        float brillo = vTipo < 0.5 ? 0.10 : (vTipo < 1.5 ? 0.35 : 0.0);
        col += uCielo * 0.55 * (brillo + fr * brillo * 1.5) * 0.30;
        col = col / (1.0 + col * 0.15);
        float d = length(vPos - cameraPosition);
        col = mix(col, uHorizonte, 1.0 - exp(-d * uNiebla));
        gl_FragColor = vec4(col, 1.0);
        #include <tonemapping_fragment>
        #include <encodings_fragment>
      }`
  });
}

/* fusiona partes [{g, t}] en una geometría no indexada con atributo aTipo */
function fusionarPartes(partes){
  const pos = [], nor = [], tip = [];
  partes.forEach(({g, t}) => {
    const n = g.index ? g.toNonIndexed() : g;
    n.computeVertexNormals();
    const p = n.attributes.position.array, q = n.attributes.normal.array;
    for(let i = 0; i < p.length; i++){ pos.push(p[i]); nor.push(q[i]); }
    for(let i = 0; i < p.length / 3; i++) tip.push(t);
  });
  const G = new THREE.BufferGeometry();
  G.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  G.setAttribute("normal", new THREE.Float32BufferAttribute(nor, 3));
  G.setAttribute("aTipo", new THREE.Float32BufferAttribute(tip, 1));
  return G;
}
const PINTURA_COCHE = [[0.30, [0.80, 0.80, 0.78]], [0.55, [0.45, 0.46, 0.48]], [0.75, [0.03, 0.03, 0.035]],
                       [0.85, [0.12, 0.12, 0.13]], [0.93, [0.04, 0.07, 0.16]], [1.01, [0.45, 0.04, 0.04]]];
const COLOR_CONT = [[0.05, 0.25, 0.08], [0.15, 0.16, 0.16], [0.60, 0.50, 0.05], [0.05, 0.10, 0.35]];

function construirCalle(){
  const I = REAL.info, Y0 = I.suelo.y;
  const mat = matSolido();
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), col = new THREE.Color();
  function instanciar(geo, lista, alto, colorDe){
    if(!lista || !lista.length) return;
    const im = new THREE.InstancedMesh(geo, mat, lista.length);
    lista.forEach((it, k) => {
      e.set(0, it[2], 0); q.setFromEuler(e);
      M.compose(new THREE.Vector3(it[0], Y0 + alto, it[1]), q, new THREE.Vector3(1, 1, 1));
      im.setMatrixAt(k, M);
      const c = colorDe(it); col.setRGB(c[0], c[1], c[2]); im.setColorAt(k, col);
    });
    im.instanceMatrix.needsUpdate = true;
    if(im.instanceColor) im.instanceColor.needsUpdate = true;
    im.frustumCulled = false;
    gCiudad.add(im);
  }
  /* coche: carrocería, cabina de cristal con techo pintado y cuatro ruedas */
  const cabina = new THREE.BoxGeometry(2.0, 0.52, 1.55).translate(-0.05, 1.18, 0);
  const cp = cabina.attributes.position;
  for(let k = 0; k < cp.count; k++) if(cp.getY(k) > 1.2){ cp.setX(k, -0.05 + (cp.getX(k) + 0.05) * 0.72); cp.setZ(k, cp.getZ(k) * 0.90); }
  const partes = [
    {g: new THREE.BoxGeometry(4.3, 0.62, 1.75).translate(0, 0.61, 0), t: 0},
    {g: cabina, t: 1},
    {g: new THREE.BoxGeometry(1.45, 0.03, 1.38).translate(-0.05, 1.445, 0), t: 0}
  ];
  [[1.35, 0.85], [1.35, -0.85], [-1.35, 0.85], [-1.35, -0.85]].forEach(([x, z]) =>
    partes.push({g: new THREE.CylinderGeometry(0.31, 0.31, 0.2, 10).rotateX(Math.PI / 2).translate(x, 0.31, z), t: 2}));
  instanciar(fusionarPartes(partes), I.coches, 0.0, it => {
    for(const [lim, c] of PINTURA_COCHE) if(it[3] < lim) return c; return PINTURA_COCHE[0][1]; });
  /* farola: fuste, brazo curvado hacia la calzada y luminaria */
  const fuste = new THREE.CylinderGeometry(0.07, 0.11, 9.0, 8).translate(0, 4.5, 0);
  const brazo = new THREE.BoxGeometry(1.9, 0.07, 0.07).translate(0.95, 9.0, 0);
  const cabeza = new THREE.BoxGeometry(0.75, 0.12, 0.32).translate(1.95, 8.95, 0);
  instanciar(fusionarPartes([{g: fuste, t: 3}, {g: brazo, t: 3}, {g: cabeza, t: 3}]),
             I.farolas, 0.0, () => [1, 1, 1]);
  /* contenedor: cuerpo del color de la recogida y tapa oscura */
  instanciar(fusionarPartes([
      {g: new THREE.BoxGeometry(1.05, 1.0, 0.95).translate(0, 0.55, 0), t: 4},
      {g: new THREE.BoxGeometry(1.1, 0.08, 1.0).translate(0, 1.09, 0), t: 3}]),
    I.urbano, 0.0, it => COLOR_CONT[it[3] % 4]);
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

/* palmera: tronco de 10 m y 16 frondas curvadas (cintas) en un solo InstancedMesh */
function construirPalmeras(lista){
  if(!lista.length) return;
  const Y0 = REAL.info.suelo.y, azar = rng(21);
  const partes = [{g: new THREE.CylinderGeometry(0.20, 0.30, 10, 8).translate(0, 5, 0), t: 5}];
  const N = 16, S = 7;
  for(let f = 0; f < N; f++){
    const ang = f / N * 2 * Math.PI + azar() * 0.3, L = 3.0 + azar() * 0.9, ca = Math.cos(ang), sa = Math.sin(ang);
    const pos = [];
    const pt = (t, lado) => { const w = (0.55 * Math.pow(1 - t, 0.7) + 0.03) * lado;
      const x = L * t, y = 10.0 + 1.3 * t - 2.1 * t * t;
      return [x * ca - w * sa, y, -(x * sa + w * ca)]; };
    for(let k = 0; k < S; k++){
      const a = pt(k / S, -1), b = pt(k / S, 1), c = pt((k + 1) / S, 1), d = pt((k + 1) / S, -1);
      pos.push(...a, ...b, ...c, ...a, ...c, ...d);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    partes.push({g, t: 4});
  }
  const im = new THREE.InstancedMesh(fusionarPartes(partes), matSolido(true), lista.length);
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), col = new THREE.Color();
  lista.forEach(([x, z, h, w, rot], k) => {
    const s = Math.min(1.25, Math.max(0.7, (h || 9) / 9.5));
    e.set(0, rot || 0, 0); q.setFromEuler(e);
    M.compose(new THREE.Vector3(x, Y0, z), q, new THREE.Vector3(s, s, s));
    im.setMatrixAt(k, M);
    col.setRGB(0.20 + azar() * 0.08, 0.34 + azar() * 0.10, 0.10 + azar() * 0.05);
    im.setColorAt(k, col);
  });
  im.instanceMatrix.needsUpdate = true;
  if(im.instanceColor) im.instanceColor.needsUpdate = true;
  im.frustumCulled = false;
  gCiudad.add(im);
}

function construirArboles(lado, planta){
  const A = REAL.info.arbol, todos = REAL.info.arboles || [];
  if(!A || !todos.length || !lado) return;
  /* ~10 % de los árboles son palmeras (geometría propia, ver construirPalmeras) */
  const esPalma = (k) => ((Math.imul(k + 1, 2654435761) >>> 0) % 100) < 10;
  const lista = todos.filter((_, k) => !esPalma(k));
  construirPalmeras(todos.filter((_, k) => esPalma(k)));
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
      uv.push(pts[k][0], pts[k][1]); sem.push(0.55); tec.push(3); top.push(0); }));
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
    if(mt.name === "revoco_fachada") m.color.setRGB(...REVOCO_HORNEADO);
    if(lm && LM[lm]){
      m.lightMap = LM[lm];
      m.lightMapIntensity = I.K[lm] * Math.PI * (mt.name === "revoco_fachada" ? 0.85 : 1.0);
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
    /* en órbita (vista de maqueta desde arriba) se ocultan los forjados y
       falsos techos: su cara superior saldría negra y tapa las estancias */
    if(n === "techo" || n.indexOf("falso_techo_") === 0 || n.indexOf("tabica_") === 0 ||
       n.indexOf("rev_gap_") === 0 || n.indexOf("ext_voladizo") === 0 ||
       n.indexOf("dl_disco") === 0 || n.indexOf("ext_azotea") === 0) ocultarEnOrbita.push(o);
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
    construirCalle();
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
