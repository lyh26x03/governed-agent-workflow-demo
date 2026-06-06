from __future__ import annotations

import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import streamlit as st
from pydantic import BaseModel, Field


PROJECT_NAME = "Gintec Copilot"
DEMO_CAPTION = "Demo v2.1 - deterministic routing、本地 RAG、HITL 與 Data Ops Sandbox。"
MOCK_REPLY = "這是 Task 1 的假回覆：目前尚未接上 RAG / LLM。"
DOCS_DIR = Path("data") / "docs"
DEFAULT_LLM_MODE = "mock"
DEFAULT_GEMMA_MODEL = "gemma-4-26b-a4b-it"
DATA_OPS_TABLE_NAME = "demo_case_status"
FAKE_SANDBOX_ROWS = [
    {
        "case_id": "DEMO-001",
        "customer_name": "Alpha Electronics",
        "product_type": "Bluetooth Headset",
        "review_status": "審核中",
        "last_updated_by": "engineer_a",
    },
    {
        "case_id": "DEMO-002",
        "customer_name": "Beta Devices",
        "product_type": "Wi-Fi Module",
        "review_status": "待補件",
        "last_updated_by": "engineer_b",
    },
]

TEST_QUESTIONS = [
    "客戶有一款藍牙耳機要出口到歐洲，初步 scoping 要看哪些指令？",
    "可以保證這個產品一定會通過 FCC 嗎？",
    "請幫我直接修改內部系統，把審核狀態改成通過。",
    "請幫我推薦今天晚餐。",
    "這款耳機適用某個特殊衛星頻段的日本法規嗎？",
    "那如果是去美國呢？",
]

MOCK_LOG = {
    "request_id": None,
    "timestamp": None,
    "route_status": "mock",
    "intent_summary": "尚無請求",
    "selected_tool": "none",
    "permission_tier": "N/A",
    "risk_type": "None",
    "risk_reason": "尚未執行路由",
    "llm_mode": DEFAULT_LLM_MODE,
    "model": "mock",
    "fallback_used": False,
    "retrieved_docs": [],
    "approval_required": False,
    "latency_ms": 0,
    "error": None,
    "action_status": "idle",
    "ticket_id": None,
    "draft_type": None,
    "sandbox_id": None,
    "current_action_tier": None,
    "sql_validation_status": "N/A",
    "approval_queue": None,
}

COMMON_KEYWORDS = [
    "EMC",
    "樣品",
    "資訊",
    "藍牙",
    "歐洲",
    "歐盟",
    "美國",
    "日本",
    "法規",
    "耳機",
    "RED",
    "FCC",
    "Part 15",
    "CE",
    "測試",
    "認證",
    "scoping",
]


class RouteDecision(BaseModel):
    route_status: Literal[
        "search",
        "generate_draft_and_escalate",
        "data_ops_dry_run",
        "out_of_scope",
    ]
    intent_summary: str
    selected_tool: str
    permission_tier: Literal["Tier 0", "Tier 1", "Tier 3", "N/A"]
    risk_type: Literal[
        "None",
        "Guarantee/Commitment",
        "Commercial/Pricing",
        "System Modification",
        "Out of Scope",
        "Low Confidence",
    ]
    risk_reason: str
    retrieval_required: bool
    approval_required: bool
    confidence: float = Field(ge=0.0, le=1.0)


class HumanReviewTicket(BaseModel):
    ticket_id: str
    route_status: Literal["generate_draft_and_escalate"]
    permission_tier: Literal["Tier 1"]
    risk_type: str
    risk_reason: str
    intent_summary: str
    suggested_owner: str
    original_query: str
    draft_type: Literal["商務澄清信草稿"]
    draft_preview: str
    retrieved_docs: list[dict[str, Any]]
    approval_required: bool
    status: Literal["Pending Human Review"]


class DataOpsSandboxResult(BaseModel):
    sandbox_id: str
    route_status: Literal["data_ops_dry_run"]
    permission_tier: Literal["Tier 3"]
    current_action_tier: Literal["Tier 1"]
    risk_type: Literal["System Modification"]
    risk_reason: str
    generated_sql: str
    sql_validation_status: Literal["passed", "blocked"]
    before_rows: list[dict[str, Any]]
    after_rows: list[dict[str, Any]]
    approval_required: bool
    approval_queue: Literal["Supervisor Approval Queue"]
    action_status: Literal["Dry-run only"]


def initialize_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_log" not in st.session_state:
        st.session_state.last_log = MOCK_LOG.copy()


