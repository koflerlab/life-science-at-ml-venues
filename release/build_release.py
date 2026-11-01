"""Build the public release tables: release/hf/p9_papers.csv and docs/data.json.

Joins the coded paper table with topics, axes and t-SNE map coordinates. Only public metadata and coded fields are
written (no abstracts, no full texts). Keys files and the data root are read locally and never copied.

Usage: python -I release/build_release.py
"""
import csv
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
RD = REPO / "verdict_audit" / "readiness"
DATA_ROOT = Path(os.environ.get("DATA_ROOT", r"C:\Projects\data"))
TSNE = DATA_ROOT / "datasets" / "literature" / "ml-venue-fulltext" / "2025-2026-v1" / "derived" / "topics-map-v1" / "tsne.csv"
N = 4340


def read(path):
    with Path(path).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    papers = read(RD / "results" / "p9_papers.csv")
    assert len(papers) == N
    tkeys = json.loads((RD / "data" / "p9" / "topic_keys.json").read_text(encoding="utf-8"))
    akeys = json.loads((RD / "data" / "p9" / "axes_keys.json").read_text(encoding="utf-8"))
    topic = {r["item_id"]: r["topic"] for r in read(RD / "codes" / "p9" / "topics" / "topics_final.csv")}
    axes = {r["item_id"]: r for r in read(RD / "codes" / "p9" / "axes" / "axes_final.csv")}
    xy = {r["item_id"]: (float(r["x"]), float(r["y"])) for r in read(TSNE)}
    pid = {(r["venue"] + "-" + r["year"], r["forum_id"]): r["item"] for r in papers}
    assert len(pid) == N
    by_topic = {pid[(k["stratum"], k["forum_id"])]: (i, k) for i, k in tkeys.items()}
    by_axes = {pid[(k["stratum"], k["forum_id"])]: i for i, k in akeys.items()}
    assert len(by_topic) == 2170 and len(by_axes) == N
    out = []
    for p in papers:
        r = {k: v for k, v in p.items() if k not in ("topic_label",)}
        t = by_topic.get(p["item"])
        r["topic"] = topic[t[0]] if t else ""
        a = axes[by_axes[p["item"]]]
        r["modality"], r["method"], r["architecture"] = a["modality"], a["method"], a["architecture"]
        r["tsne_x"], r["tsne_y"] = (f"{xy[t[0]][0]:.3f}", f"{xy[t[0]][1]:.3f}") if t else ("", "")
        out.append(r)
    assert sum(1 for r in out if r["topic"]) == 2170
    assert sum(1 for r in out if r["group"] == "life_science") == 2170
    assert all(bool(r["topic"]) == (r["group"] == "life_science") for r in out)
    (REPO / "release" / "hf").mkdir(exist_ok=True)
    with (REPO / "release" / "hf" / "p9_papers.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print("rows", len(out), "cols", len(out[0]))

    med = [r for r in out if r["topic"]]
    cols = ["item", "title", "venue", "year", "forum_id", "topic", "modality", "method", "architecture", "code",
            "main_data_access", "weights_release", "variance", "tsne_x", "tsne_y"]
    (REPO / "docs" / "data.json").write_text(json.dumps(dict(cols=cols, rows=[[r[c] for c in cols] for r in med]),
                                                         separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print("map rows", len(med))


if __name__ == "__main__":
    main()
