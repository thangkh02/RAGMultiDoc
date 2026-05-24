from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.constants import (
    RETRIEVAL_SCOPE_CURRENT_SESSION_UPLOADS,
    RETRIEVAL_SCOPE_GENERAL_QUERY,
    RETRIEVAL_SCOPE_HYBRID_SYSTEM_AND_USER,
    RETRIEVAL_SCOPE_NEED_CLARIFICATION,
    RETRIEVAL_SCOPE_SYSTEM_DOCS,
    RETRIEVAL_SCOPE_SYSTEM_PROCEDURE,
    RETRIEVAL_SCOPE_USER_ALL_UPLOADS,
    RETRIEVAL_SCOPE_USER_FILE_NAME,
    SOURCE_TYPE_SYSTEM,
    SOURCE_TYPE_USER_UPLOAD,
)


SCOPE_VALUES = {
    RETRIEVAL_SCOPE_SYSTEM_DOCS,
    RETRIEVAL_SCOPE_SYSTEM_PROCEDURE,
    RETRIEVAL_SCOPE_CURRENT_SESSION_UPLOADS,
    RETRIEVAL_SCOPE_USER_ALL_UPLOADS,
    RETRIEVAL_SCOPE_USER_FILE_NAME,
    RETRIEVAL_SCOPE_HYBRID_SYSTEM_AND_USER,
    RETRIEVAL_SCOPE_GENERAL_QUERY,
    RETRIEVAL_SCOPE_NEED_CLARIFICATION,
}

RESOLUTION_MODES = {
    "reuse_last_context",
    "switch_scope",
    "resolve_new_procedure",
    "resolve_current_upload",
    "resolve_previous_upload",
    "resolve_by_filename",
    "resolve_by_time_hint",
    "semantic_document_search",
    "mixed",
    "need_clarification",
}


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    stripped = stripped.replace("đ", "d")
    return re.sub(r"\s+", " ", stripped).strip()


@dataclass
class StructuredScopeResolution:
    scope: str
    resolution_mode: str
    should_reuse_last_filter: bool = False
    source_type: str = "none"
    procedure_title_hint: str | None = None
    document_name_hint: str | None = None
    document_id_hint: str | None = None
    time_hint: str | None = None
    document_topic_hint: str | None = None
    branches: list[dict[str, Any]] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: str | None = None
    confidence: float = 0.0
    reason: str = ""
    used_llm: bool = False

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


