import fetch_p9 as F

ATOM = """<feed><entry><id>http://arxiv.org/abs/2501.01234v2</id><published>2025-01-03T00:00:00Z</published>
<title>Deterministic Image-to-Image Translation via
  Denoising Brownian Bridge Models</title></entry>
<entry><id>http://arxiv.org/abs/1901.00001v1</id><published>2019-01-01T00:00:00Z</published>
<title>Deterministic Image-to-Image Translation via Denoising Brownian Bridge Models</title></entry></feed>"""


def test_norm_and_parse_atom():
    assert F.norm("Image-to-Image: A &amp; B — Café") == "image to image a b cafe"
    e = F.parse_atom(ATOM)
    assert [x["id"] for x in e] == ["2501.01234", "1901.00001"] and e[0]["year"] == 2025


def test_pick_rules():
    title = "Deterministic Image-to-Image Translation via Denoising Brownian Bridge Models"
    entries = F.parse_atom(ATOM)
    assert F.pick(entries, title, 2025)[:2] == ("ok", "2501.01234")  # the 2019 entry fails the year rule
    twin = entries + [dict(id="2502.09999", title=entries[0]["title"], year=2025)]
    assert F.pick(twin, title, 2025)[0] == "ambiguous"
    assert F.pick(entries, "A completely different paper", 2025)[0] == "no_match"


def test_parse_pmlr_and_cvf():
    pmlr = ('<div class="paper"><p class="title">T</p><p class="links">[<a href="https://raw.githubusercontent.com/'
            'mlresearch/v306/main/assets/x26a/x26a.pdf">Download PDF</a>][<a href="https://openreview.net/forum?id=YDz-tz_1">'
            'OpenReview</a>]</p></div>')
    assert F.parse_pmlr(pmlr, "https://proceedings.mlr.press/v306/") == {
        "YDz-tz_1": "https://raw.githubusercontent.com/mlresearch/v306/main/assets/x26a/x26a.pdf"}
    cvf = '<dt class="ptitle"><br><a href="/content/CVPR2025/html/X_CVPR_2025_paper.html">Deep Thing: A Study</a></dt>'
    assert F.parse_cvf(cvf, "https://openaccess.thecvf.com/CVPR2025?day=all") == {
        "deep thing a study": "https://openaccess.thecvf.com/content/CVPR2025/papers/X_CVPR_2025_paper.pdf"}


def test_key_is_path_safe():
    assert F.key_of(dict(stratum="cvpr-2025", forum_id="src:10379")) == "cvpr-2025__src-10379"


def test_wave_holds_partial_batches_until_final(tmp_path, monkeypatch):
    import json
    import build_p9_sheets as S
    keys = {f"P{i:04d}": dict(key=f"k{i}", title=f"t{i}", coder2=i < 3) for i in range(45)}
    (tmp_path / "keys.json").write_text(json.dumps(keys))
    (tmp_path / "batches.json").write_text(json.dumps(dict(coder1=[], coder2=[])))
    monkeypatch.setattr(S, "KEYS", tmp_path / "keys.json")
    monkeypatch.setattr(S, "BATCHES", tmp_path / "batches.json")
    monkeypatch.setattr(S, "SHEETS", tmp_path / "sheets")
    monkeypatch.setattr(S, "excerpts", lambda: {f"k{i}": dict(truncated=False, excerpt="x") for i in range(45)})
    S.wave()
    b = json.loads((tmp_path / "batches.json").read_text())
    assert [len(x["items"]) for x in b["coder1"]] == [20, 20] and b["coder2"] == []
    S.wave(final=True)
    b = json.loads((tmp_path / "batches.json").read_text())
    assert [len(x["items"]) for x in b["coder1"]] == [20, 20, 5] and [len(x["items"]) for x in b["coder2"]] == [3]
    assert len({i for x in b["coder1"] for i in x["items"]}) == 45


def test_full2more_appends_only_new_papers(tmp_path, monkeypatch):
    import json
    import build_p9_sheets as S
    keys = {f"P{i:04d}": dict(key=f"k{i}", title=f"t{i}") for i in range(30)}
    batches = dict(coder1=[dict(batch=0, items=[f"P{i:04d}" for i in range(20)])],
                   coder2=[dict(batch=0, items=["P0000", "P0001"])])
    (tmp_path / "keys.json").write_text(json.dumps(keys))
    (tmp_path / "batches.json").write_text(json.dumps(batches))
    monkeypatch.setattr(S, "KEYS", tmp_path / "keys.json")
    monkeypatch.setattr(S, "BATCHES", tmp_path / "batches.json")
    monkeypatch.setattr(S, "SHEETS", tmp_path)
    monkeypatch.setattr(S, "excerpts", lambda: {f"k{i}": dict(truncated=False, excerpt="x") for i in range(30)})
    S.full2()
    first = json.loads((tmp_path / "batches.json").read_text())["coder2full"]
    b = json.loads((tmp_path / "batches.json").read_text())
    b["coder1"].append(dict(batch=1, items=[f"P{i:04d}" for i in range(20, 30)]))
    (tmp_path / "batches.json").write_text(json.dumps(b))
    S.full2(more=True)
    full = json.loads((tmp_path / "batches.json").read_text())["coder2full"]
    assert full[:len(first)] == first and [x["batch"] for x in full] == list(range(len(full)))
    got = [i for x in full for i in x["items"]]
    assert sorted(got) == [f"P{i:04d}" for i in range(2, 30)] and len(got) == len(set(got))


