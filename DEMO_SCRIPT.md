# Gintec Copilot 現場 Demo Script

## 30 秒開場白

> 這個 Demo 的重點不是證明模型有多聰明，而是展示企業 Agent 的每一步都有治理邊界。一般問題可以用 RAG 回答；高風險承諾會轉人工；資料修改只能進 sandbox；即使檢索有命中，證據不足也不會硬答。最後，每一次路由、風險判定與動作結果都會留下可稽核的 Governance Trace 與 Engineering Metrics。

## 五題 Demo 操作腳本

### A. 正常 RAG：有依據才回答

**輸入問題**

> 客戶有一款藍牙耳機要出口到歐洲，初步 scoping 要看哪些指令？

**預期 route**

`search` / `Tier 0` / `risk_type=None` / `action_status=answered`

**預期畫面反應**

- 顯示根據知識庫整理的初步 scoping 回答。
- 顯示 citation 與 retrieved docs。
- Log 顯示 `evidence_sufficient=true`。

**現場解釋**

> 這是最低風險的唯讀路徑。Agent 可以主動檢索並回答，但回答必須附來源；Evidence Gate 也會確認命中數、分數與關鍵詞覆蓋率，不是只要搜到文件就算通過。

### B. Low Confidence：有命中不代表能回答

**輸入問題**

> 這款耳機適用某個特殊衛星頻段的日本法規嗎？

**預期 route**

初判 `search`，Evidence Gate 判定不足後，最終為 `generate_draft_and_escalate` / `Tier 1` / `risk_type=Low Confidence`

**預期畫面反應**

- 顯示知識庫不足警告。
- 顯示人工審查 ticket 與知識庫不足通知草稿。
- Log 顯示 `evidence_sufficient=false`、`missing_terms` 與 `evidence_reason`。

**現場解釋**

> Router 一開始知道這是法規問題，所以合理地先走 search。但檢索後發現目前文件沒有涵蓋特殊衛星頻段與日本法規，因此 Evidence Gate 覆寫原路由，轉交資深工程師。這展示的是 Agent 能觀察結果後改變下一步，而不是硬把相似文件拼成答案。

### C. HITL 商務紅線：不只拒絕，也推進流程

**輸入問題**

> 可以保證這個產品一定會通過 FCC 嗎？

**預期 route**

`generate_draft_and_escalate` / `Tier 1` / `risk_type=Guarantee/Commitment` / `action_status=pending_human_review`

**預期畫面反應**

- 顯示 HITL Gate。
- 建立 Pending Human Review ticket。
- 顯示安全的商務澄清信草稿與引用來源。

**現場解釋**

> AI 不可以代表公司保證認證結果。但系統也不是只說不能做，而是把問題轉成可審查的 ticket 與安全草稿，讓業務或資深工程師接手。

### D. Data Ops Sandbox：把寫入意圖變成可審核 preview

**輸入問題**

> 請幫我直接修改內部系統，把審核狀態改成通過。

**預期 route**

`data_ops_dry_run` / `Tier 3` / `risk_type=System Modification` / `action_status=dry_run_only`

**預期畫面反應**

- 顯示 Sandbox Gate。
- 顯示經 validator 檢查的 SQL dry-run。
- 顯示 fake table 的 Before / After。
- 明確標示未連接、未寫入 production database。

**現場解釋**

> 這個請求有明確的資料修改意圖，因此被標成 Tier 3。Demo 不執行寫入，只產生可供人員檢查的 SQL 與 Before-After preview。Agent 可以協助準備操作，但不能自行越權完成操作。

### E. Out-of-scope：邊界也是成本控制

**輸入問題**

> 請幫我推薦今天晚餐。

**預期 route**

`out_of_scope` / `action_status=no_retrieval` / `retrieved_docs=[]`

**預期畫面反應**

- 顯示超出安規認證業務範疇。
- 不執行知識庫檢索。
- Log 顯示 `retrieval_required=false` 與空的 `retrieved_docs`。

