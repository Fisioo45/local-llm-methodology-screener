# Annotation Guide v1.3 — 5 items, 80 test papers

This guide replaces v1.2 for all **test** papers (row 48 onwards). The label rules are the same as before for these five items; this version only explains them more simply and removes the other six items.

---

## 1. What you are doing, in three sentences

For each paper you answer 5 questions about how the study was done or reported.
Your answers are the **answer key**: the AI screener will answer the same 5 questions, and the paper reports how often it agrees with you.
So every answer must come from **reading that paper**, and every "yes-type" answer needs a sentence copied from it.

---

## 2. The routine for every paper (about 6–10 minutes)

1. **Open one paper only.** Click the "Europe PMC" link in the row. Close every other paper tab.
2. **Eligible?** Write **Y** if the paper *trains or fine-tunes* a model that *classifies medical images* and reports results on held-out data. Otherwise **N** and write why (review, segmentation only, no training, non-image input such as signals or fMRI connectivity, not medical). If N: go to step 7.
3. **Read these parts** (skim the rest):
   - the Abstract;
   - Methods: the dataset, how the data were split, how the model was trained, how it was evaluated;
   - the main Results table;
   - the **Data availability / Code availability** statements (usually at the very end, before the references).
4. **Answer the 5 items** (section 3). For each item, use **Ctrl+F** with the search words before you choose a "not reported" answer (UNCLEAR or NO).
5. **Copy the evidence.** Select the sentence in the browser, Ctrl+C, click the evidence cell, Ctrl+V. Never type or rephrase it (section 4).
6. **Fill** `minutes`, `annotated_on` (date) and `codebook_version` = **1.3**.
7. **Close the tab**, go to the next row.

Do not type in the `set` or `status` columns; they fill themselves.
If a paper took less than 4 minutes, look at it again: that is too fast to read the parts in step 3.

---

## 3. The five items

For each item, go through the steps **in order** and stop at the first one that fits.

### A1 — Could the same patient be in both training and test data?

**Where to look:** Methods (dataset, data split); dataset table.
**Search words:** patient, subject, split, divid, fold, slice, patch, per patient, external

| Step | If the paper says… | Label |
|---|---|---|
| 1 | the split was done **by patient / subject / case** ("patient-level split", "no patient appears in both sets", "patients were randomly assigned", grouped cross-validation by patient) | **SAFE** |
| 2 | the main test set comes from a **different hospital, centre, cohort or dataset** | **SAFE** |
| 3 | each patient has **only one image** | **SAFE** |
| 4 | **images / slices / patches / frames** were split randomly **and** the paper shows there are more images than patients (e.g. "3,000 images from 1,000 patients", slices from CT/MRI volumes, patches from slides, frames from videos) | **RISK** |
| 5 | anything else (e.g. only "80% training, 20% testing" with no word about patients) | **UNCLEAR** |

Examples
- "Patients were randomly divided into training (n = 300) and test (n = 100) cohorts." → **SAFE** (step 1)
- "The 12,000 slices from 150 MRI scans were randomly split 80:20." → **RISK** (step 4)
- "The dataset was split into 80% training and 20% testing." → **UNCLEAR** (step 5)

Evidence: quote the split sentence (and the images-per-patient sentence for RISK). For UNCLEAR you may quote the split sentence, or write ABSENT if there is none.

---

### A4 — Was the test set used to make choices while building the model?

Choices = choosing the best epoch/checkpoint, early stopping, tuning hyperparameters, choosing the final model or threshold.
**Where to look:** Methods (training details, evaluation); Results.
**Search words:** validation, early stop, checkpoint, best model, hyperparameter, tuning, grid search, epoch

