from __future__ import annotations

import html
import json
import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import streamlit as st
from pydantic import BaseModel, Field


PROJECT_NAME = "Certification Workflow Agent"
DEMO_CAPTION = "Prototype demo for an enterprise certification workflow: RAG, HITL, Data Ops Sandbox, Evidence Gate, Governance Trace, and Audit Log."
MOCK_REPLY = "這是 Task 1 的假回覆：目前尚未接上 RAG / LLM。"
DOCS_DIR = Path("data") / "docs"
DEFAULT_LLM_MODE = "mock"
DEFAULT_GEMMA_MODEL = "gemma-4-26b-a4b-it"
DATA_OPS_TABLE_NAME = "demo_case_status"
DESIGN_TOKENS = {
    "bg": "#F7F3EA",
    "surface": "#FFFDF8",
    "surface_alt": "#FDF8EF",
    "navy": "#0B3554",
    "navy_dark": "#08283F",
    "green": "#2F7D4A",
    "green_soft": "#E6EFE7",
    "border": "#D8D2C4",
    "text": "#1F2933",
    "muted": "#6B7A88",
    "gold": "#B9822E",
    "gold_soft": "#F5E9D6",
    "red": "#A85F5F",
    "red_soft": "#F7E6E4",
    "gray_soft": "#EEF1F2",
    "log_dark": "#0F1E2A",
}

