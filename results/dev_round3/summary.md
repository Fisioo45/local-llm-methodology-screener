# Results on 'dev' (40 gold papers)

Mean kappa excludes items whose gold labels have a single class (kappa undefined): none

| run | policy | mean kappa | mean macro-F1 | any-RISK sens | any-RISK PPV | not-verifiable sens | not-verifiable spec |
|---|---|---|---|---|---|---|---|
| rules_per_item_i5_b1800_k1_dev | raw | 0.515 | 0.647 | 0.200 | 0.200 | 0.966 | 0.364 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_dev | raw | 0.593 | 0.704 | 0.600 | 0.111 | 0.931 | 0.364 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_dev | verified | 0.583 | 0.700 | 0.600 | 0.111 | 0.931 | 0.364 |
| ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_dev | gated | 0.614 | 0.713 | 0.600 | 0.111 | 0.966 | 0.364 |
| hybrid__ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_dev | raw | 0.644 | 0.744 | 0.600 | 0.111 | 0.931 | 0.364 |
| hybrid__ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_dev | verified | 0.634 | 0.740 | 0.600 | 0.111 | 0.931 | 0.364 |
| hybrid__ollama_qwen3-8b_per_item_p22_i5_b1800_k1_think-off_dev | gated | 0.650 | 0.747 | 0.600 | 0.111 | 0.966 | 0.364 |
| ollama_qwen3.5-9b_per_item_p22_i5_b1800_k1_think-off_dev | raw | 0.572 | 0.715 | 0.800 | 0.190 | 0.931 | 0.545 |
| ollama_qwen3.5-9b_per_item_p22_i5_b1800_k1_think-off_dev | verified | 0.542 | 0.703 | 0.800 | 0.190 | 0.931 | 0.455 |
| ollama_qwen3.5-9b_per_item_p22_i5_b1800_k1_think-off_dev | gated | 0.611 | 0.732 | 0.800 | 0.190 | 0.931 | 0.455 |
| ollama_llama3.1-8b_per_item_p22_i5_b1800_k1_think-default_dev | raw | 0.489 | 0.612 | 0.600 | 0.188 | 0.690 | 0.545 |
| ollama_llama3.1-8b_per_item_p22_i5_b1800_k1_think-default_dev | verified | 0.490 | 0.610 | 0.600 | 0.188 | 0.690 | 0.545 |
| ollama_llama3.1-8b_per_item_p22_i5_b1800_k1_think-default_dev | gated | 0.514 | 0.631 | 0.600 | 0.188 | 0.724 | 0.455 |
| ollama_gemma3-4b_per_item_p22_i5_b1800_k1_think-default_dev | raw | 0.303 | 0.444 | 1.000 | 0.125 | 1.000 | 0.000 |
| ollama_gemma3-4b_per_item_p22_i5_b1800_k1_think-default_dev | verified | 0.282 | 0.442 | 1.000 | 0.132 | 1.000 | 0.000 |
| ollama_gemma3-4b_per_item_p22_i5_b1800_k1_think-default_dev | gated | 0.367 | 0.508 | 1.000 | 0.132 | 1.000 | 0.000 |
| ollama_qwen3-8b_per_item_p11_i5_b1800_k1_think-off_dev | raw | 0.597 | 0.711 | 0.600 | 0.214 | 0.931 | 0.455 |
| ollama_qwen3-8b_per_item_p11_i5_b1800_k1_think-off_dev | verified | 0.577 | 0.700 | 0.600 | 0.231 | 0.931 | 0.364 |
| ollama_qwen3-8b_per_item_p11_i5_b1800_k1_think-off_dev | gated | 0.588 | 0.706 | 0.600 | 0.231 | 0.931 | 0.364 |
| hybrid__ollama_qwen3.5-9b_per_item_p22_i5_b1800_k1_think-off_dev | raw | 0.657 | 0.775 | 0.800 | 0.190 | 0.931 | 0.545 |
| hybrid__ollama_qwen3.5-9b_per_item_p22_i5_b1800_k1_think-off_dev | verified | 0.637 | 0.768 | 0.800 | 0.190 | 0.931 | 0.455 |
| hybrid__ollama_qwen3.5-9b_per_item_p22_i5_b1800_k1_think-off_dev | gated | 0.653 | 0.775 | 0.800 | 0.190 | 0.931 | 0.455 |
| hybrid__ollama_llama3.1-8b_per_item_p22_i5_b1800_k1_think-default_dev | raw | 0.569 | 0.672 | 0.600 | 0.188 | 0.690 | 0.545 |
| hybrid__ollama_llama3.1-8b_per_item_p22_i5_b1800_k1_think-default_dev | verified | 0.562 | 0.667 | 0.600 | 0.188 | 0.690 | 0.545 |
| hybrid__ollama_llama3.1-8b_per_item_p22_i5_b1800_k1_think-default_dev | gated | 0.587 | 0.690 | 0.600 | 0.188 | 0.724 | 0.455 |
