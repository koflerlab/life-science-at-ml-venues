"""Render the manuscript and supplementary files from Markdown to Word for submission.

Handles the subset of Markdown these files use: headings, paragraphs, bullet and numbered lists, pipe tables,
**bold**, *italic*, `code`, ^superscript^ and fenced code blocks. In manuscript.md, a line TABLE1 to TABLE3 is
replaced by that table from tables.json (build_assets.py), and the figures are appended after their legends.

Usage: python manuscript/build_docx.py   -> manuscript/out/*.docx
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT  # noqa: F401  (kept for landscape tables if needed)
from docx.shared import Cm, Pt

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
ROOT = HERE.parent
TABLE_NAMES = {"table1": "Table 1", "table2": "Table 2", "table3": "Table 3", "table4": "Table 4",
               "tablea1": "Table A1"}  # captions themselves come from tables.json (build_assets.CAPTIONS)
INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\^[^^]+\^)")


def runs(par, text: str) -> None:
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**"):
            par.add_run(part[2:-2]).bold = True
        elif part.startswith("*") and len(part) > 2:
            par.add_run(part[1:-1]).italic = True
        elif part.startswith("`"):
            r = par.add_run(part[1:-1])
            r.font.name = "Courier New"
            r.font.size = Pt(10)
        elif part.startswith("^"):
            par.add_run(part[1:-1]).font.superscript = True
        else:
            par.add_run(part)


def add_table(doc, rows: list[list[str]], title: str | None = None, size: int = 9) -> None:
    if title:
        p = doc.add_paragraph()
        runs(p, f"**{title}**")
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            c = t.cell(i, j)
            c.text = ""
            p = c.paragraphs[0]
            runs(p, f"**{cell}**" if i == 0 and cell else cell)
            for r in p.runs:
                r.font.size = Pt(size)
    doc.add_paragraph()


def new_doc() -> Document:
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(12)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.5
    for s in doc.sections:
        s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.5)
    for lvl in (1, 2, 3):
        h = doc.styles[f"Heading {lvl}"]
        h.font.name = "Times New Roman"
        h.font.color.rgb = None
        h.font.size = Pt({1: 16, 2: 14, 3: 12}[lvl])
    return doc


def render(md: Path, out: Path, tables: dict | None = None, figures: dict | None = None) -> None:
    doc = new_doc()
    lines = md.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                p = doc.add_paragraph()
                r = p.add_run(lines[j])
                r.font.name, r.font.size = "Courier New", Pt(9)
                j += 1
            i = j + 1
            continue
        if line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.fullmatch(r"\|[\s:|-]+\|", lines[i]):
                    block.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            add_table(doc, block)
            continue
        m = re.match(r"(#{1,3}) (.*)", line)
        if m:
            doc.add_heading(m.group(2), level=len(m.group(1)) if i else 0).runs[0].font.name = "Times New Roman"
        elif tables is not None and line.strip().lower() in TABLE_NAMES:
            key = line.strip().lower()
            add_table(doc, tables[key], f"{TABLE_NAMES[key]}. {tables['captions'][key]}")
        elif re.match(r"\s*[*-] ", line):
            p = doc.add_paragraph(style="List Bullet")
            runs(p, re.sub(r"^\s*[*-] ", "", line))
        elif line.strip():
            p = doc.add_paragraph()
            runs(p, line)
            fm = re.match(r"\*\*Figure (\d)\.\*\*", line)
            if figures and fm and fm.group(1) in figures:
                doc.add_picture(str(figures[fm.group(1)]), width=Cm(16))
        i += 1
    doc.save(out)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    tables = json.loads((HERE / "tables.json").read_text(encoding="utf-8"))
    figs = {n: HERE / "figures" / f"fig{n}.png" for n in ("1", "2", "3", "4")}
    figs.update({n: HERE / "figures" / f"{f}.png" for n, f in (("5", "fig_topics_venue"), ("6", "fig_topics_map"),
                                                               ("7", "fig_axes"))})
    render(HERE / "manuscript.md", OUT / "manuscript.docx", tables, figs)
    render(HERE / "supplementary" / "S2_PRISMA_2020_checklist.md", OUT / "S2_PRISMA_2020_checklist.docx")
    # S1: the frozen protocols (7 for the medical label, 9 for this study, with all notes).
    s1 = HERE / "out" / "_S1.md"
    protocol = (ROOT / "verdict_audit" / "readiness" / "PROTOCOL.md").read_text(encoding="utf-8")
    s1.write_text("# Supplementary File S1. Frozen protocols\n\nVerbatim copy of verdict_audit/readiness/PROTOCOL.md "
                  "(Protocols 7, 8 and 9 with all amendments and notes) from the repository. "
                  "Commit history of every freeze and note: "
                  "https://github.com/kondratevakate/icml-2026-repro (commits 3b9e5ea, 839281e and later).\n\n"
                  + protocol.replace("\n# ", "\n## "), encoding="utf-8")
    render(s1, OUT / "S1_protocols.docx", tables)
    s1.unlink()
    print("written:", ", ".join(p.name for p in sorted(OUT.glob("*.docx"))))


if __name__ == "__main__":
    main()
