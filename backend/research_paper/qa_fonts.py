import os, sys, collections, glob, subprocess
import pymupdf
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(BASE, "research_paper.pdf")
DPI = 175
MUP = os.path.join(BASE, "_mupdf_pages")
os.makedirs(MUP, exist_ok=True)

doc = pymupdf.open(PDF)
n = doc.page_count

# ---- 1. all fonts with embed status ----
print("=== FONTS EMBEDDED? (extract_font) ===")
seen = set()
info = collections.defaultdict(list)
for i in range(n):
    for f in doc[i].get_fonts(full=True):
        xref, ext, ftype, basefont, name, enc = f[:6]
        key = (basefont, ftype, ext)
        if key not in seen:
            seen.add(key)
            info[key].append(i + 1)
for (basefont, ftype, ext), pages in sorted(info.items()):
    print(f"  basefont={basefont:45s} type={ftype:8s} ext={ext:5s} pages={pages[:4]}")

# ---- 2. rasterize with mupdf and diff against poppler ----
print("\n=== MUPDF vs POPPLER per-page pixel diff ===")
poppler = sorted(glob.glob(os.path.join(BASE, "qa_pages", "page-*.png")))
os.makedirs(os.path.join(BASE, "_diff_iso"), exist_ok=True)
for p in range(1, n + 1):
    pix = doc[p - 1].get_pixmap(dpi=DPI, alpha=False)
    mup_png = os.path.join(MUP, f"m{p:02d}.png")
    pix.save(mup_png)
    a = np.asarray(Image.open(mup_png).convert("L"), dtype=np.float32)
    b = np.asarray(Image.open(poppler[p - 1]).convert("L"), dtype=np.float32)
    if a.shape != b.shape:
        print(f"  page {p}: size mismatch {a.shape} vs {b.shape}")
        continue
    diff = (np.abs(a - b) > 40).sum()
    ratio = diff / a.size
    # save highlighted diff for inspection
    dmap = np.where(np.abs(a - b) > 40, 255, 0).astype(np.uint8)
    Image.fromarray(dmap).save(os.path.join(BASE, "_diff_iso", f"d{p:02d}.png"))
    print(f"  page {p}: diff pixels={diff} ({ratio*100:.2f}%)")
    if ratio > 0.001:
        # locate biggest diff region bbox
        ys, xs = np.where(np.abs(a - b) > 40)
        if len(xs):
            print(f"      region x[{xs.min()}-{xs.max()}] y[{ys.min()}-{ys.max()}]")

# ---- 3. figure color presence on pages (bars of figure SVGs) ----
print("\n=== FIGURE COLORS present per page (both rasters must agree) ===")
colors = {"blue": (44, 123, 182), "orange": (253, 174, 97), "red": (215, 25, 28)}
for p in range(1, n + 1):
    im = np.asarray(Image.open(glob.glob(os.path.join(BASE, "qa_pages", f"page-{p:02d}.png"))[0]).convert("RGB"))
    found = []
    for name, (r, g, b) in colors.items():
        m = (np.abs(im[:, :, 0].astype(int) - r) < 30) & (np.abs(im[:, :, 1].astype(int) - g) < 30) & (np.abs(im[:, :, 2].astype(int) - b) < 30)
        if m.sum() > 200:
            found.append(name)
    if found:
        print(f"  page {p}: {found}")