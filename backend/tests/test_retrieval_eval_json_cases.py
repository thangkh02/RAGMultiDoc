import json
from pathlib import Path

from app.rag.retrieval.context_validator import ContextValidator


CASES_PATH = Path(__file__).parent / "fixtures" / "retrieval_eval_cases.json"


def test_retrieval_eval_json_cases_hit_expected_chunks():
    validator = ContextValidator(min_similarity=0.1)

    for case in json.loads(CASES_PATH.read_text(encoding="utf-8")):
        validation = validator.validate_branch(case["contexts"], case["metadata_filter"])
        retrieved_ids = [item["metadata"]["chunk_id"] for item in validation.contexts]

        assert validation.should_answer is True, case["id"]
        for expected_chunk_id in case["expected_chunk_ids"]:
            assert expected_chunk_id in retrieved_ids, case["id"]
        assert "chunk_noise" not in retrieved_ids
        assert "chunk_other_user" not in retrieved_ids