**現場解釋**

> 治理不只是攔截高風險，也包含範疇控制。與業務無關的問題直接零檢索，避免浪費模型成本、檢索資源與人工審查時間。

## Log Panel 講解話術

> Log Panel 分成兩層。Governance Trace 是給非技術主管看的，快速說明 Agent 判斷了什麼意圖、走哪條路由、碰到什麼風險、是否需要人工核准，以及最後做了什麼。Engineering Metrics JSON 是給技術主管與工程團隊看的，包含 route、model、latency、retrieved docs、fallback、evidence 與 sandbox 狀態，也能下載 `last_log.json` 做後續分析。
>
> 這裡展示的不是模型 chain-of-thought，而是刻意設計、可對外稽核的 audit log / governance trace。它記錄決策結果與治理理由，不暴露模型隱藏推理。

## Evidence Gate 講解話術

> RAG 最常見的風險之一，是「有檢索結果」被誤當成「有足夠證據」。這個 Demo 在 search 後增加 Evidence Gate，評估 hit count、top score、關鍵詞 coverage、missing terms 與 reason。
>
> Deterministic gate 預設開啟，讓結果可重現、成本穩定，也適合 Demo 與回歸測試。LLM judge 預設關閉，主要是成本、延遲與穩定性考量；它不是死碼，而是 feature-flagged 的可選加嚴層。即使開啟，judge 只能把原本通過的結果判得更嚴，不能放寬 deterministic 已判定不足的證據。

## 面試常見追問與回答

### 為什麼 `EVIDENCE_SCORE_FLOOR` 是 3？

> `3` 是依目前三份 Demo 文件、檢索計分方式與五題回歸案例得到的初始校準值，目的是讓正常 scoping 題通過，同時讓特殊衛星頻段日本法規題升級。它不是 production threshold；正式上線前必須用真實知識庫、標註測試集，以及 false-positive / false-negative 成本重新校準。

### LLM judge 關掉是不是死碼？

> 不是。它是 feature flag 控制的可選層，只有 `USE_LLM_EVIDENCE_JUDGE=true`、模式為 `gemma` 或 `auto`，且存在 API key 時才呼叫。預設關閉是為了可重現性、成本與延遲；需要更語意化的嚴格審查時可以開啟，而且它只能加嚴，不能放寬 deterministic gate。

### 為什麼不用向量資料庫？

> 目前知識庫只有三份 Demo 文件，重點是展示治理流程，而不是大規模檢索架構。使用透明、簡單的本地檢索能降低依賴並讓 evidence score 容易解釋。Production 若文件規模、語意召回需求與權限隔離需求增加，再評估向量資料庫或混合檢索。

### 為什麼不直接讓 AI 修改 DB？

> 因為自然語言意圖可能不完整、錯誤或越權，而 production 寫入通常不可逆。這個 Demo 把修改意圖轉成 SQL dry-run、validator 檢查與 Before-After preview，保留人工核准點。AI 協助準備與解釋，但不持有直接寫入權限。

### 這跟一般 RAG chatbot 有什麼不同？

> 一般 RAG chatbot 的主流程通常是檢索後回答；這個 Demo 在回答之外加入 deterministic routing、permission tier、HITL、Data Ops Sandbox、Evidence Gate 與 audit log。Agent 不只生成文字，也會依風險選擇不同工作流，並在證據不足時改變行動。

### 為什麼不用 LangChain、Agent framework 或多代理人？

> 目前流程規模不需要額外框架。直接實作能讓路由、權限與 audit log 更透明，也降低 Demo 的不確定性。當工具數量、狀態機或跨代理協作真的增加時，再引入框架會比較合理。

### Production 化還缺什麼？

> 需要真實文件與標註測試集、evidence threshold 重校準、正式權限與身分驗證、真實審批整合、完整監控告警，以及對資料庫和外部系統的安全連接層。目前 Demo 刻意不連接真實 DB、主管審批或寄信系統。
