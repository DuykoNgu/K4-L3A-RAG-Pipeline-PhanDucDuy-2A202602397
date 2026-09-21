"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv

from .contracts import validate_search_results
from .task1_collect_legal_docs import LEGAL_SOURCES


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
ROOT_DIR = Path(__file__).parent.parent
LEGAL_DIR = ROOT_DIR / "data" / "landing" / "legal"
PAGEINDEX_CACHE = ROOT_DIR / "pageindex_doc_ids.json"
POLL_INTERVAL_SECONDS = 2
MAX_POLL_ATTEMPTS = 30


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    api_key = _get_api_key()
    if not api_key:
        print("PageIndex disabled: PAGEINDEX_API_KEY is not configured")
        return

    try:
        from pageindex import PageIndexClient

        client = PageIndexClient(api_key)
    except Exception as error:
        print(f"PageIndex unavailable: {error}")
        return

    cache = _read_cache()
    for path in sorted(LEGAL_DIR.glob("*.pdf")):
        if path.name in cache:
            continue

        try:
            response = client.submit_document(str(path))
            document_id = response.get("doc_id")
            if document_id:
                cache[path.name] = document_id
                _write_cache(cache)
                print(f"Uploaded to PageIndex: {path.name}")
        except Exception as error:
            print(f"PageIndex upload failed for {path.name}: {error}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if top_k <= 0 or not query.strip() or not _get_api_key():
        return []

    cache = _read_cache()
    if not cache:
        upload_documents()
        cache = _read_cache()
    if not cache:
        return []

    try:
        from pageindex import PageIndexClient

        client = PageIndexClient(_get_api_key())
    except Exception:
        return []

    results = []
    for path in sorted(LEGAL_DIR.glob("*.pdf")):
        document_id = cache.get(path.name)
        if not document_id:
            continue

        try:
            if not client.is_retrieval_ready(document_id):
                continue
            submitted = client.submit_query(
                doc_id=document_id,
                query=query,
                thinking=False,
            )
            retrieval_id = submitted.get("retrieval_id")
            if not retrieval_id:
                continue

            retrieval = _wait_for_retrieval(client, retrieval_id)
            results.extend(_parse_retrieval(retrieval, path, document_id))
        except Exception as error:
            print(f"PageIndex query failed for {path.name}: {error}")

    ranked_results = sorted(results, key=lambda item: item["score"], reverse=True)
    ranked_results = ranked_results[:top_k]
    validate_search_results(
        ranked_results,
        top_k=top_k,
        expected_method="pageindex",
    )
    return ranked_results


def _get_api_key() -> str:
    return os.getenv("PAGEINDEX_API_KEY", PAGEINDEX_API_KEY).strip()


def _read_cache() -> dict[str, str]:
    if not PAGEINDEX_CACHE.exists():
        return {}
    try:
        cache = json.loads(PAGEINDEX_CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return cache if isinstance(cache, dict) else {}


def _write_cache(cache: dict[str, str]) -> None:
    PAGEINDEX_CACHE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _wait_for_retrieval(client, retrieval_id: str) -> dict:
    for attempt in range(MAX_POLL_ATTEMPTS):
        response = client.get_retrieval(retrieval_id)
        status = response.get("status")
        if status in {"completed", "failed"}:
            return response
        if attempt < MAX_POLL_ATTEMPTS - 1:
            time.sleep(POLL_INTERVAL_SECONDS)
    return {}


def _parse_retrieval(retrieval: dict, path: Path, document_id: str) -> list[dict]:
    if retrieval.get("status") != "completed":
        return []

    results = []
    for node_index, node in enumerate(retrieval.get("retrieved_nodes", [])):
        node_id = str(node.get("node_id", node_index))
        title = str(node.get("title") or path.stem).strip()
        for content_index, item in enumerate(node.get("relevant_contents", [])):
            content = str(item.get("relevant_content", "")).strip()
            if not content:
                continue

            page_index = int(item.get("page_index", content_index))
            rank = len(results) + 1
            results.append(
                {
                    "id": f"pageindex:{document_id}:{node_id}:{page_index}",
                    "content": content,
                    "score": 1.0 / rank,
                    "metadata": {
                        "source": path.name,
                        "title": title,
                        "doc_type": "legal",
                        "url": LEGAL_SOURCES.get(path.name),
                        "chunk_index": page_index,
                    },
                    "retrieval_method": "pageindex",
                }
            )
    return results


if __name__ == "__main__":
    upload_documents()
