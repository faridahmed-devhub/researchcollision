import os, sys, json, collections
import pymupdf

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
doc = pymupdf.open(os.path.join(BASE, "research_paper.pdf"))

for page_idx in (4, 5):   # pdf pages 5 and 6
    page = doc[page_idx]
    print(f"\n===== PAGE {page_idx+1} fill objects (by color) =====")
    fills = collections.defaultdict(list)
    lines = 0
    for d in page.get_drawings():
        if d["fill"]:
            col = tuple(round(c, 2) for c in d["fill"])
            r = d["rect"]
            fills[col].append((round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)))
        else:
            r = d["rect"]
            if r.width > 1 and r.height > 1:
                lines += 1
    for col, rects in sorted(fills.items(), key=lambda kv: -len(kv[1])):
        print(f"  color={col} count={len(rects)}")
        for rct in rects[:12]:
            w = rct[2] - rct[0]; h = rct[3] - rct[1]
            print(f"     x0={rct[0]} y0={rct[1]} x1={rct[2]} y1={rct[3]}  {w:.1f}x{h:.1f}")
    print(f"  non-trivial strokes: {lines}")