import os, re, sys, json, collections
import pymupdf

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
doc = pymupdf.open(os.path.join(BASE, "research_paper.pdf"))
n = doc.page_count
W, H = 595.28, 841.89
ML, MR, MT, MB = 51.02, 595.28 - 51.02, 56.7, 841.89 - 56.7  # 18/18/20/20 mm
print(f"pages={n}  page=({W:.0f}x{H:.0f})  margins L{ML:.0f} R{MR:.0f} T{MT:.0f} B{MB:.0f}")

# ------------------------------------------------------------------ fonts
print("\n=== FONT USAGE (spans) ===")
font_of_char = collections.Counter()
for i in range(n):
    d = doc[i].get_text("rawdict")
    for blk in d["blocks"]:
        for line in blk.get("lines", []):
            for span in line.get("spans", []):
                font_of_char[(span["font"], span["size"])] += len(span["chars"])
for (font, size), cnt in font_of_char.most_common(30):
    print(f"  {size:5.1f}pt {font:40s} {cnt} chars")

# fonts flagged as non-embedded base-14 that poppler can't show
print("\n=== spans using Symbol/ArialUnicode/any suspicious font ===")
sus = collections.Counter()
for i in range(n):
    d = doc[i].get_text("rawdict")
    for blk in d["blocks"]:
        for line in blk.get("lines", []):
            for span in line.get("spans", []):
                fn = span["font"] or ""
                ufn = fn.upper()
                if "SYMBOL" in ufn or "ARIALUNICODE" in ufn or "ZAPF" in ufn or "DINGBAT" in ufn:
                    text = "".join(ch["c"] for ch in span["chars"])
                    sus[fn] += text

for fn, t in sus.items():
    print("  FONT:", fn)
    print("   chars:", repr(t[:200]))

# ------------------------------------------------------------------ text-text overlap
print("\n=== TEXT-TEXT OVERLAP (span intersection > 45% of smaller area) ===")
def overlap_area(a, b):
    ox = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    oy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return ox * oy

def area(a):
    return max(0, (a[2]-a[0])*(a[3]-a[1]))

total_overlap_pages = 0
for i in range(n):
    d = doc[i].get_text("rawdict")
    spans = []
    for blk in d["blocks"]:
        for line in blk.get("lines", []):
            for span in line.get("spans", []):
                txt = "".join(ch["c"] for ch in span["chars"])
                if txt.strip():
                    spans.append((tuple(span["bbox"]), txt, span["font"]))
    hits = []
    for a_i in range(len(spans)):
        for b_i in range(a_i + 1, len(spans)):
            a, b = spans[a_i][0], spans[b_i][0]
            ov = overlap_area(a, b)
            if ov == 0:
                continue
            small = min(area(a), area(b))
            if small and ov / small > 0.45:
                hits.append((spans[a_i], spans[b_i]))
    if hits:
        total_overlap_pages += 1
        print(f"  page {i+1}: {len(hits)} overlaps")
        for h in hits[:8]:
            print(f"    A '{h[0][1][:50]}' f={h[0][2]} bbox={tuple(round(x,0) for x in h[0][0])}")
            print(f"    B '{h[1][1][:50]}' f={h[1][2]} bbox={tuple(round(x,0) for x in h[1][0])}")
print("pages with text-text overlaps:", total_overlap_pages)

# ------------------------------------------------------------------ margins
print("\n=== TEXT OUTSIDE MARGINS ===")
for i in range(n):
    d = doc[i].get_text("rawdict")
    viol = []
    for blk in d["blocks"]:
        for line in blk.get("lines", []):
            for span in line.get("spans", []):
                txt = "".join(ch["c"] for ch in span["chars"])
                if not txt.strip():
                    continue
                x0, y0, x1, y1 = span["bbox"]
                if x0 < ML - 1 or x1 > MR + 1:
                    viol.append((txt[:40], round(x0), round(x1)))
    if viol:
        print(f"  page {i+1}: {len(viol)} x-overflows")
        for v in viol[:10]:
            print("   ", v)

# ------------------------------------------------------------------ footer collisions
print("\n=== CONTENT IN FOOTER BAND (y>820; footer itself excluded) ===")
footer_y = {}
for i in range(n):
    d = doc[i].get_text("rawdict")
    for blk in d["blocks"]:
        for line in blk.get("lines", []):
            for span in line.get("spans", []):
                txt = "".join(ch["c"] for ch in span["chars"])
                if not txt.strip():
                    continue
                x0, y0, x1, y1 = span["bbox"]
                is_footer = re.match(rf"^Page {i+1} of {n}$", txt.strip())
                if y0 > 815 and not is_footer:
                    footer_y[i+1] = footer_y.get(i+1, []) + [(txt[:40], round(x0), round(y0), round(y1))]
for p, v in footer_y.items():
    print(f"  page {p}: {len(v)}")
    for x in v[:10]:
        print("   ", x)

# ------------------------------------------------------------------ drawings (figures) vs text overlap + figure extents
print("\n=== DRAWINGS (vector) vs margins ===")
for i in range(n):
    dr = doc[i].get_drawings()
    if not dr:
        continue
    xmin = min(d["rect"].x0 for d in dr)
    xmax = max(d["rect"].x1 for d in dr)
    ymin = min(d["rect"].y0 for d in dr)
    ymax = max(d["rect"].y1 for d in dr)
    flag = ""
    if xmax > MR + 1:
        flag += " RIGHT-OVERFLOW"
    if xmin < ML - 1:
        flag += " LEFT-OVERFLOW"
    if ymin < MT - 5:
        flag += " TOP-OVERFLOW"
    if ymax > MB + 1 and ymax < 815:
        flag += " BOTTOM-OVERFLOW"
    print(f"  page {i+1}: {len(dr)} drawing objs bbox=({xmin:.0f},{ymin:.0f},{xmax:.0f},{ymax:.0f}){flag}")

# figure rect: specifically check the 3 svg figures' width vs content width
print("\n=== LARGEST DRAWING bbox width per page vs text column ===")
for i in range(n):
    dr = doc[i].get_drawings()
    if not dr:
        continue
    w = max(d["rect"].width for d in dr)
    print(f"  page {i+1}: max drawing width {w:.1f}pt (content column {MR-ML:.1f}pt)")