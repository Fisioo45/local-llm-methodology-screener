"""Transparent keyword-rule baseline (the comparison reviewers will expect).

Rules were written a priori from codebook v1.0 (A2 updated for v1.1) and may only be tuned on the dev
set (pilot + dev). Each decision returns the matching sentences as evidence, so
every baseline label is auditable.
"""
import re

from .corpus import full_text

_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")


def sentences(text: str) -> list:
    out = []
    for para in text.split("\n"):
        out += [s.strip() for s in _SENT.split(para) if len(s.strip()) > 15]
    return out


def find(sents, pattern, flags=re.I, limit=2):
    rx = re.compile(pattern, flags)
    return [s for s in sents if rx.search(s)][:limit]


P = {
    "patient_split": r"patient[- ]?(level|wise|based|independent|disjoint)|subject[- ]?(level|wise|independent)|"
                     r"split (at|on|by) the (patient|subject|case)|no (patient|subject) (appear|overlap)|"
                     r"(patients|subjects) (were|was) (randomly )?(split|divided|assigned|allocated)|group(ed)?[- ]?k[- ]?fold|stratified group",
    "one_per_patient": r"one (image|scan|radiograph|slide) per (patient|subject)|each (patient|subject) contributed (only )?one",
    "image_split": r"(images|slices|patches|tiles|frames|samples|data(set)?) (were|was) (randomly )?(split|divided|partitioned|separated)|"
                   r"random(ly)? (split|divided|partitioned)|(\d{2}\s?%|\d{2}:\d{2}|\d\.\d) (for )?(training|train)",
    "multi_per_patient": r"\d[\d,]* (images|slices|scans|patches|frames|radiographs) (from|of|obtained from) \d[\d,]* (patients|subjects|cases)|"
                         r"slices|patches|tiles|frames|multiple (images|views)",
    "external": r"external (validation|test|cohort|dataset)|independent (external )?(test|validation) (set|cohort|dataset)|"
                r"(another|different|second|separate) (hospital|institution|center|centre|site)|multi-?cent(er|re)|cross-dataset",
    "data_dependent": r"smote|over-?sampl|under-?sampl|class balanc|feature selection|principal component|\bpca\b|lasso|"
                      r"z-score|standardi[sz](ed|ation) (the |of )?(features|intensit|data|values|radiomic)|"
                      r"normali[sz](ed|ation) (using|with|by) the (mean|global|dataset)|imputation|mrmr",
    "before_split": r"before (the )?(split|splitting|division|partition)|prior to (split|splitting|division|partition)|"
                    r"(entire|whole|full) dataset",
    "train_only": r"(training|train) (set|data|subset) only|only (on|to) the training|fitted (only )?on the training|within each fold|inside each fold",
    "augment": r"augment|synthetic (images|data)|\bgan\b|generative adversarial|diffusion model",
    "aug_before": r"(after|following) (data )?augmentation,? (the )?(dataset|images|data) (was|were) (split|divided)|"
                  r"augmented (dataset|data|images) (was|were) (split|divided|partitioned)|augment\w* (before|prior to) (split|splitting|division)",
    "aug_train_only": r"augment\w*[^.]{0,80}(only|exclusively) (to|on|for) the training|on-the-fly|during training|(applied|used) (only )?(to|on) the training (set|data|images)",
    "test_selection": r"(best|highest)[^.]{0,40}(on|in) the test (set|data)|early stopping[^.]{0,60}test|test (accuracy|loss)[^.]{0,40}(monitor|select|save)",
    "val_selection": r"validation (set|data|loss|accuracy)[^.]{0,80}(early stopping|hyper-?parameter|select|tun|checkpoint|monitor|best)|"
                     r"(early stopping|hyper-?parameter|tuning|checkpoint)[^.]{0,80}validation",
    "three_way": r"training,? validation,? and test(ing)? (sets|subsets)|train(ing)?/validation/test",
    "duplicate": r"duplicate|near-duplicate|de-?duplicat|perceptual hash|\bmd5\b|identical images|redundant images",
    "variability": r"±|\+/-|standard deviation|confidence interval|95\s?%\s?ci|\bci\b|mean of \d+ (runs|folds)|averaged over \d+|across (the )?(\d+|five|ten) folds",
    "claim": r"outperform|superior|better than|state-of-the-art|sota",
    "stat_test": r"delong|mcnemar|wilcoxon|t-test|mann-whitney|friedman|p\s?[<=]\s?0?\.\d|p-value|statistically significant",
    "compare_prior": r"(compared|comparison) (with|to|against) (the )?(existing|previous|prior|recent|state-of-the-art|other) "
                     r"(studies|methods|works|approaches|models|literature)|reported in (the literature|previous studies|prior studies)",
    "reimplemented": r"\bre-?implement|\bre-?train(ed|ing)?\b|(same|identical) (dataset|data split|split|experimental setting|conditions|protocol|training)",
    "code_public": r"github\.com|gitlab|zenodo|code (is|are) (publicly )?available at|source code[^.]{0,60}(available|https?://)",
    "code_request": r"code[^.]{0,80}(upon|on) (reasonable )?request",
    "data_public": r"publicly available|public(ly)? (dataset|database|repository)|open-?access dataset|kaggle|figshare|"
                   r"the cancer imaging archive|\btcia\b|available (at|from) https?://|downloaded from",
    "data_request": r"(available|provided|obtained)[^.]{0,60}(upon|on) (reasonable )?request|not publicly available|restricted access",
}


