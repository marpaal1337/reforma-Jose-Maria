#!/usr/bin/env bash
# Lanza Blender resolviendo libSM/libICE locales (extraídas sin sudo en
# ~/opt/blender-libs), necesarias en WSL si el sistema no trae libsm6.
# Uso: ./scripts/blender.sh -b renders/escena.blend -noaudio -P scripts/hornear_visor.py -- ...
set -euo pipefail
LIBS="$HOME/opt/blender-libs/usr/lib/x86_64-linux-gnu"
if [ -d "$LIBS" ]; then
  export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
BIN="$HOME/opt/blender/blender"
if [ ! -x "$BIN" ]; then
  BIN="$(command -v blender || true)"
fi
if [ -z "$BIN" ] || [ ! -x "$BIN" ]; then
  echo "blender no encontrado (~/opt/blender/blender)" >&2
  exit 1
fi
exec "$BIN" "$@"
