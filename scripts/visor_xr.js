/* ══ RV (WebXR) ═══════════════════════════════════════════════════════════════
   Paseo inmersivo del visor. Lo inyecta scripts/generar_visor3d.py, después de
   visor_realista.js y antes de la carga.

   - WebXR exige contexto seguro: desde file:// no hay sesión inmersiva; el
     botón avisa. Para probar: servir en localhost (o adb reverse en Quest).
   - Dentro de la sesión se pasa a maqueta (los lightmaps + la ciudad del modo
     Realista no sostienen 72/90 Hz en estéreo) y se renderiza de forma
     continua con renderer.setAnimationLoop(); fuera sigue el dibujo bajo
     demanda de pedirFrame().
   - Locomoción: stick izquierdo anda (reutiliza colisionar(), que ya incluye
     el mobiliario), stick derecho gira a saltos de 30°; grip/B sale. La
     posición de la cabeza la pone la sesión: la cámara va montada en un
     «dolly» que es lo que se mueve. */
const XR_DISPONIBLE = !!(navigator.xr && navigator.xr.isSessionSupported);
const XR_V = 1.5;                 // m/s al andar
const XR_GIRO = Math.PI / 6;      // 30° por salto de stick
let xrSesion = null, xrModoPrev = null, xrRealistaPrev = false;
let xrTiempo = 0;
const xrInputs = {left:null, right:null};
const xrVel = new THREE.Vector3();
const _xrV = new THREE.Vector3(), _xrQ = new THREE.Quaternion();
const _xrE = new THREE.Euler(0, 0, 0, "YXZ");
const xrStickPrev = {right:0};

/* dolly persistente: los mandos viven aquí para seguir el paseo (sus poses
   llegan en el espacio de referencia, sin el desplazamiento del dolly) */
const xrDolly = new THREE.Group();
scene.add(xrDolly);
function mandoXR(i){
  const c = renderer.xr.getController(i);
  c.addEventListener("connected", e=>{
    const mano = (e.data && e.data.handedness === "left") ? "left" : "right";
    xrInputs[mano] = {mando:c, gp:(e.data && e.data.gamepad) || null};
  });
  c.addEventListener("disconnected", ()=>{
    for(const k in xrInputs)
      if(xrInputs[k] && xrInputs[k].mando === c) xrInputs[k] = null;
  });
  c.addEventListener("squeezestart", ()=>{ if(xrSesion) xrSesion.end(); });
  const geo = new THREE.BufferGeometry().setFromPoints(
    [new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, -0.6)]);
  const rayo = new THREE.Line(geo, new THREE.LineBasicMaterial(
    {color:0xB5651D, transparent:true, opacity:0.85}));
  rayo.name = "mando_rayo";
  c.add(rayo);
  c.add(new THREE.Mesh(new THREE.SphereGeometry(0.014, 12, 8),
    new THREE.MeshBasicMaterial({color:0xB5651D})));
  xrDolly.add(c);
  return c;
}
for(let i = 0; i < 2; i++) mandoXR(i);

function stickDe(gp){
  if(!gp || !gp.axes || !gp.axes.length) return null;
  const a = gp.axes;
  return a.length >= 4 ? [a[2], a[3]] : [a[0], a[1]];   // xr-standard: 2/3
}

function entrarXR(){
  if(xrSesion || camera.parent === xrDolly) return;   // ya hay sesión en curso
  if(location.protocol === "file:"){
    toast("La RV necesita abrir el visor desde http://localhost o HTTPS (file:// no permite sesiones inmersivas)");
    return;
  }
  if(!XR_DISPONIBLE) return;
  const pedir = navigator.xr.requestSession("immersive-vr",
    {optionalFeatures:["local-floor", "bounded-floor"]});
  pedir.then(sesion=>{
    xrSesion = sesion;
    xrModoPrev = camMode;
    xrRealistaPrev = realista;
    if(realista) setRealista(false);              // maqueta dentro de la RV
    if(camMode === "orbita") setCamMode("caminar");
    camera.getWorldPosition(_xrV);
    free.pos.set(_xrV.x, EYE, _xrV.z);
    camera.getWorldDirection(_xrV);
    free.yaw = Math.atan2(-_xrV.x, -_xrV.z);
    free.pitch = 0;
    xrDolly.position.set(free.pos.x, 0, free.pos.z);
    xrDolly.rotation.y = free.yaw;
    xrDolly.add(camera);
    xrVel.set(0, 0, 0);
    xrStickPrev.right = 0;
    xrTiempo = 0;
    sombrasSucias = true;
    $("#labels").style.visibility = "hidden";
    renderer.xr.enabled = true;
    renderer.xr.setReferenceSpaceType("local-floor");
    renderer.xr.setFoveation(1);
    return renderer.xr.setSession(sesion);
  }).catch(err=>{
    console.warn("RV:", err);
    if(xrSesion){ try{ xrSesion.end(); }catch(e){ /* ya cerrada */ } }
    if(camera.parent === xrDolly) salirXR();
    toast("No se pudo iniciar la sesión de RV");
  });
}

