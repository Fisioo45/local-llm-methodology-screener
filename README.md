# Local-LLM methodology-risk screener for deep-learning medical-imaging papers

Code, data and results for:

> E. F. Çelik, "Can Small Local Language Models Screen Deep-Learning Medical-Imaging Papers for Methodology Risks? A Preregistered Evaluation Against a Human Gold Standard" (manuscript under review).

The screener reads the full text of a published deep-learning medical-imaging classification paper and labels five items, each with a verbatim evidence quote that is checked against the paper:

| Item | Question |
|---|---|
| A1 | Was the train/test split made at patient level? |
| A4 | Was the reported test set used to choose or tune the model? |
| B2 | Is performance reported with variability (± / CI)? |
| C1 | Is the study's code available? |
| C2 | Are the data available? |

It runs locally with 4-bit open-weight models (Ollama) on a single 8 GB GPU. A transparent keyword-rule baseline is included.

## Preregistration and test lock
- Analysis plan v1.0: `docs/analysis_plan.md`, registered on OSF on 6 October 2026 before any test run.
- `configs/test_lock.json` fixes the gold-standard hash, a fingerprint of the code that turns a paper into a label, and the Ollama model digests. `mrscreen.run` refuses the test set if any of them differ.
- Gold-standard hash: `sha256sum data/gold/gold_frozen.csv` → `483d4647fe6fea7afccaedc6b7a120a17e6a9353b5d832c5d88e0bb3569d8667`

## Repository layout
| Path | Contents |
|---|---|
| `mrscreen/` | Screener package: retrieval (BM25), prompts (direct p1.1, decomposed p2.2), evidence verification, keyword rules, hybrid, runner, evaluation and statistics |
| `docs/` | Codebook (v1.0–v1.3; test labels use v1.3) and the preregistered analysis plan |
| `data/processed/` | Corpus frame (542 papers: PMCID, DOI, licence), random annotation order, parsed full texts |
| `data/gold/gold_frozen.csv` | Frozen gold labels and evidence quotes (40 pilot/development + 80 test papers) |
| `annotation_sheet_v1.3.xlsx` | Annotation workbook (same labels; used by the runner to assign sets) |
| `configs/` | Experiment plan, test lock, gold freeze record, re-rating selection |
| `runs/dev_round3/`, `runs/test/` | Model outputs: one JSON line per paper × item, with label, quotes, verification status, tokens and timing |
| `results/` | Evaluation tables (`TEST_RESULTS.md`, metrics, paired-bootstrap differences, McNemar tests, efficiency, prevalence) |
| `scripts/` | Corpus pipeline (01–05) and the Windows batch files used for the development and test runs |
| `tests/` | Unit tests (`python -m pytest -q tests`) |

## Quick start
```
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q tests
python -m mrscreen.freeze annotation_sheet_v1.3.xlsx --verify   # gold unchanged
python -m mrscreen.lock                                         # code matches the lock
```

### Reproduce the evaluation from the released outputs (no GPU needed)
```
python -m mrscreen.evaluate --set test --items test5 --boot 2000 --out results/repro --runs ^
  runs/test/rules_per_item_i5_b1800_k1_test ^
  runs/test/ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_test ^
  runs/test/hybrid__ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_test
```
The first run given is the baseline for `mean_kappa_diff.csv` (the primary endpoint).

### Re-run the models
Install Ollama, pull `qwen3:8b`, `qwen3.5:9b`, `llama3.1:8b` and `gemma3:4b`, and check that their digests match `configs/test_lock.json`. Then, for example:
```
python -m mrscreen.run --backend ollama --model qwen3:8b --think off --prompt decomposed --items test5 --set test --frozen
```
`scripts/run_test_core.bat` and `scripts/run_test_ablations.bat` contain all preregistered test runs. The test set runs only when the gold hash, code fingerprint and model digest match the lock.

## Licences
- Code: MIT (see `LICENSE`).
- Annotations, codebook, gold standard and results: CC BY 4.0.
- Article texts and quotes in `data/processed/papers/` and in the outputs come from openly licensed (CC BY or CC0) articles retrieved from Europe PMC; each keeps its original licence. Authors, DOIs and licences are listed in `data/processed/frame.json`.

## Citation
See `CITATION.cff`. Please cite the archived release (Zenodo DOI) and the article.