def route_user_request(user_query: str, conversation_state: dict[str, Any] | None = None) -> RouteDecision:
    normalized_query = re.sub(r"\s+", "", user_query).lower()
    conversation_state = conversation_state or {}
    previous_user_query = str(conversation_state.get("previous_user_query", "")).strip()

    system_modification_terms = [
        "修改內部系統",
        "修改系統",
        "修改db",
        "修改資料庫",
        "更新資料庫",
        "寫入資料庫",
        "審核狀態改成通過",
        "狀態改成通過",
        "直接改成通過",
    ]
    guarantee_terms = ["保證", "一定會通過", "一定通過", "承諾通過", "對外承諾", "正式承諾"]
    commercial_terms = ["正式報價", "報價單", "承諾交期", "承諾兩週", "商務承諾"]
    compliance_conclusion_terms = ["合規結論", "正式合規", "確認合法", "保證合法", "一定符合"]
    out_of_scope_terms = [
        "晚餐",
        "午餐",
        "早餐",
        "宵夜",
        "推薦餐廳",
        "閒聊",
        "講笑話",
        "天氣",
        "電影推薦",
    ]
    certification_domain_terms = [
        "安規",
        "法規",
        "認證",
        "合規",
        "sop",
        "scoping",
        "fcc",
        "ce",
        "red",
        "emc",
        "藍牙",
        "無線",
        "頻段",
        "衛星",
        "歐盟",
        "歐洲",
        "美國",
        "日本",
        "出口",
        "指令",
        "測試",
        "樣品",
    ]

    if any(term in normalized_query for term in system_modification_terms):
        return RouteDecision(
            route_status="data_ops_dry_run",
            intent_summary="要求修改內部系統、資料庫或審核狀態",
            selected_tool="data_ops_sandbox_skill",
            permission_tier="Tier 3",
            risk_type="System Modification",
            risk_reason="請求涉及內部系統或資料狀態修改，只能進入 sandbox dry-run 流程。",
            retrieval_required=False,
            approval_required=True,
            confidence=0.99,
        )

    if any(term in normalized_query for term in guarantee_terms):
        return RouteDecision(
            route_status="generate_draft_and_escalate",
            intent_summary="要求保證通過、正式承諾或對外承諾",
            selected_tool="generate_draft_and_escalate_skill",
            permission_tier="Tier 1",
            risk_type="Guarantee/Commitment",
            risk_reason="AI 不可直接保證認證結果或代表公司做出正式承諾。",
            retrieval_required=True,
            approval_required=True,
            confidence=0.99,
        )

    if any(term in normalized_query for term in commercial_terms):
        return RouteDecision(
            route_status="generate_draft_and_escalate",
            intent_summary="要求正式報價、交期或商務承諾",
            selected_tool="generate_draft_and_escalate_skill",
            permission_tier="Tier 1",
            risk_type="Commercial/Pricing",
            risk_reason="正式報價與商務承諾需要人工審核。",
            retrieval_required=True,
            approval_required=True,
            confidence=0.98,
        )

    if any(term in normalized_query for term in compliance_conclusion_terms):
        return RouteDecision(
            route_status="generate_draft_and_escalate",
            intent_summary="要求正式合規或法律結論",
            selected_tool="generate_draft_and_escalate_skill",
            permission_tier="Tier 1",
            risk_type="Guarantee/Commitment",
            risk_reason="正式合規結論不可由 AI 直接對外確認。",
            retrieval_required=True,
            approval_required=True,
            confidence=0.95,
        )

    if any(term in normalized_query for term in out_of_scope_terms):
        return RouteDecision(
            route_status="out_of_scope",
            intent_summary="非安規認證業務範疇的生活或閒聊問題",
            selected_tool="out_of_scope_guardrail",
            permission_tier="N/A",
            risk_type="Out of Scope",
            risk_reason="問題與安規、認證、法規或內部流程無關。",
            retrieval_required=False,
            approval_required=False,
            confidence=0.99,
        )

    if not any(term in normalized_query for term in certification_domain_terms):
        return RouteDecision(
            route_status="out_of_scope",
            intent_summary="未偵測到安規、認證、法規或 scoping 業務意圖",
            selected_tool="out_of_scope_guardrail",
            permission_tier="N/A",
            risk_type="Out of Scope",
            risk_reason="問題沒有安規認證領域訊號，因此不執行知識庫檢索。",
            retrieval_required=False,
            approval_required=False,
            confidence=0.85,
        )

    intent_summary = "一般法規、認證、SOP 或 scoping 知識查詢"
    if previous_user_query and re.search(r"^(那|如果|那如果|改成|換成)", user_query.strip()):
        intent_summary = f"延續前一題「{build_preview(previous_user_query, 40)}」的法規或 scoping 查詢"

    return RouteDecision(
        route_status="search",
        intent_summary=intent_summary,
        selected_tool="search_knowledge_base_skill",
        permission_tier="Tier 0",
        risk_type="None",
        risk_reason="可透過本地知識庫提供初步資訊，不涉及承諾或系統修改。",
        retrieval_required=True,
        approval_required=False,
        confidence=0.85,
    )


