from __future__ import annotations

from typing import Any

from app.core.constants import SOURCE_TYPE_SYSTEM, SOURCE_TYPE_USER_UPLOAD


class SourceFormatter:
    def source_prefix(self, sources: list[dict[str, Any]]) -> str:
        source_types = {source.get("source_type") for source in sources if source.get("source_type")}
        if source_types == {SOURCE_TYPE_SYSTEM}:
            return "Theo tài liệu hệ thống:"
        if source_types == {SOURCE_TYPE_USER_UPLOAD}:
            return "Theo tài liệu bạn upload:"
        if SOURCE_TYPE_SYSTEM in source_types and SOURCE_TYPE_USER_UPLOAD in source_types:
            return "Theo các nguồn được tìm thấy từ tài liệu hệ thống và tài liệu bạn upload:"
        return ""

    def format_answer(self, answer: str, sources: list[dict[str, Any]]) -> str:
        prefix = self.source_prefix(sources)
        if not prefix or answer.strip().startswith(prefix):
            return answer
        return f"{prefix}\n{answer.strip()}"
