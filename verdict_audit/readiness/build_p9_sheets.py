"""Protocol 9 coding sheets, built in waves while full texts are still arriving.

`init` (once, before any coding) fixes over the whole frame: a random item id per paper and the random 25% of
papers that coder 2 also codes (seed 20261019). Keys stay in data/p9/ (git-ignored); their SHA-256 goes to
results/p9_coding_manifest.json. `wave` assigns papers that have an excerpt and no batch yet to new batches of 20
for coder 1 and, for the coder-2 sample, to new coder-2 batches, in item-id order; earlier batches never change.
`status` lists batches and whether their codes exist and are complete.

`final`, once the download is complete, is `wave` that also adds the last partial batch of each role.

Usage: python build_p9_sheets.py init | wave | final | full2 | full2more | rebuild | status
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from pathlib import Path

from build_p9_excerpts import OUT as EXCERPTS
from fetch_p9 import key_of

HERE = Path(__file__).resolve().parent
P9 = HERE / "data" / "p9"
SHEETS, CODES = P9 / "sheets", HERE / "codes" / "p9"
KEYS, BATCHES = P9 / "keys.json", P9 / "batches.json"
SEED, BATCH, SHARE2 = 20261019, 20, 0.25
FIELDS = ("claims", "code", "main_data_access", "open_data_experiment", "synthetic_or_sample_release",
          "weights_release", "outputs_release", "variance", "environment", "compute", "compute_tier", "data_scale")
LABELS = dict(
    claims=("listed_and_linked", "listed", "none", "unclear"), code=("released", "promised", "no", "unclear"),
    main_data_access=("open", "credentialed_or_request", "private", "synthetic_only", "unclear"),
    open_data_experiment=("yes", "no", "unclear"), synthetic_or_sample_release=("yes", "no", "unclear"),
    weights_release=("yes", "no", "unclear"), outputs_release=("yes", "no", "unclear"), variance=("yes", "no", "unclear"),
    environment=("yes", "no", "unclear"), compute=("amount", "hardware_only", "none", "unclear"),
    compute_tier=("low", "medium", "high", "not_stated"), data_scale=("lt_1e4", "1e4_1e6", "gt_1e6", "not_stated"))


def init() -> None:
    if KEYS.exists():
        raise SystemExit("keys.json exists; ids and the coder-2 sample are drawn once")
    frame = json.loads((HERE / "results" / "p9_frame.json").read_text(encoding="utf-8"))
    keys_sorted = sorted(key_of(p) for p in frame)
    rng = random.Random(SEED)
    order = keys_sorted[:]
    rng.shuffle(order)
    second = set(rng.sample(keys_sorted, round(SHARE2 * len(keys_sorted))))
    by_key = {key_of(p): p for p in frame}
    keys = {f"P{i:04d}": dict(key=k, stratum=by_key[k]["stratum"], forum_id=by_key[k]["forum_id"],
                              group=by_key[k]["group"], title=by_key[k]["title"], coder2=k in second)
            for i, k in enumerate(order)}
    P9.mkdir(parents=True, exist_ok=True)
    KEYS.write_text(json.dumps(keys, ensure_ascii=False), encoding="utf-8")
    BATCHES.write_text(json.dumps(dict(coder1=[], coder2=[])), encoding="utf-8")
    sha = hashlib.sha256(KEYS.read_bytes()).hexdigest()
    (HERE / "results" / "p9_coding_manifest.json").write_text(json.dumps(dict(
        seed=SEED, batch_size=BATCH, coder2_share=SHARE2, items=len(keys), coder2_items=len(second), keys_sha256=sha,
        prompt_sha256=hashlib.sha256((CODES / "CODER_PROMPT.md").read_bytes()).hexdigest()), indent=1), encoding="utf-8")
    print(len(keys), "items;", len(second), "in the coder-2 sample; keys", sha[:12])


def excerpts() -> dict:
    out = {}
    for line in (EXCERPTS / "excerpts.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["status"] == "ok":
            out[r["key"]] = r
    return out


def wave(final: bool = False) -> None:
    """final: the download is complete, so the last partial batch of each role is added too."""
    keys = json.loads(KEYS.read_text(encoding="utf-8"))
    batches = json.loads(BATCHES.read_text(encoding="utf-8"))
    ex = excerpts()
    SHEETS.mkdir(parents=True, exist_ok=True)
    new = {}
    for role, want in (("coder1", lambda v: True), ("coder2", lambda v: v["coder2"])):
        done = {i for b in batches[role] for i in b["items"]}
        todo = sorted(i for i, v in keys.items() if v["key"] in ex and want(v) and i not in done)
        full = len(todo) if final else len(todo) - len(todo) % BATCH  # partial batches wait for the next wave
        for start in range(0, full, BATCH):
            items = todo[start:start + BATCH]
            n = len(batches[role])
            name = f"p9_{role}_batch_{n:03d}"
            with (SHEETS / f"{name}.csv").open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, ["item_id", "title", "truncated", "excerpt"])
                w.writeheader()
                for i in items:
                    r = ex[keys[i]["key"]]
                    w.writerow(dict(item_id=i, title=keys[i]["title"], truncated="yes" if r["truncated"] else "no",
                                    excerpt=r["excerpt"]))
            batches[role].append(dict(batch=n, items=items))
            new.setdefault(role, []).append(n)
    BATCHES.write_text(json.dumps(batches), encoding="utf-8")
    print("new batches:", {r: (v[0], v[-1], len(v)) for r, v in new.items()} or "none")


def full2(more: bool = False) -> None:
    """Note 9-6: coder 2 codes every remaining coded paper (fields below the gate), role coder2full, same prompt.
    more (Note 9-23): append batches for coder-1 papers added since, earlier coder2full batches never change."""
    keys = json.loads(KEYS.read_text(encoding="utf-8"))
    batches = json.loads(BATCHES.read_text(encoding="utf-8"))
    if batches.get("coder2full") and not more:
        raise SystemExit("coder2full batches exist")
    ex = excerpts()
    in1 = {i for b in batches["coder1"] for i in b["items"]}
    in2 = {i for b in batches["coder2"] + batches.get("coder2full", []) for i in b["items"]}
    todo = sorted(in1 - in2)
    batches.setdefault("coder2full", [])
    for n, start in enumerate(range(0, len(todo), BATCH), len(batches["coder2full"])):
        items = todo[start:start + BATCH]
        with (SHEETS / f"p9_coder2full_batch_{n:03d}.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, ["item_id", "title", "truncated", "excerpt"])
            w.writeheader()
            for i in items:
                r = ex[keys[i]["key"]]
                w.writerow(dict(item_id=i, title=keys[i]["title"], truncated="yes" if r["truncated"] else "no",
                                excerpt=r["excerpt"]))
        batches["coder2full"].append(dict(batch=n, items=items))
    BATCHES.write_text(json.dumps(batches), encoding="utf-8")
    print("coder2full batches:", len(batches["coder2full"]), "items:", len(todo))


def rebuild() -> None:
    """Rewrite the sheets of existing batches from the current excerpts (same items, Note 9-3)."""
    keys = json.loads(KEYS.read_text(encoding="utf-8"))
    batches = json.loads(BATCHES.read_text(encoding="utf-8"))
    ex = excerpts()
    for role in ("coder1", "coder2"):
        for b in batches[role]:
            if (CODES / f"p9_{role}_batch_{b['batch']:03d}.csv").exists():
                raise SystemExit(f"{role} batch {b['batch']} is already coded; not rewriting its sheet")
            with (SHEETS / f"p9_{role}_batch_{b['batch']:03d}.csv").open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, ["item_id", "title", "truncated", "excerpt"])
                w.writeheader()
                for i in b["items"]:
                    r = ex[keys[i]["key"]]
                    w.writerow(dict(item_id=i, title=keys[i]["title"], truncated="yes" if r["truncated"] else "no",
                                    excerpt=r["excerpt"]))
    print("rewrote", sum(len(v) for v in batches.values()), "sheets")


def status() -> None:
    batches = json.loads(BATCHES.read_text(encoding="utf-8"))
    for role in [r for r in ("coder1", "coder2", "coder2full") if r in batches]:
        missing, bad = [], []
        for b in batches[role]:
            f = CODES / f"p9_{role}_batch_{b['batch']:03d}.csv"
            if not f.exists():
                missing.append(b["batch"])
                continue
            rows = list(csv.DictReader(f.open(newline="", encoding="utf-8")))
            ok = sorted(r["item_id"] for r in rows) == sorted(b["items"]) and all(
                r.get(k, "").strip() in LABELS[k] for r in rows for k in FIELDS)
            if not ok:
                bad.append(b["batch"])
        print(role, "batches", len(batches[role]), "| missing", len(missing), missing[:40], "| invalid", bad)


if __name__ == "__main__":
    {"init": init, "wave": wave, "final": lambda: wave(final=True), "full2": full2,
     "full2more": lambda: full2(more=True), "rebuild": rebuild,
     "status": status}[sys.argv[1] if len(sys.argv) > 1 else "status"]()
