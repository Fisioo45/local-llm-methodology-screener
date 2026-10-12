# Annotation Codebook v1.0 — Methodology-Risk Screening of Applied Deep-Learning Papers

Status: **draft for pilot**. Revise after the 20-paper pilot → v1.1, re-annotate the pilot under v1.1, then freeze before any test-set annotation.

## 1. Purpose and unit of annotation

The unit is one published article. For each eligible article the annotator assigns one label per item (Section 4) and copies a verbatim evidence quote. These labels are the gold standard against which the local-LLM screener is evaluated, so they must describe **what the article itself lets a careful reader conclude**, not what the annotator suspects.

## 2. General rules

1. **Text-grounded only.** Judge from the article: body text, tables, figure captions, back matter, and supplementary text if included in the article. Do **not** use outside knowledge of a public dataset (e.g., "I know this Kaggle set has several images per patient"). Put such knowledge in the `external_note` column; it never changes the label.
2. **Explicit beats implicit.** A label of RISK or SAFE needs a statement that supports it. Paragraph order alone is not evidence of sequence; sequencing words ("then", "after augmentation, the dataset was split…") are.
3. **Absence is UNCLEAR (risk items) or NO (reporting items)**, never SAFE.
4. **Main experiment only.** Judge the experiment that produces the headline result in the abstract. If several experiments differ, label the headline one and note the others.
5. **Evidence.** Copy the shortest verbatim span(s) that justify the label (≤ 40 words each; separate multiple spans with ` || `). For NO / UNCLEAR write `ABSENT` or quote the closest statement that leaves the question open.
6. **Blinding.** Never look at any model output for a paper before its gold labels are final.

## 3. Eligibility (column `eligible`)

**Y** if the article is a primary study that trains or fine-tunes at least one supervised **classification** model on **medical images** and reports its performance on held-out data.

**N** (give `exclusion_reason`) for: reviews, surveys, protocols, commentaries; segmentation-, detection- or registration-only studies with no classification output; studies that only evaluate a model without any training or fine-tuning; non-image inputs only (e.g., tabular, signals, text); non-medical images.

Radiomics or deep features followed by a trained classifier → **Y**. Multi-task (segmentation + classification) → **Y**, judge the classification task.

## 4. Items

Label sets: **Risk items** use `SAFE / RISK / UNCLEAR / N/A`. **Reporting items** use `YES / NO` (plus the variants listed).

### Section A — Data partitioning and leakage

**A1 `split_unit`** (risk; leakage L3.2 non-independence)
*Are training and test data separated at the level of the independent unit (patient, subject, case, lesion, study) so that no patient contributes to both?*
- **SAFE** — patient-/subject-/case-level split or grouped cross-validation is stated; or the article states one image per patient; or the test set is a separate cohort/institution.
- **RISK** — the split is stated at image, slice, patch, tile, or frame level **and** the article indicates multiple images per patient (e.g., more images than patients, slices from volumes, patches from slides, frames from videos, multiple views).
- **UNCLEAR** — image-level random split with no information on images per patient, or the split unit is not described.
- N/A — not used for eligible papers.

**A2 `preproc_before_split`** (risk; leakage L1.2, L1.3)
*Was any data-dependent step fitted on the full dataset before the split?* Data-dependent steps: normalisation with dataset-wide statistics, feature selection or dimensionality reduction (PCA, LASSO, statistical filtering), class re-balancing (SMOTE, over-/under-sampling), imputation, learned harmonisation.
Not data-dependent (ignore): resizing, cropping, fixed intensity scaling, ImageNet mean/std, fixed windowing. Augmentation is item A3.
- **RISK** — stated as fitted on the full dataset, or sequencing words place it before the split.
- **SAFE** — stated as fitted on training data only / inside each CV fold, **or** only non-data-dependent preprocessing is used.
- **UNCLEAR** — a data-dependent step is used and its subset is not stated.

