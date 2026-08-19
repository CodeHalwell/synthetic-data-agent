"""Offline unit tests for the training-type schema registry."""

from schema.synthetic_data import (
    SCHEMA_REGISTRY,
    TRAINING_TYPE_DESCRIPTIONS,
    TrainingType,
    get_schema_for_training_type,
    get_table_name_for_training_type,
    utcnow,
)


def test_registry_covers_every_training_type():
    assert set(SCHEMA_REGISTRY) == set(TrainingType)
    assert set(TRAINING_TYPE_DESCRIPTIONS) == set(TrainingType)


def test_table_names_follow_convention():
    for training_type in TrainingType:
        table_name = get_table_name_for_training_type(training_type)
        assert table_name == f"synthetic_data_{training_type.value}"


def test_get_schema_for_training_type():
    schema = get_schema_for_training_type(TrainingType.DPO)
    assert schema.__tablename__ == "synthetic_data_dpo"


def test_training_type_is_string_valued():
    # Enum members compare equal to their lowercase string values, which is
    # what the workflow APIs expect ("sft", "dpo", ...).
    assert TrainingType.SFT == "sft"
    assert TrainingType("qa") is TrainingType.QA


def test_utcnow_is_timezone_aware():
    assert utcnow().tzinfo is not None