EXCLUDE_SEC = re.compile(r"introduction|background|related work|literature|previous work|discussion|conclusion|"
                         r"limitation|future work|acknowledg|author contribution|conflict|funding", re.I)
METRIC = r"accuracy|auc|auroc|f1|sensitivity|specificity|precision|recall|dice|kappa|mcc|error rate"
SPLIT_VERB = r"split|divid|partition|assign|allocat|separat|fold|held[- ]out|hold[- ]out|test (set|cohort)|training (set|cohort)"


def predict_paper(paper: dict) -> dict:
    # Methods/results text only: introductions and discussions describe OTHER studies.
    body = "\n".join(sec["text"] for sec in paper["sections"] if not EXCLUDE_SEC.search(sec["path"]))
    sents = sentences(paper.get("abstract", "") + "\n" + body)
    back = sentences("\n".join(b["text"] for b in paper["back"]))
    avail = back + sents
    out = {}

    def put(code, label, ev):
        out[code] = {"label": label, "evidence": ev[:3]}

    # A1 split unit
    safe = [x for x in find(sents, P["patient_split"], limit=5) if re.search(SPLIT_VERB, x, re.I)][:2]
    safe += find(sents, P["one_per_patient"]) + [x for x in find(sents, P["external"], limit=5)
                                                  if re.search(r"test|validat|evaluat", x, re.I)][:1]
    img, multi = find(sents, P["image_split"]), find(sents, P["multi_per_patient"])
    if safe:
        put("A1_split_unit", "SAFE", safe)
    elif img and multi:
        put("A1_split_unit", "RISK", img[:1] + multi[:1])
    else:
        put("A1_split_unit", "UNCLEAR", img[:1])

    # A2 data-dependent preprocessing before split
    dd = find(sents, P["data_dependent"], limit=5)
    dd_before = [s for s in dd if re.search(P["before_split"], s, re.I)]
    dd_train = [s for s in dd if re.search(P["train_only"], s, re.I)]
    if dd_before:
        put("A2_preproc_before_split", "RISK", dd_before)
    elif dd_train:
        put("A2_preproc_before_split", "SAFE", dd_train)
    elif not dd:
        put("A2_preproc_before_split", "N/A", [])        # codebook v1.1: no data-dependent step
    else:
        put("A2_preproc_before_split", "UNCLEAR", dd[:1])

    # A3 augmentation before split
    aug = find(sents, P["augment"], limit=5)
    if not aug:
        put("A3_aug_before_split", "N/A", [])
    elif find(sents, P["aug_before"]):
        put("A3_aug_before_split", "RISK", find(sents, P["aug_before"]))
    elif find(sents, P["aug_train_only"]):
        put("A3_aug_before_split", "SAFE", find(sents, P["aug_train_only"]))
    else:
        put("A3_aug_before_split", "UNCLEAR", aug[:1])

    # A4 test set used for selection
    if find(sents, P["test_selection"]):
        put("A4_test_for_selection", "RISK", find(sents, P["test_selection"]))
    elif find(sents, P["val_selection"]) or find(sents, P["three_way"]):
        put("A4_test_for_selection", "SAFE", find(sents, P["val_selection"]) + find(sents, P["three_way"], limit=1))
    else:
        put("A4_test_for_selection", "UNCLEAR", [])

    dup = find(sents, P["duplicate"])
    put("A5_duplicate_check", "YES" if dup else "NO", dup)
    ext = find(sents, P["external"])
    put("B1_external_validation", "YES" if ext else "NO", ext)
    var = [x for x in find(sents, P["variability"], limit=20) if re.search(METRIC, x, re.I)][:2]
    put("B2_variability_reported", "YES" if var else "NO", var)

    claim = find(sents, P["claim"])
    test = [x for x in find(sents, P["stat_test"], limit=20) if re.search(METRIC + r"|model|method|classifier", x, re.I)][:2]
    put("B3_stat_test_for_claim", "N/A" if not claim else ("YES" if test else "NO"), test if claim and test else claim[:1])

    prior, reimp = find(sents, P["compare_prior"]), find(sents, P["reimplemented"])
    if not prior and not claim:
        put("B4_baseline_protocol", "N/A", [])
    elif reimp:
        put("B4_baseline_protocol", "SAFE", reimp)
    elif prior:
        put("B4_baseline_protocol", "RISK", prior)
    else:
        put("B4_baseline_protocol", "UNCLEAR", claim[:1])

    code_pub, code_req = find(avail, P["code_public"]), find(avail, P["code_request"])
    put("C1_code_available", "YES" if code_pub else "REQUEST" if code_req else "NO", code_pub or code_req)

    d_pub, d_req = find(avail, P["data_public"]), find(back, P["data_request"])
    put("C2_data_available", "RESTRICTED" if d_req else "PUBLIC" if d_pub else "NO", d_req or d_pub)
    return out