# 集中式樣式表（Ivory Control Room）。色彩由 DESIGN_TOKENS 注入為 CSS 變數，見 inject_custom_css。
APP_CSS = r'''
/* ============================================================
   Certification Workflow Agent - Ivory Control Room
   安靜、精準、帶一點典雅的企業 AI workflow dashboard。
   去除:金粗邊 / 羊皮紙填色 / 厚深藍 tab bar / 大外框 / 多層卡片框。
   ============================================================ */

:root{
  --gc-font-cjk: "Microsoft JhengHei","PingFang TC","Noto Sans TC","Hiragino Sans TC",-apple-system,"Segoe UI",system-ui,sans-serif;
  --gc-font-serif: Georgia,"Times New Roman","Songti TC",serif;
  --gc-font-mono: "SFMono-Regular","JetBrains Mono",Consolas,Menlo,"Courier New",monospace;
  --gc-shadow-sm: 0 1px 2px rgba(8,40,63,.04);
  --gc-shadow-md: 0 1px 1px rgba(8,40,63,.04), 0 10px 24px -20px rgba(8,40,63,.30);
}

/* ---- base ---- */
.stApp{ background: var(--gc-bg); color: var(--gc-text); }
.stApp, .stMarkdown, .stMarkdown p, .stTextInput, .stTextArea, label, button, input, textarea{
  font-family: var(--gc-font-cjk);
}
.block-container{ padding-top: 1.5rem; padding-bottom: 5rem; max-width: 1180px; }
h1,h2,h3,h4,h5{ color: var(--gc-navy); font-weight: 700; letter-spacing: .2px; }
a{ color: var(--gc-navy); text-decoration-color: var(--gc-border); }
hr{ border-color: var(--gc-border); opacity: .7; }
[data-testid="stHeader"]{ background: transparent; }
footer{ visibility: hidden; }
#MainMenu{ visibility: hidden; }

/* ---- shared atoms ---- */
.gc-eyebrow{
  font-family: var(--gc-font-mono);
  font-size: .66rem; font-weight: 700;
  letter-spacing: .15em; text-transform: uppercase;
  color: var(--gc-muted); margin: .15rem 0 .5rem;
}
.gc-section-title{ font-size: 1.12rem; font-weight: 700; color: var(--gc-navy); margin: 0 0 .15rem; }
.gc-note{
  font-size: .8rem; color: var(--gc-muted);
  border-left: 2px solid var(--gc-border); padding: .1rem 0 .1rem .6rem; margin: .5rem 0 .2rem;
  line-height: 1.55;
}

/* ---- HERO (slim system header) ---- */
.gc-hero{
  position: relative; overflow: hidden;
  border: 1px solid rgba(11,53,84,.18);
  border-radius: 14px;
  background:
    radial-gradient(130% 150% at 92% -25%, rgba(47,125,74,.16), transparent 60%),
    linear-gradient(135deg, var(--gc-navy-dark), var(--gc-navy));
  box-shadow: var(--gc-shadow-md);
  margin: .1rem 0 1.1rem;
}
.gc-hero__grid{
  position: absolute; inset: 0; opacity: .22; pointer-events: none;
  background-image:
    linear-gradient(rgba(247,243,234,.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(247,243,234,.05) 1px, transparent 1px);
  background-size: 26px 26px;
  mask-image: linear-gradient(120deg, black, transparent 62%);
}
.gc-hero__body{ position: relative; padding: 1.05rem 1.4rem 1.1rem; }
.gc-hero__eyebrow{
  font-family: var(--gc-font-mono); font-size: .63rem; letter-spacing: .2em;
  text-transform: uppercase; color: rgba(245,233,214,.72); margin-bottom: .5rem;
}
.gc-hero__title{
  font-family: var(--gc-font-serif); font-weight: 700;
  font-size: 1.7rem; line-height: 1.08; color: var(--gc-surface); letter-spacing: .4px;
}
.gc-hero__sub{
  font-family: var(--gc-font-mono); font-size: .75rem; letter-spacing: .03em;
  color: rgba(245,233,214,.82); margin-top: .25rem;
}
.gc-hero__lede{ color: rgba(247,243,234,.80); font-size: .87rem; line-height: 1.6; max-width: 62ch; margin-top: .6rem; }
.gc-hero__chips{ display: flex; flex-wrap: wrap; gap: .45rem; margin-top: .85rem; }

/* ---- chips ---- */
.gc-chip{
  display: inline-flex; align-items: center; gap: .4rem;
  font-size: .73rem; font-weight: 600; letter-spacing: .02em;
  padding: .24rem .62rem; border-radius: 999px;
  border: 1px solid rgba(245,233,214,.26);
  background: rgba(247,243,234,.06); color: var(--gc-surface);
}
.gc-chip::before{ content: ""; width: 5px; height: 5px; border-radius: 50%; background: rgba(185,130,46,.85); }

/* ---- status badge ---- */
.gc-badge{
  display: inline-flex; align-items: center; gap: .4rem;
  font-size: .74rem; font-weight: 700; letter-spacing: .01em;
  padding: .18rem .56rem; border-radius: 999px;
  border: 1px solid transparent; line-height: 1.2;
}
.gc-badge__dot{ width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.gc-badge--success{ color: var(--gc-green); background: rgba(47,125,74,.10); border-color: rgba(47,125,74,.22); }
.gc-badge--warning{ color: var(--gc-gold);  background: rgba(185,130,46,.10); border-color: rgba(185,130,46,.24); }
.gc-badge--danger{  color: var(--gc-red);   background: rgba(168,95,95,.10);  border-color: rgba(168,95,95,.24); }
.gc-badge--neutral{ color: var(--gc-muted); background: var(--gc-gray-soft);  border-color: var(--gc-border); }

/* ---- sidebar / control panel ---- */
[data-testid="stSidebar"]{ background: var(--gc-surface); border-right: 1px solid var(--gc-border); }
[data-testid="stSidebar"] .block-container{ padding-top: 1.1rem; }
.gc-side-brand{ display: flex; align-items: center; gap: .55rem; margin-bottom: .9rem; }
.gc-side-brand__mark{
  font-family: var(--gc-font-mono); font-weight: 700; font-size: .8rem;
  color: var(--gc-surface); background: var(--gc-navy);
  width: 28px; height: 28px; border-radius: 7px;
  display: inline-flex; align-items: center; justify-content: center;
}
.gc-side-brand__name{ font-weight: 700; color: var(--gc-navy); font-size: 1rem; }

/* info cards -> light accent ticks (no box, no fill) */
.gc-info-card{
  background: transparent; border: 0;
  border-left: 2px solid var(--gc-border);
  border-radius: 0; padding: .1rem 0 .3rem .65rem; margin-bottom: .55rem;
}
.gc-info-card__k{
  font-family: var(--gc-font-mono); font-size: .6rem; letter-spacing: .12em;
  text-transform: uppercase; color: var(--gc-muted); margin-bottom: .12rem;
}
.gc-info-card__v{ font-size: .8rem; color: var(--gc-text); line-height: 1.45; }
.gc-info-card--navy{ border-left-color: rgba(11,53,84,.45); }
.gc-info-card--green{ border-left-color: var(--gc-green); }
.gc-info-card--gold{ border-left-color: var(--gc-gold); }
.gc-info-card--rose{ border-left-color: var(--gc-red); }

/* metric */
[data-testid="stMetric"]{
  background: var(--gc-surface); border: 1px solid var(--gc-border);
  border-radius: 10px; padding: .5rem .75rem; box-shadow: none;
}
[data-testid="stMetricLabel"] p{ color: var(--gc-muted); font-size: .7rem; letter-spacing: .04em; }
[data-testid="stMetricValue"]{ color: var(--gc-navy); font-family: var(--gc-font-mono); }

/* knowledge file mini rows */
.gc-kb-mini{ display: flex; align-items: center; gap: .5rem; padding: .28rem 0; border-bottom: 1px solid var(--gc-border); }
.gc-kb-mini__name{ font-size: .79rem; color: var(--gc-text); }

/* ---- buttons ---- */
.stButton > button, .stDownloadButton > button{
  background: var(--gc-surface); color: var(--gc-navy);
  border: 1px solid var(--gc-border); border-radius: 9px;
  font-weight: 600; box-shadow: none;
  transition: background .14s ease, color .14s ease, border-color .14s ease;
}
[data-testid="stSidebar"] .stButton > button{
  text-align: left; white-space: normal; line-height: 1.4;
  font-size: .8rem; font-weight: 500; padding: .45rem .65rem;
}
.stButton > button:hover, .stDownloadButton > button:hover{
  border-color: var(--gc-navy); background: var(--gc-navy); color: var(--gc-surface);
}
.stButton > button:focus, .stDownloadButton > button:focus{
  box-shadow: 0 0 0 3px rgba(11,53,84,.12); border-color: var(--gc-navy);
}
.stButton > button:active{ transform: translateY(1px); }

/* ---- tabs (thin: navy text + 2px underline, no heavy bar) ---- */
[data-testid="stTabs"] [data-baseweb="tab-list"]{
  gap: .1rem; border-bottom: 1px solid var(--gc-border); margin-bottom: .3rem;
}
[data-baseweb="tab"]{ font-weight: 600; color: var(--gc-muted); background: transparent; padding: .5rem .8rem; }
[data-baseweb="tab"]:hover{ color: var(--gc-navy); }
[data-baseweb="tab"][aria-selected="true"]{ color: var(--gc-navy); }
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{ background-color: var(--gc-navy); height: 2px; }

/* ---- expander (hairline) ---- */
[data-testid="stExpander"]{
  border: 1px solid var(--gc-border); border-radius: 10px;
  background: var(--gc-surface); box-shadow: none; overflow: hidden;
}
[data-testid="stExpander"] summary{ font-weight: 600; color: var(--gc-navy); }

/* ---- code blocks: light panel, keep token colors + copy ---- */
[data-testid="stCode"], .stCode{ background: transparent; }
[data-testid="stCode"] pre, .stCode pre, pre{
  background: var(--gc-surface-alt) !important;
  border: 1px solid var(--gc-border); border-radius: 9px;
}
code, pre, kbd{ font-family: var(--gc-font-mono); }

/* ---- text area ---- */
.stTextArea textarea{
  background: var(--gc-surface-alt) !important;
  border: 1px solid var(--gc-border) !important; border-radius: 9px !important;
  color: var(--gc-text) !important; font-family: var(--gc-font-cjk);
  font-size: .85rem; line-height: 1.6;
}
.stTextArea textarea:focus{ box-shadow: 0 0 0 3px rgba(11,53,84,.12); border-color: var(--gc-navy) !important; }

/* ---- tables (quiet data table) ---- */
[data-testid="stTable"] table{
  border-collapse: separate; border-spacing: 0;
  border: 1px solid var(--gc-border); border-radius: 9px; overflow: hidden;
  background: var(--gc-surface); font-size: .83rem;
}
[data-testid="stTable"] thead th{
  background: var(--gc-gray-soft); color: var(--gc-navy);
  font-weight: 700; letter-spacing: .02em; text-align: left;
  border-bottom: 1px solid var(--gc-border);
}
[data-testid="stTable"] tbody th{ background: var(--gc-surface); color: var(--gc-muted); }
[data-testid="stTable"] tbody td{ color: var(--gc-text); }

/* ---- chat input ---- */
[data-testid="stChatInput"]{
  border: 1px solid var(--gc-border); border-radius: 11px;
  background: var(--gc-surface); box-shadow: none;
}
[data-testid="stChatInput"]:focus-within{ border-color: var(--gc-navy); box-shadow: 0 0 0 3px rgba(11,53,84,.10); }
[data-testid="stChatInput"] textarea{ color: var(--gc-text); }

/* ---- gate container marker ----
   不再全域 styling stVerticalBlockBorderWrapper，避免 Streamlit 外層容器被 :has() 污染成大框。
   Gate 色彩改由 banner / badge / 內容區塊自己承擔。 */
.gc-marker{ display: none; }

/* ---- gate header: lightweight label row (no fill, no border) ---- */
.gc-banner{
  display: flex; align-items: baseline; gap: .55rem; flex-wrap: wrap;
  border-radius: 9px;
  padding: .45rem .65rem;
  margin: .05rem 0 .65rem;
  border: 1px solid var(--gc-border);
  background: var(--gc-surface);
  border-left-width: 3px;
}
.gc-banner__eyebrow{
  font-family: var(--gc-font-mono); font-size: .62rem; letter-spacing: .14em;
  text-transform: uppercase; font-weight: 700; color: var(--gc-muted);
}
.gc-banner__title{ font-weight: 700; font-size: .96rem; color: var(--gc-navy); }
.gc-banner--gold{
  background: rgba(185,130,46,.055);
  border-color: rgba(185,130,46,.24);
  border-left-color: var(--gc-gold);
}
.gc-banner--rose{
  background: rgba(168,95,95,.055);
  border-color: rgba(168,95,95,.24);
  border-left-color: var(--gc-red);
}
.gc-banner--lowconf{
  background: rgba(185,130,46,.045);
  border-color: rgba(185,130,46,.22);
  border-left-color: var(--gc-gold);
}
.gc-banner--green{
  background: rgba(47,125,74,.045);
  border-color: rgba(47,125,74,.22);
  border-left-color: var(--gc-green);
}
.gc-banner--gold .gc-banner__eyebrow{ color: var(--gc-gold); }
.gc-banner--rose .gc-banner__eyebrow{ color: var(--gc-red); }
.gc-banner--lowconf .gc-banner__eyebrow{ color: var(--gc-gold); }
.gc-banner--green .gc-banner__eyebrow{ color: var(--gc-green); }

/* ---- key/value: borderless definition grid ---- */
.gc-kv-grid{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: .55rem .9rem; margin: .35rem 0 .7rem;
}
.gc-kv{ background: transparent; border: 0; border-radius: 0; padding: 0; }
.gc-kv__k{
  font-family: var(--gc-font-mono); font-size: .6rem; letter-spacing: .1em;
  text-transform: uppercase; color: var(--gc-muted); margin-bottom: .1rem;
}
.gc-kv__v{ font-size: .84rem; color: var(--gc-text); font-family: var(--gc-font-mono); word-break: break-word; }

/* missing-term chips (light) */
.gc-terms{ display: flex; flex-wrap: wrap; gap: .35rem; margin: .25rem 0 .2rem; }
.gc-term{
  font-family: var(--gc-font-mono); font-size: .7rem;
  background: rgba(168,95,95,.08); color: var(--gc-red);
  border: 1px solid rgba(168,95,95,.22); border-radius: 6px; padding: .1rem .42rem;
}

/* retrieved evidence rows */
.gc-evi{
  font-family: var(--gc-font-mono); font-size: .73rem; color: var(--gc-muted);
  padding: .22rem 0; border-bottom: 1px solid var(--gc-border);
}
.gc-evi b{ color: var(--gc-text); font-weight: 600; }

/* ---- knowledge asset cards (light) ---- */
.gc-kb-card{
  background: var(--gc-surface); border: 1px solid var(--gc-border);
  border-left: 3px solid var(--gc-muted); border-radius: 10px;
  padding: .7rem .85rem; margin-bottom: .5rem; box-shadow: var(--gc-shadow-sm);
}
.gc-kb-card--navy{ border-left-color: rgba(11,53,84,.55); }
.gc-kb-card--gold{ border-left-color: var(--gc-gold); }
.gc-kb-card--rose{ border-left-color: var(--gc-red); }
.gc-kb-card__head{ display: flex; align-items: center; gap: .5rem; margin-bottom: .25rem; }
.gc-kb-card__title{ font-weight: 700; color: var(--gc-navy); font-size: .95rem; }
.gc-kb-card__file{ font-family: var(--gc-font-mono); font-size: .71rem; color: var(--gc-muted); }
.gc-kb-card__purpose{ font-size: .83rem; color: var(--gc-text); margin-top: .3rem; line-height: 1.5; }
.gc-tag{
  font-family: var(--gc-font-mono); font-size: .64rem; font-weight: 700;
  letter-spacing: .05em; padding: .1rem .46rem; border-radius: 5px; border: 1px solid transparent;
}
.gc-tag--navy{ color: var(--gc-navy); background: var(--gc-gray-soft); border-color: var(--gc-border); }
.gc-tag--gold{ color: var(--gc-gold); background: rgba(185,130,46,.10); border-color: rgba(185,130,46,.24); }
.gc-tag--rose{ color: var(--gc-red); background: rgba(168,95,95,.10); border-color: rgba(168,95,95,.24); }
.gc-tag--muted{ color: var(--gc-muted); background: var(--gc-gray-soft); border-color: var(--gc-border); }

/* ---- chat / review workbench (light cards, no enclosing panel) ---- */
.gc-msg{ margin: .5rem 0; }
.gc-msg--user{
  background: var(--gc-gray-soft); border: 1px solid var(--gc-border);
  border-radius: 11px; padding: .55rem .8rem; margin-left: auto; max-width: 86%;
}
.gc-msg__label{
  font-family: var(--gc-font-mono); font-size: .62rem; letter-spacing: .14em;
  text-transform: uppercase; color: var(--gc-muted); font-weight: 700; margin-bottom: .22rem;
}
.gc-msg--user .gc-msg__label{ color: var(--gc-navy); }
.gc-msg__body{ white-space: pre-wrap; line-height: 1.62; color: var(--gc-text); font-size: .89rem; }
.gc-msg--assistant{
  background: var(--gc-surface); border: 1px solid var(--gc-border);
  border-left: 2px solid var(--gc-muted); border-radius: 11px;
  padding: .65rem .85rem; box-shadow: var(--gc-shadow-sm); max-width: 97%;
}
.gc-msg--assistant.gc-tone-success{ border-left-color: var(--gc-green); }
.gc-msg--assistant.gc-tone-warning{ border-left-color: var(--gc-gold); }
.gc-msg--assistant.gc-tone-danger{ border-left-color: var(--gc-red); }
.gc-msg--assistant.gc-tone-neutral{ border-left-color: var(--gc-muted); }
.gc-msg__head{ display: flex; align-items: center; gap: .55rem; margin-bottom: .35rem; flex-wrap: wrap; }

/* ---- audit console (dark, no extra frame) ---- */
.gc-console{
  background: var(--gc-log-dark); border: 1px solid #182c3a; border-radius: 11px;
  padding: .9rem 1rem; box-shadow: var(--gc-shadow-sm);
  font-family: var(--gc-font-mono); color: #cdd9e2; overflow-x: auto;
}
.gc-console__pills{ display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: .8rem; }
.gc-pill{
  font-size: .69rem; letter-spacing: .02em; padding: .18rem .52rem; border-radius: 6px;
  border: 1px solid rgba(205,217,226,.16); background: rgba(205,217,226,.05); color: #e7eef3;
}
.gc-pill b{ color: #fff; font-weight: 700; }
.gc-pill--green{ border-color: rgba(86,182,124,.38); color: #8fe0ad; }
.gc-pill--gold{ border-color: rgba(214,168,96,.42); color: #e6c081; }
.gc-pill--rose{ border-color: rgba(212,143,143,.42); color: #e6a8a8; }
.gc-cline{ display: flex; gap: .7rem; padding: .18rem 0; align-items: baseline; line-height: 1.55; }
.gc-cline__tag{
  flex: 0 0 76px; font-size: .63rem; font-weight: 700; letter-spacing: .1em;
  padding: .06rem .38rem; border-radius: 4px; text-align: center;
  background: rgba(205,217,226,.07); color: #9fb3c2;
}
.gc-cline__tag--route{ color: #8ab4d8; }
.gc-cline__tag--plan{ color: #b7c3cd; }
.gc-cline__tag--guard{ color: #e6c081; }
.gc-cline__tag--action{ color: #8fe0ad; }
.gc-cline__tag--perf{ color: #b7c3cd; }
.gc-cline__tag--evidence{ color: #e6a8a8; }
.gc-cline__tag--hitl{ color: #e6c081; }
.gc-cline__tag--sandbox{ color: #e6a8a8; }
.gc-cline__txt{ font-size: .77rem; color: #d7e1e9; word-break: break-word; }
.gc-cline__txt em{ color: #90a3b1; font-style: normal; }
'''
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
    "evidence_sufficient": None,
    "evidence_confidence": None,
    "evidence_hit_count": None,
    "evidence_top_score": None,
    "evidence_coverage": None,
    "evidence_missing_terms": None,
    "evidence_reason": None,
    "evidence_judge_used": None,
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

