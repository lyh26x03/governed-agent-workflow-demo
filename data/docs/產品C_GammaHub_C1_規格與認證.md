# 產品C：GammaHub C1 規格與認證提示

> 模擬文件聲明：本文件為內部 AI assistant demo 用模擬資料，不代表真實產品、測試報告、法規意見或認證結論。內容僅可用於示範文件檢索、scoping 與風險邊界；不得對外承諾任何認證通過或不通過結果。

## C1 文件用途與引用方式

本文件描述 `GammaHub C1` 的產品規格與認證相關注意事項。此產品沒有任何 radio module，是 demo corpus 中的 negative-control product。若使用者在多輪對話中從 Bluetooth earbuds 切換到 GammaHub C1，系統應避免延續前文的 Bluetooth 測試假設。

建議引用粒度：

- `C2 產品概述`
- `C3 關鍵規格表`
- `C4 無線與射頻功能`
- `C5 認證相關注意事項`
- `C7 建議升級人工審查條件`

## C2 產品概述

GammaHub C1 是一款 USB-C docking hub，提供 USB-C PD input、HDMI、USB-A 與 Ethernet 連接。文件未列出 Bluetooth、Wi-Fi、NFC、Zigbee、Thread、UWB 或 proprietary radio。

因此，GammaHub C1 的初步認證重點通常不是 Bluetooth radio test，而是 safety、EMC、interface claims、電源輸入條件、資料介面相容性與產品標示。

## C3 關鍵規格表

| 欄位 | 規格 |
| --- | --- |
| 產品代號 | Product C |
| 產品名稱 | GammaHub C1 |
| 產品類型 | USB-C docking hub |
| 無線功能 | 無 |
| Radio module | 無 |
| Ports | USB-C PD input, HDMI, USB-A, Ethernet |
| 電源 | USB-C PD input |
| Bluetooth | 無 |
| Wi-Fi | 無 |
| 認證焦點 | Safety / EMC / interface claims |
| 主要使用情境 | 筆電或平板擴充連接埠 |

## C4 無線與射頻功能

GammaHub C1 的文件支援以下判斷：

- 產品沒有 radio module。
- 文件未提供任何 Bluetooth 或 Wi-Fi 功能。
- 若使用者問「是否需要 Bluetooth 測試」，文件支持回答「依目前文件，沒有 Bluetooth 功能，因此不應把 Bluetooth radio test 作為初步 scoping 項目」。
- 若使用者聲稱 GammaHub C1 有 wireless display、Wi-Fi 或 Bluetooth pairing，該說法與本文件不一致，應升級或要求補充文件。

## C5 認證相關注意事項

GammaHub C1 的 scoping 可優先檢查：

- EMC emission / immunity 與有線介面相關測試。
- USB-C PD input 的電源、安全與溫升資料。
- HDMI、USB-A、Ethernet claim 是否需要相容性或商標授權文件。
- 使用手冊、標籤、警語、線材與包裝資訊。
- 若搭配外部 power adapter，需要確認 adapter 是否另有安全與區域認證。

對 EU、US、Japan 等區域，系統可回答「需依產品類型檢查 EMC、安全與標示要求」，但不可保證不需要任何測試，也不可宣稱一定通過。

## C6 已知限制與不明項目

目前文件未提供：

- EMC test report、safety report、thermal report。
- USB-C PD power profile 與最大輸入功率。
- HDMI 版本、Ethernet 速度、USB 版本與線材規格。
- 是否隨附 power adapter。
- 各區標籤與使用手冊內容。

缺少上述資料時，系統應區分「文件支持無 radio 初步判斷」與「仍需人工確認最終認證範圍」。

## C7 建議升級人工審查條件

以下情境應升級給法規 / 硬體 / compliance 負責人：

- 使用者加入文件未記載的無線功能。
- 使用者要求確認完全不需要任何認證或測試。
- 使用者詢問 USB-C PD 安全、最高功率、溫升或 adapter compliance。
- 使用者要求對客戶承諾上市地區一定符合規範。
- 文件與 BOM、規格書或行銷文案出現衝突。

