# Product Context Memory Test Plan

These tests define the expected behavior for the next product/certification context-memory implementation. The project remains a demo, and these tests do not claim real certification correctness.

## Passing Tests Now

- `test_corpus_integrity.py` verifies the simulated corpus exists, includes clear demo disclaimers, distinguishes Product A/B/C/D, covers EU/US/Japan, includes a no-guarantee policy, and contains multi-turn FAQ examples.
- `test_current_carry_forward_regression.py` documents the current app limitation: carry-forward composition is based on only the immediately previous user query.

## Expected Failures Until Memory Is Implemented

- `test_product_context_memory_contract.py` expects a future `ProductConversationMemory` object, preferably in `product_context_memory.py`.
- The future object should expose the fields `active_products`, `active_regions`, `active_spec_fields`, `active_request_summary`, `active_context_deltas`, `last_retrieved_docs`, and `recent_turns`.
- The future object should support deterministic turn updates, bounded memory, deduplication, citation recall, refusal/escalation routing, and context-rich retrieval query composition.
- `test_current_carry_forward_regression.py::test_future_turn3_composed_query_preserves_product_and_certification_context` is a regression target for replacing immediate-previous-query carry-forward.

## Scope Boundaries

- Do not add real compliance logic.
- Do not guarantee certification pass/fail.
- Do not introduce heavy dependencies.
- Do not introduce RL, learned routing, or opaque personalization for this demo stage.

