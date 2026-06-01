from __future__ import annotations

import streamlit as st


PROJECT_NAME = "Gintec Copilot"
DEMO_CAPTION = "Demo v1.1 - 最小 Streamlit 專案骨架，不串接 LLM，也不實作真 RAG。"
MOCK_REPLY = "這是 Task 1 的假回覆：目前尚未接上 RAG / LLM。"

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


def add_user_message(content: str) -> None:
    st.session_state.messages.append({"role": "user", "content": content})
    st.session_state.messages.append({"role": "assistant", "content": MOCK_REPLY})
    st.session_state.last_log = MOCK_LOG.copy()


def render_sidebar() -> None:
    with st.sidebar:
        st.header("Demo 說明")
        st.write("目前是 Task 1：只完成 Streamlit chat UI。")
        st.write("尚未串接 LLM、RAG、檢索、Tool Calling 或轉人工流程。")

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


def render_chat() -> None:
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

    st.title(PROJECT_NAME)
    st.caption(DEMO_CAPTION)

    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
