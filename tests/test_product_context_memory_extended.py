"""Extended, adversarial battle-tests for ProductConversationMemory.

These go beyond the 7-turn contract: long horizons (15–60 turns), governance
fail-safes, contradiction detection, region carry-forward across product swaps,
boundedness under stress, tokenizer word-boundary safety, and determinism.

They are written to be deterministic and dependency-free (no streamlit / no LLM).
"""

from __future__ import annotations

import json
import unittest
from typing import Any

from product_context_memory import (
    ProductConversationMemory,
    detect_claimed_radios,
    detect_regions,
    detect_spec_conflict,
)


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


def _new(**kwargs: Any) -> ProductConversationMemory:
    return ProductConversationMemory(**kwargs)


class RegionCarryForwardTests(unittest.TestCase):
    """區域脈絡必須能跨產品切換被保留（這是當前 app 丟失的核心 context）。"""

    def test_region_is_preserved_when_switching_products(self) -> None:
        m = _new()
        m.update_from_turn(TURN_1)  # AlphaBuds X1 + EU
        state = m.update_from_turn(TURN_2)  # follow-up swap -> BetaBuds X2
        self.assertEqual(state["route"], "product_followup")
        self.assertTrue(_contains(state["active_regions"], "EU"))
        self.assertTrue(_contains(state["active_products"], "BetaBuds X2"))
        # 區域應出現在組裝後的 retrieval query。
        self.assertIn("EU", m.compose_retrieval_query(TURN_2))

    def test_us_region_followup_keeps_active_product(self) -> None:
        m = _new()
        m.update_from_turn(TURN_1)  # AlphaBuds X1 + EU
        state = m.update_from_turn("那如果是去美國呢？")  # app TEST_QUESTION 6
        self.assertEqual(state["route"], "region_followup")
        self.assertTrue(_contains(state["active_regions"], "US"))
        self.assertTrue(_contains(state["active_products"], "AlphaBuds X1"))
        composed = m.compose_retrieval_query("那如果是去美國呢？")
        self.assertIn("US", composed)
        self.assertIn("AlphaBuds X1", composed)

    def test_product_followup_with_only_generic_certification_word_is_not_new_task(self) -> None:
        # 回歸：generic 詞（認證/scoping）不得把純產品 follow-up 誤判為新任務而丟掉區域。
        m = _new()
        m.update_from_turn(TURN_1)  # AlphaBuds X1 + EU
        state = m.update_from_turn("那 BetaBuds X2 的認證呢？")
        self.assertEqual(state["route"], "product_followup")
        self.assertTrue(_contains(state["active_regions"], "EU"))
        self.assertTrue(_contains(state["active_request_summary"], "BetaBuds X2"))


class GovernanceBoundaryTests(unittest.TestCase):
    """治理 / fail-safe 邊界：保證請求與規格矛盾。"""

    def test_guarantee_turn_never_synthesizes_forbidden_phrases(self) -> None:
        m = _new()
        m.update_from_turn(TURN_1)
        state = m.update_from_turn(TURN_5, retrieved_docs=["產品認證風險邊界Policy.md"])
        self.assertEqual(state["route"], "generate_draft_and_escalate")
        self.assertEqual(state["risk_type"], "Guarantee/Commitment")
        # memory 不得「合成」承諾語：summary 與 deltas 不能出現保證 / 一定字樣。
        self.assertNotIn("一定", state["active_request_summary"])
        self.assertNotIn("保證", state["active_request_summary"])
        for delta in state["active_context_deltas"]:
            self.assertNotIn("一定通過", delta)
            self.assertNotIn("保證", delta)
        # 連續禁語不得出現在整個 snapshot 序列化結果。
        self.assertNotIn("一定通過", json.dumps(state, ensure_ascii=False))

    def test_guarantee_preserves_prior_task_context(self) -> None:
        m = _new()
        m.update_from_turn(TURN_1)
        summary_before = m.snapshot()["active_request_summary"]
        m.update_from_turn(TURN_5)
        self.assertEqual(m.snapshot()["active_request_summary"], summary_before)

    def test_spec_conflict_claiming_radio_absent_from_profile_escalates(self) -> None:
        m = _new()
        state = m.update_from_turn("AlphaBuds X1 其實有內建 Wi-Fi 功能")
        self.assertEqual(state["route"], "escalate_conflict")
        self.assertEqual(state["risk_type"], "Spec Conflict")
        self.assertTrue(_contains(state["active_products"], "AlphaBuds X1"))

    def test_no_radio_product_claimed_to_have_bluetooth_escalates(self) -> None:
        m = _new()
        state = m.update_from_turn("我們的 GammaHub C1 其實有藍牙配對功能")
        self.assertEqual(state["route"], "escalate_conflict")

    def test_consistent_multiradio_claim_is_not_a_conflict(self) -> None:
        # DeltaCam D4 profile 本就有 Wi-Fi + Bluetooth -> 不是矛盾。
        m = _new()
        state = m.update_from_turn("DeltaCam D4 有 Wi-Fi 和 Bluetooth，scoping 怎麼看？")
        self.assertNotEqual(state["route"], "escalate_conflict")
        self.assertEqual(state["risk_type"], "None")

    def test_negation_or_question_about_radio_is_not_a_conflict(self) -> None:
        # TURN_6 提到「藍牙」但是在「沒有無線功能」的否定脈絡下提問，不應誤判矛盾。
        self.assertFalse(detect_spec_conflict(TURN_6, ["GammaHub C1"])[0])
        self.assertEqual(detect_claimed_radios("GammaHub C1 沒有無線，需要藍牙測試嗎？"), set())

    def test_interrogative_about_radio_is_answered_not_escalated(self) -> None:
        # "BetaBuds X2 有 Wi-Fi 嗎？" 是提問（非宣稱），不應升級成 spec conflict。
        m = _new()
        state = m.update_from_turn("BetaBuds X2 有 Wi-Fi 嗎，去美國要測嗎？")
        self.assertNotEqual(state["route"], "escalate_conflict")
        self.assertEqual(detect_claimed_radios("BetaBuds X2 有 Wi-Fi 嗎？"), set())
        # 但同樣內容用陳述句宣稱，就要升級。
        m2 = _new()
        self.assertEqual(
            m2.update_from_turn("BetaBuds X2 其實有內建 Wi-Fi 功能")["route"],
            "escalate_conflict",
        )

    def test_out_of_scope_turn_does_not_pollute_product_memory(self) -> None:
        m = _new()
        m.update_from_turn(TURN_1)
        before = m.snapshot()
        state = m.update_from_turn("請幫我推薦今天晚餐")
        self.assertEqual(state["route"], "out_of_scope")
        self.assertEqual(state["active_products"], before["active_products"])
        self.assertEqual(state["active_request_summary"], before["active_request_summary"])


