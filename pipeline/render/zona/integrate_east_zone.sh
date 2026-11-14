#!/usr/bin/env bash
# Integra las 6 ventanas de la zona nueva. Cada una se solapa 64 px con la de arriba y entra con
# fundido cruzado (la de arriba no se desvanece: la de abajo la cubre poco a poco), así no queda
# una línea oscura donde se juntan.
# Orden: columna derecha (c2) primero y la izquierda (c1) encima.
# --fade 99990 100000: sin degradado inferior (era solo para el árbol de Porta do Sol).
# --hard-right en c2: el borde derecho es el borde del lienzo, no se funde con nada.
set -euo pipefail
cd /home/sonder/proyectos/NaviHack.zona-vialia
RENDER=work/render-expansion/render.png
cur=work/puerto/v14.png
step() { # nombre x y cut-top extra...
  local out=work/zona/paso_$1.png name=$1 x=$2 y=$3 cut=$4; shift 4
  python3 -W ignore -m pipeline.render.port_fix --extend --base "$cur" --render "$RENDER" \
    --window "work/zona/draw_${name}.png" --origin "$x" "$y" --fade 99990 100000 --cut-top "$cut" \
    "$@" --out "$out" 2>&1 | grep -v -i polyfit || true
  cur=$out
}
# ventanas: a = 934..1958, b = 1894..2918 (solapa 64 con a), c = 2048..3072 con corte a partir de 2854
step c2_a 3072  934   0 --hard-right
step c2_b2 3072 1894   0 --hard-right
step c2_c2 3072 2048 352 --hard-right
step c1_a 2816  934   0
step c1_b2 2816 1894   0
step c1_c 2816 2048 806
cp "$cur" work/zona/v15.png
echo "listo work/zona/v15.png"
