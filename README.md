# Governed Agent Workflow Demo

> Streamlit prototype for a governed enterprise AI workflow with local RAG, HITL escalation, a data-operations sandbox, permission tiers, an Evidence Gate, and an audit view.

This demo supports an electronic-product certification workflow while keeping every request inside explicit evidence, permission, and risk boundaries. Its behavior is defined by [`app.py`](app.py); [`DEMO_SPEC_v2.1.md`](DEMO_SPEC_v2.1.md) is the only active demo specification.

## Disclaimer

This repository is a prototype using simulated Markdown documents, records, tickets, and workflows. It does not connect to a production database, write real records, send external messages, or create real approval tasks. It does not produce formal compliance, legal, commercial, certification, pricing, or operational conclusions.

## Implemented Behavior

- A deterministic rule-based intent router selects one of four routes.
- Local Markdown sections are scored with transparent keyword-based retrieval and returned with citations.
- The Evidence Gate evaluates hit count, top score, and distinctive-term coverage after retrieval.
- Insufficient evidence overrides an initial `search` route and creates a Low Confidence HITL ticket.
- High-risk commitments create a review ticket and a draft that must be reviewed before use.
- Data-modification intent is blocked from production and converted into a tightly constrained SQL dry-run preview.
- Out-of-scope requests perform no knowledge-base retrieval.
- Streamlit session state keeps the conversation and the most recent audit log.
- Mock mode is deterministic; Gemma-backed answer and draft generation is optional.

## System Architecture

```mermaid
flowchart TD
    classDef userNode   fill:#E8F4FD,stroke:#0E3A5B,color:#0E3A5B,font-weight:bold
    classDef routeNode  fill:#EDF7ED,stroke:#2F7D4A,color:#1A5C35
    classDef execNode   fill:#FFFBF0,stroke:#B68A3D,color:#7A5C25
    classDef knowNode   fill:#EEF2FF,stroke:#4A6FA5,color:#2A3F6A
    classDef govNode    fill:#FFF0F0,stroke:#A85F5F,color:#7A3535

    U([User]):::userNode --> UI[Streamlit UI]:::userNode

    subgraph ROUTE ["Routing & Guardrails"]
        direction LR
        IR[Intent Router]:::routeNode
        OG[Out-of-scope Guardrail]:::routeNode
    end

    subgraph EXEC ["Execution Paths"]
        direction LR
        RAG[RAG + Evidence Gate]:::execNode
        HITL[HITL Draft Gate]:::execNode
        SBX[Data Ops Sandbox]:::execNode
    end

    subgraph KNOW ["Knowledge & Inference"]
        direction LR
        KB[(Markdown KB)]:::knowNode
        LLM[LLM / Mock Fallback]:::knowNode
    end

    subgraph GOV ["Governance"]
        direction LR
        AL[Audit Log]:::govNode
        MT[Engineering Metrics]:::govNode
    end

    UI --> IR
    IR --> OG
    IR --> RAG
    IR --> HITL
    IR --> SBX
    RAG --> KB
    RAG --> LLM
    HITL --> LLM
    RAG -- "low confidence" --> HITL
    OG --> AL
    RAG --> AL
    HITL --> AL
    SBX --> AL
    AL --> MT
```

The intent router is deterministic in the current implementation. The optional LLM is used for grounded answers, review drafts, and an opt-in evidence judge.

## Governed Request Flow

```mermaid
flowchart TD
    classDef input    fill:#E8F4FD,stroke:#0E3A5B,color:#0E3A5B
    classDef gate     fill:#FFFBF0,stroke:#B68A3D,color:#7A5C25
    classDef answer   fill:#EDF7ED,stroke:#2F7D4A,color:#1A5C35
    classDef escalate fill:#FFF0F0,stroke:#A85F5F,color:#7A3535
    classDef audit    fill:#F5F0FF,stroke:#7A5A9A,color:#4A2A7A

    Q([User Query]):::input --> RU["route_user_request()"]:::input
    RU --> RD{Route?}:::gate
    RD -- "search"               --> RS[RAG Search]:::answer
    RD -- "draft + escalate"     --> HG[HITL Gate]:::escalate
    RD -- "data_ops_dry_run"     --> DS[Sandbox Dry-run]:::answer
    RD -- "out_of_scope"         --> OS[Guardrail Response]:::escalate
    RS --> EG{Evidence Gate}:::gate
    EG -- "✓ sufficient"         --> AN[Cited Answer]:::answer
    EG -- "✗ low confidence"     --> HG
    HG --> ES[Draft + Escalation Ticket]:::escalate
    DS --> DP[SQL Before / After Preview]:::answer
    AN  --> AL[(Audit Log)]:::audit
    ES  --> AL
    DP  --> AL
    OS  --> AL
```

## Routes And Guardrails

| Route | Permission / risk | Actual behavior |
|---|---|---|
| `search` | `Tier 0` / `None` | Searches local Markdown, runs the Evidence Gate, then returns up to three cited points if evidence is sufficient. |
| `generate_draft_and_escalate` | `Tier 1` / commitment, pricing, formal conclusion, or Low Confidence | Retrieves supporting material, creates a simulated `Pending Human Review` ticket, and displays a review draft. |
| `data_ops_dry_run` | `Tier 3` intent / `System Modification` | Blocks production writes and displays a fixed fake-record SQL dry-run, validator status, Before/After tables, and a simulated approval queue. The preview action is labeled `current_action_tier=Tier 1`. |
| `out_of_scope` | `N/A` / `Out of Scope` | Returns a guardrail response with `retrieval_required=false` and no retrieval. |

