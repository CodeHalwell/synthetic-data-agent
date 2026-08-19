"""Offline round-trip tests: generate -> review -> store for every training type.

The generation and review workflows are deterministic (they build data from
researched context rather than calling an LLM), so the full
generate/review/store path can be exercised without an API key.
"""

import pytest

from schema.synthetic_data import TrainingType, get_schema_for_training_type
from src.orchestrator.generation_agent.workflows import generate_training_data
from src.orchestrator.reviewer_agent.workflows import review_training_data
from tools.database_tools import DatabaseTools

QUESTION_DATA = {
    "question": "What is the mechanism of SN2 reactions in organic chemistry?",
    "topic": "chemistry",
    "sub_topic": "organic chemistry",
    "ground_truth_context": (
        "The SN2 mechanism proceeds through a single concerted step where the "
        "nucleophile attacks the electrophile from the backside, causing inversion "
        "of configuration at the chiral center. The reaction is second-order overall."
    ),
    "synthesized_context": (
        '{"summary": "SN2 is a one-step nucleophilic substitution with backside attack.",'
        ' "key_concepts": ["backside attack", "inversion", "bimolecular"],'
        ' "definitions": {"SN2": "Substitution Nucleophilic Bimolecular"},'
        ' "examples": ["Methyl bromide reacting with hydroxide"]}'
    ),
}


@pytest.mark.parametrize("training_type", list(TrainingType))
async def test_generate_review_store_round_trip(training_type, tmp_path):
    generated = await generate_training_data(training_type, QUESTION_DATA)
    assert isinstance(generated, dict) and generated

    review = await review_training_data(
        training_type, generated, ground_truth=QUESTION_DATA["ground_truth_context"]
    )
    assert 0.0 <= review["quality_score"] <= 1.0
    assert review["review_status"] in {"approved", "needs_revision", "rejected"}

    # Mirror stage 5 of the orchestrator pipeline: enrich with review results,
    # then restrict the payload to the target table's columns.
    data = {
        **generated,
        "quality_score": review["quality_score"],
        "review_status": review["review_status"],
        "reviewer_notes": review.get("reviewer_notes", ""),
    }
    schema_class = get_schema_for_training_type(training_type)
    valid_columns = {column.key for column in schema_class.__table__.columns}
    payload = {key: value for key, value in data.items() if key in valid_columns}

    db_tools = DatabaseTools(database_url=f"sqlite:///{tmp_path}/{training_type.value}.db")
    stored = db_tools.add_synthetic_data(training_type.value, payload)
    assert stored["status"] == "success", f"{training_type}: {stored.get('error')}"


async def test_generate_training_data_rejects_unknown_type():
    with pytest.raises(ValueError, match="No generator"):
        await generate_training_data("not-a-type", QUESTION_DATA)