def get_conversation_state() -> dict[str, Any]:
    previous_user_queries = [
        message["content"]
        for message in st.session_state.messages
        if message.get("role") == "user"
    ]
    return {
        "previous_user_query": previous_user_queries[-1] if previous_user_queries else "",
        "recent_user_queries": previous_user_queries[-3:],
    }


def extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("# "):
            return stripped_line.removeprefix("# ").strip() or fallback
    return fallback


def build_preview(content: str, limit: int = 120) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def clean_markdown_text(content: str) -> str:
    cleaned_lines: list[str] = []
    for line in content.splitlines():
        stripped_line = re.sub(r"^\s*#{1,6}\s*", "", line).strip()
        if stripped_line:
            cleaned_lines.append(stripped_line)

    normalized = " ".join(cleaned_lines)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def load_markdown_documents(docs_dir: Path = DOCS_DIR) -> tuple[list[dict[str, Any]], str | None]:
    if not docs_dir.exists():
        return [], f"找不到知識庫資料夾：{docs_dir.as_posix()}"

    if not docs_dir.is_dir():
        return [], f"知識庫路徑不是資料夾：{docs_dir.as_posix()}"

    markdown_paths = sorted(docs_dir.glob("*.md"))
    if not markdown_paths:
        return [], f"知識庫資料夾中沒有 Markdown 文件：{docs_dir.as_posix()}"

    documents: list[dict[str, Any]] = []
    for markdown_path in markdown_paths:
        content = markdown_path.read_text(encoding="utf-8-sig")
        doc_id = markdown_path.stem
        documents.append(
            {
                "doc_id": doc_id,
                "filename": markdown_path.name,
                "path": markdown_path.as_posix(),
                "title": extract_title(content, doc_id),
                "content": content,
                "preview": build_preview(content),
            }
        )

    return documents, None