class RetrievalQueryCompositionTests(unittest.TestCase):
    def test_bare_followup_query_is_enriched_beyond_raw_text(self) -> None:
        m = _new()
        m.update_from_turn(TURN_1)
        m.update_from_turn(TURN_2)
        composed = m.compose_retrieval_query(TURN_3)  # "那日本呢？"
        self.assertIn("BetaBuds X2", composed)
        self.assertIn("Japan", composed)
        self.assertRegex(composed.lower(), r"certification|scoping")
        self.assertNotEqual(composed.strip(), TURN_3.strip())
        self.assertGreater(len(composed), len(TURN_3))

    def test_compose_query_does_not_emit_guarantee_phrase(self) -> None:
        m = _new()
        m.update_from_turn(TURN_1)
        m.update_from_turn(TURN_5)
        composed = m.compose_retrieval_query("再確認一下下一步")
        self.assertNotIn("一定通過", composed)

    def test_compose_marks_complex_for_multiradio_product(self) -> None:
        m = _new()
        m.update_from_turn(TURN_7, retrieved_docs=["產品D_DeltaCam_D4_規格與認證.md"])
        composed = m.compose_retrieval_query("下一步呢？")
        self.assertIn("complex", composed.lower())


class CitationRecallTests(unittest.TestCase):
    def test_recall_accumulates_docs_across_turns_and_is_stable(self) -> None:
        m = _new(max_retrieved_docs=8)
        m.update_from_turn(TURN_1, retrieved_docs=["產品A_AlphaBuds_X1_規格與認證.md"])
        m.update_from_turn(TURN_2, retrieved_docs=["產品B_BetaBuds_X2_規格與認證.md"])
        m.update_from_turn(TURN_3, retrieved_docs=["區域認證矩陣_EU_US_JP.md"])
        before = m.snapshot()
        state = m.update_from_turn(TURN_4)  # recall, no new docs
        self.assertEqual(state["route"], "citation_recall")
        self.assertEqual(before["last_retrieved_docs"], state["last_retrieved_docs"])
        self.assertTrue(_contains(state["last_retrieved_docs"], "產品A_AlphaBuds_X1_規格與認證.md"))
        self.assertTrue(_contains(state["last_retrieved_docs"], "產品B_BetaBuds_X2_規格與認證.md"))


class SpecFollowupTests(unittest.TestCase):
    def test_spec_followup_keeps_product_and_region(self) -> None:
        m = _new()
        m.update_from_turn(TURN_1)  # AlphaBuds + EU
        state = m.update_from_turn("那它的頻段和電池呢？")
        self.assertEqual(state["route"], "spec_followup")
        self.assertTrue(_contains(state["active_products"], "AlphaBuds X1"))
        self.assertTrue(_contains(state["active_regions"], "EU"))
        self.assertTrue(_contains(state["active_spec_fields"], "frequency band"))


class TokenizerSafetyTests(unittest.TestCase):
    def test_region_detection_respects_word_boundaries(self) -> None:
        self.assertEqual(detect_regions("What is the status because of this?"), [])
        self.assertIn("US", detect_regions("ship it to the US please"))
        self.assertIn("US", detect_regions("出口到美國"))
        self.assertIn("EU", detect_regions("for the European market"))
        self.assertIn("Japan", detect_regions("what about Japan?"))

    def test_empty_and_whitespace_queries_do_not_crash(self) -> None:
        m = _new()
        for q in ("", "   ", "\n\t"):
            state = m.update_from_turn(q)
            self.assertIsInstance(state, dict)
        self.assertEqual(m.snapshot()["active_products"], [])


