# 產品B：BetaBuds X2 規格與認證提示

> 模擬文件聲明：本文件為內部 AI assistant demo 用模擬資料，不代表真實產品、測試報告、法規意見或認證結論。內容僅可用於示範文件檢索、scoping 與風險邊界；不得對外承諾任何認證通過或不通過結果。

## B1 文件用途與引用方式

本文件描述 `BetaBuds X2` 的產品規格與認證相關注意事項，特別適合用於多輪問答中的產品切換情境。例如使用者先詢問 AlphaBuds X1，接著問「如果是 Product B 呢？」系統應切換到本文件，並指出 BetaBuds X2 不只是 Bluetooth-only，還有 low-power proprietary 2.4 GHz mode。

建議引用粒度：

- `B2 產品概述`
- `B3 關鍵規格表`
- `B4 無線與射頻功能`
- `B5 與 Product A 的 scoping 差異`
- `B7 建議升級人工審查條件`

## B2 產品概述

BetaBuds X2 是一款 Bluetooth earbuds，除了標準 Bluetooth 連線外，另含低功耗 proprietary 2.4 GHz mode，用於 special low-latency mode。此特殊模式使產品相較 AlphaBuds X1 有更高的認證 scoping 複雜度。

系統可以根據本文件說明「Product B 不能直接沿用 Product A 的 Bluetooth-only 結論」，因為 proprietary radio mode 可能需要額外射頻資料、測試模式與區域法規確認。

## B3 關鍵規格表

| 欄位 | 規格 |
| --- | --- |
| 產品代號 | Product B |
| 產品名稱 | BetaBuds X2 |
| 產品類型 | Bluetooth earbuds |
| 無線功能 | Bluetooth + low-power proprietary 2.4 GHz mode |
| Bluetooth version | 5.4 |
| 頻段 | 2.4 GHz ISM band |
| Wi-Fi | 無 |
| 特殊模式 | Low-latency proprietary mode |
| 充電介面 | USB-C charging |
| 電池續航 | 單次充電 10 小時；搭配充電盒 32 小時 |
| 重量 | 52 g with charging case |
| 主要使用情境 | 手機音訊、通話、低延遲音訊模式 |

## B4 無線與射頻功能

BetaBuds X2 的文件支援以下判斷：

- 產品具有 Bluetooth radio，版本為 5.4。
- 產品另有 low-power proprietary 2.4 GHz mode。
- 兩種無線功能都位於 2.4 GHz ISM band，但測試模式、調變方式、頻寬、duty cycle 與輸出功率可能不同。
- 文件未列出 Wi-Fi、UWB、NFC、Zigbee 或 Thread。

系統不得把 proprietary mode 簡化為「只是 Bluetooth」。若區域要求或測試範圍取決於特殊 radio 行為，應提示需要 human review。

## B5 與 Product A 的 scoping 差異

相較 AlphaBuds X1，BetaBuds X2 的主要差異是：

| 比較項 | AlphaBuds X1 | BetaBuds X2 |
| --- | --- | --- |
| Bluetooth version | 5.3 | 5.4 |
| 無線模式 | Bluetooth only | Bluetooth + proprietary 2.4 GHz |
| 認證複雜度 | 適合 Bluetooth-only scoping | 需額外檢查 proprietary mode |
| 典型風險 | 文件不足、模組整合條件 | 特殊模式測試資料不足、區域差異 |

多輪 demo 中，若使用者問「那 Product B 呢？」系統應保留上一輪的區域或認證主題，但切換產品規格。舉例：上一輪是「Product A 出口歐洲」，下一輪「Product B 呢」應回答 EU / CE / RED 脈絡下的 BetaBuds X2 差異。

## B6 已知限制與不明項目

目前文件未提供：

- proprietary 2.4 GHz mode 的調變方式、頻寬、channel plan、duty cycle、輸出功率與測試模式。
- Bluetooth 與 proprietary mode 是否可同時啟動。
- radio chipset、module certification、antenna gain 與 enclosure 設計。
- RF / EMC / safety test report。
- low-latency mode 對包裝、手冊或 app claim 的影響。

若使用者詢問是否可把 BetaBuds X2 視為 AlphaBuds X1 的同類產品直接送審，系統應指出「文件支持相似產品比較，但不支持直接等同認證結論」。

## B7 建議升級人工審查條件

以下情境應升級給法規 / 認證 / RF 工程負責人：

- 使用者要求確認 proprietary mode 在 EU、US 或 Japan 一定可通過。
- 使用者要求省略 proprietary mode 的測試或文件。
- 使用者要求把 Product A 的結果套用到 Product B。
- 使用者詢問最終 test plan、測試模式設定、輸出功率上限或 antenna matching。
- 使用者要求對客戶承諾認證時程、費用或 pass/fail。

