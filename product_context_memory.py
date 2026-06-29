"""Product / certification multi-turn context memory.

本模組是 governed agent workflow demo 的「多輪記憶機制」核心。它把原本 app.py
裡只看「上一句」的 carry-forward，升級成一個結構化、可稽核、fail-safe 的
``ProductConversationMemory``：

* active_request_summary  目前任務骨架（例如 "AlphaBuds X1 EU certification scoping"）
* active_context_deltas   後續 follow-up 的增量（例如 "switched to BetaBuds X2"）
* active_products         對話中觸及的產品（去重、有界）
* active_regions          對話中觸及的區域（EU / US / Japan）
* active_spec_fields      技術維度（Wi-Fi / Bluetooth / no wireless / proprietary ...）
* last_retrieved_docs     最近檢索 / 引用過的文件（LRU、去重、有界）
* recent_turns            最近幾輪的精簡紀錄（有界 ring buffer）

設計哲學（與 tests/product_context_memory_test_plan.md 的 scope boundary 對齊）：

1. **Deterministic over learned.** 這是一個「受治理」的 workflow，每個路由決策都必須
   可重現、可解釋、可在 mock 模式下重播；因此採規則式 policy router，而非 RL /
   learned routing / opaque personalization。每個 turn 都產生一段 rationale 供稽核。
2. **Fail-safe boundaries.** 任何「保證一定通過 / 對外承諾」的請求一律走 refusal /
   escalation，且 memory 內部永遠不會合成或回放禁語（例如「一定通過」）。
3. **Bounded + deduplicated.** 記憶是有界的：產品、區域、文件、deltas、turns 都有上限，
   避免長對話無限膨脹造成延遲與 context drift。
4. **No heavy dependencies.** 純標準函式庫，可被單元測試直接 import，不依賴 streamlit。

這個物件被設計成 retrieval/路由的「事實來源」：把結構化欄位直接餵進
``compose_retrieval_query`` 與 citation recall，避免短 follow-up（"那日本呢？"）
把第一輪建立的產品 / 認證脈絡丟掉。
"""

from __future__ import annotations

import re
from collections import deque
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# 1. Entity catalog（產品 / 區域 / 規格 / 意圖訊號）
#    全部以 (canonical, [aliases/regex]) 表示，方便稽核與擴充。
# ---------------------------------------------------------------------------

# 產品：canonical 名稱 -> 觸發詞（小寫，子字串比對；含中英、產品代號）。
PRODUCT_CATALOG: list[tuple[str, tuple[str, ...]]] = [
    ("AlphaBuds X1", ("alphabuds x1", "alphabuds", "product a", "產品a", "產品 a")),
    ("BetaBuds X2", ("betabuds x2", "betabuds", "product b", "產品b", "產品 b")),
    ("GammaHub C1", ("gammahub c1", "gammahub", "product c", "產品c", "產品 c")),
    ("DeltaCam D4", ("deltacam d4", "deltacam", "product d", "產品d", "產品 d")),
]

# 區域：canonical -> regex（拉丁字母用 word boundary，避免 "us" 命中 "status"）。
REGION_CATALOG: list[tuple[str, str]] = [
    ("EU", r"\beu\b|\beuropean?\b|歐洲|歐盟"),
    ("US", r"\bus\b|\bu\.s\.?\b|\busa\b|\bunited states\b|美國|美国"),
    ("Japan", r"\bjapan\b|\bjp\b|日本"),
]

