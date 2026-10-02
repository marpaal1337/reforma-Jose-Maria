

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
/* los blobs grandes se decodifican con el decodificador nativo (fetch sobre
   data:), sin recorrer 16 millones de bytes en el hilo principal; si el
   navegador no deja descargar data:, se cae al bucle atob de siempre */
async function bytesDeB64(b64){
  if(!b64) return null;
  try{
    const r = await fetch("data:application/octet-stream;base64," + b64);
    if(r.ok) return await r.arrayBuffer();
  }catch(e){ /* sin fetch de data: -> atob */ }
  return base64AB(b64);
}
/* El visor conserva toda la arquitectura y el mobiliario de la casa, siempre
   visible (sin conmutador): estructura, salón·cocina y resto de estancias. */
const MOB_ESTRUCTURA = ["suelo", "pav_", "techo", "falso_techo_", "tabica_",
  "rev_", "muro_", "marco_",
  "vidrio_", "mont_", "dintel_", "antepecho_", "pmarco_", "pdintel_", "phoja_",
  "dl_disco_", "peto_"];
/* 2026-09-19: "banda_" excluido a propósito — las 5 bandas de cinta no
   existen en el PEI.05 (ver generar_blender.build_bandas). El GLB viejo aún
   las trae; el visor las descarta hasta regenerar la escena con Blender. */
const MOB_SALON = ["tv_", "tv", "pilar_visto", "sofa_", "cojin_", "alfombra",
  "mesa_centro", "butaca", "aparador", "cuadro_", "coc_", "isla", "isla_tapa",
  "placa", "campana", "lampara_", "planta_", "cortina_"];
/* resto de estancias y conjunto de comedor: visibles sólo con "toda la casa" */
const MOB_RESTO = ["d1_", "d2_", "d3_", "dp_", "rec_", "tz_", "mesa", "silla_",
  "taburete_"];
function enLista(nombre, lista){
  return lista.some(p => p === nombre || nombre.indexOf(p) === 0);
}
function esMobHabitacion(nombre){
  if(nombre.indexOf("b1_") === 0 || nombre.indexOf("b2_") === 0)
    return nombre.indexOf("azulejo") < 0;
  return enLista(nombre, MOB_RESTO);
}
function mobConservar(nombre){
  return enLista(nombre, MOB_ESTRUCTURA) || enLista(nombre, MOB_SALON)
      || esMobHabitacion(nombre);
}
function cargarMobiliario(){
  if(typeof THREE.GLTFLoader !== "function" || (!MOBILIARIO_B64 && !MOBILIARIO_SRC))
    return Promise.resolve(null);
  return new Promise(res=>{
    const onLoad = g=>{
      const petos = [];
      const quitar = [];
      g.scene.traverse(o=>{
        if(!o.isMesh) return;
        if(!mobConservar(o.name)){ quitar.push(o); return; }
        o.castShadow = true;
        o.receiveShadow = true;
        if(o.name.indexOf("peto_")===0) petos.push(o);
        if(o.name === "suelo") o.visible = false;   // el visor pinta sus suelos
        if(o.name === "techo" || o.name.indexOf("falso_techo_") === 0 ||
           o.name.indexOf("tabica_") === 0 ||
           o.name.indexOf("dl_disco_") === 0) techosGLB.push(o);   // los discos cuelgan del techo
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
      quitar.forEach(o=>{ if(o.parent) o.parent.remove(o); });
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
    if(MOBILIARIO_B64) bytesDeB64(MOBILIARIO_B64).then(
      buf => buf ? loader.parse(buf, "", onLoad, onErr) : onErr(new Error("base64 vacío")), onErr);
    else loader.load(MOBILIARIO_SRC, onLoad, undefined, onErr);
  });
}
/* Carga: primero el modo Realista (el de arranque), la maqueta en segundo
   plano; se precompilan los dos modos porque la RV y las capturas usan la
   maqueta. */
function alListo(){
  if(ready) return;
  requestAnimationFrame(()=>{
    $("#loader").classList.add("done");
    ready = true;
    pedirFrame();
    if(esMovil() && !coachVisto) setTimeout(abrirCoach, 650);
  });
}
function compilarEscena(){
  try{ renderer.compile(scene, camera); }catch(e){ console.warn("compile:", e); }
}
async function cargarTodo(){
  bar.style.width = "20%";
  const conReal = !!REAL;
  if(conReal){
    const ok = await cargarRealista();
    bar.style.width = "55%";
    setRealista(ok);
    compilarEscena();
    alListo();
  }
  await Promise.all([
    cargarTextura(TEX_SRC).then(t=>{ if(t){ TEXTURA.plano = t; buildFloor(t); } }),
    ...Object.entries(TEXTURAS_SRC).map(([n,src])=>cargarTextura(src).then(t=>{ if(t) TEXTURA[n] = t; })),
    cargarMobiliario(),
  ]);
  aplicarTexturas();
  maquetaLista = true;
  bar.style.width = "90%";
  if(!realListo){
    /* sin horneado no hay Realista: queda la maqueta */
    setRealista(false);
    compilarEscena();
    alListo();
  }else{
    setRealista(false);
    compilarEscena();
    setRealista(true);
    compilarEscena();
  }
  bar.style.width = "100%";
}
cargarTodo().catch(err=>{
  console.warn(err);
  bar.style.width = "100%";
  alListo();
});
pedirFrame();
