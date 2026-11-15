import sys,numpy as np,cv2
sys.path.insert(0,"/home/sonder/proyectos/NaviHack")
from PIL import Image
from pipeline.render.sea import painted_water
Image.MAX_IMAGE_PIXELS=None
box=(3040,820,3700,1330); x0,y0,x1,y1=box
wm=np.load("/tmp/opencode/port_fix_cache/agua_fe44a6c1a82ac6cb.npy")[y0:y1,x0:x1]
pre=np.asarray(Image.open("work/estilo/v17c.png").convert("RGB"))[y0:y1,x0:x1]
cur=np.asarray(Image.open("work/mapa-sonnet/s7.png").convert("RGB"))
lab=cv2.cvtColor(pre,cv2.COLOR_RGB2LAB)
nonblue=~painted_water(pre)
near=cv2.dilate((~wm).astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(91,91)))>0
cand=(nonblue&near).astype(np.uint8)
n,l,st,_=cv2.connectedComponentsWithStats(cand,connectivity=8)
dark=(lab[...,0]<85)
keep=np.zeros(cand.shape,bool)
for i in range(1,n):
    if st[i,4]>400000: continue   # the quay itself
    c=l==i
    if st[i,4]>=25 and dark[c].sum()>=8: keep|=c
keep&=~(~wm)  # only where the old sea mask had eaten it
keep=cv2.dilate(keep.astype(np.uint8),np.ones((5,5),np.uint8))>0
print("restored px",int(keep.sum()))
a=cv2.GaussianBlur(keep.astype(np.float32),(0,0),1.0)[...,None]
out=cur.copy()
reg=cur[y0:y1,x0:x1].astype(np.float32)
out[y0:y1,x0:x1]=np.clip(reg*(1-a)+pre*a+.5,0,255).astype(np.uint8)
Image.fromarray(out).save("work/mapa-sonnet/s8.png")
rows=[]
for (x,y) in [(3330,940),(3170,1050),(3600,1000)]:
    rows.append(np.hstack([cur[y-60:y+60,x-90:x+90],out[y-60:y+60,x-90:x+90]]))
Image.fromarray(np.vstack(rows)).resize((720,720),Image.NEAREST).save("work/mapa-sonnet/obj.png")
