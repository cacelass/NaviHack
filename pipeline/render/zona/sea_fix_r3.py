import sys,numpy as np,cv2
sys.path.insert(0,"/home/sonder/proyectos/NaviHack")
from PIL import Image
from pipeline.render.sea import apply_sea
Image.MAX_IMAGE_PIXELS=None
R=int(sys.argv[1])
wm=np.load("/tmp/opencode/port_fix_cache/agua_fe44a6c1a82ac6cb.npy")
wo=cv2.morphologyEx(wm.astype(np.uint8),cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*R+1,2*R+1)))>0
print("water px removed:",int((wm&~wo).sum()),"added:",int((wo&~wm).sum()))
pre=np.asarray(Image.open("work/estilo/v17c.png").convert("RGB"))
new=apply_sea(pre,wo,2,(0,0,3072,3072))
s3=np.asarray(Image.open("work/seamwin/s3.png").convert("RGB"))
s5=np.asarray(Image.open("work/mapa-sonnet/s5.png").convert("RGB"))
d=(np.abs(new.astype(int)-s3.astype(int)).sum(2)>0).astype(np.uint8)
near=cv2.dilate((wm&~wo).astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(61,61)))
d=cv2.dilate(d,np.ones((3,3),np.uint8))*near
a=cv2.GaussianBlur(d.astype(np.float32),(0,0),1.2)[...,None]
out=np.clip(s5*(1-a)+new*a+.5,0,255).astype(np.uint8)
Image.fromarray(out).save("work/mapa-sonnet/s6.png")
print("changed px:",int(d.sum()))
