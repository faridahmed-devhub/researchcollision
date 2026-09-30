import os, sys, glob
import pymupdf
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(BASE, "research_paper.pdf")
DPI = 175
S = DPI / 72.0
doc = pymupdf.open(PDF)
n = doc.page_count

# precompute raster per page (mupdf high fidelity)
rast = {}
for p in range(n):
    pix = doc[p].get_pixmap(dpi=DPI, alpha=False)
    rast[p] = np.asarray(Image.open(os.path.join(BASE, "_mupdf_pages", f"m{p+1:02d}.png")).convert("L"), dtype=np.float32)

def ink(bb, img):
    x0, y0, x1, y1 = [v * S for v in bb]
    x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(img.shape[1], int(x1)) , min(img.shape[0], int(y1))
    if x1 <= x0 or y1 <= y0:
        return 0.0, 0
    region = img[y0:y1, x0:x1]
    return float((region < 140).mean()), int(region.size)

print("=== per-span ink test: spans with ink fraction < 0.02 (missing glyphs) ===")
tot = 0
bad_spans = 0
for p in range(n):
    img = rast[p]
    d = doc[p].get_text("rawdict")
    for blk in d["blocks"]:
        for line in blk.get("lines", []):
            for span in line.get("spans", []):
                t = "".join(c["c"] for c in span["chars"])
                if not t.strip():
                    continue
                tot += 1
                frac, sz = ink(span["bbox"], img)
                if sz and frac < 0.02 and span["size"] >= 5:
                    bad_spans += 1
                    if bad_spans <= 25:
                        print(f"  page {p+1}: ink={frac:.3f} font={span['font']} {span['size']:.1f}pt bbox={tuple(round(x) for x in span['bbox'])} text={t[:60]!r}")
print(f"total spans {tot}, low-ink spans {bad_spans}")

print("\n=== per-page ink coverage map (16x24 grid cells with <1% ink inside content area) ===")
ML, MT = 51, 57
for p in range(n):
    img = rast[p]
    H, W = img.shape
    # content area in pixels
    cx0, cy0, cx1, cy1 = int(ML*S), int(MT*S), int(544*S), int(817*S)
    abs_ink = float((img > 0).mean())
    # overlaid empty "page" cells fully inside content
    empty = []
    gy = np.linspace(cy0, cy1, 10).astype(int)
    gx = np.linspace(cx0, cx1, 10).astype(int)
    for row in range(len(gy) - 1):
        for col in range(len(gx) - 1):
            cell = img[gy[row]:gy[row+1], gx[col]:gx[col+1]]
            if cell.size and float((cell < 245).mean()) < 0.004:
                empty.append((row, col))
    print(f"  page {p+1}: abs ink {abs_ink*100:.1f}% cells<0.4%ink: {len(empty)}/81")
    if len(empty) > 40:
        print("      >> suspiciously empty page")