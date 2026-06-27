# Product Context Memory Demo Plan

## 1. Why These Files Exist

This repository now includes a simulated internal product and certification corpus for a governed AI assistant demo. The new files let the demo test whether the assistant can preserve product, region, certification scope, cited documents, and refusal boundaries across multiple turns.

The corpus is intentionally focused on 3C / electronics product Q&A rather than OCR, vector database tuning, or external compliance research.

## 2. Simulated Internal Documents

All new corpus files are simulated internal documents. They are not real product specifications, legal advice, regulatory opinions, test reports, certificates, or pass/fail evidence.

The assistant should treat them as retrieval material for demo answers only. Any answer involving certification guarantees, customer commitments, or formal compliance conclusions must refuse or escalate to human review.

## 3. Intended Interview Story

- AML RAG demonstrates deeper RAG engineering and retrieval design.
- `governed-agent-workflow-demo` demonstrates electronics / product workflow context.
- This extension focuses on multi-turn product context preservation, not OCR or vector DB infrastructure.
- The interviewer should see that short follow-up questions are resolved using bounded deterministic context, not by guessing from the latest message alone.

## 4. Target Multi-Turn Demo Script

| Turn | User prompt |
| --- | --- |
| 1 | AlphaBuds X1 如果要出口到歐洲，初步要看哪些認證或文件？ |
| 2 | 如果改成 BetaBuds X2 呢？ |
| 3 | 那日本呢？ |
| 4 | 剛才你參考了哪些文件？ |
| 5 | 可以跟客戶說一定會通過認證嗎？ |
| 6 | 如果 GammaHub C1 沒有無線功能，還要做藍牙測試嗎？ |
| 7 | DeltaCam D4 同時有 Wi-Fi 和 Bluetooth，scoping 應該先看什麼？ |

## 5. Expected Behavior By Turn

| Turn | Expected behavior |
| --- | --- |
| 1 | Set active product to AlphaBuds X1 and active region to EU. Cite Product A, region matrix, and SOP. Explain Bluetooth-only CE / RED scoping without promising results. |
| 2 | Preserve EU as the active region, switch active product to BetaBuds X2, and explain the proprietary 2.4 GHz mode difference from Product A. |
| 3 | Preserve BetaBuds X2 as the active product, switch active region to Japan, and use TELEC / MIC-style review wording. |
| 4 | Recall and list the documents referenced earlier, such as Product A, Product B, region matrix, and SOP. |
| 5 | Refuse or escalate the certification guarantee. Cite the risk-boundary policy and explain that pass/fail requires human confirmation. |
| 6 | Switch active product to GammaHub C1. Do not carry Bluetooth testing forward from the earbuds context. Explain no-radio scoping and EMC / safety focus. |
| 7 | Switch active product to DeltaCam D4. Explain Wi-Fi 6, 2.4 / 5 GHz, Bluetooth setup mode, EMC, regional radio rules, and privacy/security review needs. |

The system should preserve active product / region / certification context, cite relevant documents, and avoid answering from only the latest short follow-up.

## 6. Suggested Future Implementation

Add bounded, deterministic memory fields such as:

- `active_products`
- `active_regions`
- `active_spec_fields`
- `active_request_summary`
- `active_context_deltas`
- `last_retrieved_docs`

Keep the memory layer explicit and inspectable. In this demo stage, do not introduce RL, learned routing, or opaque personalization. The goal is to show dependable workflow context handling with clear retrieval and policy boundaries.

## 7. Corpus Files

The product / certification corpus lives under `data/docs/`:

- `產品A_AlphaBuds_X1_規格與認證.md`
- `產品B_BetaBuds_X2_規格與認證.md`
- `產品C_GammaHub_C1_規格與認證.md`
- `產品D_DeltaCam_D4_規格與認證.md`
- `區域認證矩陣_EU_US_JP.md`
- `無線測試與認證Scoping_SOP.md`
- `產品認證風險邊界Policy.md`
- `FAQ_產品認證與多輪問答.md`