# 規格 / 技術維度：canonical -> regex。
SPEC_CATALOG: list[tuple[str, str]] = [
    # no wireless 必須先於 Bluetooth/Wi-Fi 檢查，但這裡每條獨立比對，順序只影響輸出排序。
    ("no wireless", r"沒有無線|沒有\s*radio|無\s*radio\s*module|no\s+radio|no\s+wireless|沒有無線模組|沒有無線功能"),
    ("Wi-Fi", r"wi-?fi|wlan|無線網路"),
    ("Bluetooth", r"bluetooth|藍牙|\bble\b"),
    ("proprietary radio mode", r"proprietary|專有|私有.*(無線|頻段|mode)"),
    ("frequency band", r"頻段|頻率|frequency|\bband\b|\d\s*ghz|ghz"),
    ("battery", r"電池|battery|續航"),
    ("ports/interfaces", r"連接埠|\bport\b|usb-?c|hdmi|ethernet|docking"),
    ("certification", r"認證|certification|scoping|合規|compliance"),
]

# 被視為「無線電 radio 類型」的規格（用於判斷 multi-radio 複雜度）。
RADIO_SPEC_FIELDS = {"Wi-Fi", "Bluetooth", "proprietary radio mode"}

# 「certification」太通用（幾乎每題都有），不能當作「引入新任務」的判別訊號，
# 否則 "那 BetaBuds X2 的認證呢？" 這種純產品 follow-up 會被誤判成全新任務而丟失區域脈絡。
GENERIC_SPEC_FIELDS = {"certification"}

# 各產品已知的 radio profile（取自 data/docs 規格表，用於偵測使用者宣稱與文件衝突）。
# 空集合代表 negative-control（無 radio）產品。
PRODUCT_RADIO_PROFILE: dict[str, set[str]] = {
    "AlphaBuds X1": {"Bluetooth"},
    "BetaBuds X2": {"Bluetooth", "proprietary radio mode"},
    "GammaHub C1": set(),
    "DeltaCam D4": {"Wi-Fi", "Bluetooth"},
}

# 可被「宣稱」的 radio 類型 -> 比對 regex。
RADIO_CLAIM_PATTERNS: list[tuple[str, str]] = [
    ("Wi-Fi", r"wi-?fi|wlan"),
    ("Bluetooth", r"bluetooth|藍牙|\bble\b"),
    ("proprietary radio mode", r"proprietary|專有.*(無線|頻段|mode)"),
]

# 「肯定擁有某 radio」的句型前綴；用於和產品 profile 對照偵測矛盾。
RADIO_ASSERT_PREFIX = r"(有|具備|具有|支援|搭載|內建|附帶?|帶有|其實有|has|have|with|supports?|comes with)"
# 否定句型守門：出現則不視為「宣稱擁有」，避免把 "沒有無線" 誤判為矛盾。
NEGATION_REGEX = r"沒有|不需要|不用|未列|without|\bno\b|\bnot\b|does not|doesn't"
# 疑問句型守門：「有 Wi-Fi 嗎？」是提問而非宣稱，應交給 RAG 依文件回答（答案自然會更正前提），
# 不該升級成 spec conflict。只有『陳述句宣稱』與文件衝突時才升級。
INTERROGATIVE_REGEX = r"嗎|呢|是否|有沒有|有無|\?|？|do(?:es)?\s+\w+\s+have|is there|are there"

# 意圖訊號。
GUARANTEE_REGEX = r"保證|一定會通過|一定通過|一定可以過|一定會過|一定過|包過|穩過|承諾.{0,6}通過|對客戶.{0,8}通過|definitely pass|guarantee.*pass"
RECALL_REGEX = r"剛才|先前|稍早|參考了哪些|參考哪些|引用了哪些|引用哪些|哪些文件|看了哪些文件|用了哪些文件|which (docs|documents)|what (docs|documents).*(refer|use|cite)|earlier.*document"
FOLLOWUP_REGEX = r"^\s*(那|如果|那如果|改成|換成|又如果)|那.*呢|如果.*呢|改成.*呢|換成.*呢|^\s*what if|^\s*what about|^\s*how about|^\s*and (for|in|what about)"
OUT_OF_SCOPE_REGEX = r"晚餐|午餐|早餐|宵夜|推薦餐廳|餐廳推薦|天氣|笑話|電影推薦|股票|樂透|今天.*穿"

