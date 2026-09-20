# RAG evaluation results

## Run information

| Field | Value |
| --- | --- |
| Evaluation date | 2026-09-20 |
| Framework and version | pytest 8.x; dependencies from pyproject.toml |
| Evaluator model | Not run: evaluator API not configured |
| Generator model | Configurable; default `gpt-4o-mini` |
| Embedding model | Configurable; default `text-embedding-3-small` |
| Corpus version/commit | `1353fbe` on branch `truongan` |
| Golden dataset size | 15 |
| `top_k` | 5 generation; 10 search default |
| Fallback threshold and calibration | 0.3 cosine score; calibration not run |

## Configurations

- **Config A - dense-only:** Dense search, top 5; benchmark pending.
- **Config B - hybrid + RRF:** Dense + BM25 fused once with RRF, top 5; implemented.

Hai config dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric | Config A | Config B | Delta B-A |
| --- | ---: | ---: | ---: |
| Faithfulness | N/A | N/A | N/A |
| Answer relevance | N/A | N/A | N/A |
| Context recall | N/A | N/A | N/A |
| Context precision | N/A | N/A | N/A |
| **Average** | N/A | N/A | N/A |

## A/B comparison

- Cấu hình tốt hơn: Chưa kết luận vì chưa chạy evaluator A/B cùng một điều kiện.
- Evidence: 20/20 contract tests pass; dataset có 15 cases grounded.
- Trade-off về latency/cost: Dense-only ít bước hơn; hybrid thêm BM25 và RRF nhưng tăng khả năng thu hồi thuật ngữ. Chưa đo latency định lượng.

## Worst performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Task 1 word limit | N/A | N/A | N/A | N/A | N/A | evaluation | Chưa chạy evaluator |
| 2 | Academic test sections | N/A | N/A | N/A | N/A | N/A | evaluation | Chưa chạy evaluator |
| 3 | Out-of-domain query | N/A | N/A | N/A | N/A | N/A | evaluation | Threshold cần calibration |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| ---: | --- | --- | --- | --- |
| 1 | Chạy A/B trên 15 cases với cùng evaluator | Metrics chưa có | Có số đo chất lượng | Lưu output và tính 4 metrics |
| 2 | Calibrate threshold in-domain/out-of-domain | 0.3 chưa được đo | Giảm fallback/refusal sai | So sánh nhiều threshold |
| 3 | Kiểm tra citation theo source IDs | Generator cần API key | Tăng khả năng audit | Assert citation thuộc sources |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| --- | --- | ---: | ---: | --- |
| Local embedding vs API embedding | OpenAI default | N/A | Chưa đo | Chạy cùng golden set sau khi cấu hình provider |
