# 區域認證矩陣：EU / US / JP

> 模擬文件聲明：本文件為內部 AI assistant demo 用模擬資料，不代表真實法規意見、測試報告或認證結論。內容僅可用於示範文件檢索、scoping 與風險邊界；不得對外承諾任何產品一定通過或一定不通過認證。

## M1 文件用途與引用方式

本矩陣用於協助 AI assistant 對產品與區域進行初步 scoping。系統應搭配產品規格文件、無線測試 SOP 與風險邊界 policy 一起引用。此文件只能支持「需要查看哪些認證方向或文件」的回答，不能支持 pass/fail 結論。

建議引用粒度：

- `M2 區域矩陣總覽`
- `M3 產品類型範例`
- `M4 不可承諾事項`
- `M5 文件不足時的回答方式`

## M2 區域矩陣總覽

| 區域 | 初步認證方向 | Radio / EMC 主要考量 | 文件檢查重點 |
| --- | --- | --- | --- |
| EU | CE / RED | Radio equipment、EMC、safety、DoC、technical file | 頻段、輸出功率、radio test report、EMC report、labeling、user manual |
| US | FCC Part 15 | Intentional radiator / unintentional radiator、radio emission、整機整合條件 | FCC ID、module grant、antenna、test report、labeling、user manual |
| Japan | TELEC / MIC-style radio review | 2.4 GHz / 5 GHz radio、channel、輸出功率、標示 | radio module 資料、測試報告、技術基準適合、標籤與手冊 |

此矩陣為 demo 用初步判斷，不取代正式法規判讀。實際產品需由法規、RF、測試實驗室或認證單位確認。

## M3 產品類型範例

| 產品情境 | 對應範例 | 初步 scoping |
| --- | --- | --- |
| Bluetooth-only product | AlphaBuds X1 | 先看 Bluetooth radio、EMC、安全、標示與區域文件；EU 可連到 CE / RED，US 可連到 FCC Part 15，Japan 可連到 TELEC / MIC-style review。 |
| Bluetooth + proprietary 2.4 GHz | BetaBuds X2 | 除 Bluetooth 外，需額外確認 proprietary mode 的調變、頻寬、輸出功率、測試模式與區域適用性。 |
| No-radio product | GammaHub C1 | 不應自動觸發 Bluetooth / Wi-Fi radio test；優先看 EMC、安全、介面宣稱與電源相關要求。 |
| Wi-Fi + Bluetooth product | DeltaCam D4 | 同時檢查 Wi-Fi 2.4 GHz / 5 GHz、Bluetooth、EMC、安全、標示、區域 channel 與 privacy/security claims。 |
| Special-frequency or unclear radio product | 非本批產品或規格不明產品 | 若文件未列頻段、輸出功率或 radio type，應要求補充資料或升級人工審查。 |

## M4 不可承諾事項

AI assistant 必須避免以下說法：

- 「一定可以通過 CE / RED / FCC / TELEC。」
- 「不需要測試也能上市。」
- 「只要有 Bluetooth version，就代表已符合區域要求。」
- 「Product A 過了，所以 Product B 也一定過。」
- 「文件沒有寫風險，所以沒有風險。」

可接受的回答方式是：

- 「依目前文件，可做初步 scoping。」
- 「此產品看起來需要檢查下列文件與測試項目。」
- 「是否通過需由實驗室、法規或認證負責人確認。」
- 「文件不足，建議升級人工審查。」

## M5 文件不足時的回答方式

當文件缺少關鍵資料時，系統應明確標示限制：

| 缺少資料 | 建議回答 |
| --- | --- |
| radio test report | 「目前文件不足以判定測試結果，只能列出可能需要的測試方向。」 |
| antenna / output power | 「需由 RF 或認證負責人確認天線與輸出功率是否符合區域條件。」 |
| module certification | 「需確認是否使用已認證模組，以及整機整合條件是否滿足。」 |
| region-specific manual / label | 「需確認標示、警語、DoC 或 FCC ID 等區域文件。」 |
| product spec conflict | 「文件互相衝突，不能直接回答；建議升級人工審查。」 |

## M6 與多輪記憶 demo 的關係

此矩陣讓 demo 可以測試產品與區域的上下文保留：

- 使用者先問 AlphaBuds X1 出口 EU，系統應結合 Product A 與 EU。
- 使用者接著問「那 Product B 呢」，系統應保留 EU，切換產品到 BetaBuds X2。
- 使用者再問「Japan 呢」，系統應保留 Product B，切換區域到 Japan。
- 使用者問「剛才參考哪些文件」，系統應回憶最近檢索與引用的產品文件、矩陣與 SOP。
- 使用者要求保證通過時，系統應引用風險邊界並拒絕或升級。