def test_mh_rd_matches_hand_computation():
    from analyze_p9 import mh_rd
    rows = [("a", True, 1)] * 3 + [("a", True, 0)] + [("a", False, 1)] + [("a", False, 0)] * 3 \
        + [("b", True, 1)] * 2 + [("b", False, 0)] * 2 + [("c", True, 1)]  # stratum c has one group only
    # a: 0.75 - 0.25, weight 4*4/8 = 2; b: 1.0 - 0.0, weight 2*2/4 = 1 -> (2*0.5 + 1*1.0) / 3
    assert abs(mh_rd(rows) - 2 / 3) < 1e-12


def test_p9_label_set_matches_the_coder_prompt():
    import build_p9_sheets as S
    prompt = (S.CODES / "CODER_PROMPT.md").read_text(encoding="utf-8")
    header = "item_id," + ",".join(S.FIELDS)
    assert header in prompt
    for field, labels in S.LABELS.items():
        for lab in labels:
            assert lab in prompt, (field, lab)


def test_p9_release_table_is_publishable_and_matches_results():
    import csv
    import json
    from collections import Counter
    from analyze_p9 import INDICATOR
    import build_p9_release as R
    rows = list(csv.DictReader(R.OUT.open(encoding="utf-8")))
    assert tuple(rows[0]) == R.COLUMNS
    assert not {"abstract", "text", "excerpt", "url", "media_urls"} & set(R.COLUMNS)  # no listing or full-text content
    assert Counter(r["group"] for r in rows) == {"life_science": 2170, "other": 2170}
    res = json.loads((R.HERE / "results" / "p9.json").read_text(encoding="utf-8"))
    assert Counter(r["group"] for r in rows if r["code"]) == res["coded"]
    for field, pos in INDICATOR.items():
        for g in ("life_science", "other"):
            known = [r for r in rows if r["group"] == g and r[field] and r[field] != "unclear"]
            share = sum(r[field] == pos for r in known) / len(known)
            assert abs(share - res["A9_3"][field][g]["share"]) < 1e-12, (field, g)


def test_note_9_22_results_match_the_release_table():
    import csv
    import json
    import build_p9_release as R
    rows = [r for r in csv.DictReader(R.OUT.open(encoding="utf-8")) if r["code"]]
    res = json.loads((R.HERE / "results" / "p9_empirical.json").read_text(encoding="utf-8"))
    emp = [r for r in rows if r["data_scale"] != "not_stated"]
    assert res["E_a"]["units"] == {"medical": sum(r["group"] == "life_science" for r in emp),
                                   "other": sum(r["group"] == "other" for r in emp)}
    for field, pos in (("main_data_access", "open"), ("weights_release", "yes")):  # unclear counted as no
        for g, key in (("life_science", "medical"), ("other", "other")):
            sel = [r for r in rows if r["group"] == g]
            share = sum(r[field] == pos for r in sel) / len(sel)
            assert abs(share - res["E_b"][field]["share"][key]) < 1e-12, (field, g)


def test_axes_architecture_sets_are_canonical_and_exclusive():
    import build_p9_axes as A
    assert A.norm_arch("transformer; cnn") == "cnn;transformer"
    assert A.norm_arch("cnn,cnn") == "cnn"
    assert A.norm_arch("not_stated") == "not_stated"
    assert A.norm_arch("cnn;not_stated") is None and A.norm_arch("no_model;gp_kernel") is None
    assert A.norm_arch("resnet") is None and A.norm_arch("") is None
    assert A.valid("method", " theory ") == "theory" and A.valid("modality", "pixels") is None


def test_axes_agreement_scores_architecture_per_label():
    import build_p9_axes as A
    a = {"X1": dict(modality="image", method="theory", architecture="cnn;transformer"),
         "X2": dict(modality="text", method="theory", architecture="llm_vlm")}
    b = {"X1": dict(modality="image", method="theory", architecture="cnn"),
         "X2": dict(modality="image", method="theory", architecture="llm_vlm")}
    ag = A.agreement(a, b, A.PASS["a"]["axes"])
    assert ag["modality"]["n_disagreements"] == 1 and ag["method"]["raw"] == 1.0
    k = ag["architecture"]["per_label_kappa"]
    assert k["cnn"] == 1.0 and k["transformer"] == 0.0 and k["llm_vlm"] == 1.0 and ag["architecture"]["n_disagreements"] == 1


def test_claim_logbook_rows_point_at_their_values():
    import ast
    import json
    import sys

    import build_claim_logbook as B
    sys.path.insert(0, str(B.ASSETS.parent))
    import build_assets

    tree = ast.parse(B.ASSETS.read_text(encoding="utf-8"))
    results = {f: json.loads((B.HERE / "results" / f).read_text(encoding="utf-8")) for f in B.PRODUCER}
    rows = [r for name in B.ARGS for r in B.rows_for(tree, name, vars(build_assets), results)]
    assert rows and all(r["claim"] in build_assets.TEXT for r in rows)
    for r in rows:
        node = results[r["result_file"].rsplit("/", 1)[1]]
        for k in r["key_path"].replace("[", ".[").split("."):
            node = node[int(k[1:-1])] if k.startswith("[") else node[k]
        assert node == r["value"] and (B.HERE / r["script"].rsplit("/", 1)[1]).exists()
    # X5 headline: open main data within data-type strata is among the logged numbers
    assert any(r["key_path"] == "X5.main_data_access.venue_year_x_modality.mh_rd" for r in rows)
