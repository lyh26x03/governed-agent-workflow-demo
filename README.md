# Gintec Copilot

Gintec Copilot 是一個最小 Streamlit demo 骨架，用來展示認證 scoping、知識庫查詢路由、高風險轉人工與 out-of-scope 防護的介面流程。

目前版本不串接 LLM，也不實作真正的 RAG。頁面只提供六個測試問題按鈕、假回覆區與 log panel，方便先確認 demo 流程與畫面。

## 專案結構

```text
gintec_copilot/
├─ app.py
├─ requirements.txt
├─ README.md
└─ data/
   └─ docs/
      ├─ SOP_藍牙產品歐美認證初步Scoping_v2.md
      ├─ Policy_AI內部使用與對外回覆邊界原則.md
      └─ FAQ_高風險轉人工處理指南.md
```

## 安裝

建議使用 Python 3.10 以上版本。

```bash
pip install -r requirements.txt
```

## 啟動

在專案根目錄執行：

```bash
streamlit run app.py
```

啟動後，瀏覽器通常會開啟：

```text
http://localhost:8501
```

## Demo 功能

- 顯示專案名稱 `Gintec Copilot`
- 顯示六個測試問題按鈕
- 顯示假回覆區
- 顯示 log panel
- 模擬三種路由：`search`、`escalate`、`out_of_scope`

## 目前尚未實作

- LLM 串接
- 真正的 RAG 檢索
- 向量資料庫
- 真正的人工派單或 ticket 建立
- 使用者登入與權限控管
