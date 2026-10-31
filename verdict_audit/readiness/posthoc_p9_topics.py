"""Note 9-24 (post hoc, descriptive): topics of the 2,170 medical papers by venue, and a t-SNE map of their abstracts.

`embed`: SPECTER2 base CLS embeddings of title [SEP] abstract and a 2-D t-SNE (cosine, perplexity 30, PCA init,
random_state 20261101). Embeddings and coordinates stay under DATA_ROOT (derived/, never in git); the model revision
and a hash of the coordinates go to results/p9_topics_map.json.
`run`: T1 to T5 from codes/p9/topics/topics_final.csv -> results/p9_topics.json (needs `embed` for nothing; T4
needs the Note 9-23 coding complete).

Usage: python posthoc_p9_topics.py embed | run
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from analyze_p8 import wilson
from build_p9_topics import CODES as TOPIC_CODES, KEYS as TOPIC_KEYS, TOPICS
from fetch_p9 import DS

HERE = Path(__file__).resolve().parent
MAP_DIR = DS / "derived" / "topics-map-v1"
MODEL, SEED, PERPLEXITY = "allenai/specter2_base", 20261101, 30
VENUES = ("cvpr", "iccv", "eccv", "iclr", "icml", "neurips")
INDICATORS = dict(code="released", main_data_access="open", weights_release="yes", variance="yes")
RESIDUAL = 3.0


def topic_rows() -> list[dict]:
    keys = json.loads(TOPIC_KEYS.read_text(encoding="utf-8"))
    final = {r["item_id"]: r["topic"] for r in csv.DictReader((TOPIC_CODES / "topics_final.csv").open(encoding="utf-8"))}
    return [dict(item=i, stratum=k["stratum"], venue=k["stratum"].rsplit("-", 1)[0], year=k["stratum"][-4:],
                 forum_id=k["forum_id"], label=k["label"], topic=final[i]) for i, k in sorted(keys.items())]


def embed() -> None:
    import torch
    from huggingface_hub import model_info
    from sklearn.manifold import TSNE
    from transformers import AutoModel, AutoTokenizer
    keys = json.loads(TOPIC_KEYS.read_text(encoding="utf-8"))
    items = sorted(keys)
    rev = model_info(MODEL).sha
    tok = AutoTokenizer.from_pretrained(MODEL, revision=rev)
    model = AutoModel.from_pretrained(MODEL, revision=rev).eval()
    texts = [keys[i]["title"] + tok.sep_token + keys[i]["abstract"] for i in items]
    vecs = []
    with torch.no_grad():
        for s in range(0, len(texts), 16):
            enc = tok(texts[s:s + 16], padding=True, truncation=True, max_length=512, return_tensors="pt")
            vecs.append(model(**enc).last_hidden_state[:, 0, :].numpy())
            print(f"{min(s + 16, len(texts))}/{len(texts)}", end="\r", flush=True)
    emb = np.concatenate(vecs)
    xy = TSNE(n_components=2, metric="cosine", perplexity=PERPLEXITY, init="pca", random_state=SEED).fit_transform(emb)
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    np.save(MAP_DIR / "embeddings.npy", emb)
    with (MAP_DIR / "tsne.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(("item_id", "x", "y"))
        w.writerows((i, f"{a:.5f}", f"{b:.5f}") for i, (a, b) in zip(items, xy))
    (HERE / "results" / "p9_topics_map.json").write_text(json.dumps(dict(
        note="9-24", model=MODEL, revision=rev, pooling="CLS", max_length=512, tsne=dict(
            metric="cosine", perplexity=PERPLEXITY, init="pca", random_state=SEED), n=len(items),
        tsne_sha256=hashlib.sha256((MAP_DIR / "tsne.csv").read_bytes()).hexdigest()), indent=1), encoding="utf-8")
    print("\nembedded", len(items), "with", MODEL, rev[:10])


def shares(rows: list[dict], by) -> dict:
    out = {}
    for g in sorted({by(r) for r in rows}):
        sel = [r for r in rows if by(r) == g]
        c = Counter(r["topic"] for r in sel)
        out[g] = dict(n=len(sel), topics={t: dict(n=c[t], share=c[t] / len(sel), wilson=wilson(c[t], len(sel)))
                                          for t in TOPICS})
    return out


def chi2_venue(rows: list[dict]) -> dict:
    from scipy.stats import chi2_contingency
    tab = np.array([[sum(r["venue"] == v and r["topic"] == t for r in rows) for t in TOPICS] for v in VENUES])
    keep = tab.sum(0) > 0
    tab = tab[:, keep]
    topics = [t for t, k in zip(TOPICS, keep) if k]
    chi2, p, dof, exp = chi2_contingency(tab)
    n, rs, cs = tab.sum(), tab.sum(1, keepdims=True), tab.sum(0, keepdims=True)
    adj = (tab - exp) / np.sqrt(exp * (1 - rs / n) * (1 - cs / n))
    cells = {v: {t: round(float(adj[a, b]), 2) for b, t in enumerate(topics)} for a, v in enumerate(VENUES)}
    flags = [dict(venue=v, topic=t, residual=r, direction="over" if r > 0 else "under")
             for v, d in cells.items() for t, r in d.items() if abs(r) >= RESIDUAL]
    return dict(chi2=float(chi2), dof=int(dof), p=float(p), min_expected=float(exp.min()),
                adjusted_residuals=cells, flagged=sorted(flags, key=lambda f: -abs(f["residual"])))


def practices(rows: list[dict]) -> dict:
    from analyze_p9 import final_codes
    from build_p9_sheets import KEYS
    keys = json.loads(KEYS.read_text(encoding="utf-8"))
    codes = {(keys[i]["stratum"], keys[i]["forum_id"]): c for i, c in final_codes().items()}
    out = {}
    for t in TOPICS:
        sel = [codes[(r["stratum"], r["forum_id"])] for r in rows if r["topic"] == t and (r["stratum"], r["forum_id"]) in codes]
        e = dict(n_coded=len(sel))
        for f, pos in INDICATORS.items():
            known = [c[f] for c in sel if c[f] != "unclear"]
            k = sum(x == pos for x in known)
            e[f] = dict(n_known=len(known), share=k / len(known) if known else None, wilson=wilson(k, len(known)))
        out[t] = e
    return out


def icml_attempts(rows: list[dict]) -> dict:
    sys.path.insert(0, str(HERE))
    import p8_common as P8
    cv = P8.claim_verdicts()
    out = {}
    for t in TOPICS:
        sel = [r for r in rows if r["topic"] == t and r["stratum"] == "icml-2026"]
        att = [r for r in sel if r["forum_id"] in cv]
        dec = sum(any(c["verdict"] in P8.DECISIVE for c in cv[r["forum_id"]]) for r in att)
        out[t] = dict(icml2026=len(sel), attempted=len(att), decided=dec,
                      decided_share=dec / len(att) if att else None, wilson=wilson(dec, len(att)))
    return out


def run() -> dict:
    rows = topic_rows()
    agreement = json.loads((HERE / "results" / "p9_topics_agreement.json").read_text(encoding="utf-8"))
    res = dict(note="9-24", post_hoc=True, n=len(rows), agreement=agreement,
               overall={t: dict(n=c, share=c / len(rows)) for t, c in sorted(Counter(r["topic"] for r in rows).items(),
                                                                          key=lambda x: -x[1])},
               by_label={lab: dict(Counter(r["topic"] for r in rows if r["label"] == lab)) for lab in ("clinical", "life_science")},
               T1_by_venue=shares(rows, lambda r: r["venue"]), T1_by_venue_year=shares(rows, lambda r: r["stratum"]),
               T2_venue_by_topic=chi2_venue(rows), T3_by_year=shares(rows, lambda r: r["year"]),
               T4_practices=practices(rows), T5_icml2026=icml_attempts(rows))
    (HERE / "results" / "p9_topics.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "embed":
        embed()
    else:
        r = run()
        print(json.dumps(dict(n=r["n"], agreement=r["agreement"], overall=r["overall"],
                              flagged=r["T2_venue_by_topic"]["flagged"]), indent=1))