# === 情境五 Self-Correction Loop：證據評估設定 ===
# top chunk 的原始分數必須清過此底線（依實際知識庫校準，見 README）
USE_LLM_EVIDENCE_JUDGE = False
EVIDENCE_SCORE_FLOOR = 3
# 「具鑑別力的查詢詞」至少要有這個比例落在檢索內容裡，才算有依據
EVIDENCE_COVERAGE_THRESHOLD = 0.5
EVIDENCE_MIN_HITS = 1

# 太通用、單獨命中不足以證明主題相關的詞（不計入 coverage 分母）
EVIDENCE_GENERIC_TERMS = {
    "耳機", "產品", "法規", "認證", "測試", "資訊", "樣品",
    "適用", "需要", "哪些", "什麼", "可以", "這款",
}

# 具鑑別力的訊號詞（中文無空白，retrieval tokenizer 會漏掉，這裡補上）
EVIDENCE_SIGNAL_TERMS = [
    "衛星", "頻段", "日本", "美國", "歐洲", "歐盟",
    "藍牙", "無線", "scoping", "fcc", "part 15", "red", "ce", "emc",
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
    draft_type: Literal["商務澄清信草稿", "知識庫不足通知"]
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


class EvidenceAssessment(BaseModel):
    """情境五的核心：檢索後對證據強度的顯式評估結果。"""
    sufficient: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    top_score: int
    hit_count: int
    coverage: float = Field(ge=0.0, le=1.0)
    matched_terms: list[str]
    missing_terms: list[str]
    judge_used: bool = False
    judge_verdict: str | None = None


def initialize_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_log" not in st.session_state:
        st.session_state.last_log = MOCK_LOG.copy()


def inject_custom_css() -> None:
    """集中式 Ivory Control Room 樣式。色彩一律由 DESIGN_TOKENS 推導為 CSS 變數，
    版面樣式存在模組常數 APP_CSS，方便單點調整與審閱。"""
    root_vars = ":root{" + ";".join(
        f"--gc-{key.replace('_', '-')}: {value}" for key, value in DESIGN_TOKENS.items()
    ) + ";}"
    st.markdown(f"<style>{root_vars}{APP_CSS}</style>", unsafe_allow_html=True)


def html_escape(text: Any) -> str:
    return html.escape(str(text), quote=True)


def build_badge_html(label: str, tone: str) -> str:
    safe_tone = tone if tone in {"success", "warning", "danger", "neutral"} else "neutral"
    return (
        f'<span class="gc-badge gc-badge--{safe_tone}">'
        f'<span class="gc-badge__dot"></span>{html_escape(label)}</span>'
    )


def render_chip(label: str) -> str:
    return f'<span class="gc-chip">{html_escape(label)}</span>'


def render_hero() -> None:
    chips = "".join(render_chip(label) for label in ["RAG", "HITL", "Data Ops Sandbox", "Audit Log"])
    st.markdown(
        f"""
        <div class="gc-hero">
          <div class="gc-hero__grid"></div>
          <div class="gc-hero__body">
            <div class="gc-hero__eyebrow">ENTERPRISE CERTIFICATION WORKFLOW</div>
            <div class="gc-hero__title">{PROJECT_NAME}</div>
            <div class="gc-hero__sub">Demo v2.1 · Governed Agentic Workflow</div>
            <div class="gc-hero__lede">企業內部知識助理，將 RAG、人工審查、Data Ops Sandbox 與 Audit Log
            串成可治理的 Agentic Workflow。</div>
            <div class="gc-hero__chips">{chips}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_gate_banner(eyebrow: str, title: str, accent: str) -> None:
    st.markdown(
        f'<div class="gc-banner gc-banner--{accent}">'
        f'<span class="gc-banner__eyebrow">{html_escape(eyebrow)}</span>'
        f'<span class="gc-banner__title">{html_escape(title)}</span></div>',
        unsafe_allow_html=True,
    )


def render_gate_marker(accent: str) -> None:
    """隱藏標記元素，供 CSS :has() 為其所在的 bordered container 上色（漸進增強）。"""
    st.markdown(f'<span class="gc-marker gc-marker--{accent}"></span>', unsafe_allow_html=True)


def render_kv_grid(rows: list[tuple[str, Any]]) -> None:
    cells = "".join(
        f'<div class="gc-kv"><div class="gc-kv__k">{html_escape(key)}</div>'
        f'<div class="gc-kv__v">{html_escape(value)}</div></div>'
        for key, value in rows
    )
    st.markdown(f'<div class="gc-kv-grid">{cells}</div>', unsafe_allow_html=True)


def render_eyebrow(label: str) -> None:
    st.markdown(f'<div class="gc-eyebrow">{html_escape(label)}</div>', unsafe_allow_html=True)


def classify_document(filename: str) -> tuple[str, str, str]:
    """UI-only：依檔名前綴決定文件分類標籤、用途短句與配色。"""
    name = filename.lower()
    if name.startswith("sop"):
        return "SOP", "認證 scoping 與流程依據", "navy"
    if name.startswith("policy"):
        return "Policy", "AI 對外回覆與承諾邊界", "gold"
    if name.startswith("faq"):
        return "FAQ", "高風險轉人工規則", "rose"
    return "DOC", "內部知識文件", "muted"


def extract_missing_terms(reason: str) -> list[str]:
    """UI-only：從 evidence reason 文字中解析未命中的關鍵詞，供 Low Confidence 面板顯示。"""
    match = re.search(r"未命中：([^）)]+)", reason or "")
    if not match:
        return []
    return [
        term.strip()
        for term in re.split(r"[、,，]", match.group(1))
        if term.strip() and term.strip() != "無"
    ]


def render_status_badge(label: str, tone: Literal["success", "warning", "danger", "neutral"]) -> None:
    st.markdown(build_badge_html(label, tone), unsafe_allow_html=True)


def build_status_badge(
    route_status: str,
    action_status: str,
    risk_type: str,
) -> tuple[str, Literal["success", "warning", "danger", "neutral"]]:
    if route_status == "search" and action_status == "answered":
        return "已引用來源", "success"
    if risk_type == "Low Confidence" and action_status == "low_confidence_escalated":
        return "資料不足，已轉人工", "warning"
    if route_status == "generate_draft_and_escalate" and action_status == "pending_human_review":
        return "需人工審查", "warning"
    if route_status == "data_ops_dry_run":
        return "已禁止 production 寫入", "danger"
    if route_status == "out_of_scope":
        return "零檢索", "neutral"
    return "狀態已記錄", "neutral"


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


def extract_evidence_terms(query: str) -> list[str]:
    """抽出查詢中『具主題訊號』的詞，獨立於 retrieval tokenizer，
    確保像「衛星」這種中文無空白詞也能被納入 coverage 計算。"""
    lower_query = query.lower()
    pool = COMMON_KEYWORDS + EVIDENCE_SIGNAL_TERMS
    terms = {keyword.lower() for keyword in pool if keyword.lower() in lower_query}
    return sorted(terms)


def build_evidence_judge_prompt(query: str, results: list[dict[str, Any]]) -> str:
    context_lines = []
    for index, result in enumerate(results[:3], start=1):
        context_lines.append(
            f"[{index}] {result['filename']} / {result['section_title']}：" +
            build_preview(result["clean_content"], 220)
        )
    context_text = "\n".join(context_lines) if context_lines else "（無任何檢索結果）"

    return f"""你是企業知識庫的「證據充分性審查員」。
只根據下方檢索段落，判斷是否足以對使用者問題給出有依據、可信的初步回答。
保守原則：只要檢索段落沒有正面涵蓋問題的關鍵主題，就視為不足。
你只能輸出 JSON，不要任何多餘文字或 Markdown，格式如下：
{{"sufficient": true/false, "confidence": 0.0~1.0, "reason": "一句中文理由"}}

使用者問題：
{query}

檢索段落：
{context_text}
"""


def call_evidence_judge(
    query: str,
    results: list[dict[str, Any]],
    api_key: str,
    model: str,
) -> tuple[bool, float, str]:
    """LLM-as-judge：回傳 (sufficient, confidence, reason)。失敗則由呼叫端忽略。"""
    if not api_key:
        raise ValueError("缺少 GEMINI_API_KEY，無法呼叫 evidence judge。")

    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=build_evidence_judge_prompt(query, results),
    )
    text = (getattr(response, "text", None) or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    parsed = json.loads(text)
    sufficient = bool(parsed.get("sufficient", False))
    confidence = float(parsed.get("confidence", 0.0))
    confidence = min(max(confidence, 0.0), 1.0)
    reason = str(parsed.get("reason", "")).strip() or "judge 未提供理由"
    return sufficient, confidence, reason


def load_evidence_config() -> dict[str, bool | float | int]:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass

    judge_value = os.getenv("USE_LLM_EVIDENCE_JUDGE", str(USE_LLM_EVIDENCE_JUDGE)).strip().lower()
    use_llm_judge = judge_value in {"1", "true", "yes", "on"}

    try:
        score_floor = max(0, int(os.getenv("EVIDENCE_SCORE_FLOOR", str(EVIDENCE_SCORE_FLOOR))))
    except ValueError:
        score_floor = EVIDENCE_SCORE_FLOOR

    try:
        coverage_threshold = float(
            os.getenv("EVIDENCE_COVERAGE_THRESHOLD", str(EVIDENCE_COVERAGE_THRESHOLD))
        )
        coverage_threshold = min(max(coverage_threshold, 0.0), 1.0)
    except ValueError:
        coverage_threshold = EVIDENCE_COVERAGE_THRESHOLD

    return {
        "use_llm_judge": use_llm_judge,
        "score_floor": score_floor,
        "coverage_threshold": coverage_threshold,
    }


def evaluate_evidence(
    query: str,
    results: list[dict[str, Any]],
    llm_mode: str = "mock",
    api_key: str = "",
    model: str = DEFAULT_GEMMA_MODEL,
) -> EvidenceAssessment:
    """情境五 self-correction 的關鍵步驟：檢索『之後』顯式評估證據強度。

    設計：deterministic 門檻是永遠生效的底線（mock 模式也能重現）；
    LLM judge 為可選的彈性層，且『只能加嚴、不能放寬』——
    judge 認為不足可推翻 deterministic 的『足夠』，但 judge 認為足夠
    不會推翻 deterministic 的『不足』。這讓 demo 保持 fail-safe。
    """
    evidence_config = load_evidence_config()
    use_llm_judge = bool(evidence_config["use_llm_judge"])
    score_floor = int(evidence_config["score_floor"])
    coverage_threshold = float(evidence_config["coverage_threshold"])
    top_score = int(results[0]["score"]) if results else 0
    hit_count = len(results)

    # --- 訊號一：具鑑別力查詢詞的覆蓋率 ---
    evidence_terms = extract_evidence_terms(query)
    distinctive_terms = [t for t in evidence_terms if t not in EVIDENCE_GENERIC_TERMS]
    retrieved_text = " ".join(result["clean_content"].lower() for result in results)
    matched = [t for t in distinctive_terms if t in retrieved_text]
    missing = [t for t in distinctive_terms if t not in retrieved_text]
    coverage = (len(matched) / len(distinctive_terms)) if distinctive_terms else (1.0 if results else 0.0)

    # --- deterministic 底線判定 ---
    det_sufficient = (
        hit_count >= EVIDENCE_MIN_HITS
        and top_score >= score_floor
        and coverage >= coverage_threshold
    )
    if not results:
        det_reason = "檢索無任何命中文件，知識庫依據不足。"
    elif top_score < score_floor:
        det_reason = f"最高檢索分數 {top_score} 低於門檻 {score_floor}，依據不足。"
    elif coverage < coverage_threshold:
        det_reason = (
            f"關鍵查詢詞覆蓋率 {coverage:.0%} 低於門檻 "
            f"{coverage_threshold:.0%}（未命中：{', '.join(missing) or '無'}）。"
        )
    else:
        det_reason = f"檢索分數 {top_score} 與關鍵詞覆蓋率 {coverage:.0%} 均達門檻。"

    sufficient = det_sufficient
    confidence = round(min(coverage, top_score / max(score_floor * 2, 1)), 3) if results else 0.0
    reason = det_reason
    judge_used = False
    judge_verdict = None

    # --- 可選彈性層：LLM judge（只能加嚴）---
    if use_llm_judge and llm_mode in {"gemma", "auto"} and api_key:
        try:
            judge_ok, judge_conf, judge_reason = call_evidence_judge(query, results, api_key, model)
            judge_used = True
            judge_verdict = f"sufficient={judge_ok}, confidence={judge_conf}, reason={judge_reason}"
            if det_sufficient and not judge_ok:
                # judge 加嚴：推翻 deterministic 的「足夠」
                sufficient = False
                confidence = min(confidence, judge_conf)
                reason = f"deterministic 通過但 LLM judge 判定依據不足：{judge_reason}"
            elif det_sufficient and judge_ok:
                confidence = round((confidence + judge_conf) / 2, 3)
                reason = f"{det_reason}（LLM judge 亦判定足夠）"
        except Exception as exc:  # judge 失敗不影響底線
            judge_used = False
            judge_verdict = f"judge 呼叫失敗，採用 deterministic 結果：{exc}"

    return EvidenceAssessment(
        sufficient=sufficient,
        confidence=confidence,
        reason=reason,
        top_score=top_score,
        hit_count=hit_count,
        coverage=round(coverage, 3),
        matched_terms=matched,
        missing_terms=missing,
        judge_used=judge_used,
        judge_verdict=judge_verdict,
    )


def build_low_confidence_route(
    original: RouteDecision,
    evidence: EvidenceAssessment,
) -> RouteDecision:
    """把初判的 search 覆寫成 Low Confidence 的 Tier 1 escalation。"""
    return RouteDecision(
        route_status="generate_draft_and_escalate",
        intent_summary=(
            "知識庫依據不足，已從 search 自動升級為人工審查路由"
            f"（原意圖：{original.intent_summary}）"
        ),
        selected_tool="generate_draft_and_escalate_skill",
        permission_tier="Tier 1",
        risk_type="Low Confidence",
        risk_reason=evidence.reason,
        retrieval_required=True,
        approval_required=True,
        confidence=evidence.confidence,
    )


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


def build_low_confidence_draft_template(user_query: str, evidence: EvidenceAssessment | None = None) -> str:
    missing_hint = ""
    if evidence and evidence.missing_terms:
        missing_hint = f"\n（系統偵測到未涵蓋的關鍵主題：{', '.join(evidence.missing_terms)}）"
    return f"""主旨：知識庫依據不足，建議補充文件後再評估

您好，

針對您的問題，本系統在目前的內部知識庫中，尚未檢索到足以提供可信依據的相關文件。
檢索信心分數低於設定門檻，為避免在依據不足的情況下做出可能誤導的回覆，系統已自動將此問題轉為人工審查。{missing_hint}

原始問題：
{user_query}

建議後續處理：
1. 由資深認證工程師確認此主題是否屬於現行法規／SOP 範圍。
2. 補充對應的法規或測試文件至知識庫後重新查詢。
3. 在補件完成前，請勿將本系統回覆作為對外依據。

本通知為人工審查草稿，尚未經過確認。"""


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
    low_confidence: bool = False,
    evidence: EvidenceAssessment | None = None,
) -> dict[str, Any]:
    search_results = prioritize_human_review_results(
        search_knowledge_base(user_query, documents, top_k=12)
    )
    config = load_llm_config()
    llm_mode = config["llm_mode"]
    model = config["gemma_model"]
    fallback_used = False
    error = None

    if low_confidence:
        # 知識庫不足：用 deterministic 的「不足通知」草稿，不走商務信驗證。
        draft_type = "知識庫不足通知"
        draft_preview = build_low_confidence_draft_template(user_query, evidence)
        response_model = "deterministic-template"
    else:
        draft_type = "商務澄清信草稿"
        draft_preview = build_human_review_draft_template(user_query)
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
        draft_type=draft_type,
        draft_preview=draft_preview,
        retrieved_docs=[
            {
                "filename": result["filename"],
                "section_title": result["section_title"],
                "score": result["score"],
                "citation": (
                    "[檢索分數低於門檻，依據不足]" if low_confidence else result["citation"]
                ),
            }
            for result in search_results
        ],
        approval_required=True,
        status="Pending Human Review",
    )

    answer = (
        "本系統目前知識庫中，尚未收錄足以回答此問題的文件。\n"
        "檢索信心分數低於門檻，無法提供可信依據。\n"
        "建議將此問題轉交資深工程師，並在補充相關文件後重新查詢。"
        if low_confidence
        else "已建立人工審查 ticket 與商務澄清信草稿，需由指定窗口確認後才能對外使用。"
    )

    return {
        "ticket": ticket,
        "search_results": search_results,
        "answer": answer,
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
    evidence: EvidenceAssessment | None = None,
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
        # === 情境五 self-correction 證據評估的可觀測欄位 ===
        "evidence_sufficient": evidence.sufficient if evidence else None,
        "evidence_confidence": evidence.confidence if evidence else None,
        "evidence_hit_count": evidence.hit_count if evidence else None,
        "evidence_top_score": evidence.top_score if evidence else None,
        "evidence_coverage": evidence.coverage if evidence else None,
        "evidence_missing_terms": evidence.missing_terms if evidence else None,
        "evidence_reason": evidence.reason if evidence else None,
        "evidence_judge_used": evidence.judge_used if evidence else None,
    }
    return log


def add_user_message(content: str, documents: list[dict[str, Any]]) -> None:
    started_at = time.perf_counter()
    conversation_state = get_conversation_state()
    route_decision = route_user_request(content, conversation_state)
    results: list[dict[str, Any]] = []
    ticket: HumanReviewTicket | None = None
    sandbox_result: DataOpsSandboxResult | None = None
    evidence: EvidenceAssessment | None = None

    if route_decision.route_status == "search":
        search_query = content
        previous_user_query = conversation_state.get("previous_user_query", "")
        if previous_user_query and route_decision.intent_summary.startswith("延續前一題"):
            search_query = f"{previous_user_query} {content}"
        results = search_knowledge_base(search_query, documents)

        # === 情境五 Self-Correction Loop ===
        # 檢索『之後』顯式評估證據強度，不足就推翻初判路由（observe → decide → act differently）
        config = load_llm_config()
        evidence = evaluate_evidence(
            search_query,
            results,
            llm_mode=config["llm_mode"],
            api_key=config["gemini_api_key"],
            model=config["gemma_model"],
        )

        if not evidence.sufficient:
            route_decision = build_low_confidence_route(route_decision, evidence)
            hitl_result = generate_draft_and_escalate_skill(
                content, route_decision, documents, low_confidence=True, evidence=evidence,
            )
            ticket = hitl_result["ticket"]
            results = hitl_result["search_results"]
            answer_result = {
                "answer": hitl_result["answer"],
                "llm_mode": hitl_result["llm_mode"],
                "model": hitl_result["model"],
                "fallback_used": True,  # 由 search 降級為 escalate，標示 fallback
                "error": hitl_result["error"],
            }
            action_status = "low_confidence_escalated"
        else:
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
    badge_label, badge_tone = build_status_badge(
        route_decision.route_status,
        action_status,
        route_decision.risk_type,
    )
    assistant_message["status_badge"] = {"label": badge_label, "tone": badge_tone}
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
        evidence,
    )


def render_log_panel(last_log: dict[str, Any]) -> None:
    json_text = json.dumps(last_log, ensure_ascii=False, indent=2)

    render_eyebrow("Governance Trace · 決策摘要")

    def pill(label: str, value: Any, variant: str = "") -> str:
        cls = f"gc-pill gc-pill--{variant}" if variant else "gc-pill"
        return f'<span class="{cls}">{html_escape(label)} <b>{html_escape(value)}</b></span>'

    risk_type = last_log.get("risk_type")
    risk_variant = "rose" if risk_type in {"System Modification", "Low Confidence"} else (
        "gold" if risk_type in {"Guarantee/Commitment", "Commercial/Pricing"} else "green"
    )
    pills = "".join(
        [
            pill("route", last_log.get("route_status")),
            pill("tier", last_log.get("permission_tier")),
            pill("risk", risk_type, risk_variant),
            pill("latency", f"{last_log.get('latency_ms')}ms"),
            pill("fallback", last_log.get("fallback_used"),
                 "gold" if last_log.get("fallback_used") else ""),
        ]
    )

    def cline(tag: str, tag_class: str, text: str) -> str:
        return (
            f'<div class="gc-cline"><span class="gc-cline__tag gc-cline__tag--{tag_class}">{tag}</span>'
            f'<span class="gc-cline__txt">{text}</span></div>'
        )

    def field(key: str, value: Any) -> str:
        return f'<em>{html_escape(key)}=</em>{html_escape(value)}'

    lines = [
        cline("ROUTE", "route", html_escape(last_log.get("intent_summary"))),
        cline("PLAN", "plan", field("selected_tool", last_log.get("selected_tool"))),
        cline("GUARD", "guard",
              field("tier", last_log.get("permission_tier")) + "&nbsp;&nbsp;"
              + field("risk", last_log.get("risk_type"))),
        cline("GUARD", "guard", html_escape(last_log.get("risk_reason"))),
        cline("ACTION", "action",
              field("approval_required", last_log.get("approval_required")) + "&nbsp;&nbsp;"
              + field("action_status", last_log.get("action_status"))),
        cline("PERF", "perf",
              field("model", last_log.get("model")) + "&nbsp;&nbsp;"
              + field("latency_ms", last_log.get("latency_ms")) + "&nbsp;&nbsp;"
              + field("fallback_used", last_log.get("fallback_used"))),
    ]

    if last_log.get("evidence_sufficient") is not None:
        lines.append(
            cline("EVIDENCE", "evidence",
                  field("sufficient", last_log.get("evidence_sufficient")) + "&nbsp;&nbsp;"
                  + field("coverage", last_log.get("evidence_coverage")) + "&nbsp;&nbsp;"
                  + field("top_score", last_log.get("evidence_top_score")))
        )
        lines.append(cline("EVIDENCE", "evidence", html_escape(last_log.get("evidence_reason"))))

    if last_log.get("ticket_id"):
        lines.append(
            cline("HITL", "hitl",
                  field("ticket_id", last_log.get("ticket_id")) + "&nbsp;&nbsp;"
                  + field("draft_type", last_log.get("draft_type")))
        )

    if last_log.get("sandbox_id"):
        lines.append(
            cline("SANDBOX", "sandbox",
                  field("sandbox_id", last_log.get("sandbox_id")) + "&nbsp;&nbsp;"
                  + field("sql_validation_status", last_log.get("sql_validation_status")))
        )

    st.markdown(
        f'<div class="gc-console"><div class="gc-console__pills">{pills}</div>{"".join(lines)}</div>',
        unsafe_allow_html=True,
    )

    render_eyebrow("Engineering Metrics · JSON")
    st.code(json_text, language="json")
    st.download_button(
        label="下載 last_log.json",
        data=json_text,
        file_name="certification_workflow_agent_last_log.json",
        mime="application/json",
        use_container_width=True,
    )

    with st.expander("Raw st.json view", expanded=False):
        st.json(last_log)


def render_system_status() -> None:
    llm_config = load_llm_config()
    evidence_config = load_evidence_config()
    last_log = st.session_state.get("last_log", {})
    llm_mode = llm_config["llm_mode"]
    model = "mock" if llm_mode == "mock" else llm_config["gemma_model"]
    fallback_used = last_log.get("fallback_used", "N/A")

    render_eyebrow("System Status")
    st.text(f"llm_mode: {llm_mode}")
    st.text(f"model: {model}")
    st.text(f"evidence_judge: {'enabled' if evidence_config['use_llm_judge'] else 'disabled'}")
    st.text(f"fallback_used: {fallback_used}")


def render_sidebar(documents: list[dict[str, Any]], load_error: str | None) -> None:
    with st.sidebar:
        st.markdown(
            '<div class="gc-side-brand"><span class="gc-side-brand__mark">CW</span>'
            f'<span class="gc-side-brand__name">{PROJECT_NAME}</span></div>',
            unsafe_allow_html=True,
        )
        render_eyebrow("Control Panel")

        info_cards = [
            ("ROUTING", "受控路由：先判定意圖與權限，再決定檢索、人工審查或 sandbox。", "navy"),
            ("HUMAN REVIEW", "人工審查：高風險承諾不直接回答，改產生審查 ticket 與澄清信草稿。", "gold"),
            ("DATA OPS", "資料修改只產生 SQL dry-run preview，不寫入 production。", "rose"),
            ("EVIDENCE GATE", "證據不足時自動升級為 Low Confidence 人工審查。", "green"),
        ]
        for key, value, accent in info_cards:
            st.markdown(
                f'<div class="gc-info-card gc-info-card--{accent}">'
                f'<div class="gc-info-card__k">{html_escape(key)}</div>'
                f'<div class="gc-info-card__v">{html_escape(value)}</div></div>',
                unsafe_allow_html=True,
            )

        st.divider()
        render_system_status()

        st.divider()
        render_eyebrow("Knowledge Base")
        if load_error:
            st.warning(load_error)
        else:
            st.metric("已載入知識文件", len(documents))
            for document in documents:
                tag, _purpose, accent = classify_document(document["filename"])
                st.markdown(
                    f'<div class="gc-kb-mini"><span class="gc-tag gc-tag--{accent}">{tag}</span>'
                    f'<span class="gc-kb-mini__name">{html_escape(document["title"])}</span></div>',
                    unsafe_allow_html=True,
                )

        st.divider()
        render_eyebrow("受控測試情境")
        for index, question in enumerate(TEST_QUESTIONS, start=1):
            if st.button(f"{index}. {question}", key=f"test_question_{index}", use_container_width=True):
                add_user_message(question, documents)
                st.rerun()

        st.divider()
        if st.button("清除對話", key="clear_conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_log = MOCK_LOG.copy()
            st.rerun()


def render_document_preview(documents: list[dict[str, Any]], load_error: str | None) -> None:
    render_eyebrow("Knowledge Assets")
    st.markdown('<div class="gc-section-title">知識庫文件</div>', unsafe_allow_html=True)
    st.caption("三份本地 Markdown 文件，供 RAG、Evidence Gate 與人工審查草稿引用。")

    if load_error:
        st.error(load_error)
        return

    for document in documents:
        tag, purpose, accent = classify_document(document["filename"])
        st.markdown(
            f'<div class="gc-kb-card gc-kb-card--{accent}">'
            f'<div class="gc-kb-card__head"><span class="gc-tag gc-tag--{accent}">{tag}</span>'
            f'<span class="gc-kb-card__title">{html_escape(document["title"])}</span></div>'
            f'<div class="gc-kb-card__file">{html_escape(document["filename"])}</div>'
            f'<div class="gc-kb-card__purpose">{html_escape(purpose)}</div></div>',
            unsafe_allow_html=True,
        )
        with st.expander("原始 Markdown 內容", expanded=False):
            st.caption(f"檔案路徑：{document['path']}")
            st.text_area(
                label="原始 Markdown 內容",
                value=document["content"],
                height=200,
                disabled=True,
                key=f"raw_markdown_{document['doc_id']}",
                label_visibility="collapsed",
            )


def render_hitl_ticket(ticket: dict[str, Any]) -> None:
    is_low_confidence = ticket.get("risk_type") == "Low Confidence"
    accent = "lowconf" if is_low_confidence else "gold"

    with st.container(border=True):
        render_gate_marker(accent)
        if is_low_confidence:
            render_gate_banner(
                "EVIDENCE GATE · LOW CONFIDENCE", "人工審查佇列（知識庫依據不足）", "lowconf"
            )
        else:
            render_gate_banner(
                "HITL GATE · PENDING HUMAN REVIEW", "人工審查佇列（Tier 1）", "gold"
            )

        render_kv_grid(
            [
                ("ticket_id", ticket["ticket_id"]),
                ("risk_type", ticket["risk_type"]),
                ("suggested_owner", ticket["suggested_owner"]),
                ("status", ticket["status"]),
            ]
        )

        if is_low_confidence:
            render_eyebrow("Evidence Gate")
            render_kv_grid([("evidence_sufficient", "false")])
            missing_terms = extract_missing_terms(ticket["risk_reason"])
            if missing_terms:
                chips = "".join(f'<span class="gc-term">{html_escape(term)}</span>' for term in missing_terms)
                st.markdown(
                    f'<div class="gc-eyebrow">missing_terms</div><div class="gc-terms">{chips}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div class="gc-note">evidence_reason：{html_escape(ticket["risk_reason"])}</div>',
                unsafe_allow_html=True,
            )
            draft_label = "知識庫不足通知草稿"
        else:
            st.markdown(
                f'<div class="gc-note">risk_reason：{html_escape(ticket["risk_reason"])}</div>',
                unsafe_allow_html=True,
            )
            draft_label = "商務澄清信草稿"

        render_eyebrow(f"Draft for Review · {draft_label}")
        st.text_area(
            draft_label,
            value=ticket["draft_preview"],
            height=320,
            key=f"draft_preview_{ticket['ticket_id']}",
            label_visibility="collapsed",
        )

        render_eyebrow("Retrieved Evidence")
        if not ticket["retrieved_docs"]:
            st.caption("無有效命中文件。")
        for result in ticket["retrieved_docs"]:
            st.markdown(
                f'<div class="gc-evi"><b>{html_escape(result["citation"])}</b> · '
                f'{html_escape(result["section_title"])} · score={html_escape(result["score"])}</div>',
                unsafe_allow_html=True,
            )


def render_data_ops_sandbox(sandbox_result: dict[str, Any]) -> None:
    with st.container(border=True):
        render_gate_marker("rose")
        render_gate_banner("SANDBOX GATE · TIER 3", "Data Ops Dry-run Preview", "rose")

        render_kv_grid(
            [
                ("sandbox_id", sandbox_result["sandbox_id"]),
                ("permission_tier", sandbox_result["permission_tier"]),
                ("current_action_tier", sandbox_result["current_action_tier"]),
                ("sql_validation_status", sandbox_result["sql_validation_status"]),
            ]
        )
        st.markdown(
            '<div class="gc-note">Production write blocked · Dry-run only · 未連接或寫入任何 production database。</div>',
            unsafe_allow_html=True,
        )

        render_eyebrow("Generated SQL · Dry-run")
        st.code(sandbox_result["generated_sql"], language="sql")

        render_eyebrow("Before")
        st.table(sandbox_result["before_rows"])
        render_eyebrow("After")
        st.table(sandbox_result["after_rows"])

        st.markdown(
            '<div class="gc-note">此結果僅為 dry-run preview，需主管核准後才可由授權人員處理。</div>',
            unsafe_allow_html=True,
        )


def render_chat(documents: list[dict[str, Any]]) -> None:
    render_eyebrow("Review Workbench")
    st.markdown('<div class="gc-section-title">企業知識助理 · 對話工作台</div>', unsafe_allow_html=True)
    st.caption(
        "每則回覆都保留治理語意：已引用來源 / 需人工審查 / 資料不足轉人工 / 禁止 production 寫入 / 零檢索。"
    )

    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(
                f'<div class="gc-msg gc-msg--user"><div class="gc-msg__label">USER</div>'
                f'<div class="gc-msg__body">{html_escape(message["content"])}</div></div>',
                unsafe_allow_html=True,
            )
            continue

        badge = message.get("status_badge") or {}
        tone = badge.get("tone", "neutral")
        badge_html = build_badge_html(badge["label"], tone) if badge.get("label") else ""
        st.markdown(
            f'<div class="gc-msg gc-msg--assistant gc-tone-{tone}">'
            f'<div class="gc-msg__head"><span class="gc-msg__label">{PROJECT_NAME}</span>{badge_html}</div>'
            f'<div class="gc-msg__body">{html_escape(message["content"])}</div></div>',
            unsafe_allow_html=True,
        )
        if message.get("hitl_ticket"):
            render_hitl_ticket(message["hitl_ticket"])
        if message.get("sandbox_result"):
            render_data_ops_sandbox(message["sandbox_result"])

    prompt = st.chat_input("輸入產品認證或 scoping 問題（系統會先做受控路由）")
    if prompt:
        add_user_message(prompt, documents)
        st.rerun()


def main() -> None:
    st.set_page_config(page_title=PROJECT_NAME, page_icon="G", layout="wide")
    initialize_state()
    inject_custom_css()

    documents, load_error = load_markdown_documents()

    render_hero()
    render_sidebar(documents, load_error)

    tab_console, tab_audit, tab_kb = st.tabs(["對話工作台", "Audit Log", "知識庫文件"])
    with tab_console:
        render_chat(documents)
    with tab_audit:
        render_log_panel(st.session_state.last_log)
    with tab_kb:
        render_document_preview(documents, load_error)


if __name__ == "__main__":
    main()
