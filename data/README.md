# Rater reliability (20 test papers)

The 20 papers were drawn at random from the 80 test papers (seed 20261005; list in `configs/rerating_selection.json`).

| File | Contents |
|---|---|
| `rerating_author.xlsx` | Author's blind second pass (codebook v1.3), at least two weeks after the first pass |
| `rating_second_rater.xlsx` | Independent second rater (same codebook; trained on 3 development papers; added after registration) |

Agreement tables are in `results/reliability/`:
- `agreement_intra.csv`: gold standard vs author's second pass
- `agreement_inter_gold.csv`: gold standard vs second rater
- `agreement_inter_rerate.csv`: author's second pass vs second rater

Reproduce:
```
python -m mrscreen.evaluate --intra-rater annotation_sheet_v1.3.xlsx data/reliability/rerating_author.xlsx --items test5 --out results/reliability_repro
python -m mrscreen.evaluate --intra-rater annotation_sheet_v1.3.xlsx data/reliability/rating_second_rater.xlsx --items test5 --out results/reliability_repro
```
