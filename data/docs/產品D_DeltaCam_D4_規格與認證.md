# 產品D：DeltaCam D4 規格與認證提示

> 模擬文件聲明：本文件為內部 AI assistant demo 用模擬資料，不代表真實產品、測試報告、法規意見或認證結論。內容僅可用於示範文件檢索、scoping 與風險邊界；不得對外承諾任何認證通過或不通過結果。

## D1 文件用途與引用方式

本文件描述 `DeltaCam D4` 的產品規格與認證相關注意事項。此產品同時具備 Wi-Fi 6 與 Bluetooth setup mode，並涉及 video streaming 與 mobile-app pairing。它適合用於 demo 中較複雜的多功能產品 scoping。

建議引用粒度：

- `D2 產品概述`
- `D3 關鍵規格表`
- `D4 無線與射頻功能`
- `D5 認證相關注意事項`
- `D7 建議升級人工審查條件`

## D2 產品概述

DeltaCam D4 是一款 wireless camera，透過 Wi-Fi 6 進行 video streaming，並使用 Bluetooth setup mode 進行初始配對。產品以 USB-C 供電，搭配 mobile app 完成配網與設備管理。

DeltaCam D4 的初步 scoping 不應只看 Bluetooth，也不應只看 Wi-Fi。系統應同時考慮 2.4 GHz / 5 GHz Wi-Fi、Bluetooth 2.4 GHz、EMC、產品安全、privacy / security claims、app pairing 相關說明與區域 radio rules。

## D3 關鍵規格表

| 欄位 | 規格 |
| --- | --- |
| 產品代號 | Product D |
| 產品名稱 | DeltaCam D4 |
| 產品類型 | Wireless camera |
| 無線功能 | Wi-Fi 6 + Bluetooth setup mode |
| Wi-Fi 頻段 | 2.4 GHz and 5 GHz Wi-Fi |
| Bluetooth 頻段 | 2.4 GHz |
| Power | USB-C |
| 主要功能 | Video streaming, mobile-app pairing |
| 認證焦點 | Radio, EMC, privacy/security claims, regional radio rules |
| 主要使用情境 | 家用或辦公環境影像串流與遠端管理 |

## D4 無線與射頻功能

DeltaCam D4 的文件支援以下判斷：

- 產品具有 Wi-Fi 6，使用 2.4 GHz 與 5 GHz Wi-Fi。
- 產品具有 Bluetooth setup mode，使用 2.4 GHz。
- Wi-Fi 5 GHz channel plan、DFS、indoor/outdoor restrictions 與區域功率限制可能影響 EU、US、Japan scoping。
- Bluetooth setup mode 即使不是主要資料傳輸功能，也仍可能需要納入 radio review。
- Mobile-app pairing 與 video streaming 可能涉及 privacy / security claims，但本文件不提供法律結論。

## D5 認證相關注意事項

對 EU 初步 scoping，可引用：

- Wi-Fi 與 Bluetooth radio 可能落入 CE / RED radio equipment 相關評估。
- 5 GHz Wi-Fi 需確認支援 channel、輸出功率、DFS / TPC 等區域條件。
- 需確認 EMC、safety、cybersecurity / privacy claim 與 user manual。

對 US 初步 scoping，可引用：

- Wi-Fi 與 Bluetooth radio 通常需考慮 FCC Part 15。
- 需確認 2.4 GHz / 5 GHz radio test report、FCC ID、antenna 設計與最終產品整合條件。
- 若使用既有 module，仍需確認整機整合限制與標示。

對 Japan 初步 scoping，可引用：

- Wi-Fi 與 Bluetooth radio 可能需要 TELEC / MIC-style radio review。
- 5 GHz Wi-Fi 的 channel 與使用限制需要區域化確認。

## D6 已知限制與不明項目

目前文件未提供：

- Wi-Fi channel list、最大輸出功率、DFS support、antenna gain。
- Bluetooth setup mode 的版本、輸出功率與測試模式。
- camera sensor、影像加密、雲端連線、資料保存與 app permission 說明。
- RF / EMC / safety / privacy / security 測試報告。
- 區域版 firmware 是否不同。

系統應避免根據「Wi-Fi 6」單一資訊推論合規結果。若資料不足，應說明需要 RF 工程、法規與資安 / 隱私負責人確認。

## D7 建議升級人工審查條件

以下情境應升級給法規 / RF / security / privacy 負責人：

- 使用者要求確認 EU、US 或 Japan 一定可通過。
- 使用者詢問 5 GHz channel、DFS、輸出功率、firmware lock 或國別限制。
- 使用者詢問影像資料、雲端儲存、app 權限或 privacy claim。
- 文件缺少 radio test mode、antenna、RF report 或 region firmware 資訊。
- 使用者要求對客戶作出上市承諾或認證保證。