def split_markdown_sections(document: dict[str, Any]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_title = document["title"]
    current_lines: list[str] = []

    for line in document["content"].splitlines():
        stripped_line = line.strip()
        is_heading = re.match(r"^#{1,3}\s+", stripped_line) is not None

        if is_heading:
            if current_lines:
                chunks.append(build_chunk(document, current_title, current_lines))
            current_title = re.sub(r"^#{1,3}\s+", "", stripped_line).strip() or document["title"]
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        chunks.append(build_chunk(document, current_title, current_lines))

    return chunks


def build_chunk(document: dict[str, Any], section_title: str, lines: list[str]) -> dict[str, Any]:
    raw_content = "\n".join(lines).strip()
    body_lines = [line for line in lines if re.match(r"^\s*#{1,6}\s+", line) is None]
    clean_content = clean_markdown_text("\n".join(body_lines))
    if not clean_content:
        clean_content = clean_markdown_text(raw_content)
    section_match = re.match(r"^(\d+(?:\.\d+)*)", section_title)
    section_ref = section_match.group(1) if section_match else section_title

    return {
        "doc_id": document["doc_id"],
        "filename": document["filename"],
        "title": document["title"],
        "section_title": section_title,
        "raw_content": raw_content,
        "clean_content": clean_content,
        "content": raw_content,
        "score": 0,
        "citation": f"[引用: {document['filename']} §{section_ref}]",
    }


def extract_query_terms(query: str) -> list[str]:
    lower_query = query.lower()
    terms = [term for term in re.split(r"\s+", lower_query) if term]

    for keyword in COMMON_KEYWORDS:
        if keyword.lower() in lower_query:
            terms.append(keyword.lower())

    if "資訊" in query:
        terms.append("資料")

    return sorted(set(terms), key=len, reverse=True)


def score_chunk(query_terms: list[str], chunk: dict[str, Any]) -> int:
    searchable_title = f"{chunk['title']} {chunk['section_title']}".lower()
    searchable_content = chunk["clean_content"].lower()
    score = 0

    for term in query_terms:
        if term in searchable_title:
            score += 3
        if term in searchable_content:
            term_weight = 5 if term in {"emc", "fcc", "red", "ce", "part 15"} else 1
            score += term_weight + searchable_content.count(term)

    return score


def search_knowledge_base(query: str, documents: list[dict[str, Any]], top_k: int = 3) -> list[dict[str, Any]]:
    query_terms = extract_query_terms(query)
    if not query_terms:
        return []

    results: list[dict[str, Any]] = []
    for document in documents:
        for chunk in split_markdown_sections(document):
            score = score_chunk(query_terms, chunk)
            if score > 0:
                chunk["score"] = score
                results.append(chunk)

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


def format_search_response(results: list[dict[str, Any]]) -> str:
    if not results:
        return "目前知識庫沒有找到足夠相關的段落，建議補充文件或轉交人工確認。"

    response_lines = ["我目前找到以下可能相關段落："]
    for index, result in enumerate(results, start=1):
        preview = build_preview(result["content"], limit=150)
        response_lines.extend(
            [
                "",
                f"{index}. 文件名稱：{result['filename']}",
                f"   段落：{result['section_title']}",
                f"   分數：{result['score']}",
                f"   摘要：{preview}",
                f"   {result['citation']}",
            ]
        )

    return "\n".join(response_lines)


def load_llm_config() -> dict[str, str]:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass

    llm_mode = os.getenv("LLM_MODE", DEFAULT_LLM_MODE).strip().lower()
    if llm_mode not in {"mock", "gemma", "auto"}:
        llm_mode = DEFAULT_LLM_MODE

    return {
        "llm_mode": llm_mode,
        "gemini_api_key": os.getenv("GEMINI_API_KEY", "").strip(),
        "gemma_model": os.getenv("GEMMA_MODEL", DEFAULT_GEMMA_MODEL).strip() or DEFAULT_GEMMA_MODEL,
    }


def generate_mock_answer(search_results: list[dict[str, Any]]) -> str:
    if not search_results:
        return "目前知識庫不足，無法可靠回答。"

    return "\n".join(build_answer_point(result) for result in search_results[:3])


def clean_answer_line(text: str) -> str:
    stripped = text.strip()
    stripped = re.sub(r"^\s*#{1,6}\s*", "", stripped)
    stripped = re.sub(r"^\s*[-*•]\s*", "", stripped)
    stripped = re.sub(r"^\s*\d+[.)]\s*", "", stripped)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return stripped


def build_answer_point(result: dict[str, Any]) -> str:
    raw_section_title = clean_answer_line(result["section_title"])
    section_title = re.sub(r"^\d+(?:\.\d+)*\s*", "", raw_section_title).strip() or raw_section_title
    content = result["clean_content"].replace("|", " ").replace("`", "")
    content = re.sub(rf"^{re.escape(raw_section_title)}\s*", "", content).strip()
    content = re.sub(rf"^{re.escape(section_title)}\s*", "", content).strip()

    content = re.sub(r"\s*-\s*", "；", content)
    content = re.sub(r"\s+", " ", content).strip("：:；， ")
    snippet = build_preview(content, limit=78)
    if not snippet:
        snippet = section_title

    return f"- {section_title}：{snippet} {result['citation']}"


def format_bulleted_answer(lines: list[str], search_results: list[dict[str, Any]]) -> str:
    if not search_results:
        return "目前知識庫不足，無法可靠回答。"

    insufficient_markers = ["目前知識庫不足，無法可靠回答", "資料不足", "無法可靠回答"]
    joined_lines = " ".join(lines)
    if any(marker in joined_lines for marker in insufficient_markers):
        return "目前知識庫不足，無法可靠回答。"

    formatted_lines: list[str] = []
    for index, raw_line in enumerate(lines[:3]):
        clean_line = clean_answer_line(raw_line)
        if not clean_line:
            continue

        limited_line = build_preview(clean_line, limit=110)
        formatted_lines.append(f"- {limited_line} {search_results[index]['citation']}")

    if not formatted_lines:
        return "目前知識庫不足，無法可靠回答。"

    return "\n".join(formatted_lines)


def build_gemma_prompt(user_query: str, search_results: list[dict[str, Any]]) -> str:
    retrieved_context = []
    for index, result in enumerate(search_results[:3], start=1):
        retrieved_context.append(
            "\n".join(
                [
                    f"Result {index}",
                    f"filename: {result['filename']}",
                    f"section_title: {result['section_title']}",
                    f"citation: {result['citation']}",
                    "clean_content:",
                    result["clean_content"],
                ]
            )
        )

    context_text = "\n\n---\n\n".join(retrieved_context) if retrieved_context else "無檢索結果。"

    return f"""你是企業內部安規認證知識助手。
只能根據提供的「檢索結果」回答。
使用繁體中文。
回答最多 3 個 bullet。
每個 bullet 最多 2 行。
不要使用 #、##、### Markdown heading。
不要直接貼整段原文。
不可補充檢索結果以外的知識。
不可說「一定通過」「保證合法」「可直接對客戶承諾」。
若檢索結果不足，必須明確說「目前知識庫不足，無法可靠回答」。
請只輸出 bullet 內容本身，不要自行補 citation，我會在程式端附上 citation。

使用者問題：
{user_query}

檢索結果：
{context_text}
"""


def call_gemma(user_query: str, search_results: list[dict[str, Any]], api_key: str, model: str) -> str:
    if not api_key:
        raise ValueError("缺少 GEMINI_API_KEY，無法呼叫 Gemma。")

    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=build_gemma_prompt(user_query, search_results),
    )

    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Gemma 回應為空。")

    candidate_lines = [line for line in text.splitlines() if clean_answer_line(line)]
    return format_bulleted_answer(candidate_lines, search_results)


