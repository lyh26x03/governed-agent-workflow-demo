# FAQ：產品認證與多輪問答範例

> 模擬文件聲明：本文件為內部 AI assistant demo 用模擬資料，不代表真實法規意見、測試報告、客戶回覆或認證結論。內容僅可用於示範文件檢索、scoping 與風險邊界；不得對外承諾任何產品一定通過或一定不通過認證。

## F1 文件用途與引用方式

本 FAQ 提供多輪 demo 友善的問答樣式，協助測試 active product、active region、last retrieved docs 與風險邊界。實際回答仍應引用產品規格、區域矩陣、SOP 與 policy。

建議引用粒度：

- `F2 Product A exported to Europe`
- `F3 What if it is Product B`
- `F4 What about Japan`
- `F5 Which documents were referenced earlier`
- `F6 Can we tell the customer it will definitely pass`
- `F7 Product C has no wireless module`
- `F8 Product D has Wi-Fi and Bluetooth`

## F2 Product A exported to Europe

**問：AlphaBuds X1 如果要出口到歐洲，初步要看哪些認證或文件？**

答：依 AlphaBuds X1 文件，該產品是 Bluetooth-only earbuds，Bluetooth version 5.3，使用 2.4 GHz ISM band，沒有 Wi-Fi。若目標是 EU，初步應看 CE / RED 相關 radio equipment scoping，並確認 radio test report、EMC、safety、DoC、labeling、user manual 與 technical file。此回答只能作初步 scoping，不代表認證結果。

## F3 What if it is Product B

**問：如果改成 BetaBuds X2 呢？**

答：若上一輪區域仍是 EU，系統應保留 EU 脈絡並切換產品到 BetaBuds X2。BetaBuds X2 有 Bluetooth 5.4，另有 low-power proprietary 2.4 GHz mode。相較 AlphaBuds X1，Product B 需要額外確認 proprietary mode 的調變、頻寬、輸出功率、test mode 與區域適用性，不能直接套用 Product A 的 Bluetooth-only scoping。

## F4 What about Japan

**問：那日本呢？**

答：若上一輪 active product 是 BetaBuds X2，系統應保留 Product B，將 active region 切換到 Japan。依區域矩陣，日本可用 TELEC / MIC-style radio review 的 wording 做初步說明。BetaBuds X2 的 Bluetooth 與 proprietary 2.4 GHz mode 都需確認 radio 資料；尤其 proprietary mode 文件不足時，應升級人工審查。

## F5 Which documents were referenced earlier

**問：剛才你參考了哪些文件？**

答：系統應列出實際檢索或引用過的文件，而不是重新猜測。範例：

- `產品A_AlphaBuds_X1_規格與認證.md`
- `產品B_BetaBuds_X2_規格與認證.md`
- `區域認證矩陣_EU_US_JP.md`
- `無線測試與認證Scoping_SOP.md`

若第五輪涉及保證或拒答，也應加入 `產品認證風險邊界Policy.md`。

## F6 Can we tell the customer it will definitely pass

**問：可以跟客戶說一定會通過認證嗎？**

答：不可以。AI assistant 不得對客戶保證任何產品一定通過 CE、RED、FCC、TELEC 或其他認證。可改成：「依目前內部文件，可支持初步 scoping；是否通過需由法規負責人、測試實驗室或認證單位確認。」此類問題應標示為 high risk 並升級 human review。

## F7 Product C has no wireless module

**問：GammaHub C1 沒有無線模組，還需要 Bluetooth testing 嗎？**

答：依 GammaHub C1 文件，該產品是 USB-C docking hub，沒有 radio module，未列 Bluetooth 或 Wi-Fi。因此初步不應把 Bluetooth radio test 作為 scoping 項目。仍需檢查 EMC、安全、USB-C PD、HDMI / USB / Ethernet interface claims、labeling 與手冊。若有其他文件聲稱產品有 wireless feature，需升級人工審查。

## F8 Product D has Wi-Fi and Bluetooth

**問：DeltaCam D4 同時有 Wi-Fi 和 Bluetooth，scoping 應該先看什麼？**

答：依 DeltaCam D4 文件，產品有 Wi-Fi 6，使用 2.4 GHz 與 5 GHz Wi-Fi，另有 Bluetooth setup mode。初步應先確認 radio 功能清單、頻段、channel plan、output power、antenna、test mode 與區域目標，再看 EMC、安全、labeling、manual、privacy/security claims。5 GHz Wi-Fi、camera video streaming 與 mobile-app pairing 都會增加 review 複雜度。

## F9 Demo 回答風格提醒

回答應保持三段式：

1. 文件支持的事實。
2. 區域或產品 scoping。
3. 文件缺口、不得保證與升級建議。

若問題是簡短 follow-up，系統應使用 conversation memory 補足產品與區域，而不是只根據最新一句話回答。

