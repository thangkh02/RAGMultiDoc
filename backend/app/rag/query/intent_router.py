from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any


INTENT_ASK_QUESTION = "ask_question"
INTENT_SUMMARIZE_DOCUMENT = "summarize_document"
INTENT_COMPARE_DOCUMENTS = "compare_documents"
INTENT_FIND_INFORMATION = "find_information"
INTENT_FOLLOW_UP = "follow_up"
INTENT_GENERAL_QUERY = "general_query"
INTENT_NEED_CLARIFICATION = "need_clarification"

ANSWER_STYLE_SHORT = "short_answer"
ANSWER_STYLE_BULLET_LIST = "bullet_list"
ANSWER_STYLE_SUMMARY = "summary"
ANSWER_STYLE_COMPARISON = "comparison"
ANSWER_STYLE_STEPS = "steps"


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    stripped = stripped.replace("đ", "d")
    return re.sub(r"\s+", " ", stripped).strip()


@dataclass
class IntentResolution:
    intent: str
    answer_style: str = ANSWER_STYLE_SHORT
    is_follow_up: bool = False
    needs_retrieval: bool = True
    confidence: float = 0.75
    matched_rules: list[str] = field(default_factory=list)
    reason: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


class IntentRouter:
    _document_terms = (
        "file",
        "tai lieu",
        "van ban",
        "thu tuc",
        "ho so",
        "quy dinh",
        "quy trinh",
        "le phi",
        "thoi han",
        "giay to",
    )
    _follow_up_terms = (
        "the",
        "con",
        "vay",
        "thi sao",
        "no",
        "cai do",
        "tai lieu nay",
        "tai lieu do",
        "thu tuc nay",
        "file nay",
    )
    _ambiguous_terms = ("tai lieu do", "file do", "van ban do", "cai do")

    def _contains_any(self, text: str, terms: tuple[str, ...]) -> bool:
        return any(term in text for term in terms)

    def _answer_style(self, text: str, intent: str) -> str:
        if intent == INTENT_COMPARE_DOCUMENTS:
            return ANSWER_STYLE_COMPARISON
        if intent == INTENT_SUMMARIZE_DOCUMENT:
            return ANSWER_STYLE_SUMMARY
        if any(term in text for term in ("cac buoc", "quy trinh", "cach thuc")):
            return ANSWER_STYLE_STEPS
        if any(term in text for term in ("liet ke", "danh sach", "gom nhung gi", "can ho so", "ho so gi", "giay to gi")):
            return ANSWER_STYLE_BULLET_LIST
        return ANSWER_STYLE_SHORT

    def route(self, question: str, conversation_state: dict[str, Any] | None = None) -> IntentResolution:
        conversation_state = conversation_state or {}
        text = _normalize_text(question)
        matched_rules: list[str] = []
        has_state = bool(
            conversation_state.get("last_scope")
            or conversation_state.get("last_referenced_doc")
            or conversation_state.get("last_filename")
            or conversation_state.get("last_procedure_title")
        )

        if self._contains_any(text, self._ambiguous_terms) and not has_state:
            return IntentResolution(
                intent=INTENT_NEED_CLARIFICATION,
                needs_retrieval=False,
                confidence=0.9,
                matched_rules=["ambiguous_reference_without_state"],
                reason="Question references a document ambiguously without conversation state.",
            )

        if has_state and (len(text.split()) <= 6 or self._contains_any(text, self._follow_up_terms)):
            matched_rules.append("follow_up")
            intent = INTENT_FOLLOW_UP
            return IntentResolution(
                intent=intent,
                answer_style=self._answer_style(text, intent),
                is_follow_up=True,
                needs_retrieval=True,
                confidence=0.86,
                matched_rules=matched_rules,
                reason="Question depends on previous document context.",
            )

        if any(term in text for term in ("so sanh", "doi chieu", "khac nhau", "giong nhau", "dap ung")):
            intent = INTENT_COMPARE_DOCUMENTS
            matched_rules.append("compare")
        elif any(term in text for term in ("tom tat", "noi dung chinh", "tong quan")):
            intent = INTENT_SUMMARIZE_DOCUMENT
            matched_rules.append("summarize")
        elif any(term in text for term in ("tim", "tra cuu", "cho biet", "kiem tra")):
            intent = INTENT_FIND_INFORMATION
            matched_rules.append("find_information")
        elif self._contains_any(text, self._document_terms):
            intent = INTENT_ASK_QUESTION
            matched_rules.append("document_question")
        else:
            return IntentResolution(
                intent=INTENT_GENERAL_QUERY,
                needs_retrieval=False,
                confidence=0.82,
                matched_rules=["no_document_signal"],
                reason="Question does not appear to target documents.",
            )

        return IntentResolution(
            intent=intent,
            answer_style=self._answer_style(text, intent),
            is_follow_up=False,
            needs_retrieval=True,
            confidence=0.8,
            matched_rules=matched_rules,
            reason="Resolved by deterministic query rules.",
        )
