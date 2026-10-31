"""Note 9-24 topic coding sheets, agreement, adjudication sheets and final topics of the 2,170 medical papers.

`sheets` (once) draws a random item id per medical paper (seed 20261101) and writes blind sheets of 50 (item_id,
title, abstract; venue, year and labels hidden) to data/p9/topic_sheets/; keys stay in data/p9/topic_keys.json
(git-ignored, SHA-256 in results/p9_topics_manifest.json). `status` checks the coder files. `adj` scores
agreement and writes the disagreements, labels in random order, to data/p9/topic_adj_sheets/ in batches of 50.
`final` writes codes/p9/topics/topics_final.csv (item_id, topic) from agreement or adjudication.

Usage: python build_p9_topics.py sheets | status | adj | final
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P9 = HERE / "data" / "p9"
SHEETS, ADJ_SHEETS = P9 / "topic_sheets", P9 / "topic_adj_sheets"
CODES = HERE / "codes" / "p9" / "topics"
KEYS = P9 / "topic_keys.json"
SEED, BATCH = 20261101, 50
ROLES = ("topic1", "topic2")
TOPICS = ("radiology", "pathology_microscopy", "other_clinical_imaging", "ehr_clinical_text", "physiological_signals",
          "neuroscience", "genomics_omics", "proteins", "molecules_drug_discovery", "chemistry_materials",
          "epidemiology_public_health", "other_biology", "other")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, header: tuple, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def keys() -> dict:
    return json.loads(KEYS.read_text(encoding="utf-8"))


def n_batches() -> int:
    return -(-len(keys()) // BATCH)


def sheets() -> None:
    if KEYS.exists():
        raise SystemExit("topic keys exist; sheets are drawn once")
    frame = json.loads((HERE / "results" / "p9_frame.json").read_text(encoding="utf-8"))
    papers = {(p["stratum"], p["forum_id"]): p for p in json.loads((HERE / "data" / "papers.json").read_text(encoding="utf-8"))}
    med = sorted((u for u in frame if u["group"] == "life_science"), key=lambda u: (u["stratum"], u["forum_id"]))
    random.Random(SEED).shuffle(med)
    out = {}
    for i, u in enumerate(med):
        p = papers[(u["stratum"], u["forum_id"])]
        out[f"T{i:04d}"] = dict(stratum=u["stratum"], forum_id=u["forum_id"], label=u["label"], title=p["title"],
                                abstract=" ".join((p.get("abstract") or "").split()))
    KEYS.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    items = sorted(out)
    for b in range(-(-len(items) // BATCH)):
        rows = [(i, out[i]["title"], out[i]["abstract"]) for i in items[b * BATCH:(b + 1) * BATCH]]
        for role in ROLES:
            write_csv(SHEETS / f"p9_{role}_batch_{b:03d}.csv", ("item_id", "title", "abstract"), rows)
    (HERE / "results" / "p9_topics_manifest.json").write_text(json.dumps(dict(
        note="9-24", seed=SEED, batch=BATCH, n_items=len(items), keys_sha256=sha(KEYS)), indent=1), encoding="utf-8")
    print(len(items), "items,", -(-len(items) // BATCH), "batches per coder")


def read_role(role: str) -> dict:
    out = {}
    for f in sorted(CODES.glob(f"p9_{role}_batch_*.csv")):
        for r in csv.DictReader(f.open(encoding="utf-8")):
            out[r["item_id"]] = r["topic"].strip()
    return out


def status() -> dict:
    k, res = keys(), {}
    for role in ROLES:
        missing, invalid = [], []
        for b in range(n_batches()):
            f = CODES / f"p9_{role}_batch_{b:03d}.csv"
            want = {r["item_id"] for r in csv.DictReader((SHEETS / f.name).open(encoding="utf-8"))}
            if not f.exists():
                missing.append(b)
                continue
            got = {r["item_id"]: r.get("topic", "").strip() for r in csv.DictReader(f.open(encoding="utf-8"))}
            if set(got) != want or any(t not in TOPICS for t in got.values()):
                invalid.append(b)
        res[role] = dict(missing=missing, invalid=invalid)
        print(role, "batches", n_batches(), "| missing", len(missing), missing[:20], "| invalid", invalid)
    return res


def kappa(pairs: list[tuple[str, str]]) -> float:
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == t for a, _ in pairs) / n) * (sum(b == t for _, b in pairs) / n) for t in TOPICS)
    return (po - pe) / (1 - pe)


def adj() -> None:
    st = status()
    if any(v["missing"] or v["invalid"] for v in st.values()):
        raise SystemExit("coder files incomplete")
    k, a, b = keys(), read_role("topic1"), read_role("topic2")
    pairs = [(a[i], b[i]) for i in sorted(k)]
    dis = [i for i in sorted(k) if a[i] != b[i]]
    agreement = dict(n=len(pairs), raw=round(sum(x == y for x, y in pairs) / len(pairs), 4), kappa=round(kappa(pairs), 4),
                     n_disagreements=len(dis))
    rng = random.Random(SEED)
    rows = []
    for i in dis:
        la, lb = (a[i], b[i]) if rng.random() < 0.5 else (b[i], a[i])
        rows.append((i, la, lb, k[i]["title"], k[i]["abstract"]))
    for n, s in enumerate(range(0, len(rows), BATCH)):
        write_csv(ADJ_SHEETS / f"p9_topicadj_batch_{n:03d}.csv", ("item_id", "label_a", "label_b", "title", "abstract"),
                  rows[s:s + BATCH])
    (HERE / "results" / "p9_topics_agreement.json").write_text(json.dumps(agreement, indent=1), encoding="utf-8")
    print(json.dumps(agreement), "->", -(-len(rows) // BATCH), "adjudication batches")


def final() -> None:
    k, a, b = keys(), read_role("topic1"), read_role("topic2")
    decided = {}
    for f in sorted(CODES.glob("p9_topicadj_batch_*.csv")):
        for r in csv.DictReader(f.open(encoding="utf-8")):
            decided[r["item_id"]] = r["topic"].strip()
    rows = []
    for i in sorted(k):
        t = a[i] if a[i] == b[i] else decided.get(i)
        if t not in TOPICS:
            raise SystemExit(f"{i}: no valid final topic")
        rows.append((i, t))
    write_csv(CODES / "topics_final.csv", ("item_id", "topic"), rows)
    print(len(rows), "final topics")


if __name__ == "__main__":
    {"sheets": sheets, "status": status, "adj": adj, "final": final}[sys.argv[1] if len(sys.argv) > 1 else "status"]()
