---
license: cc-by-4.0
language:
- en
pretty_name: Life science at ML venues
size_categories:
- 1K<n<10K
task_categories:
- text-classification
tags:
- meta-research
- reproducibility
- medical-machine-learning
- openreview
configs:
- config_name: default
  data_files: p9_papers.csv
---

# Life science at ML venues: coded reproducibility practices

One row per paper for a frame of 4,340 papers at nine venue-years of CVPR, ICCV, ECCV, ICLR, ICML and NeurIPS
(2025 and 2026): all 2,170 clinical or life-science papers (`group = life_science`, called medical papers in the
manuscript) and an equal random sample of 2,170 other papers (`group = other`). It accompanies the medRxiv
preprint and the code repository <https://github.com/kondratevakate/life-science-at-ml-venues>.

**Public fields only.** The table has titles, OpenReview links and our codes. It has no abstracts and no full
texts, which are not redistributable. Rows are matched to OpenReview by `venue`, `year` and `forum_id`.

## How the coding was done

- Frame and sample were fixed under a protocol frozen before the random sample was drawn (see the repository).
- Full texts were retrieved for 3,787 of the 4,340 papers (87%). For the other 553, `fulltext_status` is
  `no_match` (130) or `error` (423), and all practice fields are empty.
- Language-model coders read excerpts of each full text and coded twelve reported practices; a random 25% was
  coded twice, and fields below the agreement threshold were coded twice and adjudicated.
- `topic` (medical papers only), `modality`, `method` and `architecture` were coded post hoc from title and
  abstract by the same duplicate-and-adjudicate procedure (Notes 9-24 and 9-26 in the repository).
- `tsne_x`, `tsne_y` come from SPECTER2 embeddings (`allenai/specter2_base`, CLS pooling) of title and abstract,
  t-SNE with cosine metric, perplexity 30, seed 20261101. Medical papers only; the map is for browsing, not a
  measurement.

## Columns

| Column | Meaning |
|---|---|
| `item` | Paper id in this table (P0000 to P4339) |
| `venue`, `year`, `forum_id`, `openreview_url`, `title` | Public metadata from OpenReview |
| `group` | `life_science` or `other` |
| `fulltext_status`, `fulltext_source`, `arxiv_id` | Whether and where the full text was retrieved |
| `claims` | Whether the paper lists its claims: `listed`, `listed_and_linked`, `none`, `unclear` |
| `code` | Code: `released`, `promised`, `no`, `unclear` |
| `main_data_access` | Main dataset: `open`, `credentialed_or_request`, `private`, `synthetic_only`, `unclear` |
| `open_data_experiment` | Whether at least one experiment uses open data |
| `synthetic_or_sample_release` | Whether a synthetic or sample dataset is released |
| `weights_release` | Model weights released: `yes`, `no`, `unclear` |
| `outputs_release` | Model outputs or predictions released |
| `variance` | Variability over seeds or splits reported: `yes`, `no`, `unclear` |
| `environment` | Software environment specified |
| `compute`, `compute_tier`, `data_scale` | Compute reporting (`none`, `hardware_only`, `amount`, `unclear`), tier (`low`, `medium`, `high`, `not_stated`) and data scale (`lt_1e4`, `1e4_1e6`, `gt_1e6`, `not_stated`) |
| `code_used`, `data_obtained`, `weights_used` | Whether reproduction-challenge logbooks actually obtained the code, data or weights (`yes`, `no`, `unclear`); filled for 222 papers, empty otherwise |
| `topic` | Medical papers only: radiology, pathology_microscopy, other_clinical_imaging, ehr_clinical_text, physiological_signals, neuroscience, genomics_omics, proteins, molecules_drug_discovery, chemistry_materials, epidemiology_public_health, other_biology, other |
| `modality` | image, volumetric, video, geometry_3d, text, audio_speech, tabular_records, time_series, biological_sequence, omics_matrix, graph_molecule, interactive_environment, multimodal, none_or_synthetic |
| `method` | supervised_prediction, generative_modeling, representation_learning, causal_inference_trials, biostatistics_inference, uncertainty_calibration, reinforcement_decision, llm_prompting_agents, optimization_efficiency, trustworthy_ml, theory, benchmark_dataset, other |
| `architecture` | Semicolon-separated set from cnn, transformer, llm_vlm, gnn_equivariant, diffusion_flow, state_space_rnn, other_neural, gp_kernel, classical_ml; or alone `not_stated` / `no_model` |
| `tsne_x`, `tsne_y` | Map coordinates (medical papers only) |

Exact definitions and decision rules for each practice are in the frozen protocol (supplement S1 and the
repository).

## Interactive view

<https://kondratevakate.github.io/life-science-at-ml-venues/> (once published).

## Citation

Kondrateva E, Kofler F, Simkó A. Life science at ML venues: reproducibility practice and agentic reproduction of
medical and life-science papers. medRxiv preprint (DOI to be added on posting). Dataset and code:
<https://github.com/kondratevakate/life-science-at-ml-venues>

## License

CC BY 4.0. Paper titles are bibliographic metadata of the respective papers; their copyright stays with the
authors.
