# Protocol 7: reproduction readiness of medical papers across ML venues

Frozen 2026-10-18, approved by Kate in chat, before any venue file is
downloaded for analysis, any paper is labelled, and any readiness share is
computed. Git commit is the provenance. Part of the PSE9 abstract
"Unfalsifiable by default: medical papers in the ICML 2026 agent reproduction
challenge". Companion to protocols 3 (release audits), 4 (adjusted verdict
gap) and 6 (decidability) in `verdict_audit/`.

## Status of the evidence

Protocol 6 showed that medical ICML 2026 papers were attempted as often as
others but rarely decided, and protocol 4 that the judge was not harsher on
them within team and claim type. This protocol tests one mechanism outside the
challenge: are medical papers, at several venues, released in a form that a
third party can reproduce? Before freezing, only the structure of the sources
was inspected (field names, topic vocabularies, one record); no readiness
share was computed for any group.

## Sources (downloaded once, SHA-256 recorded in `results/manifest.json`)

* Conference virtual-site files `https://{venue}.cc/static/virtual/data/{venue}-{year}-orals-posters.json`
  for ICLR 2025, ICLR 2026, NeurIPS 2024, NeurIPS 2025, ICML 2025, ICML 2026.
* RECLAIM benchmark, dataset `Mithilss/reclaim`, revision
  `59099a8ececf954665dff90a41ad8541e3b21291`, file `eval_100.jsonl`; and the
  RECLAIM code repository `https://github.com/mithils3/reclaim` at the commit
  current on download (recorded).
* ICML 2026 challenge verdicts: `data/verdicts_confirmation_2026-10-17/verdicts.json`
  (dataset revision `f0c5a8b369d6d618ecc9fa060aa2e2f27f9e2602`, SHA-256
  `652f1c16…`), deduplicated as in protocol 1.
* Abstracts for RECLAIM papers from the arXiv API by the `custom_id` arXiv id.

Raw files go to `verdict_audit/readiness/data/` (git-ignored; they contain
author names). Only aggregates and per-paper labels keyed by OpenReview or
arXiv id are committed.

## Unit

One accepted paper per venue-year: items with `eventtype` Poster or Oral,
deduplicated by the OpenReview forum id in `paper_url` (else `sourceid`).
Items without an abstract are excluded and counted. Strata: the six
venue-years.

## Medical label

* Candidate if either holds:
  - `topic` is one of: `Applications->Health`, `Applications->Health / Medicine`,
    `Applications->Genetics, Cell Biology, Health, etc`,
    `Applications->Genetics, Cell Biology, etc`,
    `Applications->Neuroscience, Cognitive Science`,
    `Neuroscience, Cognitive Science`, `Computational Biology`,
    `Applications->Chemistry and Drug Discovery`;
  - title or abstract matches, case-insensitive, the regex
    `\b(patients?|clinical\w*|clinicians?|hospitals?|EHRs?|electronic health records?|medical|medicine|diseases?|diagnos\w*|prognos\w*|radiolog\w*|patholog\w*|histopatholog\w*|MRI|fMRI|CT scans?|X-rays?|ultrasound|ECG|EEG|surg\w*|cancers?|tumou?rs?|oncolog\w*|cardi\w*|alzheimer\w*|dementia|ICU|MIMIC\w*|sepsis|drugs?|pharmac\w*|therap\w*|health ?care|public health|epidemi\w*|biomedic\w*|proteins?|genes?|genom\w*|transcriptom\w*|single-cell|scRNA\w*|DNA|RNA|molecul\w*|enzymes?|antibod\w*|peptides?|biolog\w*|neurons?|neuroscien\w*|brain)\b`.
* Codebook: the E0 codebook of protocol 4 (`clinical`, `life_science`, `no`),
  from title and abstract only.
* Coder 1 (a Claude subagent) codes every candidate. Coder 2 (an independent
  Claude subagent) codes a random 25% of candidates (seed 20261018) and a
  random 200 non-candidates pooled over venue-years (seed 20261018), which
  coder 1 also codes. Coders see title and abstract only: no venue, topic,
  links, verdicts or each other's files. Their model is recorded from the
  subagent transcripts.
* Gate: Cohen's kappa (three categories) between coders on the candidate
  overlap at least 0.80. If met, coder 1's labels stand outside the overlap
  and overlap disagreements are adjudicated by this session with a written
  reason. If not met, coder 2 codes all remaining candidates and every
  disagreement is adjudicated; this is reported.
* Groups: **medical** = candidates with label `clinical` or `life_science`;
  **other** = non-candidates. Candidates labelled `no` are excluded from both
  groups and counted. Secondary groups: `clinical` only, `life_science` only.
  The 200 non-candidates give the share of medical papers the prefilter
  misses (consensus of both coders), with a Wilson interval.

## Outcomes (per paper)

* **O1 code link (primary):** any link, in the `url` field or in an
  `eventmedia` item of type `URL`, whose host is `github.com`, `gitlab.com`,
  `bitbucket.org`, `huggingface.co`, `codeberg.org`, `sourceforge.net`,
  `gitee.com` or `anonymous.4open.science` (the last counted separately too).
* **O2 any artifact link (sensitivity):** any such link with a host other than
  `openreview.net`, the venue's own domain, `youtube.com`, `slideslive.com`,
  `x.com` or `twitter.com`.
* **O3 restricted-data mention (descriptive):** title or abstract matches,
  case-insensitive,
  `\b(MIMIC\w*|eICU|UK Biobank|ADNI|PhysioNet|electronic health records?|EHRs?|in-house|proprietary|private (data|dataset|cohort)s?|institutional (data|dataset|cohort)s?|hospital (data|records|cohort)s?)\b`.
  A lower bound: abstracts omit most data statements.

## Analyses

Uncertainty: stratified bootstrap over papers (resampling within group and
venue-year), 2000 resamples, seed 20261017, percentile 95% intervals.

* **R-A1 (primary).** Mantel-Haenszel risk difference in O1, medical minus
  other, over the six venue-years; also each venue-year separately. Label
  "medical papers are less often released with code" only if the pooled CI
  upper bound is below 0 AND the difference is negative in at least four of the
  six venue-years. If the label is not met, the abstract does not claim a
  readiness difference across venues.
* **R-A1 secondary and sensitivity (reported, never substituted):** clinical
  only; life science only; O2 instead of O1; topic-only label (candidates by
  topic list, no coding) versus non-candidates; excluding ICML 2026.
* **R-A2 (descriptive).** The same estimate for O3. No label.
* **R-A3 (descriptive, ICML 2026).** Join ICML 2026 papers to the challenge by
  OpenReview id = `orid`. Attempted = at least one judged logbook after
  deduplication, excluding Kate's namespace `kondratevakate`. Decided = at
  least one verified or falsified claim verdict in any logbook. Reported:
  decided share in the four cells medical/other by O1 yes/no; the medical
  minus other difference in decided share, unadjusted and Mantel-Haenszel
  adjusted over O1 strata. The verdicts were seen in protocol 6; O1 has not
  been linked to them before this protocol. Sensitivity: protocol 6 label.
* **R-B1 (descriptive, small n).** Both coders label all 100 RECLAIM papers
  (title and abstract from arXiv), consensus with adjudication. Reported by
  group: number of papers, distribution of the dataset's `tier` field as
  released, and median `h100_hours_adjudicated`. Per-paper agent outcomes are
  reported by group only if the RECLAIM repository releases them; otherwise
  stated as not available.

## Evidence boundary

* A code link is a declared link, not working code; data access is seen only
  in abstracts. Readiness here is a lower bound on what a third party needs.
* Virtual-site metadata are entered by authors and venues and may be
  incomplete or added at different times per venue; the stratified estimate
  compares groups within a venue-year only.
* Labels come from language-model coders, validated against each other, not
  against domain experts.
