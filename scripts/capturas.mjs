#!/usr/bin/env node
/**
 * Capturas automáticas del visor (modo Realista) — 6 vistas.
 *
 * Uso:
 *   node scripts/capturas.mjs [--visor render3d.html] [--salida capturas/] [--ancho 1280] [--alto 800]
 *   node scripts/capturas.mjs --medir [--visor render3d.html]
 *   node scripts/capturas.mjs --maqueta [--salida capturas/]
 *
 * Requiere: playwright-core y chromium (los resuelve scripts/capturas.sh, que
 * los cachea en ~/.cache/opencode-reforma y ~/.cache/ms-playwright).
 * Vistas: orbita, salon (s4), terraza, cocina (s2), dormitorio (s3), fachada.
 * El visor arranca siempre en Realista; --maqueta lo fuerza a la maqueta.
 *
 * --medir no guarda capturas: informa del peso del HTML, el tiempo hasta estar
 * listo, draw calls/triángulos/programas/memoria de cada modo y milisegundos
 * por fotograma en reposo y orbitando. Chromium sin pantalla (WSL) no da FPS
 * reales, pero sirve para comparar antes/después. Para FPS reales, abre el
 * visor con ?perf y mira el indicador.
 */
import { createRequire } from 'module';
import { homedir } from 'os';
import { mkdirSync, readdirSync, existsSync, statSync } from 'fs';
import { resolve } from 'path';

const require = createRequire(import.meta.url);
const CANDIDATOS_PW = [
  process.env.PW_CORE,
  homedir() + '/.cache/opencode-reforma/node_modules/playwright-core',
  '/tmp/opencode/cap/node_modules/playwright-core',
].filter(Boolean);
const PW = CANDIDATOS_PW.find(p => existsSync(p));
if (!PW) {
  console.error('falta playwright-core; lanza ./scripts/capturas.sh (lo instala en ~/.cache/opencode-reforma)');
  process.exit(1);
}
const { chromium } = require(PW);

function buscarChrome() {
  if (process.env.CHROME_BIN && existsSync(process.env.CHROME_BIN)) return process.env.CHROME_BIN;
  const base = homedir() + '/.cache/ms-playwright';
  if (!existsSync(base)) return null;
  const dirs = readdirSync(base).filter(d => d.startsWith('chromium-')).sort().reverse();
  for (const d of dirs) {
    const p = `${base}/${d}/chrome-linux64/chrome`;
    if (existsSync(p)) return p;
  }
  return null;
}

const args = process.argv.slice(2);
const opt = (n, d) => {
  const i = args.indexOf(n);
  return i >= 0 ? args[i + 1] : d;
};
const MEDIR = args.includes('--medir');
const MAQUETA = args.includes('--maqueta');
const VISOR = resolve(opt('--visor', 'render3d.html'));
const SALIDA = resolve(opt('--salida', 'capturas'));
const ANCHO = parseInt(opt('--ancho', '1280'), 10);
const ALTO = parseInt(opt('--alto', '800'), 10);

if (!MEDIR) mkdirSync(SALIDA, { recursive: true });

// pos + target en coords Three.js (x=X, y=Z, z=-Y Blender)
const VISTAS = {
  orbita: { orbita: true },
  salon: { pos: [2.7, 1.55, 0.1], target: [7.6, 1.15, 2.7] },
  terraza: { pos: [8.75, 1.62, 1.5], target: [30, 4.0, 1.5] },
  cocina: { pos: [4.6, 1.55, 3.1], target: [0.2, 1.15, 0.6] },
  dormitorio: { pos: [3.1, 1.5, -0.95], target: [5.9, 1.05, -3.0] },
  fachada: { pos: [20, 7.0, -8.0], target: [0, 1.0, 0.6] },
};

const CHROME = buscarChrome();
if (!CHROME) {
  console.error('no encuentro chromium de playwright en ~/.cache/ms-playwright (npx playwright install chromium)');
  process.exit(1);
}
const browser = await chromium.launch({ executablePath: CHROME });
const page = await browser.newPage({ viewport: { width: ANCHO, height: ALTO } });
page.on('console', m => { if (m.type() === 'warning') console.log('[consola]', m.text().slice(0, 160)); });

