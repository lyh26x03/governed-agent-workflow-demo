from __future__ import annotations

import dataclasses
import importlib
import unittest
from typing import Any


TURN_1 = "AlphaBuds X1 如果要出口到歐洲，初步要看哪些認證或文件？"
TURN_2 = "如果改成 BetaBuds X2 呢？"
TURN_3 = "那日本呢？"
TURN_4 = "剛才你參考了哪些文件？"
TURN_5 = "可以跟客戶說一定會通過認證嗎？"
TURN_6 = "如果 GammaHub C1 沒有無線功能，還要做藍牙測試嗎？"
TURN_7 = "DeltaCam D4 同時有 Wi-Fi 和 Bluetooth，scoping 應該先看什麼？"


def _contains(value: Any, expected: str) -> bool:
    if isinstance(value, str):
        return expected.lower() in value.lower()
    if isinstance(value, dict):
        return any(_contains(item, expected) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains(item, expected) for item in value)
    return expected.lower() in str(value).lower()


class ProductConversationMemoryContractMixin:
    """Adapter layer for the future memory object.

    The tests intentionally allow a few method names so the implementation can
    fit the app, while still requiring deterministic observable behavior.
    """

    def new_memory(self, **kwargs: Any) -> Any:
        module = importlib.import_module("product_context_memory")
        cls = getattr(module, "ProductConversationMemory")
        try:
            return cls(**kwargs)
        except TypeError:
            return cls()

    def snapshot(self, memory: Any) -> dict[str, Any]:
        for method_name in ("snapshot", "to_dict", "model_dump"):
            method = getattr(memory, method_name, None)
            if callable(method):
                state = method()
                self.assertIsInstance(state, dict)
                return state
        if dataclasses.is_dataclass(memory):
            return dataclasses.asdict(memory)
        state = getattr(memory, "state", None)
        if isinstance(state, dict):
            return state
        self.fail("ProductConversationMemory must expose snapshot(), to_dict(), model_dump(), or .state")

    def update_turn(
        self,
        memory: Any,
        query: str,
        *,
        retrieved_docs: list[str] | None = None,
    ) -> dict[str, Any]:
        retrieved_docs = retrieved_docs or []
        for method_name in ("update_from_turn", "record_turn", "add_turn"):
            method = getattr(memory, method_name, None)
            if callable(method):
                try:
                    result = method(user_query=query, retrieved_docs=retrieved_docs)
                except TypeError:
                    try:
                        result = method(query, retrieved_docs=retrieved_docs)
                    except TypeError:
                        result = method(query)
                return result if isinstance(result, dict) else self.snapshot(memory)
        self.fail("ProductConversationMemory must expose update_from_turn(), record_turn(), or add_turn()")

    def compose_query(self, memory: Any, query: str) -> str:
        for method_name in ("compose_retrieval_query", "build_retrieval_query", "to_retrieval_query"):
            method = getattr(memory, method_name, None)
            if callable(method):
                return str(method(query))
        self.fail("ProductConversationMemory must expose a retrieval-query composer")

    def route_or_action(self, state: dict[str, Any]) -> str:
        for key in ("route", "action", "route_status", "memory_action", "turn_type"):
            value = state.get(key)
            if value:
                return str(value)
        return ""


