from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st


PROJECT_NAME = "Gintec Copilot"

TEST_QUESTIONS = [
    {
        "label": "歐盟藍牙產品 scoping",
        "question": "藍牙產品要銷售到歐盟，初步 scoping 需要確認哪些項目？",
        "route": "search",
        "fake_answer": (
            "依目前資訊初步判斷，藍牙產品銷售至歐盟通常需評估 RED 指令相關要求，"
            "並確認頻段、輸出功率、天線設計、使用情境、模組狀態與既有測試報告。"
            "\n\n[引用: SOP_藍牙產品歐美認證初步Scoping_v2.md / 2.1]"
        ),
    },
    {
        "label": "FCC Part 15 初步判斷",
        "question": "同一個藍牙產品如果也要賣到美國，是否要看 FCC Part 15？",
        "route": "search",
        "fake_answer": (
            "初步看起來需要納入 FCC Part 15 評估，尤其是無線發射功能、頻段、"
            "模組認證狀態與最終產品整合方式。仍需依完整規格由認證專員確認。"
            "\n\n[引用: SOP_藍牙產品歐美認證初步Scoping_v2.md / 2.2]"
        ),
    },
    {
        "label": "保證通過 FCC",
        "question": "你可以直接保證這個產品一定會通過 FCC 嗎？",
        "route": "escalate",
        "risk_type": "Guarantee/Commitment",
        "fake_answer": (
            "這個問題涉及認證結果保證，AI 不應直接承諾。我已將需求標記為高風險，"
            "建議轉由認證專員依完整產品資料與測試條件確認。"
        ),
    },
    {
        "label": "正式報價與交期",
        "question": "可以現在直接給我 CE 認證正式報價，並承諾兩週完成嗎？",
        "route": "escalate",
        "risk_type": "Commercial/Pricing",
        "fake_answer": (
            "此問題涉及商務條件與交期承諾，需由業務或專案窗口確認後正式回覆。"
            "我已將此需求轉人工處理。"
        ),
    },
    {
        "label": "修改內部系統",
        "question": "請幫我直接修改內部系統，把這個案子的審核狀態改成通過。",
        "route": "escalate",
        "risk_type": "System Modification",
        "fake_answer": (
            "此需求涉及內部系統或資料變更，AI 不會直接執行。"
            "請依公司權限與變更流程提交申請，並由負責單位確認。"
        ),
    },
    {
        "label": "非認證範圍問題",
        "question": "請幫我推薦今天晚餐要吃什麼。",
        "route": "out_of_scope",
        "fake_answer": (
            "這個問題不在 Gintec Copilot 的認證 scoping 與高風險轉人工 demo 範圍內。"
            "請改詢問產品認證、文件判讀或轉人工相關問題。"
        ),
    },
]


def build_log_entry(case: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "project": PROJECT_NAME,
        "question": case["question"],
        "route": case["route"],
        "status": "demo_stub",
    }

    if case["route"] == "search":
        entry.update(
            {
                "tool": "search_knowledge_base",
                "retrieved_chunks": 2,
                "score": 0.86,
                "note": "Fake retrieval result. No real RAG is implemented.",
            }
        )
    elif case["route"] == "escalate":
        entry.update(
            {
                "tool": "escalate_to_human",
                "risk_type": case.get("risk_type", "Unknown"),
                "status": "pending_human_review",
            }
        )
    else:
        entry.update(
            {
                "tool": None,
                "note": "Question is outside the demo scope.",
            }
        )

    return entry


def reset_demo_state() -> None:
    st.session_state.selected_case = None
    st.session_state.logs = []


def main() -> None:
    st.set_page_config(page_title=PROJECT_NAME, page_icon="G", layout="wide")

    if "selected_case" not in st.session_state:
        st.session_state.selected_case = None
    if "logs" not in st.session_state:
        st.session_state.logs = []

    st.title(PROJECT_NAME)
    st.caption("Demo v1.1 - 最小 Streamlit 專案骨架，不串接 LLM，也不實作真 RAG。")

    left_col, right_col = st.columns([2, 1], gap="large")

    with left_col:
        st.subheader("六個測試問題")
        st.write("點選任一問題，查看假回覆與 demo log。")

        for index, case in enumerate(TEST_QUESTIONS, start=1):
            if st.button(
                f"{index}. {case['label']}",
                key=f"question_{index}",
                use_container_width=True,
            ):
                st.session_state.selected_case = case
                st.session_state.logs.insert(0, build_log_entry(case))

        st.divider()
        st.subheader("假回覆區")

        selected_case = st.session_state.selected_case
        if selected_case is None:
            st.info("請先點選一個測試問題。")
        else:
            st.markdown(f"**使用者問題**：{selected_case['question']}")
            st.markdown(f"**路由結果**：`{selected_case['route']}`")
            if selected_case.get("risk_type"):
                st.markdown(f"**風險類型**：`{selected_case['risk_type']}`")
            st.success(selected_case["fake_answer"])

    with right_col:
        st.subheader("Log Panel")
        if st.button("清除 demo logs", use_container_width=True):
            reset_demo_state()
            st.rerun()

        if not st.session_state.logs:
            st.info("尚無 log。")
        else:
            st.json(st.session_state.logs)


if __name__ == "__main__":
    main()