| Step | If the paper says… | Label |
|---|---|---|
| 1 | the best model / checkpoint / epoch was chosen **on the test set**, or early stopping / tuning used the test set | **RISK** |
| 2 | only **two** sets exist, and the second set is used **during training** (monitoring, early stopping, choosing the best epoch) **and** its results are the reported results | **RISK** |
| 3 | several models were compared on the test set and **the best one was then adopted** as the proposed/final model | **RISK** |
| 4 | **three separate sets** (training, validation, test): choices on validation, test used only at the end — or nested cross-validation, or hyperparameters fixed in advance | **SAFE** |
| 5 | anything else (e.g. "80/20 split", nothing about how epochs or hyperparameters were chosen) | **UNCLEAR** |

Careful: some papers call their final set "validation". Judge by **what the set is used for**, not by its name.

Examples
- "We saved the model with the highest accuracy on the test set." → **RISK** (step 1)
- "Data were split into training (70%), validation (15%) and test (15%) sets; early stopping monitored the validation loss." → **SAFE** (step 4)

---

### B2 — Is the main result reported with a ± or a confidence interval?

**Where to look:** Abstract, main Results table, Results text.
**Search words:** ±, CI, confidence, SD, standard deviation, 95%

| Step | If the paper… | Label |
|---|---|---|
| 1 | reports a **performance number** (accuracy, AUC, sensitivity, specificity, F1, Dice…) **with** ± / SD / range over folds or runs / per-fold results / a **confidence interval** — in text or in a table | **YES** |
| 2 | otherwise | **NO** |

Does NOT count: "we used 5-fold cross-validation" without the spread; ± on patient age or other demographics; confidence intervals of a *cited* study; a significance test or p-value on its own (z-test, t-test, DeLong, McNemar); a CI only for the *difference* between two models.

Examples
- "The model achieved an accuracy of 93% ± 4%." → **YES**
- "AUC 0.91 (95% CI 0.87–0.94)." → **YES**
- "Five-fold cross-validation gave a mean accuracy of 0.92." → **NO**

---

### C1 — Can readers get this study's code?

**Where to look:** Code availability / Data availability statements, the end of Methods, footnotes.
**Search words:** github, gitlab, zenodo, code, repository, doi

| Step | If the paper… | Label |
|---|---|---|
| 1 | gives a **link or DOI to this study's code** (the code that trains or evaluates their model) — also "will be made available at https://…" | **YES** |
| 2 | says the code is available **on request** | **REQUEST** |
| 3 | anything else: no statement; "code will be available" **without** a link; links only to **other people's** tools or libraries (e.g. PyTorch, a YOLO repository) or only to a preprocessing tool | **NO** |

**C1 is only about CODE.** A *Data* availability statement ("data are available on request", "included in the article…") says nothing about code: it decides C2, not C1. If the paper says nothing about its code, C1 = **NO**. The quote for YES or REQUEST must mention code, software, a repository or a link.

---

### C2 — Can readers get the data?

**Where to look:** the Data availability statement (end of paper) and the dataset section of Methods.
**Search words:** availab, request, public, dataset, kaggle, repository

| Step | If… | Label |
|---|---|---|
| 1 | **every** dataset used is a **named public dataset** (e.g. BraTS, ADNI, a Kaggle or TCIA dataset, "publicly available at https://…"), or the authors deposited their data with a link/DOI | **PUBLIC** |
| 2 | the statement says the data are available **on request**, from the corresponding author, through an access procedure, "without undue reservation", "included in the article/supplementary material, further inquiries can be directed to the corresponding author", or "available within the article"; or some data are public and some are private | **RESTRICTED** |
| 3 | the statement says the data are **not available** (and gives no request option), or there is no statement and the data are not public | **NO** |

Step 1 comes first: if all data are public, the label is PUBLIC even if the statement also mentions requests.

Examples
- "The datasets are available from the corresponding author on reasonable request." → **RESTRICTED**
- "The original contributions presented in the study are included in the article/supplementary material, further inquiries can be directed to the corresponding author." → **RESTRICTED**
- "Publicly available datasets were analyzed in this study. This data can be found here: https://…" → **PUBLIC**
- "The data are not publicly available due to privacy restrictions." → **NO**

