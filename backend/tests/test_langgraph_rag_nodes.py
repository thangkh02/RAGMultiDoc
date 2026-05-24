from app.core.constants import SOURCE_TYPE_SYSTEM, SOURCE_TYPE_USER_UPLOAD
from app.rag.graph.nodes import ACTION_REUSE_LAST_FILTER, RAGGraphNodes
from app.rag.pipeline.qa_pipeline import QAPipeline


def _nodes() -> RAGGraphNodes:
    return RAGGraphNodes(QAPipeline())


def test_retrieval_planner_reuses_last_filter_for_protected_follow_up():
    nodes = _nodes()

    result = nodes.retrieval_planner_node(
        {
            "original_query": "đi đăng ký cần chuẩn bị gì?",
            "final_query": "Thủ tục đăng ký kết hôn cần chuẩn bị những giấy tờ gì?",
            "was_rewritten": True,
            "intent_resolution": {"intent": "ask_question", "needs_retrieval": True},
            "runtime_context": {
                "last_resolved_context": {
                    "scope": "system_procedure",
                    "procedure_title": "Đăng ký kết hôn",
                    "filter": {"source_type": SOURCE_TYPE_SYSTEM, "procedure_title": "Đăng ký kết hôn"},
                }
            },
        }
    )

    assert result["planner_action"] == ACTION_REUSE_LAST_FILTER
    assert result["retrieval_plan"]["target_scope"] == "system_procedure"


def test_retrieval_planner_does_not_reuse_last_filter_when_source_switches():
    nodes = _nodes()

    result = nodes.retrieval_planner_node(
        {
            "original_query": "còn trong file tôi upload hôm qua thì sao?",
            "final_query": "Trong file tôi upload hôm qua, lệ phí là bao nhiêu?",
            "was_rewritten": True,
            "intent_resolution": {"intent": "ask_question", "needs_retrieval": True},
            "runtime_context": {
                "last_resolved_context": {
                    "scope": "system_procedure",
                    "procedure_title": "Đăng ký kết hôn",
                    "filter": {"source_type": SOURCE_TYPE_SYSTEM, "procedure_title": "Đăng ký kết hôn"},
                }
            },
        }
    )

    assert result["planner_action"] != ACTION_REUSE_LAST_FILTER
    assert result["planner_action"] == "resolve_previous_upload"


def test_candidate_selector_clarifies_multiple_candidates():
    nodes = _nodes()

    result = nodes.candidate_selector_node(
        {
            "document_candidates": [
                {"document_id": "doc_1", "filename": "tam_tru_1.pdf"},
                {"document_id": "doc_2", "filename": "tam_tru_2.pdf"},
            ],
            "document_resolution": {"selected_document_ids": ["doc_1", "doc_2"]},
        }
    )

    assert result["candidate_selection"]["confident"] is False
    assert result["candidate_selection"]["needs_clarification"] is True


def test_mixed_evidence_validation_reports_missing_system_branch():
    nodes = _nodes()

    result = nodes.evidence_validation_node(
        {
            "retrieval_plan": {"mode": "hybrid_compare"},
            "branch_results": [
                {
                    "name": "system_chunks",
                    "metadata_filter": {"source_type": SOURCE_TYPE_SYSTEM},
                    "contexts": [],
                },
                {
                    "name": "user_upload_chunks",
                    "metadata_filter": {"source_type": SOURCE_TYPE_USER_UPLOAD, "owner_user_id": "user_1"},
                    "contexts": [
                        {
                            "id": "chunk_user_1",
                            "content": "File upload có lệ phí nội bộ là 75.000 đồng.",
                            "similarity": 0.9,
                            "metadata": {
                                "chunk_id": "chunk_user_1",
                                "document_id": "doc_1",
                                "source_type": SOURCE_TYPE_USER_UPLOAD,
                                "owner_user_id": "user_1",
                            },
                        }
                    ],
                },
            ],
        }
    )

    assert result["context_validation"]["should_answer"] is True
    assert "Chưa tìm thấy thông tin tương ứng trong tài liệu hệ thống." in result["mixed_branch_warnings"]


