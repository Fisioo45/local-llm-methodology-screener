# Annotation Codebook v1.1 — Methodology-Risk Screening of Applied Deep-Learning Papers

Status: **v1.1 PROPOSED after the 20-paper pilot — confirm, then freeze before any test-set annotation.** Changes from v1.0 are marked **[v1.1]** and listed in §8.

## 1. Purpose and unit of annotation

The unit is one published article. For each eligible article the annotator assigns one label per item (Section 4) and copies a verbatim evidence quote. These labels are the gold standard against which the local-LLM screener is evaluated, so they must describe **what the article itself lets a careful reader conclude**, not what the annotator suspects.

## 2. General rules

1. **Text-grounded only.** Judge from the article: body text, tables, figure captions, back matter, and supplementary text if included in the article. Do **not** use outside knowledge of a public dataset (e.g., "I know this Kaggle set has several images per patient"). Put such knowledge in the `external_note` column; it never changes the label.
2. **Explicit beats implicit.** A label of RISK or SAFE needs a statement that supports it. Paragraph order alone is not evidence of sequence; sequencing words ("then", "after augmentation, the dataset was split…") are.
3. **Absence is UNCLEAR (risk items) or NO (reporting items)**, never SAFE.
4. **Main experiment only.** Judge the experiment that produces the headline result in the abstract. If several experiments differ, label the headline one and note the others.
5. **Evidence.** Copy the shortest verbatim span(s) that justify the label (≤ 40 words each; separate multiple spans with ` || `). For NO / UNCLEAR / N/A write `ABSENT` or quote the closest statement that leaves the question open.
   **[v1.1]** *Verbatim* means copy-paste from the article: no summaries in your own words, no inserted words in [brackets], no `...` inside a quote (use ` || ` between two spans). Your reasoning goes in `notes`, never in the evidence cell. Every SAFE, RISK, YES, PUBLIC, RESTRICTED or REQUEST label needs at least one quote.
6. **Blinding.** Never look at any model output for a paper before its gold labels are final.

## 3. Eligibility (column `eligible`)

**Y** if the article is a primary study that trains or fine-tunes at least one supervised **classification** model on **medical images** and reports its performance on held-out data.

**N** (give `exclusion_reason`) for: reviews, surveys, protocols, commentaries; segmentation-, detection- or registration-only studies with no classification output; studies that only evaluate a model without any training or fine-tuning; non-image inputs only (e.g., tabular, signals, text); non-medical images.

Radiomics or deep features followed by a trained classifier → **Y**. Multi-task (segmentation + classification) → **Y**, judge the classification task.

**[v1.1]** The classifier's input must be images or image-derived maps, patches, slices or volumes. Inputs computed from signals or region-level time series are **not images** → **N** (non-image input). Examples: Doppler waveforms; fMRI functional-connectivity matrices built from atlas-region time series.

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
*Was any data-dependent step fitted on the full dataset before the split?* Data-dependent steps learn something from **several samples at once**: normalisation with dataset-wide statistics, feature selection or dimensionality reduction (PCA, LASSO, statistical filtering), class re-balancing (SMOTE, over-/under-sampling), imputation, learned harmonisation.
Not data-dependent (ignore): resizing, cropping, filtering, fixed intensity scaling, ImageNet mean/std, fixed windowing, **[v1.1]** normalisation computed per image or per subject, and "normalisation" with no mention of dataset statistics. Augmentation is item A3.
- **RISK** — stated as fitted on the full dataset, or sequencing words place it before the split.
- **SAFE** — **[v1.1]** a data-dependent step is used AND stated as fitted on training data only / inside each CV fold.
- **UNCLEAR** — a data-dependent step is used and its subset is not stated.
- **N/A** — **[v1.1]** no data-dependent step is described (only the "ignore" kind, or no preprocessing at all).

**A3 `aug_before_split`** (risk; leakage L1.4 duplicates by construction)
*Was augmentation or synthetic-image generation (e.g., GAN, diffusion) applied before the train/test split?*
- **RISK** — stated, or the reported post-augmentation dataset size is the one that gets split ("after augmentation, 12,000 images were divided 80:20"), **[v1.1]** unless the split explicitly keeps every augmented/synthetic copy in the same set as its source patient or image (then SAFE).
- **SAFE** — applied to the training set only, or on-the-fly during training, **[v1.1]** or augmentation came first but the split is explicitly grouped by source patient/image.
- **UNCLEAR** — augmentation/synthesis used; timing relative to the split not stated.
- **N/A** — no augmentation or synthetic data.

