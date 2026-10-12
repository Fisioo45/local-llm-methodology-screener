# Test-set results (n = 80) — pre-registered analysis (plan v1.0, OSF 6 Oct 2026)

All runs started after the registration; lock OK (gold SHA-256 483d4647…, code 3ed2afc7…, model digests as locked). No parse failures in any run.

## Table 1. Mean κ over five items and difference to rules (paired bootstrap, 2,000 resamples)

| System | Mean κ | Δ vs R [95% CI] | p | Δ vs M1 [95% CI] |
|---|---|---|---|---|
| Rules (R) | 0.429 | — | — | — |
| M1 qwen3:8b decomposed (primary) | 0.519 | +0.090 [+0.011, +0.174] | 0.026 | — |
| H1 hybrid (rules B2/C1 + M1) | 0.506 | +0.077 [+0.021, +0.131] | 0.011 | -0.013 [-0.079, +0.046] |
| M2 qwen3.5:9b decomposed | 0.557 | +0.129 [+0.048, +0.206] | 0.000 | +0.038 [-0.023, +0.101] |
| M3 llama3.1:8b decomposed | 0.422 | -0.007 [-0.086, +0.078] | 0.921 | — |
| M4 gemma3:4b decomposed | 0.332 | -0.097 [-0.175, -0.017] | 0.013 | — |
| P1 qwen3:8b direct | 0.554 | +0.125 [+0.033, +0.213] | 0.002 | +0.035 [-0.042, +0.112] |
| A-b900 (M1, budget 900) | 0.523 | +0.094 [+0.013, +0.180] | 0.019 | +0.004 [-0.061, +0.071] |
| A-b3600 (M1, budget 3,600) | 0.515 | +0.086 [+0.005, +0.172] | 0.038 | -0.004 [-0.049, +0.045] |
| A-k5 (M1, self-consistency k=5) | 0.529 | +0.100 [+0.019, +0.183] | 0.018 | +0.009 [-0.007, +0.027] |
| A-think (M1, thinking on) | 0.586 | +0.157 [+0.079, +0.240] | 0.000 | +0.067 [-0.008, +0.146] |

## Table 2. Per-item κ [95% CI]

| System | A1 split | A4 test selection | B2 variability | C1 code | C2 data |
|---|---|---|---|---|---|
| Rules (R) | 0.31 [0.15, 0.47] | 0.24 [0.14, 0.36] | 0.74 [0.58, 0.88] | 0.69 [0.46, 0.88] | 0.15 [0.05, 0.26] |
| M1 qwen3:8b decomposed (primary) | 0.37 [0.21, 0.52] | 0.12 [-0.04, 0.27] | 0.90 [0.80, 0.97] | 0.55 [0.28, 0.78] | 0.66 [0.52, 0.79] |
| H1 hybrid (rules B2/C1 + M1) | 0.37 [0.21, 0.52] | 0.12 [-0.04, 0.27] | 0.74 [0.58, 0.88] | 0.64 [0.38, 0.84] | 0.66 [0.52, 0.79] |
| M2 qwen3.5:9b decomposed | 0.27 [0.12, 0.42] | 0.19 [0.04, 0.35] | 0.80 [0.65, 0.92] | 0.79 [0.54, 0.96] | 0.74 [0.60, 0.86] |
| M3 llama3.1:8b decomposed | 0.22 [0.07, 0.38] | 0.01 [-0.14, 0.17] | 0.82 [0.68, 0.95] | 0.50 [0.26, 0.69] | 0.56 [0.40, 0.71] |
| M4 gemma3:4b decomposed | 0.46 [0.29, 0.61] | -0.01 [-0.05, 0.00] | 0.62 [0.44, 0.78] | 0.22 [0.05, 0.39] | 0.38 [0.22, 0.54] |
| P1 qwen3:8b direct | 0.35 [0.21, 0.50] | 0.35 [0.21, 0.49] | 0.80 [0.65, 0.92] | 0.68 [0.43, 0.87] | 0.59 [0.44, 0.74] |
| A-b900 (M1, budget 900) | 0.37 [0.21, 0.52] | 0.18 [0.01, 0.34] | 0.80 [0.65, 0.92] | 0.58 [0.31, 0.81] | 0.69 [0.56, 0.81] |
| A-b3600 (M1, budget 3,600) | 0.27 [0.11, 0.42] | 0.17 [0.01, 0.32] | 0.85 [0.72, 0.95] | 0.61 [0.35, 0.83] | 0.68 [0.55, 0.81] |
| A-k5 (M1, self-consistency k=5) | 0.35 [0.19, 0.50] | 0.14 [-0.02, 0.30] | 0.90 [0.80, 0.97] | 0.55 [0.28, 0.78] | 0.70 [0.56, 0.83] |
| A-think (M1, thinking on) | 0.27 [0.12, 0.42] | 0.24 [0.08, 0.40] | 0.87 [0.75, 0.97] | 0.84 [0.59, 1.00] | 0.71 [0.58, 0.84] |

