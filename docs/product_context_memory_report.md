# Product Context Memory — Implementation & Test Report

**Scope:** a robust, governed multi-turn / memory mechanism for the Certification
Workflow Agent demo.
**Branch:** `feature/product-context-memory`
**Core artifact:** [`product_context_memory.py`](../product_context_memory.py) —
`ProductConversationMemory`
**Result:** **51/51 tests pass** (was 11 pass / 10 xfail). The 10 placeholder
`xfail` tests are now genuine green tests; 30 new battle-tests were added.

---

## 1. Philosophy

This is a *governed* agent. Its entire value proposition is that every decision is
auditable, reproducible, and fail-safe. That single fact dictated every design call:

1. **Deterministic over learned.** The brief floated a "learned policy router / RL."
   The committed test plan explicitly forbids it (*"Do not introduce RL, learned
   routing, or opaque personalization… no heavy dependencies"*), and rightly so: an
   opaque router cannot be replayed in mock mode, cannot explain itself to an auditor,
   and cannot be unit-tested deterministically. So the "intelligence" lives in a
   **transparent, rule-based policy router** where *every* turn emits a human-readable
   `rationale` (see `to_debug_dict()`). This is the more defensible "advanced design"
   for this product — and it is exactly where a learned layer could later slot in
   **behind** the same interface without weakening governance (see §6).

2. **Memory is structured state, not a transcript.** Stuffing raw history into a prompt
   is the naive baseline. Instead we distill each turn into a small, typed state object
   (products / regions / spec fields / task skeleton / cited docs) that can be fed
   directly into retrieval and citation recall. Structure is what survives 60 turns;
   raw text is what drifts.

3. **Bounded by construction.** Every collection has an explicit cap (deque `maxlen`
   for turns/deltas, LRU-style ordered-unique for cited docs, dedup caps for
   products/regions/specs). Long conversations cannot blow up latency or smuggle in
   context drift.

4. **Fail-safe boundaries are non-negotiable.** Guarantee/commitment requests and
   spec contradictions always route to escalation, and the memory **never synthesizes**
   a forbidden phrase (e.g. "一定通過") into a summary, delta, or composed query.

---

## 2. Architecture

`ProductConversationMemory` is a five-layer pipeline. Each turn flows through:

```
user_query
   │
   ▼  (1) Entity extraction      products / regions / spec fields  (catalog + word-boundary regex)
   ▼  (2) Intent signals         guarantee · recall · out-of-scope · follow-up marker · spec-conflict
   ▼  (3) Policy router          new_task | product_followup | region_followup | spec_followup
   │                             | citation_recall | generate_draft_and_escalate | escalate_conflict
   │                             | out_of_scope        (+ rationale)
   ▼  (4) State store            active_request_summary skeleton, bounded+deduped active sets,
   │                             LRU last_retrieved_docs, ring-buffer recent_turns
   ▼  (5) Retrieval composer     active product + region + spec + task core + raw query
```

### State schema (the 7 contract fields + governance fields)

| field | meaning | discipline |
|---|---|---|
| `active_request_summary` | current task skeleton, e.g. `BetaBuds X2 Japan certification scoping` | rebuilt on focus change |
| `active_context_deltas` | chronological follow-up changes (`switched to BetaBuds X2`, `added region Japan`) | bounded deque, dedup |
| `active_products` / `active_regions` / `active_spec_fields` | everything in play this session | dedup + capped |
| `last_retrieved_docs` | docs actually cited/retrieved | **LRU**, unique, bounded |
| `recent_turns` | compact per-turn records | ring buffer (`maxlen`) |
| `route` / `risk_type` / `boundary_note` | governance trace for the audit log | per turn |

### The key discriminator: follow-up swap vs. new task

The hardest semantic call is distinguishing *"如果改成 BetaBuds X2 呢？"* (preserve the
EU certification task, just swap the product) from *"如果 GammaHub C1 沒有無線功能…"*
(reframe around a genuinely new product). The rule:

> **new task** ⟺ no task yet **OR** (a new product is introduced **AND** it carries a
> *substantive technical* spec, or it is not phrased as a follow-up).
> Otherwise it is a **follow-up swap** that preserves the task skeleton and appends a delta.

Crucially, the generic task word "certification/scoping/認證" is **excluded** from
"substantive spec," because it appears in nearly every certification question — counting
it would misfire *"那 BetaBuds X2 的認證呢？"* as a new task and silently drop the region.
(This was a real bug caught during iteration — see §4, Round 2.)

---

## 3. Integration into the app

The memory is an **augmentation + rescue layer** around the existing governance router
(`route_user_request`), not a replacement — the governance demo's behavior is preserved.
In [`app.py`](../app.py) `add_user_message`:

* **Context-rich retrieval.** The search path now uses
  `memory.compose_retrieval_query(content)`. The original immediate-previous-query
  carry-forward lines are retained verbatim as a documented baseline (and pinned by
  `test_current_carry_forward_regression.py`).
* **Follow-up rescue.** A bare follow-up like *"那日本呢？"* has no domain keyword, so the
  keyword router drops it to `out_of_scope`. If memory shows an active task and a
  continuation route, the turn is **rescued back into controlled retrieval**. Genuine
  chit-chat ("推薦晚餐") — no active task / no follow-up — is *not* rescued.
* **Citation recall.** *"剛才你參考了哪些文件？"* is answered directly from
  `last_retrieved_docs` (no re-search), with the current task focus appended.
* **Observability.** The full memory snapshot + `memory_route` are written into the
  audit `last_log` and rendered as a `MEMORY` line in the Governance Trace console.

### Before vs. after, on the 7-turn demo

| turn | keyword router alone | with memory layer |
|---|---|---|
| T2 "如果改成 BetaBuds X2 呢？" | `out_of_scope` → zero retrieval | `product_followup` → **answered**, focus `BetaBuds X2 / EU` |
| T3 "那日本呢？" | depends on stray keyword | `region_followup` → focus `BetaBuds X2 / Japan` |
| T4 "剛才你參考了哪些文件？" | `out_of_scope` | `citation_recall` → lists the 5 remembered docs |
| T5 "一定會通過嗎？" | escalate | escalate (unchanged — boundary preserved) |

---

## 4. Iterative test-and-refine log

The implementation went through five observe→refine cycles. The value of TDD here was
that each refinement was a *named, tested* fix, not a silent edit.

**Round 1 — contract green.** Implemented the schema, router, bounded state, and
composer. All 10 placeholder `xfail` tests passed; converted them to real green tests.

**Round 2 — generic-term leak (real bug).** Reasoning through *"那 BetaBuds X2 的認證呢？"*
showed the new-task discriminator treated the task word "認證" as substantive spec,
misclassifying a product follow-up as a new task and dropping the region. Fix:
`GENERIC_SPEC_FIELDS` excluded from the discriminator. Locked by
`test_product_followup_with_only_generic_certification_word_is_not_new_task`.

**Round 3 — contradiction detection (new capability).** The corpus repeatedly demands
escalation when a user *claims a radio the product lacks* ("AlphaBuds X1 has Wi-Fi";
"GammaHub C1 has Bluetooth pairing"). Added a corpus-grounded `PRODUCT_RADIO_PROFILE`
and an `escalate_conflict` route. Guarded against the no-radio product's own
*negation* ("沒有無線功能") so TURN 6 is not a false positive.

**Round 4 — over-escalation on questions (precision fix).** End-to-end probing revealed
*"BetaBuds X2 有 Wi-Fi 嗎？"* (a **question**) was being flagged as a conflict. A question
should get a RAG answer that naturally corrects the premise; only a **declarative claim**
should escalate. Added `INTERROGATIVE_REGEX` guarding. Locked by
`test_interrogative_about_radio_is_answered_not_escalated`.

**Round 5 — app rescue + recall (headline integration).** The first end-to-end run showed
the memory *tracked* focus correctly while the app still dropped follow-ups to
zero-retrieval. Added the pure `classify()` peek, the out_of_scope rescue, and the
citation-recall handler. Locked by `test_app_memory_integration.py`.

---

## 5. Findings — edge cases & vulnerabilities probed

| # | Edge case | Behavior | Test |
|---|---|---|---|
| 1 | Region must survive a product swap | `EU` retained when AlphaBuds→BetaBuds | `test_region_is_preserved_when_switching_products` |
| 2 | 15- and 60-turn horizons | all 4 products remembered; every cap respected; dedup invariants hold | `LongHorizonAndBoundednessTests` |
| 3 | Guarantee never synthesizes禁語 | "一定"/"保證" absent from summary & deltas | `test_guarantee_turn_never_synthesizes_forbidden_phrases` |
| 4 | Off-topic mid-conversation | `out_of_scope`, product memory untouched | `test_out_of_scope_turn_does_not_pollute_product_memory` |
| 5 | False spec claim vs. honest question | claim → escalate; question → answer | `GovernanceBoundaryTests` |
| 6 | Tokenizer word boundaries | "status"/"because" ≠ region; "the US"/"European" do | `test_region_detection_respects_word_boundaries` |
| 7 | Empty / whitespace input | no crash, no entities | `test_empty_and_whitespace_queries_do_not_crash` |
| 8 | Determinism | identical script → identical snapshot | `test_same_script_yields_identical_snapshots` |
| 9 | Multi-radio complexity | DeltaCam (Wi-Fi+BT) → summary marked `complex` | `test_compose_marks_complex_for_multiradio_product` |
| 10 | Citation recall stability | recall turn never mutates `last_retrieved_docs` | `test_recall_accumulates_docs_across_turns_and_is_stable` |

**Known limitations (honest):** entity recognition is catalog/regex-based, so a
brand-new product code or a claim phrased as a *trailing-question after a declaration*
("…有 Wi-Fi，去美國要測嗎？") can be missed. These are acceptable for a deterministic demo
and degrade *safely* — a missed conflict still gets a doc-grounded RAG answer that
contradicts the false premise, and a missed entity simply falls back to the raw query.

---

## 6. Insights — maintaining long-horizon product context

1. **Distill, don't accumulate.** The durable unit of memory is a *typed slot*
   (product / region / spec / task), not a growing transcript. Slots are what a
   one-word follow-up can refer back to.
2. **Separate "what's in play" from "current focus."** `active_products` is the union
   of everything touched; `active_request_summary` is the single current skeleton.
   Conflating them is what makes a product swap either lose history or fail to reframe.
3. **A follow-up is a *delta*, not a new request.** Modeling turns as deltas over a
   stable skeleton is what preserves Turn-1 context through Turn-N.
4. **Boundedness is a feature, not a constraint.** Caps + dedup + LRU keep latency flat
   and prevent stale context from re-surfacing — context hygiene over context hoarding.
5. **Route on memory, not just the latest sentence.** The biggest real-world win was
   letting the memory *rescue* keyword-router misclassifications; the latest sentence is
   the worst possible sole signal in a multi-turn dialogue.
6. **Where a learned layer fits later:** `classify()` is a pure function with a stable
   signature. A learned scorer could replace the rule body *inside* it while the
   deterministic guards (guarantee / conflict / boundedness) remain as a fail-safe
   envelope — adding adaptivity without surrendering governance.

---

## 7. How to run

```bash
python -m unittest discover -s tests -v      # 51 tests
LLM_MODE=mock streamlit run app.py           # interactive demo
```
