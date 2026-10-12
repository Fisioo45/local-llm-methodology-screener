# Analysis plan — local-LLM methodology-risk screener

Status: **v1.0 — FROZEN 2026-10-06, before any model was run on the test set.** Lock: `configs/test_lock.json` (gold SHA-256, code fingerprint, model digests); `run.py` refuses the test set if any of them differ.
Author: Esat (sole author). Repository: this project; gold standard: `annotation_sheet_v1.3.xlsx`.

## 1. Data
- Corpus: 542 open-access (CC BY / CC0) 2025 deep-learning medical-imaging classification papers from Europe PMC (frozen frame in `data/processed/`).
- Random annotation order (seed 20260923); ineligible papers skipped. Pilot = first 20 eligible, dev = next 20, **test = next 80**.
- Test items (codebook v1.3): A1 split unit, A4 test set used for selection, B2 variability reported, C1 code available, C2 data available.
- Gold labels by one annotator (the author). A keyword checker (`check_annotations`) and an AI assistant flagged possible inconsistencies; **every change was confirmed by the annotator** and is logged in the workbook sheets "Batch … fixes".
- Gold freeze (2026-10-05): `configs/gold_freeze.json`, SHA-256 = 483d4647fe6fea7afccaedc6b7a120a17e6a9353b5d832c5d88e0bb3569d8667 (120 papers: pilot 20, dev 20, test 80). No label changes after freezing; any correction is logged and reported.
- Blinding: no model output was viewed for any test paper before its labels were final.

## 2. Systems compared on the test set
All LLM runs: Ollama, 4-bit, one RTX 4060 8 GB, `num_ctx` 8192, per-item retrieval with a 1,800-token budget, greedy decoding (k = 1), items = test5. Model digests are recorded in `run_meta.json` and must equal the dev round 3 digests.

| ID | System | Role |
|---|---|---|
| R | Keyword rules | baseline |
| **M1** | **qwen3:8b, decomposed prompt p2.2, think off** | **primary system** |
| H1 | Hybrid: rules for B2 and C1, M1 for A1, A4, C2 | pre-specified secondary (split by item type, fixed before testing) |
| M2 | qwen3.5:9b, decomposed p2.2, think off | model comparison |
| M3 | llama3.1:8b, decomposed p2.2 | model comparison |
| M4 | gemma3:4b, decomposed p2.2 | model comparison (small model) |
| P1 | qwen3:8b, direct prompt p1.1, think off | prompt design (direct vs decomposed) |
| A-b900 / A-b3600 | M1 with retrieval budget 900 / 3,600 tokens | ablation: context size |
| A-k5 | M1 with self-consistency, k = 5, T = 0.7 | ablation: sampling |
| A-think | M1 with thinking on, max new tokens 4,096 | ablation: reasoning mode |

Model digests (Ollama 0.34.4, Q4_K_M) are fixed in `configs/test_lock.json`. Ablations were not run on dev; if an ablation fails technically (parse failures in > 10 % of paper-items), it is reported as failed and not re-tuned.

Label policy: **gated** for every LLM system (best on dev for M1, M2, M3, M4); raw for R. Raw and verified results are reported in the supplement.

## 3. Endpoints
**Primary.** Mean Cohen's κ over the five items, M1 versus R: difference with a 95 % paired-bootstrap CI (2,000 resamples of papers, seed 12345) and a two-sided bootstrap p-value. The hypothesis is two-sided; no direction is assumed.

**Secondary.**
1. H1 versus R, and H1 versus M1, same method (no multiplicity correction; reported as secondary).
2. Per item: κ and macro-F1 with bootstrap 95 % CIs; exact McNemar on per-paper correctness for M1 vs R, H1 vs R, P1 vs M1, each M vs M1 and each ablation vs M1, Holm-corrected over the five items within each pair. Model and ablation comparisons are descriptive.
3. Leakage flags: sensitivity and PPV for RISK on A1 and A4; paper level "any leakage risk" (A1 or A4 = RISK) and "not verifiably safe" (A1 or A4 = RISK or UNCLEAR).
4. Evidence: share of quotes found verbatim (exact or ≥ 90 % fuzzy) in the paper.
5. Cost: seconds, energy (J) and peak VRAM per paper; parse failures. Human time: annotation minutes per paper from the workbook.
6. Prevalence (RQ4): proportion of each label in the 80 test papers with Wilson 95 % CIs. An extension to the whole corpus (prediction-powered inference) is **exploratory** and will be labelled as such.

Unparseable model output counts as the item's "not reported" label (as on dev). κ is not computed for an item whose gold labels have a single class.

## 4. Intra-rater reliability
20 test papers drawn at random (seed 20261005; list in `configs/rerating_selection.json`), re-annotated blind on or after 19 October 2026 with codebook v1.3. Reported: per-item agreement and κ with bootstrap CIs, against the frozen gold.

## 5. Known limitations stated in advance
- Single annotator.
- The keyword checker flagged possible misses on B2, C1 and C2 during annotation; this can favour the rule baseline on those items (dev shows rules κ = 1.00 on C1 and 0.85 on B2).
- 80 papers: CIs of about ±0.1–0.2 for κ; rare labels (C1 = YES ≈ 10 papers) give wide CIs.
- Prompts were developed on 40 dev papers; dev results are optimistic and are reported separately.

## 6. Dev results used to fix this plan (supplement)
Dev round 3 (2026-10-06): prompts p2.2 / p1.1, 5 items, 40 papers (pilot + dev), corrected dev gold. Mean κ and difference to R (95 % paired-bootstrap CI):

| System | Mean κ | Δ vs R | sec/paper | VRAM (MiB) |
|---|---|---|---|---|
| R rules | 0.515 | — | 0.05 | — |
| M1 qwen3:8b p2.2 gated | 0.614 | +0.10 (−0.01 to 0.20) | 30.3 | 6,425 |
| M2 qwen3.5:9b p2.2 gated | 0.611 | +0.10 (−0.00 to 0.19) | 30.6 | 7,291 |
| M3 llama3.1:8b p2.2 gated | 0.514 | −0.00 (−0.11 to 0.11) | 26.8 | 6,316 |
| M4 gemma3:4b p2.2 gated | 0.367 | −0.15 (−0.27 to −0.03) | 22.8 | 7,167 |
| P1 qwen3:8b p1.1 gated | 0.588 | +0.07 (−0.05 to 0.19) | 32.7 | 6,299 |
| H1 hybrid with M1 | 0.650 | +0.14 (0.05 to 0.23) | 19.6 | 6,425 |

Per item (κ, M1 / R): A1 0.55 / 0.29; A4 0.10 / 0.23; B2 0.75 / 0.85; C1 0.92 / 1.00; C2 0.75 / 0.20. M1 was chosen over M2 for the higher mean κ at lower VRAM. Tables: `results/dev_round3/`.

## 7. Deviations
Any deviation from this plan will be listed with its reason in the paper.
