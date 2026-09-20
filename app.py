import streamlit as st

from src.task10_generation import generate_with_citation
from dotenv import load_dotenv


load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Thay mô tả theo đề tài của nhóm")
    top_k = st.slider("Số chunks", 3, 10, 5)

st.title("RAG Chatbot")
st.caption("Thay tiêu đề và hướng dẫn sử dụng")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        for source in message.get("sources", []):
            metadata = source["metadata"]
            st.caption(
                f"{metadata['title']} — {metadata['source']} "
                f"| {source['retrieval_method']} | score: {source['score']:.3f}"
            )

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        result = generate_with_citation(query, top_k=top_k)
        answer = result["answer"]
        sources = []
        st.markdown(answer)

        for source in result["sources"]:
            metadata = source["metadata"]
            st.caption(
                f"{metadata['title']} — {metadata['source']} "
                f"| {source['retrieval_method']} | score: {source['score']:.3f}"
            )

    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": result["sources"]})
