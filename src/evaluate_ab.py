"""Deterministic A/B evaluation for the golden retrieval dataset.

The metrics are lexical, reproducible proxies:
- faithfulness: expected-answer token coverage in retrieved context
- answer_relevance: question token coverage in retrieved context
- context_recall: whether the expected source is retrieved
- context_precision: fraction of retrieved chunks from that expected source
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from .task5_semantic_search import semantic_search
from .task9_retrieval_pipeline import retrieve


ROOT = Path(__file__).parent.parent
GOLDEN_PATH = ROOT / "group_project" / "evaluation" / "golden_dataset.json"
OUTPUT_PATH = ROOT / "group_project" / "evaluation" / "ab_results.json"


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _ratio(expected: str, observed: str) -> float:
    wanted = _tokens(expected)
    return len(wanted & _tokens(observed)) / len(wanted) if wanted else 0.0


def _score(case: dict, results: list[dict]) -> dict:
    expected_source = case["expected_context"]
    sources = [item.get("metadata", {}).get("source", "") for item in results]
    context = "\n".join(item["content"] for item in results)
    return {
        "faithfulness": _ratio(case["expected_answer"], context),
        "answer_relevance": _ratio(case["question"], context),
        "context_recall": float(expected_source in sources),
        "context_precision": (sources.count(expected_source) / len(sources)) if sources else 0.0,
        "retrieved_sources": sources,
    }


def _mean(rows: list[dict]) -> dict:
    keys = ("faithfulness", "answer_relevance", "context_recall", "context_precision")
    return {key: round(sum(row[key] for row in rows) / len(rows), 4) for key in keys}


def run_evaluation(top_k: int = 5) -> dict:
    cases = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    configs = {
        "A_dense_only": lambda query: semantic_search(query, top_k=top_k),
        "B_hybrid_rrf": lambda query: retrieve(query, top_k=top_k),
    }
    report: dict = {"top_k": top_k, "cases": len(cases), "configs": {}}
    for name, search in configs.items():
        rows = []
        started = time.perf_counter()
        for case in cases:
            query_started = time.perf_counter()
            results = search(case["question"])
            row = {"question": case["question"], "expected_context": case["expected_context"], **_score(case, results)}
            row["latency_seconds"] = round(time.perf_counter() - query_started, 4)
            rows.append(row)
        total = time.perf_counter() - started
        report["configs"][name] = {
            "overall": _mean(rows),
            "average_latency_seconds": round(total / len(cases), 4),
            "rows": rows,
        }
    a, b = report["configs"]["A_dense_only"]["overall"], report["configs"]["B_hybrid_rrf"]["overall"]
    report["delta_b_minus_a"] = {key: round(b[key] - a[key], 4) for key in a}
    report["worst_hybrid_cases"] = sorted(
        report["configs"]["B_hybrid_rrf"]["rows"],
        key=lambda row: sum(row[key] for key in ("faithfulness", "answer_relevance", "context_recall", "context_precision")),
    )[:3]
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run_evaluation()
    print(json.dumps({
        "A": result["configs"]["A_dense_only"]["overall"],
        "B": result["configs"]["B_hybrid_rrf"]["overall"],
        "delta": result["delta_b_minus_a"],
        "results": str(OUTPUT_PATH),
    }, ensure_ascii=False, indent=2))