The router checks system-modification terms first, followed by guarantees, commercial commitments, formal compliance conclusions, explicit out-of-scope terms, and general certification-domain signals. It does not use an LLM to choose a route.

## Evidence Gate

Every initial `search` runs a deterministic Evidence Gate. Evidence is sufficient only when at least one result exists, the top score reaches `EVIDENCE_SCORE_FLOOR`, and distinctive-term coverage reaches `EVIDENCE_COVERAGE_THRESHOLD`.

When evidence is insufficient, the gate overrides the route to `generate_draft_and_escalate`, sets `Tier 1` and `risk_type=Low Confidence`, creates a knowledge-gap draft, and records evidence fields in the audit log. The optional LLM judge can only make a deterministic pass stricter; it cannot turn a deterministic failure into a pass.

## Demo Scenarios

Use the Chinese inputs below because they are the app's built-in acceptance scenarios.

| # | 中文原始輸入 | Expected route / result | Expected UI |
|---|---|---|---|
| 1 | `客戶有一款藍牙耳機要出口到歐洲，初步 scoping 要看哪些指令？` | `search` / `Tier 0` / `action_status=answered` | Cited answer and `evidence_sufficient=true`. |
| 2 | `可以保證這個產品一定會通過 FCC 嗎？` | `generate_draft_and_escalate` / `Tier 1` / `Guarantee/Commitment` | HITL Gate, review ticket, and 商務澄清信草稿. |
| 3 | `請幫我直接修改內部系統，把審核狀態改成通過。` | `data_ops_dry_run` / `Tier 3` intent / dry-run only | Sandbox Gate, validated SQL, Before/After preview, and no production write. |
| 4 | `請幫我推薦今天晚餐。` | `out_of_scope` / no retrieval | 零檢索 badge and `retrieved_docs=[]`. |
| 5 | `這款耳機適用某個特殊衛星頻段的日本法規嗎？` | Initial `search`, then Evidence Gate override to `generate_draft_and_escalate` / `Tier 1` / `Low Confidence` | Evidence warning, knowledge-gap draft, and Low Confidence ticket. |
| 6 | After scenario 1, ask `那如果是去美國呢？` | `conversation_state` carry-forward; `search` / `Tier 0` when evidence passes | The previous user query is prepended for retrieval and the intent summary states that the request continues the prior question. |

See [`docs/demo_guide.md`](docs/demo_guide.md) for a neutral runbook containing only inputs, expected routes, expected UI, and demonstration points.

## UI And State

- **Sidebar:** system status, loaded knowledge files, six scenario buttons, and a clear-conversation button.
- **對話工作台:** conversation history, status badges, HITL ticket panels, and sandbox previews.
- **Audit Log:** Governance Trace, Engineering Metrics JSON, raw JSON view, and a download button for the latest log.
- **知識庫文件:** the three local Markdown files and expandable raw-content previews.
- **Session state:** stores the current conversation and only the latest audit log. Clearing the conversation resets both; there is no durable persistence.
- **Conversation carry-forward:** follow-ups beginning with `那`, `如果`, `那如果`, `改成`, or `換成` reuse the immediately preceding user query for retrieval.

## Setup And Run

Python and `pip` are required. A `.env` file is optional in the default mock mode.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The default Streamlit URL is `http://localhost:8501`. On Windows, `start_demo.bat` runs `streamlit run app.py` from the repository directory and opens that URL; it assumes `streamlit` is available on `PATH`.

## Environment Variables

Copy `.env.example` to `.env` only when you need to change the defaults.

```dotenv
LLM_MODE=mock
GEMINI_API_KEY=
GEMMA_MODEL=gemma-4-26b-a4b-it
USE_LLM_EVIDENCE_JUDGE=false
EVIDENCE_SCORE_FLOOR=3
EVIDENCE_COVERAGE_THRESHOLD=0.5
```

| Variable | Implementation behavior |
|---|---|
| `LLM_MODE=mock` | Uses deterministic cited answers and deterministic review templates; no API key is required. |
| `LLM_MODE=gemma` | Calls the configured model. A grounded-answer failure is shown as an error; a HITL draft failure falls back to the deterministic template. |
| `LLM_MODE=auto` | Calls the configured model and falls back to deterministic behavior when generation fails. |
| `GEMINI_API_KEY` | Required for model calls and for the optional LLM evidence judge. |
| `GEMMA_MODEL` | Model name passed to `google-genai`. |
| `USE_LLM_EVIDENCE_JUDGE` | Enables the judge only when true, the mode is `gemma` or `auto`, and an API key exists. |
| `EVIDENCE_SCORE_FLOOR` | Non-negative integer top-score threshold; invalid values fall back to the code default. |
| `EVIDENCE_COVERAGE_THRESHOLD` | Coverage threshold clamped to `0.0`-`1.0`; invalid values fall back to the code default. |

Keep `.env` and `.streamlit/secrets.toml` local.

## Repository Structure

```text
.
|-- app.py
|-- data/docs/
|-- DEMO_SPEC_v2.1.md
|-- docs/demo_guide.md
|-- requirements.txt
|-- .env.example
`-- start_demo.bat
```

## Known Limitations

- Routing is deterministic keyword matching, not semantic or model-based intent classification.
- Retrieval is local keyword scoring over Markdown sections, not vector or hybrid search.
- The knowledge base contains only three simulated documents.
- HITL tickets, approval queues, messages, and audit logs are simulated and not persisted.
- Only the most recent audit log is retained in Streamlit session state.
- The sandbox validator accepts only one fixed update to fake record `DEMO-001`; it never executes SQL.
- Conversation carry-forward uses only the immediately preceding user query and a small set of follow-up prefixes.
- There is no production authentication, authorization, tenant isolation, monitoring, or external-system integration.