# 結構化任務骨架使用的固定核心關鍵詞（英文，確保 retrieval 訊號穩定）。
TASK_CORE = "certification scoping"
TASK_CORE_COMPLEX = "complex multi-radio certification scoping"

# 路由分組：供 app 端判斷是否該把被誤判的 follow-up 搶救回受控檢索。
CONTINUATION_SEARCH_ROUTES = frozenset(
    {"product_followup", "region_followup", "spec_followup", "followup"}
)
RECALL_ROUTE = "citation_recall"
ESCALATION_ROUTES = frozenset({"generate_draft_and_escalate", "escalate_conflict"})


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _ordered_unique_extend(base: list[str], incoming: Iterable[str], limit: int) -> list[str]:
    """把 incoming 併入 base，保持插入順序、去重，並保留最後 ``limit`` 個（LRU 風格）。"""
    result = list(base)
    for item in incoming:
        if item in result:
            result.remove(item)
        result.append(item)
    if limit > 0 and len(result) > limit:
        result = result[-limit:]
    return result


def detect_products(text: str) -> list[str]:
    lowered = (text or "").lower()
    found: list[str] = []
    for canonical, aliases in PRODUCT_CATALOG:
        if any(alias in lowered for alias in aliases):
            found.append(canonical)
    return found


def detect_regions(text: str) -> list[str]:
    lowered = (text or "").lower()
    found: list[str] = []
    for canonical, pattern in REGION_CATALOG:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            found.append(canonical)
    return found


def detect_spec_fields(text: str) -> list[str]:
    lowered = (text or "").lower()
    found: list[str] = []
    for canonical, pattern in SPEC_CATALOG:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            found.append(canonical)
    return found


def detect_guarantee(text: str) -> bool:
    return re.search(GUARANTEE_REGEX, text or "", flags=re.IGNORECASE) is not None


def detect_recall(text: str) -> bool:
    return re.search(RECALL_REGEX, text or "", flags=re.IGNORECASE) is not None


def detect_followup_marker(text: str) -> bool:
    return re.search(FOLLOWUP_REGEX, (text or "").strip(), flags=re.IGNORECASE) is not None


def detect_out_of_scope(text: str) -> bool:
    return re.search(OUT_OF_SCOPE_REGEX, text or "", flags=re.IGNORECASE) is not None


def detect_claimed_radios(text: str) -> set[str]:
    """偵測使用者『肯定宣稱產品擁有』的 radio 類型（排除否定 / 詢問句）。"""
    body = text or ""
    if re.search(NEGATION_REGEX, body, flags=re.IGNORECASE):
        return set()
    if re.search(INTERROGATIVE_REGEX, body, flags=re.IGNORECASE):
        return set()
    claimed: set[str] = set()
    for canonical, radio_pattern in RADIO_CLAIM_PATTERNS:
        if re.search(RADIO_ASSERT_PREFIX + r".{0,6}(" + radio_pattern + r")", body, flags=re.IGNORECASE):
            claimed.add(canonical)
    return claimed


def detect_spec_conflict(text: str, products: list[str]) -> tuple[bool, list[str]]:
    """若使用者宣稱某產品具備其 profile 中沒有的 radio，視為規格矛盾，需升級人工審查。

    回傳 (是否矛盾, 衝突描述清單)。Fail-safe：只在『肯定宣稱』且與已知 profile 衝突時觸發。
    """
    claimed = detect_claimed_radios(text)
    if not claimed or not products:
        return False, []
    conflicts: list[str] = []
    for product in products:
        if product not in PRODUCT_RADIO_PROFILE:
            continue
        profile = PRODUCT_RADIO_PROFILE[product]
        for radio in sorted(claimed):
            if radio not in profile:
                conflicts.append(f"{product} claimed {radio} but profile has no such radio")
    return bool(conflicts), conflicts


