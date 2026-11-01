"""Note 9-26 (post hoc, exploratory): modality, method and architecture of all 4,340 frame papers.

Reads codes/p9/axes/axes_final.csv and the axes keys; writes results/p9_axes.json with X1 to X5 of Note 9-26 and
the medical-topic crosstabs. Architecture is a set: each label is read as "the paper uses this family".

Usage: python posthoc_p9_axes.py
"""
from __future__ import annotations

import csv
import json
from collections import Counter

from analyze_p8 import wilson
from analyze_p9 import boot_ci, final_codes, mh_rd
from build_p9_axes import CODES, KEYS, LABELS
from posthoc_p9_topics import INDICATORS, RESIDUAL, VENUES, topic_rows

HERE = CODES.parents[2]
GROUPS = ("life_science", "other")
AXES = ("modality", "method", "architecture")


def axis_rows() -> list[dict]:
    keys = json.loads(KEYS.read_text(encoding="utf-8"))
    final = {r["item_id"]: r for r in csv.DictReader((CODES / "axes_final.csv").open(encoding="utf-8"))}
    return [dict(item=i, group=k["group"], stratum=k["stratum"], venue=k["stratum"].rsplit("-", 1)[0],
                 year=k["stratum"][-4:], forum_id=k["forum_id"], modality=final[i]["modality"],
                 method=final[i]["method"], architecture=set(final[i]["architecture"].split(";")),
                 architecture_pass=final[i]["architecture_pass"]) for i, k in sorted(keys.items())]


def has(r: dict, axis: str, lab: str) -> bool:
    return lab in r[axis] if axis == "architecture" else r[axis] == lab


def shares(rows: list[dict], axis: str) -> dict:
    n = len(rows)
    out = dict(n=n, labels={})
    for lab in LABELS[axis]:
        k = sum(has(r, axis, lab) for r in rows)
        out["labels"][lab] = dict(n=k, share=k / n if n else None, wilson=wilson(k, n))
    return out


def x1(rows: list[dict]) -> dict:
    out = {}
    for ax in AXES:
        e = out[ax] = {}
        for g in GROUPS:
            sel = [r for r in rows if r["group"] == g]
            e[g] = dict(all=shares(sel, ax), by_venue={v: shares([r for r in sel if r["venue"] == v], ax) for v in VENUES},
                        by_year={y: shares([r for r in sel if r["year"] == y], ax) for y in ("2025", "2026")})
    return out


def x2(rows: list[dict]) -> dict:
    out = {}
    for ax in AXES:
        out[ax] = {}
        for lab in LABELS[ax]:
            data = [(r["stratum"], r["group"] == "life_science", int(has(r, ax, lab))) for r in rows]
            if not any(y for _, _, y in data):
                out[ax][lab] = dict(mh_rd=None, ci=None)
                continue
            out[ax][lab] = dict(mh_rd=mh_rd(data), ci=boot_ci(data, mh_rd))
    return out


def chi2(rows: list[dict], axis: str) -> dict:
    import numpy as np
    from scipy.stats import chi2_contingency
    labs = [lab for lab in LABELS[axis] if any(r[axis] == lab for r in rows)]
    tab = np.array([[sum(r["venue"] == v and r[axis] == lab for r in rows) for lab in labs] for v in VENUES])
    c, p, dof, exp = chi2_contingency(tab)
    n, rs, cs = tab.sum(), tab.sum(1, keepdims=True), tab.sum(0, keepdims=True)
    adj = (tab - exp) / np.sqrt(exp * (1 - rs / n) * (1 - cs / n))
    cells = {v: {lab: round(float(adj[a, b]), 2) for b, lab in enumerate(labs)} for a, v in enumerate(VENUES)}
    flags = [dict(venue=v, label=lab, residual=x, direction="over" if x > 0 else "under")
             for v, d in cells.items() for lab, x in d.items() if abs(x) >= RESIDUAL]
    return dict(chi2=float(c), dof=int(dof), p=float(p), min_expected=float(exp.min()), adjusted_residuals=cells,
                flagged=sorted(flags, key=lambda f: -abs(f["residual"])))