class LongHorizonAndBoundednessTests(unittest.TestCase):
    def test_fifteen_turn_horizon_preserves_and_bounds_context(self) -> None:
        m = _new(max_recent_turns=6, max_context_deltas=8, max_retrieved_docs=8)
        script = [
            (TURN_1, ["產品A_AlphaBuds_X1_規格與認證.md", "區域認證矩陣_EU_US_JP.md"]),
            (TURN_2, ["產品B_BetaBuds_X2_規格與認證.md"]),
            (TURN_3, ["區域認證矩陣_EU_US_JP.md"]),
            ("那如果是去美國呢？", ["區域認證矩陣_EU_US_JP.md"]),
            (TURN_4, []),
            ("那它的頻段呢？", ["無線測試與認證Scoping_SOP.md"]),
            (TURN_5, ["產品認證風險邊界Policy.md"]),
            ("請幫我推薦今天晚餐", []),
            (TURN_6, ["產品C_GammaHub_C1_規格與認證.md"]),
            ("那 GammaHub C1 的電源和連接埠呢？", ["產品C_GammaHub_C1_規格與認證.md"]),
            (TURN_7, ["產品D_DeltaCam_D4_規格與認證.md"]),
            ("那 DeltaCam D4 去歐洲呢？", ["區域認證矩陣_EU_US_JP.md"]),
            ("DeltaCam D4 其實沒有 Wi-Fi，只有藍牙嗎？", ["產品D_DeltaCam_D4_規格與認證.md"]),
            (TURN_4, []),
            ("可以保證 DeltaCam D4 一定會通過嗎？", ["產品認證風險邊界Policy.md"]),
        ]
        for query, docs in script:
            m.update_from_turn(query, retrieved_docs=docs)

        state = m.snapshot()
        # 全部四個產品都被記得（去重）。
        for product in ("AlphaBuds X1", "BetaBuds X2", "GammaHub C1", "DeltaCam D4"):
            self.assertTrue(_contains(state["active_products"], product), product)
        # 有界性。
        self.assertLessEqual(len(state["recent_turns"]), 6)
        self.assertLessEqual(len(state["active_context_deltas"]), 8)
        self.assertLessEqual(len(state["last_retrieved_docs"]), 8)
        # 去重不變式。
        self.assertEqual(len(state["active_products"]), len(set(state["active_products"])))
        self.assertEqual(len(state["active_regions"]), len(set(state["active_regions"])))
        self.assertEqual(len(state["last_retrieved_docs"]), len(set(state["last_retrieved_docs"])))
        # 最後一輪是 guarantee -> 升級。
        self.assertEqual(state["route"], "generate_draft_and_escalate")

    def test_sixty_turn_stress_stays_bounded(self) -> None:
        m = _new(max_recent_turns=4, max_context_deltas=5, max_retrieved_docs=3)
        cycle = [TURN_1, TURN_2, TURN_3, TURN_6, TURN_7]
        docs = ["d1.md", "d2.md", "d3.md", "d2.md", "d4.md"]
        for i in range(60):
            m.update_from_turn(cycle[i % len(cycle)], retrieved_docs=docs)
        state = m.snapshot()
        self.assertLessEqual(len(state["recent_turns"]), 4)
        self.assertLessEqual(len(state["active_context_deltas"]), 5)
        self.assertLessEqual(len(state["last_retrieved_docs"]), 3)
        self.assertEqual(len(state["last_retrieved_docs"]), len(set(state["last_retrieved_docs"])))
        self.assertEqual(len(state["active_products"]), len(set(state["active_products"])))


class DeterminismAndObservabilityTests(unittest.TestCase):
    def test_same_script_yields_identical_snapshots(self) -> None:
        script = [TURN_1, TURN_2, TURN_3, TURN_4, TURN_5, TURN_6, TURN_7]

        def run() -> dict[str, Any]:
            m = _new()
            for q in script:
                m.update_from_turn(q, retrieved_docs=["區域認證矩陣_EU_US_JP.md"])
            return m.snapshot()

        self.assertEqual(run(), run())

    def test_debug_dict_exposes_config_and_rationale(self) -> None:
        m = _new()
        m.update_from_turn(TURN_1)
        m.update_from_turn(TURN_5)
        debug = m.to_debug_dict()
        self.assertIn("config", debug)
        self.assertIn("rationale_log", debug)
        self.assertTrue(all("rationale" in entry for entry in debug["rationale_log"]))

    def test_reset_clears_all_state(self) -> None:
        m = _new()
        m.update_from_turn(TURN_1)
        m.update_from_turn(TURN_2)
        m.reset()
        state = m.snapshot()
        self.assertEqual(state["active_products"], [])
        self.assertEqual(state["active_request_summary"], "")
        self.assertEqual(state["recent_turns"], [])


if __name__ == "__main__":
    unittest.main()
