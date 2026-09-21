"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .contracts import validate_document

load_dotenv()


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = 1024
EMBEDDING_BATCH_SIZE = 32

COLLECTION_NAME = "rag_documents"


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts with the configured provider using the shared model."""
    if not texts:
        return []

    if EMBEDDING_PROVIDER == "sentence_transformers":
        return _embed_with_sentence_transformers(texts)
    raise ValueError(
        "Unsupported EMBEDDING_PROVIDER: "
        f"{EMBEDDING_PROVIDER}. Use sentence_transformers for this pipeline."
    )


@lru_cache(maxsize=1)
def _get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def _embed_with_sentence_transformers(texts: list[str]) -> list[list[float]]:
    model = _get_embedding_model()
    vectors: list[list[float]] = []

    for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[start : start + EMBEDDING_BATCH_SIZE]
        encoded = model.encode(
            batch,
            batch_size=EMBEDDING_BATCH_SIZE,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        vectors.extend(encoded.tolist())

    return vectors


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        metadata = _read_markdown_metadata(path, content)
        document = {
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": metadata,
        }
        validate_document(document)
        documents.append(document)

    return documents


def _read_markdown_metadata(path: Path, content: str) -> dict:
    title = path.stem.replace("-", " ").title()
    source_url = None

    for line in content.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    source_prefix = "**Source:**"
    for line in content.splitlines():
        if line.startswith(source_prefix):
            source_url = line[len(source_prefix) :].strip() or None
            break

    relative_path = path.relative_to(STANDARDIZED_DIR)
    doc_type = "legal" if relative_path.parts[0] == "legal" else "news"
    return {
        "source": path.name,
        "title": title,
        "doc_type": doc_type,
        "url": source_url,
    }


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []

    for document in documents:
        validate_document(document)
        split_texts = splitter.split_text(document["content"])
        for index, text in enumerate(split_texts):
            chunk = {
                "id": f"{document['id']}::chunk-{index}",
                "content": text.strip(),
                "metadata": {**document["metadata"], "chunk_index": index},
            }
            if chunk["content"]:
                validate_document(chunk, require_chunk=True)
                chunks.append(chunk)

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    if not chunks:
        return []

    for chunk in chunks:
        validate_document(chunk, require_chunk=True)

    vectors = embed_texts([chunk["content"] for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("Embedding provider returned an unexpected vector count")

    return [
        {
            **chunk,
            "metadata": dict(chunk["metadata"]),
            "embedding": vector,
        }
        for chunk, vector in zip(chunks, vectors)
    ]


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        return

    for chunk in chunks:
        validate_document(chunk, require_chunk=True)
        if not chunk.get("embedding"):
            raise ValueError(f"Missing embedding for chunk: {chunk['id']}")

    collection = get_collection()
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[_chroma_metadata(chunk["metadata"]) for chunk in chunks],
    )


def _chroma_metadata(metadata: dict) -> dict:
    return {key: value for key, value in metadata.items() if value is not None}


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
