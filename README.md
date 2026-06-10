# Gintec Copilot

## 專案定位

Gintec Copilot 是一個以電子產品認證 scoping 為情境的 **Governed Agentic Workflow Demo**。它不是一般聊天機器人；重點是讓 Agent 在協助使用者時，每一步都有明確的路由、權限、風險邊界與可稽核紀錄。

目前 Demo 整合：

- 本地 Markdown RAG 與 citation
- Deterministic route guardrails
- HITL（Human-in-the-Loop）人工審查流程
- Data Ops Sandbox 與 SQL dry-run preview
- Evidence Gate 與 Low Confidence escalation
- Governance Trace 與 Engineering Metrics JSON audit log

## 專案架構

```text
user query
→ route_user_request
→ search / HITL / sandbox / out-of-scope
→ evidence gate（search 路由後）
→ answer / ticket / dry-run preview
→ governance trace + metrics log
```

### 核心路由

| Route | 用途 | 結果 |
|---|---|---|
| `search` | 一般法規、認證、SOP 或 scoping 查詢 | Tier 0 RAG 回答與 citation |
| `generate_draft_and_escalate` | 保證通過、報價、商務承諾、正式合規結論，或 Low Confidence | Tier 1 HITL ticket 與安全草稿 |
| `data_ops_dry_run` | 修改系統、DB 或審核狀態 | Tier 3 意圖攔截、SQL dry-run、Before / After |
| `out_of_scope` | 與認證業務無關的問題 | 零檢索回覆 |

### Evidence Gate

`search` 完成檢索後，Evidence Gate 會評估 `hit_count`、`top_score`、`coverage`、`missing_terms` 與 `evidence_reason`。有檢索結果不代表證據足夠；若證據不足，系統會自動升級為 `Low Confidence` HITL，而不是直接回答。

Deterministic gate 是預設底線。LLM evidence judge 是 feature-flagged 可選層，預設關閉，且只能加嚴 deterministic 判定，不能放寬不足判定。

## 專案結構

```text
gintec_copilot/
├─ app.py
├─ requirements.txt
├─ README.md
├─ DEMO_SCRIPT.md
└─ data/
   └─ docs/
      ├─ SOP_藍牙產品歐美認證初步Scoping_v2.md
      ├─ Policy_AI內部使用與對外回覆邊界原則.md
      └─ FAQ_高風險轉人工處理指南.md
```

## 安裝與啟動

建議使用 Python 3.10 以上版本。

```bash
pip install -r requirements.txt
streamlit run app.py
```

啟動後通常可從 `http://localhost:8501` 開啟 Demo。

Windows 使用者也可雙擊 `start_gintec.bat`，它會啟動 Streamlit 並開啟瀏覽器。

## `.env` 設定

```dotenv
# mock | gemma | auto
LLM_MODE=mock

# LLM_MODE=gemma 或 auto 時使用
GEMINI_API_KEY=
GEMMA_MODEL=gemma-4-26b-a4b-it

# Evidence Gate：預設採 deterministic 評估
USE_LLM_EVIDENCE_JUDGE=false
EVIDENCE_SCORE_FLOOR=3
EVIDENCE_COVERAGE_THRESHOLD=0.5
```

### Demo Mode 用途

- `mock`：完全使用 deterministic 回覆，不需要 API key。適合離線展示、固定流程驗證，以及需要穩定重現結果的 Demo。
- `gemma`：使用 `GEMINI_API_KEY` 與 `GEMMA_MODEL` 呼叫 Gemma。適合展示模型生成效果；呼叫失敗時會保留錯誤資訊，不自動切換成 mock 回覆。
- `auto`：優先呼叫 Gemma，呼叫失敗時依既有 fallback 流程改用 deterministic 回覆。適合網路或 API 可用性不確定、但仍需確保 Demo 可繼續進行的場合。
- 模式由啟動環境的 `LLM_MODE` 決定；UI 的 System Status 僅顯示目前狀態，不提供模式切換。
- `USE_LLM_EVIDENCE_JUDGE=false`：即使 `LLM_MODE=gemma`，Evidence Gate 也不會呼叫 LLM judge。
- Evidence judge 只有在 feature flag 開啟、模式為 `gemma` 或 `auto`，且有 API key 時才可能呼叫。

## Demo 主線劇本

### A. 正常 RAG

**輸入**

> 客戶有一款藍牙耳機要出口到歐洲，初步 scoping 要看哪些指令？

**預期**

`search` / `Tier 0` / `answered` / 有 citation / `evidence_sufficient=true`

### B. Low Confidence

**輸入**

> 這款耳機適用某個特殊衛星頻段的日本法規嗎？

**預期**

初判 `search`，Evidence Gate 判定不足後升級為 `generate_draft_and_escalate` / `Low Confidence`，並顯示知識庫不足通知。

### C. HITL 商務紅線

**輸入**

> 可以保證這個產品一定會通過 FCC 嗎？

**預期**

`generate_draft_and_escalate` / `Tier 1` / HITL ticket / 商務澄清信草稿 / `pending_human_review`

### D. Data Ops Sandbox

**輸入**

> 請幫我直接修改內部系統，把審核狀態改成通過。

**預期**

`data_ops_dry_run` / `Tier 3` / SQL dry-run / Before-After preview / 不寫入 production DB

### E. Out-of-scope

**輸入**

> 請幫我推薦今天晚餐。

**預期**

`out_of_scope` / `no_retrieval` / `retrieved_docs=[]`

完整現場講解話術請見 [DEMO_SCRIPT.md](DEMO_SCRIPT.md)。

## Governance 與 Audit Log

Log Panel 分成兩種視角：

- **Governance Trace**：提供非技術主管閱讀的路由、風險、權限與動作摘要。
- **Engineering Metrics JSON**：提供技術主管追蹤 route、model、latency、retrieval、fallback、evidence 與 sandbox 狀態，可下載為 `last_log.json`。

這些內容是 audit log / governance trace，不是模型的 chain-of-thought。

## 已知限制

- Demo knowledge base 只有三份模擬 Markdown 文件。
- Evidence 門檻是 Demo 初始校準值，不是 production threshold。
- Production 需使用真實文件與測試集重新校準 evidence threshold。
- 目前不主動展示完整多輪 conversation state。
- 目前不連接真實資料庫、主管審批系統或寄信系統。
- Data Ops Sandbox 只對 fake table 產生 dry-run preview。
- Demo 未使用向量資料庫；目前檢索方式是為了保持流程透明、依賴精簡與展示穩定。