class ScopeAnalyzer:
    source_switch_terms = (
        "file vua upload",
        "file vua gui",
        "tai lieu vua gui",
        "file toi upload hom qua",
        "hom kia",
        "ngay ",
        "lan truoc",
        "tai lieu cu",
        "file da tung upload",
        "so sanh",
        "doi chieu",
        "voi quy dinh he thong",
    )

    def __init__(self) -> None:
        self.chain = None
        if settings.SCOPE_RESOLVER_USE_LLM and settings.OPENROUTER_API_KEY:
            default_headers = {}
            if settings.OPENROUTER_SITE_URL:
                default_headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
            if settings.OPENROUTER_APP_NAME:
                default_headers["X-Title"] = settings.OPENROUTER_APP_NAME
            llm = ChatOpenAI(
                model=settings.OPENROUTER_SCOPE_MODEL,
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL,
                temperature=0,
                default_headers=default_headers or None,
            )
            self.chain = self._prompt() | llm | StrOutputParser()

    def _prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "Bạn là Scope Resolver cho hệ thống RAG tài liệu hành chính.\n"
                        "Nhiệm vụ: trả JSON structured để xác định query nên tìm trong scope nào.\n"
                        "Không được tạo metadata_filter. Không được quyết định quyền truy cập.\n"
                        "Filter cuối cùng sẽ do code build deterministic.\n\n"
                        "Scope hợp lệ: system_docs, system_procedure, current_session_uploads, "
                        "user_all_uploads, user_file_name, hybrid_system_and_user, general_query, need_clarification.\n"
                        "resolution_mode hợp lệ: reuse_last_context, switch_scope, resolve_new_procedure, "
                        "resolve_current_upload, resolve_previous_upload, resolve_by_filename, resolve_by_time_hint, "
                        "semantic_document_search, mixed, need_clarification.\n"
                        "Nếu không chắc, needs_clarification=true.\n"
                        "Chỉ trả JSON hợp lệ, không markdown."
                    ),
                ),
                (
                    "human",
                    (
                        "Input state:\n"
                        "{state_json}\n\n"
                        "Schema bắt buộc:\n"
                        "{{\"scope\":\"...\",\"resolution_mode\":\"...\",\"should_reuse_last_filter\":false,"
                        "\"source_type\":\"system|user_upload|hybrid|none\",\"procedure_title_hint\":null,"
                        "\"document_name_hint\":null,\"document_id_hint\":null,\"time_hint\":null,"
                        "\"document_topic_hint\":null,\"branches\":[],\"needs_clarification\":false,"
                        "\"clarification_question\":null,\"confidence\":0.0,\"reason\":\"...\"}}"
                    ),
                ),
            ]
        )

    def _has_source_switch_signal(self, query: str) -> bool:
        normalized = _normalize_text(query)
        return any(term in normalized for term in self.source_switch_terms) or bool(
            re.search(r"\b[a-z0-9][a-z0-9_\-\s().\[\]]*\.(?:pdf|docx?|xlsx?|pptx?|txt|md)\b", normalized)
        )

    def _filename_hint(self, query: str) -> str | None:
        match = re.search(r"\b([a-z0-9][a-z0-9_\-().\[\]]*\.(?:pdf|docx?|xlsx?|pptx?|txt|md))\b", query, re.I)
        return match.group(0).strip() if match else None

    def _procedure_hint(self, query: str) -> str | None:
        match = re.search(r"(?i)(?:thủ tục|thu tuc)\s+(.+?)(?:\s+cần|\s+can|\s+gồm|\s+gom|\s+là|\s+la|\?|$)", query)
        if not match:
            return None
        return match.group(1).strip(" .,:;?") or None

    def _topic_hint(self, query: str) -> str | None:
        match = re.search(r"(?i)(?:upload về|upload ve|tài liệu.*về|tai lieu.*ve)\s+(.+?)(?:\s+có|\s+co|\s+nói|\s+noi|\?|$)", query)
        if not match:
            return None
        return match.group(1).strip(" .,:;?") or None

    def _time_hint(self, query: str) -> str | None:
        normalized = _normalize_text(query)
        if "hom qua" in normalized:
            return "yesterday"
        if "hom kia" in normalized:
            return "two_days_ago"
        match = re.search(r"(?i)ngày\s+(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)", query)
        if match:
            return match.group(1)
        return None

    def _fallback(self, state: dict[str, Any], reason: str = "Resolved by deterministic fallback.") -> StructuredScopeResolution:
        query = state.get("final_query") or state.get("original_query") or ""
        normalized = _normalize_text(query)
        action = state.get("retrieval_plan", {}).get("action") or state.get("planner_action")
        last_context = (state.get("runtime_context") or {}).get("last_resolved_context") or {}
        filename = self._filename_hint(query)
        procedure = self._procedure_hint(query)
        topic = self._topic_hint(query)
        time_hint = self._time_hint(query)

        if action == "reuse_last_filter" and last_context.get("filter") and not self._has_source_switch_signal(query):
            return StructuredScopeResolution(
                scope=last_context.get("scope") or RETRIEVAL_SCOPE_NEED_CLARIFICATION,
                resolution_mode="reuse_last_context",
                should_reuse_last_filter=True,
                source_type=last_context.get("source_type") or "none",
                procedure_title_hint=last_context.get("procedure_title"),
                document_name_hint=last_context.get("filename"),
                document_id_hint=last_context.get("document_id"),
                confidence=0.9,
                reason="Safe follow-up reused last resolved context.",
            )
        if any(term in normalized for term in ("so sanh", "doi chieu", "khac nhau", "giong nhau", "dap ung")):
            return StructuredScopeResolution(
                scope=RETRIEVAL_SCOPE_HYBRID_SYSTEM_AND_USER,
                resolution_mode="mixed",
                source_type="hybrid",
                branches=[
                    {"branch_name": "system", "scope": RETRIEVAL_SCOPE_SYSTEM_DOCS},
                    {"branch_name": "user_upload", "scope": RETRIEVAL_SCOPE_CURRENT_SESSION_UPLOADS},
                ],
                confidence=0.84,
                reason=reason,
            )
        if filename:
            return StructuredScopeResolution(
                scope=RETRIEVAL_SCOPE_USER_FILE_NAME,
                resolution_mode="resolve_by_filename",
                source_type=SOURCE_TYPE_USER_UPLOAD,
                document_name_hint=filename,
                confidence=0.88,
                reason=reason,
            )
        if any(term in normalized for term in ("file vua upload", "tai lieu vua upload", "file vua gui", "tai lieu vua gui", "file nay", "tai lieu nay")):
            return StructuredScopeResolution(
                scope=RETRIEVAL_SCOPE_CURRENT_SESSION_UPLOADS,
                resolution_mode="resolve_current_upload",
                source_type=SOURCE_TYPE_USER_UPLOAD,
                confidence=0.86,
                reason=reason,
            )
        if time_hint:
            return StructuredScopeResolution(
                scope=RETRIEVAL_SCOPE_USER_ALL_UPLOADS,
                resolution_mode="resolve_by_time_hint",
                source_type=SOURCE_TYPE_USER_UPLOAD,
                time_hint=time_hint,
                confidence=0.84,
                reason=reason,
            )
        if topic and "upload" in normalized:
            return StructuredScopeResolution(
                scope=RETRIEVAL_SCOPE_USER_ALL_UPLOADS,
                resolution_mode="semantic_document_search",
                source_type=SOURCE_TYPE_USER_UPLOAD,
                document_topic_hint=topic,
                confidence=0.76,
                reason=reason,
            )
        if procedure:
            return StructuredScopeResolution(
                scope=RETRIEVAL_SCOPE_SYSTEM_PROCEDURE,
                resolution_mode="resolve_new_procedure",
                source_type=SOURCE_TYPE_SYSTEM,
                procedure_title_hint=procedure,
                confidence=0.82,
                reason=reason,
            )
        if action == "general_query":
            return StructuredScopeResolution(
                scope=RETRIEVAL_SCOPE_GENERAL_QUERY,
                resolution_mode="need_clarification",
                source_type="none",
                confidence=0.8,
                reason="Intent does not require retrieval.",
            )
        if action == "resolve_system_procedure":
            return StructuredScopeResolution(
                scope=RETRIEVAL_SCOPE_SYSTEM_PROCEDURE,
                resolution_mode="resolve_new_procedure",
                source_type=SOURCE_TYPE_SYSTEM,
                procedure_title_hint=procedure,
                confidence=0.72,
                reason=reason,
            )
        if action == "resolve_current_upload":
            return StructuredScopeResolution(
                scope=RETRIEVAL_SCOPE_CURRENT_SESSION_UPLOADS,
                resolution_mode="resolve_current_upload",
                source_type=SOURCE_TYPE_USER_UPLOAD,
                confidence=0.72,
                reason=reason,
            )
        if action == "resolve_previous_upload":
            return StructuredScopeResolution(
                scope=RETRIEVAL_SCOPE_USER_ALL_UPLOADS,
                resolution_mode="resolve_previous_upload",
                source_type=SOURCE_TYPE_USER_UPLOAD,
                confidence=0.72,
                reason=reason,
            )
        return StructuredScopeResolution(
            scope=RETRIEVAL_SCOPE_NEED_CLARIFICATION,
            resolution_mode="need_clarification",
            source_type="none",
            needs_clarification=True,
            clarification_question="Bạn muốn hỏi tài liệu hệ thống, file vừa upload, file cũ, hay một file cụ thể?",
            confidence=0.45,
            reason=reason,
        )

    def _build_llm_input(self, state: dict[str, Any]) -> dict[str, Any]:
        runtime_context = state.get("runtime_context") or {}
        return {
            "original_query": state.get("original_query"),
            "rewritten_query": state.get("rewritten_query"),
            "final_query": state.get("final_query"),
            "was_rewritten": state.get("was_rewritten"),
            "intent_resolution": state.get("intent_resolution"),
            "retrieval_plan": state.get("retrieval_plan"),
            "planner_action": state.get("planner_action"),
            "requested_scope": state.get("requested_scope"),
            "recent_chat_history": runtime_context.get("recent_chat_history", [])[-6:],
            "last_resolved_context": runtime_context.get("last_resolved_context"),
            "current_session_docs": runtime_context.get("current_session_docs", []),
            "active_document_ids": runtime_context.get("active_document_ids", []),
            "selected_document_ids": state.get("selected_document_ids", []),
            "document_candidates": (state.get("document_candidates") or [])[:5],
        }

    def _clean_payload(self, payload: dict[str, Any]) -> StructuredScopeResolution:
        scope = str(payload.get("scope") or RETRIEVAL_SCOPE_NEED_CLARIFICATION)
        if scope not in SCOPE_VALUES:
            scope = RETRIEVAL_SCOPE_NEED_CLARIFICATION
        mode = str(payload.get("resolution_mode") or "need_clarification")
        if mode not in RESOLUTION_MODES:
            mode = "need_clarification"
        return StructuredScopeResolution(
            scope=scope,
            resolution_mode=mode,
            should_reuse_last_filter=bool(payload.get("should_reuse_last_filter")),
            source_type=str(payload.get("source_type") or "none"),
            procedure_title_hint=payload.get("procedure_title_hint"),
            document_name_hint=payload.get("document_name_hint"),
            document_id_hint=payload.get("document_id_hint"),
            time_hint=payload.get("time_hint"),
            document_topic_hint=payload.get("document_topic_hint"),
            branches=payload.get("branches") if isinstance(payload.get("branches"), list) else [],
            needs_clarification=bool(payload.get("needs_clarification")),
            clarification_question=payload.get("clarification_question"),
            confidence=float(payload.get("confidence") or 0.0),
            reason=str(payload.get("reason") or "Resolved by scope LLM."),
            used_llm=True,
        )

    def _apply_security_guards(self, resolution: StructuredScopeResolution, state: dict[str, Any]) -> StructuredScopeResolution:
        query = state.get("final_query") or state.get("original_query") or ""
        last_context = (state.get("runtime_context") or {}).get("last_resolved_context") or {}
        if resolution.should_reuse_last_filter:
            if not last_context.get("filter") or self._has_source_switch_signal(query):
                resolution.should_reuse_last_filter = False
                resolution.resolution_mode = "need_clarification"
                resolution.scope = RETRIEVAL_SCOPE_NEED_CLARIFICATION
                resolution.needs_clarification = True
                resolution.clarification_question = "Câu hỏi có dấu hiệu đổi nguồn tài liệu. Bạn muốn hỏi file upload hay tài liệu hệ thống?"
                resolution.reason = "Reuse last filter blocked by source-switch/security guard."
        if resolution.scope == RETRIEVAL_SCOPE_HYBRID_SYSTEM_AND_USER and not resolution.branches:
            resolution.branches = [
                {"branch_name": "system", "scope": RETRIEVAL_SCOPE_SYSTEM_DOCS},
                {"branch_name": "user_upload", "scope": RETRIEVAL_SCOPE_CURRENT_SESSION_UPLOADS},
            ]
        return resolution

    def resolve(self, state: dict[str, Any]) -> StructuredScopeResolution:
        if self.chain is None:
            return self._fallback(state, reason="Scope LLM unavailable; used deterministic fallback.")
        try:
            raw = self.chain.invoke(
                {"state_json": json.dumps(self._build_llm_input(state), ensure_ascii=False, default=str)}
            ).strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                raw = raw.removeprefix("json").strip()
            resolution = self._clean_payload(json.loads(raw))
        except Exception:
            resolution = self._fallback(state, reason="Scope LLM failed; used deterministic fallback.")
        return self._apply_security_guards(resolution, state)
