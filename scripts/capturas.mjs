#!/usr/bin/env node
/**
 * Capturas automáticas del visor (modo Realista) — 6 vistas.
 *
 * Uso:
 *   node scripts/capturas.mjs [--visor render3d.html] [--salida capturas/] [--ancho 1280] [--alto 800]
 *
 * Requiere: playwright-core y chromium (los resuelve scripts/capturas.sh, que
 * los cachea en ~/.cache/opencode-reforma y ~/.cache/ms-playwright).
 * Vistas: orbita, salon (s4), terraza, cocina (s2), dormitorio (s3), fachada.
 * Activa el modo Realista si el horneado está disponible; si no, captura la maqueta.
 */
import { createRequire } from 'module';
import { homedir } from 'os';
import { mkdirSync, readdirSync, existsSync } from 'fs';
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
const VISOR = resolve(opt('--visor', 'render3d.html'));
const SALIDA = resolve(opt('--salida', 'capturas'));
const ANCHO = parseInt(opt('--ancho', '1280'), 10);
const ALTO = parseInt(opt('--alto', '800'), 10);

mkdirSync(SALIDA, { recursive: true });

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
await page.goto('file://' + VISOR);
await page.waitForFunction('window.__visor && window.__visor.listo', null, { timeout: 120000 });
await page.waitForTimeout(1200);

// El visor arranca en Realista si hay horneado (setRealista(realListo)):
// solo clicar si está apagado.
const realista = await page.evaluate(() => {
  const b = document.querySelector('#b-real');
  if (!b) return false;
  if (b.getAttribute('aria-pressed') !== 'true') b.click();
  return document.body.classList.contains('realista');
});
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
  }, v);
  await page.waitForTimeout(900);
  const out = `${SALIDA}/${nombre}.png`;
  await page.screenshot({ path: out });
  console.log(`OK ${out}`);
}
await browser.close();
