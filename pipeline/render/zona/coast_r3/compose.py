import sys,numpy as np,cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
C="/home/sonder/proyectos/NaviHack/work/mapa-sonnet/"
src,dst=sys.argv[1],sys.argv[2]; tiles=[tuple(map(int,a.split(","))) for a in sys.argv[3:]]
base=np.asarray(Image.open(C+src).convert("RGB")).copy()
wm=np.load("/tmp/opencode/port_fix_cache/agua_fe44a6c1a82ac6cb.npy").astype(np.uint8)
land_near=cv2.dilate(wm,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(91,91)))>0   # water + 45 px of land
allowed=land_near
landd=cv2.distanceTransform(wm,cv2.DIST_L2,3)   # water px: distance to land
thr_map=np.where(landd>25,85,45).astype(np.float32)
for x,y in tiles:
    x1,y1=min(x+512,5120),min(y+512,3072); w,h=x1-x,y1-y
    old=base[y:y1,x:x1].astype(np.float32)
    new=np.asarray(Image.open(f"{C}c/out_{x}_{y}.png").convert("RGB").resize((w,h),Image.LANCZOS)).astype(np.float32)
    d0=np.abs(new-old).sum(2); keep=d0<np.percentile(d0,70)
    for c in range(3):  # colour transfer from the quiet 70% of pixels
        a=old[...,c][keep];b=new[...,c][keep]; new[...,c]=(new[...,c]-b.mean())*(a.std()/(b.std()+1e-3))+a.mean()
    new=np.clip(new,0,255); d=np.abs(new-old).sum(2)
    m=((d>thr_map[y:y1,x:x1])&allowed[y:y1,x:x1]).astype(np.uint8)
    n,l,st,_=cv2.connectedComponentsWithStats(m,connectivity=8)
    big=np.isin(l,[i for i in range(1,n) if st[i,4]>=40]).astype(np.uint8)
    m=cv2.morphologyEx(cv2.dilate(big,np.ones((7,7),np.uint8)),cv2.MORPH_CLOSE,np.ones((7,7),np.uint8)).astype(np.float32)
    ry0,ry1,rx0,rx1=max(870-y,0),min(1310-y,h),max(3060-x,0),min(3540-x,w)
    if ry1>ry0 and rx1>rx0: m[ry0:ry1,rx0:rx1]=0   # keep the redrawn quay corner
    e=np.minimum(np.minimum(np.arange(w),np.arange(w)[::-1])[None,:],np.minimum(np.arange(h),np.arange(h)[::-1])[:,None])
    m=np.clip(cv2.GaussianBlur(m,(0,0),1.5)*1.3,0,1)*np.clip(e/16,0,1)
    base[y:y1,x:x1]=np.clip(old*(1-m[...,None])+new*m[...,None]+.5,0,255).astype(np.uint8)
    print(x,y,"mask%",round(float((m>.5).mean())*100,1))
Image.fromarray(base).save(C+dst)
