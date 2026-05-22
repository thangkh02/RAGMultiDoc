import json
from pathlib import Path

from app.rag.retrieval.resolvers import ScopeResolver


CASES_PATH = Path(__file__).parent / "fixtures" / "scope_resolver_cases.json"


def _load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def _assert_metadata_contains(actual: dict, expected: dict) -> None:
    for key, value in expected.items():
        assert actual.get(key) == value


def test_scope_resolver_json_cases():
    resolver = ScopeResolver()

    for case in _load_cases():
        resolution = resolver.resolve(
            question=case["question"],
            user_id=case["user_id"],
            session_id=case.get("session_id"),
            selected_document_ids=case.get("selected_document_ids"),
            conversation_state=case.get("conversation_state"),
        )

        assert resolution.scope == case["expected_scope"], case["id"]
        assert resolution.should_retrieve is case["expected_should_retrieve"], case["id"]

        if "expected_detected_procedure_title" in case:
            assert resolution.detected_procedure_title == case["expected_detected_procedure_title"], case["id"]
        if "expected_detected_filename" in case:
            assert resolution.detected_filename == case["expected_detected_filename"], case["id"]
        if "expected_metadata_contains" in case:
            _assert_metadata_contains(resolution.metadata_filter, case["expected_metadata_contains"])
        if "expected_metadata_has_key" in case:
            assert case["expected_metadata_has_key"] in resolution.metadata_filter, case["id"]
