# RAG evaluation results

## Run information

| Field | Value |
| --- | --- |
| Evaluation date | 2026-09-20 |
| Framework and version | pytest 8.x; dependencies from pyproject.toml |
| Evaluator model | Deterministic lexical proxy evaluator in `src.evaluate_ab` |
| Generator model | Not used for this retrieval-focused A/B run |
| Embedding model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` on DirectML |
| Corpus version/commit | `1353fbe` on branch `truongan` |
| Golden dataset size | 15 |
| `top_k` | 5 generation; 10 search default |
| Fallback threshold and calibration | `0.65` cosine score. In-domain: 0.7941 (four Writing criteria); out-of-domain: 0.5057 (capital of Japan). Threshold nằm giữa hai score. |

## Configurations

- **Config A - dense-only:** Dense search, top 5; implemented and smoke-tested.
- **Config B - hybrid + RRF:** Dense + BM25 fused once with RRF, top 5; implemented and smoke-tested.

Hai config dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric | Config A | Config B | Delta B-A |
| --- | ---: | ---: | ---: |
| Faithfulness | 0.9533 | 0.9473 | -0.0060 |
| Answer relevance | 0.8261 | 0.8509 | +0.0248 |
| Context recall | 1.0000 | 1.0000 | 0.0000 |
| Context precision | 0.4267 | 0.5067 | +0.0800 |
| **Average** | 0.8015 | 0.8262 | +0.0247 |

## A/B comparison

- Cấu hình tốt hơn: **Config B (hybrid + RRF)** theo average (+0.0247), answer relevance (+0.0248) và context precision (+0.0800); context recall không đổi.
- Evidence: `ab_results.json` chứa kết quả từng case và nguồn retrieved; 20/20 test pass.
- Trade-off về latency/cost: Hybrid thêm BM25 + RRF nên có overhead CPU nhỏ; không gọi API evaluator/generator, nên chi phí benchmark bằng 0.

## Worst performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Score-setting resources for organisations | B | 0.8333 | 0.9091 | 1.0000 | 0.2000 | retrieval | Chỉ 1/5 chunks thuộc `article_05`; 4 chunks còn lại nhiễu từ trang Academic. |
| 2 | Academic Task 1 word limit | B | 1.0000 | 0.7692 | 1.0000 | 0.2000 | retrieval | Word-limit xuất hiện ở nhiều trang, dẫn tới 4/5 chunks ngoài PDF mẫu. |
| 3 | Academic Task 2 word limit | B | 1.0000 | 0.7692 | 1.0000 | 0.2000 | retrieval | Cùng lỗi ambiguity; chunk đúng đứng thứ hai thay vì đầu. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| ---: | --- | --- | --- | --- |
| 1 | Thử tăng trọng số BM25 cho query có số/đơn vị (`150`, `250`, `words`) | Precision 0.20 ở hai case word-limit | Đưa PDF mẫu lên hạng 1 | Chạy lại A/B và so sánh context precision. |
| 2 | Calibrate threshold bằng query in-domain/out-of-domain | In-domain 0.7941; out-of-domain 0.5057; chọn threshold 0.65 | Giảm fallback/refusal sai | Log best dense score trên hai nhóm query sau khi thay corpus. |
| 3 | Kiểm tra citation theo source IDs trong UI | Generation trả sources từ hybrid | Tăng khả năng audit | Assert citation thuộc `GenerationResult.sources`. |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| --- | --- | ---: | ---: | --- |
| Local embedding vs API embedding | OpenAI default | N/A | Chưa đo | Chạy cùng golden set sau khi cấu hình provider |