def coded(rows: list[dict]) -> list[dict]:
    """Axis rows joined to the final Protocol 9 practice codes (papers with a full text only)."""
    from build_p9_sheets import KEYS as P9_KEYS
    keys = json.loads(P9_KEYS.read_text(encoding="utf-8"))
    codes = {(keys[i]["stratum"], keys[i]["forum_id"]): c for i, c in final_codes().items()}
    return [dict(r, codes=codes[(r["stratum"], r["forum_id"])]) for r in rows if (r["stratum"], r["forum_id"]) in codes]


def x4(rows: list[dict]) -> dict:
    out = {}
    for ax in AXES:
        out[ax] = {}
        for lab in LABELS[ax]:
            out[ax][lab] = {}
            for g in GROUPS:
                sel = [r["codes"] for r in rows if r["group"] == g and has(r, ax, lab)]
                e = dict(n_coded=len(sel))
                for f, pos in INDICATORS.items():
                    known = [c[f] for c in sel if c[f] != "unclear"]
                    k = sum(x == pos for x in known)
                    e[f] = dict(n_known=len(known), share=k / len(known) if known else None, wilson=wilson(k, len(known)))
                out[ax][lab][g] = e
    return out


def x5(rows: list[dict]) -> dict:
    out = {}
    for f, pos in INDICATORS.items():
        known = [r for r in rows if r["codes"][f] != "unclear"]
        e = out[f] = {}
        for name, stratum in (("venue_year", lambda r: r["stratum"]),
                              ("venue_year_x_modality", lambda r: f"{r['stratum']}|{r['modality']}"),
                              ("venue_year_x_method", lambda r: f"{r['stratum']}|{r['method']}")):
            data = [(stratum(r), r["group"] == "life_science", int(r["codes"][f] == pos)) for r in known]
            both = {s for s, _, _ in data if any(x == s and g for x, g, _ in data) and any(x == s and not g for x, g, _ in data)}
            e[name] = dict(mh_rd=mh_rd(data), ci=boot_ci(data, mh_rd), strata_both_groups=len(both),
                           papers_in_those=sum(s in both for s, _, _ in data), papers=len(data))
    return out


def topic_cross(rows: list[dict]) -> dict:
    topic = {(t["stratum"], t["forum_id"]): t["topic"] for t in topic_rows()}
    med = [dict(r, topic=topic[(r["stratum"], r["forum_id"])]) for r in rows if r["group"] == "life_science"]
    return {ax: {t: dict(Counter(lab for r in med if r["topic"] == t for lab in
                                 (sorted(r[ax]) if ax == "architecture" else [r[ax]])).most_common())
                 for t in sorted({r["topic"] for r in med})} for ax in AXES}


def run() -> dict:
    rows = axis_rows()
    cr = coded(rows)
    agreement = {p: json.loads((HERE / "results" / f"p9_axes_agreement_{p}.json").read_text(encoding="utf-8"))
                 for p in ("a", "b") if (HERE / "results" / f"p9_axes_agreement_{p}.json").exists()}
    res = dict(note="9-26", post_hoc=True, n=len(rows), n_coded=len(cr), agreement=agreement,
               architecture_pass=dict(Counter(r["architecture_pass"] for r in rows)),
               X1=x1(rows), X2=x2(rows),
               X3={g: {ax: chi2([r for r in rows if r["group"] == g], ax) for ax in ("modality", "method")} for g in GROUPS},
               X4=x4(cr), X5=x5(cr), topic_cross=topic_cross(rows))
    (HERE / "results" / "p9_axes.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = run()
    print(json.dumps(dict(n=r["n"], n_coded=r["n_coded"], agreement=r["agreement"],
                          X5={f: {k: (round(v["mh_rd"], 4), v["ci"]) for k, v in e.items()} for f, e in r["X5"].items()}),
                     indent=1))