---

## 4. Evidence rules

- **Copy-paste only.** The checker compares your quote with the paper; a rephrased sentence fails.
- One or two short spans (up to about 40 words each). Join two spans with ` || `.
- **SAFE, RISK, YES, REQUEST, PUBLIC, RESTRICTED always need a quote.**
- For UNCLEAR or NO: quote the closest relevant sentence if there is one, otherwise write **ABSENT**.
- Your thinking goes in `notes`, never in the evidence cell.

---

## 5. Before you send a batch of 20

In Anaconda Prompt, in the screener folder:

```
python -m mrscreen.check_annotations annotation_sheet_v1.3.xlsx --from 48
```

Fix every line it prints:

- **NOT_IN_PAPER** – the quote is not in that paper. Copy it again from the paper.
- **IN_OTHER_PAPER** – you copied from the wrong tab. Open the right paper and redo that item.
- **NO_EVIDENCE** – add the quote.
- **POSSIBLE_MISS** – the paper contains something like a GitHub link, a 95% CI or an availability statement while your label says NO. Open the paper at that sentence and decide. Keep NO only if the sentence really does not change the answer (for example, a link to someone else's tool, or a data link under C1). **If you keep your label, write `checked C1` (or `checked B2`, `checked C2`) in notes** — the checker then stops showing that flag.
- **NOT_CODE** – C1 is YES or REQUEST but your quote is about data, not code. Change C1 to NO unless the paper has a separate sentence about its code.

Send the file when the checker prints **OK – nothing to fix.**

---

## 6. Mistakes seen in earlier batches (so you can avoid them)

- Data availability statements that say "on request" or "included in the article… further inquiries…" were labelled NO. They are **RESTRICTED**.
- Results with "± 4%" or "95% CI" were labelled B2 = NO. They are **YES**.
- A code link in a "Code availability" section was labelled NO. It is **YES**.
- Quotes were pasted into the row of a different paper (several tabs open). Use one tab.
- Every paper got the same number of minutes. Write the real time.
- Data availability statements were used for C1 (code). "Data on request" is C2 = RESTRICTED; it does not make C1 = REQUEST.

---

## 7. One-page summary

| Item | Question | Labels | Must search |
|---|---|---|---|
| A1 | Same patient in training and test? | SAFE / RISK / UNCLEAR | patient, split, slice, patch |
| A4 | Test set used for choices? | SAFE / RISK / UNCLEAR | validation, early stop, best model |
| B2 | ± or CI with the main result? | YES / NO | ±, CI, confidence, SD |
| C1 | Study code available? | YES / REQUEST / NO | github, code, zenodo |
| C2 | Data available? | PUBLIC / RESTRICTED / NO | availab, request, public |

---

## 8. After all 80 test papers

- Wait at least **3 weeks**, then re-annotate **16 randomly chosen test papers** (I will send the list) without looking at your first answers. This measures your own consistency and goes into the paper.
- Optional but strongly recommended: a colleague annotates **20 test papers** with this guide (about 2–3 hours); they are thanked in the Acknowledgements.

## 9. Change log

- v1.3 clarification (2026-10-02): B2 — a significance test or p-value alone (e.g. a two-proportion z-test), or a CI only for the difference between two models, does not count as variability.
- v1.3 clarification (2026-09-29): C1 is only about code — data statements never decide C1; "checked <item>" in notes silences a POSSIBLE_MISS flag after re-reading; the checker accepts "no evidence"/"none" as ABSENT.
- v1.3 (2026-09-27) — test annotation reduced to five items (A1, A4, B2, C1, C2) and 80 papers, decided before any test labels were used; plain-language guide with ordered decision steps; clarifications: C1 excludes links to other people's tools or preprocessing-only code; C2 treats "available within the article" as RESTRICTED and public datasets take precedence; A4 judges sets by their use, not their name. Earlier rules: codebook_v1.2.md.
