"""Note 9-23 (post hoc, exploratory): do papers recovered from proceedings, OpenReview or OpenAlex document
differently from papers of the first retrieval (mostly arXiv)? And the A9.3 estimates on the first-retrieval papers
only (sensitivity analysis), read from the committed p9.json of commit 092e8a5.

Per A9.3 indicator and group: Mantel-Haenszel risk difference, recovered minus first retrieval, over venue-year
strata, with the A9.3 paper bootstrap (2,000 resamples within stratum x recovered cells, seed 20261017).

Usage: python posthoc_p9_recovery.py   -> results/p9_recovery.json
"""
from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

from analyze_p9 import INDICATOR, boot_ci, final_codes, mh_rd
from build_p9_sheets import KEYS
from fetch_p9 import MANIFEST, RECOVERY

HERE = Path(__file__).resolve().parent
FIRST_COMMIT = "092e8a5"


def recovered_keys() -> set[str]:
    last = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        last[r["key"]] = r
    return {k for k, r in last.items() if r["status"] == "ok" and r.get("recovery") == RECOVERY}


def main() -> dict:
    keys = json.loads(KEYS.read_text(encoding="utf-8"))
    final, rec = final_codes(), recovered_keys()
    papers = [dict(group=keys[i]["group"], stratum=keys[i]["stratum"], recovered=keys[i]["key"] in rec, **final[i])
              for i in sorted(final)]
    out = dict(note="9-23", post_hoc=True, coded=dict(Counter((p["group"], p["recovered"]) for p in papers).items()),
               by_field={})
    out["coded"] = {f"{g}|{'recovered' if r else 'first'}": n for (g, r), n in sorted(out["coded"].items())}
    for f, pos in INDICATOR.items():
        out["by_field"][f] = {}
        for g in ("life_science", "other"):
            rows = [(p["stratum"], p["recovered"], int(p[f] == pos)) for p in papers if p["group"] == g and p[f] != "unclear"]
            share = lambda r: (sum(x[2] for x in rows if x[1] == r) / max(1, sum(x[1] == r for x in rows)))
            out["by_field"][f][g] = dict(n_recovered=sum(r[1] for r in rows), n_first=sum(not r[1] for r in rows),
                                         share_recovered=share(True), share_first=share(False),
                                         mh_rd=mh_rd(rows), mh_ci=boot_ci(rows, mh_rd))
    first = json.loads(subprocess.check_output(
        ["git", "show", f"{FIRST_COMMIT}:verdict_audit/readiness/results/p9.json"], cwd=HERE, text=True))
    out["first_retrieval_A9_3"] = {f: dict(mh_rd=first["A9_3"][f].get("mh_rd"), mh_ci=first["A9_3"][f].get("mh_ci"))
                                   for f in INDICATOR}
    out["first_retrieval_labels"] = first["labels"]
    (HERE / "results" / "p9_recovery.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1)[:4000])
