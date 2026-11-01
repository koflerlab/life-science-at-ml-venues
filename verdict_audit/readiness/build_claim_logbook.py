"""Log every number quoted in the manuscript to a local trackio project, one row per number.

The rows are derived from the number checks in manuscript/build_assets.py (`checks`, `checks_posthoc`): each element
of their `want` lists is one quoted claim. Every element is evaluated on its own against result files wrapped so that
each JSON leaf read is recorded. A row gives the claim text, the result file, the JSON key path, the producing script
and command, and the raw value, so that each claim can be recomputed independently.

Usage: python verdict_audit/readiness/build_claim_logbook.py [--dry-run]
Logs locally only; refuses to run if TRACKIO_SPACE_ID or TRACKIO_SERVER_URL is set.
"""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ASSETS = ROOT / "manuscript" / "build_assets.py"
PROJECT = "p9-manuscript-claims"

# Result file -> script that writes it (verified by grep of the readiness scripts).
PRODUCER = {
    "p9.json": "analyze_p9.py", "p9_areas.json": "posthoc_p9_areas.py",
    "p9_extended.json": "posthoc_p9_extended.py", "p9_claims.json": "analyze_p9_claims.py",
    "p9_adversarial.json": "posthoc_p9_adversarial.py", "p9_ext.json": "analyze_p9_ext.py",
    "p9_more.json": "posthoc_p9_more.py", "p9_empirical.json": "posthoc_p9_empirical.py",
    "p9_posthoc.json": "posthoc_p9.py", "p9_topics.json": "posthoc_p9_topics.py", "p9_axes.json": "posthoc_p9_axes.py",
}
# Arguments of checks() and checks_posthoc() -> result file, as main() in build_assets.py loads them.
ARGS = {
    "checks": dict(p9="p9.json", areas="p9_areas.json", ext="p9_extended.json", claims="p9_claims.json",
                   adv="p9_adversarial.json", ext9="p9_ext.json", more="p9_more.json", emp="p9_empirical.json"),
    "checks_posthoc": dict(top="p9_topics.json", ax="p9_axes.json"),
}


class Tracked:
    """Read-only view of a JSON node that records every leaf read into a shared log."""

    def __init__(self, node, file: str, path: tuple, log: list):
        self._node, self._file, self._path, self._log = node, file, path, log

    def _wrap(self, key, value):
        path = self._path + (key,)
        if isinstance(value, (dict, list)):
            return Tracked(value, self._file, path, self._log)
        self._log.append((self._file, path, value))
        return value

    def __getitem__(self, key):
        return self._wrap(key, self._node[key])

    def __iter__(self):
        # Iterating a list (a confidence interval) reads each element.
        if isinstance(self._node, dict):
            return iter(self._node)
        return (self[i] for i in range(len(self._node)))

    def __len__(self):
        return len(self._node)

    def items(self):
        return ((k, self[k]) for k in self._node)


def key_path(path: tuple) -> str:
    return "".join(f"[{k}]" if isinstance(k, int) else f".{k}" for k in path).lstrip(".")


def function(tree: ast.Module, name: str) -> ast.FunctionDef:
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def rows_for(tree: ast.Module, name: str, assets_ns: dict, results: dict) -> list[dict]:
    fn = function(tree, name)
    log: list = []
    load = lambda f: Tracked(results[f], f, (), log)
    ns = dict(assets_ns, load=load, **{a: load(f) for a, f in ARGS[name].items()})
    want = next(s for s in fn.body if isinstance(s, ast.Assign) and getattr(s.targets[0], "id", None) == "want")
    preamble = ast.Module(body=fn.body[:fn.body.index(want)], type_ignores=[])
    exec(compile(preamble, str(ASSETS), "exec"), ns)
    log.clear()  # the preamble only binds names; reads count from the claims onward
    rows = []
    for i, elt in enumerate(want.value.elts, 1):
        log.clear()
        # Evaluates this repository's own build_assets.py expressions, not external input.
        claim = eval(compile(ast.Expression(elt), str(ASSETS), "eval"), ns)
        if not log:  # a fixed phrase with no number from a result file
            continue
        seen = set()
        for file, path, value in log:
            if (file, path) in seen:
                continue
            seen.add((file, path))
            script = PRODUCER[file]
            rows.append(dict(claim_id=f"{name}:{i:02d}", claim=claim, result_file=f"verdict_audit/readiness/results/{file}",
                             key_path=key_path(path), value=value, script=f"verdict_audit/readiness/{script}",
                             command=f"python verdict_audit/readiness/{script}"))
    return rows


def main() -> None:
    if os.environ.get("TRACKIO_SPACE_ID") or os.environ.get("TRACKIO_SERVER_URL"):
        sys.exit("TRACKIO_SPACE_ID or TRACKIO_SERVER_URL is set; this logbook is local only. Unset it and rerun.")
    sys.path.insert(0, str(ASSETS.parent))
    import build_assets  # noqa: E402  (helpers pct, pts, ci, est and the manuscript TEXT)

    tree = ast.parse(ASSETS.read_text(encoding="utf-8"))
    results = {f: json.loads((HERE / "results" / f).read_text(encoding="utf-8")) for f in PRODUCER}
    rows = [r for name in ARGS for r in rows_for(tree, name, vars(build_assets), results)]
    missing = sorted({r["claim"] for r in rows if r["claim"] not in build_assets.TEXT})
    if missing:
        sys.exit(f"{len(missing)} claims not in manuscript.md; run manuscript/build_assets.py first")
    claims = len({r["claim_id"] for r in rows})
    print(f"{claims} claims, {len(rows)} numbers", file=sys.stderr)
    if "--dry-run" in sys.argv:
        return
    import trackio

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                            check=True).stdout.strip()
    cols = ["claim_id", "claim", "result_file", "key_path", "value", "script", "command"]
    trackio.init(project=PROJECT, name=f"claims-{commit}", config=dict(commit=commit, claims=claims, numbers=len(rows)),
                 auto_log_cpu=False, auto_log_gpu=False)
    trackio.log({"claims": trackio.Table(columns=cols, data=[[str(r[c]) for c in cols] for r in rows]),
                 "n_claims": claims, "n_numbers": len(rows)})
    trackio.finish()
    print(f"logged to local trackio project {PROJECT!r}, run claims-{commit}", file=sys.stderr)


if __name__ == "__main__":
    main()
