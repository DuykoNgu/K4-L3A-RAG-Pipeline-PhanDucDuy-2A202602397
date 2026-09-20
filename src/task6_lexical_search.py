"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""


CORPUS: list[dict] = []


def _get_corpus() -> list[dict]:
    """Load the same deterministic chunks used by the dense index on first use."""
    global CORPUS
    if not CORPUS:
        from .task4_chunking_indexing import chunk_documents, load_documents

        CORPUS = chunk_documents(load_documents())
    return CORPUS


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi

    return BM25Okapi([item["content"].lower().split() for item in corpus])


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    corpus = _get_corpus()
    if not corpus or top_k <= 0:
        return []
    scores = build_bm25_index(corpus).get_scores(query.lower().split())
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
    return [
        {
            "id": corpus[index]["id"],
            "content": corpus[index]["content"],
            "score": float(score),
            "metadata": corpus[index]["metadata"],
            "retrieval_method": "bm25",
        }
        for index, score in ranked[:top_k]
    ]


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
