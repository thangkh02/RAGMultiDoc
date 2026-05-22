from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    stripped = stripped.replace("đ", "d")
    return re.sub(r"\s+", " ", stripped).strip()


@dataclass
class QueryRewrite:
    original_question: str
    rewritten_question: str
    was_rewritten: bool
    reason: str

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


class QueryRewriter:
    _ambiguous_terms = (
        "no",
        "cai do",
        "tai lieu nay",
        "tai lieu do",
        "thu tuc nay",
        "file nay",
        "file do",
        "van ban nay",
        "van ban do",
    )

    def _needs_rewrite(self, question: str, intent_resolution: dict[str, Any]) -> bool:
        text = _normalize_text(question)
        return bool(
            intent_resolution.get("is_follow_up")
            or len(text.split()) <= 6
            or any(term in text for term in self._ambiguous_terms)
        )

    def _subject_from_state(
        self,
        conversation_state: dict[str, Any],
        scope_resolution: dict[str, Any],
        document_resolution: dict[str, Any],
    ) -> str:
        procedure_title = scope_resolution.get("detected_procedure_title") or conversation_state.get("last_procedure_title")
        filename = scope_resolution.get("detected_filename") or conversation_state.get("last_filename")
        if procedure_title:
            return f'thủ tục "{procedure_title}"'
        if filename:
            return f'tài liệu "{filename}"'

        documents = document_resolution.get("resolved_documents") or []
        if documents:
            first_doc = documents[0]
            if first_doc.get("procedure_title"):
                return f'thủ tục "{first_doc["procedure_title"]}"'
            if first_doc.get("filename"):
                return f'tài liệu "{first_doc["filename"]}"'

        last_doc = conversation_state.get("last_referenced_doc") or {}
        if isinstance(last_doc, dict):
            if last_doc.get("procedure_title"):
                return f'thủ tục "{last_doc["procedure_title"]}"'
            if last_doc.get("filename"):
                return f'tài liệu "{last_doc["filename"]}"'
        return "tài liệu đang được hỏi"

    def rewrite(
        self,
        question: str,
        intent_resolution: dict[str, Any],
        scope_resolution: dict[str, Any],
        document_resolution: dict[str, Any],
        conversation_state: dict[str, Any] | None = None,
    ) -> QueryRewrite:
        conversation_state = conversation_state or {}
        if not self._needs_rewrite(question, intent_resolution):
            return QueryRewrite(
                original_question=question,
                rewritten_question=question,
                was_rewritten=False,
                reason="Question is explicit enough.",
            )

        subject = self._subject_from_state(conversation_state, scope_resolution, document_resolution)
        rewritten = f"Trong {subject}, {question.strip()}"
        return QueryRewrite(
            original_question=question,
            rewritten_question=rewritten,
            was_rewritten=True,
            reason="Question is a follow-up or contains ambiguous references.",
        )
