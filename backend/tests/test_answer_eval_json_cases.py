import json
from pathlib import Path

from app.rag.generation.openai_llm import OpenAILLMService
from app.rag.generation.source_formatter import SourceFormatter


CASES_PATH = Path(__file__).parent / "fixtures" / "answer_eval_cases.json"


def test_answer_eval_source_formatting_json_cases():
    formatter = SourceFormatter()

    for case in json.loads(CASES_PATH.read_text(encoding="utf-8")):
        formatted = formatter.format_answer(case["answer"], case["sources"])
        if "expected_prefix" in case:
            assert formatted.startswith(case["expected_prefix"]), case["id"]
        if "expected_contains" in case:
            assert case["expected_contains"] in formatted, case["id"]


def test_answer_eval_empty_context_fallback():
    llm = OpenAILLMService()

    answer = llm.generate_answer("Hồ sơ gồm gì?", contexts=[])

    assert answer == "Không tìm thấy thông tin này trong tài liệu phù hợp."
