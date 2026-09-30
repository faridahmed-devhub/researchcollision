import os, sys, re
import pymupdf

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(BASE, "research_paper.pdf")

# --- scan all xref objects for the literal font-name strings
data = open(PDF, "rb").read()
for name in (b"Symbol", b"ArialUnicode", b"ZapfDingbats", b"Courier", b"Times-Roman", b"Helvetica"):
    print(name.decode(), "occurrences in binary:", data.count(name))

print("\n=== which xrefs reference these names ===")
doc = pymupdf.open(PDF)
for x in range(1, doc.xref_length()):
    obj = doc.xref_object(x)
    if any(k in obj for k in ("/Font", "/BaseFont", "/ToUnicode", "/FontFile")):
        for name in ("Symbol", "ArialUnicode", "Zapf", "Helvetica", "Courier", "Times"):
            if name in obj:
                print(f"  xref {x}: {obj.strip()[:160].replace(chr(10),' ')}")
                break

print("\n=== CambriaMath '∈' glyph location & all non-latin presence ===")
for p in range(doc.page_count):
    d = doc[p].get_text("rawdict")
    for blk in d["blocks"]:
        for line in blk.get("lines", []):
            for span in line.get("spans", []):
                for ch in span["chars"]:
                    c = ch["c"]
                    if ord(c) > 0x7F:
                        print(f"  page {p+1}: U+{ord(c):04X} {c!r} font={span['font']} at {tuple(round(v) for v in ch['bbox'])}")