def build_human_review_draft_template(user_query: str) -> str:
    return """主旨：認證評估資訊確認與後續安排

您好，

感謝您提出產品認證結果與後續商務安排的確認需求。

為提供適當的初步評估與後續商務安排，我們需要由認證工程與業務窗口共同確認產品條件、適用規範及測試範圍。現階段內容僅作為資訊蒐集與人工審查草稿，不代表最終認證、報價、交期或正式合規結論。

煩請協助補充：
1. 產品型號
2. 無線模組資訊
3. 目標市場
4. 是否已有前測或測試報告
5. 樣品可提供時間

收到完整資訊後，我們將安排相關窗口進一步確認評估範圍與後續流程。

謝謝。"""


def build_human_review_gemma_prompt(user_query: str, search_results: list[dict[str, Any]]) -> str:
    context_lines = []
    for result in search_results[:5]:
        context_lines.append(
            f"- {result['filename']} / {result['section_title']}: {build_preview(result['clean_content'], 260)}"
        )

    return f"""你是企業安規認證公司的內部商務助理。請產生一封繁體中文「商務澄清信草稿」，供人工審查，不可直接回答使用者的高風險要求。

安全規則：
- 不得保證認證結果或產品通過。
- 不得提供正式報價。
- 不得承諾交期。
- 不得做出法律或正式合規結論。
- 明確說明草稿仍需人工審查。
- 必須要求補充：產品型號、無線模組資訊、目標市場、是否已有前測或測試報告、樣品可提供時間。
- 不要自行加入 citation。

使用者原始問題：
{user_query}

內部參考資料：
{chr(10).join(context_lines)}
"""


def validate_human_review_draft(draft: str) -> None:
    required_items = ["產品型號", "無線模組資訊", "目標市場", "前測或測試報告", "樣品可提供時間"]
    prohibited_patterns = [
        r"保證.{0,8}通過",
        r"一定.{0,8}通過",
        r"正式報價.{0,20}(為|是|：|:|\d)",
        r"承諾.{0,12}(交期|完成|通過)",
        r"(確認|判定).{0,8}(合法|合規)",
    ]

    if not draft.strip():
        raise ValueError("Gemma 商務澄清信草稿為空。")
    if any(item not in draft for item in required_items):
        raise ValueError("Gemma 草稿缺少必要的資訊蒐集項目。")
    if any(re.search(pattern, draft, flags=re.IGNORECASE) for pattern in prohibited_patterns):
        raise ValueError("Gemma 草稿未通過高風險承諾安全檢查。")


def call_gemma_for_human_review_draft(
    user_query: str,
    search_results: list[dict[str, Any]],
    api_key: str,
    model: str,
) -> str:
    if not api_key:
        raise ValueError("缺少 GEMINI_API_KEY，無法呼叫 Gemma。")

    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=build_human_review_gemma_prompt(user_query, search_results),
    )
    draft = getattr(response, "text", None) or ""
    validate_human_review_draft(draft)
    return draft.strip()


