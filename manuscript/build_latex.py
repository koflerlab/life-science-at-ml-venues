"""Render manuscript.md and tables.json to a LaTeX project for Overleaf.

Same source as build_docx.py, so the Word and LaTeX versions cannot drift apart: edit manuscript.md, then rebuild
both. Numeric citations [n] become \\cite{rn}; bracketed placeholders such as [EMAIL] are kept and shown in red so
co-authors see what is still missing. Each table and figure is placed right after the paragraph that first cites
it; figures are the vector PDFs written by build_assets.py.

Usage: python manuscript/build_latex.py   -> manuscript/latex/ (main.tex, figures/), manuscript/out/overleaf.zip
"""
from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEX = HERE / "latex"
ZIP = HERE / "out" / "overleaf.zip"
INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\^[^^]+\^|https?://[^\s)]+[^\s).,;]|\[[^\]]+\])")
CITED = re.compile(r"(?<!Supplementary )\b(Table|Figure) (\d)\b")
SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{",
           "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[a4paper,margin=2.5cm]{geometry}
\usepackage{setspace}
\usepackage{graphicx}
\usepackage{array}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{lineno}
\usepackage[hidelinks]{hyperref}
\usepackage{xurl}
\DeclareUnicodeCharacter{2212}{\ensuremath{-}}
\newcommand{\todo}[1]{\textcolor{red}{#1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\renewcommand{\tabularxcolumn}[1]{>{\raggedright\arraybackslash}p{#1}}
\setlength{\tabcolsep}{4pt}
\onehalfspacing
\linenumbers
"""
# First column (X) takes the remaining width; the others are fixed so numbers never overflow.
COLS = {"table1": "L{1.75cm}L{1.75cm}L{3.55cm}L{1.75cm}",
        "table2": "L{3.6cm}",
        "table3": "L{0.7cm}L{1.6cm}L{1.6cm}L{1.0cm}L{2.4cm}",
        "table4": "L{3.55cm}L{3.55cm}L{3.9cm}",
        "tablea1": "L{4.2cm}L{4.2cm}"}
NUMBER = {"table1": "1", "table2": "2", "table3": "3", "table4": "4", "tablea1": "A1"}  # captions: tables.json


def esc(s: str) -> str:
    return "".join(SPECIAL.get(c, c) for c in s)


def inline(text: str) -> str:
    out = []
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**"):
            out.append(r"\textbf{" + inline(part[2:-2]) + "}")
        elif part.startswith("*") and len(part) > 2:
            out.append(r"\textit{" + inline(part[1:-1]) + "}")
        elif part.startswith("`"):
            out.append(r"\texttt{" + esc(part[1:-1]) + "}")
        elif part.startswith("^"):
            out.append(r"\textsuperscript{" + esc(part[1:-1]) + "}")
        elif part.startswith("http"):
            out.append(r"\url{" + part.replace("%", r"\%").replace("#", r"\#") + "}")
        elif part.startswith("["):
            inner = part[1:-1]
            if re.fullmatch(r"\d+(\s*,\s*\d+)*", inner):
                out.append(r"~\cite{" + ",".join("r" + n.strip() for n in inner.split(",")) + "}")
            elif inner in ("Internet", "Preprint", "dataset"):
                out.append(esc(part))
            else:
                out.append(r"\todo{" + esc(part) + "}")
        else:
            out.append(esc(part))
    return "".join(out).replace(" ~\\cite", "~\\cite")


def table(key: str, rows: list[list[str]], caption: str) -> str:
    head = " & ".join(r"\textbf{" + esc(c) + "}" for c in rows[0]) + r" \\ \midrule"
    body = [" & ".join(esc(c) for c in r) + r" \\" for r in rows[1:]]
    # Floats are placed where first cited, so LaTeX's own counter would number them by position; fix it.
    return "\n".join([r"\begin{table}[htbp]", r"\centering\footnotesize",
                      r"\renewcommand{\thetable}{" + NUMBER[key] + "}",
                      r"\caption{" + esc(caption) + r"}\label{tab:" + key + "}",
                      r"\begin{tabularx}{\textwidth}{X" + COLS[key] + "}", r"\toprule", head, *body,
                      r"\bottomrule", r"\end{tabularx}", r"\end{table}", ""])


# Post hoc figures keep their descriptive file names.
FIG_FILE = {"5": "fig_topics_venue", "6": "fig_topics_map", "7": "fig_axes"}


def figure(n: str, caption: str) -> str:
    return "\n".join([r"\begin{figure}[htbp]", r"\centering", r"\setcounter{figure}{" + str(int(n) - 1) + "}",
                      r"\includegraphics[width=\textwidth]{figures/" + FIG_FILE.get(n, "fig" + n) + ".pdf}",
                      r"\caption{" + caption + r"}\label{fig:" + n + "}", r"\end{figure}", ""])


def main() -> None:
    lines = (HERE / "manuscript.md").read_text(encoding="utf-8").splitlines()
    tables = json.loads((HERE / "tables.json").read_text(encoding="utf-8"))
    legends = {m.group(1): inline(m.group(2)) for m in
               (re.match(r"\*\*Figure (\d)\.\*\* (.*)", ln) for ln in lines) if m}
    caps = tables["captions"]
    floats = {("Table", NUMBER[k]): table(k, tables[k], caps[k]) for k in NUMBER if k != "tablea1"}
    floats.update({("Figure", n): figure(n, c) for n, c in legends.items()})
    placed: set = set()
    items: list[str] = []

    def flush_items() -> None:
        if items:
            doc.append("\\begin{itemize}\n" + "\n".join("\\item " + t for t in items) + "\n\\end{itemize}\n")
            items.clear()

    def bibliography() -> list[str]:
        return ["\\begin{thebibliography}{99}", *[f"\\bibitem{{r{n}}} {t}" for n, t in refs],
                "\\end{thebibliography}"]

    title = lines[0].lstrip("# ").strip()
    head, i = [], 1
    while not lines[i].startswith("## "):
        if lines[i].strip():
            head.append(inline(lines[i]))
        i += 1
    doc = [PREAMBLE, "\\title{" + esc(title) + "}", "\\author{" + head[0] + "}", "\\date{}",
           "\\begin{document}", "\\maketitle", "\\begin{flushleft}\\small", r" \\ ".join(head[1:]),
           "\\end{flushleft}"]
    section, refs, bib_done = None, [], False
    for line in lines[i:]:
        if not re.match(r"\s*[*-] ", line):
            flush_items()
        m = re.match(r"(#{2,3}) (.*)", line)
        if m:
            section = m.group(2)
            if section.startswith("Appendix") and not bib_done:
                doc += [floats[k] for k in sorted(floats) if k not in placed]  # anything never cited
                placed.update(floats)
                doc += ["\\clearpage"] + bibliography()
                bib_done = True
            if section not in ("References", "Tables", "Figure legends"):
                doc.append(("\\section*{" if len(m.group(1)) == 2 else "\\subsection*{") + esc(section) + "}")
            continue
        if not line.strip() or section in ("Tables", "Figure legends"):
            continue
        if section == "References":
            rm = re.match(r"(\d+)\. (.*)", line)
            refs.append((rm.group(1), inline(rm.group(2))))
            continue
        if line.strip().lower() == "tablea1":
            doc.append(table("tablea1", tables["tablea1"], caps["tablea1"]))
            continue
        if re.match(r"\s*[*-] ", line):
            items.append(inline(re.sub(r"^\s*[*-] ", "", line)))
            continue
        doc.append(inline(line) + "\n")
        for kind, n in CITED.findall(line):
            if (kind, n) in floats and (kind, n) not in placed:
                doc.append(floats[(kind, n)])
                placed.add((kind, n))
    flush_items()
    if not bib_done:
        doc += [floats[k] for k in sorted(floats) if k not in placed] + bibliography()
    doc += ["\\end{document}"]

    TEX.mkdir(exist_ok=True)
    figdir = TEX / "figures"
    if figdir.exists():
        shutil.rmtree(figdir)
    figdir.mkdir()
    for f in (HERE / "figures").glob("fig*.pdf"):
        shutil.copy(f, figdir / f.name)
    (TEX / "main.tex").write_text("\n".join(doc), encoding="utf-8")
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(TEX.rglob("*")):
            if f.is_file() and (f.name == "main.tex" or f.parent == figdir):
                z.write(f, f.relative_to(TEX).as_posix())
    print(f"written {TEX / 'main.tex'} and {ZIP.name}; floats placed inline: {len(placed)} of {len(floats)}")


if __name__ == "__main__":
    main()
