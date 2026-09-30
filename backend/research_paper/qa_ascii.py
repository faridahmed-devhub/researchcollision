import os, sys, glob
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

# We render an ASCII "photo" of each page from the mupdf raster.
# chars: more ink density => denser symbol
CHARS = " .:-=+*#%@"

def asciify(png, cols=96, rows=54):
    im = np.asarray(Image.open(png).convert("L"), dtype=np.float32)
    H, W = im.shape
    cs = W / cols
    rs = H / rows
    out = []
    for r in range(rows):
        y0, y1 = int(r * rs), min(H, int((r + 1) * rs))
        line = []
        for c in range(cols):
            x0, x1 = int(c * cs), min(W, int((c + 1) * cs))
            cell = im[y0:y1, x0:x1]
            dark = float((cell < 180).mean())
            line.append(CHARS[min(len(CHARS) - 1, int(dark * len(CHARS)))])
        out.append("".join(line))
    return out

pages = sorted(glob.glob(os.path.join(BASE, "_mupdf_pages", "m*.png")))
for idx, png in enumerate(pages, 1):
    print(f"\n########## PAGE {idx} ##########")
    for line in asciify(png):
        print(line)