class ProductConversationMemorySchemaTests(
    ProductConversationMemoryContractMixin,
    unittest.TestCase,
):
    @unittest.expectedFailure
    def test_expected_schema_fields_exist(self) -> None:
        memory = self.new_memory()
        state = self.snapshot(memory)
        expected_fields = {
            "active_products",
            "active_regions",
            "active_spec_fields",
            "active_request_summary",
            "active_context_deltas",
            "last_retrieved_docs",
            "recent_turns",
        }
        self.assertTrue(expected_fields.issubset(state.keys()))

    @unittest.expectedFailure
    def test_first_substantive_product_query_seeds_active_request_summary(self) -> None:
        memory = self.new_memory()
        state = self.update_turn(
            memory,
            TURN_1,
            retrieved_docs=[
                "產品A_AlphaBuds_X1_規格與認證.md",
                "區域認證矩陣_EU_US_JP.md",
                "無線測試與認證Scoping_SOP.md",
            ],
        )

        self.assertTrue(_contains(state["active_products"], "AlphaBuds X1"))
        self.assertTrue(_contains(state["active_regions"], "EU") or _contains(state["active_regions"], "Europe"))
        self.assertTrue(_contains(state["active_request_summary"], "certification") or _contains(state["active_request_summary"], "scoping") or _contains(state["active_request_summary"], "認證"))
        self.assertTrue(_contains(state["last_retrieved_docs"], "產品A_AlphaBuds_X1_規格與認證.md"))

    @unittest.expectedFailure
    def test_product_followup_preserves_task_and_adds_product_delta(self) -> None:
        memory = self.new_memory()
        self.update_turn(memory, TURN_1)
        state = self.update_turn(memory, TURN_2, retrieved_docs=["產品B_BetaBuds_X2_規格與認證.md"])
        composed_query = self.compose_query(memory, TURN_2)

        self.assertTrue(_contains(state["active_products"], "BetaBuds X2"))
        self.assertTrue(_contains(state["active_context_deltas"], "BetaBuds X2"))
        self.assertTrue(_contains(state["active_request_summary"], "certification") or _contains(state["active_request_summary"], "scoping") or _contains(state["active_request_summary"], "認證"))
        self.assertIn("BetaBuds X2", composed_query)
        self.assertRegex(composed_query.lower(), r"certification|scoping|認證")

    @unittest.expectedFailure
    def test_region_followup_preserves_active_product_and_adds_japan_delta(self) -> None:
        memory = self.new_memory()
        self.update_turn(memory, TURN_1)
        self.update_turn(memory, TURN_2)
        state = self.update_turn(memory, TURN_3, retrieved_docs=["區域認證矩陣_EU_US_JP.md"])
        composed_query = self.compose_query(memory, TURN_3)

        self.assertTrue(_contains(state["active_products"], "BetaBuds X2"))
        self.assertTrue(_contains(state["active_regions"], "Japan"))
        self.assertTrue(_contains(state["active_context_deltas"], "Japan"))
        self.assertIn("BetaBuds X2", composed_query)
        self.assertIn("Japan", composed_query)
        self.assertRegex(composed_query.lower(), r"certification|scoping|認證")

    @unittest.expectedFailure
    def test_citation_recall_uses_last_retrieved_docs_without_new_product_task(self) -> None:
        memory = self.new_memory()
        self.update_turn(
            memory,
            TURN_1,
            retrieved_docs=[
                "產品A_AlphaBuds_X1_規格與認證.md",
                "區域認證矩陣_EU_US_JP.md",
                "無線測試與認證Scoping_SOP.md",
            ],
        )
        before = self.snapshot(memory)
        state = self.update_turn(memory, TURN_4)

        self.assertIn(self.route_or_action(state), {"history_recall", "citation_recall", "recall_docs"})
        self.assertEqual(before["last_retrieved_docs"], state["last_retrieved_docs"])
        self.assertEqual(before["active_request_summary"], state["active_request_summary"])

    @unittest.expectedFailure
    def test_guarantee_query_triggers_refusal_or_escalation_boundary(self) -> None:
        memory = self.new_memory()
        self.update_turn(memory, TURN_1)
        state = self.update_turn(memory, TURN_5, retrieved_docs=["產品認證風險邊界Policy.md"])

        action = self.route_or_action(state)
        self.assertIn(action, {"refuse", "escalate", "refusal", "generate_draft_and_escalate"})
        self.assertTrue(_contains(state, "Guarantee") or _contains(state, "保證") or _contains(state, "不得"))
        self.assertFalse(_contains(state, "一定通過"))

    @unittest.expectedFailure
    def test_new_unrelated_product_task_replaces_or_resets_active_summary(self) -> None:
        memory = self.new_memory()
        self.update_turn(memory, TURN_1)
        state = self.update_turn(memory, TURN_6, retrieved_docs=["產品C_GammaHub_C1_規格與認證.md"])

        self.assertTrue(_contains(state["active_products"], "GammaHub C1"))
        self.assertTrue(_contains(state["active_request_summary"], "GammaHub C1"))
        self.assertFalse(_contains(state["active_request_summary"], "AlphaBuds X1"))
        self.assertTrue(_contains(state["active_spec_fields"], "no wireless") or _contains(state["active_spec_fields"], "無線功能") or _contains(state["active_spec_fields"], "no radio"))

    @unittest.expectedFailure
    def test_memory_is_bounded_and_deduplicates_products_regions_and_docs(self) -> None:
        memory = self.new_memory(max_recent_turns=3, max_context_deltas=4, max_retrieved_docs=3)
        turns = [TURN_1, TURN_2, TURN_3, TURN_3, TURN_4, TURN_5, TURN_6, TURN_7]
        docs = [
            "產品A_AlphaBuds_X1_規格與認證.md",
            "產品B_BetaBuds_X2_規格與認證.md",
            "區域認證矩陣_EU_US_JP.md",
            "區域認證矩陣_EU_US_JP.md",
            "產品認證風險邊界Policy.md",
        ]
        for turn in turns:
            self.update_turn(memory, turn, retrieved_docs=docs)
        state = self.snapshot(memory)

        self.assertLessEqual(len(state["recent_turns"]), 3)
        self.assertLessEqual(len(state["active_context_deltas"]), 4)
        self.assertLessEqual(len(state["last_retrieved_docs"]), 3)
        self.assertEqual(len(state["active_products"]), len(set(state["active_products"])))
        self.assertEqual(len(state["active_regions"]), len(set(state["active_regions"])))
        self.assertEqual(len(state["last_retrieved_docs"]), len(set(state["last_retrieved_docs"])))


