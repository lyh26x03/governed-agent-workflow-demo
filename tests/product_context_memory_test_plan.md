# Product Context Memory Test Plan

These tests define the expected behavior for the product/certification context-memory
mechanism. The project remains a demo, and these tests do not claim real certification
correctness.

> **Status (implemented):** `ProductConversationMemory` now lives in
> [`product_context_memory.py`](../product_context_memory.py) and is wired into
> `app.py`. The 10 originally-`xfail` tests are now genuine passing tests (the
> `@unittest.expectedFailure` placeholders were removed once the feature shipped).
> Two new suites were added. **Total: 51 tests passing.**
> See [`docs/product_context_memory_report.md`](../docs/product_context_memory_report.md).

## Suites

- `test_corpus_integrity.py` (9) — simulated corpus exists, demo disclaimers, Product
  A/B/C/D distinction, EU/US/Japan coverage, no-guarantee policy, multi-turn FAQ examples.
- `test_current_carry_forward_regression.py` (3) — pins the documented baseline
  (immediate-previous-query carry-forward) **and** the regression target proving the
  composed query preserves product + certification context across turns.
- `test_product_context_memory_contract.py` (9) — schema fields, deterministic turn
  updates, bounded + deduplicated memory, citation recall, refusal/escalation routing,
  context-rich query composition, and the full 7-turn acceptance scenario.
- `test_product_context_memory_extended.py` (23) — adversarial battle-tests: region
  carry-forward across product swaps, 15- and 60-turn horizons, governance fail-safes,
  contradiction detection (claim vs. question), tokenizer word-boundary safety, empty
  input, determinism, observability.
- `test_app_memory_integration.py` (7) — memory wired into `app.add_user_message`:
  follow-up rescue from `out_of_scope`, citation recall from memory, genuine off-topic
  still zero-retrieval, guarantee still escalates, memory surfaced in the audit log.

## Implemented Object

`ProductConversationMemory` exposes the fields `active_products`, `active_regions`,
`active_spec_fields`, `active_request_summary`, `active_context_deltas`,
`last_retrieved_docs`, `recent_turns` (plus governance fields `route` / `risk_type`).
It supports deterministic turn updates, bounded memory, deduplication, citation recall,
refusal/escalation routing, a pure `classify()` peek, and `compose_retrieval_query`.

## Scope Boundaries (honored)

- Do not add real compliance logic.
- Do not guarantee certification pass/fail.
- Do not introduce heavy dependencies. *(pure stdlib; no new requirements)*
- Do not introduce RL, learned routing, or opaque personalization for this demo stage.
  *(the policy router is deterministic and emits a rationale per turn)*

