import subprocess, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RENDER_DIR = Path.home()/"Downloads/vigo-bloque-3x3/tiles"
OUT = ROOT/"work/tiles-p3"
PROMPT = ROOT/"pipeline/prompts/p-3-highbit.txt"
TILES = sys.argv[1:] or ["r1c0","r1c2","r2c1","r2c0","r2c2","r0c1"]
OUT.mkdir(exist_ok=True)
for t in TILES:
    dst = OUT/f"draw_{t}.png"
    if dst.exists():
        print("skip", t); continue
    cmd = ["node", str(ROOT/"pipeline/imggen.mjs"), str(dst), str(PROMPT), str(RENDER_DIR/f"render_{t}.png")]
    env = {**os.environ, "MODEL":"gemini-3.1-flash-image", "AR":"1:1", "LABEL":f"p3-{t}"}
    r = subprocess.run(cmd, env=env)
    print("done", t, "rc", r.returncode, flush=True)
    if r.returncode != 0:
        print("STOP at", t, flush=True); sys.exit(r.returncode)
print("ALL DONE")
