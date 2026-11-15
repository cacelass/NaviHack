set -e
cd /home/sonder/proyectos/NaviHack.mapa-sonnet/pipeline/render
W=../../work/mapa-sonnet/w
B=$W/c0.png; cp ../../work/seamwin/s3.png $B
s(){ python3 seam_window_blend.py $B $W/$1 $W/c1.png "${@:2}" >/dev/null; mv $W/c1.png $B; }
s draw_A1.png --origin 512 2048 --axis v --clip 0 2400 9999 9999
s draw_X1.png --origin 1536 1536 --axis x --taper-lo 120
s draw_B1.png --origin 1536 1100 --axis v --clip 0 1260 9999 1580
s draw_Y1.png --origin 512 1536 --axis x --taper-lo 120
s draw_D1.png --origin 1536 2048 --axis v --clip 0 2500 9999 9999
s draw_E1.png --origin 512 1100 --axis v --clip 0 1300 9999 1620
python3 seam_metric.py $B | tail -12
# round-2 fixes: ghosts found by Jose
B=$W/c0.png
python3 seam_window_blend.py $B $W/draw_B1.png $W/c1.png --origin 1536 1100 --axis v --core 400 --fade 480 --clip 1880 1440 2350 1700 >/dev/null; mv $W/c1.png $B
python3 - <<'PY'
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
W="../../work/mapa-sonnet/w/"
b=np.asarray(Image.open(W+"c0.png").convert("RGB")).astype(np.float32)
o=np.asarray(Image.open("../../work/seamwin/s3.png").convert("RGB")).astype(np.float32)
x0,y0,x1,y1=820,1650,980,1790
m=np.zeros(b.shape[:2],np.float32); m[y0:y1,x0:x1]=1
m=cv2.GaussianBlur(m,(0,0),12); m=np.clip(m*1.6,0,1)[...,None]
Image.fromarray(np.clip(o*m+b*(1-m)+.5,0,255).astype(np.uint8)).save(W+"c0.png")
PY
python3 seam_metric.py $B | tail -12
