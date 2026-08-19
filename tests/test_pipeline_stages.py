"""Offline test of the orchestrator pipeline stages (research stage bypassed).

Stage 2 (research) needs a live Gemini agent, so this test injects research
context directly and then runs the real stage functions:
store -> generate -> review -> final storage.
"""

from schema.synthetic_data import TrainingType
from src.orchestrator.workflows import (
    PipelineProgress,
    stage_1_store_questions,
    stage_3_generate_data,
    stage_4_review_data,
    stage_5_final_storage,
)
from tools.database_tools import DatabaseTools

RESEARCH_CONTEXT = (
    "A covalent bond is a chemical bond formed by the sharing of electron pairs "
    "between atoms. The shared pairs are known as bonding pairs, and the stable "
    "balance of attractive and repulsive forces is called covalent bonding."
)
SYNTHESIZED_CONTEXT = (
    '{"summary": "Covalent bonds share electron pairs between atoms.",'
    ' "key_concepts": ["electron sharing", "bonding pairs"],'
    ' "definitions": {"covalent bond": "a bond formed by shared electron pairs"},'
    ' "examples": ["H2 molecule", "O2 molecule"]}'
)


async def test_pipeline_stages_store_generate_review_store(monkeypatch, tmp_path):
    # All DatabaseTools instances created inside the stage functions should
    # bind to this test's database.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/pipeline.db")
    db_tools = DatabaseTools()
    progress = PipelineProgress(total_questions=1)
    results: list[dict] = []

    # Stage 1: store questions
    question_ids = await stage_1_store_questions(
        questions=["What is a covalent bond?"],
        topic="chemistry",
        sub_topic="bonding",
        training_type="sft",
        progress=progress,
    )
    assert len(question_ids) == 1

    # Stage 2 (bypassed): inject research context directly
    update = db_tools.update_question_context(
        question_id=question_ids[0],
        ground_truth_context=RESEARCH_CONTEXT,
        synthesized_context=SYNTHESIZED_CONTEXT,
        context_sources=[{"url": "https://example.com", "title": "Covalent bond"}],
        quality_score=0.9,
    )
    assert update["status"] == "success"

    # Stage 3: generate training data
    generated = await stage_3_generate_data(
        question_ids=question_ids,
        training_type_enum=TrainingType.SFT,
        database_tools=db_tools,
        progress=progress,
        batch_size=10,
    )
    assert len(generated) == 1
    assert generated[0]["question_id"] == question_ids[0]

    # Stage 4: review
    reviewed = await stage_4_review_data(
        generated_data_list=generated,
        training_type_enum=TrainingType.SFT,
        database_tools=db_tools,
        progress=progress,
        batch_size=10,
        auto_approve=True,
    )
    assert len(reviewed) == 1
    assert reviewed[0]["review_status"] in {"approved", "needs_revision"}

    # Stage 5: final storage into synthetic_data_sft
    stored = await stage_5_final_storage(
        reviewed_data_list=reviewed,
        training_type="sft",
        progress=progress,
        results=results,
    )
    assert len(stored) == 1
    assert stored[0]["status"] == "success"
    assert progress.stages["approved"] == 1
    assert results and results[0]["status"] == "success"
