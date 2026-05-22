from app.rag.generation.source_formatter import SourceFormatter
from app.rag.retrieval.context_validator import FALLBACK_NO_CONTEXT, ContextValidator
from app.rag.retrieval.strategy import RetrievalStrategy


def test_retrieval_strategy_splits_hybrid_sources():
    strategy = RetrievalStrategy()

    plan = strategy.plan(
        rewritten_question="Đối chiếu hồ sơ",
        intent_resolution={"intent": "compare_documents", "needs_retrieval": True},
        scope="hybrid_system_and_user",
        metadata_filter={
            "$or": [
                {"source_type": "system", "visibility": "global"},
                {"source_type": "user_upload", "owner_user_id": "user_1"},
            ]
        },
    )

    assert plan.mode == "hybrid_compare"
    assert [branch.name for branch in plan.branches] == ["system_chunks", "user_upload_chunks"]
    assert plan.branches[0].metadata_filter["source_type"] == "system"
    assert plan.branches[1].metadata_filter["source_type"] == "user_upload"


def test_retrieval_strategy_does_not_retrieve_general_query():
    strategy = RetrievalStrategy()

    plan = strategy.plan(
        rewritten_question="Embedding là gì?",
        intent_resolution={"intent": "general_query", "needs_retrieval": False},
        scope="general_query",
        metadata_filter={},
    )

    assert plan.should_retrieve is False
    assert plan.branches == []


def test_context_validator_rejects_empty_and_wrong_metadata():
    validator = ContextValidator(min_similarity=0.1)

    empty = validator.validate_all([])
    assert empty.should_answer is False
    assert empty.fallback_answer == FALLBACK_NO_CONTEXT

    wrong_metadata = validator.validate_branch(
        contexts=[
            {
                "content": "abc",
                "metadata": {"source_type": "system"},
                "similarity": 0.9,
            }
        ],
        metadata_filter={"source_type": "user_upload"},
    )
    assert wrong_metadata.should_answer is False
    assert wrong_metadata.rejected_count == 1


def test_source_formatter_prefixes_source_type():
    formatter = SourceFormatter()

    assert formatter.source_prefix([{"source_type": "system"}]) == "Theo tài liệu hệ thống:"
    assert formatter.source_prefix([{"source_type": "user_upload"}]) == "Theo tài liệu bạn upload:"
    assert "tài liệu hệ thống và tài liệu bạn upload" in formatter.source_prefix(
        [{"source_type": "system"}, {"source_type": "user_upload"}]
    )
