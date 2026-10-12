"""Machine-readable version of the codebook (v1.3: docs/codebook_v1.3.md; label rules as v1.1 with clarifications).

Single source of truth for the LLM prompts, the rule baseline, the evidence
policy and the evaluation. When the codebook changes (v1.1 after the pilot),
update CODEBOOK_VERSION and the matching entries here in the same commit.
"""
from dataclasses import dataclass, field

CODEBOOK_VERSION = "1.3"


@dataclass(frozen=True)
class Item:
    code: str                      # column name in the annotation workbook
    kind: str                      # "risk" or "report"
    labels: tuple                  # allowed labels, in display order
    question: str
    rules: str                     # decision rules shown to the model
    absent_label: str              # label when the text is silent
    query: tuple                   # retrieval terms (lower-case, stems allowed)
    prefer_back: bool = False      # availability items: search back matter first
    no_evidence_ok: tuple = ()     # labels that legitimately need no quote
    downgrade: dict = field(default_factory=dict)  # label -> label if no verified quote
    gate: dict = field(default_factory=dict)       # label -> regex a verified quote must match (v1.1 dev)


RISK4 = ("SAFE", "RISK", "UNCLEAR", "N/A")
RISK3 = ("SAFE", "RISK", "UNCLEAR")

ITEMS = (
    Item("A1_split_unit", "risk", RISK3,
         "Are training and test data separated at the level of the independent unit (patient, subject, case, lesion, study), so that no patient contributes data to both?",
         "SAFE: a patient-, subject- or case-level split or grouped cross-validation is stated; or the article states one image per patient; or the test set is a separate cohort or institution.\n"
         "RISK: the split is stated at image, slice, patch, tile or frame level AND the article indicates several images per patient (more images than patients, slices from volumes, patches from slides, frames from videos, multiple views).\n"
         "UNCLEAR: an image-level random split with no information on images per patient, or the split unit is not described.",
         "UNCLEAR",
         ("patient", "patients", "subject", "split", "divided", "partition", "random", "training set", "test set",
          "slice", "slices", "patch", "patches", "frame", "per patient", "patient-level", "patient-wise", "cohort", "fold", "images from"),
         gate={"SAFE": r"patient|subject|case|individual|participant|cohort|institution|hospital|cent(er|re)|external|one (image|scan)"}, downgrade={"SAFE": "UNCLEAR", "RISK": "UNCLEAR"}),
    Item("A2_preproc_before_split", "risk", RISK4,
         "Was any data-dependent preprocessing step fitted on the full dataset before the train/test split?",
         "Data-dependent steps learn from several samples at once: normalisation with dataset-wide statistics, feature selection or dimensionality reduction (PCA, LASSO, statistical filtering), class re-balancing (SMOTE, over- or under-sampling), imputation, learned harmonisation. "
         "Not data-dependent (ignore): resizing, cropping, filtering, fixed intensity scaling, ImageNet mean/std, fixed windowing, normalisation computed per image or per subject, and 'normalisation' with no mention of dataset statistics. Augmentation is a different item.\n"
         "RISK: a data-dependent step is stated as fitted on the full dataset, or sequencing words place it before the split.\n"
         "SAFE: a data-dependent step is used AND stated as fitted on training data only or inside each fold.\n"
         "UNCLEAR: a data-dependent step is used and the subset it was fitted on is not stated.\n"
         "N/A: no data-dependent step is described.",
         "N/A",
         ("normaliz", "normalis", "standardiz", "mean", "standard deviation", "smote", "oversampl", "undersampl",
          "balanc", "feature selection", "pca", "principal component", "lasso", "imputation", "preprocess", "entire dataset", "whole dataset", "before split"),
         no_evidence_ok=("N/A",), downgrade={"SAFE": "UNCLEAR", "RISK": "UNCLEAR"}),
    Item("A3_aug_before_split", "risk", RISK4,
         "Was data augmentation or synthetic-image generation (e.g. GAN, diffusion) applied before the train/test split?",
         "RISK: stated, or the reported post-augmentation dataset size is the one that gets split (e.g. 'after augmentation, 12,000 images were divided 80:20'), unless the split explicitly keeps every augmented or synthetic copy in the same set as its source patient or image.\n"
         "SAFE: applied to the training set only, or on-the-fly during training, or augmentation came first but the split is explicitly grouped by source patient or image.\n"
         "UNCLEAR: augmentation or synthesis is used and its timing relative to the split is not stated.\n"
         "N/A: no augmentation or synthetic data is used.",
         "N/A",
         ("augment", "augmentation", "synthetic", "gan", "generative", "diffusion", "rotation", "flip", "oversampl",
          "after augmentation", "training set only", "on-the-fly", "split", "divided"),
         no_evidence_ok=("N/A",), downgrade={"SAFE": "UNCLEAR", "RISK": "UNCLEAR"}),
    Item("A4_test_for_selection", "risk", RISK3,
         "Was the set used to report final performance also used for development decisions (hyperparameter tuning, early stopping, checkpoint or epoch selection, model or threshold selection)?",
         "SAFE: a separate validation set or inner cross-validation is used for these decisions and the test set only for final evaluation (stated, or clearly implied by a three-way split with defined roles).\n"
         "RISK: stated (e.g. best checkpoint saved on test accuracy, early stopping on the test set), OR only two sets exist and the reported one is the one monitored during training.\n"
         "UNCLEAR: a two-way split with no description of how epochs, checkpoints or hyperparameters were chosen. "
         "Papers sometimes call their final evaluation set 'validation': judge by what the set is used for, not by its name.\n"
         "Several models compared on the test set with the best one then adopted as the proposed/final model (or used to build the next model): RISK. "
         "Cross-validation with no separate test set: SAFE if nested CV or hyperparameters fixed in advance are stated; RISK if tuning/selection on the same folds that give the reported result is stated; otherwise UNCLEAR. "
         "Hyperparameter optimisation (grid search, metaheuristics) whose evaluation subset is not stated: UNCLEAR.",
         "UNCLEAR",
         ("validation", "validation set", "test set", "early stopping", "checkpoint", "best model", "hyperparameter",
          "tuning", "grid search", "epoch", "monitor", "model selection", "held-out", "hold-out", "inner"),
         downgrade={"SAFE": "UNCLEAR", "RISK": "UNCLEAR"}),
    Item("A5_duplicate_check", "report", ("YES", "NO"),
         "Do the authors report checking for duplicate or near-duplicate images (and handling them)?",
         "YES: a check for duplicate or near-duplicate images is described (e.g. hashing, similarity search, manual review) and its handling stated.\nNO: no such check is described.",
         "NO",
         ("duplicate", "duplicates", "near-duplicate", "deduplicat", "redundant", "hash", "identical images", "repeated images"),
         gate={"YES": r"duplicat|dedup|hash|identical|redundan|repeated image"}, downgrade={"YES": "NO"}),
    Item("B1_external_validation", "report", ("YES", "NO"),
         "Is the final model evaluated on at least one test set from a source not used in development (different institution, site or dataset)?",
         "YES: evaluated on data from an institution, site or dataset not used for training or tuning.\n"
         "NO: only a held-out part of the development data (including cross-validation). Temporal-only validation at the same site is NO.",
         "NO",
         ("external", "external validation", "external test", "independent", "another hospital", "different hospital",
          "institution", "center", "centre", "multicenter", "cross-dataset", "generaliz", "unseen dataset"),
         gate={"YES": r"external|independent|another|different|separate|second|multi-?cent|hospital|institution|site|dataset"}, downgrade={"YES": "NO"}),
    Item("B2_variability_reported", "report", ("YES", "NO"),
         "Is variability of the main result reported: spread across folds, seeds or repeated runs (e.g. mean ± SD), or a confidence interval?",
         "YES: a performance metric of the authors' own model (main test result or cross-validation result) is given with its spread across folds/seeds/runs (± SD, range, per-fold values) or with a confidence interval (bootstrap, Wilson, DeLong), in the text or a table.\n"
         "NO: single point estimates only. Using cross-validation is not enough: a mean over folds without the spread is NO. A p-value or significance test alone, or ± on patient age or other demographics, is NO.",
         "NO",
         ("±", "standard deviation", "confidence interval", "95% ci", "ci", "mean", "fold", "folds", "runs", "seeds", "repeated", "bootstrap"),
         gate={"YES": r"±|\+/-|\bsd\b|standard deviation|confidence interval|\bci\b|95\s?%|range|interquartile|iqr|std"}, downgrade={"YES": "NO"}),
    Item("B3_stat_test_for_claim", "report", ("YES", "NO", "N/A"),
         "When the article claims its model outperforms comparators, is the claim supported by a statistical test or non-overlapping confidence intervals?",
         "YES: a statistical test (e.g. DeLong, McNemar, Wilcoxon, t-test) or non-overlapping confidence intervals support the superiority claim.\n"
         "NO: superiority is claimed without such support.\nN/A: no claim that the model outperforms other models.",
         "NO",
         ("outperform", "superior", "better than", "state-of-the-art", "p <", "p-value", "p value", "statistically significant",
          "delong", "mcnemar", "wilcoxon", "t-test", "significance"),
         no_evidence_ok=("N/A",), gate={"YES": r"p\s?[<=>]|p-value|p value|signific|delong|mcnemar|wilcoxon|t-test|mann|friedman|chi|confidence interval|\bci\b"}, downgrade={"YES": "NO"}),
    Item("B4_baseline_protocol", "risk", RISK4,
         "Are comparisons with other methods made under the same data and protocol?",
         "SAFE: comparators are re-trained or re-evaluated on the same splits, or only the authors' own identically trained models are compared.\n"
         "RISK: a comparison reports numbers taken from other publications that used different data, splits or protocols, and it supports a superiority claim.\n"
         "UNCLEAR: a comparison exists but you cannot tell whether comparator numbers were reproduced or copied.\nN/A: no comparison with other methods.\n"
         "A comparison means the proposed model's performance is compared with other models, methods or human readers; expert labelling of the test set (the reference standard) is not a comparison. "
         "Comparison with readers, or with and without AI, on the same test cases: SAFE.",
         "N/A",
         ("compar", "comparison", "state-of-the-art", "previous studies", "existing methods", "reported in", "literature",
          "baseline", "re-implement", "same dataset", "same split", "benchmark", "table"),
         no_evidence_ok=("N/A",), downgrade={"SAFE": "UNCLEAR", "RISK": "UNCLEAR"}),
    Item("C1_code_available", "report", ("YES", "REQUEST", "NO"),
         "Is the study code publicly available?",
         "YES: a public repository link or DOI for the study code is given (also when phrased 'will be made available at <link>').\n"
         "REQUEST: code available on request.\nNO: not stated, stated as not available, or 'will be made available' with no link. "
         "Links only to other people's tools or libraries, or only to a preprocessing tool, are NO: the link must lead to the code that trains or evaluates this study's model.",
         "NO",
         ("code", "github", "gitlab", "zenodo", "repository", "source code", "available", "request", "implementation"),
         prefer_back=True, gate={"YES": r"https?://|github|gitlab|zenodo|bitbucket|figshare|osf\.io|doi|code ocean|huggingface", "REQUEST": r"request"}, downgrade={"YES": "NO", "REQUEST": "NO"}),
    Item("C2_data_available", "report", ("PUBLIC", "RESTRICTED", "NO"),
         "Are the data used publicly available?",
         "PUBLIC: all data used are publicly accessible and the source is named (a named public dataset such as ADNI, BraTS or Kaggle counts).\n"
         "RESTRICTED: available on request or through an access procedure (including when only part of the data is public). These boilerplate statements are RESTRICTED when the images are not in the article: "
         "'available on (reasonable) request', 'will be made available by the authors, without undue reservation', 'included in the article/supplementary material, further inquiries can be directed to the corresponding author', 'data are available within the article'. "
         "If every dataset used is a named public dataset, the label is PUBLIC even when the statement also mentions requests.\n"
         "NO: not available, or availability not stated.",
         "NO",
         ("data availability", "available", "publicly", "public", "dataset", "kaggle", "figshare", "request", "repository", "download", "access"),
         prefer_back=True, downgrade={"PUBLIC": "NO", "RESTRICTED": "NO"}),
)

ITEM_BY_CODE = {it.code: it for it in ITEMS}

# v1.3: the test set is annotated on these five items only (decided 2026-09-27, before any test labels were used)
TEST_ITEMS = ("A1_split_unit", "A4_test_for_selection", "B2_variability_reported", "C1_code_available", "C2_data_available")
ITEM_SETS = {"all": tuple(it.code for it in ITEMS), "test5": TEST_ITEMS}
RISK_ITEMS = tuple(it.code for it in ITEMS if it.kind == "risk")
LEAKAGE_ITEMS = ("A1_split_unit", "A2_preproc_before_split", "A3_aug_before_split", "A4_test_for_selection")
