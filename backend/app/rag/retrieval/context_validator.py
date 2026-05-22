from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


FALLBACK_NO_CONTEXT = "Không tìm thấy thông tin này trong tài liệu phù hợp."


@dataclass
class ContextValidation:
    contexts: list[dict[str, Any]]
    should_answer: bool
    fallback_answer: str | None = None
    warnings: list[str] = field(default_factory=list)
    rejected_count: int = 0

    def model_dump(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["contexts"] = []
        return payload


class ContextValidator:
    def __init__(self, min_similarity: float = 0.1) -> None:
        self.min_similarity = min_similarity

    def _matches_simple_filter(self, metadata: dict[str, Any], key: str, expected: Any) -> bool:
        if isinstance(expected, dict):
            if "$in" in expected:
                return metadata.get(key) in expected["$in"]
            return True
        return metadata.get(key) == expected

    def _matches_filter(self, metadata: dict[str, Any], metadata_filter: dict[str, Any]) -> bool:
        if not metadata_filter:
            return True
        if "$and" in metadata_filter:
            return all(self._matches_filter(metadata, item) for item in metadata_filter["$and"])
        if "$or" in metadata_filter:
            return any(self._matches_filter(metadata, item) for item in metadata_filter["$or"])
        for key, expected in metadata_filter.items():
            if key.startswith("$"):
                continue
            if not self._matches_simple_filter(metadata, key, expected):
                return False
        return True

    def validate_branch(
        self,
        contexts: list[dict[str, Any]],
        metadata_filter: dict[str, Any],
    ) -> ContextValidation:
        valid_contexts: list[dict[str, Any]] = []
        rejected_count = 0
        for item in contexts:
            metadata = item.get("metadata") or {}
            similarity = item.get("similarity")
            if similarity is not None and similarity < self.min_similarity:
                rejected_count += 1
                continue
            if not self._matches_filter(metadata, metadata_filter):
                rejected_count += 1
                continue
            valid_contexts.append(item)

        if not valid_contexts:
            return ContextValidation(
                contexts=[],
                should_answer=False,
                fallback_answer=FALLBACK_NO_CONTEXT,
                rejected_count=rejected_count,
            )
        return ContextValidation(contexts=valid_contexts, should_answer=True, rejected_count=rejected_count)

    def validate_all(self, branch_results: list[dict[str, Any]]) -> ContextValidation:
        all_contexts: list[dict[str, Any]] = []
        warnings: list[str] = []
        rejected_count = 0
        for result in branch_results:
            validation = self.validate_branch(result["contexts"], result["metadata_filter"])
            rejected_count += validation.rejected_count
            if not validation.should_answer:
                warnings.append(f"No valid context for branch: {result['name']}")
            all_contexts.extend(validation.contexts)

        if not all_contexts:
            return ContextValidation(
                contexts=[],
                should_answer=False,
                fallback_answer=FALLBACK_NO_CONTEXT,
                warnings=warnings,
                rejected_count=rejected_count,
            )
        return ContextValidation(contexts=all_contexts, should_answer=True, warnings=warnings, rejected_count=rejected_count)