## Table 3. Leakage detection (positive = RISK; paper level: A1 or A4 = RISK)

| System | A1 sens / PPV | A4 sens / PPV | Paper sens / PPV / κ |
|---|---|---|---|
| Rules (R) | 0.40 / 0.62 | 0.05 / 0.50 | 0.34 / 0.86 / 0.32 |
| M1 qwen3:8b decomposed (primary) | 0.20 / 0.57 | 0.48 / 0.25 | 0.54 / 0.43 / -0.01 |
| H1 hybrid (rules B2/C1 + M1) | 0.20 / 0.57 | 0.48 / 0.25 | 0.54 / 0.43 / -0.01 |
| M2 qwen3.5:9b decomposed | 0.10 / 0.33 | 0.38 / 0.30 | 0.40 / 0.44 / 0.00 |
| M3 llama3.1:8b decomposed | 0.20 / 0.24 | 0.19 / 0.14 | 0.54 / 0.44 / 0.01 |
| M4 gemma3:4b decomposed | 0.35 / 0.70 | 0.95 / 0.25 | 0.97 / 0.43 / -0.03 |
| P1 qwen3:8b direct | 0.05 / 0.33 | 0.29 / 0.35 | 0.34 / 0.60 / 0.17 |
| A-think (M1, thinking on) | 0.05 / 0.50 | 0.33 / 0.33 | 0.29 / 0.48 / 0.04 |

Gold: A1 RISK 20, A4 RISK 21, any leakage risk 35 of 80 papers.

## Table 4. Cost and evidence (RTX 4060 laptop, 8 GB)

| System | s / paper | peak VRAM (MiB) | output tokens / paper | quotes exact / fuzzy / unverified |
|---|---|---|---|---|
| Rules (R) | 0.0 | — | 0 | 100% / 0% / 0% |
| M1 qwen3:8b decomposed (primary) | 28.2 | 6,451 | 597 | 89% / 9% / 2% |
| H1 hybrid (rules B2/C1 + M1) | 17.9 | 6,451 | 395 | 90% / 8% / 2% |
| M2 qwen3.5:9b decomposed | 28.7 | 7,050 | 548 | 87% / 8% / 6% |
| M3 llama3.1:8b decomposed | 26.2 | 7,045 | 557 | 71% / 27% / 2% |
| M4 gemma3:4b decomposed | 22.1 | 5,848 | 621 | 9% / 80% / 11% |
| P1 qwen3:8b direct | 30.9 | 6,167 | 717 | 82% / 15% / 3% |
| A-b900 (M1, budget 900) | 25.1 | 6,509 | 539 | 91% / 7% / 2% |
| A-b3600 (M1, budget 3,600) | 30.4 | 6,306 | 566 | 85% / 12% / 3% |
| A-k5 (M1, self-consistency k=5) | 121.6 | 6,302 | 2887 | 85% / 12% / 3% |
| A-think (M1, thinking on) | 105.4 | 6,302 | 4093 | 57% / 34% / 9% |

Human annotation (same 5 items, codebook v1.3): median 5.0 min per paper (IQR 4–6, mean 5.6).

## Table 5. Prevalence in the 80 test papers (gold, Wilson 95% CI)

| Item | Label | n | % [95% CI] |
|---|---|---|---|
| A1_split_unit | SAFE | 33 | 41.2 [31.1, 52.2] |
| A1_split_unit | RISK | 20 | 25.0 [16.8, 35.5] |
| A1_split_unit | UNCLEAR | 27 | 33.8 [24.3, 44.6] |
| A4_test_for_selection | SAFE | 47 | 58.8 [47.8, 68.9] |
| A4_test_for_selection | RISK | 21 | 26.2 [17.9, 36.8] |
| A4_test_for_selection | UNCLEAR | 12 | 15.0 [8.8, 24.4] |
| B2_variability_reported | YES | 36 | 45.0 [34.6, 55.9] |
| B2_variability_reported | NO | 44 | 55.0 [44.1, 65.4] |
| C1_code_available | YES | 10 | 12.5 [6.9, 21.5] |
| C1_code_available | REQUEST | 0 | 0.0 [0.0, 4.6] |
| C1_code_available | NO | 70 | 87.5 [78.5, 93.1] |
| C2_data_available | PUBLIC | 31 | 38.8 [28.8, 49.7] |
| C2_data_available | RESTRICTED | 39 | 48.8 [38.1, 59.5] |
| C2_data_available | NO | 10 | 12.5 [6.9, 21.5] |
| PAPER_any_leakage_risk | FLAG | 35 | 43.8 [33.4, 54.7] |
| PAPER_not_verifiably_safe | FLAG | 61 | 76.2 [65.9, 84.2] |

## McNemar (M1 vs R, Holm over 5 items)

See `comparisons.csv`. Only C2 differs significantly: M1 correct and R wrong on 38 papers, the reverse on 6 (p_Holm < 0.001).
