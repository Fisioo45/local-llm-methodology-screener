"""Decomposed prompting (prompt p2.x), designed on the dev set after round 1.

p2.2 (2026-10-05, dev only, before any test run): B2 and C2 sub-questions aligned with codebook v1.3
(B2: any performance metric of the own model incl. CV results; C2: partly public data -> RESTRICTED).

Round 1 showed that small models misuse the label vocabulary (e.g. UNCLEAR when
the codebook says N/A, YES for B2 whenever cross-validation is mentioned). Here
the model only answers short factual sub-questions about the text; the codebook
decision rules are applied deterministically in code (map_label). The model
still has to supply verbatim evidence for its answers.
"""
from .items import ITEM_BY_CODE

PROMPT_VERSION = "p2.2"

YN = ["yes", "no"]
YNU = ["yes", "no", "not_stated"]

# item -> list of (field, allowed values or "list", question)
FACTS = {
    "A1_split_unit": [
        ("split_level", ["patient_or_subject_or_case", "image_slice_patch_or_frame", "not_stated"],
         "At what level does the text say the data were divided into training and test sets (or folds)? Choose not_stated if it only says the data/images were split without naming the unit."),
        ("test_is_separate_cohort", YN, "Is the test set a separate cohort, institution, site or dataset from the training data?"),
        ("one_image_per_patient", YNU, "Does the text state that each patient contributes only one image/scan?"),
        ("several_images_per_patient", YNU, "Does the text indicate several images, slices, patches or frames per patient (e.g. more images than patients)?"),
    ],
    "A2_preproc_before_split": [
        ("data_dependent_steps", "list",
         "List ONLY steps that learn from several samples at once: normalisation using dataset-wide statistics, feature selection, PCA or other dimensionality reduction, SMOTE/over-/under-sampling, imputation, learned harmonisation. "
         "Do NOT list resizing, cropping, filtering, fixed scaling, ImageNet mean/std, per-image normalisation, 'normalisation' without dataset statistics, or augmentation. Empty list if none."),
        ("fitted_on", ["training_data_only_or_within_folds", "full_dataset_before_split", "not_stated", "no_such_step"],
         "For the listed steps: on which data were they fitted? no_such_step if the list is empty."),
    ],
    "A3_aug_before_split": [
        ("augmentation_or_synthetic_used", YN, "Is data augmentation or synthetic-image generation (GAN, diffusion) used?"),
        ("timing", ["training_set_only_or_on_the_fly", "before_the_split", "not_stated", "not_used"],
         "When was it applied relative to the train/test split?"),
        ("split_grouped_by_source", YN, "Does the text say augmented or synthetic copies were kept in the same set as their source patient or image?"),
    ],
    "A4_test_for_selection": [
        ("design", ["train_validation_test", "train_test_only", "cross_validation_only", "not_stated"],
         "Which evaluation design is described?"),
        ("reported_set_used_for_decisions", YNU,
         "Was the set whose results are reported also used for early stopping, checkpoint/epoch selection, hyperparameter tuning or threshold selection?"),
        ("best_model_chosen_on_reported_set", YN,
         "Were several models compared on the reported set and the best one then adopted as the final/proposed model?"),
        ("nested_cv_or_fixed_hyperparameters", YN, "Does the text state nested cross-validation, or hyperparameters fixed in advance?"),
    ],
    "A5_duplicate_check": [
        ("duplicate_check_reported", YN, "Does the text describe checking for duplicate or near-duplicate images?"),
    ],
    "B1_external_validation": [
        ("external_test", ["different_institution_site_or_dataset", "same_source_only", "temporal_only"],
         "Is the final model tested on data from an institution, site or dataset NOT used for training or tuning?"),
    ],
    "B2_variability_reported": [
        ("spread_or_ci_reported", YN,
         "Is a performance metric of the authors' own model (accuracy, AUC, sensitivity, Dice, F1...) reported WITH its spread (± SD, range, per-fold values) or a confidence interval, in the text or a table? Mentioning cross-validation or a mean alone is not enough; a p-value or significance test alone is not enough; ± on patient age or other demographics does not count."),
    ],
    "B3_stat_test_for_claim": [
        ("superiority_claim", YN, "Does the article claim its model outperforms other models, methods or readers?"),
        ("statistical_support", YN,
         "Is that claim supported by a statistical test (DeLong, McNemar, Wilcoxon, t-test, p-value) or non-overlapping confidence intervals?"),
    ],
    "B4_baseline_protocol": [
        ("compares_with_other_methods_or_readers", YN,
         "Is the proposed model's performance compared with other models, methods or human readers? (Expert labelling of the test set is not a comparison.)"),
        ("comparator_source", ["retrained_or_evaluated_on_same_data", "numbers_taken_from_other_papers", "own_models_only", "not_stated", "no_comparison"],
         "Where do the comparator results come from?"),
    ],
    "C1_code_available": [
        ("code_link", "string", "Copy the URL or DOI given for THIS study's model code, or empty string if none. Links to other people's tools/libraries or to a preprocessing tool only do not count."),
        ("code_on_request", YN, "Does the text say the code is available on request?"),
    ],
    "C2_data_available": [
        ("all_data_public_and_named", YN, "Are all data used publicly accessible with the source named (e.g. a public dataset such as ADNI, BraTS, Kaggle, or a repository link)?"),
        ("available_on_request_or_restricted", YN,
         "Does the text say data are available on request, through an access procedure, 'without undue reservation', 'included in the article' / 'further inquiries to the corresponding author', or 'available within the article'? Answer yes also when only SOME of the datasets used are public and the others are not."),
    ],
}


