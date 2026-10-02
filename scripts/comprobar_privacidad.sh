#!/usr/bin/env bash
# Comprobación de privacidad (AGENTS.md): el visor y el tour no deben llevar
# importes, "presupuesto", códigos postales de Valencia ni direcciones.
# Ignora los blobs base64 (cadenas largas sin espacios).
# Uso: ./scripts/comprobar_privacidad.sh [fichero.html …]   (por defecto render3d.html tour3d.html)
set -euo pipefail
cd "$(dirname "$0")/.."
FICHEROS=("$@"); [ ${#FICHEROS[@]} -gt 0 ] || FICHEROS=(render3d.html tour3d.html)
fallos=0
for f in "${FICHEROS[@]}"; do
  [ -f "$f" ] || { echo "falta $f"; fallos=1; continue; }
  limpio=$(sed -E 's/[A-Za-z0-9+\/=_-]{120,}/<b64>/g' "$f")
  hits=$( { grep -n -i -o -E '.{0,20}(€|\beuros?\b|\bEUR\b|presupuesto|\b46[0-9]{3}\b).{0,20}' <<<"$limpio" || true
            grep -n -o -E '.{0,20}(\bC/ |\bAvda\.? |\bCalle [A-ZÁÉÍÓÚ]|\bAvenida [A-ZÁÉÍÓÚ]).{0,20}' <<<"$limpio" || true; } )
  if [ -n "$hits" ]; then echo "PRIVACIDAD: posibles datos sensibles en $f:"; echo "$hits" | head -20; fallos=1
  else echo "ok  $f"; fi
done
exit $fallos
