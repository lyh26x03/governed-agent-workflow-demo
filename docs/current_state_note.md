# Current State Note — Multi-turn Product Context Memory

**Branch:** `feature/product-context-memory`  
**Date:** 2026-06-29  
**Tests:** 51 / 51 passing (`python -m unittest discover -s tests -v`)  
**Core artifact:** [`product_context_memory.py`](../product_context_memory.py)

---

## 1. What the memory does

`ProductConversationMemory` is a **deterministic, bounded, auditable** state object that tracks what the conversation is about across turns. It is wired into `app.py` as an augmentation layer around the existing governance router — it does **not** replace any governance logic.

### State schema

| Field | Meaning |
|---|---|
| `active_request_summary` | Current task skeleton, e.g. `"BetaBuds X2 Japan certification scoping"` |
| `active_context_deltas` | Ordered log of follow-up changes (`"switched to BetaBuds X2"`, `"added region Japan"`) |
| `active_products` | All products in play this session (deduped, capped) |
| `active_regions` | All regions in play (deduped, capped) |
| `active_spec_fields` | All spec dimensions mentioned (deduped, capped) |
| `last_retrieved_docs` | Docs actually retrieved this session (LRU, unique, bounded) |
| `recent_turns` | Per-turn compact records (ring buffer with `maxlen`) |
| `route` / `risk_type` / `boundary_note` | Governance trace fields, written to audit log each turn |

---

## 2. How it operates turn by turn

Each user message flows through five layers inside the memory object:

```
user_query
  │
  ▼  (1) Entity extraction      products / regions / spec fields  (catalog + word-boundary regex)
  ▼  (2) Intent signals         guarantee · recall · out-of-scope · follow-up marker · spec-conflict
  ▼  (3) Policy router          new_task | product_followup | region_followup | spec_followup
  │                             | citation_recall | generate_draft_and_escalate | escalate_conflict
  │                             | out_of_scope        (+ human-readable rationale per turn)
  ▼  (4) State update           bounded + deduped active sets, LRU docs, ring-buffer turns
  ▼  (5) Retrieval composer     active product + region + spec + task core + raw query
```

The router emits a **rationale string** on every turn, which is written into the audit log (`memory_route`, `product_memory`). Every decision is replayable in mock mode.

---

## 3. Memory behaviour on each route type

This is the most important section for interview / review purposes.

### `out_of_scope` — memory is **not updated, not cleared**

- Risk flags (`_last_risk_type = "Out of Scope"`, `boundary_note`) are set for the audit log.
- **No entity is written** into `active_products`, `active_regions`, `active_spec_fields`, `active_request_summary`, or `active_context_deltas`.
- The previous task skeleton survives untouched. A follow-up on the next turn can still resume.
- Locked by: `test_out_of_scope_turn_does_not_pollute_product_memory`

### `generate_draft_and_escalate` (guarantee/commitment) — memory is **partially updated**

- Risk flag set: `_last_risk_type = "Guarantee/Commitment"`.
- A delta `"guarantee request → escalate to human review"` is appended to `active_context_deltas`.
- **The forbidden phrase ("一定通過", etc.) is never written** into any summary or delta field.
- Products/regions/specs are **not** added from this turn (the request skeleton is preserved from prior turns).
- Locked by: `test_guarantee_turn_never_synthesizes_forbidden_phrases`, `test_guarantee_preserves_prior_task_context`

### `escalate_conflict` (spec contradiction) — memory **records the product but does not adopt the false claim**

- Products mentioned in the conflicting turn are added to `active_products` (to keep track of what was discussed).
- A delta `"spec conflict → escalate (…)"` is appended.
- The claimed radio/spec **is not** added to `active_spec_fields`; the false claim is not baked into future retrieval queries.
- Locked by: `test_spec_conflict_claiming_radio_absent_from_profile_escalates`, `test_no_radio_product_claimed_to_have_bluetooth_escalates`

### `new_task` — memory is **replaced / rebuilt**

- `active_request_summary` is rebuilt around the new product/region/spec.
- `active_spec_fields` is **reset** to only the current turn's specs.
- New product becomes `_primary_product`; products/regions are accumulated (not cleared) in `active_products` / `active_regions` so cross-task history remains queryable.
- A delta `"new task: …"` is appended.

### `product_followup` / `region_followup` / `spec_followup` / `followup` — memory is **updated by delta**

- Existing task skeleton preserved; only the changed dimension is updated.
- A delta is appended describing what changed.
- `active_request_summary` is rebuilt to reflect the new focus.

### `citation_recall` — memory is **read, not written** (via `classify()`)