def schema(code: str) -> dict:
    props = {"evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 3}}
    for name, allowed, _ in FACTS[code]:
        if allowed == "list":
            props[name] = {"type": "array", "items": {"type": "string"}, "maxItems": 6}
        elif allowed == "string":
            props[name] = {"type": "string"}
        else:
            props[name] = {"type": "string", "enum": allowed}
    return {"type": "object", "properties": props, "required": list(props)}


def questions(code: str) -> str:
    lines = []
    for name, allowed, q in FACTS[code]:
        opts = "a list of strings" if allowed == "list" else "a string" if allowed == "string" else " | ".join(allowed)
        lines.append(f"- {name} ({opts}): {q}")
    return "\n".join(lines)


def _g(f, k, default="not_stated"):
    v = f.get(k, default)
    return v if v is not None else default


def map_label(code: str, f: dict) -> str:
    """Codebook v1.1 decision rules applied to the model's factual answers."""
    if not isinstance(f, dict) or not f:
        return None
    if code == "A1_split_unit":
        if _g(f, "split_level") == "patient_or_subject_or_case" or _g(f, "test_is_separate_cohort") == "yes" \
                or _g(f, "one_image_per_patient") == "yes":
            return "SAFE"
        if _g(f, "split_level") == "image_slice_patch_or_frame" and _g(f, "several_images_per_patient") == "yes":
            return "RISK"
        return "UNCLEAR"
    if code == "A2_preproc_before_split":
        steps = [s for s in (f.get("data_dependent_steps") or []) if isinstance(s, str) and s.strip()]
        fit = _g(f, "fitted_on")
        if not steps or fit == "no_such_step":
            return "N/A"
        return {"full_dataset_before_split": "RISK", "training_data_only_or_within_folds": "SAFE"}.get(fit, "UNCLEAR")
    if code == "A3_aug_before_split":
        if _g(f, "augmentation_or_synthetic_used", "no") == "no" or _g(f, "timing") == "not_used":
            return "N/A"
        t = _g(f, "timing")
        if t == "training_set_only_or_on_the_fly":
            return "SAFE"
        if t == "before_the_split":
            return "SAFE" if _g(f, "split_grouped_by_source", "no") == "yes" else "RISK"
        return "UNCLEAR"
    if code == "A4_test_for_selection":
        if _g(f, "reported_set_used_for_decisions") == "yes" or _g(f, "best_model_chosen_on_reported_set", "no") == "yes":
            return "RISK"
        d = _g(f, "design")
        if d == "train_validation_test":
            return "SAFE"
        if d == "cross_validation_only" and _g(f, "nested_cv_or_fixed_hyperparameters", "no") == "yes":
            return "SAFE"
        return "UNCLEAR"
    if code == "A5_duplicate_check":
        return "YES" if _g(f, "duplicate_check_reported", "no") == "yes" else "NO"
    if code == "B1_external_validation":
        return "YES" if _g(f, "external_test") == "different_institution_site_or_dataset" else "NO"
    if code == "B2_variability_reported":
        return "YES" if _g(f, "spread_or_ci_reported", "no") == "yes" else "NO"
    if code == "B3_stat_test_for_claim":
        if _g(f, "superiority_claim", "no") == "no":
            return "N/A"
        return "YES" if _g(f, "statistical_support", "no") == "yes" else "NO"
    if code == "B4_baseline_protocol":
        src = _g(f, "comparator_source")
        if _g(f, "compares_with_other_methods_or_readers", "no") == "no" or src == "no_comparison":
            return "N/A"
        return {"numbers_taken_from_other_papers": "RISK", "retrained_or_evaluated_on_same_data": "SAFE",
                "own_models_only": "SAFE"}.get(src, "UNCLEAR")
    if code == "C1_code_available":
        link = (f.get("code_link") or "").strip()
        if link and any(k in link.lower() for k in ("http", "github", "gitlab", "zenodo", "doi", "bitbucket", "figshare", "osf", "huggingface")):
            return "YES"
        return "REQUEST" if _g(f, "code_on_request", "no") == "yes" else "NO"
    if code == "C2_data_available":
        if _g(f, "all_data_public_and_named", "no") == "yes":
            return "PUBLIC"
        return "RESTRICTED" if _g(f, "available_on_request_or_restricted", "no") == "yes" else "NO"
    raise KeyError(code)


def messages(code: str, context: str, title: str, system: str) -> list:
    it = ITEM_BY_CODE[code]
    user = (
        f"TOPIC: {it.question}\n\n"
        f"ARTICLE: {title}\nEXCERPTS (selected passages, in document order; [P#] are passage ids):\n<<<\n{context}\n>>>\n\n"
        "Answer these questions about the excerpts only. If the excerpts do not say, choose not_stated / no / empty.\n"
        f"{questions(code)}\n\n"
        'Return JSON with "evidence" first (0-3 verbatim quotes, at most 40 words each, that support your answers; '
        "empty list if the text is silent), then one key per question in the order given."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
