from __future__ import annotations

import re
import time
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

COMMON_KEYWORDS = [
    "EMC",
    "樣品",
    "資訊",
    "藍牙",
    "歐洲",
    "歐盟",
    "RED",
    "FCC",
    "Part 15",
    "CE",
    "測試",
    "認證",
    "scoping",
]


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


def split_markdown_sections(document: dict[str, Any]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_title = document["title"]
    current_lines: list[str] = []

    for line in document["content"].splitlines():
        stripped_line = line.strip()
        is_heading = re.match(r"^#{1,3}\s+", stripped_line) is not None

        if is_heading:
            if current_lines:
                chunks.append(build_chunk(document, current_title, current_lines))
            current_title = re.sub(r"^#{1,3}\s+", "", stripped_line).strip() or document["title"]
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        chunks.append(build_chunk(document, current_title, current_lines))

    return chunks


def build_chunk(document: dict[str, Any], section_title: str, lines: list[str]) -> dict[str, Any]:
    content = "\n".join(lines).strip()
    section_match = re.match(r"^(\d+(?:\.\d+)*)", section_title)
    section_ref = section_match.group(1) if section_match else section_title

    return {
        "doc_id": document["doc_id"],
        "filename": document["filename"],
        "title": document["title"],
        "section_title": section_title,
        "content": content,
        "score": 0,
        "citation": f"[引用: {document['filename']} §{section_ref}]",
    }


def extract_query_terms(query: str) -> list[str]:
    lower_query = query.lower()
    terms = [term for term in re.split(r"\s+", lower_query) if term]

    for keyword in COMMON_KEYWORDS:
        if keyword.lower() in lower_query:
            terms.append(keyword.lower())

    if "資訊" in query:
        terms.append("資料")

    return sorted(set(terms), key=len, reverse=True)


def score_chunk(query_terms: list[str], chunk: dict[str, Any]) -> int:
    searchable_title = f"{chunk['title']} {chunk['section_title']}".lower()
    searchable_content = chunk["content"].lower()
    score = 0

    for term in query_terms:
        if term in searchable_title:
            score += 3
        if term in searchable_content:
            term_weight = 5 if term in {"emc", "fcc", "red", "ce", "part 15"} else 1
            score += term_weight + searchable_content.count(term)

    return score


def search_knowledge_base(query: str, documents: list[dict[str, Any]], top_k: int = 3) -> list[dict[str, Any]]:
    query_terms = extract_query_terms(query)
    if not query_terms:
        return []

    results: list[dict[str, Any]] = []
    for document in documents:
        for chunk in split_markdown_sections(document):
            score = score_chunk(query_terms, chunk)
            if score > 0:
                chunk["score"] = score
                results.append(chunk)

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


def format_search_response(results: list[dict[str, Any]]) -> str:
    if not results:
        return "目前知識庫沒有找到足夠相關的段落，建議補充文件或轉交人工確認。"

    response_lines = ["我目前找到以下可能相關段落："]
    for index, result in enumerate(results, start=1):
        preview = build_preview(result["content"], limit=150)
        response_lines.extend(
            [
                "",
                f"{index}. 文件名稱：{result['filename']}",
                f"   段落：{result['section_title']}",
                f"   分數：{result['score']}",
                f"   摘要：{preview}",
                f"   {result['citation']}",
            ]
        )

    return "\n".join(response_lines)


def build_search_log(results: list[dict[str, Any]], latency_ms: int) -> dict[str, Any]:
    return {
        "route_decision": "search",
        "selected_tool": "search_knowledge_base",
        "retrieved_docs": [
            {
                "filename": result["filename"],
                "section_title": result["section_title"],
                "score": result["score"],
            }
            for result in results
        ],
        "latency_ms": latency_ms,
    }


def add_user_message(content: str, documents: list[dict[str, Any]]) -> None:
    started_at = time.perf_counter()
    results = search_knowledge_base(content, documents)
    latency_ms = round((time.perf_counter() - started_at) * 1000)

    st.session_state.messages.append({"role": "user", "content": content})
    st.session_state.messages.append({"role": "assistant", "content": format_search_response(results)})
    st.session_state.last_log = build_search_log(results, latency_ms)


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
                add_user_message(question, documents)
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


def render_chat(documents: list[dict[str, Any]]) -> None:
    st.subheader("Chat")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("請輸入產品認證或 scoping 相關問題")
    if prompt:
        add_user_message(prompt, documents)
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
    render_chat(documents)


if __name__ == "__main__":
    main()
