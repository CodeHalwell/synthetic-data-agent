"""Offline unit tests for DatabaseTools against an isolated SQLite database."""

import pytest

from schema.synthetic_data import TrainingType
from tools.database_tools import DatabaseTools


@pytest.fixture
def db_tools(tmp_path):
    """DatabaseTools instance bound to a fresh throwaway database."""
    return DatabaseTools(database_url=f"sqlite:///{tmp_path}/unit.db")


def test_add_and_fetch_questions(db_tools):
    result = db_tools.add_questions_to_database(
        questions=["What is a covalent bond?", "What is an ionic bond?"],
        topic="chemistry",
        sub_topic="bonding",
        training_type="sft",
    )
    assert result["status"] == "success"
    assert result["count"] == 2

    pending = db_tools.get_pending_questions(topic="chemistry")
    assert len(pending) == 2
    assert {q["status"] for q in pending} == {"pending"}

    fetched = db_tools.get_question_by_id(result["question_ids"][0])
    assert fetched["question"] == "What is a covalent bond?"
    assert fetched["pipeline_stage"] == "pending"


def test_update_question_status_and_context(db_tools):
    result = db_tools.add_questions_to_database(
        questions=["What is entropy?"], topic="physics", sub_topic="thermodynamics"
    )
    question_id = result["question_ids"][0]

    status_result = db_tools.update_question_status(
        question_id, status="answered", answer="A measure of disorder."
    )
    assert status_result["status"] == "success"

    context_result = db_tools.update_question_context(
        question_id=question_id,
        ground_truth_context="Entropy measures disorder in a system.",
        synthesized_context='{"summary": "Entropy measures disorder."}',
        context_sources=[{"url": "https://example.com", "title": "Entropy"}],
        quality_score=0.9,
    )
    assert context_result["status"] == "success"

    question = db_tools.get_question_by_id(question_id)
    assert question["status"] == "researched"
    assert question["pipeline_stage"] == "ready_for_generation"
    assert question["context_quality_score"] == 0.9
    assert question["research_completed_at"] is not None


def test_update_question_status_missing_question(db_tools):
    result = db_tools.update_question_status(question_id=99999, status="answered")
    assert result["status"] == "error"


def test_add_synthetic_data_for_each_training_type(db_tools):
    minimal_payloads = {
        "sft": {"instruction": "Explain X", "response": "X is ..."},
        "dpo": {"prompt": "p", "chosen": "good", "rejected": "bad"},
        "ppo": {"prompt": "p", "response": "r", "reward": 0.5},
        "grpo": {"prompt": "p", "group_id": "g1", "response": "r"},
        "rlhf": {"prompt": "p", "response_a": "a", "response_b": "b", "preference": "a"},
        "kto": {"prompt": "p", "response": "r", "is_desirable": True},
        "orpo": {"prompt": "p", "chosen": "good", "rejected": "bad"},
        "chat": {"conversation_id": "c1", "messages": [{"role": "user", "content": "hi"}]},
        "qa": {"question": "q", "answer": "a"},
    }
    assert set(minimal_payloads) == {t.value for t in TrainingType}

    for training_type, payload in minimal_payloads.items():
        result = db_tools.add_synthetic_data(training_type, payload)
        assert result["status"] == "success", f"{training_type}: {result.get('error')}"
        assert result["table"] == f"synthetic_data_{training_type}"


def test_add_synthetic_data_rejects_unknown_type(db_tools):
    result = db_tools.add_synthetic_data("nonsense", {"prompt": "p"})
    assert result["status"] == "error"
    assert "Invalid training type" in result["error"]


def test_questions_count_and_stage_queries(db_tools):
    db_tools.add_questions_to_database(
        questions=["q1", "q2", "q3"], topic="biology", sub_topic="cells"
    )
    count = db_tools.get_questions_count(topic="biology", status="pending")
    assert count["count"] == 3

    staged = db_tools.get_questions_by_stage("pending", topic="biology", limit=2)
    assert len(staged) == 2


def test_clear_all_tables(db_tools):
    db_tools.add_questions_to_database(questions=["q"], topic="t", sub_topic="s")
    db_tools.add_synthetic_data("qa", {"question": "q", "answer": "a"})

    cleared = db_tools.clear_all_tables()
    assert cleared["questions"] == 1
    assert cleared["synthetic_data_qa"] == 1
    assert db_tools.get_questions_count()["count"] == 0


def test_isolated_instances_use_their_own_database(tmp_path):
    first = DatabaseTools(database_url=f"sqlite:///{tmp_path}/a.db")
    second = DatabaseTools(database_url=f"sqlite:///{tmp_path}/b.db")

    first.add_questions_to_database(questions=["only in a"], topic="t", sub_topic="s")
    assert first.get_questions_count()["count"] == 1
    assert second.get_questions_count()["count"] == 0
