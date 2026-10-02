#!/usr/bin/env python3
"""
Servidor de desarrollo del visor: sirve visor/src/ sin regenerar render3d.html.

    python3 scripts/dev_visor.py [--puerto 8000] [--sin-realista] [--sin-recarga]

- `/` monta la página al vuelo con los mismos datos que generar_visor3d.py, pero
  CSS, JS y librerías van como ficheros aparte y el mobiliario/texturas por URL.
- Guardar un fichero de visor/src/ o de data/ recarga la pestaña sola.
- Los datos pesados (modo Realista, ~20 MB en base64) se cachean hasta que cambia
  alguno de sus ficheros.
- /visor.js es visor.js + realista.js + carga.js concatenados (como en el HTML
  final): las líneas de los errores de la consola cuentan sobre esa unión.
- Solo escucha en 127.0.0.1. El resto de rutas sirven ficheros del repo (libs/, data/).
"""
from __future__ import annotations

import argparse
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar_visor3d as g  # noqa: E402

RECARGA = """<script>
(function(){let v=null;setInterval(()=>fetch("/__version",{cache:"no-store"}).then(r=>r.text()).then(t=>{
if(v===null)v=t;else if(t!==v)location.reload();}).catch(()=>{}),1000);})();
</script>
"""


class Estado:
    def __init__(self, realista: bool, recarga: bool):
        self.realista, self.recarga = realista, recarga
        self._firma = None
        self._datos = None

    @staticmethod
    def _mtimes(rutas):
        return tuple((p, p.stat().st_mtime_ns) for p in rutas if p.exists())

    def datos(self):
        firma = self._mtimes(g.entradas())
        if firma != self._firma:
            print("  (re)cargando datos…", flush=True)
            self._datos = g.cargar(embed=False, realista=self.realista)
            self._firma = firma
        return self._datos

    def version(self) -> str:
        m = self._mtimes(g.fuentes() + g.entradas())
        return str(max((t for _, t in m), default=0))


def crear_handler(estado: Estado):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(g.ROOT), **k)

        def _enviar(self, cuerpo: str, tipo: str):
            b = cuerpo.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_GET(self):
            ruta = self.path.split("?")[0]
            try:
                if ruta in ("/", "/index.html", "/render3d.html"):
                    html = g.pagina(estado.datos(), dev=True)
                    if estado.recarga:
                        html = html.replace("</body>", RECARGA + "</body>")
                    return self._enviar(html, "text/html; charset=utf-8")
                if ruta == "/visor.js":
                    return self._enviar(g.js_completo(estado.datos()), "text/javascript; charset=utf-8")
                if ruta == "/favicon.ico":
                    self.send_response(204)
                    self.end_headers()
                    return
                if ruta == "/__version":
                    return self._enviar(estado.version(), "text/plain")
            except Exception as e:  # error de datos: se ve en el navegador, no mata el servidor
                return self._enviar(f"Error al montar el visor: {e!r}", "text/plain; charset=utf-8")
            return super().do_GET()

        def log_message(self, fmt, *args):
            if "/__version" not in str(args[0] if args else ""):
                super().log_message(fmt, *args)

    return Handler


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--sin-realista", action="store_true", help="arranca solo la maqueta (más rápido)")
    ap.add_argument("--sin-recarga", action="store_true", help="no recarga la pestaña al guardar")
    a = ap.parse_args()
    estado = Estado(realista=not a.sin_realista, recarga=not a.sin_recarga)
    estado.datos()  # falla pronto si faltan libs/ o datos
    srv = ThreadingHTTPServer(("127.0.0.1", a.puerto), crear_handler(estado))
    print(f"Visor en http://127.0.0.1:{a.puerto}/  (?perf para fps) — Ctrl+C para parar", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