* Observational and descriptive; no causal effect of being medical is claimed.
* Only aggregates and per-paper labels keyed by public ids are committed; no
  author is named.

## Amendment 1 (2026-10-18, after download, before any labelling or readiness computation)

Mechanics only; definitions, outcomes, analyses and labels are unchanged.

* The 2026 virtual-site files (ICLR 2026, ICML 2026) have no `abstract` field;
  their link fields (`url`, `eventmedia`) are present. The first build of the
  paper table therefore excluded both strata as "no abstract". Abstracts are
  added as follows, and units whose abstract cannot be found are excluded and
  counted:
  - ICML 2026: from the local `papers.json` (key `abstracts`, keyed by
    OpenReview id; SHA-256 recorded in the manifest), joined on the forum id.
  - ICLR 2026: from each paper's virtual-site page
    `https://iclr.cc{virtualsite_url}`, the text of the element whose id starts
    with `abstract`, fetched at most two requests per second.
* Coding in batches: no single subagent can read several thousand abstracts.
  Coder 1 and coder 2 are each a role played by successive Claude subagent
  instances with the identical prompt, each instance coding one batch of at
  most 250 items. Batches follow the shuffled sheet order. Instances of one role
  never see the other role's files.

## Amendment 2 (2026-10-18, before any labelling or readiness computation)

Approved by Kate in chat. Scope extended to computer-vision venues and to
NeurIPS 2026. No paper had been labelled and no readiness share computed.

* Strata (12): ICLR 2025, ICLR 2026, NeurIPS 2024, NeurIPS 2025, NeurIPS 2026,
  ICML 2025, ICML 2026 (machine learning); ICCV 2025, CVPR 2024, CVPR 2025,
  ECCV 2024, ECCV 2026 (computer vision). Sources: the same virtual-site files
  at `iccv.thecvf.com`, `cvpr.thecvf.com`, `eccv.ecva.net` and `neurips.cc`.
  CVPR 2026 is excluded because its virtual-site file lists only 200 of its
  papers (the CVF list has no code-link field). ICCV 2026 does not exist.
* Abstracts for NeurIPS 2026 and ECCV 2026 (files without an `abstract` field)
  come from each paper's virtual-site page, as for ICLR 2026 in Amendment 1.
* Unit: accepted items with `eventtype` Poster, Oral or Spotlight (ECCV 2026
  uses Spotlight). Computer-vision files have no OpenReview link, so the
  deduplication key falls back to `sourceid`, else `id`. They have no
  health or biology topics, so candidates there come from the regex only.
* R-A1 label rule restated for 12 strata: the pooled CI upper bound below 0
  AND a negative difference in at least 8 of the 12 strata (two thirds, as in
  four of six). Added secondary analyses: machine-learning and
  computer-vision venues separately; 2024-2025 strata only (excluding all
  2026 strata, whose code links may still be added before or after the
  meeting).
* All candidates are coded, as frozen (option b).

# Protocol 8: hidden science — what a crowd can check without the data

Frozen 2026-10-19, approved by Kate in chat, before any sample was drawn,
any full text fetched or any contrast computed. Designed after the
results of protocols 3, 4, 6 and 7 were seen. Every analysis below uses data
already looked at in aggregate (ICML 2026 verdicts, medical labels); none of
the contrasts below has been computed. Part of the PSE9 abstract
"Unfalsifiable by default", extended towards hidden science (research whose
evidence rests on data others cannot access) and synthetic or toy releases.

## Questions

H8.1 Within papers, is the medical decidability gap concentrated in empirical
     claims rather than theoretical ones?
H8.2 Does a restricted-data mention go with fewer decided papers, and does it
     account for part of the medical gap?
H8.3 What reasons does the judge give when it does not decide a claim, and
     do they differ for medical papers?
H8.4 Asymmetry at scale: are mechanism and theory claims of medical papers
     decided as often as those of other papers, while headline and secondary
     empirical claims are not?