class ProductContextMemoryAcceptanceScenarioTests(
    ProductConversationMemoryContractMixin,
    unittest.TestCase,
):
    @unittest.expectedFailure
    def test_full_seven_turn_demo_scenario(self) -> None:
        memory = self.new_memory(max_recent_turns=6, max_context_deltas=8, max_retrieved_docs=8)

        state = self.update_turn(
            memory,
            TURN_1,
            retrieved_docs=[
                "產品A_AlphaBuds_X1_規格與認證.md",
                "區域認證矩陣_EU_US_JP.md",
                "無線測試與認證Scoping_SOP.md",
            ],
        )
        self.assertTrue(_contains(state["active_products"], "AlphaBuds X1"))
        self.assertTrue(_contains(state["active_regions"], "EU") or _contains(state["active_regions"], "Europe"))
        self.assertTrue(_contains(state["active_request_summary"], "scoping") or _contains(state["active_request_summary"], "認證"))
        self.assertTrue(_contains(state["last_retrieved_docs"], "產品A_AlphaBuds_X1_規格與認證.md"))

        state = self.update_turn(memory, TURN_2, retrieved_docs=["產品B_BetaBuds_X2_規格與認證.md"])
        self.assertTrue(_contains(state["active_products"], "BetaBuds X2"))
        self.assertRegex(self.compose_query(memory, TURN_2).lower(), r"certification|scoping|認證")

        state = self.update_turn(memory, TURN_3, retrieved_docs=["區域認證矩陣_EU_US_JP.md"])
        self.assertTrue(_contains(state["active_regions"], "Japan"))
        self.assertTrue(_contains(state["active_products"], "BetaBuds X2"))
        self.assertTrue(_contains(state["last_retrieved_docs"], "區域認證矩陣_EU_US_JP.md"))

        state = self.update_turn(memory, TURN_4)
        self.assertIn(self.route_or_action(state), {"history_recall", "citation_recall", "recall_docs"})
        self.assertTrue(_contains(state["last_retrieved_docs"], "產品B_BetaBuds_X2_規格與認證.md"))

        state = self.update_turn(memory, TURN_5, retrieved_docs=["產品認證風險邊界Policy.md"])
        self.assertIn(self.route_or_action(state), {"refuse", "escalate", "refusal", "generate_draft_and_escalate"})
        self.assertTrue(_contains(state["last_retrieved_docs"], "產品認證風險邊界Policy.md"))

        state = self.update_turn(memory, TURN_6, retrieved_docs=["產品C_GammaHub_C1_規格與認證.md"])
        self.assertTrue(_contains(state["active_products"], "GammaHub C1"))
        self.assertTrue(_contains(state, "no wireless") or _contains(state, "無線功能"))
        self.assertFalse(_contains(state, "GammaHub C1 Bluetooth setup mode"))

        state = self.update_turn(memory, TURN_7, retrieved_docs=["產品D_DeltaCam_D4_規格與認證.md"])
        self.assertTrue(_contains(state["active_products"], "DeltaCam D4"))
        self.assertTrue(_contains(state["active_spec_fields"], "Wi-Fi"))
        self.assertTrue(_contains(state["active_spec_fields"], "Bluetooth"))
        self.assertTrue(_contains(state["active_request_summary"], "complex") or _contains(state["active_request_summary"], "複雜"))


if __name__ == "__main__":
    unittest.main()

