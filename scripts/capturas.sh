#!/usr/bin/env bash
# Capturas automáticas del visor desde 6 vistas (órbita, salón, terraza,
# cocina, dormitorio, fachada). Usa scripts/capturas.mjs (playwright/chromium).
# Uso: ./scripts/capturas.sh [--visor render3d.html] [--salida capturas/] [--ancho 1280] [--alto 800]
set -euo pipefail
cd "$(dirname "$0")/.."

CACHE="$HOME/.cache/opencode-reforma"
if [ ! -d "$CACHE/node_modules/playwright-core" ]; then
  echo "instalando playwright-core en $CACHE (una vez)…"
  npm install --prefix "$CACHE" --silent playwright-core@1.63.0 >/dev/null 2>&1 || {
    echo "no se pudo instalar playwright-core; instálalo a mano en $CACHE" >&2
    exit 1
  }
fi
export PW_CORE="$CACHE/node_modules/playwright-core"
node scripts/capturas.mjs "$@"
