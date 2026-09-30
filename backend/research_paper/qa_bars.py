import os, sys, re, json
import pymupdf
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(BASE, "research_paper.pdf")
S = 175 / 72.0
DPI = 175
doc = pymupdf.open(PDF)

# canonical counts (authoritative; NEVER change)
FIG1 = [("intersection-55", 55, "#2c7bb6"), ("hypothesis-50", 50, "#fdae61"), ("gap-83", 83, "#d7191c")]
FIG2 = [("keyword-41", 41, "#1b7837"), ("embedding-36", 36, "#762a83"),
        ("llm_only-53", 53, "#2166ac"), ("pipeline-58", 58, "#b2182b")]
FIG3 = [("keyword-12", 12, "#1b7837"), ("embedding-12", 12, "#762a83"),
        ("llm_only-12", 12, "#2166ac"), ("pipeline-8", 8, "#b2182b")]
# [intended value sequence, expected relative fractions]
EXPECT = [("fig1", [v for _, v, _ in FIG1]),
          ("fig2", [v for _, v, _ in FIG2]),
          ("fig3", [v for _, v, _ in FIG3])]

_RECT = re.compile(r"<rect x=\"([\d.]+)\" y=\"([\d.]+)\" width=\"([\d.]+)\" height=\"([\d.]+)\" fill=\"(#[\da-fA-F]{6})\"")
_LBL = re.compile(r"<text x=\"([\d.]+)\" y=\"([\d.]+)\" text-anchor=\"middle\" font-size=\"13\" font-weight=\"bold\">([^<]+)</text>")


def parse_svg(name):
    svg = open(os.path.join(BASE, "figures", name), encoding="utf-8-sig").read()
    rects = {hexf(m.group(5)): {"y": float(m.group(2)), "h": float(m.group(4))}
             for m in _RECT.finditer(svg) if m.group(5) != "#ffffff"}
    labels = [(m.group(3), float(m.group(1)), float(m.group(2))) for m in _LBL.finditer(svg)]
    return rects, labels


def hexf(c):
    return "#" + c.lstrip("#").upper()


def bar_height(rects, color):
    r = rects.get(hexf(color))
    return None if r is None else r["h"]


def fractions(vals):
    m = max(vals)
    return [v / m for v in vals]


ok = True
results = {}
print("=== SVG bar proportionality (embedded verbatim -> source of truth) ===")
names = {"fig1": "fig1_surface_distribution.svg", "fig2": "fig2_evidence_per_system.svg",
         "fig3": "fig3_case_coverage_per_system.svg"}
colors = {"fig1": [c for _, _, c in FIG1], "fig2": [c for _, _, c in FIG2], "fig3": [c for _, _, c in FIG3]}
for tag, vals in EXPECT:
    rects, labels = parse_svg(names[tag])
    hs = [bar_height(rects, c) for c in colors[tag]]
    if any(h is None for h in hs):
        print(f"  [FAIL] {tag}: missing bar rect(s) -> {hs}")
        ok = False
        results[tag] = False
        continue
    g = fractions(vals)
    f = fractions(hs)
    errs = [abs(a - b) for a, b in zip(g, f)]
    worst = max(errs)
    status = "PASS" if worst <= 0.015 else "FAIL"
    pair = ", ".join(f"{v}:{round(h,1)}px" for v, h in zip(vals, hs))
    print(f"  [{status}] {tag} values {vals} -> heights {pair}")
    print(f"          expected fractions {[round(x,4) for x in g]}  drawn {[round(x,4) for x in f]}  max-err {worst:.4f}")
    ok = ok and (worst <= 0.015)
    results[tag] = (status == "PASS")

# raster spot-check: fig1 must be proportional on its own page, and fig2/fig3
# must be present (upper/lower halves) on the §5.3 page. Figure pages are located
# dynamically from the PDF text so the check survives any manuscript reflow.
print("\n=== raster spot-check (pages located dynamically) ===")

def raster(page_no, dpi=DPI):
    pix = doc[page_no].get_pixmap(dpi=dpi, alpha=False)
    return np.asarray(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))

def page_of(needle, start=1):
    for p in range(start, doc.page_count):
        if needle in doc[p].get_text():
            return p
    return None

scan_from = 2
for p in range(1, doc.page_count):
    for line in doc[p].get_text().splitlines():
        if line.strip() == "Contents":
            scan_from = p + 1

p_fig1 = page_of("Figure 1:", start=scan_from)
p_fig2 = page_of("Figure 2:", start=scan_from)
p_fig3 = page_of("Figure 3:", start=scan_from)
if p_fig1 is None or p_fig2 is None or p_fig3 is None:
    print("  [FATAL] could not locate figure caption pages", p_fig1, p_fig2, p_fig3)
    ok = False
    results["raster"] = False
else:
    print(f"  figure pages: fig1={p_fig1 + 1} fig2={p_fig2 + 1} fig3={p_fig3 + 1}")
    im = raster(p_fig1)
    raster_f1 = []
    for name, val, color in FIG1:
        r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
        m = (np.abs(im[:, :, 0].astype(int) - r) < 26) & \
            (np.abs(im[:, :, 1].astype(int) - g) < 26) & \
            (np.abs(im[:, :, 2].astype(int) - b) < 26)
        ys = np.where(m)[0]
        ext = int(ys.max() - ys.min()) if len(ys) else 0
        raster_f1.append((name, ext, len(ys)))
        print(f"  {name}: raster vertical extent {ext}px  pixels={len(ys)}")

    fr = [e for _, e, _ in raster_f1 if e]
    if fr:
        g = fractions([v for _, v, _ in FIG1])
        f = fractions([e for _, e, _ in raster_f1])
        worst = max(abs(a - b) for a, b in zip(g, f))
        status = "PASS" if worst <= 0.04 else "FAIL"
        print(f"  raster-fractions {[round(x,4) for x in f]} expected {[round(x,4) for x in g]} max-err {worst:.4f} -> [{status}]")
        ok = ok and (status == "PASS")
        results["fig1_raster"] = (status == "PASS")

    # fig2 (large bars, upper half) and fig3 (lower half) share the §5.3 page
    pfig2 = p_fig2 if p_fig2 == p_fig3 else p_fig2
    im6 = raster(pfig2)
    h6 = im6.shape[0]
    for band, fig in (("fig2 (upper)", FIG2), ("fig3 (lower)", FIG3)):
        y0, y1 = (0, h6 // 2) if band.startswith("fig2") else (h6 // 2, h6)
        seen = {}
        for name, val, color in fig:
            r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
            m = (np.abs(im6[y0:y1, :, 0].astype(int) - r) < 26) & \
                (np.abs(im6[y0:y1, :, 1].astype(int) - g) < 26) & \
                (np.abs(im6[y0:y1, :, 2].astype(int) - b) < 26)
            n = int(np.where(m)[1].size)
            seen[name] = n
        miss = [k for k, n in seen.items() if n == 0]
        st = "PASS" if not miss else "FAIL"
        print(f"  {band}: {(' '.join(f'{k}={n}' for k,n in seen.items()) if seen else 'no colors')}")
        if miss:
            ok = False
        results[band] = (not miss)

manifest = os.path.join(BASE, "bar_proportionality_qa.json")
json.dump({"pass": ok, "results": results}, open(manifest, "w"), indent=2)
print("\nOVERALL BAR-QA:", "PASS" if ok else "FAIL", "->", manifest)
sys.exit(0 if ok else 1)