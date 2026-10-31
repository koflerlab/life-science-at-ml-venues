"""Note 9-24 figures: t-SNE map of the 2,170 medical abstracts and the venue-by-topic table.

Reads results/p9_topics.json, codes/p9/topics/topics_final.csv, the topic keys and the t-SNE coordinates (both under
the data root, git-ignored). Writes manuscript/figures/fig_topics_map.{png,pdf} and fig_topics_venue.{png,pdf}.
The map is an illustration; every share quoted in the text comes from p9_topics.json.

Usage: python manuscript/build_topic_figures.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
READY = HERE.parent / "verdict_audit" / "readiness"
sys.path.insert(0, str(READY))
from build_assets import FIG, GRID, INK, INK2, RES, plt, save  # noqa: E402
from build_p9_topics import CODES as TOPIC_CODES, KEYS as TOPIC_KEYS, TOPICS  # noqa: E402
from posthoc_p9_topics import MAP_DIR, VENUES  # noqa: E402

# Six topic families on categorical slots 1-6 of the dataviz reference (validated light mode, adjacent pairs; three
# slots sit below 3:1 on the surface, so every family is also labelled directly on the map). "Other" stays neutral.
FAMILIES = (
    ("Medical imaging", ("radiology", "pathology_microscopy", "other_clinical_imaging"), "#2a78d6"),
    ("Clinical records, signals, epidemiology", ("ehr_clinical_text", "physiological_signals",
                                                 "epidemiology_public_health"), "#eb6834"),
    ("Neuroscience", ("neuroscience",), "#1baf7a"),
    ("Genomics and omics", ("genomics_omics",), "#eda100"),
    ("Proteins", ("proteins",), "#e87ba4"),
    ("Molecules and chemistry", ("molecules_drug_discovery", "chemistry_materials"), "#008300"),
    ("Other biology and other", ("other_biology", "other"), "#a3a29d"),
)
FAMILY_OF = {t: f for f, ts, _ in FAMILIES for t in ts}
COLOR = {f: c for f, _, c in FAMILIES}
VENUE_NAME = dict(cvpr="CVPR", iccv="ICCV", eccv="ECCV", iclr="ICLR", icml="ICML", neurips="NeurIPS")
TOPIC_NAME = dict(radiology="Radiology", pathology_microscopy="Pathology, microscopy",
                  other_clinical_imaging="Other clinical imaging", ehr_clinical_text="EHR, clinical text",
                  physiological_signals="Physiological signals", neuroscience="Neuroscience",
                  genomics_omics="Genomics, omics", proteins="Proteins",
                  molecules_drug_discovery="Molecules, drug discovery", chemistry_materials="Chemistry, materials",
                  epidemiology_public_health="Epidemiology, public health", other_biology="Other biology",
                  other="Other")


def points() -> list[dict]:
    keys = json.loads(TOPIC_KEYS.read_text(encoding="utf-8"))
    topic = {r["item_id"]: r["topic"] for r in csv.DictReader((TOPIC_CODES / "topics_final.csv").open(encoding="utf-8"))}
    xy = {r["item_id"]: (float(r["x"]), float(r["y"])) for r in csv.DictReader((MAP_DIR / "tsne.csv").open(encoding="utf-8"))}
    return [dict(item=i, venue=keys[i]["stratum"].rsplit("-", 1)[0], topic=topic[i], family=FAMILY_OF[topic[i]],
                 x=xy[i][0], y=xy[i][1]) for i in sorted(keys)]


def fig_map(pts: list[dict]) -> None:
    fig = plt.figure(figsize=(7.2, 8.6))
    gs = fig.add_gridspec(3, 3, height_ratios=(2.2, 1, 1), hspace=0.25, wspace=0.08)
    ax = fig.add_subplot(gs[0, :])
    order = [f for f, _, _ in FAMILIES][::-1]  # neutral "other" drawn first, underneath
    for f in order:
        sel = [p for p in pts if p["family"] == f]
        ax.scatter([p["x"] for p in sel], [p["y"] for p in sel], s=9, c=COLOR[f], linewidths=0.4, edgecolors="white",
                   label=f"{f} ({len(sel)})", zorder=2)
    for f, _, _ in FAMILIES[:-1]:  # direct labels at the family median (secondary encoding)
        sel = np.array([(p["x"], p["y"]) for p in pts if p["family"] == f])
        if len(sel):
            mx, my = np.median(sel, axis=0)
            ax.text(mx, my, f, fontsize=7.5, color=INK, ha="center", va="center", zorder=3,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), frameon=False, fontsize=7.5, markerscale=1.6)
    ax.set_title("(a) Medical papers by topic family (t-SNE of SPECTER2 abstract embeddings)", loc="left", fontsize=9)
    for k, v in enumerate(VENUES):
        a = fig.add_subplot(gs[1 + k // 3, k % 3])
        a.scatter([p["x"] for p in pts], [p["y"] for p in pts], s=3, c="#dedcd7", linewidths=0, zorder=1)
        sel = [p for p in pts if p["venue"] == v]
        a.scatter([p["x"] for p in sel], [p["y"] for p in sel], s=4, c=INK2, linewidths=0, zorder=2)
        a.set_xticks([]); a.set_yticks([])
        for s in a.spines.values():
            s.set_color(GRID)
        a.set_title(f"{VENUE_NAME[v]} (n = {len(sel)})", loc="left", fontsize=8.5)
    fig.text(0.125, 0.355, "(b) Papers of each venue on the same map", fontsize=9, weight="bold")
    save(fig, "fig_topics_map")


def fig_venue(res: dict) -> None:
    by = res["T1_by_venue"]
    flags = {(f["venue"], f["topic"]): f["direction"] for f in res["T2_venue_by_topic"]["flagged"]}
    topics = [t for t in TOPICS if any(by[v]["topics"][t]["n"] for v in VENUES)]
    m = np.array([[100 * by[v]["topics"][t]["share"] for v in VENUES] for t in topics])
    fig, ax = plt.subplots(figsize=(6.4, 0.32 * len(topics) + 1.2))
    ax.imshow(m, cmap="Blues", vmin=0, vmax=max(40, m.max()), aspect="auto")
    for i, t in enumerate(topics):
        for j, v in enumerate(VENUES):
            mark = {"over": " ▲", "under": " ▼"}.get(flags.get((v, t)), "")
            ax.text(j, i, f"{m[i, j]:.0f}{mark}", ha="center", va="center", fontsize=7.5,
                    color="white" if m[i, j] > 25 else INK)
    ax.set_xticks(range(len(VENUES)), [f"{VENUE_NAME[v]}\n(n = {by[v]['n']})" for v in VENUES], fontsize=8)
    ax.set_yticks(range(len(topics)), [TOPIC_NAME[t] for t in topics], fontsize=8)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Share of each venue's medical papers by topic (%)", loc="left", fontsize=9)
    fig.text(0.0, -0.02, "▲ / ▼ adjusted standardised residual ≥ 3 / ≤ −3 (Note 9-24, T2)", fontsize=7, color=INK2,
             transform=ax.transAxes)
    save(fig, "fig_topics_venue")


def main() -> None:
    res = json.loads((RES / "p9_topics.json").read_text(encoding="utf-8"))
    fig_map(points())
    fig_venue(res)
    print("wrote", FIG / "fig_topics_map.png", FIG / "fig_topics_venue.png")


if __name__ == "__main__":
    main()