function salirXR(){
  if(camera.parent === xrDolly){
    xrDolly.remove(camera);
    free.pos.set(xrDolly.position.x, EYE, xrDolly.position.z);
    free.yaw = xrDolly.rotation.y;
  }
  free.pitch = 0;
  xrVel.set(0, 0, 0);
  xrSesion = null;
  camera.rotation.order = "YXZ";
  camera.rotation.set(0, free.yaw, 0);
  camera.position.set(free.pos.x, EYE, free.pos.z);
  camera.updateProjectionMatrix();
  $("#labels").style.visibility = "";
  if(xrRealistaPrev) setRealista(true);
  if(xrModoPrev && xrModoPrev !== camMode) setCamMode(xrModoPrev);
  xrModoPrev = null;
  xrRealistaPrev = false;
  pedirFrame();
}

function xrTick(t){
  const dt = xrTiempo ? Math.min(0.05, (t - xrTiempo) / 1000) : 0.016;
  xrTiempo = t;
  /* orientación de la cabeza para mover en la dirección en la que se mira */
  const xrCam = renderer.xr.getCamera();
  xrCam.getWorldQuaternion(_xrQ);
  _xrE.setFromQuaternion(_xrQ, "YXZ");
  const yaw = _xrE.y, cy = Math.cos(yaw), sy = Math.sin(yaw);
  let f = 0, s = 0;
  const izq = stickDe(xrInputs.left && xrInputs.left.gp);
  if(izq){ f += -izq[1]; s += izq[0]; }
  const der = stickDe(xrInputs.right && xrInputs.right.gp);
  if(der){
    const x = der[0], prev = xrStickPrev.right;
    if(prev > -0.7 && x <= -0.7) xrDolly.rotation.y += XR_GIRO;
    else if(prev < 0.7 && x >= 0.7) xrDolly.rotation.y -= XR_GIRO;
    xrStickPrev.right = x;
  }
  f = Math.max(-1, Math.min(1, f));
  s = Math.max(-1, Math.min(1, s));
  if(Math.abs(f) < 0.15) f = 0;
  if(Math.abs(s) < 0.15) s = 0;
  const dir = _xrV.set(-sy * f + cy * s, 0, -cy * f - sy * s);
  if(dir.lengthSq() > 0) dir.normalize().multiplyScalar(XR_V);
  xrVel.lerp(dir, 1 - Math.pow(0.0008, dt));
  if(xrVel.lengthSq() > 1e-6){
    xrDolly.position.addScaledVector(xrVel, dt);
    xrDolly.position.y = 0;
    colisionar(xrDolly.position);
    xrDolly.position.y = 0;
  }
  if(techoGLB){
    const ver = camera.getWorldPosition(_xrV).y < 2.45;
    if(ver !== techoGLB.visible){ techoGLB.visible = ver; sombrasSucias = true; }
  }
  if(sombrasSucias){ renderer.shadowMap.needsUpdate = true; sombrasSucias = false; }
  renderer.render(scene, camera);
}

renderer.xr.addEventListener("sessionstart", ()=>{
  renderer.setAnimationLoop(xrTick);
  toast("RV: stick izquierdo andar · stick derecho girar · grip salir", 5200);
});
renderer.xr.addEventListener("sessionend", ()=>{
  renderer.setAnimationLoop(null);
  salirXR();
});

const VR_BTN = $("#b-vr"), VR_ACT = $("#a-vr");
function mostrarVR(on){
  VR_BTN.hidden = !on;
  VR_ACT.hidden = !on;
}
if(XR_DISPONIBLE){
  mostrarVR(true);
  navigator.xr.isSessionSupported("immersive-vr")
    .then(ok=>{ if(!ok) mostrarVR(false); })
    .catch(()=>{ mostrarVR(false); });
}
VR_BTN.addEventListener("click", entrarXR);
VR_ACT.addEventListener("click", entrarXR);
