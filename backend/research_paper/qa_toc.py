import os, re, json, pymupdf

BASE = os.path.dirname(os.path.abspath(__file__))
doc = pymupdf.open(os.path.join(BASE, "research_paper.pdf"))
texts = [doc[i].get_text() for i in range(doc.page_count)]
n = doc.page_count

# --- parse TOC from the HTML (source of truth for baked numbers) ---
html = open(os.path.join(BASE, "research_paper.html"), encoding="utf-8").read()
toc_block = re.search(r'<nav id="toc">(.*?)</nav>', html, re.S).group(1)
rows = re.findall(r'<li class="trow">.*?<span class="tlab">(.*?)</span>.*?<span class="num">(\d*)</span>', toc_block, re.S)
toc_claims = [(re.sub(r"<[^>]+>", "", r[0]), int(r[1]) if r[1] else None) for r in rows]
print("TOC rows in HTML:", len(toc_claims))
seen = {}
for label, pg in toc_claims:
    seen.setdefault(label, []).append(pg)
dups = {k: v for k, v in seen.items() if len(v) > 1}
print("duplicate TOC labels:", dups)

# --- resolve each label to its actual page in the final PDF body ---
ok, bad = [], []
for label, claimed in toc_claims:
    actual = None
    for p in range(1, n):  # skip title/TOC page
        # require a standalone heading hit (line start) to avoid TOC-page collision
        for line in texts[p].splitlines():
            if line.strip() == label or line.strip().startswith(label + " "):
                actual = p + 1
                break
        if actual:
            break
    if claimed is None or actual is None or claimed != actual:
        bad.append((label, claimed, actual))
    else:
        ok.append((label, claimed))

print("\n=== TOC page-number accuracy ===")
print(f"matched {len(ok)}/{len(toc_claims)}")
for b in bad:
    print("MISMATCH:", b)

# --- single-instance check for top-level section headings ---
print("\n=== heading duplication check ===")
for h in ["References", "Appendix A — Full 12×4 evidence matrix",
          "Verification Matrix (one-line audit summary)",
          "Appendix B: Pipeline Failures (verbatim)"]:
    pages = []
    for p in range(n):
        for line in texts[p].splitlines():
            if line.strip() == h:
                pages.append(p + 1)
                break
    print(f"'{h}' on pages {pages}")

# --- figures present on pages ---
print("\n=== figures ===")
for label in ["Evidence surface distribution", "Evidence records per system",
              "Cases with evidence per system"]:
    print(label, [i + 1 for i, t in enumerate(texts) if label in t])

# --- appendix matrix \u4e0e supplemental block presence ---
full = "\n".join(texts)
print("\n=== appendix content ===")
print("full matrix cells (FAIL) present:", "FAIL" in full)
print("table_a header 'Case' + 'keyword' present:", ("Case" in full and "keyword" in full))
print("\n=== footer + blank ===")
print("footers complete:", all(re.search(rf"Page {i+1} of {n}", texts[i]) for i in range(n)))
print("blank pages:", [i + 1 for i, t in enumerate(texts) if not t.strip()])

print("\n=== total pages:", n)