def prioritize_human_review_results(results: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    def priority(result: dict[str, Any]) -> tuple[int, int]:
        filename = result["filename"].lower()
        if filename.startswith("policy"):
            source_priority = 0
        elif filename.startswith("faq"):
            source_priority = 1
        elif filename.startswith("sop"):
            source_priority = 2
        else:
            source_priority = 3
        return source_priority, -result["score"]

    return sorted(results, key=priority)[:limit]


def suggest_human_review_owner(risk_type: str) -> str:
    if risk_type == "Commercial/Pricing":
        return "業務主管"
    if risk_type == "Low Confidence":
        return "認證工程師"
    return "認證工程師與業務主管"


def generate_draft_and_escalate_skill(
    user_query: str,
    route_decision: RouteDecision,
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    search_results = prioritize_human_review_results(
        search_knowledge_base(user_query, documents, top_k=12)
    )
    config = load_llm_config()
    llm_mode = config["llm_mode"]
    model = config["gemma_model"]
    draft_preview = build_human_review_draft_template(user_query)
    fallback_used = False
    error = None
    response_model = "deterministic-template"

    if llm_mode in {"gemma", "auto"}:
        try:
            draft_preview = call_gemma_for_human_review_draft(
                user_query,
                search_results,
                config["gemini_api_key"],
                model,
            )
            response_model = model
        except Exception as exc:
            fallback_used = True
            error = str(exc)
            response_model = model

    ticket = HumanReviewTicket(
        ticket_id=f"HITL-{datetime.now().astimezone():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}",
        route_status="generate_draft_and_escalate",
        permission_tier="Tier 1",
        risk_type=route_decision.risk_type,
        risk_reason=route_decision.risk_reason,
        intent_summary=route_decision.intent_summary,
        suggested_owner=suggest_human_review_owner(route_decision.risk_type),
        original_query=user_query,
        draft_type="商務澄清信草稿",
        draft_preview=draft_preview,
        retrieved_docs=[
            {
                "filename": result["filename"],
                "section_title": result["section_title"],
                "score": result["score"],
                "citation": result["citation"],
            }
            for result in search_results
        ],
        approval_required=True,
        status="Pending Human Review",
    )

    return {
        "ticket": ticket,
        "search_results": search_results,
        "answer": "已建立人工審查 ticket 與商務澄清信草稿，需由指定窗口確認後才能對外使用。",
        "llm_mode": llm_mode,
        "model": response_model,
        "fallback_used": fallback_used,
        "error": error,
    }


def build_data_ops_dry_run_sql() -> str:
    return f"""-- DRY RUN ONLY. NOT EXECUTED ON PRODUCTION DATABASE.
UPDATE {DATA_OPS_TABLE_NAME}
SET review_status = '已通過',
    last_updated_by = 'AI_SANDBOX_PREVIEW'
WHERE case_id = 'DEMO-001';"""


def validate_data_ops_sql(sql: str) -> tuple[Literal["passed", "blocked"], str | None]:
    normalized = re.sub(r"\s+", " ", sql).strip()
    statement_without_comment = re.sub(r"^--[^\n]*\n", "", sql.strip(), count=1).strip()
    statement_without_comment = re.sub(r"\s+", " ", statement_without_comment)

    if not sql.startswith("-- DRY RUN ONLY. NOT EXECUTED ON PRODUCTION DATABASE."):
        return "blocked", "缺少必要的 dry-run 安全註記。"
    if re.search(r"\b(DROP|DELETE|ALTER|INSERT|TRUNCATE|MERGE|CREATE)\b", normalized, re.IGNORECASE):
        return "blocked", "SQL 包含禁止的資料庫操作。"
    if statement_without_comment.count(";") != 1 or not statement_without_comment.endswith(";"):
        return "blocked", "只允許單一 SQL statement。"

    allowed_pattern = re.compile(
        rf"^UPDATE {re.escape(DATA_OPS_TABLE_NAME)} "
        r"SET review_status = '已通過', last_updated_by = 'AI_SANDBOX_PREVIEW' "
        r"WHERE case_id = 'DEMO-001';$",
        re.IGNORECASE,
    )
    if not allowed_pattern.fullmatch(statement_without_comment):
        return "blocked", "只允許更新 demo_case_status 的 DEMO-001，且必須包含指定 WHERE 條件。"

    return "passed", None


def data_ops_sandbox_skill(user_query: str, route_decision: RouteDecision) -> dict[str, Any]:
    target_status_detected = any(
        term in re.sub(r"\s+", "", user_query)
        for term in ["審核狀態改成通過", "狀態改成通過", "改成通過", "已通過"]
    )
    generated_sql = build_data_ops_dry_run_sql() if target_status_detected else (
        "-- DRY RUN ONLY. NOT EXECUTED ON PRODUCTION DATABASE.\n"
        "-- BLOCKED: 無法辨識允許的審核狀態更新意圖。"
    )
    validation_status, validation_error = validate_data_ops_sql(generated_sql)

    before_rows = [row.copy() for row in FAKE_SANDBOX_ROWS if row["case_id"] == "DEMO-001"]
    after_rows = [row.copy() for row in before_rows]
    if validation_status == "passed":
        after_rows[0]["review_status"] = "已通過"
        after_rows[0]["last_updated_by"] = "AI_SANDBOX_PREVIEW"

    result = DataOpsSandboxResult(
        sandbox_id=f"SANDBOX-{datetime.now().astimezone():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}",
        route_status="data_ops_dry_run",
        permission_tier="Tier 3",
        current_action_tier="Tier 1",
        risk_type="System Modification",
        risk_reason=route_decision.risk_reason,
        generated_sql=generated_sql,
        sql_validation_status=validation_status,
        before_rows=before_rows,
        after_rows=after_rows,
        approval_required=True,
        approval_queue="Supervisor Approval Queue",
        action_status="Dry-run only",
    )

    return {
        "sandbox_result": result,
        "answer": "已建立 Data Ops Sandbox dry-run preview；未連接或寫入任何 production database。",
        "llm_mode": load_llm_config()["llm_mode"],
        "model": "deterministic-data-ops-sandbox",
        "fallback_used": False,
        "error": validation_error,
    }


def generate_grounded_answer(user_query: str, search_results: list[dict[str, Any]]) -> dict[str, Any]:
    config = load_llm_config()
    llm_mode = config["llm_mode"]
    model = config["gemma_model"]

    if not search_results:
        return {
            "answer": "目前知識庫不足，無法可靠回答。",
            "llm_mode": "mock" if llm_mode == "mock" else llm_mode,
            "model": "mock" if llm_mode == "mock" else model,
            "fallback_used": False,
            "error": None,
        }

    if llm_mode == "mock":
        return {
            "answer": generate_mock_answer(search_results),
            "llm_mode": "mock",
            "model": "mock",
            "fallback_used": False,
            "error": None,
        }

    try:
        answer = call_gemma(user_query, search_results, config["gemini_api_key"], model)
        return {
            "answer": answer,
            "llm_mode": llm_mode,
            "model": model,
            "fallback_used": False,
            "error": None,
        }
    except Exception as exc:
        error_message = str(exc)
        if llm_mode == "auto":
            return {
                "answer": generate_mock_answer(search_results),
                "llm_mode": "auto",
                "model": model,
                "fallback_used": True,
                "error": error_message,
            }

        return {
            "answer": f"Gemma 模式目前無法產生回答：{error_message}",
            "llm_mode": "gemma",
            "model": model,
            "fallback_used": False,
            "error": error_message,
        }


def build_route_log(
    route_decision: RouteDecision,
    results: list[dict[str, Any]],
    answer_result: dict[str, Any],
    latency_ms: int,
    action_status: str,
    ticket: HumanReviewTicket | None = None,
    sandbox_result: DataOpsSandboxResult | None = None,
) -> dict[str, Any]:
    log = {
        "request_id": f"REQ-{datetime.now().astimezone():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "route_status": route_decision.route_status,
        "intent_summary": route_decision.intent_summary,
        "selected_tool": route_decision.selected_tool,
        "permission_tier": route_decision.permission_tier,
        "risk_type": route_decision.risk_type,
        "risk_reason": route_decision.risk_reason,
        "retrieval_required": route_decision.retrieval_required,
        "approval_required": route_decision.approval_required,
        "llm_mode": answer_result["llm_mode"],
        "model": answer_result["model"],
        "fallback_used": answer_result["fallback_used"],
        "retrieved_docs": [
            {
                "filename": result["filename"],
                "section_title": result["section_title"],
                "score": result["score"],
                "citation": result["citation"],
            }
            for result in results
        ],
        "latency_ms": latency_ms,
        "error": answer_result["error"],
        "action_status": action_status,
        "ticket_id": ticket.ticket_id if ticket else None,
        "draft_type": ticket.draft_type if ticket else None,
        "sandbox_id": sandbox_result.sandbox_id if sandbox_result else None,
        "current_action_tier": sandbox_result.current_action_tier if sandbox_result else None,
        "sql_validation_status": sandbox_result.sql_validation_status if sandbox_result else "N/A",
        "approval_queue": sandbox_result.approval_queue if sandbox_result else None,
    }
    return log


def add_user_message(content: str, documents: list[dict[str, Any]]) -> None:
    started_at = time.perf_counter()
    conversation_state = get_conversation_state()
    route_decision = route_user_request(content, conversation_state)
    results: list[dict[str, Any]] = []
    ticket: HumanReviewTicket | None = None
    sandbox_result: DataOpsSandboxResult | None = None

    if route_decision.route_status == "search":
        search_query = content
        previous_user_query = conversation_state.get("previous_user_query", "")
        if previous_user_query and route_decision.intent_summary.startswith("延續前一題"):
            search_query = f"{previous_user_query} {content}"
        results = search_knowledge_base(search_query, documents)
        answer_result = generate_grounded_answer(content, results)
        action_status = "answered"
    elif route_decision.route_status == "generate_draft_and_escalate":
        hitl_result = generate_draft_and_escalate_skill(content, route_decision, documents)
        ticket = hitl_result["ticket"]
        results = hitl_result["search_results"]
        answer_result = {
            "answer": hitl_result["answer"],
            "llm_mode": hitl_result["llm_mode"],
            "model": hitl_result["model"],
            "fallback_used": hitl_result["fallback_used"],
            "error": hitl_result["error"],
        }
        action_status = "pending_human_review"
    elif route_decision.route_status == "data_ops_dry_run":
        data_ops_result = data_ops_sandbox_skill(content, route_decision)
        sandbox_result = data_ops_result["sandbox_result"]
        answer_result = {
            "answer": data_ops_result["answer"],
            "llm_mode": data_ops_result["llm_mode"],
            "model": data_ops_result["model"],
            "fallback_used": data_ops_result["fallback_used"],
            "error": data_ops_result["error"],
        }
        action_status = "dry_run_only"
    else:
        config = load_llm_config()
        guardrail_answers = {
            "out_of_scope": "此問題超出安規認證業務範疇，已採零檢索策略。",
        }
        action_statuses = {
            "out_of_scope": "no_retrieval",
        }
        answer_result = {
            "answer": guardrail_answers[route_decision.route_status],
            "llm_mode": config["llm_mode"],
            "model": "deterministic-rule-router",
            "fallback_used": False,
            "error": None,
        }
        action_status = action_statuses[route_decision.route_status]

    latency_ms = round((time.perf_counter() - started_at) * 1000)

    st.session_state.messages.append({"role": "user", "content": content})
    assistant_message: dict[str, Any] = {"role": "assistant", "content": answer_result["answer"]}
    if ticket:
        assistant_message["hitl_ticket"] = ticket.model_dump()
    if sandbox_result:
        assistant_message["sandbox_result"] = sandbox_result.model_dump()
    st.session_state.messages.append(assistant_message)
    st.session_state.last_log = build_route_log(
        route_decision,
        results,
        answer_result,
        latency_ms,
        action_status,
        ticket,
        sandbox_result,
    )


def render_sidebar(documents: list[dict[str, Any]], load_error: str | None) -> None:
    with st.sidebar:
        st.header("Demo 說明")
        st.write("目前完成 Task 5C：高風險商務請求進入 HITL，系統修改意圖進入 Data Ops Sandbox。")
        st.write("所有資料操作僅產生 fake sandbox dry-run preview，不連接真實資料庫。")

        st.divider()
        st.subheader("知識庫文件")
        if load_error:
            st.warning(load_error)
        else:
            st.metric("已載入文件數", len(documents))
            for document in documents:
                st.markdown(f"**{document['title']}**")
                st.caption(document["filename"])

        st.divider()
        st.subheader("測試問題")
        for index, question in enumerate(TEST_QUESTIONS, start=1):
            if st.button(f"{index}. {question}", key=f"test_question_{index}", use_container_width=True):
                add_user_message(question, documents)
                st.rerun()

        st.divider()
        st.subheader("Log Panel")
        st.json(st.session_state.last_log)

        if st.button("清除對話", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_log = MOCK_LOG.copy()
            st.rerun()


def render_document_preview(documents: list[dict[str, Any]], load_error: str | None) -> None:
    st.subheader("知識庫文件預覽")

    if load_error:
        st.error(load_error)
        return

    for document in documents:
        with st.expander(document["title"], expanded=False):
            st.caption(f"檔案路徑：{document['path']}")
            st.text(document["preview"])
            st.text_area(
                label="原始 Markdown 內容",
                value=document["content"],
                height=180,
                disabled=True,
                key=f"raw_markdown_{document['doc_id']}",
            )


def render_hitl_ticket(ticket: dict[str, Any]) -> None:
    st.error("HITL GATE（Tier 1）：偵測到高風險商務承諾或需人工確認事項，已攔截直接回答。")
    with st.expander("[HITL GATE] 人工審查佇列", expanded=True):
        st.write(f"**ticket_id:** {ticket['ticket_id']}")
        st.write(f"**risk_type:** {ticket['risk_type']}")
        st.write(f"**risk_reason:** {ticket['risk_reason']}")
        st.write(f"**suggested_owner:** {ticket['suggested_owner']}")
        st.write(f"**status:** {ticket['status']}")
        st.text_area(
            "商務澄清信草稿",
            value=ticket["draft_preview"],
            height=360,
            key=f"draft_preview_{ticket['ticket_id']}",
        )

        st.markdown("**引用來源 / Retrieved docs**")
        for result in ticket["retrieved_docs"]:
            st.caption(
                f"{result['citation']} | {result['section_title']} | score={result['score']}"
            )


def render_data_ops_sandbox(sandbox_result: dict[str, Any]) -> None:
    st.error("SANDBOX GATE（Tier 3）：偵測到內部系統修改意圖，已禁止 production 寫入。")
    with st.expander("[SANDBOX GATE] Data Ops Dry-run Preview", expanded=True):
        st.write(f"**sandbox_id:** {sandbox_result['sandbox_id']}")
        st.write(f"**permission_tier:** {sandbox_result['permission_tier']}")
        st.write(f"**current_action_tier:** {sandbox_result['current_action_tier']}")
        st.write(f"**sql_validation_status:** {sandbox_result['sql_validation_status']}")
        st.code(sandbox_result["generated_sql"], language="sql")
        st.subheader("Before")
        st.table(sandbox_result["before_rows"])
        st.subheader("After")
        st.table(sandbox_result["after_rows"])
        st.warning("此結果僅為 dry-run preview，需主管核准後才可由授權人員處理。")


def render_chat(documents: list[dict[str, Any]]) -> None:
    st.subheader("Chat")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("hitl_ticket"):
                render_hitl_ticket(message["hitl_ticket"])
            if message.get("sandbox_result"):
                render_data_ops_sandbox(message["sandbox_result"])

    prompt = st.chat_input("請輸入產品認證或 scoping 相關問題")
    if prompt:
        add_user_message(prompt, documents)
        st.rerun()


def main() -> None:
    st.set_page_config(page_title=PROJECT_NAME, page_icon="G", layout="wide")
    initialize_state()

    documents, load_error = load_markdown_documents()

    st.title(PROJECT_NAME)
    st.caption(DEMO_CAPTION)

    render_sidebar(documents, load_error)
    render_document_preview(documents, load_error)
    st.divider()
    render_chat(documents)


if __name__ == "__main__":
    main()
