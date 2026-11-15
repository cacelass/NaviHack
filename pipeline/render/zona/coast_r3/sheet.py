import sys
from PIL import Image
C="/home/sonder/proyectos/NaviHack/work/mapa-sonnet/c/"
tiles=[tuple(map(int,a.split(","))) for a in sys.argv[2:]]
rows=[]
S=Image.new("RGB",(3*400,400*len(tiles)))
for i,(x,y) in enumerate(tiles):
    for j,f in enumerate((f"map_{x}_{y}.png",f"out_{x}_{y}.png",f"render_{x}_{y}.png")):
        S.paste(Image.open(C+f).convert("RGB").resize((400,400)),(j*400,i*400))
S.save(C+sys.argv[1])