/* ── instrumentación de fotogramas (envolver renderer.render) ── */
async function instrumentar() {
  await page.evaluate(() => {
    const R = window.__visor.renderer;
    if (R.__t) return;
    R.__t = [];
    const orig = R.render.bind(R);
    R.render = (...a) => { R.__t.push(performance.now()); return orig(...a); };
  });
}
async function medirFrames(ms) {
  return page.evaluate(ms => new Promise(res => {
    const R = window.__visor.renderer;
    R.__t.length = 0;
    setTimeout(() => {
      const t = R.__t, iv = [];
      for (let i = 1; i < t.length; i++) iv.push(t[i] - t[i - 1]);
      iv.sort((a, b) => a - b);
      const q = p => iv.length ? +iv[Math.min(iv.length - 1, Math.floor(p * (iv.length - 1)))].toFixed(2) : null;
      res({
        fotogramas: t.length,
        ms_medio: iv.length ? +(iv.reduce((s, v) => s + v, 0) / iv.length).toFixed(2) : null,
        ms_p50: q(0.5), ms_p95: q(0.95),
      });
    }, ms);
  }), ms);
}
async function info() {
  return page.evaluate(() => {
    const V = window.__visor, R = V.renderer;
    R.render(V.scene, V.camera);
    return {
      drawCalls: R.info.render.calls,
      triangulos: R.info.render.triangles,
      programas: R.info.programs ? R.info.programs.length : null,
      geometrias: R.info.memory.geometries,
      texturas: R.info.memory.textures,
      memoria_mb: typeof performance.memory === 'object'
        ? +(performance.memory.usedJSHeapSize / 1048576).toFixed(1) : null,
    };
  });
}
/* con dibujo bajo demanda, espera a que la cámara deje de animarse */
async function esperarQuieto() {
  await page.waitForFunction('window.__visor.animando === undefined || !window.__visor.animando',
    null, { timeout: 60000 }).catch(() => {});
}
/* la altura de muros es fija (2,60 m): ya no hay intro que esperar */
async function esperarIntro() {
  await page.waitForFunction('window.__visor.intro === undefined || window.__visor.intro >= 1',
    null, { timeout: 120000 }).catch(() => {});
}

await page.goto('file://' + VISOR);
await page.waitForFunction('window.__visor && window.__visor.listo', null, { timeout: 120000 });

if (MEDIR) {
  const listo_ms = await page.evaluate(() => Math.round(performance.now()));
  await page.waitForTimeout(1200);
  // el visor arranca en Realista; la altura de muros ya no se anima
  await esperarIntro();
  const realista = await page.evaluate(() => document.body.classList.contains('realista'));
  await instrumentar();
  await esperarQuieto();
  const rep = {
    archivo: VISOR.replace(process.cwd() + '/', ''),
    mb: +(statSync(VISOR).size / 1048576).toFixed(1),
    listo_ms,
    realista,
    info_inicial: await info(),
    reposo: await medirFrames(2000),
  };
  // órbita: arrastrar en el lienzo durante 3 s
  const caja = await page.evaluate(() => {
    const r = document.querySelector('#c').getBoundingClientRect();
    return { x: r.left + r.width / 2, y: r.top + r.height / 2, r: Math.min(r.width, r.height) * 0.3 };
  });
  const medP = medirFrames(3000);
  await page.mouse.move(caja.x, caja.y);
  await page.mouse.down();
  const tA = Date.now();
  let ang = 0;
  while (Date.now() - tA < 3000) {
    ang += 0.22;
    await page.mouse.move(caja.x + Math.cos(ang) * caja.r, caja.y + Math.sin(ang) * caja.r * 0.6);
    await page.waitForTimeout(8);
  }
  await page.mouse.up();
  rep.orbita = await medP;
  rep.info_orbita = await info();
  if (realista) {
    await page.evaluate(() => window.__visor.setRealista(false));
    await page.waitForFunction('window.__visor.maquetaLista !== false', null, { timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(1500);
    await esperarQuieto();
    rep.info_maqueta = await info();
    rep.reposo_maqueta = await medirFrames(2000);
  }
  console.log(JSON.stringify(rep, null, 2));
  await browser.close();
  process.exit(0);
}

await page.waitForTimeout(1200);

// El visor arranca en Realista; solo cambia si se pide --maqueta.
const realista = await page.evaluate((maqueta) => {
  const V = window.__visor;
  if (!V || !V.setRealista) return false;
  if (maqueta && V.realista) V.setRealista(false);
  if (!maqueta && !V.realista) V.setRealista(true);
  return document.body.classList.contains('realista');
}, MAQUETA);
await page.waitForFunction('window.__visor.maquetaLista !== false', null, { timeout: 60000 }).catch(() => {});
await esperarIntro();
await esperarQuieto();
await page.waitForTimeout(1500);
console.log(`modo realista solicitado: ${realista}`);

for (const [nombre, v] of Object.entries(VISTAS)) {
  await page.evaluate((vv) => {
    const V = window.__visor;
    if (vv.orbita) {
      V.setCamMode('orbita');
    } else {
      V.setCamMode('vuelo');
      const [px, py, pz] = vv.pos, [tx, ty, tz] = vv.target;
      const fx = tx - px, fy = ty - py, fz = tz - pz;
      const L = Math.hypot(fx, fy, fz) || 1;
      V.free.pos.set(px, py, pz);
      V.free.yaw = Math.atan2(-fx / L, -fz / L);
      V.free.pitch = Math.asin(Math.min(1, Math.max(-1, fy / L)));
      V.free.vel.set(0, 0, 0);
    }
    if (V.pedirFrame) V.pedirFrame();   // dibujo bajo demanda: fuerza un fotograma
  }, v);
  await page.waitForTimeout(900);
  const out = `${SALIDA}/${nombre}.png`;
  await page.screenshot({ path: out });
  console.log(`OK ${out}`);
}
await browser.close();
