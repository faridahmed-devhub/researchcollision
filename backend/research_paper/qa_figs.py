import os, sys, re, glob
import pymupdf
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
doc = pymupdf.open(os.path.join(BASE, "research_paper.pdf"))
n = doc.page_count
DPI = 175
S = DPI / 72.0

texts = [doc[i].get_text() for i in range(n)]

# figure captions present on which pages
print("=== figure captions ===")
for lbl in ["Figure 1:", "Figure 2:", "Figure 3:"]:
    where = [i + 1 for i, t in enumerate(texts) if lbl in t]
    print(f"  {lbl} on pages {where}")

# figure svg titles (from inside svg) on which pages
for lbl in ["Evidence surface distribution", "Evidence records per system", "Cases with evidence per system"]:
    where = [i + 1 for i, t in enumerate(texts) if lbl in t]
    print(f"  svg-title {lbl!r} on pages {where}")

# check whether any svg drawing block straddles a page boundary (split figure)
print("\n=== svg drawing clusters: contiguous y-extent vs page height ===")
for p in range(n):
    dr = doc[p].get_drawings()
    if not dr:
        continue
    # cluster drawings into y-groups separated by gaps > 40pt (different svg blocks/tables)
    rects = sorted((d["rect"].y0, d["rect"].y1) for d in dr)
    groups = []
    cur = None
    for y0, y1 in rects:
        if cur is None or y0 - cur[1] > 40:
            cur = [y0, y1]
            groups.append(cur)
        else:
            cur[1] = max(cur[1], y1)
    for g in groups:
        if g[1] - g[0] > 200:  # big vector block (svg bars or big table border)
            print(f"  page {p+1}: big vector block y[{g[0]:.0f}..{g[1]:.0f}] height {g[1]-g[0]:.0f}")

# Check caption y-pos relative to figure block on pages 5 & 6
print("\n=== page 5/6 figure + caption geometry (from raster, per horizontal band) ===")
import re as _re
for p in [4, 5]:
    t = doc[p].get_text("rawdict")
    caps = []
    serp = []
    for blk in t["blocks"]:
        for line in blk.get("lines", []):
            for span in line.get("spans", []):
                tx = "".join(c["c"] for c in span["chars"])
                if _re.match(r"^Figure \d:", tx) or _re.match(r"^Evidence (surface|records|Cases)", tx):
                    caps.append((tx[:40], tuple(round(x) for x in span["bbox"])))
    dr = doc[p].get_drawings()
    if dr:
        rects = sorted((d["rect"].y0, d["rect"].y1) for d in dr)
        # svg block = biggest contiguous group
        groups = []
        cur = None
        for y0, y1 in rects:
            if cur is None or y0 - cur[1] > 40:
                cur = [y0, y1]; groups.append(cur)
            else:
                cur[1] = max(cur[1], y1)
        groups.sort(key=lambda g: g[1]-g[0], reverse=True)
        print(f"  page {p+1} top-3 vector blocks heights: {[(round(g[0]),round(g[1]),round(g[1]-g[0])) for g in groups[:3]]}")
    print(f"  page {p+1} caption/svg-text spans: {caps}")