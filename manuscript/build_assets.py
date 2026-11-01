"""Build the manuscript's tables and figures from the committed result files, and check its numbers.

Every table cell and figure value is read from verdict_audit/readiness/results/ at build time. The number check
recomputes each figure the text quotes and fails if the rounded value is not in manuscript.md.

Usage: python manuscript/build_assets.py   -> manuscript/tables.json, manuscript/figures/fig{1,2,3}.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
RES = HERE.parent / "verdict_audit" / "readiness" / "results"
FIG = HERE / "figures"
TEXT = (HERE / "manuscript.md").read_text(encoding="utf-8")
STRATA = ("cvpr-2025", "iccv-2025", "eccv-2026", "iclr-2025", "iclr-2026", "icml-2025", "icml-2026", "neurips-2025",
          "neurips-2026")
INDICATORS = (("claims", "Main claims listed and linked to evidence"), ("code", "Code released"),
              ("main_data_access", "Main data openly available"), ("open_data_experiment", "Experiment on open data"),
              ("synthetic_or_sample_release", "Synthetic or sample data released"),
              ("weights_release", "Weights released"), ("outputs_release", "Outputs released"),
              ("variance", "Variance reported"), ("environment", "Environment stated"),
              ("compute", "Compute amount stated"))
LABEL = dict(INDICATORS)
# Candidate screening counts for the nine venue-years (results/candidates_summary.json and codes/labels.csv).
SCREEN = dict(listed=40290, candidates=5530, clinical=1013, life_science=1157, excluded_no=3360)
# Two-group palette from the dataviz reference (categorical slots 2 and 1), validated light-mode: medical is
# orange, other papers blue; text and neutral marks stay in ink colours, never the series colour.
MED, OTH, INK, INK2, GRID = "#eb6834", "#2a78d6", "#0b0b0b", "#52514e", "#c9c8c3"
plt.rcParams.update({"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK, "axes.titleweight": "bold"})


def dumbbell(ax, rows: list[tuple[str, float, float, str]], title: str) -> None:
    """One row per measure: medical (orange) and other (blue) shares joined by a line, the difference on the right."""
    for i, (label, med, oth, note) in enumerate(reversed(rows)):
        ax.plot([100 * oth, 100 * med], [i, i], color=GRID, lw=3, solid_capstyle="round", zorder=1)
        ax.scatter([100 * oth], [i], s=46, color=OTH, edgecolor="white", linewidth=1.2, zorder=3)
        ax.scatter([100 * med], [i], s=46, color=MED, edgecolor="white", linewidth=1.2, zorder=3)
        ax.text(103, i, note, va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(range(len(rows)), [r[0] for r in reversed(rows)])
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("% of papers (claims where marked)")
    ax.xaxis.grid(True, color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", fontsize=9)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)


def summary(p9, areas, ext, claims, more, emp) -> None:
    """Figure 1: the paper in one picture, four panels that read left to right, top to bottom."""
    a3, d, ec = p9["A9_3"], areas["PH9_d"], emp["E_c"]
    sh = lambda f, g: a3[f][g]["share"]
    rd = lambda f: f"{pts(a3[f]['mh_rd'])} pts"
    others = [v for k, v in areas["PH9_c"].items() if k != "medical"]
    oth_decided = sum(v["decided"] * v["attempted"] for v in others) / sum(v["attempted"] for v in others)
    fig = plt.figure(figsize=(7.4, 6.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], hspace=0.55, wspace=0.95)
    a = fig.add_subplot(gs[0, 0])
    dumbbell(a, [("Code released", sh("code", "life_science"), sh("code", "other"), rd("code")),
                 ("Main data open", sh("main_data_access", "life_science"), sh("main_data_access", "other"),
                  rd("main_data_access")),
                 ("Variance reported", sh("variance", "life_science"), sh("variance", "other"), rd("variance")),
                 ("Claims tied to a result", sh("claims", "life_science"), sh("claims", "other"), rd("claims"))],
             "(a) Reported practices")
    b = fig.add_subplot(gs[0, 1])
    dumbbell(b, [("Paper decided", areas["PH9_c"]["medical"]["decided"], oth_decided,
                  f"{pts(d['unadjusted']['rd'])} pts"),
                 ("Claims verified", ec["medical"]["claim_share"]["verified"], ec["other"]["claim_share"]["verified"],
                  ""),
                 ("Claims inconclusive", ec["medical"]["claim_share"]["inconclusive"],
                  ec["other"]["claim_share"]["inconclusive"], "")],
             "(b) Reproduction outcomes")
    b.set_xlabel("% of attempted ICML 2026 papers or claims")
    c = fig.add_subplot(gs[1, 0])
    steps = [("Decided, as observed", d["unadjusted"]),
             ("> same team, claim level", d["claim_level_within_team"]),
             ("> after first-team performance", ext["E1"]["decided"]["adjusted"]),
             ("Fully verified, as observed", ext["E4"]["fully_verified"]["unadjusted"]),
             ("> after first-team performance", more["G1"]["adj_strength"]),
             ("> + claim requirements (220 papers)", claims["K3"]["strength_and_cost"])]
    for i, (label, x) in enumerate(reversed(steps)):
        clear = x["ci"][0] > 0 or x["ci"][1] < 0
        c.plot([100 * x["ci"][0], 100 * x["ci"][1]], [i, i], color=MED, lw=1.8, alpha=0.45, solid_capstyle="round")
        c.scatter([100 * x["rd"]], [i], s=40, color=MED if clear else "white", edgecolor=MED, linewidth=1.4, zorder=3)
        c.text(14, i, f"{pts(x['rd'])}", va="center", fontsize=7.5, color=INK2)
    c.axvline(0, color=INK2, lw=0.8)
    c.set_yticks(range(len(steps)), [s[0] for s in reversed(steps)])
    c.set_xlim(-32, 22)
    c.set_ylim(-0.6, len(steps) - 0.4)
    c.set_xlabel("Medical minus other, percentage points (95% CI)")
    c.set_title("(c) Unadjusted and adjusted differences", loc="left", fontsize=9)
    for s in ("top", "right", "left"):
        c.spines[s].set_visible(False)
    c.tick_params(axis="y", length=0)
    e = fig.add_subplot(gs[1, 1])
    a4 = p9["A9_4"]
    kap = [("Code: reported vs run", a4["code_vs_code_used"]["kappa"]),
           ("Data: open vs obtained", a4["main_data_access_vs_data_obtained"]["kappa"]),
           ("Weights: reported vs used", a4["weights_release_vs_weights_used"]["kappa"])]
    for i, (label, k) in enumerate(reversed(kap)):
        e.barh(i, k, height=0.5, color=INK2)
        e.text(k + 0.02, i, f"{k:.2f}", va="center", fontsize=7.5, color=INK)
    e.axvline(0.40, color=GRID, lw=0.8, ls=(0, (3, 2)))
    e.text(0.42, len(kap) - 0.3, "kappa 0.40", fontsize=7, color=INK2)
    e.set_yticks(range(len(kap)), [k[0] for k in reversed(kap)])
    e.set_xlim(0, 1)
    e.set_ylim(-0.6, len(kap) - 0.05)
    e.set_xlabel("Cohen's kappa, reported vs logbook evidence")
    e.set_title("(d) Reported vs logbook evidence", loc="left", fontsize=9)
    for s in ("top", "right", "left"):
        e.spines[s].set_visible(False)
    e.tick_params(axis="y", length=0)
    handles = [plt.Line2D([], [], marker="o", ls="", color=MED, ms=7, label="Medical papers"),
               plt.Line2D([], [], marker="o", ls="", color=OTH, ms=7, label="Other papers")]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.01), fontsize=8)
    save(fig, "fig1")

# Table captions: first sentence is what the reader should see, then what the table is. Read by both builders.
CAPTIONS = {
    "table1": "Reported reproducibility practices, medical versus other papers, nine venue-years. Medical papers had "
              "higher reporting rates for nine of ten indicators. Shares among papers with a known value; pooled "
              "difference is the Mantel-Haenszel risk difference over venue-years with a 95% paper bootstrap interval.",
    "table2": "Unadjusted and adjusted differences in reproduction outcomes of attempted ICML 2026 papers, medical minus "
              "other (post hoc analyses, Notes 9-9 to 9-15). Rows marked subsample use the 220 papers with coded claim "
              "requirements.",
    "table3": "Agreement between reported practices and logbook evidence of material use, 222 attempted ICML 2026 frame "
              "papers; the last column pools them with the 300-paper extension sample. Agreement was limited for code "
              "and data and higher for weights.",
    "table4": "Sensitivity analyses of reported practices, medical minus other, Mantel-Haenszel over venue-years, "
              "percentage points with 95% CI (post hoc, Note 9-22): main analysis, papers reporting a training-set "
              "size, and all coded papers with unclear treated as no reported release.",
    "tablea1": "Papers in the frame and with a coded full text, by group and venue-year. Retrieval was nearly complete "
               "where open proceedings exist and lowest at NeurIPS 2026.",
}


def load(name: str) -> dict:
    return json.loads((RES / name).read_text(encoding="utf-8"))


def pct(x: float) -> str:
    return f"{100 * x:.1f}"


def pts(x: float) -> str:
    """Percentage points with sign; the text uses the Unicode minus."""
    return f"{100 * x:+.1f}".replace("-", "−")


def ci(c: list) -> str:
    return f"{pts(c[0])} to {pts(c[1])}"


def est(x: dict) -> str:
    return f"{pts(x['rd'])} ({ci(x['ci'])})"


def table1(p9: dict) -> list[list[str]]:
    rows = [["Practice", "Medical, % (n known)", "Other, % (n known)", "Pooled difference, points (95% CI)",
             "Unclear, medical / other"]]
    for f, label in INDICATORS:
        a = p9["A9_3"][f]
        ls, ot = a["life_science"], a["other"]
        rows.append([label, f"{pct(ls['share'])} ({ls['n_known']})", f"{pct(ot['share'])} ({ot['n_known']})",
                     f"{pts(a['mh_rd'])} ({ci(a['mh_ci'])})", f"{ls['unclear']} / {ot['unclear']}"])
    return rows


def table2(areas: dict, ext: dict, claims: dict, adv: dict, more: dict) -> list[list[str]]:
    d, e1, e4, k3 = areas["PH9_d"], ext["E1"], ext["E4"], claims["K3"]
    return [["Outcome and adjustment", "Medical minus other, points (95% CI)"],
            ["Decided, all attempted papers (110 vs 1,821), unadjusted", est(d["unadjusted"])],
            ["Decided, clinical papers only", est(adv["F2"]["label_split"]["clinical"])],
            ["Decided, life-science papers only", est(adv["F2"]["label_split"]["life_science"])],
            ["Decided, adjusted for number of teams", est(d["teams"])],
            ["Decided, adjusted for first-team performance", est(e1["decided"]["adjusted"])],
            ["Fully verified, all attempted papers, unadjusted", est(e4["fully_verified"]["unadjusted"])],
            ["Fully verified, all attempted papers, adjusted for first-team performance", est(more["G1"]["adj_strength"])],
            ["Fully verified, claim-coded subsample (220 papers), unadjusted", est(k3["unadjusted"])],
            ["Fully verified, subsample, adjusted for first-team performance", est(k3["strength"])],
            ["Fully verified, subsample, adjusted for first-team performance and claim requirements", est(k3["strength_and_cost"])],
            ["Claim decided, unadjusted (claim level)", est(d["claim_level_unadjusted"])],
            ["Claim decided, within team (claim level)", est(d["claim_level_within_team"])]]


def table3(p9: dict, ext: dict) -> list[list[str]]:
    a4, pooled = p9["A9_4"], ext["pooled"]
    rows = [["Stated in full text vs obtained by reproducers", "n", "Sensitivity", "Specificity", "Kappa",
             "Kappa pooled with extension (n)"]]
    for key, label in (("code_vs_code_used", "Code released vs authors' code run"),
                       ("main_data_access_vs_data_obtained", "Main data open vs data obtained"),
                       ("weights_release_vs_weights_used", "Weights released vs weights used")):
        x, y = a4[key], pooled[key]
        rows.append([label, str(x["n"]), f"{x['sensitivity']:.2f}", f"{x['specificity']:.2f}", f"{x['kappa']:.2f}",
                     f"{y['kappa']:.2f} ({y['n']})"])
    c = a4["neurips_checklist_item5_vs_code"]
    rows.append(["NeurIPS checklist item 5 vs code released", str(c["n"]), f"{c['sensitivity']:.2f}",
                 f"{c['specificity']:.2f}", f"{c['kappa']:.2f}", ""])
    return rows


def table4(p9: dict, emp: dict) -> list[list[str]]:
    rows = [["Practice", "Main analysis: known value", "Papers reporting a training-set size",
             "All coded papers, unclear as no reported release"]]
    for f in ("code", "main_data_access", "weights_release", "variance", "synthetic_or_sample_release",
              "outputs_release"):
        a = p9["A9_3"][f]
        e = emp["E_a"]["fields"].get(f)
        b = emp["E_b"].get(f)
        rows.append([LABEL[f], f"{pts(a['mh_rd'])} ({ci(a['mh_ci'])})", est(e) if e else "",
                     (f"{pct(b['share']['medical'])} vs {pct(b['share']['other'])}%; {est(b)}") if b else ""])
    return rows


def table_s1(p9: dict) -> list[list[str]]:
    cov = p9["coverage"]
    rows = [["Venue-year", "Medical: frame / full text", "Other: frame / full text"]]
    for s in STRATA:
        ls, ot = cov[f"life_science|{s}"], cov[f"other|{s}"]
        rows.append([s, f"{ls['frame']} / {ls['coded']}", f"{ot['frame']} / {ot['coded']}"])
    tot = lambda g, k: sum(v[k] for kk, v in cov.items() if kk.startswith(g + "|"))
    rows.append(["Total", f"{tot('life_science', 'frame')} / {tot('life_science', 'coded')}",
                 f"{tot('other', 'frame')} / {tot('other', 'coded')}"])
    return rows


def save(fig, name: str) -> None:
    """PNG for Word, vector PDF for LaTeX; white background, no transparency."""
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=300, bbox_inches="tight", facecolor="white", transparent=False)
    plt.close(fig)


def fig1(p9: dict) -> None:
    """PRISMA-style flow: fixed box sizes, every arrow ends on a box edge."""
    from matplotlib.patches import Rectangle
    coded = p9["coded"]
    frame = sum(v["frame"] for v in p9["coverage"].values())
    W, H, SW, X, XL, XR = 0.42, 0.105, 0.265, 0.52, 0.1425, 0.8675
    Y = (0.92, 0.74, 0.56, 0.38, 0.20)
    nl = "\n"
    main = [f"Papers at nine venue-years{nl}2025-2026{nl}n = {SCREEN['listed']:,}",
            f"Candidates by topic{nl}or term screen{nl}n = {SCREEN['candidates']:,}",
            f"Labelled clinical ({SCREEN['clinical']:,}){nl}or life science ({SCREEN['life_science']:,}){nl}"
            f"medical group, n = {SCREEN['clinical'] + SCREEN['life_science']:,}",
            f"Frame, n = {frame:,}{nl}medical {frame // 2:,}{nl}random other {frame // 2:,}",
            f"Full text retrieved and coded{nl}medical {coded['life_science']:,}{nl}other {coded['other']:,}"]
    fig, ax = plt.subplots(figsize=(6.3, 6.0))
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(0.12, 0.99)
    ax.axis("off")
    kw = dict(ha="center", va="center", fontsize=8, linespacing=1.3)
    line = dict(color="black", lw=0.8)
    arrow = dict(arrowstyle="-|>", color="black", lw=0.8, mutation_scale=9, shrinkA=0, shrinkB=0)

    def box(x, y, w, text, h=H, fs=8):
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec="black", lw=0.8))
        ax.text(x, y, text, **{**kw, "fontsize": fs})

    for y, t in zip(Y, main):
        box(X, y, W, t)
    for y0, y1 in zip(Y, Y[1:]):
        ax.annotate("", xy=(X, y1 + H / 2), xytext=(X, y0 - H / 2), arrowprops=arrow)
    # exclusions branch right from the midpoint of the arrow above them; reasons from the release table
    import csv
    from collections import Counter
    with (RES / "p9_papers.csv").open(encoding="utf-8") as fh:
        ft = Counter((r["group"], r["fulltext_status"]) for r in csv.DictReader(fh) if r["fulltext_status"] != "ok")
    why = Counter(s for _, s in ft.elements())
    lost = {g: sum(n for (gg, _), n in ft.items() if gg == g) for g in ("life_science", "other")}
    nofull = (f"Excluded: no full text{nl}n = {sum(why.values()):,}{nl}medical {lost['life_science']:,}, "
              f"other {lost['other']:,}{nl}no match on any{nl}source: {why['no_match']:,}{nl}"
              f"OpenAlex not checked,{nl}quota reached: {why['error']}")
    assert set(why) <= {"no_match", "error"}
    assert sum(why.values()) == frame - coded["life_science"] - coded["other"]
    for (y0, y1), text, h, fs in (((Y[1], Y[2]), f"Excluded:{nl}labelled not medical{nl}n = {SCREEN['excluded_no']:,}",
                                   0.085, 8),
                                  ((Y[3], Y[4]), nofull, 0.165, 7)):
        ym = (y0 + y1) / 2
        box(XR, ym, SW, text, h=h, fs=fs)
        ax.annotate("", xy=(XR - SW / 2, ym), xytext=(X, ym), arrowprops=arrow)
    # non-candidates branch left from the first arrow and rejoin the frame from the left
    yb, hl = (Y[0] + Y[1]) / 2, 0.13
    box(XL, Y[1], SW, f"Non-candidates{nl}n = {SCREEN['listed'] - SCREEN['candidates']:,}{nl}"
                      f"random sample{nl}drawn per venue-year", h=hl)
    ax.plot([X, XL], [yb, yb], **line)
    ax.annotate("", xy=(XL, Y[1] + hl / 2), xytext=(XL, yb), arrowprops=arrow)
    ax.plot([XL, XL], [Y[1] - hl / 2, Y[3]], **line)
    ax.annotate("", xy=(X - W / 2, Y[3]), xytext=(XL, Y[3]), arrowprops=arrow)
    save(fig, "fig2")


def forest_ax(ax, rows: list[tuple[str, dict]], xlabel: str, title: str | None = None) -> None:
    hi = max(100 * x["ci"][1] for _, x in rows)
    for i, (_, x) in enumerate(reversed(rows)):
        clear = x["ci"][0] > 0 or x["ci"][1] < 0  # interval excludes zero
        ax.plot([100 * x["ci"][0], 100 * x["ci"][1]], [i, i], color=INK2, lw=1.6, solid_capstyle="round")
        ax.plot(100 * x["rd"], i, "o", ms=6, color=INK if clear else "white", mec=INK, mew=1.2)
        ax.text(hi + 2, i, f"{pts(x['rd'])} ({ci(x['ci'])})", va="center", fontsize=7.5, color=INK2)
    ax.axvline(0, color=GRID, lw=0.8)
    ax.set_xlim(right=hi + 20)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_yticks(range(len(rows)), [r[0] for r in reversed(rows)], fontsize=8.5)
    ax.set_xlabel(xlabel, fontsize=8.5)
    ax.tick_params(axis="x", labelsize=8.5)
    if title:
        ax.set_title(title, fontsize=10, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def main() -> None:
    FIG.mkdir(exist_ok=True)
    p9, areas, ext = load("p9.json"), load("p9_areas.json"), load("p9_extended.json")
    claims, adv, ext9 = load("p9_claims.json"), load("p9_adversarial.json"), load("p9_ext.json")
    more, emp = load("p9_more.json"), load("p9_empirical.json")
    tables = dict(table1=table1(p9), table2=table2(areas, ext, claims, adv, more), table3=table3(p9, ext9),
                  table4=table4(p9, emp), tablea1=table_s1(p9))
    tables["captions"] = CAPTIONS
    (HERE / "tables.json").write_text(json.dumps(tables, indent=1, ensure_ascii=False), encoding="utf-8")
    summary(p9, areas, ext, claims, more, emp)
    fig1(p9)
    fig, ax = plt.subplots(figsize=(6.3, 0.36 * len(INDICATORS) + 0.9))
    forest_ax(ax, [(label, dict(rd=p9["A9_3"][f]["mh_rd"], ci=p9["A9_3"][f]["mh_ci"])) for f, label in INDICATORS],
              "Medical minus other, percentage points (Mantel-Haenszel, 95% CI)")
    save(fig, "fig3")
    d = areas["PH9_d"]
    paper = [("Decided, unadjusted", d["unadjusted"]),
             ("Decided, clinical papers only", adv["F2"]["label_split"]["clinical"]),
             ("Decided, life-science papers only", adv["F2"]["label_split"]["life_science"]),
             ("Decided, adjusted for number of teams", d["teams"]),
             ("Decided, adjusted for first-team performance", ext["E1"]["decided"]["adjusted"]),
             ("Fully verified, unadjusted", ext["E4"]["fully_verified"]["unadjusted"]),
             ("Fully verified, adjusted for first-team performance", more["G1"]["adj_strength"]),
             ("Fully verified, subsample, performance and claim requirements", claims["K3"]["strength_and_cost"])]
    claim = [("Claim decided, unadjusted", d["claim_level_unadjusted"]),
             ("Claim decided, within team", d["claim_level_within_team"])]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.3, 5.4), gridspec_kw=dict(height_ratios=[len(paper), len(claim) + 0.6]),
                                 sharex=True)
    forest_ax(a1, paper, "", "(a) Paper level, attempted ICML 2026 papers")
    forest_ax(a2, claim, "Medical minus other, percentage points (95% CI)", "(b) Claim level")
    fig.tight_layout()
    save(fig, "fig4")
    missing = checks(p9, areas, ext, claims, adv, ext9, more, emp) + checks_posthoc(load("p9_topics.json"),
                                                                                  load("p9_axes.json"))
    for m in missing:
        print("NOT IN TEXT:", m, file=sys.stderr)
    print(f"tables and figures written; {len(missing)} quoted numbers not found in the text", file=sys.stderr)
    sys.exit(1 if missing else 0)


def checks(p9, areas, ext, claims, adv, ext9, more, emp) -> list[str]:
    """Quoted text that must appear verbatim in manuscript.md, each built from a result file."""
    a3, a5, d, ea, eb, ec = p9["A9_3"], p9["A9_5"], areas["PH9_d"], emp["E_a"], emp["E_b"], emp["E_c"]
    ph9b = load("p9_posthoc.json")["PH9_b"]
    sh = lambda f, g: pct(a3[f][g]["share"])
    mh = lambda f: dict(rd=a3[f]["mh_rd"], ci=a3[f]["mh_ci"])
    pair = lambda x: f"{pts(x['rd'])}, {ci(x['ci'])}"
    s1 = ext["E1"]["first_team_strength"]
    f2, e4, k1, k3, a4 = adv["F2"], ext["E4"], claims["K1"], claims["K3"], p9["A9_4"]
    want = [
        # Reported practices
        f"code release ({sh('code', 'life_science')}% versus {sh('code', 'other')}%; pooled difference "
        f"{pts(a3['code']['mh_rd'])} percentage points, 95% CI {ci(a3['code']['mh_ci'])})",
        f"open main data ({sh('main_data_access', 'life_science')}% versus {sh('main_data_access', 'other')}%; "
        f"{pair(mh('main_data_access'))})",
        f"weights release ({sh('weights_release', 'life_science')}% versus {sh('weights_release', 'other')}%; "
        f"{pair(mh('weights_release'))})",
        f"variance ({sh('variance', 'life_science')}% versus {sh('variance', 'other')}%; {pair(mh('variance'))})",
        f"({sh('claims', 'life_science')}% versus {sh('claims', 'other')}%; {pair(mh('claims'))})",
        f"(+7.5, {ci(ext['E5']['vision']['main_data_access']['ci'])})",
        f"Among the {ea['units']['medical']:,} medical and {ea['units']['other']:,} other papers reporting a "
        f"training-set size",
        f"code {pts(ea['fields']['code']['rd'])} percentage points ({ci(ea['fields']['code']['ci'])}), open main data "
        f"{pts(ea['fields']['main_data_access']['rd'])} ({ci(ea['fields']['main_data_access']['ci'])}), weights "
        f"{pts(ea['fields']['weights_release']['rd'])} ({ci(ea['fields']['weights_release']['ci'])}) and variance "
        f"{pts(ea['fields']['variance']['rd'])} ({ci(ea['fields']['variance']['ci'])})",
        f"({pct(eb['main_data_access']['share']['medical'])}% versus {pct(eb['main_data_access']['share']['other'])}%; "
        f"{pair(eb['main_data_access'])})",
        f"decreased to {pts(eb['weights_release']['rd'])} percentage points ({ci(eb['weights_release']['ci'])})",
        f"sample or synthetic data ({pair(eb['synthetic_or_sample_release'])}) and outputs ({pair(eb['outputs_release'])})",
        # Reproduction outcomes
        f"{pct(a5['cells']['life_science']['decided'])}% of medical papers were decided",
        f"{pts(d['unadjusted']['rd'])} percentage points (95% CI {ci(d['unadjusted']['ci'])}; permutation p < 0.001)",
        f"{pts(f2['label_split']['clinical']['rd'])} percentage points for clinical papers "
        f"(95% CI {ci(f2['label_split']['clinical']['ci'])})",
        f"{pts(f2['label_split']['life_science']['rd'])} for life-science papers ({ci(f2['label_split']['life_science']['ci'])})",
        f"{pts(f2['top_medical_team_dropped']['rd'])} ({ci(f2['top_medical_team_dropped']['ci'])}) when every logbook",
        f"full verification ({pair(e4['fully_verified']['unadjusted'])})",
        f"falsified claim ({pair(e4['any_falsified']['unadjusted'])})",
        f"rated verified in {pct(ec['medical']['claim_share']['verified'])}% against "
        f"{pct(ec['other']['claim_share']['verified'])}% and inconclusive in "
        f"{pct(ec['medical']['claim_share']['inconclusive'])}% against {pct(ec['other']['claim_share']['inconclusive'])}%",
        f"Toy verdicts accounted for {pct(ec['medical']['claim_share']['toy'])}% of medical claims and "
        f"{pct(ec['other']['claim_share']['toy'])}% of other claims (difference {pts(ec['toy_claim_diff']['rd'])} "
        f"percentage points, 95% CI {ci(ec['toy_claim_diff']['ci'])})",
        f"the difference was {pts(a5['unadjusted']['rd'])} percentage points ({ci(a5['unadjusted']['ci'])})",
        f"changed it to {est(a5['both'])}",
        f"decreased from {pts(d['claim_level_unadjusted']['rd'])} to {pts(d['claim_level_within_team']['rd'])} "
        f"percentage points (95% CI {ci(d['claim_level_within_team']['ci'])})",
        f"on {pct(s1['mean'][0])}% of its other attempted papers, against {pct(s1['mean'][1])}% for teams first on "
        f"other papers ({pts(s1['diff'])}, {ci(s1['ci'])})",
        f"Among {more['G2']['papers']} papers attempted by at least two teams",
        f"(difference {pts(more['G2']['rd'])} percentage points, 95% CI {ci(more['G2']['ci'])})",
        f"decreased from {pts(ext['E1']['decided']['unadjusted']['rd'])} to {pts(ext['E1']['decided']['adjusted']['rd'])} "
        f"percentage points (95% CI {ci(ext['E1']['decided']['adjusted']['ci'])})",
        f"A difference in full verification remained ({pair(more['G1']['adj_strength'])})",
        f"changed the decided difference to {pts(ph9b['rd'])} percentage points ({ci(ph9b['ci'])}; "
        f"{ph9b['n']} frame papers)",
        f"({ph9b['distribution']['life_science']['listed_and_linked']} medical and "
        f"{ph9b['distribution']['other']['listed_and_linked']} other papers)",
        f"coders classified {pct(k1['costly']['medical'])}% of medical claims and {pct(k1['costly']['other'])}% of "
        f"other claims",
        f"(difference {pts(k1['costly']['diff'])} percentage points, 95% CI {ci(k1['costly']['ci'])})",
        f"and {pct(k1['analytic']['medical'])}% and {pct(k1['analytic']['other'])}% as checkable by analysis alone",
        f"the full-verification difference was {pts(k3['unadjusted']['rd'])} percentage points, "
        f"{est(k3['strength'])} after adjustment",
        f"and {est(k3['strength_and_cost'])} after adjustment for both",
        # Agreement
        f"(kappa {a4['code_vs_code_used']['kappa']:.2f}; n = {a4['code_vs_code_used']['n']}; sensitivity "
        f"{a4['code_vs_code_used']['sensitivity']:.2f}, specificity {a4['code_vs_code_used']['specificity']:.2f})",
        f"(kappa {a4['main_data_access_vs_data_obtained']['kappa']:.2f}, n = {a4['main_data_access_vs_data_obtained']['n']})",
        f"kappas were {ext9['pooled']['code_vs_code_used']['kappa']:.2f} (n = {ext9['pooled']['code_vs_code_used']['n']})",
        f"(kappa {a4['neurips_checklist_item5_vs_code']['kappa']:.2f}, n = {a4['neurips_checklist_item5_vs_code']['n']})",
        # Methods and recommendations
        f"{p9['adjudicated']:,} disagreements",
        f"This mapping was present in {sh('claims', 'life_science')}% of medical papers and {sh('claims', 'other')}% "
        f"of other papers",
        f"Access could not be coded from the text for {a3['main_data_access']['life_science']['unclear']} of "
        f"{a3['main_data_access']['life_science']['n']:,} medical papers",
        f"Weights were not reported in {a3['weights_release']['life_science']['unclear']:,} of "
        f"{a3['weights_release']['life_science']['n']:,} medical papers",
        f"The compute tier was not reported in {a3['compute_tier']['life_science']['distribution']['not_stated']:,} "
        f"of {a3['compute_tier']['life_science']['n']:,} medical papers",
        f"specific result ({sh('claims', 'life_science')}% versus {sh('claims', 'other')}%)",
    ]
    return [w for w in want if w not in TEXT]


def checks_posthoc(top: dict, ax: dict) -> list[str]:
    """Quoted numbers of the topic and axes section (Notes 9-24 to 9-27), each built from a result file."""
    ov, res = top["overall"], top["T2_venue_by_topic"]
    r = lambda v, t: f"{res['adjusted_residuals'][v][t]:.1f}"
    topic = lambda t: f"{ov[t]['n']}, {pct(ov[t]['share'])}%"
    ag = ax["agreement"]["a"]
    x2 = lambda a, l: f"{pts(ax['X2'][a][l]['mh_rd'])}, {ci(ax['X2'][a][l]['ci'])}"
    share = lambda a, g, l: pct(ax["X1"][a][g]["all"]["labels"][l]["share"])
    both = lambda a, l: f"{share(a, 'life_science', l)}% versus {share(a, 'other', l)}%"
    x5 = lambda f, s: ax["X5"][f][s]
    want = [
        f"(Notes 9-24 and 9-26)",
        f"each of the {top['n']:,} medical papers",
        f"coded all {ax['n']:,} papers",
        f"agreed on {pct(top['agreement']['raw'])}% of medical papers (kappa {top['agreement']['kappa']:.2f}; "
        f"{top['agreement']['n_disagreements']} disagreements adjudicated)",
        f"neuroscience ({ov['neuroscience']['n']} papers, {pct(ov['neuroscience']['share'])}%), radiology "
        f"({topic('radiology')}), proteins ({topic('proteins')}) and genomics and omics ({topic('genomics_omics')})",
        f"(chi-square {res['chi2']:.1f}, {res['dof']} degrees of freedom",
        f"(adjusted residuals {r('cvpr', 'radiology')}, {r('iccv', 'radiology')} and {r('eccv', 'radiology')})",
        f"neuroscience at NeurIPS ({r('neurips', 'neuroscience')})",
        f"data type (kappa {ag['modality']['kappa']:.2f}) and method (kappa {ag['method']['kappa']:.2f})",
        f"(exact agreement on the label set {ag['architecture']['raw']:.2f}); "
        f"{sum(ag[k]['n_disagreements'] for k in ('modality', 'method', 'architecture')):,} item-axis",
        f"molecular graphs ({x2('modality', 'graph_molecule').replace(',', ' percentage points,', 1)}), time series ({x2('modality', 'time_series')}) and "
        f"volumetric images ({x2('modality', 'volumetric')})",
        f"text ({x2('modality', 'text')}) or no data or synthetic data ({x2('modality', 'none_or_synthetic')})",
        f"representation learning ({x2('method', 'representation_learning')})",
        f"optimisation and efficiency ({x2('method', 'optimization_efficiency')}) or theory ({x2('method', 'theory')})",
        f"Causal inference and trials ({both('method', 'causal_inference_trials')}) and biostatistical inference "
        f"({both('method', 'biostatistics_inference')})",
        f"in {share('architecture', 'life_science', 'llm_vlm')}% of medical and "
        f"{share('architecture', 'other', 'llm_vlm')}% of other papers",
        f"code {pts(x5('code', 'venue_year_x_method')['mh_rd'])} percentage points "
        f"({ci(x5('code', 'venue_year_x_method')['ci'])}), open main data "
        f"{pts(x5('main_data_access', 'venue_year_x_method')['mh_rd'])} "
        f"({ci(x5('main_data_access', 'venue_year_x_method')['ci'])}), weights "
        f"{pts(x5('weights_release', 'venue_year_x_method')['mh_rd'])} "
        f"({ci(x5('weights_release', 'venue_year_x_method')['ci'])}) and variance "
        f"{pts(x5('variance', 'venue_year_x_method')['mh_rd'])}",
        f"code ({pts(x5('code', 'venue_year_x_modality')['mh_rd'])}), weights "
        f"({pts(x5('weights_release', 'venue_year_x_modality')['mh_rd'])}, "
        f"{ci(x5('weights_release', 'venue_year_x_modality')['ci'])}) and variance "
        f"({pts(x5('variance', 'venue_year_x_modality')['mh_rd'])})",
        f"open main data difference of {pts(x5('main_data_access', 'venue_year')['mh_rd'])} reversed to "
        f"{pts(x5('main_data_access', 'venue_year_x_modality')['mh_rd'])} percentage points "
        f"({ci(x5('main_data_access', 'venue_year_x_modality')['ci'])})",
    ]
    return [w for w in want if w not in TEXT]


if __name__ == "__main__":
    main()
