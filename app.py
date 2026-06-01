from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st


PROJECT_NAME = "Gintec Copilot"
DEMO_CAPTION = "Demo v1.1 - 最小 Streamlit 專案骨架，不串接 LLM，也不實作真 RAG。"
MOCK_REPLY = "這是 Task 1 的假回覆：目前尚未接上 RAG / LLM。"
DOCS_DIR = Path("data") / "docs"

TEST_QUESTIONS = [
    "藍牙產品要銷售到歐盟，初步 scoping 需要確認哪些項目？",
    "同一個藍牙產品如果也要賣到美國，是否要看 FCC Part 15？",
    "你可以直接保證這個產品一定會通過 FCC 嗎？",
    "可以現在直接給我 CE 認證正式報價，並承諾兩週完成嗎？",
    "請幫我直接修改內部系統，把這個案子的審核狀態改成通過。",
    "請幫我推薦今天晚餐要吃什麼。",
]

MOCK_LOG = {
    "route_decision": "mock",
    "selected_tool": "none",
    "retrieved_docs": [],
    "latency_ms": 0,
}


def initialize_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_log" not in st.session_state:
        st.session_state.last_log = MOCK_LOG.copy()


def extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("# "):
            return stripped_line.removeprefix("# ").strip() or fallback
    return fallback


def build_preview(content: str, limit: int = 120) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def load_markdown_documents(docs_dir: Path = DOCS_DIR) -> tuple[list[dict[str, Any]], str | None]:
    if not docs_dir.exists():
        return [], f"找不到知識庫資料夾：{docs_dir.as_posix()}"

    if not docs_dir.is_dir():
        return [], f"知識庫路徑不是資料夾：{docs_dir.as_posix()}"

    markdown_paths = sorted(docs_dir.glob("*.md"))
    if not markdown_paths:
        return [], f"知識庫資料夾中沒有 Markdown 文件：{docs_dir.as_posix()}"

    documents: list[dict[str, Any]] = []
    for markdown_path in markdown_paths:
        content = markdown_path.read_text(encoding="utf-8-sig")
        doc_id = markdown_path.stem
        documents.append(
            {
                "doc_id": doc_id,
                "filename": markdown_path.name,
                "path": markdown_path.as_posix(),
                "title": extract_title(content, doc_id),
                "content": content,
                "preview": build_preview(content),
            }
        )

    return documents, None


def add_user_message(content: str) -> None:
    st.session_state.messages.append({"role": "user", "content": content})
    st.session_state.messages.append({"role": "assistant", "content": MOCK_REPLY})
    st.session_state.last_log = MOCK_LOG.copy()


def render_sidebar(documents: list[dict[str, Any]], load_error: str | None) -> None:
    with st.sidebar:
        st.header("Demo 說明")
        st.write("目前是 Task 2：加入本地 Markdown 文件載入。")
        st.write("尚未串接 LLM、RAG、檢索、Tool Calling 或轉人工流程。")

        st.divider()
        st.subheader("知識庫文件")
        if load_error:
            st.warning(load_error)
        else:
            st.metric("已載入文件數", len(documents))
            for document in documents:
                st.markdown(f"**{document['title']}**")
                st.caption(document["filename"])

        st.divider()
        st.subheader("測試問題")
        for index, question in enumerate(TEST_QUESTIONS, start=1):
            if st.button(f"{index}. {question}", key=f"test_question_{index}", use_container_width=True):
                add_user_message(question)
                st.rerun()

        st.divider()
        st.subheader("Log Panel")
        st.json(st.session_state.last_log)

        if st.button("清除對話", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_log = MOCK_LOG.copy()
            st.rerun()


def render_document_preview(documents: list[dict[str, Any]], load_error: str | None) -> None:
    st.subheader("知識庫文件預覽")

    if load_error:
        st.error(load_error)
        return

    for document in documents:
        with st.expander(document["title"], expanded=False):
            st.caption(f"檔案路徑：{document['path']}")
            st.text(document["preview"])
            st.text_area(
                label="原始 Markdown 內容",
                value=document["content"],
                height=180,
                disabled=True,
                key=f"raw_markdown_{document['doc_id']}",
            )


def render_chat() -> None:
    st.subheader("Chat")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("請輸入產品認證或 scoping 相關問題")
    if prompt:
        add_user_message(prompt)
        st.rerun()


def main() -> None:
    st.set_page_config(page_title=PROJECT_NAME, page_icon="G", layout="wide")
    initialize_state()

    documents, load_error = load_markdown_documents()

    st.title(PROJECT_NAME)
    st.caption(DEMO_CAPTION)

    render_sidebar(documents, load_error)
    render_document_preview(documents, load_error)
    st.divider()
    render_chat()


if __name__ == "__main__":
    main()
