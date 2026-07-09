# Huecos y duplicidades

_Generado el 2026-07-09._

## Oficios con un único PDF (legacy) y sin oferta de contratista real

Estos oficios **no tienen oferta independiente** — están cubiertos dentro del presupuesto global de Cyss, pero conviene confirmarlo:

| Oficio | PDF | Cubierto en Cyss v2.0 |
|---|---|---|
| Demolición | desconocido_Demolición.pdf | cap. 01 = 4.571,48 € |
| Pladur | desconocido_Pladur.pdf | cap. 03 = 10.448,45 € |
| Detalle baños | desconocido_Detalle baños.pdf | sub-capítulo dentro de cap. 02 y 03 (alicatados, sanitarios) |
| Encimeras | desconocido_Encimeras.pdf | no incluido en Cyss — el cap. 02 menciona colocación de pavimentos pero no encimeras |


## Oficios NO incluidos en Cyss v2.0

Estos oficios **no están en el presupuesto de Cyss** y deben contratarse aparte en cualquier escenario:

| Oficio | Contratista | Importe estimado (IVA incl.) | Notas |
|---|---:|---|---|
| Carpintería exterior | Ventanas Nacher | 10.151,48 € | Proyecto SOFIA — 8 ventanas |
| Carpintería interior | Valenzuela | 27.146,92 € | Armarios + Cocina + Puertas (3 presupuestos) |
| Encimeras | Pendiente | **¿?** | DEKTON Marmorio + SILESTONE Charcoal Soapstone |

**Total adicional mínimo si se contrata Cyss**: 37.298,40 € + encimeras.

**Importante**: las encimeras (DEKTON Marmorio + SILESTONE Charcoal Soapstone, según `desconocido_Encimeras.pdf`) **no aparecen explícitamente en Cyss v2.0**. Hay que pedir presupuesto a un marmolista y/o confirmar si Cyss las incluye.

## Duplicidades detectadas

1. **Cyss v1 + Cyss v2.0**: dos versiones del presupuesto general. Conservadas ambas en `Contratista general/` (renombradas `Cyss_v1_*` y `Cyss_v2.0_*`). La v2.0 es la vigente.
2. **David Barat 1-000079 + 1-000022 DEF**: dos presupuestos de fontanería. El 1-000022 (DEF) es el consolidado que también incluye clima. El 1-079 es el inicial, ya superado.
3. **Toni 468 + Toni 472**: dos presupuestos de albañilería. El 468 es del 'PROYECTO SOFIA' (no es este proyecto). El 472 es el que aplica (REFORMA CALLE JOSE MARIA LERMA).
4. **Poveda borrador + Paracon**: dos presupuestos de electricidad. Poveda está caducado (validez 16-11-2025). Paracon es el vigente.

## Partidas con '?' o importe abierto en PDFs de contratistas

Toni 472 tiene **5 partidas sin cerrar** (marcadas con '?' en el PDF):

- 1.13 Desmontaje de split
- 1.14 Desmontaje de split con recuperación
- 2.6 Faldcado de premarcos
- 2.7 Colocación de vierteaguas
- Notas adicionales sobre regatas, maestrado, contenedores — a confirmar.

**Acción**: escribir a Toni para que cierre estos importes antes de comparar con Cyss.

## Partidas en el Excel que no aparecen en Cyss v2.0

Del cruce con `Presupuesto.xlsx`, hay columnas en el Excel que parecen totales alternativos:

- Columna 1 de cifras: 22.055 / 3.900 / 3.360 / 4.535 / 6.177 / 8.386 / 22.433 (subtotal parcial: 70.846)
- Columna 2 de cifras: 22.135 / 9.583 / 3.965 / 5.005 / 7.962 / 8.386 / 22.433 (subtotal parcial: 79.469)
- Columna 4: 80 (albañilería), 'sin luz' (electricidad)
- Columna 7: 'Techos a 30' / 'Oscuros a 54' / 'Tabicas a 30' / 'Registro a 60' / 'Refuerzo a 25' — parecen notas del planificador, no importes.

Los importes de la columna 1 **coinciden en algunos casos con Cyss v1** y en otros con presupuestos individuales (3.360 = David Barat 1-000079 sin IVA; 6.177 = David Barat 1-000084 sin IVA; 5.005 = Paracon base). El Excel parece ser una **hoja de trabajo de Sofia (la arquitecta)** que mezcla cifras de distintas fuentes. No es un presupuesto contractual.