**A3 `aug_before_split`** (risk; leakage L1.4 duplicates by construction)
*Was augmentation or synthetic-image generation (e.g., GAN, diffusion) applied before the train/test split?*
- **RISK** — stated, or the reported post-augmentation dataset size is the one that gets split ("after augmentation, 12,000 images were divided 80:20").
- **SAFE** — applied to the training set only, or on-the-fly during training.
- **UNCLEAR** — augmentation/synthesis used; timing relative to the split not stated.
- **N/A** — no augmentation or synthetic data.

**A4 `test_for_selection`** (risk; test-set reuse)
*Was the set used to report final performance also used for development decisions: hyperparameter tuning, early stopping, checkpoint/epoch selection, model or threshold selection?*
- **SAFE** — a separate validation set or inner CV is used for these decisions and the test set only for final evaluation (stated or clearly implied by a three-way split with defined roles).
- **RISK** — stated (e.g., best checkpoint saved on test accuracy; early stopping on the test set), **or** only two sets exist and the reported one is the one monitored during training (e.g., reported "validation accuracy" with training curves on that same set).
- **UNCLEAR** — two-way split with no description of how epochs/checkpoints/hyperparameters were chosen.

**A5 `duplicate_check`** (reporting; leakage L1.4)
*Do the authors report checking for duplicate or near-duplicate images (and handling them)?* **YES / NO.**

### Section B — Evaluation robustness

**B1 `external_validation`** (reporting)
*Is the final model evaluated on at least one test set from a source not used in development (different institution, site, scanner fleet, or dataset)?* **YES / NO.** A held-out part of the same dataset is NO. Temporal-only validation at the same site: **NO** and write `temporal` in notes.

**B2 `variability_reported`** (reporting)
*Is performance variability reported for the main result: spread across folds/seeds/repeated runs (mean ± SD) or a confidence interval (bootstrap, Wilson, DeLong)?* **YES / NO.**

**B3 `stat_test_for_claim`** (reporting)
*When the article claims its model outperforms comparators, is the claim supported by a statistical test (e.g., DeLong, McNemar, Wilcoxon) or by non-overlapping confidence intervals?* **YES / NO / N/A** (no superiority claim).

**B4 `baseline_protocol`** (risk)
*Are comparisons with other methods made under the same data and protocol?*
- **SAFE** — comparators re-trained/re-evaluated on the same splits, or only the authors' own identically trained models are compared.
- **RISK** — a comparison table reports numbers taken from other publications that used different data, splits or protocols, and it supports a superiority claim.
- **UNCLEAR** — cannot tell whether comparator numbers were reproduced or copied.
- **N/A** — no comparison with other methods.

### Section C — Reproducibility

**C1 `code_available`** (reporting) — **YES** (public repository link or DOI for the study code) / **REQUEST** (available on request) / **NO** (not stated, or not available).

**C2 `data_available`** (reporting) — **PUBLIC** (all data used are publicly accessible and the source is named) / **RESTRICTED** (on request, or access procedure) / **NO** (not available or not stated).

## 5. Derived variables (computed, not annotated)

- `any_leakage_risk` = any of A1–A4 is RISK.
- `unverifiable_partitioning` = none of A1–A4 is RISK and at least one is UNCLEAR.

## 6. Other columns

`minutes` (time spent on the paper), `notes` (anything unusual, which experiment was judged), `external_note` (outside knowledge; never affects labels), `annotated_on` (date).

## 7. Grounding in existing guidance (to be cited in the manuscript)

- Leakage types L1.1–L3.3: Kapoor S, Narayanan A. 2023. Leakage and the reproducibility crisis in machine-learning-based science. *Patterns*.
- REFORMS checklist: Kapoor S et al. 2024. *Science Advances*.
- CLAIM 2024 update (checklist for AI in medical imaging): Tejani AS et al. 2024. *Radiology: Artificial Intelligence*.
- TRIPOD+AI: Collins GS et al. 2024. *BMJ*.

(Verify full reference details before submission.)

## 8. Change log

- v1.0 — initial draft for the 20-paper pilot.
