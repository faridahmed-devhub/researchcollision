import os, re, json, pymupdf

BASE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(BASE, "research_paper.pdf")
doc = pymupdf.open(PDF)
texts = [doc[i].get_text() for i in range(doc.page_count)]
n = doc.page_count

print(f"pages={n}")
print("=== TOC (page 1) rows with claimed page numbers ===")
toc_text = texts[0]
rows = re.findall(r"([0-9][^\n]*?)\s+(\d+)", toc_text)
seen = []
for label, pg in rows:
    pg = int(pg)
    # find the actual page containing this label (body occurrence, page>=2)
    actual = None
    for p in range(1, n):
        if label.strip() in texts[p]:
            actual = p + 1
            break
    if actual is None:
        # try with case-insensitive or segment
        for p in range(1, n):
            if label.split("(")[0].strip().split()[0] in texts[p]:
                actual = p + 1
                break
    ok = (actual == pg)
    seen.append((label, pg, actual, ok))
    print(f"{'OK ' if ok else 'MISS'} '{label[:50]}' toc={pg} actual={actual}")

bad = [s for s in seen if not s[3]]
print("\nTOC mismatches:", len(bad))

print("\n=== footer check ===")
foot_fail = []
for i in range(n):
    if not re.search(rf"Page {i+1} of {n}", texts[i]):
        foot_fail.append(i + 1)
print("pages missing footer:", foot_fail)

print("\n=== figures ===")
for label in ["Evidence surface distribution", "Evidence records per system",
              "Cases with evidence per system"]:
    hits = [i + 1 for i, t in enumerate(texts) if label in t]
    print(label, "on pages", hits)

print("\n=== tables ===")
for t in ["Table A", "Table B", "Table C", "Table D",
          "causal_inference_x_clinical_ml", "FULL MATRIX", "FAIL"]:
    hits = [i + 1 for i, x in enumerate(texts) if t in x]
    print(t, "on pages", hits[:12])

print("\n=== blank pages ===")
print([i + 1 for i, t in enumerate(texts) if not t.strip()])

print("\n=== content bbox vs A4 margins (should stay within 18mm=51pt left/right, 20mm=56.7pt top/bottom) ===")
L, R, T, B = 51, 595.28 - 51, 56.7, 841.89 - 56.7
viol = []
for i in range(n):
    for b in doc[i].get_text("blocks"):
        x0, y0, x1, y1 = b[:4]
        if x0 < L - 10 or x1 > R + 10 or y0 < T - 20 or y1 > B + 20:
            # footer is intentionally in bottom margin (y ~825-830)
            if y1 > 821.5 and y0 < 838:
                continue
            viol.append((i + 1, round(x0), round(y0), round(x1), round(y1), b[4][:40].replace("\n", " ")))
print("margin violations (excluding footer):", len(viol))
for v in viol[:15]:
    print(v)

print("\n=== page size ===")
print([(round(doc[i].rect.width, 1), round(doc[i].rect.height, 1)) for i in (0, n // 2, n - 1)])