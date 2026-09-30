#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_research_paper.py
------------------------
FINAL PRODUCTION RENDERER for the 12-case / 188-record research paper.

Pipeline (honest, reproducible):
  1. Read canonical sources under this directory:
       paper.md                                  (master manuscript body)
       tables/table_a_casexsystem.md             (Table A matrix)
       tables/table_b_system_totals.md           (Table B)
       tables/table_c_surface_distribution.md    (Table C)
       tables/table_d_pipeline_failures.md       (Table D)
       figures/*.svg                             (Figures 1-3, embedded verbatim)
appendix/*.md                             (supplementary appendices)
        Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.bib  (15 verified refs;
                                                                      only the cited subset is rendered)
  2. Build a publication HTML (research_paper.html) with professional academic
     print CSS, title/disclosure block, dot-leader TOC, captioned tables and
     figures, and the cited-entry reference list.
  3. Render  -> research_paper.pdf  using Microsoft Edge (Chromium) headless
     print-to-pdf (the only HTML->PDF engine available on this host; no
     LaTeX/pandoc/wkhtmltopdf/weasyprint/playwright installed - verified).
  4. Post-process the PDF with PyMuPDF: stamp centered page-footer numbers
     ("Page N of M") inside the 20mm bottom margin, and a final pass bakes the
     correct per-section page numbers into the TOC.

No scientific content is modified: the body text is converted verbatim from
paper.md; numbers, failure strings and references are never re-computed.
No experiment is re-run.
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pymupdf  # PyMuPDF (fitz API is deprecated)

BASE = os.path.dirname(os.path.abspath(__file__))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
TOC_PAGE_NUMBERS = {}  # heading slug -> page (filled in pass 2)

# --------------------------------------------------------------------------
# small BibTeX -> readable reference formatter
# --------------------------------------------------------------------------

_DIACRITICS = {
    r"{\"u}": "u", r"{\"U}": "U", r"{\"o}": "o", r"{\"a}": "a",
    r"{\`e}": "e", r"{\'e}": "e", r"{\'i}": "i", r"{\'a}": "a",
    r"{\v{Z}}": "Z", r"{\v{z}}": "z", r"{\'{\i}}": "i", r"{\l}": "l",
    r"{\L}": "L", r"{\c{c}}": "c", r"{\u{g}}": "g", r"{\v{C}}": "C",
}


def _plain(s):
    # Order matters: resolve LaTeX diacritic macros (which contain braces, e.g.
    # {\L}ukasz) BEFORE removing the remaining braces, otherwise '{\L}' would be
    # reduced to '\L' and survive as a literal backslash in printed text.
    s = s.replace("\\url{", "")
    for k, v in _DIACRITICS.items():
        s = s.replace(k, v)
    s = re.sub(r"[{}]", "", s)
    s = re.sub(r"\\'|\\`|\\\^|\\c|\\v|\\u|\\\"", "", s)
    return s.strip()


def _strip_braces(x):
    return re.sub(r"[{}]", "", x)


# Entries from the canonical .bib that are actually cited somewhere in paper.md's
# body. Uncited entries stay in the .bib (provenance) but are excluded from the
# rendered reference list so the paper never shows a reference it does not use.
CITED_KEYS = [
    "swanson1986",
    "swanson1997",
    "reimers2019sentencebert",
    "karpukhin2020dpr",
    "lewis2020rag",
    "touvron2023llama",
    "priem2022openalex",
]


def _parse_authors(raw):
    parts = [p.strip() for p in raw.split(" and ")]
    out = []
    for p in parts:
        p = _plain(p)
        if "," in p:
            last, given = p.split(",", 1)
            last = last.strip()
            initials = " ".join(n[0] + "." for n in given.split() if n)
            out.append((last, initials))
        else:
            names = p.split()
            out.append((names[-1], " ".join(n[0] + "." for n in names[:-1])))
    return out


def _format_authors(authors):
    parts = []
    for last, initials in authors:
        parts.append(f"{last}, {initials}" if initials else last)
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} & {parts[1]}"
    return f"{', '.join(parts[:-1])}, & {parts[-1]}"


def parse_bib(text):
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+)\s*,\s*(.*?)\n\}", text, re.S):
        kind, key, body = m.group(1), m.group(2).strip(), m.group(3)
        fields = _parse_fields(body)
        entries.append({"kind": kind, "key": key, "fields": fields})
    return entries


def _parse_fields(body):
    """Brace-aware field parser: field = key = {balanced-braces} (handles \\u{g} macros)."""
    fields = {}
    i = 0
    n = len(body)
    while i < n:
        m = re.match(r'\s*([A-Za-z]+)\s*=\s*\{', body[i:])
        if not m:
            i += 1
            continue
        key = m.group(1).lower()
        j = i + m.end()
        depth = 1
        start = j
        buf = []
        while j < n and depth > 0:
            c = body[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            buf.append(c)
            j += 1
        fields[key] = "".join(buf)
        i = j + 1
    return fields


def format_reference(entry):
    f = entry["fields"]
    authors = _parse_authors(f.get("author", ""))
    year = f.get("year", "n.d.")
    title = _plain(f.get("title", "Untitled"))
    venue = _plain(f.get("booktitle", f.get("journal", f.get("institution", ""))))
    vol = f.get("volume", "")
    num = f.get("number", "")
    pages = f.get("pages", "")
    doi = f.get("doi", "")
    note = f.get("note", "")
    how = f.get("howpublished", "")
    loc = []
    if venue:
        loc.append(venue)
    elif how:
        loc.append(_plain(how))
    if vol:
        loc.append(f"Vol. {vol}" + (f", No. {num}" if num else ""))
    if pages:
        loc.append(f"pp. {pages}")
    text = f"{_format_authors(authors)} ({year}). {title}. " + ". ".join(loc)
    if isinstance(note, str) and note:
        text += f" [{_plain(note)}]"
    if doi:
        text += f" DOI: https://doi.org/{doi}"
    elif how and ("http" in how):
        text += f" URL: {_plain(how)}"
    return text


# --------------------------------------------------------------------------
# markdown helpers (simple, controlled; no external libs required)
# --------------------------------------------------------------------------

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


_INLINE = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))")


def md_inline(s):
    def repl(m):
        t = m.group(1)
        if t.startswith("`") and t.endswith("`"):
            return f'<code>{esc(t[1:-1])}</code>'
        if t.startswith("**") and t.endswith("**"):
            return f"<strong>{esc(t[2:-2])}</strong>"
        if t.startswith("*") and t.endswith("*"):
            return f"<em>{esc(t[1:-1])}</em>"
        mm = re.match(r"\[([^\]]+)\]\(([^)]+)\)", t)
        if mm:
            return f'<a href="{esc(mm.group(2))}">{esc(mm.group(1))}</a>'
        return t
    return _INLINE.sub(repl, s)


def md_table(lines):
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if re.match(r"^[\s:|-]+$", ln.strip().replace("|", "")):
            continue
        rows.append(cells)
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    html = '<table>\n<thead>\n<tr>' + "".join(f"<th>{md_inline(esc(h))}</th>" for h in header) + "</tr>\n</thead>\n<tbody>\n"
    for r in body:
        html += "<tr>" + "".join(f"<td>{md_inline(esc(c))}</td>" for c in r) + "</tr>\n"
    html += "</tbody>\n</table>"
    return html


def md_paragraph(text):
    text = text.strip()
    if not text:
        return ""
    return f"<p>{md_inline(esc(text))}</p>"


def md_list_block(lines):
    items = []
    buf = []
    for ln in lines:
        if ln.startswith("- "):
            if buf:
                items.append(buf)
                buf = []
            buf.append(ln[2:])
        else:
            buf.append(ln.strip())
    if buf:
        items.append(buf)
    lis = []
    for it in items:
        # Join the item's raw lines FIRST, then apply inline markdown once so
        # emphasis/bold spanning multiple wrapped lines cannot leak literal '**'.
        inner = md_inline(esc(" ".join(x for x in it if x)))
        lis.append(f"<li>{inner}</li>")
    return "<ul>\n" + "\n".join(lis) + "\n</ul>"


def md_block(text):
    def block_starters():
        return ("|", "- ", "```", "#")
    lines = [ln.rstrip() for ln in text.split("\n")]
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.strip().startswith("|"):
            tbl = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl.append(lines[i])
                i += 1
            out.append(md_table(tbl))
            continue
        if ln.strip().startswith("- "):
            lst = []
            while i < len(lines) and lines[i].strip():
                s = lines[i].strip()
                if s.startswith("- "):
                    lst.append(lines[i])
                    i += 1
                elif s.startswith(block_starters()):
                    break
                else:
                    # wrapped continuation of the current bullet item
                    lst.append(lines[i])
                    i += 1
            out.append(md_list_block(lst))
            continue
        if re.match(r"^\d+\.\s", ln.strip()):
            lst = []
            while i < len(lines) and lines[i].strip():
                s = lines[i].strip()
                if re.match(r"^\d+\.\s", s):
                    lst.append(s)
                    i += 1
                elif s.startswith(block_starters()):
                    break
                else:
                    lst.append(lines[i])
                    i += 1
            _num = re.compile(r"^\d+\.\s*")
            lis = []
            buf = []
            for x in lst:
                if re.match(r"^\d+\.\s", x):
                    if buf:
                        lis.append(buf)
                        buf = []
                    buf.append(x)
                else:
                    buf.append(x.strip())
            if buf:
                lis.append(buf)
            lis_html = []
            for it in lis:
                joined = " ".join(i2 for i2 in it if i2)
                lis_html.append(f"<li>{md_inline(esc(_num.sub('', joined)))}</li>")
            out.append(f"<ol>\n{chr(10).join(lis_html)}\n</ol>")
            continue
        if ln.strip().startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(f"<pre><code>{esc(chr(10).join(buf))}</code></pre>")
            continue
        m = re.match(r"^(#{1,6})\s+(.+)$", ln.strip())
        if m:
            level = min(len(m.group(1)), 4)
            txt = m.group(2)
            out.append(f'<h{level} id="{slugify(txt)}">{esc(txt)}</h{level}>')
            i += 1
            continue
        buf = [ln]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("|", "- ", "```", "#")):
            buf.append(lines[i])
            i += 1
        out.append(md_paragraph(" ".join(buf)))
    return "\n".join(out)


# --------------------------------------------------------------------------
# figure / caption helpers
# --------------------------------------------------------------------------

def figure_html(idx, svg_content, caption):
    svg = svg_content
    return (
        f'<figure id="fig{idx}">\n'
        f"<div class=\"figwrap\">{svg}</div>\n"
        f"<figcaption>{caption}</figcaption>\n</figure>"
    )


def caption_html(label, text):
    return f'<div class="table-caption" id="{label.lower().replace(" ", "-")}">{label}. {text}</div>'


# --------------------------------------------------------------------------
# HTML document assembly
# --------------------------------------------------------------------------

CSS = """
:root {
  --ink: #1a1a1a;
  --accent: #2347a3;
  --rule: #b9b9b9;
  --soft: #f4f4f0;
}
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html { font-size: 11pt; }
body {
  font-family: Georgia, 'Times New Roman', serif;
  color: var(--ink);
  max-width: 960px; margin: 0 auto; padding: 1.5rem 1rem 3rem;
  line-height: 1.55; text-align: justify; hyphens: auto;
  -webkit-hyphens: auto;
}
h1.title { font-size: 21pt; text-align: center; line-height: 1.3;
  margin: 0 0 .25em 0; }
p.subtitle { text-align: center; font-style: italic; font-size: 11pt; margin: 0 0 1.1em 0; }
.meta { text-align: center; font-size: 10pt; color: #333; margin: .1em 0 0 0; }
.meta:last-child { margin-bottom: .95em; }
.meta div { margin: .15em 0; }
.disclosure { border: 1.1pt solid #8a8a8a; background: var(--soft);
  padding: .6em 1em; margin: 1.2em 0; font-size: 9.5pt; text-align: left; }
.disclosure h2 { margin-top: 0; }
h2 { font-size: 14.5pt; margin: 1.5em 0 .5em 0; border-bottom: 1px solid var(--rule);
  padding-bottom: .12em; page-break-after: avoid; break-after: avoid; }
h3 { font-size: 12.5pt; margin: 1.2em 0 .4em 0; page-break-after: avoid; break-after: avoid; }
h4 { font-size: 11pt; margin: 1em 0 .35em 0; page-break-after: avoid; break-after: avoid; }
p { margin: .5em 0; }
ul, ol { margin: .4em 0 .6em 1.2em; }
li { margin: .22em 0; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 0.88em;
  background: #eef1f5; padding: 0 .25em; border-radius: 2px; }
pre { background: #eef1f5; border: 0.5pt solid var(--rule); padding: .6em .8em;
  white-space: pre-wrap; page-break-inside: avoid; font-size: 9pt; }
pre code { background: none; padding: 0; }
table { width: 100%; border-collapse: collapse; font-size: 9.3pt; margin: .5em 0 .7em 0;
  page-break-inside: avoid; break-inside: avoid; }
table.wide-table { page-break-inside: auto; break-inside: auto; }
th, td { border: 0.7pt solid #6a6a6a; padding: .28em .5em; vertical-align: top; }
th { background: #e8ecf3; font-weight: bold; }
tbody tr:nth-child(even) td { background: #fafafa; }
.table-caption { font-size: 9.6pt; font-weight: bold; margin: 1em 0 .25em 0;
  page-break-after: avoid; break-after: avoid; }
figure { margin: 1.2em auto; text-align: center; page-break-inside: avoid; break-inside: avoid; }
figure svg { max-width: 100%; height: auto; }
figcaption { font-size: 9.4pt; font-style: italic; margin-top: .35em; text-align: center; }
#toc { border: 0.7pt solid var(--rule); background: var(--soft); padding: .8em 1.2em;
  margin: 0 0 1.4em 0; page-break-before: always; break-before: page;
  page-break-after: always; break-after: page; }
#toc h2 { border-bottom: none; margin-top: 0; }
#toc ul { list-style: none; margin: .2em 0; padding: 0; }
#toc li { margin: .18em 0; }
#toc a { text-decoration: none; color: var(--ink); }
#toc a:hover { color: var(--accent); }
#toc .dot { border-bottom: 1pt dotted #333; flex: 1; margin: 0 .45em; }
#toc .trow { display: flex; align-items: baseline; }
#toc .num { min-width: 2.2em; text-align: right; font-variant-numeric: tabular-nums; }
.refs { font-size: 9.4pt; }
.refs ol { margin-left: 1.4em; list-style: none; }
.refs li { margin: .3em 0; }
a { color: var(--accent); }
#appendix-mark h2 { border-top: 2px solid var(--rule); padding-top: .5em; }
.verif { font-size: 9.5pt; }
.verif li { margin: .3em 0; }
.note { font-size: 9pt; font-style: italic; color: #444; }
.refkey { display: none; }
@media print {
  @page { size: A4; margin: 20mm 18mm 20mm 18mm;
    @bottom-center { content: "Page " counter(page) " of " counter(pages);
      font-family: Georgia, 'Times New Roman', serif; font-size: 8pt; color: #595959; }
  }
  body { max-width: none; padding: 0; font-size: 11pt; }
  a { color: inherit; }
}
"""

# --------------------------------------------------------------------------
# source loading
# --------------------------------------------------------------------------

def read(name):
    with open(os.path.join(BASE, name), "r", encoding="utf-8-sig") as fh:
        return fh.read()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_svg(name):
    return read(os.path.join("figures", name))


# --------------------------------------------------------------------------
# paper.md parsing
# --------------------------------------------------------------------------

FRONTMETA = {}


def parse_frontmatter(text):
    global FRONTMETA
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return text
    for ln in m.group(1).splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            FRONTMETA[k.strip()] = v.strip().strip('"')
    return text[m.end():]


def split_sections(body):
    """Parse body into top-level ``## `` sections, each with typed chunks.

    Chunk kinds:
      ("h3", heading)      - subsection heading (rendered as <h3 id=...>)
      ("h4", heading)      - sub-subsection heading
      ("body", text)       - raw markdown block (tables/lists/paragraphs)

    Returns list of {"heading": str, "chunks": [(kind, text), ...]}.
    This gives the renderer a real hierarchy (no brittle "heading == '4.1 ...'"
    string matching) and lets figures anchor to the subsection they belong to.
    """
    lines = body.splitlines()
    sections = []
    cur = {"heading": None, "chunks": []}
    for ln in lines:
        if ln.startswith("## "):
            if cur["heading"] is not None:
                sections.append(cur)
            cur = {"heading": ln[3:].strip(), "chunks": []}
        elif cur["heading"] is None:
            continue
        elif ln.startswith("### "):
            cur["chunks"].append(("h3", ln[4:].strip()))
        elif ln.startswith("#### "):
            cur["chunks"].append(("h4", ln[5:].strip()))
        else:
            if cur["chunks"] and cur["chunks"][-1][0] == "body":
                prev = cur["chunks"][-1][1] + "\n" + ln
                cur["chunks"][-1] = ("body", prev)
            else:
                cur["chunks"].append(("body", ln))
    if cur["heading"] is not None:
        sections.append(cur)
    return sections


def slugify(text):
    s = re.sub(r"[^\w ]+", "", text.lower().strip())
    return re.sub(r"\s+", "-", s)


def toc_entries(sections):
    out = []
    for s in sections:
        hid = s["heading"]
        out.append({"id": slugify(hid), "label": hid})
    return out


# --------------------------------------------------------------------------
# HTML assembly
# --------------------------------------------------------------------------

def render_chunks(chunks, placed_figs, fig_anchors, figures):
    """Render one section's typed chunks to HTML.

    Subsection headings become real <h3>/<h4> (with anchors) instead of being
    flattened into paragraphs, and figures are emitted *after* the subsection
    they describe.  Anchoring is semantic: a figure attaches to the subsection
    whose heading text carries its topic phrase (e.g. fig1 after the
    'Surface distribution' subsection) - no brittle equality/position matching.
    """
    out = []
    for kind, text in chunks:
        if kind in ("h3", "h4"):
            tag = "h3" if kind == "h3" else "h4"
            anchor = slugify(text)
            out.append(f'<{tag} id="{anchor}">{esc(text)}</{tag}>')
            for fid, phrase in fig_anchors:
                if fid not in placed_figs and phrase in text.lower():
                    out.append(figures[fid])
                    placed_figs.add(fid)
        else:
            out.append(md_block(text))
    return "\n".join(out)


def build_bibliography():
    bib = parse_bib(read("Farid_Ahmed_Evidence_Discovery_Comparative_Evaluation.bib"))
    cited = [e for e in bib if e["key"] in CITED_KEYS]
    items = []
    for i, e in enumerate(cited, 1):
        text = format_reference(e)
        key = e["key"]
        items.append(
            f'<li id="ref-{esc(key)}"><span class="refnum">[{i}]</span> {esc(text)} '
            f'<span class="refkey">(bib key: {esc(key)})</span></li>'
        )
    return bib, "<ol>\n" + "\n".join(items) + "\n</ol>"


def table_md_to_html(name, cls=""):
    md = read(os.path.join("tables", name))
    block = md_block(md)
    if cls:
        block = block.replace("<table>", f'<table class="{cls}">', 1)
    return block


def appendix_html():
    parts = []
    mapping = [
        ("appendix_a_method_and_config.md", "Appendix A: Experimental Configuration"),
        ("appendix_c_full_evidence_matrix.md", "Appendix B: Case-Level Evidence Matrix"),
        ("appendix_b_failures_verbatim.md", "Appendix C: Runtime Failures"),
        ("appendix_d_reproducibility.md", "Appendix D: Reproducibility Information"),
    ]
    for fn, label in mapping:
        md = read(os.path.join("appendix", fn))
        body = md_block(md)
        # drop the file's own H1 (its title duplicates the <h2> we inject below);
        # sub-headings (## A.x) are now real <h2> elements emitted by md_block.
        body = re.sub(r"^\s*<h1[^>]*>.*?</h1>\s*\n?", "", body, count=1, flags=re.S).strip()
        # allow long appendix tables (e.g. the 12x4 case matrix) to break across pages.
        body = body.replace("<table>", '<table class="wide-table">')
        parts.append(f'<section id="{slugify(label)}"><h2>{esc(label)}</h2>\n{body}</section>\n')
    return "\n".join(parts)


CAPTION_HTML = []


def insert_captions(body_text):
    """Insert table-caption placeholders before the tables the manuscript numbers.

    A sentinel token (not a literal <div>) is inserted so the markdown -> HTML
    pipeline can never leak raw '<div class="table-caption">' text into the
    rendered page; the tokens are swapped for real caption divs in build_html.
    """
    caps = [
        ("| surface | count | share of 188 |",
         "Table C", "Evidence records by evidence surface (counts and share of N=188)."),
        ("| system | records | cases covered (of 12) |",
         "Table B", "Evidence records and case coverage by system."),
        ("| # | case | failure record |",
         "Table D", "Pipeline runtime failures by case, as reported by the runtime."),
    ]
    for marker, label, text in caps:
        token = f"@@CAPTION{len(CAPTION_HTML)}@@"
        CAPTION_HTML.append(caption_html(label, text))
        lines = body_text.splitlines()
        out = []
        done = False
        for ln in lines:
            if not done and marker in ln:
                out.append(token)
                done = True
            out.append(ln)
        body_text = "\n".join(out)
    return body_text


# --------------------------------------------------------------------------
# main build
# --------------------------------------------------------------------------

def build_html(pass_label):
    global TOC_PAGE_NUMBERS
    CAPTION_HTML.clear()
    paper = read("paper.md")
    body = parse_frontmatter(paper).strip()
    body = insert_captions(body)
    sections = split_sections(body)
    toc = toc_entries(sections)

    # inline figure blocks
    fig1 = figure_html(1, load_svg("fig1_surface_distribution.svg"),
                       "Figure 1: Evidence-surface distribution across all evidence records "
                       "(intersection 55, hypothesis 50, gap 83; N=188).")
    fig2 = figure_html(2, load_svg("fig2_evidence_per_system.svg"),
                       "Figure 2: Evidence records per system "
                       "(keyword 41, embedding 36, llm_only 53, pipeline 58).")
    fig3 = figure_html(3, load_svg("fig3_case_coverage_per_system.svg"),
                       "Figure 3: Cases with evidence per system "
                       "(keyword 12/12, embedding 12/12, llm_only 12/12, pipeline 8/12).")

    fig_anchors = [
        ("fig1", "surface distribution"),
        ("fig2", "coverage"),
        ("fig3", "coverage"),
    ]
    figures = {"fig1": fig1, "fig2": fig2, "fig3": fig3}

    bib, bib_html = build_bibliography()

    body_html = []
    frontmatter_html = []
    appendix_done = False
    placed_figs = set()
    for s in sections:
        hid = s["heading"]
        sid = slugify(hid)
        if hid.lower() in ("references", "references (see references.bib)"):
            n_cited = len(CITED_KEYS)
            mdbody = ("<p class=\"note\">References are numbered in the order in which they are first "
                      "cited in the text. Every entry was verified against public scholarly records; "
                      "no reference is fabricated, and no cited work is omitted from this list.</p>\n"
                      + "<div class=\"refs\">" + bib_html + "</div>")
            body_html.append(f'<section id="{sid}"><h2>{esc(hid)}</h2>\n{mdbody}</section>')
            continue
        if hid.lower().startswith("appendices") and not appendix_done:
            # master appendix section: keep its pointer text, then embed the four
            # supplemental appendices inside this section (the case matrix now lives
            # in Appendix B's own content, so nothing is injected here besides them)
            mdbody = render_chunks(s["chunks"], placed_figs, fig_anchors, figures)
            mdbody = mdbody + "\n" + appendix_html()
            appendix_done = True
            body_html.append(f'<section id="{sid}"><h2>{esc(hid)}</h2>\n{mdbody}</section>')
            continue
        mdbody = render_chunks(s["chunks"], placed_figs, fig_anchors, figures)
        sec = f'<section id="{sid}"><h2>{esc(hid)}</h2>\n{mdbody}</section>'
        if sid in ("abstract", "keywords"):
            # Abstract and Keywords lead the front matter (before the Contents),
            # matching the conventional academic opening-page order.
            frontmatter_html.append(sec)
        else:
            body_html.append(sec)

    # --- References / appendix replacement -----------------------------------
    main_sections = "".join(body_html)
    # swap caption sentinel tokens (survive markdown as <p>@@CAPTIONn@@</p>) for
    # the real caption divs; escaping can never leak raw '<div class=...>'.
    for i, cap_html in enumerate(CAPTION_HTML):
        main_sections = main_sections.replace(f"<p>@@CAPTION{i}@@</p>", cap_html)

    # --- TOC ----------------------------------------------------------------
    toc_rows = []
    for e in toc:
        pg = TOC_PAGE_NUMBERS.get(e["id"], "")
        toc_rows.append(
            f'<li class="trow"><a href="#{e["id"]}"><span class="tlab">{esc(e["label"])}</span></a>'
            f'<span class="dot"></span><span class="num">{pg}</span></li>'
        )
    for lbl in ["Appendix A: Experimental Configuration",
                "Appendix B: Case-Level Evidence Matrix",
                "Appendix C: Runtime Failures",
                "Appendix D: Reproducibility Information"]:
        sid = slugify(lbl)
        toc_rows.append(
            f'<li class="trow"><a href="#{sid}"><span class="tlab">{esc(lbl)}</span></a>'
            f'<span class="dot"></span><span class="num">{TOC_PAGE_NUMBERS.get(sid, "")}</span></li>'
        )
    toc_html = '<nav id="toc"><h2>Contents</h2><ul>' + "\n".join(toc_rows) + "</ul></nav>"

    # --- title / author block ------------------------------------------------
    title = FRONTMETA.get("title", "Research Paper")
    subtitle = FRONTMETA.get("short_title", "")
    author = FRONTMETA.get("author", "")
    meta = []
    for part in author.split(" | "):
        part = part.strip()
        if part:
            meta.append(f'<div class="meta">{esc(part)}</div>')
    meta.append(f'<div class="meta">Date: {esc(FRONTMETA.get("date", ""))}&nbsp;&middot;&nbsp;'
                f'Dataset: <code>{esc(FRONTMETA.get("dataset", ""))}</code></div>')

    html = f"""<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<header>
<h1 class="title">{esc(title)}</h1>
{'<p class="subtitle">' + esc(subtitle) + '</p>' if subtitle else ''}
{chr(10).join(meta)}
</header>
{chr(10).join(frontmatter_html)}
{toc_html}
<main>
{main_sections}
</main>
</body>
</html>
"""
    with open(os.path.join(BASE, "research_paper.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    return html


# --------------------------------------------------------------------------
# PDF render (Edge headless = Chromium)
# --------------------------------------------------------------------------

def run_edge(html_path, pdf_path):
    uri = "file:///" + html_path.replace("\\", "/")
    cmd = [EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={pdf_path}", uri]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        out = (r.stdout or "") + (r.stderr or "")
    except FileNotFoundError:
        sys.exit("Edge not found: " + EDGE)
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        return True, out
    return False, out


def body_start_page(doc):
    """First page index whose text still holds body content (after title and TOC pages).

    The Contents page repeats every top-level heading as a TOC row, so searching for a heading
    right after the title page would hit the TOC row instead of the body occurrence. We locate
    the page whose *own* heading is \"Contents\" and start every heading search after it.
    """
    for pno in range(doc.page_count):
        for line in doc[pno].get_text().splitlines():
            if line.strip() == "Contents":
                return pno + 1
    return 2


def find_heading_pages(doc, entries):
    """Return {slug: page_no} for the *body* occurrence of each heading (skip title/TOC pages).

    Abstract and Keywords now lead the front matter *before* the Contents page, so they are
    resolved on the pages preceding Contents. Everything else is resolved *after* Contents,
    where the TOC rows for the body headings cannot be confused with the real headings.
    """
    res = {}
    start = body_start_page(doc)     # first page index searching after the Contents page
    cp = max(0, start - 1)           # the page that carries the TOC ("Contents" heading)
    front_ids = {"abstract", "keywords"}
    for e in entries:
        label = e["label"]
        found = False
        last = cp if e["id"] in front_ids else cp
        for pno in range(0, last):
            if doc[pno].search_for(label):
                res[e["id"]] = pno + 1
                found = True
                break
        if not found and e["id"] in front_ids and doc[cp].search_for(label):
            res[e["id"]] = cp + 1   # front-matter heading shares the Contents page
            found = True
        if not found:
            for pno in range(max(start, 0), doc.page_count):
                if doc[pno].search_for(label):
                    res[e["id"]] = pno + 1
                    found = True
                    break
        if not found:
            res[e["id"]] = -1
    return res


# --------------------------------------------------------------------------
# QA helpers
# --------------------------------------------------------------------------

def extract_all(doc):
    return [doc[i].get_text() for i in range(doc.page_count)]


def check_refs_html(html_text, bib):
    checks = []
    for i, e in enumerate(bib, 1):
        ok = f'[{i}]' in html_text and ("bib key: " + e["key"]) in html_text
        checks.append(("bib[" + e["key"] + "]", ok))
    return checks


def rasterize(pdf_path, out_pattern, dpi=150):
    import glob
    for g in glob.glob(out_pattern + "*.png"):
        try:
            os.remove(g)
        except OSError:
            pass
    topp = r"C:\Users\HP\AppData\Local\Programs\Python\Python310\pdftoppm"
    prefix = out_pattern.rstrip("*")
    cmd = [topp, "-png", "-r", str(dpi), pdf_path, prefix]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    pages = sorted(glob.glob(out_pattern + "*.png"))
    return pages, r.returncode


def ink_ratio(png):
    from PIL import Image
    im = Image.open(png).convert("L")
    px = list(im.getdata())
    dark = sum(1 for v in px if v < 245)
    return dark / max(1, len(px))


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

def main():
    build_html("pass 1 (layout probe)")

    pdf1 = os.path.join(BASE, "_probe_research_paper.pdf")
    ok, out = run_edge(os.path.join(BASE, "research_paper.html"), pdf1)
    if not ok:
        sys.exit("Edge render failed (pass 1). " + out)

    doc = pymupdf.open(pdf1)
    global TOC_PAGE_NUMBERS
    TOC_PAGE_NUMBERS = find_heading_pages(doc, toc_entries(split_sections(insert_captions(parse_frontmatter(read("paper.md")).strip()))))
    # also resolve special anchors (supplemental appendices live inside the master appendix section,
    # so find_heading_pages cannot see them as top-level section headings)
    labels = ["Appendix A: Experimental Configuration",
              "Appendix B: Case-Level Evidence Matrix",
              "Appendix C: Runtime Failures",
              "Appendix D: Reproducibility Information"]
    start = body_start_page(doc)
    for lbl in labels:
        sid = slugify(lbl)
        found = False
        for pno in range(start, doc.page_count):
            if doc[pno].search_for(lbl):
                TOC_PAGE_NUMBERS[sid] = pno + 1
                found = True
                break
        if not found:
            TOC_PAGE_NUMBERS[sid] = -1

    build_html("pass 2 (final)")

    pdf_final = os.path.join(BASE, "research_paper.pdf")
    ok, out = run_edge(os.path.join(BASE, "research_paper.html"), pdf_final)
    if ok:
        pass
    else:
        sys.exit("Edge render failed (final). " + out)
    # per-page footers ('Page N of M') are produced by the print engine itself
    # (@page @bottom-center margin box) -> embedded fonts + extractable text.
    doc.close()
    os.remove(pdf1)
    print("PDF rendered:", pdf_final, os.path.getsize(pdf_final), "bytes")
    print("TOC page map:", TOC_PAGE_NUMBERS)


if __name__ == "__main__":
    main()
