# Atajos del proyecto. `make` sin argumentos lista los objetivos.
# Los objetivos de Blender son lentos (minutos u horas) y no se lanzan solos.
PY ?= python3
BLENDER = ./scripts/blender.sh

.DEFAULT_GOAL := ayuda
.PHONY: ayuda dev dev-maqueta visor tour datos todo check mobiliario privacidad humo humo-dev capturas medir escena glb hornear-rapido

ayuda:
	@echo "Iterar:"
	@echo "  make dev            servidor de desarrollo del visor (visor/src/, recarga al guardar) en :8000"
	@echo "  make dev-maqueta    igual, sin modo Realista (arranca antes)"
	@echo "Generar:"
	@echo "  make visor          render3d.html autocontenido"
	@echo "  make tour           tour3d.html"
	@echo "  make datos          plano PDF -> planos3d/puertas/texturas/ventanas"
	@echo "  make todo           datos + visor + tour"
	@echo "Comprobar:"
	@echo "  make check          mobiliario + privacidad + humo (carga el visor en Chromium)"
	@echo "  make mobiliario     revisar_mobiliario.py (0 incumplimientos)"
	@echo "  make privacidad     sin importes/direcciones en render3d.html y tour3d.html"
	@echo "  make humo           abre render3d.html y falla si hay errores de consola"
	@echo "  make humo-dev       lo mismo contra http://127.0.0.1:8000/ (make dev en otra terminal)"
	@echo "  make capturas       PNG de las vistas en capturas/    make medir   rendimiento"
	@echo "Blender (lento, de uno en uno en WSL):"
	@echo "  make escena | glb | hornear-rapido"

dev:
	$(PY) scripts/dev_visor.py

dev-maqueta:
	$(PY) scripts/dev_visor.py --sin-realista

visor:
	$(PY) scripts/generar_visor3d.py

tour:
	$(PY) scripts/generar_tour3d.py

datos:
	$(PY) scripts/generar_geometria3d.py
	$(PY) scripts/medir_puertas.py
	$(PY) scripts/generar_texturas.py
	$(PY) scripts/extraer_ventanas.py

todo: datos visor tour

check: mobiliario privacidad humo

mobiliario:
	$(PY) scripts/revisar_mobiliario.py

privacidad:
	./scripts/comprobar_privacidad.sh

humo:
	./scripts/capturas.sh --humo

humo-dev:
	./scripts/capturas.sh --humo --url http://127.0.0.1:8000/

capturas:
	./scripts/capturas.sh

medir:
	./scripts/capturas.sh --medir

escena:
	$(BLENDER) -b --factory-startup -noaudio -P scripts/generar_blender.py

glb:
	$(BLENDER) -b renders/escena.blend -noaudio -P scripts/exportar_glb.py

hornear-rapido:
	$(BLENDER) -b renders/escena.blend -noaudio -P scripts/hornear_visor.py -- --rapido
