import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="IELTS Writing RAG",
    page_icon="",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander(f"Nguồn tham khảo ({len(sources)})"):
        for index, source in enumerate(sources, 1):
            metadata = source["metadata"]
            title = metadata.get("title", "Untitled")
            source_name = metadata.get("source", "Unknown source")
            source_url = metadata.get("url")
            st.markdown(f"**{index}. {title}**")
            if source_url:
                st.markdown(f"[{source_name}]({source_url})")
            else:
                st.caption(source_name)
            st.caption(
                f"Method: {source.get('retrieval_method', 'unknown')} | "
                f"Score: {source.get('score', 0.0):.4f} | ID: {source['id']}"
            )

with st.sidebar:
    st.title("IELTS Writing RAG")
    st.caption("Tra cứu thông tin IELTS Writing từ nguồn chính thức")
    top_k = st.slider("Số chunks", 3, 10, 5)

st.title("IELTS Writing RAG")
st.caption("Hỏi về format bài thi, tiêu chí chấm và band descriptors.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            retrieval_source = message.get("retrieval_source", "none")
            st.caption(f"Retrieval source: {retrieval_source}")
            render_sources(message.get("sources", []))

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        try:
            result = generate_with_citation(query, top_k=top_k)
        except Exception:
            result = {
                "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
                "sources": [],
                "retrieval_source": "none",
            }

        answer = result["answer"]
        sources = result["sources"]
        st.markdown(answer)
        st.caption(f"Retrieval source: {result['retrieval_source']}")
        render_sources(sources)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "retrieval_source": result["retrieval_source"],
        }
    )