def test_scope_resolver_structured_reuses_last_context_when_safe():
    nodes = _nodes()

    result = nodes.scope_resolver_node(
        {
            "original_query": "can chuan bi gi?",
            "final_query": "Thu tuc dang ky ket hon can chuan bi giay to gi?",
            "was_rewritten": True,
            "planner_action": "reuse_last_filter",
            "retrieval_plan": {"action": "reuse_last_filter"},
            "runtime_context": {
                "last_resolved_context": {
                    "scope": "system_procedure",
                    "source_type": "system",
                    "procedure_title": "dang ky ket hon",
                    "filter": {"source_type": SOURCE_TYPE_SYSTEM, "procedure_title": "dang ky ket hon"},
                }
            },
        }
    )

    scope = result["scope_resolution"]
    assert scope["scope"] == "system_procedure"
    assert scope["resolution_mode"] == "reuse_last_context"
    assert scope["should_reuse_last_filter"] is True
    assert scope["procedure_title_hint"] == "dang ky ket hon"


def test_scope_resolver_structured_blocks_reuse_when_switching_to_current_upload():
    nodes = _nodes()

    result = nodes.scope_resolver_node(
        {
            "original_query": "con trong file vua upload thi sao?",
            "final_query": "con trong file vua upload thi sao?",
            "was_rewritten": True,
            "planner_action": "reuse_last_filter",
            "retrieval_plan": {"action": "reuse_last_filter"},
            "runtime_context": {
                "last_resolved_context": {
                    "scope": "system_procedure",
                    "source_type": "system",
                    "procedure_title": "dang ky ket hon",
                    "filter": {"source_type": SOURCE_TYPE_SYSTEM, "procedure_title": "dang ky ket hon"},
                }
            },
        }
    )

    scope = result["scope_resolution"]
    assert scope["should_reuse_last_filter"] is False
    assert scope["scope"] in {"current_session_uploads", "need_clarification"}


def test_scope_resolver_structured_previous_upload_time_hint():
    nodes = _nodes()

    result = nodes.scope_resolver_node(
        {
            "original_query": "Thong tin nguoi dung trong file toi upload hom qua la gi?",
            "final_query": "Thong tin nguoi dung trong file toi upload hom qua la gi?",
            "planner_action": "resolve_previous_upload",
            "retrieval_plan": {"action": "resolve_previous_upload"},
            "runtime_context": {},
        }
    )

    scope = result["scope_resolution"]
    assert scope["scope"] == "user_all_uploads"
    assert scope["resolution_mode"] == "resolve_by_time_hint"
    assert scope["time_hint"] == "yesterday"


def test_scope_resolver_structured_topic_hint_for_old_upload():
    nodes = _nodes()

    result = nodes.scope_resolver_node(
        {
            "original_query": "Tai lieu toi tung upload ve tam tru co thong tin gi?",
            "final_query": "Tai lieu toi tung upload ve tam tru co thong tin gi?",
            "planner_action": "semantic_document_search",
            "retrieval_plan": {"action": "semantic_document_search"},
            "runtime_context": {},
        }
    )

    scope = result["scope_resolution"]
    assert scope["scope"] == "user_all_uploads"
    assert scope["resolution_mode"] == "semantic_document_search"
    assert scope["document_topic_hint"] == "tam tru"


def test_build_filter_node_builds_deterministic_filter_after_scope_resolution():
    nodes = _nodes()

    result = nodes.build_filter_node(
        {
            "user_id": "user_1",
            "session_id": "sess_1",
            "scope_resolution": {
                "scope": "current_session_uploads",
                "should_reuse_last_filter": False,
            },
            "document_resolution": {"selected_document_ids": ["doc_1"]},
        }
    )

    assert result["metadata_filter"]["$and"][0]["$and"] == [
        {"source_type": SOURCE_TYPE_USER_UPLOAD},
        {"owner_user_id": "user_1"},
        {"session_id": "sess_1"},
    ]
    assert result["metadata_filter"]["$and"][1] == {"document_id": {"$in": ["doc_1"]}}


def test_scope_reuse_routes_directly_to_build_filter():
    nodes = _nodes()

    route = nodes.route_after_scope_resolution(
        {
            "scope_resolution": {
                "scope": "system_procedure",
                "should_reuse_last_filter": True,
                "needs_clarification": False,
            }
        }
    )

    assert route == "build_filter"


def test_scope_non_reuse_routes_to_document_resolver():
    nodes = _nodes()

    route = nodes.route_after_scope_resolution(
        {
            "scope_resolution": {
                "scope": "system_procedure",
                "should_reuse_last_filter": False,
                "needs_clarification": False,
            }
        }
    )

    assert route == "document_resolver"