- The `classify()` method is a pure read-only peek; it changes no state.
- The actual `update_from_turn()` call that follows is what records that this turn happened.
- During the recall turn itself, no new docs are retrieved, so `last_retrieved_docs` does not change.
- Locked by: `test_recall_accumulates_docs_across_turns_and_is_stable`

---

## 4. Integration into `app.py`

Memory is wired into `add_user_message` as three additive blocks:

1. **Rescue layer** (before branching): if the keyword router returns `out_of_scope` but memory shows an active task and a continuation route, the turn is rescued to controlled retrieval (`build_memory_continuation_route`).
2. **Citation recall branch**: if memory route is `citation_recall` and `last_retrieved_docs` is non-empty, answer directly from memory without re-searching the knowledge base.
3. **Memory-enriched retrieval**: for the `search` path, `compose_retrieval_query(content)` replaces the raw content as the retrieval input, fusing all active state into a richer query.
4. **State update** (after all results): `update_from_turn(content, retrieved_docs=…)` writes the turn into memory.
5. **Audit log**: `log["memory_route"]` and `log["product_memory"]` are appended to the governance trace.
6. **Clear button**: resets `st.session_state.product_memory = ProductConversationMemory()`.

The baseline carry-forward lines from before this feature are preserved verbatim (pinned by `test_current_carry_forward_regression.py`) — they run first but are immediately overridden by the richer memory query.

---

## 5. Test suite (51 tests, 5 suites)

| Suite | Count | What it covers |
|---|---|---|
| `test_corpus_integrity.py` | 9 | Corpus structure, demo disclaimers, product coverage |
| `test_current_carry_forward_regression.py` | 3 | Pins the pre-memory baseline AND the composed-query regression target |
| `test_product_context_memory_contract.py` | 9 | Schema, deterministic turn updates, bounded memory, citation recall, escalation, 7-turn acceptance |
| `test_product_context_memory_extended.py` | 23 | Adversarial: region carry-forward, 15-/60-turn horizons, governance fail-safes, contradiction detection, word-boundary safety, determinism, observability |
| `test_app_memory_integration.py` | 7 | Memory wired into app: follow-up rescue, citation recall, off-topic zero-retrieval, guarantee escalation, audit log |

Run command (Anaconda environment has a shadowing `tests` package — always use `discover`):

```bash
python -m unittest discover -s tests -v
```

---

## 6. Known limitations (honest)

- **Catalog-only entity recognition**: products and regions are matched via hardcoded alias lists + word-boundary regex. A brand-new product code not in the catalog will not be tracked. Failure mode is safe: missed entity falls back to the raw query.
- **Declarative-vs-question heuristic**: the interrogative guard (`嗎|呢|是否|？`) is simple pattern matching. A declaration phrased as a trailing question after an assertion (e.g. "AlphaBuds X1 有 Wi-Fi，去美國要測嗎？") may not escalate because the interrogative is detected last. Safe failure: the RAG answer will naturally contradict the false premise.
- **No cross-session persistence**: memory lives in `st.session_state` and is lost on page reload. Intentional for this demo scope.
- **No RL or learned routing**: explicitly forbidden by the test plan and the governance constraint. The deterministic router is the right design for this auditable demo.

---

## 7. Interview talking points

**Q: What problem does this solve?**  
A naive keyword router treats each user message in isolation. A one-word follow-up like "那日本呢？" has no domain keyword — it gets dropped to zero-retrieval. The memory layer maintains structured state so a 1-word follow-up composes to a full retrieval query like "BetaBuds X2 EU Japan certification scoping 那日本呢？".

**Q: Why deterministic instead of a learned router?**  
This is a governance demo — every decision must be auditable, replayable, and unit-testable with fixed inputs. An opaque ML router can't satisfy those requirements. The deterministic router emits a human-readable rationale per turn (visible in the Governance Trace console) and is fully covered by 51 unit tests.

**Q: What happens to memory when the user asks an off-topic question?**  
Nothing is written. The task skeleton, active products, regions, and docs are all preserved. The next turn can resume the same task. This is intentional and tested (`test_out_of_scope_turn_does_not_pollute_product_memory`).

**Q: What happens when the user asks for a guarantee ("一定會通過嗎")?**  
The governance router escalates to human review (unchanged from before this feature). The memory records a delta `"guarantee request → escalate"` but never synthesizes or echoes the forbidden phrase. Tested with both a turn-level snapshot check and a full serialization-to-JSON scan.

**Q: Where would you put a learned layer if you added one later?**  
`classify()` is a pure function with a stable `(route, rationale)` signature. A learned scorer could replace the rule body inside it while the deterministic guards (guarantee / conflict / boundedness) remain as a fail-safe envelope — adaptivity without surrendering governance.
