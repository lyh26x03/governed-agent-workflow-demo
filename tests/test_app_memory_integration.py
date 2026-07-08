"""Integration tests: ProductConversationMemory wired into app.add_user_message.

These verify the *headline* multi-turn behavior at the app layer:
  * bare follow-ups the keyword router would drop to out_of_scope are rescued to
    controlled retrieval using memory;
  * "which docs did you reference" is answered from memory (citation recall);
  * genuine off-topic chit-chat is still zero-retrieval;
  * the governance guarantee boundary still escalates;
  * the memory state is surfaced in the audit log.

We fake ``st.session_state`` (a dict that also allows attribute access) so the
pure decision/memory logic in ``add_user_message`` runs without a Streamlit
runtime. LLM mode is forced to ``mock`` so no network calls happen.
"""

from __future__ import annotations

import os
import unittest


os.environ["LLM_MODE"] = "mock"  # 必須在 import app 之前；load_dotenv 不會覆寫既有 env。

import app  # noqa: E402


class _FakeSessionState(dict):
    def __getattr__(self, key: str):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class AppMemoryIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        app.st.session_state = _FakeSessionState()
        app.initialize_state()
        documents, error = app.load_markdown_documents()
        self.assertIsNone(error, error)
        self.documents = documents

    def _send(self, text: str) -> dict:
        app.add_user_message(text, self.documents)
        return app.st.session_state.last_log

    def test_bare_product_followup_is_rescued_from_out_of_scope(self) -> None:
        self._send("AlphaBuds X1 如果要出口到歐洲，初步要看哪些認證或文件？")
        log = self._send("如果改成 BetaBuds X2 呢？")
        # 關鍵字路由原會判 out_of_scope；記憶把它救回受控檢索並真的有命中。
        self.assertEqual(log["memory_route"], "product_followup")
        self.assertEqual(log["route_status"], "search")
        self.assertNotEqual(log["action_status"], "no_retrieval")
        self.assertGreater(len(log["retrieved_docs"]), 0)

    def test_region_followup_rescued_and_keeps_product(self) -> None:
        self._send("AlphaBuds X1 出口歐洲 認證 scoping")
        self._send("如果改成 BetaBuds X2 呢？")
        log = self._send("那日本呢？")
        self.assertEqual(log["memory_route"], "region_followup")
        self.assertEqual(log["route_status"], "search")
        memory = log["product_memory"]
        self.assertIn("BetaBuds X2", memory["active_products"])
        self.assertIn("Japan", memory["active_regions"])

    def test_citation_recall_answers_from_memory(self) -> None:
        self._send("AlphaBuds X1 如果要出口到歐洲，初步要看哪些認證或文件？")
        self._send("如果改成 BetaBuds X2 呢？")
        log = self._send("剛才你參考了哪些文件？")
        self.assertEqual(log["memory_route"], "citation_recall")
        self.assertEqual(log["action_status"], "history_recall")
        # 答案應列出記憶中的文件，且不重新檢索知識庫。
        answer = app.st.session_state.messages[-1]["content"]
        self.assertIn(".md", answer)
        self.assertEqual(log["retrieved_docs"], [])

    def test_genuine_offtopic_is_not_rescued(self) -> None:
        self._send("AlphaBuds X1 如果要出口到歐洲，初步要看哪些認證或文件？")
        log = self._send("請幫我推薦今天晚餐")
        self.assertEqual(log["memory_route"], "out_of_scope")
        self.assertEqual(log["route_status"], "out_of_scope")
        self.assertEqual(log["action_status"], "no_retrieval")

    def test_guarantee_still_escalates_to_human_review(self) -> None:
        self._send("AlphaBuds X1 如果要出口到歐洲，初步要看哪些認證或文件？")
        log = self._send("可以跟客戶說一定會通過認證嗎？")
        self.assertEqual(log["route_status"], "generate_draft_and_escalate")
        self.assertEqual(log["action_status"], "pending_human_review")

    def test_audit_log_surfaces_memory_state(self) -> None:
        log = self._send("AlphaBuds X1 如果要出口到歐洲，初步要看哪些認證或文件？")
        memory = log["product_memory"]
        self.assertIsInstance(memory, dict)
        self.assertIn("AlphaBuds X1", memory["active_products"])
        self.assertIn("active_request_summary", memory)
        self.assertEqual(log["memory_route"], memory["route"])

    def test_clear_conversation_resets_memory_focus(self) -> None:
        self._send("AlphaBuds X1 出口歐洲認證")
        # 模擬「清除對話」按鈕的狀態重置。
        app.st.session_state.product_memory = app.ProductConversationMemory()
        self.assertEqual(app.st.session_state.product_memory.snapshot()["active_products"], [])


if __name__ == "__main__":
    unittest.main()
