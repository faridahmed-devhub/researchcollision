import pymupdf, sys, re
sys.stdout.reconfigure(encoding="utf-8")
BASE = r"E:\AICode\opencode\ResearchCollision\backend\research_paper"
doc = pymupdf.open(BASE + r"\research_paper.pdf")

p0 = doc[0].get_text("rawdict")
texts_p0 = []
for blk in p0["blocks"]:
    for line in blk.get("lines", []):
        for span in line.get("spans", []):
            t = "".join(c["c"] for c in span["chars"])
            if t.strip():
                texts_p0.append((t.strip(), tuple(round(x, 1) for x in span["bbox"]), span["font"], round(span["size"], 1)))

print("=== page 1 spans (first 60) ===")
for t, b, f, s in texts_p0[:60]:
    print(f"  {t[:45]:46s} bbox={b} f={f} {s}pt")

# find the pair of a TOC label and its number
print("\n=== TOC label/number alignment check ===")
labels = ["Abstract", "1. Introduction", "2. Related Work", "3. Methodology"]
for lbl in labels:
    lblsp = [x for x in texts_p0 if x[0] == lbl or x[0].startswith(lbl)]
    if not lblsp:
        continue
    bx = lblsp[0][1]
    # find a lone number span within the same x range below
    nums = [x for x in texts_p0 if re.fullmatch(r"\d{1,2}", x[0])]
    same_line = [x for x in nums if abs(x[1][1] - bx[1]) < 4 and bx[2] - x[1][0] > -10]
    print(f"  {lbl}: span bbox={bx}  numbers on same baseline (dy<4): {same_line}")