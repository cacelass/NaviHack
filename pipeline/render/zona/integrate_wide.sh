#!/usr/bin/env bash
# Integra las 13 ventanas pintadas con referencia de estilo sobre v14 (puerto ya integrado).
# Orden: muelle norte, luego columnas de dentro afuera (c2, c1, e1, e2) y, dentro de cada una, de
# arriba abajo: el borde difuminado de cada ventana lo tapa la siguiente, sin dejar ver lo viejo.
# --hard-right en c2 y e1: su borde derecho lo cubre la columna siguiente o es el borde del lienzo.
# --fade 99990 100000: sin degradado inferior (era solo para el árbol de Porta do Sol).
set -euo pipefail
cd /home/sonder/proyectos/NaviHack.zona-vialia
RENDER=work/render-wide/render.png
cur=work/puerto/v14.png
step() { # nombre extra...
  local name=$1; shift
  local read; read=$(python3 -c "import json;p=json.load(open('work/estilo/plan.json'))['$name'];print(p['x'],p['y'],p['cut_top'])")
  set -- $read "$@"
  local x=$1 y=$2 cut=$3; shift 3
  local out=work/estilo/paso_${name}.png
  python3 -W ignore -m pipeline.render.port_fix --extend --base "$cur" --render "$RENDER" \
    --window "work/estilo/draw_${name}.png" --origin "$x" "$y" --fade 99990 100000 --cut-top "$cut" \
    "$@" --out "$out" 2>&1 | grep -v -i polyfit || true
  cur=$out
}
step n1
step c2_a --hard-right
step c2_b2 --hard-right
step c2_c2 --hard-right
step c1_a
step c1_b2
step c1_c
step e1_a --hard-right
step e1_b2 --hard-right
step e1_c --hard-right
step e2_a
step e2_b2
step e2_c
cp "$cur" work/estilo/v17.png
echo "listo work/estilo/v17.png"
