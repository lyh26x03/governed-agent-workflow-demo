# 產品A：AlphaBuds X1 規格與認證提示

> 模擬文件聲明：本文件為內部 AI assistant demo 用模擬資料，不代表真實產品、測試報告、法規意見或認證結論。內容僅可用於示範文件檢索、scoping 與風險邊界；不得對外承諾任何認證通過或不通過結果。

## A1 文件用途與引用方式

本文件描述 `AlphaBuds X1` 的產品規格與認證相關注意事項，供 demo 系統回答產品與區域 scoping 問題時引用。若使用者詢問「Product A」、「AlphaBuds」或「Bluetooth earbuds」，可優先檢索本文件，並搭配區域認證矩陣與無線測試 SOP。

建議引用粒度：

- `A2 產品概述`
- `A3 關鍵規格表`
- `A4 無線與射頻功能`
- `A5 認證相關注意事項`
- `A7 建議升級人工審查條件`

## A2 產品概述

AlphaBuds X1 是一款 Bluetooth true wireless earbuds。產品使用 Bluetooth 作為唯一無線連線方式，主要功能包含手機配對、音訊播放、通話與充電盒收納。此產品沒有 Wi-Fi、蜂巢式網路或其他 proprietary radio mode。

AlphaBuds X1 適合用於 EU / US Bluetooth-only 產品的初步認證 scoping 範例。系統可根據文件回答「需要看 Bluetooth radio、EMC、安全與標示文件」等方向，但不可推論已通過 CE、RED、FCC 或其他區域要求。

## A3 關鍵規格表

| 欄位 | 規格 |
| --- | --- |
| 產品代號 | Product A |
| 產品名稱 | AlphaBuds X1 |
| 產品類型 | Bluetooth earbuds |
| 無線功能 | Bluetooth only |
| Bluetooth version | 5.3 |
| 頻段 | 2.4 GHz ISM band |
| Wi-Fi | 無 |
| 充電介面 | USB-C charging |
| 電池續航 | 單次充電 8 小時；搭配充電盒 28 小時 |
| 重量 | 48 g with charging case |
| 主要使用情境 | 手機音訊、通話、短距離藍牙連線 |

## A4 無線與射頻功能

AlphaBuds X1 的文件支援以下判斷：

- 產品具有 Bluetooth radio，版本為 5.3。
- 頻段位於 2.4 GHz ISM band。
- 文件未列出 Wi-Fi、UWB、NFC、Zigbee、Thread 或 proprietary 2.4 GHz mode。
- 產品應依 Bluetooth-only device 進行初步無線 scoping。

若使用者在後續對話中只說「那 Product A 去歐洲呢」或「同一款去美國呢」，系統應保留本產品的 Bluetooth-only 脈絡，並切換區域要求，不應把 Wi-Fi 或 proprietary radio 加入答案。

## A5 認證相關注意事項

對 EU 初步 scoping，可引用：

- Bluetooth radio 可能落入 RED / CE radio equipment 相關評估。
- 需確認 radio test report、EMC、safety、DoC、labeling 與 technical file 的可用性。
- 不能僅憑 Bluetooth version 判定是否通過 EU 要求。

對 US 初步 scoping，可引用：

- 2.4 GHz Bluetooth radio 通常需考慮 FCC Part 15 radio emission 與設備授權流程。
- 需確認是否使用已認證模組、FCC ID、antenna 設計與最終產品整合條件。
- 不能承諾 FCC pass/fail。

對 Japan 初步 scoping，可引用：

- 2.4 GHz Bluetooth radio 可能需要 TELEC / MIC-style radio review。
- 需確認頻率、輸出功率、模組認證與標示條件。

## A6 已知限制與不明項目

目前文件未提供：

- radio chipset 型號與 module certification 狀態。
- antenna gain、天線位置與最終外殼設計。
- RF test report、EMC report、safety report 或 DoC。
- 產品包裝、標籤、使用手冊與區域警語。
- 是否附贈 USB-C charger 或僅提供 cable。

上述資訊不足時，系統應回答「文件可支持初步 scoping，但需要人工確認測試報告與法規文件」。

## A7 建議升級人工審查條件

以下情境應升級給法規 / 認證 / compliance 負責人：

- 使用者要求保證 CE、RED、FCC、TELEC 或其他認證一定通過。
- 使用者要求對客戶作出 pass/fail 承諾。
- 使用者提供與本文件衝突的新規格，例如宣稱 AlphaBuds X1 有 Wi-Fi。
- 詢問最終上市地、標示、DoC、FCC ID 或測試報告是否已完成，但文件中沒有證據。
- 問題涉及法律責任、合約承諾、出貨時程或正式 compliance sign-off。

