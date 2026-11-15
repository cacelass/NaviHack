# usage: run.sh X Y  (512 px tile of s12 + render -> model)
cd /home/sonder/proyectos/NaviHack.mapa-sonnet-r3
C=/home/sonder/proyectos/NaviHack/work/mapa-sonnet
python3 - "$1" "$2" <<'PY'
import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
x,y=int(sys.argv[1]),int(sys.argv[2]);b=(x,y,min(x+512,5120),min(y+512,3072))
C="/home/sonder/proyectos/NaviHack/work/mapa-sonnet/"
Image.open(C+"s13.png").convert("RGB").crop(b).resize((1024,1024),Image.LANCZOS).save(f"{C}c/map_{x}_{y}.png")
Image.open("/home/sonder/proyectos/NaviHack/work/render-wide/render.png").convert("RGB").crop(b).resize((1024,1024),Image.LANCZOS).save(f"{C}c/render_{x}_{y}.png")
PY
MODEL=gemini-3.1-flash-image AR=1:1 LABEL=r3-costa-$1-$2 node pipeline/imggen.mjs $C/c/out_$1_$2.png $C/c/prompt.txt $C/c/map_$1_$2.png $C/c/render_$1_$2.png