**A4 `test_for_selection`** (risk; test-set reuse)
*Was the set used to report final performance also used for development decisions: hyperparameter tuning, early stopping, checkpoint/epoch selection, model or threshold selection?*
- **SAFE** — a separate validation set or inner CV is used for these decisions and the test set only for final evaluation (stated or clearly implied by a three-way split with defined roles).
- **RISK** — stated (e.g., best checkpoint saved on test accuracy; early stopping on the test set), **or** only two sets exist and the reported one is the one monitored during training (e.g., reported "validation accuracy" with training curves on that same set).
- **UNCLEAR** — two-way split with no description of how epochs/checkpoints/hyperparameters were chosen.
- **[v1.1]** Several models compared on the test set, and the best one is then adopted as the proposed/final model or used to build the next model → **RISK**. Merely reporting several models on the test set, with the final model fixed in advance → not RISK by itself.
- **[v1.1]** k-fold cross-validation with no separate test set: **SAFE** if nested CV is used or hyperparameters are stated as fixed in advance; **RISK** if tuning/selection on the same folds that give the reported result is stated; otherwise **UNCLEAR**.
- **[v1.1]** Hyperparameter optimisation (grid search, metaheuristics such as "Osprey/Whale/PSO" tuning) whose evaluation subset is not stated → **UNCLEAR**.

**A5 `duplicate_check`** (reporting; leakage L1.4)
*Do the authors report checking for duplicate or near-duplicate images (and handling them)?* **YES / NO.**

### Section B — Evaluation robustness

**B1 `external_validation`** (reporting)
*Is the final model evaluated on at least one test set from a source not used in development (different institution, site, scanner fleet, or dataset)?* **YES / NO.** A held-out part of the same dataset is NO. Temporal-only validation at the same site: **NO** and write `temporal` in notes.

**B2 `variability_reported`** (reporting)
*Is performance variability reported for the main result: spread across folds/seeds/repeated runs (mean ± SD) or a confidence interval (bootstrap, Wilson, DeLong)?* **YES / NO.**
**[v1.1]** Using cross-validation is not enough: YES needs the spread itself (± SD, range, per-fold values) or a CI for a main performance metric. Mean over folds with no spread → NO.

**B3 `stat_test_for_claim`** (reporting)
*When the article claims its model outperforms comparators, is the claim supported by a statistical test (e.g., DeLong, McNemar, Wilcoxon) or by non-overlapping confidence intervals?* **YES / NO / N/A** (no superiority claim).

**B4 `baseline_protocol`** (risk)
*Are comparisons with other methods made under the same data and protocol?*
- **SAFE** — comparators re-trained/re-evaluated on the same splits, or only the authors' own identically trained models are compared.
- **RISK** — a comparison table reports numbers taken from other publications that used different data, splits or protocols, and it supports a superiority claim.
- **UNCLEAR** — cannot tell whether comparator numbers were reproduced or copied.
- **N/A** — no comparison with other methods.
- **[v1.1]** "Comparison" means the proposed model's performance is compared with other models, methods or human readers. Labelling of the test set by experts (the reference standard) is **not** a comparison. Comparison with readers, or with and without AI, on the same test cases → SAFE. UNCLEAR needs a quote showing that a comparison exists; with no comparison use N/A.

### Section C — Reproducibility

**C1 `code_available`** (reporting) — **YES** (public repository link or DOI for the study code) / **REQUEST** (available on request) / **NO** (not stated, or not available).
**[v1.1]** A link or DOI counts as YES even if phrased "will be made available at <link>". "Will be made available" with no link and no request wording → NO.

**C2 `data_available`** (reporting) — **PUBLIC** (all data used are publicly accessible and the source is named) / **RESTRICTED** (on request, or access procedure) / **NO** (not available or not stated).
**[v1.1]** These boilerplate statements → RESTRICTED when the images themselves are not in the article: "available on (reasonable) request"; "will be made available by the authors, without undue reservation"; "included in the article/supplementary material, further inquiries can be directed to the corresponding author". A named public dataset (e.g. ADNI, BraTS, Kaggle) with no statement → PUBLIC.

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
- v1.1 (proposed after pilot, 20 eligible + 2 excluded papers) — verbatim-evidence rule made explicit and every substantive label needs a quote; eligibility excludes signal/connectivity inputs; A2 gains N/A and SAFE now means "data-dependent step fitted on training data only"; A3 exception for patient/source-grouped splits; A4 rules for test-set model selection, CV-only designs and metaheuristic tuning; B2 requires the spread itself; B4 defines "comparison" and N/A; C1 link rule; C2 boilerplate rule.
