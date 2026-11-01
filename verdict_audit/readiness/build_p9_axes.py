"""Note 9-26 axes (modality, method, architecture) of all 4,340 frame papers: sheets, agreement, adjudication, finals.

Pass A codes the three axes from title and abstract; pass B recodes architecture from the full-text excerpt for papers
whose pass-A architecture is `not_stated`. `sheets` (once) draws item ids X0000... (seed 20261102) and writes blind
pass-A sheets of 50 to data/p9/axes_sheets/; keys stay in data/p9/axes_keys.json (git-ignored, SHA-256 in
results/p9_axes_manifest.json). `status a|b` checks coder files. `adj a|b` scores agreement and writes the
disagreements, one row per item and axis with the answers in random order. `final_a` writes
codes/p9/axes/axes_a_final.csv; `sheets_b` writes the pass-B sheets of 20 from it; `final` writes
codes/p9/axes/axes_final.csv.

Usage: python build_p9_axes.py sheets | status a|b | adj a|b | final_a | sheets_b | final
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
CODES = HERE / "codes" / "p9" / "axes"
KEYS = P9 / "axes_keys.json"
SEED = 20261102
PASS = dict(a=dict(sheets=P9 / "axes_sheets", adj=P9 / "axes_adj_sheets", roles=("axes1", "axes2"), batch=50,
                   adj_role="axesadj", axes=("modality", "method", "architecture")),
            b=dict(sheets=P9 / "axes_b_sheets", adj=P9 / "axes_b_adj_sheets", roles=("axes1b", "axes2b"), batch=20,
                   adj_role="axesadjb", axes=("architecture",)))
MODALITY = ("image", "volumetric", "video", "geometry_3d", "text", "audio_speech", "tabular_records", "time_series",
            "biological_sequence", "omics_matrix", "graph_molecule", "interactive_environment", "multimodal",
            "none_or_synthetic")
METHOD = ("supervised_prediction", "generative_modeling", "representation_learning", "causal_inference_trials",
          "biostatistics_inference", "uncertainty_calibration", "reinforcement_decision", "llm_prompting_agents",
          "optimization_efficiency", "trustworthy_ml", "theory", "benchmark_dataset", "other")
ARCH = ("cnn", "transformer", "llm_vlm", "gnn_equivariant", "diffusion_flow", "state_space_rnn", "other_neural",
        "gp_kernel", "classical_ml")
ARCH_ALONE = ("not_stated", "no_model")
LABELS = dict(modality=MODALITY, method=METHOD, architecture=ARCH + ARCH_ALONE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, header: tuple, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def norm_arch(value: str) -> str | None:
    """Canonical ';'-joined architecture set, or None if invalid (unknown label, or not_stated/no_model not alone)."""
    parts = sorted({p.strip() for p in value.replace(",", ";").split(";") if p.strip()})
    if not parts or any(p not in LABELS["architecture"] for p in parts):
        return None
    if len(parts) > 1 and set(parts) & set(ARCH_ALONE):
        return None
    return ";".join(parts)


def valid(axis: str, value: str) -> str | None:
    value = value.strip()
    if axis == "architecture":
        return norm_arch(value)
    return value if value in LABELS[axis] else None


def keys() -> dict:
    return json.loads(KEYS.read_text(encoding="utf-8"))


def sheets() -> None:
    if KEYS.exists():
        raise SystemExit("axes keys exist; sheets are drawn once")
    frame = json.loads((HERE / "results" / "p9_frame.json").read_text(encoding="utf-8"))
    papers = {(p["stratum"], p["forum_id"]): p for p in json.loads((HERE / "data" / "papers.json").read_text(encoding="utf-8"))}
    units = sorted(frame, key=lambda u: (u["stratum"], u["forum_id"]))
    random.Random(SEED).shuffle(units)
    out = {}
    for i, u in enumerate(units):
        p = papers[(u["stratum"], u["forum_id"])]
        out[f"X{i:04d}"] = dict(stratum=u["stratum"], forum_id=u["forum_id"], group=u["group"], label=u.get("label"),
                                title=p["title"], abstract=" ".join((p.get("abstract") or "").split()))
    KEYS.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    items, n = sorted(out), PASS["a"]["batch"]
    for b in range(-(-len(items) // n)):
        rows = [(i, out[i]["title"], out[i]["abstract"]) for i in items[b * n:(b + 1) * n]]
        for role in PASS["a"]["roles"]:
            write_csv(PASS["a"]["sheets"] / f"p9_{role}_batch_{b:03d}.csv", ("item_id", "title", "abstract"), rows)
    (HERE / "results" / "p9_axes_manifest.json").write_text(json.dumps(dict(
        note="9-26", seed=SEED, batch=n, n_items=len(items), keys_sha256=sha(KEYS),
        prompt_sha256=sha(CODES / "AXES_PROMPT.md")), indent=1), encoding="utf-8")
    print(len(items), "items,", -(-len(items) // n), "batches per coder")


def sheet_items(p: str, role: str) -> dict[str, set]:
    return {f.name: {r["item_id"] for r in csv.DictReader(f.open(encoding="utf-8"))}
            for f in sorted(PASS[p]["sheets"].glob(f"p9_{role}_batch_*.csv"))}


def read_role(p: str, role: str) -> dict:
    """item_id -> {axis: canonical value or None}."""
    out = {}
    for f in sorted(CODES.glob(f"p9_{role}_batch_*.csv")):
        for r in csv.DictReader(f.open(encoding="utf-8")):
            out[r["item_id"]] = {a: valid(a, r.get(a) or "") for a in PASS[p]["axes"]}
    return out


def status(p: str) -> dict:
    res = {}
    for role in PASS[p]["roles"]:
        missing, invalid = [], []
        got = read_role(p, role)
        for name, want in sheet_items(p, role).items():
            f = CODES / name
            if not f.exists():
                missing.append(name[-7:-4])
                continue
            rows = {r["item_id"] for r in csv.DictReader(f.open(encoding="utf-8"))}
            if rows != want or any(v is None for i in want for v in got[i].values()):
                invalid.append(name[-7:-4])
        res[role] = dict(missing=missing, invalid=invalid)
        print(role, "sheets", len(sheet_items(p, role)), "| missing", len(missing), missing[:30], "| invalid", invalid)
    return res


def kappa(pairs: list[tuple], labels) -> float | None:
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == t for a, _ in pairs) / n) * (sum(b == t for _, b in pairs) / n) for t in labels)
    return None if pe == 1 else (po - pe) / (1 - pe)


def agreement(a: dict, b: dict, axes) -> dict:
    items = sorted(set(a) & set(b))
    out = dict(n=len(items))
    for ax in axes:
        pairs = [(a[i][ax], b[i][ax]) for i in items]
        e = dict(raw=round(sum(x == y for x, y in pairs) / len(pairs), 4), n_disagreements=sum(x != y for x, y in pairs))
        if ax == "architecture":
            e["per_label_kappa"] = {}
            for lab in LABELS[ax]:
                bp = [(lab in x.split(";"), lab in y.split(";")) for x, y in pairs]
                k = kappa(bp, (True, False))
                e["per_label_kappa"][lab] = None if k is None else round(k, 4)
        else:
            k = kappa(pairs, LABELS[ax])
            e["kappa"] = None if k is None else round(k, 4)
        out[ax] = e
    return out


def text_of(p: str) -> dict:
    """item_id -> (title, text) shown to adjudicators: the abstract (pass A) or the excerpt (pass B)."""
    k = keys()
    if p == "a":
        return {i: (v["title"], v["abstract"]) for i, v in k.items()}
    out = {}
    for f in sorted(PASS["b"]["sheets"].glob(f"p9_{PASS['b']['roles'][0]}_batch_*.csv")):
        for r in csv.DictReader(f.open(encoding="utf-8")):
            out[r["item_id"]] = (r["title"], r["excerpt"])
    return out


def adj(p: str) -> None:
    st = status(p)
    if any(v["missing"] or v["invalid"] for v in st.values()):
        raise SystemExit("coder files incomplete")
    r1, r2 = (read_role(p, r) for r in PASS[p]["roles"])
    ag = agreement(r1, r2, PASS[p]["axes"])
    rng, txt, rows = random.Random(SEED), text_of(p), []
    for i in sorted(r1):
        for ax in PASS[p]["axes"]:
            if r1[i][ax] != r2[i][ax]:
                x, y = (r1[i][ax], r2[i][ax]) if rng.random() < 0.5 else (r2[i][ax], r1[i][ax])
                rows.append((i, ax, x, y, *txt[i]))
    n = PASS[p]["batch"]
    for b, s in enumerate(range(0, len(rows), n)):
        write_csv(PASS[p]["adj"] / f"p9_{PASS[p]['adj_role']}_batch_{b:03d}.csv",
                  ("item_id", "axis", "answer_a", "answer_b", "title", "text"), rows[s:s + n])
    (HERE / "results" / f"p9_axes_agreement_{p}.json").write_text(json.dumps(ag, indent=1), encoding="utf-8")
    print(json.dumps(ag), "->", -(-len(rows) // n), "adjudication batches")


def decided(p: str) -> dict:
    out = {}
    for f in sorted(CODES.glob(f"p9_{PASS[p]['adj_role']}_batch_*.csv")):
        for r in csv.DictReader(f.open(encoding="utf-8")):
            out[(r["item_id"], r["axis"])] = valid(r["axis"], r["answer"])
    return out


def resolve(p: str) -> dict:
    r1, r2 = (read_role(p, r) for r in PASS[p]["roles"])
    dec, out = decided(p), {}
    for i in sorted(r1):
        out[i] = {}
        for ax in PASS[p]["axes"]:
            v = r1[i][ax] if r1[i][ax] == r2[i][ax] else dec.get((i, ax))
            if v is None:
                raise SystemExit(f"{i} {ax}: no valid final answer")
            out[i][ax] = v
    return out


def final_a() -> None:
    res = resolve("a")
    if set(res) != set(keys()):
        raise SystemExit("pass A does not cover every item")
    write_csv(CODES / "axes_a_final.csv", ("item_id", "modality", "method", "architecture"),
              [(i, v["modality"], v["method"], v["architecture"]) for i, v in res.items()])
    print(len(res), "pass-A finals;", sum(v["architecture"] == "not_stated" for v in res.values()), "not_stated")


def sheets_b() -> None:
    from build_p9_sheets import excerpts
    from fetch_p9 import key_of
    if any(PASS["b"]["sheets"].glob("*.csv")):
        raise SystemExit("pass-B sheets exist")
    k, ex = keys(), excerpts()
    fa = {r["item_id"]: r for r in csv.DictReader((CODES / "axes_a_final.csv").open(encoding="utf-8"))}
    todo = [i for i in sorted(fa) if fa[i]["architecture"] == "not_stated" and key_of(k[i]) in ex]
    n = PASS["b"]["batch"]
    for b, s in enumerate(range(0, len(todo), n)):
        rows = [(i, k[i]["title"], ex[key_of(k[i])]["excerpt"]) for i in todo[s:s + n]]
        for role in PASS["b"]["roles"]:
            write_csv(PASS["b"]["sheets"] / f"p9_{role}_batch_{b:03d}.csv", ("item_id", "title", "excerpt"), rows)
    print(len(todo), "pass-B items,", -(-len(todo) // n), "batches per coder")


def final() -> None:
    fa = {r["item_id"]: r for r in csv.DictReader((CODES / "axes_a_final.csv").open(encoding="utf-8"))}
    fb = resolve("b") if any(PASS["b"]["sheets"].glob("*.csv")) else {}
    rows = [(i, v["modality"], v["method"], fb[i]["architecture"] if i in fb else v["architecture"],
             "b" if i in fb else "a") for i, v in sorted(fa.items())]
    write_csv(CODES / "axes_final.csv", ("item_id", "modality", "method", "architecture", "architecture_pass"), rows)
    print(len(rows), "finals;", len(fb), "architectures from pass B")


if __name__ == "__main__":
    mode, arg = (sys.argv + ["status", "a"])[1:3]
    fn = dict(sheets=sheets, status=status, adj=adj, final_a=final_a, sheets_b=sheets_b, final=final)[mode]
    fn(arg) if mode in ("status", "adj") else fn()
