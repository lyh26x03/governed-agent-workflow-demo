from __future__ import annotations

import inspect
import unittest


class CurrentCarryForwardRegressionTests(unittest.TestCase):
    def test_current_app_carry_forward_is_immediate_previous_query_only(self) -> None:
        import app

        source = inspect.getsource(app.add_user_message)
        self.assertIn('previous_user_query = conversation_state.get("previous_user_query", "")', source)
        self.assertIn('search_query = f"{previous_user_query} {content}"', source)

    def test_current_immediate_previous_query_strategy_drops_turn1_task_context(self) -> None:
        turn_1 = "AlphaBuds X1 Europe certification scoping CE RED"
        turn_2 = "BetaBuds X2"
        turn_3 = "Japan"

        current_app_style_query = f"{turn_2} {turn_3}"

        self.assertIn("BetaBuds X2", current_app_style_query)
        self.assertIn("Japan", current_app_style_query)
        self.assertNotIn("AlphaBuds X1", current_app_style_query)
        self.assertNotIn("certification", current_app_style_query)
        self.assertNotIn("scoping", current_app_style_query)

        # Keep turn_1 referenced so the test makes the dropped context obvious.
        self.assertIn("certification scoping", turn_1)

    def test_future_turn3_composed_query_preserves_product_and_certification_context(self) -> None:
        from product_context_memory import ProductConversationMemory

        memory = ProductConversationMemory(max_recent_turns=5, max_context_deltas=8, max_retrieved_docs=8)
        memory.update_from_turn("AlphaBuds X1 Europe certification scoping CE RED")
        memory.update_from_turn("What if it is BetaBuds X2?")
        composed_query = memory.compose_retrieval_query("What about Japan?")

        self.assertIn("BetaBuds X2", composed_query)
        self.assertIn("Japan", composed_query)
        self.assertRegex(composed_query.lower(), r"certification|scoping")
        self.assertNotEqual("What if it is BetaBuds X2? What about Japan?", composed_query)


if __name__ == "__main__":
    unittest.main()

