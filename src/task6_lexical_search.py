"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import re

from rank_bm25 import BM25Okapi

from .contracts import validate_search_results
from .task4_chunking_indexing import chunk_documents, load_documents


CORPUS: list[dict] = []
TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
BM25_TIE_BREAK_SCORE = 1e-6


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    if not corpus:
        raise ValueError("BM25 corpus must not be empty")

    tokenized_corpus = [_tokenize(item["content"]) for item in corpus]
    return BM25Okapi(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if top_k <= 0 or not query.strip():
        return []

    corpus = _get_corpus()
    if not corpus:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    bm25 = build_bm25_index(corpus)
    scores = bm25.get_scores(query_tokens)
    tokenized_corpus = [_tokenize(item["content"]) for item in corpus]
    ranked_indices = sorted(
        range(len(corpus)),
        key=lambda index: (
            float(scores[index]),
            len(set(query_tokens).intersection(tokenized_corpus[index])),
        ),
        reverse=True,
    )

    results = []
    for index in ranked_indices:
        score = float(scores[index])
        if score <= 0:
            matching_tokens = len(
                set(query_tokens).intersection(tokenized_corpus[index])
            )
            if matching_tokens == 0:
                continue
            score = BM25_TIE_BREAK_SCORE * matching_tokens

        item = corpus[index]
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": score,
                "metadata": dict(item["metadata"]),
                "retrieval_method": "bm25",
            }
        )
        if len(results) == top_k:
            break

    validate_search_results(results, top_k=top_k, expected_method="bm25")
    return results


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _get_corpus() -> list[dict]:
    global CORPUS
    if not CORPUS:
        CORPUS = chunk_documents(load_documents())
    return CORPUS


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
