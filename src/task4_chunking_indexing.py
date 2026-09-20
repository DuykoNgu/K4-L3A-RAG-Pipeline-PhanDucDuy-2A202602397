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

from pathlib import Path
import os
import re

from dotenv import load_dotenv


load_dotenv()


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

_model_tag = re.sub(
    r"[^a-zA-Z0-9_-]+",
    "-",
    os.getenv("LOCAL_EMBEDDING_MODEL", os.getenv("OPENAI_EMBEDDING_MODEL", EMBEDDING_MODEL)),
).strip("-")[-40:]
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", f"rag_documents_{_model_tag}")
_LOCAL_MODEL_CACHE = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    if provider == "openai":
        from openai import OpenAI

        model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        response = OpenAI().embeddings.create(model=model, input=texts)
        return [item.embedding for item in response.data]
    if provider == "gemini":
        from google import genai

        model = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.embed_content(model=model, contents=texts)
        return [item.values for item in response.embeddings]
    if provider in {"local", "sentence_transformers", "sentence-transformers"}:
        from sentence_transformers import SentenceTransformer

        global _LOCAL_MODEL_CACHE
        model_name = os.getenv("LOCAL_EMBEDDING_MODEL", EMBEDDING_MODEL)
        if _LOCAL_MODEL_CACHE is None:
            _LOCAL_MODEL_CACHE = SentenceTransformer(model_name)
        model = _LOCAL_MODEL_CACHE
        device = os.getenv("EMBEDDING_DEVICE", "auto").lower()
        if device in {"auto", "directml"}:
            try:
                import torch_directml

                model.to(torch_directml.device())
            except ImportError:
                if device == "directml":
                    raise RuntimeError("Install torch-directml to use EMBEDDING_DEVICE=directml")
        return model.encode(texts, normalize_embeddings=True).tolist()
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")


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
        doc_type = "legal" if "legal" in path.parts else "news"
        documents.append({
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": {
                "source": path.name,
                "title": content.splitlines()[0].removeprefix("# ") or path.stem,
                "doc_type": doc_type,
                "url": None,
            },
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    def split_text(text: str) -> list[str]:
        """Split near natural boundaries while retaining a small overlap."""
        pieces: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            if end < len(text):
                boundary = max(
                    text.rfind(separator, start + CHUNK_SIZE // 2, end)
                    for separator in ("\n\n", "\n", ". ", " ")
                )
                if boundary > start:
                    end = boundary + 1
            piece = text[start:end].strip()
            if piece:
                pieces.append(piece)
            if end >= len(text):
                break
            start = max(end - CHUNK_OVERLAP, start + 1)
        return pieces

    chunks = []
    for document in documents:
        for index, text in enumerate(split_text(document["content"])):
            content = text.strip()
            if content:
                chunks.append({
                    "id": f"{document['id']}::chunk-{index}",
                    "content": content,
                    "metadata": {**document["metadata"], "chunk_index": index},
                })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("Embedding provider returned an unexpected vector count")
    return [{**chunk, "embedding": vector} for chunk, vector in zip(chunks, vectors)]


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        return
    collection = get_collection()
    existing_ids = collection.get(include=[]).get("ids", [])
    if existing_ids:
        collection.delete(ids=existing_ids)
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
    )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
