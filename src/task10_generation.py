"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Trả lời chỉ từ context được cung cấp.
Mỗi khẳng định phải có citation. Nếu thiếu evidence, hãy từ chối xác minh."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context."""
    if len(chunks) <= 2:
        return list(chunks)
    return list(chunks[::2]) + list(chunks[1::2])[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    return "\n\n---\n\n".join(
        f"[Document {index} | Title: {chunk['metadata']['title']} | "
        f"Source: {chunk['metadata']['source']}]\n{chunk['content']}"
        for index, chunk in enumerate(chunks, 1)
    )


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    provider = LLM_PROVIDER.lower()
    if provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        # OpenRouter keys use the OpenAI-compatible API, but a different base URL.
        base_url = os.getenv("OPENAI_BASE_URL")
        if not base_url and api_key and api_key.startswith("sk-or-"):
            base_url = "https://openrouter.ai/api/v1"
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=LLM_MODEL or ("openai/gpt-4o-mini" if base_url else "gpt-4o-mini"),
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content or ""
    if provider == "gemini":
        from google import genai

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model=LLM_MODEL or "gemini-2.0-flash",
            contents=f"{system_prompt}\n\n{user_message}",
        )
        return response.text or ""
    if provider == "anthropic":
        from anthropic import Anthropic

        response = Anthropic().messages.create(
            model=LLM_MODEL or "claude-3-5-haiku-latest",
            max_tokens=1000,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if hasattr(block, "text"))
    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    refusal = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {"answer": refusal, "sources": [], "retrieval_source": "none"}
    try:
        answer = call_llm(
            SYSTEM_PROMPT,
            f"Context:\n{format_context(reorder_for_llm(chunks))}\n\nQuestion: {query}",
        ).strip()
    except Exception:
        return {"answer": refusal, "sources": [], "retrieval_source": "none"}
    if not answer:
        return {"answer": refusal, "sources": [], "retrieval_source": "none"}
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0]["retrieval_method"],
    }


if __name__ == "__main__":
    print(generate_with_citation("test query"))