class ProductConversationMemory:
    """結構化、有界、可稽核的多輪產品 / 認證上下文記憶。

    主要 API（測試契約）：

    * ``update_from_turn(user_query, retrieved_docs=None) -> dict`` 觀察一輪並更新狀態，
      回傳當輪 snapshot（含 ``route`` 路由決策）。
    * ``compose_retrieval_query(current_query) -> str`` 用累積脈絡擴寫當前 query。
    * ``snapshot() / to_dict() / model_dump()`` 取得狀態的深拷貝。
    * ``to_debug_dict()`` 取得含 rationale 歷史與設定的稽核視圖。
    """

    def __init__(
        self,
        max_recent_turns: int = 6,
        max_context_deltas: int = 8,
        max_retrieved_docs: int = 8,
        max_active_products: int = 8,
        max_active_regions: int = 6,
        max_active_spec_fields: int = 12,
        **_ignored: Any,
    ) -> None:
        self.max_recent_turns = max(1, int(max_recent_turns))
        self.max_context_deltas = max(1, int(max_context_deltas))
        self.max_retrieved_docs = max(1, int(max_retrieved_docs))
        self.max_active_products = max(1, int(max_active_products))
        self.max_active_regions = max(1, int(max_active_regions))
        self.max_active_spec_fields = max(1, int(max_active_spec_fields))

        # --- 結構化狀態 ---
        self.active_products: list[str] = []
        self.active_regions: list[str] = []
        self.active_spec_fields: list[str] = []
        self.active_request_summary: str = ""
        self.active_context_deltas: deque[str] = deque(maxlen=self.max_context_deltas)
        self.last_retrieved_docs: list[str] = []
        self.recent_turns: deque[dict[str, Any]] = deque(maxlen=self.max_recent_turns)

        # --- 任務焦點（驅動 summary 重建）---
        self._primary_product: str | None = None
        self._primary_region: str | None = None
        self._task_complex: bool = False

        # --- 路由 / 稽核 ---
        self._turn_index: int = 0
        self._last_route: str = "idle"
        self._last_risk_type: str = "None"
        self._last_boundary_note: str = ""
        self._rationale_log: deque[dict[str, Any]] = deque(maxlen=max(self.max_recent_turns, 8))

    # ------------------------------------------------------------------
    # 觀察一輪
    # ------------------------------------------------------------------
    def update_from_turn(
        self,
        user_query: str,
        retrieved_docs: list[str] | None = None,
    ) -> dict[str, Any]:
        query = _normalize(user_query)
        retrieved_docs = [d for d in (retrieved_docs or []) if d]
        self._turn_index += 1

        signals = self._detect_signals(query)
        products = signals["products"]
        regions = signals["regions"]
        specs = signals["specs"]
        is_guarantee = signals["is_guarantee"]
        conflicts = signals["conflicts"]
        route, rationale = self._route_turn(**signals)

        # 文件累積：任何有提供 retrieved_docs 的 turn 都更新 LRU；
        # 沒提供（典型 recall / 純對話）就保持不變，確保 citation recall 穩定。
        if retrieved_docs:
            self.last_retrieved_docs = _ordered_unique_extend(
                self.last_retrieved_docs, retrieved_docs, self.max_retrieved_docs
            )

        # 依路由套用狀態變更。
        self._apply_route(
            route=route,
            query=query,
            products=products,
            regions=regions,
            specs=specs,
            is_guarantee=is_guarantee,
            conflicts=conflicts,
        )

        self._last_route = route
        self.recent_turns.append(
            {
                "turn": self._turn_index,
                "query": query,
                "route": route,
                "products": products,
                "regions": regions,
            }
        )
        self._rationale_log.append(
            {"turn": self._turn_index, "route": route, "rationale": rationale}
        )
        return self.snapshot()

    # 別名（契約 mixin 允許多種命名）。
    record_turn = update_from_turn
    add_turn = update_from_turn

    # ------------------------------------------------------------------
    # 訊號擷取 + 純函式 classify（不改狀態，供 app 在路由前 peek）
    # ------------------------------------------------------------------
    def _detect_signals(self, query: str) -> dict[str, Any]:
        products = detect_products(query)
        regions = detect_regions(query)
        specs = detect_spec_fields(query)
        has_conflict, conflicts = detect_spec_conflict(query, products)
        return {
            "query": query,
            "products": products,
            "regions": regions,
            "specs": specs,
            "is_guarantee": detect_guarantee(query),
            "is_recall": detect_recall(query),
            "is_out_of_scope": detect_out_of_scope(query) and not (products or regions or specs),
            "followup_marker": detect_followup_marker(query),
            "has_conflict": has_conflict,
            "conflicts": conflicts,
        }

    def classify(self, user_query: str) -> tuple[str, str]:
        """在『不改變狀態』的前提下，回傳此 turn 在目前記憶下會走的 (route, rationale)。

        app 端可用它來『搶救』被關鍵字路由誤判為 out_of_scope 的短 follow-up，
        並決定是否走 citation recall。"""
        return self._route_turn(**self._detect_signals(_normalize(user_query)))

    @property
    def has_active_task(self) -> bool:
        return bool(self.active_request_summary)

    # ------------------------------------------------------------------
    # Policy router（規則式、可解釋）
    # ------------------------------------------------------------------
    def _route_turn(
        self,
        *,
        query: str,
        products: list[str],
        regions: list[str],
        specs: list[str],
        is_guarantee: bool,
        is_recall: bool,
        is_out_of_scope: bool,
        followup_marker: bool,
        has_conflict: bool,
        conflicts: list[str],
    ) -> tuple[str, str]:
        # 1) 高風險承諾：永遠優先走拒絕 / 升級，fail-safe。
        if is_guarantee:
            return (
                "generate_draft_and_escalate",
                "偵測到保證 / 對外承諾語意（Guarantee/Commitment），依風險邊界 policy 升級人工審查，不直接回答。",
            )
        # 2) 規格矛盾：使用者宣稱的 radio 與產品 profile 衝突 -> 升級，不沿用前文假設。
        if has_conflict:
            return (
                "escalate_conflict",
                f"偵測到規格矛盾（與文件 profile 衝突）：{'; '.join(conflicts)}，升級人工審查。",
            )
        # 3) 引用回憶：使用既有 last_retrieved_docs，不改任務狀態。
        if is_recall:
            return (
                "citation_recall",
                "偵測到『剛才參考哪些文件』類問題，回放 last_retrieved_docs，不重建任務脈絡。",
            )
        # 4) 離題：不污染產品記憶。
        if is_out_of_scope:
            return ("out_of_scope", "偵測到非認證業務（生活 / 閒聊）語意，採零檢索且不更新產品脈絡。")

        new_products = [p for p in products if p != self._primary_product]
        has_new_product = bool(new_products)
        # 只有「實質技術維度」才算引入新任務的訊號；certification/scoping 太通用要排除。
        substantive_specs = [s for s in specs if s not in GENERIC_SPEC_FIELDS]

        # 5) 全新任務 vs follow-up 切換的判別：
        #    - 尚無任務骨架 -> 種下新任務。
        #    - 引入新產品「且」帶有實質規格維度，或不是 follow-up 句型 -> 視為新任務。
        #    - 否則（純產品 / 區域切換，且為 follow-up 句型）-> 保留任務、追加 delta。
        if not self.active_request_summary:
            return ("new_task", "首個實質產品 / 認證查詢，種下 active_request_summary。")
        if has_new_product and (substantive_specs or not followup_marker):
            return (
                "new_task",
                f"引入新產品 {new_products} 並帶有實質規格 {substantive_specs or '(獨立提問)'}，重建任務骨架（取代舊摘要）。",
            )
        if has_new_product:
            return ("product_followup", f"follow-up 產品切換到 {new_products}，保留任務與區域脈絡。")
        if regions:
            return ("region_followup", f"follow-up 區域切換到 {regions}，保留 active product。")
        if specs:
            return ("spec_followup", f"follow-up 補充規格維度 {specs}，沿用 active product 與 region。")
        return ("followup", "一般延續提問，沿用既有任務脈絡。")

    # ------------------------------------------------------------------
    # 套用狀態變更
    # ------------------------------------------------------------------
    def _apply_route(
        self,
        *,
        route: str,
        query: str,
        products: list[str],
        regions: list[str],
        specs: list[str],
        is_guarantee: bool,
        conflicts: list[str] | None = None,
    ) -> None:
        if route == "citation_recall":
            # 不改任務狀態；只記風險為 None。
            self._last_risk_type = "None"
            self._last_boundary_note = ""
            return

        if route == "generate_draft_and_escalate":
            # Fail-safe：標示風險邊界，但「不」把禁語寫入任何狀態欄位。
            self._last_risk_type = "Guarantee/Commitment"
            self._last_boundary_note = "不得對外保證認證結果（CE/RED/FCC/TELEC 的 pass/fail 需人工審查）。"
            self._push_delta("guarantee request → escalate to human review")
            return

        if route == "escalate_conflict":
            # 規格矛盾：記錄產品（讓後續可追蹤），標示風險，但不沿用前文 radio 假設、不重建任務。
            self._last_risk_type = "Spec Conflict"
            self._last_boundary_note = "使用者宣稱規格與文件 profile 衝突，不得直接回答，升級人工審查並要求補件。"
            if products:
                self.active_products = _ordered_unique_extend(
                    self.active_products, products, self.max_active_products
                )
            note = "; ".join(conflicts or []) or "spec conflict"
            self._push_delta(f"spec conflict → escalate ({note})")
            return

        if route == "out_of_scope":
            self._last_risk_type = "Out of Scope"
            self._last_boundary_note = "問題超出安規認證範疇，採零檢索。"
            return

        # 一般任務路徑：重置風險旗標。
        self._last_risk_type = "None"
        self._last_boundary_note = ""

        # 累積 active 集合（去重、有界）。
        if products:
            self.active_products = _ordered_unique_extend(
                self.active_products, products, self.max_active_products
            )
        if regions:
            self.active_regions = _ordered_unique_extend(
                self.active_regions, regions, self.max_active_regions
            )

        if route == "new_task":
            # 重建任務焦點：新產品成為 primary，spec 維度重置為本輪內容。
            if products:
                self._primary_product = products[-1]
            if regions:
                self._primary_region = regions[-1]
            self.active_spec_fields = _ordered_unique_extend(
                [], specs, self.max_active_spec_fields
            )
            self._task_complex = self._is_multi_radio(specs)
            self._rebuild_summary()
            self._push_delta(self._summarize_focus(prefix="new task"))
            return

        # follow-up 類路由：保留任務骨架，更新 primary 與 deltas。
        if specs:
            self.active_spec_fields = _ordered_unique_extend(
                self.active_spec_fields, specs, self.max_active_spec_fields
            )
            if self._is_multi_radio(self.active_spec_fields):
                self._task_complex = True

        if route == "product_followup" and products:
            self._primary_product = products[-1]
            self._rebuild_summary()
            self._push_delta(f"switched to {products[-1]}")
        elif route == "region_followup" and regions:
            self._primary_region = regions[-1]
            self._rebuild_summary()
            self._push_delta(f"added region {regions[-1]}")
        elif route == "spec_followup" and specs:
            self._rebuild_summary()
            self._push_delta(f"added spec focus {', '.join(specs)}")

    # ------------------------------------------------------------------
    # Summary / delta 輔助
    # ------------------------------------------------------------------
    def _is_multi_radio(self, specs: Iterable[str]) -> bool:
        radios = {s for s in specs if s in RADIO_SPEC_FIELDS}
        return len(radios) >= 2

    def _rebuild_summary(self) -> None:
        core = TASK_CORE_COMPLEX if self._task_complex else TASK_CORE
        parts = [p for p in (self._primary_product, self._primary_region, core) if p]
        self.active_request_summary = " ".join(parts)

    def _summarize_focus(self, prefix: str) -> str:
        focus = " / ".join(p for p in (self._primary_product, self._primary_region) if p)
        return f"{prefix}: {focus}" if focus else prefix

    def _push_delta(self, delta: str) -> None:
        delta = _normalize(delta)
        if not delta:
            return
        # 避免連續重複 delta。
        if self.active_context_deltas and self.active_context_deltas[-1] == delta:
            return
        self.active_context_deltas.append(delta)

    # ------------------------------------------------------------------
    # 檢索 query 組裝
    # ------------------------------------------------------------------
    def compose_retrieval_query(self, current_query: str) -> str:
        """用累積脈絡擴寫當前 query，修正『只看上一句』的 carry-forward。

        融合順序：active products + 當前 query 產品、active regions + 當前 query 區域、
        spec 維度、任務核心關鍵詞，最後接原始 query 全文（確保未入庫的新詞也被帶上）。
        """
        current = _normalize(current_query)
        cur_products = detect_products(current)
        cur_regions = detect_regions(current)
        cur_specs = detect_spec_fields(current)

        tokens: list[str] = []
        for value in (
            *self.active_products,
            *cur_products,
            *self.active_regions,
            *cur_regions,
            *self.active_spec_fields,
            *cur_specs,
        ):
            if value and value not in tokens:
                tokens.append(value)

        core = TASK_CORE_COMPLEX if self._task_complex else TASK_CORE
        tokens.append(core)

        parts = [" ".join(tokens).strip(), current]
        composed = " ".join(part for part in parts if part).strip()
        return composed or current

    # 別名。
    build_retrieval_query = compose_retrieval_query
    to_retrieval_query = compose_retrieval_query

    def detect_followup(self, query: str) -> bool:
        """是否為短 follow-up（句型標記，且沒有引入完整新任務）。"""
        return detect_followup_marker(query) and not detect_recall(query)

    # ------------------------------------------------------------------
    # Snapshot / 稽核
    # ------------------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        return {
            "active_products": list(self.active_products),
            "active_regions": list(self.active_regions),
            "active_spec_fields": list(self.active_spec_fields),
            "active_request_summary": self.active_request_summary,
            "active_context_deltas": list(self.active_context_deltas),
            "last_retrieved_docs": list(self.last_retrieved_docs),
            "recent_turns": [dict(turn) for turn in self.recent_turns],
            # --- 路由 / 治理可觀測欄位 ---
            "route": self._last_route,
            "risk_type": self._last_risk_type,
            "boundary_note": self._last_boundary_note,
            "primary_product": self._primary_product,
            "primary_region": self._primary_region,
            "task_complex": self._task_complex,
            "turn_index": self._turn_index,
        }

    # 別名。
    to_dict = snapshot
    model_dump = snapshot

    def to_debug_dict(self) -> dict[str, Any]:
        state = self.snapshot()
        state["config"] = {
            "max_recent_turns": self.max_recent_turns,
            "max_context_deltas": self.max_context_deltas,
            "max_retrieved_docs": self.max_retrieved_docs,
            "max_active_products": self.max_active_products,
            "max_active_regions": self.max_active_regions,
            "max_active_spec_fields": self.max_active_spec_fields,
        }
        state["rationale_log"] = [dict(entry) for entry in self._rationale_log]
        return state

    def reset(self) -> None:
        """清空對話（對應 app 的『清除對話』）。"""
        self.__init__(
            max_recent_turns=self.max_recent_turns,
            max_context_deltas=self.max_context_deltas,
            max_retrieved_docs=self.max_retrieved_docs,
            max_active_products=self.max_active_products,
            max_active_regions=self.max_active_regions,
            max_active_spec_fields=self.max_active_spec_fields,
        )