H8.5 Policy test: were papers with at least one experiment on open data
     decided more often? How common are private-only evaluations ("hidden
     science") and released synthetic, sample or toy data?
H8.6 (optional) Expert check of the medical label.

## Units, groups and outcomes

* Papers: ICML 2026 papers in `readiness/data/papers.json` (stratum
  `icml-2026`). Medical = protocol 7 label `clinical` or `life_science`;
  other = protocol 7 non-candidates; candidates labelled `no` are excluded.
  Secondary: clinical only. Sensitivity: protocol 6 label.
* Logbooks: confirmation snapshot (`data/verdicts_confirmation_2026-10-17/verdicts.json`,
  SHA-256 `652f1c16…`), deduplicated as in protocol 1, Kate's namespace
  `kondratevakate` excluded. Attempted paper = at least one logbook.
* Claim verdict: one claim in one logbook. Decisive = `verified` or
  `falsified`. Paper decided = at least one decisive claim verdict.
* Uncertainty: paper-cluster bootstrap (resampling papers within group),
  2000 resamples, seed 20261017, percentile 95% intervals. Samples drawn with
  seed 20261018.

## H8.1 (primary): theory versus empirical claims within papers

* Claim type by the protocol 4 dictionary (regex in `e1_adjusted/PROTOCOL.md`,
  validated kappa 0.76): `theory` or `empirical`.
* Gap(type) = decisive share, medical minus other, among claim verdicts of
  that type in attempted papers. Estimate: DiD = Gap(empirical) minus
  Gap(theory).
* Label "the medical gap is concentrated in empirical claims" only if the DiD
  CI upper bound is below 0. Reported with both gaps, their CIs and counts.

## H8.2 (descriptive): restricted-data mentions

* Restricted-data mention = protocol 7 outcome O3 (title or abstract regex).
* Decided share among attempted papers in the four cells medical/other by O3;
  medical minus other gap unadjusted and Mantel-Haenszel adjusted over O3.

## H8.3 (descriptive): the judge's stated reasons

* Sample: 150 `toy` or `inconclusive` claim verdicts from attempted medical
  papers and 150 from attempted other papers, at most 3 per paper.
* Two blind coders (Claude subagents) code all 300 from the claim text and the
  judge's evidence text; paper titles are masked and the group is hidden.
  Reason (one, the main one): `data_unavailable` (restricted, private or
  unreleased data), `artifacts_missing` (weights, predictions, outputs or
  derived data not released), `code_missing_or_broken`,
  `reduced_scale_or_compute`, `not_attempted`, `underspecified_paper`,
  `other`. Consensus by agreement, else adjudication by this session with a
  written reason. Cohen's kappa reported.
* Reported: share of each reason by group with Wilson intervals, and the
  medical minus other difference for `data_unavailable` and
  `artifacts_missing` with bootstrap CIs.

## H8.4 (secondary): claim-type map and the asymmetry

* Codebook: protocol 3 claim types (`theory`, `mechanism`, `data_protocol`,
  `headline_performance`, `secondary_empirical`), from claim text only.
* Items: every unique claim text of attempted medical papers, and a random
  sample of the same number of unique claim texts from attempted other papers.
* Coding as protocol 7 option (b): coder 1 codes all, coder 2 a random 25%,
  gate kappa at least 0.80 (else coder 2 codes all and every disagreement is
  adjudicated). Claude subagents; model recorded from transcripts.
* Decisive share by group and type at the claim-verdict level. Contrast:
  Gap({headline_performance, secondary_empirical}) minus
  Gap({theory, mechanism}).
* Label "checkable-without-data claims were decided as often, data-dependent
  claims were not" only if the CI of Gap({theory, mechanism}) includes 0 AND
  the contrast CI upper bound is below 0.

## H8.5 (policy test and prevalence): open data, private data, synthetic releases

* Papers: every attempted medical paper and a random equal-size sample of
  attempted other papers.
* Full text: arXiv HTML at `https://arxiv.org/html/<arxiv id>` (id from
  `papers.json`), else the arXiv PDF parsed with `pypdf`; at most one request
  per three seconds. Papers without full text are excluded and counted.
* Excerpt: paragraphs matching, case-insensitive,
  `dataset|data availab|publicly available|public|private|proprietary|in-house|institutional|IRB|ethic|consent|synthetic|simulated|toy|sample data|demo|download|access|PhysioNet|credential|request|licen|weights|checkpoint|code`,
  in document order, capped at 6,000 characters, with the title.
* Two blind coders (Claude subagents) code every paper (group hidden):
  - `main_data_access`: `open` (downloadable without a data-use agreement),
    `credentialed_or_request` (e.g. PhysioNet credentialing, UK Biobank
    application, on request), `private` (not released), `synthetic_only`,
    `unclear`;
  - `open_data_experiment`: `yes` if at least one main experiment uses open
    data, `no`, `unclear`;
  - `synthetic_or_sample_release`: `yes` if the paper states a released
    synthetic, sample, demo or toy dataset for running the code, `no`,
    `unclear`;
  - `weights_release`: `yes`, `no`, `unclear`.
  Kappa per field; consensus by agreement, else adjudication with a reason.
* Reported: prevalence of each field by group; hidden science = medical
  papers with `main_data_access` = `private` and `open_data_experiment` = `no`.
  Decided share by `open_data_experiment` within medical and within other
  papers; Mantel-Haenszel difference (yes minus no) over the two groups.
* Label "papers with an open-data experiment were decided more often" only if
  the pooled CI lower bound is above 0. `unclear` is excluded and counted.

## H8.6 (optional): expert check

If Kate provides it: 60 ICML 2026 papers drawn at random (30 protocol 7
medical, 30 non-candidates), coded blind by Kate with the E0 codebook.
Agreement with the protocol 7 labels is reported; labels are not changed.

## Evidence boundary

* All verdicts come from one LLM judge. Decisive is the challenge's label.
* Observational: teams chose papers and claims; the within-paper contrasts
  (H8.1, H8.4) remove paper choice but not claim difficulty.
* Excerpts can miss data statements; `unclear` is reported, not imputed.
* Coders are language models; agreement is between model coders.
* The policy test describes existing variation; it does not show what a
  mandate would do.
* A synthetic or transfer reproduction pilot (re-running private-data papers
  on open data or schema-faithful synthetic data) is out of scope here and
  would be a separately frozen protocol.
* Aggregates and per-item codes keyed by public ids only; no author named.

## Note 8-1 (2026-10-19, after H8.5 coding, before any H8.1-H8.5 contrast was computed)

H8.5 adjudication rules, fixed before `analyze_p8.py run`:

* A release field (`synthetic_or_sample_release`, `weights_release`) coded
  `no` by one coder and `unclear` by the other is adjudicated by the
  excerpt length: an excerpt that reached the 6,000-character cap may have
  lost later paragraphs, so the label is `unclear`; a shorter excerpt holds
  every matching paragraph, so the label is `no`. 107 of 129 disagreements
  were settled this way.
* The other 22 disagreements (19 papers' field pairs, listed in
  `codes/p8/adjudication_h85.csv` with reasons) were adjudicated from the
  excerpt only, without outside knowledge of a dataset's access terms; a
  named dataset without stated terms is `unclear`.
* `synthetic_or_sample_release` follows the convention both coders applied
  where they agreed (e.g. F0132): a code release that runs synthetic
  experiments is not a stated synthetic-data release.
* Agreement on the two release fields was low (kappa 0.12 and 0.40), and
  most excerpts reached the cap, so their prevalences are reported as lower
  bounds with this caveat. No label of protocol 8 depends on them.

## Note 8-2 (2026-10-19, post hoc, after `results/p8.json` was seen)

The H8.5 policy contrast came out negative (papers without an open-data
experiment were decided more often). A likely reading is composition: the
`no` cell holds theory papers and synthetic-only papers, whose claims are
easy to decide. Three descriptive analyses, defined here before being
computed, are reported as post hoc, with no label, in `results/p8_posthoc.json`
(`posthoc_p8.py`):

* PH8-a: per policy cell, the number of papers with `main_data_access` =
  `synthetic_only` and the number with no empirical claim verdict (protocol 4
  dictionary).
* PH8-b: decided share by `main_data_access` within medical papers, open
  versus restricted (`credentialed_or_request` or `private`), Wilson
  intervals, and the difference restricted minus open with a paper bootstrap
  CI (2000 resamples, seed 20261017). The same cells for other papers are
  reported.
* PH8-c: the H8.5 policy cells and Mantel-Haenszel difference recomputed
  among papers with at least one empirical claim verdict and
  `main_data_access` not `synthetic_only`.

## Note 8-3 (2026-10-19, post hoc, before being computed)

H8.5 counts hidden science among attempted papers only. If teams avoided
medical papers that rely on restricted data, that count says little about
the population. One descriptive check, no label, in
`results/p8_posthoc.json` (`posthoc_p8.py`, key `PH8_d`):

* PH8-d: among all ICML 2026 papers in the protocol 8 groups, the attempt
  rate (at least one logbook outside the author's namespace) by protocol 7
  outcome O3 (restricted-data mention in title or abstract), within medical
  and within other papers, with Wilson intervals; within medical papers the
  difference O3 = 1 minus O3 = 0 with a paper bootstrap CI (resampling within
  O3 cells, 2000 resamples, seed 20261017).
* O3 is an abstract-level regex and a lower bound on restricted data; a
  paper whose abstract does not mention its data is counted as O3 = 0.

## Note 8-4 (2026-10-19, correction, after PH8-d was computed)

* Bug: `consensus()` in `analyze_p8.py` iterated a Python `set` of item ids,
  whose order depends on the per-process string hash seed. The order of
  papers entering the H8.3, H8.5 and PH8 bootstraps therefore changed between
  runs, so their percentile intervals were not reproducible (point estimates
  were). Found when a rerun of `posthoc_p8.py` moved the PH8-b interval from
  −34.4…+27.2 to −31.7…+27.2 points. Fix: iterate the ids in sorted order.
  `results/p8.json` and `results/p8_posthoc.json` are recomputed and checked
  to be identical under two hash seeds; the values committed in 0e5ccb7 are
  superseded. H8.1, H8.2 and H8.4 do not depend on this order.
* Sanity check defined after PH8-d was seen (it showed medical papers with a
  restricted-data mention attempted more often, not less): the number of
  distinct team namespaces among attempted medical papers with O3 = 1, to
  see whether one team drives the difference. Descriptive, key
  `PH8_d.teams_o3_1`.

# Protocol 9: a 2025–2026 baseline of reproducibility practice in life-science ML

Frozen 2026-10-19, approved by Kate in chat, before the frame was drawn, any
full text was fetched or any pilot run. Designed after the results of
protocols 6–8 were seen.
Purpose: a re-runnable baseline of what authors of life-science papers at
top ML venues stated and released in 2025–2026, compared with other papers,
anchored on the ICML 2026 agent reproductions, with a pilot of toy
(synthetic-data) checks for restricted-data papers. Built to be repeated
with the same frame and codebook in later years.

## Questions
Q9.1 (descriptive) Papers, life-science papers and declared code links per
     venue-year (protocol 7 data; no new download).
Q9.2 (descriptive) ICML 2026 funnel: papers, attempted, decided, fully
     verified; life science versus other (protocols 6–8 results).
Q9.3 (primary) Prevalence of reproducibility practices in full texts.
Q9.4 (secondary) Do stated practices match what reproducers found
     (ICML 2026 logbooks as reference standard)?
Q9.5 (secondary) Do compute and data scale account for the ICML 2026
     decidability gap?
Q9.6 (descriptive) Share of claims in restricted-data life-science papers
     that are checkable without the data (theory or mechanism).
Q9.7 (pilot) Can released code plus schema-faithful synthetic data decide
     mechanism claims of restricted-data papers?

## Frame
* Venue-years: CVPR 2025, ICCV 2025, ECCV 2026, ICLR 2025, ICLR 2026,
  ICML 2025, ICML 2026, NeurIPS 2025, NeurIPS 2026 (protocol 7 sources;
  CVPR 2026 is not among them).
* Life science = protocol 7 label clinical or life_science: all 2,170.
  Other = non-candidates: random sample of equal size, allocated to
  venue-years in proportion to life-science counts, seed 20261019.
  Candidates labelled `no` are excluded.
* Frame (ids, group, venue-year, seed) written to results/p9_frame.json
  and hashed before any full text is fetched.

## Full text
* Order: arXiv HTML, arXiv PDF (id by arXiv API title search; accepted if
  normalised titles are identical or similarity >= 0.95 and the arXiv year
  is at least venue year - 1; ambiguous matches excluded), then the open
  proceedings PDF (CVF open access, ECVA, PMLR, proceedings.neurips.cc).
  No OpenReview scraping. At most one request per 3 s per host. Papers
  without full text are counted by group and venue-year, not imputed.
* Storage: C:\Projects\data\datasets\literature\ml-venue-fulltext\
  2025-2026-v1\raw\, registered in _registry/datasets.json with retrieval
  date and SHA-256 manifest. Full texts never enter git.
* Excerpt, cap 15,000 characters, filled in this order: last 3,000
  characters of the Introduction; sections whose heading matches
  availab|reproducib|ethic|data|experimental setup|implementation|training
  details|compute|resources|limitation; NeurIPS checklist items 4-8 and 13
  when present; then paragraphs matching the protocol 8 regex. A truncation
  flag is stored per paper.

## Codebook (per paper; `unclear` allowed in every field)
1  claims: listed_and_linked (main claims enumerated and each tied to a
   table, figure or theorem), listed, none
2  code: released (link given), promised, no
3  main_data_access: open, credentialed_or_request, private,
   synthetic_only (protocol 8)
4  open_data_experiment: yes, no
5  synthetic_or_sample_release: yes, no (protocol 8 and Note 8-1)
6  weights_release: yes, no
7  outputs_release: yes (predictions, raw outputs or logs), no
8  variance: yes (several seeds, error bars or intervals on main results), no
9  environment: yes (versions, requirements file or container), no
10 compute: amount (hardware and time or GPU-hours), hardware_only, none
11 compute_tier: low (<= 1 GPU-day or CPU only), medium (1-30 GPU-days),
   high (> 30), not_stated
12 data_scale: largest training set < 10^4, 10^4-10^6, > 10^6 samples,
   not_stated
Rules fixed now (from Note 8-1): stated text only, no outside knowledge of
a dataset's terms; a named dataset without stated terms is `unclear`; on a
release field, `no` versus `unclear` follows the truncation flag.

## Coding and agreement
* Claude subagents, claude-sonnet-5-5, 20 papers per batch, group hidden.
  Coder 1 all; coder 2 a random 25% (seed 20261019).
* Gate: Cohen's kappa >= 0.80 on each primary field (code,
  main_data_access, weights_release, variance, compute). Below the gate,
  coder 2 codes all papers for that field and every disagreement is
  adjudicated. Other fields are descriptive, reported with their kappa.
* Adjudication by this session from the excerpt only, with a reason.

## Reference standard (Q9.4)
* ICML 2026 papers in the frame with at least one logbook (author's
  namespace excluded). From logbook claims and the judge's evidence text,
  two blind coders label what reproducers found: code_used (authors' code
  obtained and run), data_obtained (main data obtained), weights_used;
  each yes, no, unclear.
* Reported: agreement of full-text fields with these (sensitivity,
  specificity, kappa).
* NeurIPS 2025/2026: agreement of `code` with checklist item 5 where
  present (self-report; consistency only).

## Analyses
A9.1 Counts and shares per venue-year (aggregation of protocol 7 results).
A9.2 Funnel from protocols 6-8, each number with its source file.
A9.3 Prevalence by group and venue-year, Wilson intervals; life science
     minus other, Mantel-Haenszel over venue-years, paper bootstrap within
     strata (2000 resamples, seed 20261017; inputs in sorted id order,
     checked under two hash seeds). 2025 versus 2026 descriptive.
     Labels only if the MH CI excludes 0 in the stated direction:
     L9.1 life-science papers report open main data less often;
     L9.2 life-science papers release weights less often;
     L9.3 life-science papers report variance less often.
     `unclear` excluded and counted per field.
A9.4 Agreement tables for Q9.4.
A9.5 ICML 2026 attempted papers in the frame: decided share by group; MH
     gap adjusted for compute_tier, for data_scale, and for both (strata
     with both groups only). Label "scale accounts for the gap" only if the
     both-adjusted CI includes 0 and its point estimate is less than half
     the unadjusted gap.
A9.6 Share of challenge claims typed theory or mechanism (H8.4 codes) in
     ICML 2026 attempted life-science papers with restricted main data
     (protocol 8 codes), Wilson interval; same for open-data papers.

## Toy pilot (Q9.7)
* Wave 1 (now): ICML 2026 attempted life-science papers coded restricted
  (credentialed_or_request or private) in protocol 8 that state a code
  release: 5 papers. Wave 2 (after A9.3): up to 5 more, random (seed
  20261019) among census life-science papers with restricted main data and
  code `released`, ICML 2026 first.
* Per paper, from the paper and its repository only. No real restricted
  data is downloaded or requested; credentialed datasets are never touched.
  1 Clone the repository; record commit hash and licence; skip if no
    licence permits use.
  2 CPU-only Docker container; network off after dependency installation;
    no host mounts except a per-paper work directory; 8 GB memory; 2 hours
    wall time per paper.
  3 Write a schema-faithful synthetic dataset (shapes, field names, types
    and label space from the paper and the data loader; random values;
    small size).
  4 For each challenge claim with H8.4 type theory or mechanism, decide
    before running whether it can be observed on synthetic data, write the
    check, run it, and record consistent, inconsistent,
    not_checkable_on_synthetic, or blocked (no running pipeline within
    budget). Headline and secondary claims are recorded as
    not_checkable_on_synthetic unless a check is stated (negative control).
  5 The executor is blind to challenge verdicts.
* Executor: one Claude subagent per paper (claude-sonnet-5-5); a second
  subagent re-runs the scripts and confirms each consistent or
  inconsistent outcome from the logs.
* Reported: share of theory/mechanism claims that were checkable
  (consistent or inconsistent), Wilson interval; time to a running
  pipeline; reasons for blocked; every inconsistent outcome in full,
  offered to the authors before publication; descriptive comparison with
  the challenge verdicts for the same claims. No label (feasibility, not
  prevalence).

## Rerun as a baseline
Frame procedure, codebook, extraction code, prompts and model id are
frozen here. A later rerun applies them to new venue-years and re-codes a
random 10% of the 2025-2026 papers with its new coder model to measure
instrument drift.

## Evidence boundary
* Full texts show what authors state, not working artifacts; Q9.4 measures
  that gap for ICML 2026 only.
* Coders and executors are language models; the reference standard is
  coded by language models from logbooks judged by an LLM.
* ICLR full texts depend on arXiv; papers without full text are excluded
  and counted.
* Aggregates and per-paper codes keyed by public ids; no author named;
  repository code is not redistributed.

## Note 9-1 (2026-10-19, before any protocol 9 coding)

Implementation choices left open by the protocol, fixed before coding (`build_p9_excerpts.py`, `fetch_p9.py`):

* Full-text sources: the open proceedings exist for ICML 2025 and 2026 (PMLR v267, v306) and CVPR and ICCV 2025
  (CVF). ECVA lists ECCV only up to 2024, and the NeurIPS 2025 proceedings site listed 64 papers on 2026-10-19,
  so ICLR, ECCV 2026 and NeurIPS 2025 and 2026 rely on arXiv alone. Missing full texts are counted per group
  and venue-year.
* PDF text is read with PyMuPDF text blocks (the protocol 8 excerpts used pypdf); headings in PDFs are
  detected from numbered or known section titles. arXiv HTML headings come from its LaTeXML section titles.
* Within the matched sections, the order is by the first keyword found in the heading: availab, reproducib,
  ethic, compute, resources, implementation, training details, experimental setup, data, limitation
  (release and access statements first, then compute and scale, then setup, then data descriptions, then
  limitations); document order within a level. Each matched section contributes at most 2,000 characters,
  so that long data sections do not crowd out the others before the 15,000-character cap.
* NeurIPS checklist items are counted by their "Question:" paragraphs; for items 4-8 and 13 the question, answer
  and justification are kept and the checklist's guideline text is left out.
* The truncation rule for release fields is applied by the coders: each sheet row carries the truncation
  flag, and a release field with no statement is `unclear` when the excerpt was truncated and `no` when not.
* Coders: 20 papers per batch, title and excerpt only (venue, year and group hidden); prompt in
  `codes/p9/CODER_PROMPT.md`.

## Note 9-2 (2026-10-19)

By Kate's decision the pilot counts only as aggregate numbers in the overall test totals: no paper is named with an outcome, the authors are not contacted, and per-paper pilot files are not published.

## Note 9-3 (2026-10-19)

After the first two coder batches (recoded, not used), the excerpt also takes up to 1,500 characters of paragraphs and table captions on seeds, spread and repeated runs, right after the introduction, because the variance field was otherwise mostly `unclear`.

## Note 9-4 (2026-10-19)

The coders of batches 080 and 083 ran at the same time and both wrote a helper script to the same shared path (`/tmp/show.py`); one coder reported a read that returned another batch's excerpt. Both batches are recoded by fresh coders (the earlier codes are set aside, not used). From these recodes and batch 108 on, the prompt ends with one more sentence: "Do not write helper files to shared temporary paths such as /tmp; read the sheet with inline Python instead." The coding instructions are unchanged.

## Note 9-5 (2026-10-21, after the agreement scores, before any comparison was computed)

Coder agreement on the 813 double-coded papers: the gate is met for code (kappa 0.85), main_data_access (0.83)
and weights_release (0.96) and not met for variance (0.71) and compute (0.70). Choices for the analysis, fixed now:

* Fields that meet the gate use coder 1's code for every paper; coder 2 is the reliability sample and
  disagreements on these fields are not adjudicated.
* Variance and compute do not meet the gate. Until coder 2 has coded them for all papers and every
  disagreement is adjudicated (the protocol's rule), their results, including L9.3, are reported from coder 1
  as provisional and no label is assigned.
* A9.3 indicators (positive category versus the other non-`unclear` categories): claims listed_and_linked,
  code released, main_data_access open, open_data_experiment yes, synthetic_or_sample_release yes,
  weights_release yes, outputs_release yes, variance yes, environment yes, compute amount. compute_tier and
  data_scale are reported as distributions only. Mantel-Haenszel risk differences over the nine venue-years.
* A9.5: attempted = at least one logbook in the protocol 8 verdict snapshot (author's namespace excluded);
  decided = at least one claim verified or falsified. Strata are the coded categories, `not_stated` included;
  papers coded `unclear` on a stratifying field are left out of that adjusted estimate and counted.
* A9.6 uses the protocol 8 final codes (claim types from H8.4, main data access from H8.5) for ICML 2026
  attempted life-science papers; Wilson intervals over claims, as written, without a cluster correction.
* A9.4 needs the reference-standard coding of ICML 2026 logbooks, which has not been done; it is not reported.

## Note 9-6 (2026-10-21, before coder 2 completes the fields below the gate)

Kate approved completing the gate rule for variance and compute. Choices:

* Coder 2 codes the 2,465 coded papers outside its 25% sample with the unchanged prompt (`codes/p9/CODER_PROMPT.md`,
  role `coder2full`, 20 papers per batch, the Note 9-4 sentence appended). It labels all twelve fields; only
  variance and compute are used. The other fields keep coder 1's codes (Note 9-5).
* Every coder 1 versus coder 2 disagreement on variance or compute, over all coded papers, is adjudicated from
  the excerpt only, with a reason. Deviation from "adjudication by this session": about 1,300 items exceed what
  one session can read, so adjudication is done by Claude subagents (claude-opus-5-5, this session's model), 20
  items per batch. Each adjudicator sees the title, truncation flag, excerpt, the field definition from the
  coder prompt and the two labels in random order (seed 20261019), not which coder gave which.
* Agreement for variance and compute is reported on the 813-paper sample (the gate) and on all coded papers.

## Note 9-7 (2026-10-21, before the reference standard for Q9.4 is built)

* Units: the 222 ICML 2026 frame papers with at least one logbook in the protocol 8 verdict snapshot
  (deduplicated, author's namespace excluded); all have full-text codes.
* Sheet per paper: title, then each logbook's claims with the judge's verdict and evidence text, in snapshot
  order, capped at 15,000 characters with a truncation flag. Group and full-text codes hidden.
* Two blind coders (claude-sonnet-5-5, roles ref1 and ref2) code every paper; prompt in
  `codes/p9/REF_PROMPT.md`. Paper level: `yes` if any logbook states it was done, `no` if the evidence shows it
  was not (for example code reimplemented or unavailable, data substituted or not obtained), `unclear` otherwise.
  Disagreements are adjudicated as in Note 9-6.
* Agreement with full-text fields, `unclear` excluded on either side: code `released` versus code_used,
  main_data_access `open` versus data_obtained, weights_release `yes` versus weights_used. Sensitivity,
  specificity and Cohen's kappa.
* NeurIPS 2025 and 2026: checklist item 5 answer parsed from the excerpt ("Answer: [Yes]" or "[No]"; `[NA]`
  left out) versus code `released` (`unclear` excluded); kappa and raw agreement.

## Note 9-8 (2026-10-22, before the coder2full codes are compared or adjudicated)

The coder2full file for batch 093 has one label outside the codebook (compute_tier `unclear` for one paper), so
the batch fails the completeness check. The batch is recoded by a fresh coder with the same prompt; the earlier
file is set aside, not used. Coder instances that stopped on a usage limit before writing their file are rerun
with the same prompt; a file written before an instance stopped is used if it passes the check.

## Note 9-9 (2026-10-22, post hoc, frozen before computing)

Question raised after the final A9.3 and A9.5 results: life-science papers state more reproducibility practices yet
are decided less often in ICML 2026; is the gap carried by the papers' claims or by how far reproducers got? Post
hoc and descriptive; reported as such. Units: the A9.5 papers (ICML 2026 frame, at least one logbook, author's
namespace excluded; decided = at least one verified or falsified claim verdict). Script `posthoc_p9.py`, output
`results/p9_posthoc.json`; MH risk differences and bootstrap as in A9.5.

* PH9-a, decomposition. Unadjusted decided difference (life science minus other), then MH-adjusted for (i) number
  of distinct teams (1, 2, 3 or more), (ii) number of distinct claim texts, in tertiles of the pooled distribution,
  (iii) both. Claim-level decided share per group (verdict rows), with a paper bootstrap within group.
* PH9-b, claim linkage. Decided difference MH-adjusted for the P9 `claims` code (listed_and_linked, listed, none;
  unclear excluded); the code's distribution by group among these papers.
* Reading rule, as A9.5: an adjustment "accounts for the gap" if its CI includes 0 and its point estimate is less
  than half the unadjusted one in absolute value. If (iii) accounts for the gap while the claim-level shares do not
  differ, the gap is attributed to how many claims and teams papers had; if PH9-b accounts for it, to claim
  linkage; otherwise neither explains it. No claim texts are coded in this note.

## Note 9-10 (2026-10-22, post hoc, frozen before computing)

Kate asked to split the "other" papers by area and to use the whole ICML 2026 challenge instead of the A9.5 sample.
Descriptive; post hoc. Script `posthoc_p9_areas.py`, output `results/p9_areas.json`.

* Rows: medical (protocol 7 label clinical or life_science) as one row; all other papers split by ICML area, the
  part of the `topic` field before "->" (empty topic: `unknown`). Candidates labelled `no` are excluded, as in the
  frame, and counted.
* PH9-c, challenge (all ICML 2026 papers, protocol 8 verdict snapshot, author's namespace excluded): per row, papers,
  attempted share, mean teams among attempted, decided share among attempted, claim-level decisive share; Wilson
  intervals.
* PH9-d, medical versus all other attempted papers: decided difference unadjusted and MH-adjusted for teams (1, 2,
  3 or more), bootstrap over papers within group (2,000, seed 20261017); reading rule as in Note 9-9. Claim-level
  decisive difference within team: MH over team namespaces, bootstrap over papers within group.
* PH9-e, documentation (final P9 codes, ICML 2025 and ICML 2026 frame papers, which share the area taxonomy): per row,
  shares of code `released`, main_data_access `open`, weights_release `yes`, variance `yes` (unclear excluded), Wilson
  intervals. Other papers here are the frame's random sample, so area counts are small.

## Note 9-11 (2026-10-22, post hoc, frozen before computing)

Note 9-10 found that medical papers are attempted about as often as others but by fewer teams (mean 1.5), and that
within a team their claims are decided about as often. Kate asked to test each candidate reason why fewer teams take
them up. Post hoc and descriptive. Units: attempted ICML 2026 papers as in Note 9-10 (author's namespace excluded,
candidates labelled `no` excluded). Outcome: a second team (at least two distinct team namespaces). Entry time of a
team on a paper = its earliest `judged_at` in the snapshot (a proxy: judging time, not submission time). Script
`posthoc_p9_uptake.py`, output `results/p9_uptake.json`. MH differences, bootstrap over papers within group (2,000,
seed 20261017); "accounts for the gap" as in Note 9-9, applied to the medical minus other difference in the outcome.

* T1 herding: first team's first logbook decided or not. Second-team rate by that status and group; medical gap
  adjusted for first-logbook status, and for status plus the first team's entry week (later papers had less time).
* T2 expected points: number of anchored claims per paper (`claims_anchored.json`, tertiles of the pooled
  distribution); gap adjusted for it. On the ICML 2026 frame papers also for P9 compute_tier (not_stated a category).
* T3 who takes medical papers: per group, distinct teams, share of attempts by the top 1 and top 5 teams; among teams
  with any medical attempt, share of their attempts that are medical. Descriptive only.
* T4 entry threshold and documentation: on the ICML 2026 frame papers, gap adjusted for P9 data_scale (not_stated a
  category); within each group, mean teams for papers with versus without code `released`, main_data_access `open`,
  synthetic_or_sample_release `yes` (unclear excluded), difference with bootstrap CI.

## Note 9-12 (2026-10-23, adversarial checks of the post hoc claims, frozen before computing)

Kate asked to try to refute the main claims. Each test states in advance what would refute the claim. Script
`posthoc_p9_adversarial.py`, output `results/p9_adversarial.json`; bootstrap and MH as in Notes 9-9 to 9-11.

* F1, "life-science papers document more" (code `released`, main_data_access `open`, weights_release `yes`, variance
  `yes`): refuted for a field if any of these fails: (i) leaving out each venue-year in turn, every MH difference > 0;
  (ii) coder 1 codes alone and coder 2 codes alone, CI lower bound > 0; (iii) only papers whose excerpt was not
  truncated, CI lower bound > 0; (iv) MH over venue-year by excerpt-length tertile, CI lower bound > 0.
* F2, "medical papers are decided less often in ICML 2026" (attempted papers, Note 9-10 units): refuted if any fails:
  (i) label permutation among attempted papers (2,000, seed 20261017), two-sided p < 0.05; (ii) clinical-only and
  life_science-only labels versus other, each CI upper bound < 0; (iii) dropping every logbook of the team with the
  most medical attempts, CI upper bound < 0.
* F3, "the gap is depth of the crowd, not the papers": (i) decided by the first team's first logbook only, one per
  paper; if this gap is at least half of the all-team gap, depth alone does not explain it; (ii) that first-logbook
  gap MH-adjusted for the first team's namespace (teams with both kinds of first attempts); if the adjusted gap is
  under half and its CI includes 0, the residual is attributed to which teams take medical papers; (iii) the
  within-team claim-level difference recomputed without the team with the most medical attempts; refuted if its CI
  upper bound < 0 and its point estimate is below -5 points.
* F4, "a decided first logbook does not draw a second team to medical papers": difference in the herding effect
  (medical minus other) with bootstrap CI; the contrast is supported only if the CI upper bound < 0.
* F5, "stated practices poorly predict what reproducers obtained": A9.4 kappas recomputed with ref1 codes alone, ref2
  codes alone, and on papers whose logbook evidence was not truncated; refuted if any code or data kappa >= 0.40.

## Note 9-13 (2026-10-23, extended post hoc experiments, frozen before computing)

Note 9-12 replaced "depth of the crowd" by "which teams take medical papers" and found the decided gap mainly in
clinical papers. Kate asked to test this numerically and to extend the experiments. Script `posthoc_p9_extended.py`,
output `results/p9_extended.json`; units, bootstrap and MH as in Notes 9-10 to 9-12.

* E1, team strength. A team's strength on a paper = share of its other attempted ICML 2026 papers (this paper left
  out) on which its own latest logbook was decided; fewer than 3 other papers = category `few`. Compare the first
  team's strength on medical versus other papers (difference in means, bootstrap). Adjust the first-logbook gap and
  the all-team decided gap for the first team's strength (tertiles of the pooled values, plus `few`). The
  composition explanation is supported if both adjusted gaps are under half the unadjusted ones with CIs including 0.
* E2, team experience: number of ICML 2026 papers the first team attempted (tertiles); same adjustments and rule.
* E3, clinical versus life_science separately against other papers: the four documentation fields (as F1, MH over
  venue-year) and the ICML 2026 decided gap with and without the E1 adjustment.
* E4, outcome definitions for the decided gap: fully verified (some logbook verified every claim it rated), any
  falsified claim, no decisive verdict; unadjusted and E1-adjusted.
* E5, documentation by venue family: vision venues (CVPR, ICCV, ECCV) versus learning venues (ICLR, ICML, NeurIPS),
  the four fields, MH over venue-year within family.

## Note 9-14 (2026-10-23, further adversarial checks without new coding, frozen before computing)

Script `posthoc_p9_more.py`, output `results/p9_more.json`; units and team strength as in Note 9-13.

* G1, claim "full verification is harder for medical papers even with strong first teams" (outcome fully_verified):
  label permutation p (2,000); gap adjusted for first-team strength after dropping every logbook of the team with
  the most medical attempts; adjusted gap for clinical and life_science separately. Survives if p < 0.05, the
  drop-top adjusted CI upper bound < 0 and the clinical adjusted CI upper bound < 0.
* G2, claim "team strength is a property of teams, not of the papers they pick": within-paper test on papers with at
  least two teams. Each team's strength on the paper excludes that paper; strong = above the pooled median. MH over
  papers of decided (strong minus weak team). Supported if the CI lower bound > 0. Medical papers alone reported.
* G3, herding contrast (Note 9-12 F4) after dropping the top medical team, and with the herding effect estimated
  within entry week. Supported if both CI upper bounds < 0.
* G4, within-team claim-level difference for clinical and life_science separately. Refuted for a subgroup if its CI
  upper bound < 0 and its estimate is below -5 points.

## Note 9-15 (2026-10-23, claim-text coding, frozen before any claim is coded)

Kate asked for more coding to test the claims further. Question: do medical papers make claims that are costlier to
check, and does that explain the claim-level and full-verification gaps?

* Units: every distinct claim text (normalised) rated in any logbook of the 110 attempted medical ICML 2026 papers,
  and of a random 110 of the 1,821 attempted other papers (seed 20261023, sorted ids). Builder
  `build_p9_claims.py`; keys and sheets in `data/p9/` (git-ignored); codes in `codes/p9/claims/`.
* Two blind coders (claude-sonnet-5-5 subagents, roles claim1 and claim2), batches of 50, claim text only (no title,
  no paper id, no group, no verdict); prompt `codes/p9/CLAIM_PROMPT.md`. Fields: check_cost (`inference_only`: one run
  of released or easily rebuilt artifacts settles it; `retrain`: the method must be trained; `large_scale`: many runs,
  large models or datasets, or broad sweeps; `analytic`: a proof or derivation, no experiment; `unclear`),
  quantitative (`yes`/`no`: states a number or metric value), comparison (`yes`/`no`: against a baseline, prior work
  or state of the art). Cohen's kappa per field. Every disagreement is adjudicated as in Note 9-6
  (claude-opus-5-5, labels in random order, reason required). Claim texts can reveal the domain; coders are blind to
  the group label, not to the subject.
* Analysis (`posthoc_p9_claims.py`, `results/p9_claims.json`): K1 share of `retrain` or `large_scale` claims and of
  quantitative and comparison claims by group, bootstrap over papers. K2 within-team claim-level decisive difference
  MH over team by check_cost strata; K3 fully_verified difference MH over first-team strength (Note 9-13) by the
  paper's share of costly claims (0, up to half, over half). Claim cost "accounts" for a gap if the adjusted estimate
  is under half the unadjusted one with a CI including 0; otherwise it does not.

## Note 9-16 (2026-10-23, before the claim coding beyond batch 000)

To limit the number of instances, each claim coder instance after claim1 batch 000 codes four to six consecutive
batches of 50 (same prompt, extended to list several sheets, one output file per batch). Roles stay separate.

## Note 9-17 (2026-10-23, extension sample for Q9.4, frozen before any paper is drawn)

Kate chose to extend the Q9.4 reference standard (claim 7) with a sample, not the whole challenge.

* Units: 300 drawn at random (seed 20261023, sorted ids) from the 1,709 attempted ICML 2026 papers outside the P9
  frame (all are non-medical; candidates labelled `no` excluded as in Note 9-10). Frame file
  `results/p9_ext_frame.json` (group `ext`), written and hashed before any full text is fetched.
* Full texts and excerpts exactly as in Protocol 9 (`fetch_p9.py run --frame`, `build_p9_excerpts.py`); papers
  without a full text are counted, not replaced.
* Full-text coding: the unchanged coder prompt, two blind coders (roles ext1, ext2), batches of 20, several
  batches per instance as in Note 9-16. Reference coding: the unchanged `REF_PROMPT.md`, two blind coders (roles
  refx1, refx2) on the same logbook sheets as Note 9-7.
* Full-text fields as in Note 9-5: coder 1 (ext1) codes for code, main_data_access and weights_release if their
  kappa on this sample is at least 0.80, otherwise every disagreement on that field is adjudicated. Reference
  disagreements are all adjudicated (Note 9-6 procedure).
* Analysis (`analyze_p9_ext.py`, `results/p9_ext.json`): the three A9.4 agreement tables (sensitivity, specificity,
  kappa) on the extension sample alone and pooled with the 222 frame papers. Claim 7 is strengthened if pooled code
  and data kappas stay below 0.40; it is weakened if either reaches 0.40 or more.

## Note 9-18 (2026-10-23, before the extension coding)

Full-text and logbook sheets hold up to 15,000 characters per paper, so each extension coder instance codes one
batch of 20 (the original Protocol 9 procedure), not several as Note 9-17 allowed.

## Note 9-19 (2026-10-23, state of the Note 9-17 extension when the thread was closed)

All 300 extension papers have full text and were coded by ext1, ext2, refx1 and refx2 (codes in `codes/p9/ext/`).
Agreement: full-text code and main_data_access below 0.80, so both are to be adjudicated; weights_release kappa
0.97; reference code_used 0.72, data_obtained 0.73, weights_used 0.52. The 302 disagreements are in adjudication
sheets (`data/p9/ext_adj_sheets/`, git-ignored) but have not been adjudicated, and `analyze_p9_ext.py run` has not
been executed. Claim 7 in the submitted abstract rests on the 222 frame papers only.

## Note 9-20 (2026-10-24, result of the Note 9-17 extension)

All 302 extension disagreements were adjudicated by 16 blind claude-opus instances (unchanged `ADJ_PROMPT.md`,
paths `ext_adj_sheets/` -> `codes/p9/ext/`; `codes/p9/ext/ext_adjudication.csv`). `analyze_p9_ext.py run` gives
identical `results/p9_ext.json` under PYTHONHASHSEED 0 and 1; the frame tables recompute to the reported values.
A9.4 kappas, extension alone / pooled with the 222 frame papers: code vs code_used 0.34 (n 185) / 0.28 (n 347);
main_data_access vs data_obtained 0.22 (n 74) / 0.16 (n 163); weights_release vs weights_used 0.63 (n 75) /
0.60 (n 118). Pooled code and data kappas stay below 0.40, so claim 7 is strengthened by the Note 9-17 rule.

## Note 9-21 (2026-10-29, post hoc, lexicon frozen before computing)

Kate asked which life-science papers at these venues bear on biosecurity. Descriptive; post hoc; not part of the
PSE9 abstracts. Script `posthoc_p9_biosec.py`, output `results/p9_biosec.json`.

* Units: the 2,170 frame papers with group `life_science` (`results/p9_frame.json`). Titles only; the frame has no
  abstracts.
* Six regex topics, case-insensitive, frozen in the script before any count: pathogens_infection, protein_design,
  dna_genome_models, epidemics_surveillance, countermeasures_trials, biosafety_dual_use. A paper can hit several.
  "Direct" = pathogens_infection, epidemics_surveillance or biosafety_dual_use.
* Reading rule: report counts as a lower bound and as a screen, not a coded variable. Hand check on 2026-10-29: all
  direct hits and 25 random hits read as on-topic; misses include drug-target affinity and synthesis-library titles.
* Result: 523 of 2,170 (24%) hit any topic; 22 (about 1%) are direct (NeurIPS 10, ICML 8, ICLR 4; none at CVPR,
  ICCV, ECCV).

## Note 9-22 (2026-10-30, post hoc, after an internal review of the manuscript; frozen before the intervals below)

An internal review of the medRxiv manuscript raised three points that the existing results do not answer. Post hoc;
reported as such. Script `posthoc_p9_empirical.py`, output `results/p9_empirical.json`; MH and bootstrap exactly as
in A9.3 (`analyze_p9.mh_rd`, `boot_ci`, 2,000 resamples, seed 20261017). Disclosure: the reviewer computed the point
estimates of E-a from `results/p9_papers.csv` before this note was written (code +10.6, main data open +7.1, weights
+21.7, variance +24.7 points); no interval and nothing in E-b or E-c had been computed.

* E-a, empirical papers only. Units: coded frame papers whose data_scale is not `not_stated` (a training-set size
  was stated, so the paper reports an experiment on data). Fields code, main_data_access, weights_release,
  variance, indicators as in Note 9-5, `unclear` excluded. Reading rule: "medical papers document more" holds for a
  field among empirical papers if the CI lower bound is above 0.
* E-b, release fields with `unclear` counted as not released or not open: main_data_access, weights_release,
  synthetic_or_sample_release, outputs_release over all coded papers. Descriptive; shares by group and MH
  difference with CI.
* E-c, verdict mix: attempted ICML 2026 papers as in Note 9-10 (author's namespace excluded, candidates labelled
  `no` excluded). Claim-level shares of verified, falsified, toy, inconclusive and other by group, with the
  difference in the toy share bootstrapped over papers within group (Note 9-10 procedure); paper-level share with
  at least one toy verdict, same bootstrap. Descriptive.
* Result (identical under PYTHONHASHSEED 0 and 1). E-a, 1,129 medical and 962 other empirical papers: code +10.6
  (CI +6.0 to +15.0), main data open +7.1 (+2.1 to +12.2), weights +21.7 (+12.7 to +30.7), variance +24.7 (+20.1 to
  +29.3); the claim holds for all four fields. E-b, unclear as no: main data open 46.2% vs 24.7% (+21.7), weights
  8.7% vs 5.6% (+3.1, +1.3 to +4.8), synthetic or sample data -0.6 (-1.7 to +0.5), outputs -0.2 (-1.2 to +0.8).
  E-c, claim verdicts of medical vs other attempted papers: verified 21.7% vs 49.7%, falsified 3.6% vs 4.7%, toy
  25.5% vs 20.9% (difference +4.7, -0.6 to +10.7), inconclusive 49.2% vs 24.8%; papers with any toy verdict 64.5% vs
  71.3% (-6.8, -15.9 to +2.3).

## Note 9-23 (2026-11-01, full-text recovery, frozen before any recovery request)

Kate decided on 2026-10-31 to complete full-text coverage of the frame and to report the result in version 1 of the
medRxiv manuscript (not yet approved for posting). 1,062 of the 4,340 frame papers had no full text (1,057
`no_match`, 4 `error`, 1 `no_fulltext`). The frozen rule lists proceedings.neurips.cc and ECVA among the open
proceedings, but `fetch_p9.py` indexed only PMLR and CVF; NeurIPS 2025 is now on proceedings.neurips.cc and ICLR
2025 and 2026 on proceedings.iclr.cc (not named in the protocol). The protocol excluded OpenReview scraping;
unauthenticated OpenReview requests now meet a bot check (HTTP 403, `ChallengeRequiredError`).

Disclosure of what was seen before this note (2026-10-31): one unauthenticated OpenReview request per stratum
(403); with Kate's own OpenReview session token (she logged in herself; the token is stored outside the repository
and the data tree and never logged), one ICLR 2025 PDF (HTTP 200, content discarded) and five NeurIPS 2026 notes
(HTTP 403 "no permission": NeurIPS 2026 papers are not public before the conference); title counts of the missing
papers against the proceedings listings (476 of 493 missing NeurIPS 2025, ICLR 2025 and ICLR 2026 papers have an
identical normalised title); arXiv and OpenAlex on a random 20 of the missing NeurIPS 2026 and ECCV 2026 papers (0
arXiv matches, 1 OpenAlex open-access PDF). No recovered text was read and nothing was coded.

* Units: frame papers whose last manifest row is not `ok`. Script `fetch_p9.py index-recovery` and
  `fetch_p9.py recover`; manifest rows carry `recovery: "9-23"`.
* Order: arXiv HTML, arXiv PDF (unchanged search and title rule); open proceedings (PMLR and CVF as before,
  proceedings.neurips.cc 2025 and proceedings.iclr.cc 2025 and 2026 by a unique normalised title similarity of at
  least 0.95); the OpenReview API PDF with Kate's session token (public notes only); a unique OpenAlex work with
  title similarity of at least 0.95 and publication year at least the venue year minus 1 that lists an open-access
  PDF. A bot check or an access refusal counts as no full text and is never worked around. Spacing as before.
* Excerpts, sheets and coding exactly as Protocol 9: `build_p9_excerpts.py`, then `build_p9_sheets.py final` (item
  ids and the 25% coder-2 sample were fixed over the whole frame by `init`); coder 1 on every new paper, coder 2 on
  the new papers in its sample, coder2full on the rest for variance and compute (Note 9-6), every variance and
  compute disagreement adjudicated (Note 9-6, claude-opus-5-5, labels in random order); other fields from coder 1
  (Note 9-5). Coders claude-sonnet-5-5, unchanged `CODER_PROMPT.md` with this repository's paths, one batch of 20
  per instance (Note 9-18). Agreement is reported for the new papers alone and pooled.
* Analyses: A9.3 and Note 9-22 E-a and E-b are rerun on all coded papers; these become the main estimates of the
  manuscript. The estimates on the 3,278 papers of the first retrieval (results at commit 092e8a5) are reported as a
  sensitivity analysis. Labels L9.1 to L9.3 are re-evaluated by the unchanged rule; any change in a label or in the
  sign of a pooled difference is reported in the abstract.
* Post hoc, exploratory (`posthoc_p9_recovery.py`, `results/p9_recovery.json`): within venue-year strata, the
  pooled difference in each A9.3 indicator between recovered papers and papers of the first retrieval (MH and
  bootstrap as in A9.3), by group; it asks whether papers found on arXiv document more than the others.
* Papers still without a full text are counted by group and venue-year. A later pass after the NeurIPS 2026 papers
  become public would need its own note.

## Note 9-24 (2026-11-01, topics of the medical papers, post hoc, codebook frozen before any paper is coded)

Kate asked on 2026-10-31 for a summary table of the topics of the medical papers and a t-SNE map of their abstracts
showing which topics appear more often at which venue. Post hoc and descriptive. Kate chose a fixed codebook with two
blind coders over clusters, and the 2,170 medical papers as the corpus.

* Units: all 2,170 medical papers, with or without a full text. Input: title and abstract from the venue listing
  (`papers.json`). Venue, year, group and the clinical or life-science label are hidden; items in random order
  (seed 20261101), item ids `T0000` onward; keys in `data/p9/topic_keys.json` (git-ignored).
* Codebook (one primary topic, the application domain the paper's method is built for or evaluated on; prompt
  `codes/p9/topics/TOPIC_PROMPT.md`): radiology, pathology_microscopy, other_clinical_imaging, ehr_clinical_text,
  physiological_signals, neuroscience, genomics_omics, proteins, molecules_drug_discovery, chemistry_materials,
  epidemiology_public_health, other_biology, other.
* Coders: two blind claude-sonnet-5-5 subagents (roles topic1, topic2) code every paper, batches of 50, several
  batches per instance (Note 9-16). Cohen's kappa reported, no gate; every disagreement adjudicated blind by
  claude-opus-5-5 (labels in random order, one-sentence reason; `ADJ`-style prompt in the same folder). Final topic:
  the agreed label or the adjudicated one.
* Analyses (`posthoc_p9_topics.py`, `results/p9_topics.json`): T1 counts and shares of each topic per venue (six
  venues, years pooled) and per venue-year, Wilson intervals; T2 chi-square test of venue by topic with adjusted
  standardised residuals, a cell read as over- or under-represented only if its residual is at least 3 in absolute
  value; T3 shares by year (2025 versus 2026); T4 per topic among coded papers, the shares reporting code released,
  open main data, weights released and variance (Note 9-5 indicators, `unclear` excluded); T5 among attempted ICML
  2026 medical papers (Note 9-10), papers and the decided share per topic. All descriptive, no multiplicity
  correction.
* Map: SPECTER2 base (`allenai/specter2_base`, revision recorded) CLS embedding of title, separator and abstract;
  t-SNE (scikit-learn, cosine metric, perplexity 30, PCA initialisation, random_state 20261101); points coloured by
  final topic, a second panel by venue. The map illustrates the table and is not used for inference.
