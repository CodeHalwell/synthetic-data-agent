import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent.parent))

from google.adk.tools import BaseTool
from sqlalchemy.orm import Session, sessionmaker

from schema.synthetic_data import (
    QUESTIONS_TABLE,
    TrainingType,
    get_schema_for_training_type,
    utcnow,
)
from utils.db import create_db_engine


class DatabaseTools(BaseTool):
    """
    Database tools for managing synthetic data generation pipeline.

    Handles:
    - Storing questions from the question agent
    - Adding synthetic data to appropriate training type tables
    - Querying and managing database records

    The database location comes from the DATABASE_URL environment variable
    (any SQLAlchemy URL) and defaults to sqlite:///db/synthetic_data.db.
    Tables are created automatically if they do not exist yet.
    """

    def __init__(self, database_url: str | None = None):
        super().__init__(
            name="database_tools",
            description="Tools for interacting with the synthetic data database. Can add questions, store synthetic data for different training types (SFT, DPO, PPO, GRPO, RLHF, KTO, ORPO, Chat, QA), and query database records.",
        )
        self._engine = create_db_engine(database_url)
        self._session_factory = sessionmaker(bind=self._engine)
        self._session: Session | None = None

    def _get_session(self) -> Session:
        """Get or create a database session."""
        if self._session is None:
            self._session = self._session_factory()
        return self._session

    def add_questions_to_database(
        self, questions: list[str], topic: str, sub_topic: str, training_type: str | None = None
    ) -> dict[str, Any]:
        """
        Add questions to the questions database table.

        This method is used by the question agent to store questions that need
        to be researched and answered before generating synthetic data.

        Args:
            questions: A list of question strings to add to the database
            topic: The main topic (e.g., "chemistry", "mathematics", "computer science")
            sub_topic: The sub-topic (e.g., "organic", "analytical", "inorganic" for chemistry)
            training_type: Optional training type this question relates to (e.g., "sft", "dpo")

        Returns:
            Dictionary with count of questions added and list of question IDs
        """
        session = self._get_session()
        added_ids = []

        try:
            for question_text in questions:
                question_record = QUESTIONS_TABLE(
                    question=question_text,
                    topic=topic,
                    sub_topic=sub_topic,
                    training_type=training_type,
                    status="pending",
                )
                session.add(question_record)
                session.flush()  # Get the ID
                added_ids.append(question_record.id)

            session.commit()
            return {
                "count": len(added_ids),
                "question_ids": added_ids,
                "topic": topic,
                "sub_topic": sub_topic,
                "status": "success",
            }
        except Exception as e:
            session.rollback()
            return {"count": 0, "error": str(e), "status": "error"}

    def add_synthetic_data(self, training_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Add synthetic data to the appropriate training type table.

        Args:
            training_type: The training type (e.g., "sft", "dpo", "ppo", "grpo", "rlhf", "kto", "orpo", "chat", "qa")
            data: Dictionary containing the data fields for the specific training type schema

        Returns:
            Dictionary with the created record ID and status
        """
        session = self._get_session()

        try:
            # Get the appropriate schema for the training type
            training_type_enum = TrainingType(training_type.lower())
            schema_class = get_schema_for_training_type(training_type_enum)

            if schema_class is None:
                return {"status": "error", "error": f"Unknown training type: {training_type}"}

            # Create a new record with the provided data
            record = schema_class(**data)
            session.add(record)
            session.flush()
            record_id = record.id
            session.commit()

            return {
                "status": "success",
                "id": record_id,
                "training_type": training_type,
                "table": schema_class.__tablename__,
            }
        except ValueError:
            return {
                "status": "error",
                "error": f"Invalid training type: {training_type}. Valid types: {[t.value for t in TrainingType]}",
            }
        except Exception as e:
            session.rollback()
            return {"status": "error", "error": str(e)}

    def get_pending_questions(
        self, topic: str | None = None, sub_topic: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get pending questions from the database.

        Args:
            topic: Optional filter by topic
            sub_topic: Optional filter by sub-topic

        Returns:
            List of question dictionaries
        """
        session = self._get_session()

        try:
            query = session.query(QUESTIONS_TABLE).filter(QUESTIONS_TABLE.status == "pending")

            if topic:
                query = query.filter(QUESTIONS_TABLE.topic == topic)
            if sub_topic:
                query = query.filter(QUESTIONS_TABLE.sub_topic == sub_topic)

            questions = query.all()
            return [
                {
                    "id": q.id,
                    "question": q.question,
                    "topic": q.topic,
                    "sub_topic": q.sub_topic,
                    "status": q.status,
                    "training_type": q.training_type,
                }
                for q in questions
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def update_question_status(
        self, question_id: int, status: str, answer: str | None = None
    ) -> dict[str, Any]:
        """
        Update the status of a question (e.g., mark as answered).

        Args:
            question_id: The ID of the question to update
            status: New status ("pending", "researching", "answered", "skipped")
            answer: Optional answer/research findings

        Returns:
            Dictionary with update status
        """
        session = self._get_session()

        try:
            question = (
                session.query(QUESTIONS_TABLE).filter(QUESTIONS_TABLE.id == question_id).first()
            )

            if not question:
                return {"status": "error", "error": f"Question with ID {question_id} not found"}

            question.status = status
            if answer:
                question.answer = answer
            if status == "answered":
                question.answered_at = utcnow()

            session.commit()

            return {"status": "success", "question_id": question_id, "new_status": status}
        except Exception as e:
            session.rollback()
            return {"status": "error", "error": str(e)}

    def get_question_by_id(self, question_id: int) -> dict[str, Any] | None:
        """
        Get a question by its ID.

        Args:
            question_id: The ID of the question to retrieve

        Returns:
            Dictionary with question data, or None if not found
        """
        session = self._get_session()

        try:
            question = (
                session.query(QUESTIONS_TABLE).filter(QUESTIONS_TABLE.id == question_id).first()
            )

            if not question:
                return None

            return {
                "id": question.id,
                "question": question.question,
                "topic": question.topic,
                "sub_topic": question.sub_topic,
                "status": question.status,
                "pipeline_stage": question.pipeline_stage,
                "training_type": question.training_type,
                "ground_truth_context": question.ground_truth_context,
                "synthesized_context": question.synthesized_context,
                "context_sources": question.context_sources,
                "context_quality_score": question.context_quality_score,
                "research_completed_at": question.research_completed_at.isoformat()
                if question.research_completed_at
                else None,
            }
        except Exception as e:
            return {"error": str(e)}

    def get_questions_count(
        self,
        topic: str | None = None,
        sub_topic: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """
        Get count of questions by filters.

        Args:
            topic: Optional filter by topic
            sub_topic: Optional filter by sub-topic
            status: Optional filter by status

        Returns:
            Dictionary with counts
        """
        session = self._get_session()

        try:
            query = session.query(QUESTIONS_TABLE)

            if topic:
                query = query.filter(QUESTIONS_TABLE.topic == topic)
            if sub_topic:
                query = query.filter(QUESTIONS_TABLE.sub_topic == sub_topic)
            if status:
                query = query.filter(QUESTIONS_TABLE.status == status)

            count = query.count()
            return {"count": count, "topic": topic, "sub_topic": sub_topic, "status": status}
        except Exception as e:
            return {"count": 0, "error": str(e)}

    def update_question_context(
        self,
        question_id: int,
        ground_truth_context: str,
        synthesized_context: str,
        context_sources: list[dict[str, Any]],
        quality_score: float | None = None,
    ) -> dict[str, Any]:
        """
        Update a question with research context.

        This method is used by the Research Agent to store both raw ground truth
        and synthesized context after gathering information from sources.

        Args:
            question_id: ID of the question
            ground_truth_context: Raw, word-for-word text from authoritative sources
            synthesized_context: LLM-structured context (JSON string or formatted text)
            context_sources: List of source metadata dicts with url, title, license, etc.
            quality_score: Optional quality score (0-1) for the research

        Returns:
            Update status dict
        """
        session = self._get_session()

        try:
            question = (
                session.query(QUESTIONS_TABLE).filter(QUESTIONS_TABLE.id == question_id).first()
            )

            if not question:
                return {"status": "error", "error": f"Question {question_id} not found"}

            question.ground_truth_context = ground_truth_context
            question.synthesized_context = synthesized_context
            question.context_sources = context_sources
            question.context_quality_score = quality_score
            question.status = "researched"
            question.pipeline_stage = "ready_for_generation"
            question.research_completed_at = utcnow()

            session.commit()

            return {
                "status": "success",
                "question_id": question_id,
                "new_status": "researched",
                "pipeline_stage": "ready_for_generation",
            }
        except Exception as e:
            session.rollback()
            return {"status": "error", "error": str(e)}

    def update_question_artifacts(
        self,
        question_id: int,
        task_spec: dict | None = None,
        evidence: dict | None = None,
        reference_solution: dict | None = None,
        review: dict | None = None,
        pipeline_stage: str | None = None,
    ) -> dict[str, Any]:
        """
        Update structured artifacts for a question.

        Artifacts are JSON blobs that persist at each pipeline stage:
        - task_spec: Training type, constraints, format requirements
        - evidence: Grounding inputs with provenance
        - reference_solution: Gold answer with acceptance criteria
        - review: Validation results and decisions

        Args:
            question_id: ID of the question
            task_spec: Task specification dict
            evidence: Evidence pack dict
            reference_solution: Reference solution dict
            review: Review results dict
            pipeline_stage: New pipeline stage

        Returns:
            Update status dict
        """
        session = self._get_session()

        try:
            question = (
                session.query(QUESTIONS_TABLE).filter(QUESTIONS_TABLE.id == question_id).first()
            )

            if not question:
                return {"status": "error", "error": f"Question {question_id} not found"}

            if task_spec is not None:
                question.task_spec = task_spec
            if evidence is not None:
                question.evidence = evidence
            if reference_solution is not None:
                question.reference_solution = reference_solution
            if review is not None:
                question.review = review
            if pipeline_stage is not None:
                question.pipeline_stage = pipeline_stage

            question.updated_at = utcnow()
            session.commit()

            return {
                "status": "success",
                "question_id": question_id,
                "pipeline_stage": pipeline_stage,
            }
        except Exception as e:
            session.rollback()
            return {"status": "error", "error": str(e)}

    def print_all_tables(
        self, limit_per_table: int | None = None, show_all_columns: bool = False
    ) -> dict[str, int]:
        """
        Print contents of all database tables.

        This is a convenience method that uses the db_inspector utility.

        Args:
            limit_per_table: Optional limit on records per table
            show_all_columns: If True, show all columns including empty ones

        Returns:
            Dictionary mapping table names to record counts
        """
        from utils.db_inspector import print_all_tables

        return print_all_tables(limit_per_table=limit_per_table, show_all_columns=show_all_columns)

    def get_questions_by_stage(
        self,
        pipeline_stage: str,
        topic: str | None = None,
        sub_topic: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get questions by pipeline stage.

        Args:
            pipeline_stage: Pipeline stage to filter by
            topic: Optional topic filter
            sub_topic: Optional sub-topic filter
            limit: Optional limit on number of results

        Returns:
            List of question dictionaries
        """
        session = self._get_session()

        try:
            query = session.query(QUESTIONS_TABLE).filter(
                QUESTIONS_TABLE.pipeline_stage == pipeline_stage
            )

            if topic:
                query = query.filter(QUESTIONS_TABLE.topic == topic)
            if sub_topic:
                query = query.filter(QUESTIONS_TABLE.sub_topic == sub_topic)
            if limit:
                query = query.limit(limit)

            questions = query.all()
            return [
                {
                    "id": q.id,
                    "question": q.question,
                    "topic": q.topic,
                    "sub_topic": q.sub_topic,
                    "status": q.status,
                    "pipeline_stage": q.pipeline_stage,
                    "training_type": q.training_type,
                    "ground_truth_context": q.ground_truth_context,
                    "synthesized_context": q.synthesized_context,
                    "context_sources": q.context_sources,
                    "task_spec": q.task_spec,
                    "evidence": q.evidence,
                    "reference_solution": q.reference_solution,
                }
                for q in questions
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def clear_all_tables(self, confirm: bool = True) -> dict[str, int]:
        """
        Clear all data from all database tables.

        WARNING: This will permanently delete all data from all tables!

        Args:
            confirm: If True, proceed with deletion. Defaults to True for programmatic use.

        Returns:
            Dictionary mapping table names to number of records deleted
        """
        if not confirm:
            return {}

        session = self._get_session()
        results = {}

        try:
            # Import all table classes
            from schema.synthetic_data import (
                SyntheticDataChat,
                SyntheticDataDPO,
                SyntheticDataGRPO,
                SyntheticDataKTO,
                SyntheticDataORPO,
                SyntheticDataPPO,
                SyntheticDataQA,
                SyntheticDataRLHF,
                SyntheticDataSFT,
            )

            all_tables = {
                "questions": QUESTIONS_TABLE,
                "synthetic_data_sft": SyntheticDataSFT,
                "synthetic_data_dpo": SyntheticDataDPO,
                "synthetic_data_ppo": SyntheticDataPPO,
                "synthetic_data_grpo": SyntheticDataGRPO,
                "synthetic_data_rlhf": SyntheticDataRLHF,
                "synthetic_data_kto": SyntheticDataKTO,
                "synthetic_data_orpo": SyntheticDataORPO,
                "synthetic_data_chat": SyntheticDataChat,
                "synthetic_data_qa": SyntheticDataQA,
            }

            for table_name, table_class in all_tables.items():
                count = session.query(table_class).count()
                if count > 0:
                    session.query(table_class).delete()
                results[table_name] = count

            session.commit()
            return results

        except Exception as e:
            session.rollback()
            return {"error": str(e)}
