# Results on 'test' (80 gold papers)

Mean kappa excludes items whose gold labels have a single class (kappa undefined): none

| run | policy | mean kappa | mean macro-F1 | any-RISK sens | any-RISK PPV | not-verifiable sens | not-verifiable spec |
|---|---|---|---|---|---|---|---|
| rules_per_item_i5_b1800_k1_test | raw | 0.429 | 0.596 | 0.343 | 0.857 | 0.902 | 0.316 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_test | raw | 0.514 | 0.692 | 0.543 | 0.432 | 0.787 | 0.263 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_test | verified | 0.505 | 0.684 | 0.543 | 0.432 | 0.787 | 0.211 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_test | gated | 0.519 | 0.691 | 0.543 | 0.432 | 0.820 | 0.211 |
| hybrid__ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_test | raw | 0.515 | 0.689 | 0.543 | 0.432 | 0.787 | 0.263 |
| hybrid__ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_test | verified | 0.513 | 0.686 | 0.543 | 0.432 | 0.787 | 0.211 |
| hybrid__ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_test | gated | 0.506 | 0.683 | 0.543 | 0.432 | 0.820 | 0.211 |
| ollama_qwen3.5-9b_per_item_p22_i5_b1800_k1_think-off_test | raw | 0.513 | 0.709 | 0.457 | 0.471 | 0.852 | 0.421 |
| ollama_qwen3.5-9b_per_item_p22_i5_b1800_k1_think-off_test | verified | 0.501 | 0.701 | 0.400 | 0.438 | 0.869 | 0.421 |
| ollama_qwen3.5-9b_per_item_p22_i5_b1800_k1_think-off_test | gated | 0.557 | 0.711 | 0.400 | 0.438 | 0.885 | 0.316 |
| ollama_llama3.1-8b_per_item_p22_i5_b1800_k1_think-default_test | raw | 0.414 | 0.636 | 0.543 | 0.442 | 0.770 | 0.158 |
| ollama_llama3.1-8b_per_item_p22_i5_b1800_k1_think-default_test | verified | 0.410 | 0.632 | 0.543 | 0.442 | 0.770 | 0.158 |
| ollama_llama3.1-8b_per_item_p22_i5_b1800_k1_think-default_test | gated | 0.422 | 0.643 | 0.543 | 0.442 | 0.869 | 0.053 |
| ollama_gemma3-4b_per_item_p22_i5_b1800_k1_think-default_test | raw | 0.272 | 0.491 | 1.000 | 0.438 | 1.000 | 0.000 |
| ollama_gemma3-4b_per_item_p22_i5_b1800_k1_think-default_test | verified | 0.257 | 0.484 | 0.971 | 0.430 | 1.000 | 0.000 |
| ollama_gemma3-4b_per_item_p22_i5_b1800_k1_think-default_test | gated | 0.332 | 0.538 | 0.971 | 0.430 | 1.000 | 0.000 |
| ollama_qwen3-8b_per_item_p11_i5_b1800_k1_think-off_test | raw | 0.550 | 0.699 | 0.400 | 0.583 | 0.967 | 0.526 |
| ollama_qwen3-8b_per_item_p11_i5_b1800_k1_think-off_test | verified | 0.560 | 0.705 | 0.343 | 0.600 | 0.967 | 0.526 |
| ollama_qwen3-8b_per_item_p11_i5_b1800_k1_think-off_test | gated | 0.554 | 0.698 | 0.343 | 0.600 | 0.967 | 0.368 |
| ollama_qwen3-8b_per_item_p22_i5_b900_k1_think-off_test | raw | 0.510 | 0.691 | 0.543 | 0.452 | 0.852 | 0.263 |
| ollama_qwen3-8b_per_item_p22_i5_b900_k1_think-off_test | verified | 0.500 | 0.683 | 0.543 | 0.452 | 0.852 | 0.263 |
| ollama_qwen3-8b_per_item_p22_i5_b900_k1_think-off_test | gated | 0.523 | 0.695 | 0.543 | 0.452 | 0.885 | 0.263 |
| ollama_qwen3-8b_per_item_p22_i5_b3600_k1_think-off_test | raw | 0.508 | 0.678 | 0.629 | 0.449 | 0.836 | 0.211 |
| ollama_qwen3-8b_per_item_p22_i5_b3600_k1_think-off_test | verified | 0.514 | 0.680 | 0.600 | 0.447 | 0.836 | 0.211 |
| ollama_qwen3-8b_per_item_p22_i5_b3600_k1_think-off_test | gated | 0.515 | 0.681 | 0.600 | 0.447 | 0.852 | 0.158 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k5_think-off_test | raw | 0.520 | 0.697 | 0.571 | 0.426 | 0.787 | 0.263 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k5_think-off_test | verified | 0.514 | 0.691 | 0.571 | 0.435 | 0.787 | 0.263 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k5_think-off_test | gated | 0.529 | 0.698 | 0.571 | 0.435 | 0.820 | 0.263 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-on_test | raw | 0.590 | 0.716 | 0.286 | 0.455 | 0.738 | 0.368 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-on_test | verified | 0.580 | 0.710 | 0.286 | 0.476 | 0.754 | 0.368 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-on_test | gated | 0.586 | 0.713 | 0.286 | 0.476 | 0.787 | 0.263 |
