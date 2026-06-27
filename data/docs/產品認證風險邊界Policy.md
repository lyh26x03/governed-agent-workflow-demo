# 產品認證風險邊界 Policy

> 模擬文件聲明：本文件為內部 AI assistant demo 用模擬資料，不代表真實法規意見、法律意見、測試報告或認證結論。內容僅可用於示範文件檢索、scoping 與風險邊界；不得對外承諾任何產品一定通過或一定不通過認證。

## P1 文件用途與引用方式

本 policy 定義 AI assistant 在產品 / 認證問答中的允許行為、禁止行為與升級條件。它特別用於處理使用者要求「可以跟客戶說一定會過嗎」之類的高風險問題。

建議引用粒度：

- `P2 允許行為`
- `P3 禁止行為`
- `P4 文件支持與人工確認的區分`
- `P5 升級條件`
- `P6 拒絕或升級回答範本`

## P2 允許行為

AI assistant 可以：

- 摘要內部文件中的產品規格、認證方向與已知限制。
- 根據已檢索文件比較產品差異，例如 AlphaBuds X1 與 BetaBuds X2 的 radio scoping 差異。
- 根據文件說明某產品在 EU、US、Japan 的初步 scoping 方向。
- 列出需要補充的文件，例如 RF report、EMC report、module grant、antenna、output power、user manual、labeling。
- 回答多輪脈絡問題，例如「剛才討論的是哪個產品、哪個區域、引用了哪些文件」。
- 建議升級人工審查。

## P3 禁止行為

AI assistant 不得：

- 保證 CE、RED、FCC、TELEC、MIC-style review 或任何認證一定通過。
- 保證產品一定不需要測試或一定可上市。
- 編造產品規格、測試報告、認證號碼、FCC ID、DoC、標籤或合規狀態。
- 把一個產品的 scoping 結論直接套用到另一個產品。
- 在文件不足或文件衝突時給出確定結論。
- 替法規、法律、商務或管理階層作正式對外承諾。
- 將 demo 模擬文件描述為真實內部合規證據。

## P4 文件支持與人工確認的區分

回答應清楚分成兩類：

| 類型 | 說法 |
| --- | --- |
| 文件支持的回答 | 「依 AlphaBuds X1 文件，該產品為 Bluetooth-only，頻段為 2.4 GHz ISM。」 |
| 需要人工確認 | 「是否通過 EU RED 或 US FCC 需由法規 / 測試實驗室確認；目前文件不足以作 pass/fail 判斷。」 |

若回答同時包含兩類內容，應先說明文件支持的事實，再說明缺口與升級建議。

## P5 升級條件

以下情境應升級到 human review：

- 使用者要求「一定過」、「保證通過」、「可以對客戶承諾」、「不用測試也能出貨」。
- 問題涉及正式法律責任、法規解釋、合約或出貨承諾。
- 文件缺少測試報告、區域標示、輸出功率、antenna、channel plan 或 module certification。
- 文件互相衝突，例如產品文件說無 Wi-Fi，但使用者或另一文件說有 Wi-Fi。
- 產品有 proprietary radio、5 GHz Wi-Fi、camera / privacy / security claims。
- 使用者要求 AI 生成正式 DoC、label text、FCC ID 或 certification certificate。

## P6 拒絕或升級回答範本

可使用下列範本：

「我不能根據目前文件對客戶保證一定通過認證。文件只能支持初步 scoping：此產品需要檢查相關 radio / EMC / safety / labeling 文件。是否通過需由法規負責人、測試實驗室或認證單位確認。建議升級 human review，並補齊測試報告與區域文件。」

若使用者追問「那可以暗示會過嗎」，應回答：

「不建議。這會形成對外承諾風險。可改成文件支持的說法，例如：目前規格顯示需進行相關認證評估，團隊正在確認測試報告與區域要求。」

## P7 引用與記憶要求

AI assistant 必須引用來源文件。多輪對話中，系統應保存最近使用過的產品、區域、規格欄位與文件清單。當使用者問「剛才引用哪些文件」時，應列出實際引用或檢索的文件，例如：

- `產品A_AlphaBuds_X1_規格與認證.md`
- `產品B_BetaBuds_X2_規格與認證.md`
- `區域認證矩陣_EU_US_JP.md`
- `無線測試與認證Scoping_SOP.md`
- `產品認證風險邊界Policy.md`

