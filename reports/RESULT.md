# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | RAGAS 0.4.3 installed; metric scoring not executed |
| Evaluator model                    | Not configured; no separate evaluator run |
| Generator provider                 | Gemini |
| Generator model                    | `gemini-3.6-flash` |
| Embedding model                    | `BAAI/bge-m3` |
| Corpus version/commit              | 8 documents, 555 indexed chunks |
| Golden dataset size                | 15 |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.3 default; not calibrated with a labeled threshold set |

## Configurations

- **Config A — dense-only:** semantic search with the shared `BAAI/bge-m3` embedding model.
- **Config B — hybrid + RRF:** dense search plus BM25, fused once with RRF using `k=60`.

Both configurations use the same corpus, golden dataset, prompt and `top_k`; only the retrieval strategy changes. The Gemini generation smoke test succeeded, but automated metric scoring was not executed because no separate evaluator model is configured.

## Verified Runtime Results

| Check | Result |
| ----- | ------ |
| Indexed documents | 8 |
| Indexed chunks | 555 |
| Embedding dimension | 1024 |
| Dense retrieval smoke test | 10 results, unique IDs, sorted scores |
| BM25 retrieval smoke test | 10 results, unique IDs, sorted scores |
| Hybrid RRF smoke test | 5 results, `retrieval_method=hybrid` |
| Generation smoke test | Successful with `retrieval_source=hybrid` |
| Citation coverage | 5/5 returned sources contained URLs |
| Contract/full test suite | 20 passed |

## Overall Scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      | N/A | N/A | N/A |
| Answer relevance  | N/A | N/A | N/A |
| Context recall    | N/A | N/A | N/A |
| Context precision | N/A | N/A | N/A |
| **Average**       | N/A | N/A | N/A |

## A/B Comparison

- Cấu hình tốt hơn: Chưa kết luận vì chưa chạy evaluator.
- Evidence: Dense, BM25 và hybrid smoke tests đúng schema; generation smoke test trả 5 nguồn có URL và citation dạng `[Document N]`.
- Trade-off về latency/cost: Dense cần embedding inference; hybrid thêm BM25 và RRF nhưng không thêm LLM call.

## Worst Performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------- | ---------- |
| 1 | Not scored | N/A | N/A | N/A | N/A | N/A | evaluation | No separate evaluator model is configured |
| 2 | Not scored | N/A | N/A | N/A | N/A | N/A | evaluation | Four-metric runner has not been executed |
| 3 | Not scored | N/A | N/A | N/A | N/A | N/A | evaluation | PageIndex API key is not configured |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
| 1 | Configure a separate evaluator model in `.env` | Metric run is not yet available | Enables four-metric scoring | Run the same 15 cases for both configurations |
| 2 | Calibrate `SCORE_THRESHOLD` with in-domain and out-of-domain queries | Current value is the 0.3 default | Better fallback precision and refusal behavior | Record dense scores and fallback decisions |
| 3 | Configure PageIndex if vectorless fallback is required | PageIndex currently fails safe to hybrid results | Improves retrieval for difficult PDF queries | Demonstrate one fallback query and inspect citations |

## Bonus Experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| None executed | Hybrid + RRF | N/A | N/A | No bonus experiment was measured |
