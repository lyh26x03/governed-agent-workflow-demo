# 無線測試與認證 Scoping SOP

> 模擬文件聲明：本文件為內部 AI assistant demo 用模擬資料，不代表真實法規意見、測試報告或認證結論。內容僅可用於示範文件檢索、scoping 與風險邊界；不得對外承諾任何產品一定通過或一定不通過認證。

## S1 文件用途與引用方式

本 SOP 定義 AI assistant 在產品認證問答中的初步 scoping 流程。它適用於 Bluetooth、Wi-Fi、proprietary radio 與 no-radio 產品。系統回答時應引用具體產品文件，並在需要時搭配區域認證矩陣與風險邊界 policy。

建議引用粒度：

- `S2 無線功能辨識流程`
- `S3 初步 scoping 決策`
- `S4 A/B/C/D 範例處理`
- `S5 文件不足時的回答`
- `S6 升級人工審查條件`

## S2 無線功能辨識流程

AI assistant 應依序檢查以下資訊：

1. 產品規格是否明確列出 Bluetooth、Wi-Fi、NFC、UWB、Zigbee、Thread、cellular 或 proprietary radio。
2. 頻段是否明確，例如 2.4 GHz ISM band、5 GHz Wi-Fi 或其他特殊頻段。
3. 無線模式是否只有標準協定，或包含 proprietary / low-latency / pairing-only mode。
4. 是否有 radio module、antenna、output power、channel plan、test mode 或 module certification 資訊。
5. 是否有區域目標，例如 EU、US、Japan。

若產品文件未列出 radio，不應假設有 Bluetooth 或 Wi-Fi。若使用者提供的新資訊與文件衝突，需標示衝突並升級人工審查。

## S3 初步 scoping 決策

| 判斷結果 | 初步 scoping |
| --- | --- |
| Bluetooth only | 檢查 Bluetooth radio、EMC、安全、標示、DoC / FCC ID / TELEC-style 文件與測試報告。 |
| Wi-Fi only or Wi-Fi + Bluetooth | 檢查 2.4 GHz / 5 GHz radio、channel、output power、DFS、EMC、安全、標示與區域 radio rules。 |
| Proprietary 2.4 GHz mode | 除標準協定外，要求調變、頻寬、duty cycle、output power、test mode 與區域適用性。 |
| No radio | 不觸發 Bluetooth / Wi-Fi radio test；優先看 EMC、安全、電源、介面宣稱與標示。 |
| 文件不明或互相衝突 | 不做結論；列出缺口並升級人工審查。 |

系統應避免只依產品名稱判斷。耳機通常有 Bluetooth，但仍需文件支持；hub 通常無 radio，但若文件或 BOM 顯示有無線模組，需重新 scoping。

## S4 A/B/C/D 範例處理

| 產品 | 文件支持的判斷 | 回答重點 |
| --- | --- | --- |
| AlphaBuds X1 | Bluetooth 5.3 only，2.4 GHz ISM，無 Wi-Fi | 適合 Bluetooth-only radio scoping；EU / US / Japan 均需看區域 radio 文件，但不得承諾通過。 |
| BetaBuds X2 | Bluetooth 5.4 + low-power proprietary 2.4 GHz mode | 保留 Bluetooth scoping，同時升高 proprietary mode 的資料需求；不可直接套用 Product A。 |
| GammaHub C1 | No radio module，USB-C hub | 不應要求 Bluetooth 測試；重點轉向 EMC、安全、USB-C PD、HDMI / USB / Ethernet claims。 |
| DeltaCam D4 | Wi-Fi 6 + Bluetooth setup mode | 同時檢查 Wi-Fi 2.4/5 GHz、Bluetooth、EMC、安全、5 GHz channel、privacy/security claims。 |

多輪情境中，使用者若只說「那日本呢」，系統應使用上一輪的 active product，切換 active region 到 Japan。若上一輪剛從 Product A 切到 Product B，則「日本」應套用到 Product B，而不是回到 Product A。

## S5 文件不足時的回答

當文件不足時，AI assistant 應採用以下回答結構：

1. `文件支持的回答`：明確列出目前文件可支持的產品、功能、區域或 scoping。
2. `需要確認的缺口`：列出缺少的測試報告、antenna、output power、channel plan、module grant、label 或 user manual。
3. `下一步`：建議取得文件或升級給 RF / compliance / legal / privacy 負責人。
4. `風險邊界`：不得保證通過，不得對客戶作正式承諾。

範例回答：

「依文件，BetaBuds X2 有 Bluetooth 5.4 與 proprietary 2.4 GHz mode。若目標是 EU，初步需看 RED / CE 相關 radio 與 EMC 文件；但 proprietary mode 的調變、輸出功率與測試模式未提供，因此不能判定是否通過，建議升級 RF / compliance review。」

## S6 升級人工審查條件

以下情境必須升級：

- 使用者要求保證 pass/fail、承諾客戶或替公司作正式聲明。
- 文件缺少 RF test report、EMC report、safety report、antenna、output power 或 channel plan。
- 產品規格與使用者描述、BOM、行銷文案或其他文件互相衝突。
- 產品含 proprietary radio、5 GHz Wi-Fi、camera / video streaming、privacy/security claim 或區域 firmware。
- 使用者詢問法律責任、上市合規、標籤正式文字、合約或出貨承諾。

## S7 回答時的引用要求

AI assistant 應引用：

- 至少一份產品規格文件。
- 有區域問題時引用區域認證矩陣。
- 有流程或不足問題時引用本 SOP。
- 有保證、拒答或升級問題時引用風險邊界 policy。

若使用者詢問「剛才引用哪些文件」，系統應列出最近幾輪真正使用過或檢索到的文件，並避免補列未使用文件。

