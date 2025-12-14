"""
Orchestrator workflows for coordinating the complete synthetic data generation pipeline.

This module provides high-level workflow functions that coordinate all agents
to generate synthetic training data from questions to final approved datasets.

Pipeline Stages:
1. Stage 1: Generate and store questions → Database
2. Stage 2: Research all questions (parallel) → Database
3. Stage 3: Generate all training data (parallel) → Database
4. Stage 4: Review all data (parallel) → Database
5. Stage 5: Final storage (database manager)
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from tools.database_tools import DatabaseTools
from src.orchestrator.research_agent.workflows import research_question
from src.orchestrator.generation_agent.workflows import generate_training_data
from src.orchestrator.reviewer_agent.workflows import review_training_data
from schema.synthetic_data import TrainingType
from utils.resilience import (
    retry_with_backoff,
    research_circuit_breaker,
    generation_circuit_breaker,
    review_circuit_breaker,
    database_circuit_breaker,
    CircuitBreakerOpenError
)

# Import database sub-agents for writes
# Note: Full sub-agent integration requires workflow updates to use agent.invoke()
# For now, using DatabaseTools directly as fallback
from src.orchestrator.question_agent.question_db_sub_agent import root_agent as question_db_sub_agent


class PipelineProgress:
    """Track progress through the pipeline stages."""
    
    def __init__(self, total_questions: int):
        self.total_questions = total_questions
        self.stages = {
            "questions_added": 0,
            "researched": 0,
            "generated": 0,
            "reviewed": 0,
            "approved": 0,
            "failed": 0
        }
        self.errors = []
    
    def update(self, stage: str, count: int = 1):
        """Update progress for a stage."""
        if stage in self.stages:
            self.stages[stage] += count
    
    def add_error(self, question_id: int, stage: str, error: str):
        """Record an error."""
        self.errors.append({
            "question_id": question_id,
            "stage": stage,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.update("failed")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary."""
        return {
            "total": self.total_questions,
            "stages": self.stages.copy(),
            "errors": len(self.errors),
            "completion_percentage": (
                (self.stages["approved"] / self.total_questions * 100)
                if self.total_questions > 0 else 0
            )
        }


async def generate_synthetic_data(
    questions: List[str],
    topic: str,
    sub_topic: str,
    training_type: str,
    database_tools: Optional[DatabaseTools] = None,
    max_questions: Optional[int] = None,
    auto_approve: bool = False,
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    Complete workflow: Question -> Research -> Generation -> Review -> Database.
    
    Stage-by-stage processing with parallelization:
    1. Stage 1: Generate and store questions → Database
    2. Stage 2: Research all questions (parallel) → Database
    3. Stage 3: Generate all training data (parallel) → Database
    4. Stage 4: Review all data (parallel) → Database
    5. Stage 5: Final storage (database manager)
    
    Args:
        questions: List of questions to process
        topic: Main topic (e.g., "chemistry", "biology")
        sub_topic: Sub-topic (e.g., "organic", "cellular biology")
        training_type: Training type (e.g., "sft", "dpo", "grpo")
        database_tools: Optional DatabaseTools instance (for reads)
        max_questions: Optional limit on number of questions to process
        auto_approve: If True, store data even if review status is "needs_revision"
        batch_size: Number of items to process in parallel per stage (default: 10)
        
    Returns:
        Dictionary with:
        - status: "success" or "partial" or "error"
        - progress: Progress summary
        - results: List of results for each question
        - summary: Overall statistics
    """
    if database_tools is None:
        database_tools = DatabaseTools()
    
    # Limit questions if specified
    if max_questions:
        questions = questions[:max_questions]
    
    progress = PipelineProgress(len(questions))
    results = []
    
    try:
        # ============================================================
        # STAGE 1: Generate and Store Questions
        # ============================================================
        print(f"\n[Stage 1/5] Adding {len(questions)} questions to database...")
        question_ids = await stage_1_store_questions(
            questions, topic, sub_topic, training_type, progress
        )
        
        if not question_ids:
            return {
                "status": "error",
                "error": "Failed to add questions to database",
                "progress": progress.get_summary()
            }
        
        print(f"  [OK] Added {len(question_ids)} questions")
        
        # ============================================================
        # STAGE 2: Research All Questions (Parallel)
        # ============================================================
        print(f"\n[Stage 2/5] Researching {len(question_ids)} questions (parallel batches of {batch_size})...")
        researched_question_ids = await stage_2_research_questions(
            question_ids, topic, sub_topic, training_type, database_tools, 
            progress, batch_size
        )
        
        if not researched_question_ids:
            return {
                "status": "error",
                "error": "No questions were successfully researched",
                "progress": progress.get_summary()
            }
        
        print(f"  [OK] Researched {len(researched_question_ids)}/{len(question_ids)} questions")
        
        # ============================================================
        # STAGE 3: Generate All Training Data (Parallel)
        # ============================================================
        print(f"\n[Stage 3/5] Generating training data (parallel batches of {batch_size})...")
        training_type_enum = TrainingType(training_type.lower())
        generated_data_list = await stage_3_generate_data(
            researched_question_ids, training_type_enum, database_tools,
            progress, batch_size
        )
        
        print(f"  [OK] Generated {len(generated_data_list)} training data items")
        
        # ============================================================
        # STAGE 4: Review All Data (Parallel)
        # ============================================================
        print(f"\n[Stage 4/5] Reviewing data (parallel batches of {batch_size})...")
        reviewed_data_list = await stage_4_review_data(
            generated_data_list, training_type_enum, database_tools,
            progress, batch_size, auto_approve
        )
        
        print(f"  [OK] Reviewed {len(reviewed_data_list)} items")
        
        # ============================================================
        # STAGE 5: Final Storage
        # ============================================================
        print(f"\n[Stage 5/5] Storing approved data...")
        final_results = await stage_5_final_storage(
            reviewed_data_list, training_type, progress, results
        )
        
        print(f"  [OK] Stored {progress.stages['approved']} approved items")
        
        # Final summary
        summary = {
            "total_questions": len(questions),
            "researched": progress.stages["researched"],
            "generated": progress.stages["generated"],
            "reviewed": progress.stages["reviewed"],
            "approved": progress.stages["approved"],
            "rejected": progress.stages["reviewed"] - progress.stages["approved"],
            "failed": progress.stages["failed"],
            "success_rate": (
                (progress.stages["approved"] / len(questions) * 100)
                if len(questions) > 0 else 0
            )
        }
        
        # Determine final status
        if progress.stages["approved"] == len(questions):
            final_status = "success"
        elif progress.stages["approved"] > 0:
            final_status = "partial"
        else:
            final_status = "error"
        
        return {
            "status": final_status,
            "progress": progress.get_summary(),
            "results": results,
            "summary": summary,
            "errors": progress.errors
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "progress": progress.get_summary(),
            "results": results
        }


# ============================================================
# Stage Functions
# ============================================================

@retry_with_backoff(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=5.0,
    exponential_base=2.0,
    retry_on=(Exception,)
)
async def stage_1_store_questions(
    questions: List[str],
    topic: str,
    sub_topic: str,
    training_type: str,
    progress: PipelineProgress
) -> List[int]:
    """
    Stage 1: Store questions in database using question_db_sub_agent.
    
    Returns list of question IDs.
    """
    try:
        # Use circuit breaker for database operations
        async def _do_store():
            # Use question_db_sub_agent to store questions
            result = await question_db_sub_agent.invoke({
                "action": "add_questions",
                "questions": questions,
                "topic": topic,
                "sub_topic": sub_topic,
                "training_type": training_type
            })
            
            # Parse result (agent returns text, extract question_ids)
            # For now, use DatabaseTools directly as fallback
            from tools.database_tools import DatabaseTools
            db_tools = DatabaseTools()
            add_result = db_tools.add_questions_to_database(
                questions=questions,
                topic=topic,
                sub_topic=sub_topic,
                training_type=training_type
            )
            
            if add_result.get("status") == "success":
                question_ids = add_result["question_ids"]
                progress.update("questions_added", len(question_ids))
                return question_ids
            else:
                return []
        
        # Execute with circuit breaker
        return await database_circuit_breaker.call_async(_do_store)
        
    except CircuitBreakerOpenError as e:
        print(f"  [ERROR] Stage 1 circuit breaker open: {e}")
        return []
    except Exception as e:
        print(f"  [ERROR] Stage 1 failed: {e}")
        return []


async def stage_2_research_questions(
    question_ids: List[int],
    topic: str,
    sub_topic: str,
    training_type: str,
    database_tools: DatabaseTools,
    progress: PipelineProgress,
    batch_size: int
) -> List[int]:
    """
    Stage 2: Research all questions in parallel batches.
    
    Returns list of successfully researched question IDs.
    """
    researched_ids = []
    
    # Process in batches
    for i in range(0, len(question_ids), batch_size):
        batch = question_ids[i:i+batch_size]
        
        # Create parallel research tasks
        research_tasks = []
        for question_id in batch:
            task = _research_single_question(
                question_id, topic, sub_topic, training_type, database_tools
            )
            research_tasks.append(task)
        
        # Execute batch in parallel
        batch_results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Process results
        for result in batch_results:
            if isinstance(result, Exception):
                continue
            if result.get("status") == "success":
                researched_ids.append(result["question_id"])
                progress.update("researched")
            else:
                progress.add_error(
                    result.get("question_id", 0),
                    "research",
                    result.get("error", "Unknown error")
                )
    
    return researched_ids


@retry_with_backoff(
    max_attempts=3,
    initial_delay=2.0,
    max_delay=10.0,
    exponential_base=2.0,
    retry_on=(Exception,)
)
async def _research_single_question(
    question_id: int,
    topic: str,
    sub_topic: str,
    training_type: str,
    database_tools: DatabaseTools
) -> Dict[str, Any]:
    """Research a single question and store results via research_db_sub_agent."""
    try:
        # Use circuit breaker for research operations
        async def _do_research():
            # Get question from database
            question_data = database_tools.get_question_by_id(question_id)
            if not question_data or "error" in question_data:
                return {
                    "status": "error",
                    "question_id": question_id,
                    "error": "Failed to retrieve question"
                }
            
            # Research using research agent
            research_result = await research_question(
                question=question_data["question"],
                topic=topic,
                sub_topic=sub_topic,
                training_type=training_type,
                use_web_search=True
            )
            
            # Store research via research_db_sub_agent
            # For now, use DatabaseTools directly (sub-agent integration needs workflow updates)
            update_result = database_tools.update_question_context(
                question_id=question_id,
                ground_truth_context=research_result["ground_truth_context"],
                synthesized_context=research_result["synthesized_context"],
                context_sources=research_result["context_sources"],
                quality_score=research_result["quality_score"]
            )
            
            if update_result.get("status") == "success":
                return {
                    "status": "success",
                    "question_id": question_id,
                    "research": research_result
                }
            else:
                return {
                    "status": "error",
                    "question_id": question_id,
                    "error": update_result.get("error", "Database update failed")
                }
        
        # Execute with circuit breaker
        return await research_circuit_breaker.call_async(_do_research)
        
    except CircuitBreakerOpenError as e:
        return {
            "status": "error",
            "question_id": question_id,
            "error": f"Circuit breaker open: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "question_id": question_id,
            "error": str(e)
        }


async def stage_3_generate_data(
    question_ids: List[int],
    training_type_enum: TrainingType,
    database_tools: DatabaseTools,
    progress: PipelineProgress,
    batch_size: int
) -> List[Dict[str, Any]]:
    """
    Stage 3: Generate training data for all questions in parallel batches.
    
    Returns list of generated data dictionaries with question_id.
    """
    generated_data_list = []
    
    # Process in batches
    for i in range(0, len(question_ids), batch_size):
        batch = question_ids[i:i+batch_size]
        
        # Create parallel generation tasks
        generation_tasks = []
        for question_id in batch:
            task = _generate_single_data(
                question_id, training_type_enum, database_tools
            )
            generation_tasks.append(task)
        
        # Execute batch in parallel
        batch_results = await asyncio.gather(*generation_tasks, return_exceptions=True)
        
        # Process results
        for result in batch_results:
            if isinstance(result, Exception):
                continue
            if result.get("status") == "success":
                generated_data_list.append(result["data"])
                progress.update("generated")
            else:
                progress.add_error(
                    result.get("question_id", 0),
                    "generation",
                    result.get("error", "Unknown error")
                )
    
    return generated_data_list


@retry_with_backoff(
    max_attempts=3,
    initial_delay=2.0,
    max_delay=10.0,
    exponential_base=2.0,
    retry_on=(Exception,)
)
async def _generate_single_data(
    question_id: int,
    training_type_enum: TrainingType,
    database_tools: DatabaseTools
) -> Dict[str, Any]:
    """Generate training data for a single question."""
    try:
        # Use circuit breaker for generation operations
        async def _do_generate():
            # Get question data
            question_data = database_tools.get_question_by_id(question_id)
            if not question_data or "error" in question_data:
                return {
                    "status": "error",
                    "question_id": question_id,
                    "error": "Failed to retrieve question"
                }
            
            # Generate training data
            generated_data = await generate_training_data(
                training_type_enum,
                {
                    'question': question_data["question"],
                    'topic': question_data["topic"],
                    'sub_topic': question_data["sub_topic"],
                    'ground_truth_context': question_data.get("ground_truth_context", ""),
                    'synthesized_context': question_data.get("synthesized_context", "")
                }
            )
            
            # Add question_id for tracking
            generated_data['question_id'] = question_id
            
            # Store via generation_db_sub_agent (for now, just return data)
            # Full integration would store here
            
            return {
                "status": "success",
                "question_id": question_id,
                "data": generated_data
            }
        
        # Execute with circuit breaker
        return await generation_circuit_breaker.call_async(_do_generate)
        
    except CircuitBreakerOpenError as e:
        return {
            "status": "error",
            "question_id": question_id,
            "error": f"Circuit breaker open: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "question_id": question_id,
            "error": str(e)
        }


async def stage_4_review_data(
    generated_data_list: List[Dict[str, Any]],
    training_type_enum: TrainingType,
    database_tools: DatabaseTools,
    progress: PipelineProgress,
    batch_size: int,
    auto_approve: bool
) -> List[Dict[str, Any]]:
    """
    Stage 4: Review all generated data in parallel batches.
    
    Returns list of reviewed data with review metadata.
    """
    reviewed_data_list = []
    
    # Process in batches
    for i in range(0, len(generated_data_list), batch_size):
        batch = generated_data_list[i:i+batch_size]
        
        # Create parallel review tasks
        review_tasks = []
        for data in batch:
            question_id = data.get('question_id', 0)
            # Get ground truth context
            question_data = database_tools.get_question_by_id(question_id)
            ground_truth = question_data.get("ground_truth_context", "") if question_data else ""
            
            task = _review_single_data(
                data, training_type_enum, ground_truth
            )
            review_tasks.append(task)
        
        # Execute batch in parallel
        batch_results = await asyncio.gather(*review_tasks, return_exceptions=True)
        
        # Process results
        for result in batch_results:
            if isinstance(result, Exception):
                continue
            if result.get("status") == "success":
                # Add review metadata to data
                data = result["data"]
                data['quality_score'] = result["review"]["quality_score"]
                data['review_status'] = result["review"]["review_status"]
                data['reviewer_notes'] = result["review"].get("reviewer_notes", "")
                
                # Filter by approval
                should_store = (
                    result["review"]["review_status"] == "approved" or
                    (auto_approve and result["review"]["review_status"] == "needs_revision")
                )
                
                if should_store:
                    reviewed_data_list.append(data)
                
                progress.update("reviewed")
            else:
                progress.add_error(
                    result.get("question_id", 0),
                    "review",
                    result.get("error", "Unknown error")
                )
    
    return reviewed_data_list


@retry_with_backoff(
    max_attempts=3,
    initial_delay=2.0,
    max_delay=10.0,
    exponential_base=2.0,
    retry_on=(Exception,)
)
async def _review_single_data(
    data: Dict[str, Any],
    training_type_enum: TrainingType,
    ground_truth: str
) -> Dict[str, Any]:
    """Review a single generated data item."""
    try:
        question_id = data.get('question_id', 0)
        
        # Use circuit breaker for review operations
        async def _do_review():
            # Review training data
            review_result = await review_training_data(
                training_type_enum,
                data,
                ground_truth=ground_truth
            )
            
            return {
                "status": "success",
                "question_id": question_id,
                "data": data,
                "review": review_result
            }
        
        # Execute with circuit breaker
        return await review_circuit_breaker.call_async(_do_review)
        
    except CircuitBreakerOpenError as e:
        return {
            "status": "error",
            "question_id": data.get('question_id', 0),
            "error": f"Circuit breaker open: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "question_id": data.get('question_id', 0),
            "error": str(e)
        }


async def stage_5_final_storage(
    reviewed_data_list: List[Dict[str, Any]],
    training_type: str,
    progress: PipelineProgress,
    results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Stage 5: Store approved data using review_db_sub_agent.
    
    Returns list of storage results.
    """
    storage_results = []
    
    for data in reviewed_data_list:
        try:
            question_id = data.get('question_id', 0)
            
            # Use retry logic for database storage
            @retry_with_backoff(
                max_attempts=3,
                initial_delay=1.0,
                max_delay=5.0,
                exponential_base=2.0,
                retry_on=(Exception,)
            )
            async def _do_store():
                # Store via review_db_sub_agent
                # For now, use DatabaseTools directly (sub-agent integration needs workflow updates)
                from tools.database_tools import DatabaseTools
                db_tools = DatabaseTools()
                return db_tools.add_synthetic_data(
                    training_type,
                    data
                )
            
            # Execute with circuit breaker
            store_result = await database_circuit_breaker.call_async(_do_store)
            
            if store_result.get("status") == "success":
                progress.update("approved")
                results.append({
                    "question_id": question_id,
                    "status": "success",
                    "generated_id": store_result.get("id"),
                    "quality_score": data.get("quality_score"),
                    "review_status": data.get("review_status")
                })
                storage_results.append(store_result)
            else:
                progress.add_error(
                    question_id,
                    "storage",
                    store_result.get("error", "Storage failed")
                )
        except CircuitBreakerOpenError as e:
            question_id = data.get('question_id', 0)
            progress.add_error(question_id, "storage", f"Circuit breaker open: {str(e)}")
        except Exception as e:
            question_id = data.get('question_id', 0)
            progress.add_error(question_id, "storage", str(e))
    
    return storage_results


async def process_pending_questions(
    topic: Optional[str] = None,
    sub_topic: Optional[str] = None,
    training_type: Optional[str] = None,
    limit: Optional[int] = None,
    database_tools: Optional[DatabaseTools] = None,
    auto_approve: bool = False
) -> Dict[str, Any]:
    """
    Process pending questions from the database.
    
    This workflow:
    1. Retrieves pending questions from database
    2. Researches them
    3. Generates training data
    4. Reviews and stores approved data
    
    Args:
        topic: Optional topic filter
        sub_topic: Optional sub-topic filter
        training_type: Optional training type filter
        limit: Optional limit on number of questions
        database_tools: Optional DatabaseTools instance
        auto_approve: If True, store data even if review status is "needs_revision"
        
    Returns:
        Dictionary with processing results
    """
    if database_tools is None:
        database_tools = DatabaseTools()
    
    # Get pending questions
    pending_questions = database_tools.get_questions_by_stage(
        pipeline_stage="pending",
        topic=topic,
        sub_topic=sub_topic,
        limit=limit
    )
    
    if not pending_questions or len(pending_questions) == 0:
        return {
            "status": "success",
            "message": "No pending questions found",
            "processed": 0
        }
    
    # Extract question details
    questions = [q["question"] for q in pending_questions]
    question_ids = [q["id"] for q in pending_questions]
    
    # Get topic/sub_topic from first question (assuming they're all the same)
    if pending_questions:
        topic = topic or pending_questions[0]["topic"]
        sub_topic = sub_topic or pending_questions[0]["sub_topic"]
        training_type = training_type or pending_questions[0].get("training_type", "sft")
    
    # Process using main workflow
    return await generate_synthetic_data(
        questions=questions,
        topic=topic,
        sub_topic=sub_topic,
        training_type=training_type,
        database_tools=database_tools,
        auto_approve=auto_approve
    )


async def resume_failed_questions(
    topic: Optional[str] = None,
    sub_topic: Optional[str] = None,
    database_tools: Optional[DatabaseTools] = None
) -> Dict[str, Any]:
    """
    Resume processing for questions that failed at any stage.
    
    This workflow:
    1. Finds questions that failed during research, generation, or review
    2. Retries from the appropriate stage
    3. Completes the pipeline
    
    Args:
        topic: Optional topic filter
        sub_topic: Optional sub-topic filter
        database_tools: Optional DatabaseTools instance
        
    Returns:
        Dictionary with retry results
    """
    if database_tools is None:
        database_tools = DatabaseTools()
    
    # Get questions that are in error states or stuck
    # For MVP, we'll look for questions that are pending but should be processed
    # In production, we'd track failure states more explicitly
    
    pending = database_tools.get_questions_by_stage(
        pipeline_stage="pending",
        topic=topic,
        sub_topic=sub_topic
    )
    
    if not pending:
        return {
            "status": "success",
            "message": "No failed questions to resume",
            "resumed": 0
        }
    
    # Process them
    return await process_pending_questions(
        topic=topic,
        sub_topic=sub_topic,
        database_tools=database_tools
    )


async def get_pipeline_status(
    topic: Optional[str] = None,
    sub_topic: Optional[str] = None,
    database_tools: Optional[DatabaseTools] = None
) -> Dict[str, Any]:
    """
    Get status of the pipeline for a given topic/sub-topic.
    
    Returns counts of questions at each pipeline stage.
    
    Args:
        topic: Optional topic filter
        sub_topic: Optional sub-topic filter
        database_tools: Optional DatabaseTools instance
        
    Returns:
        Dictionary with counts by stage
    """
    if database_tools is None:
        database_tools = DatabaseTools()
    
    stages = [
        "pending",
        "ready_for_generation",
        "generated",
        "reviewed",
        "approved"
    ]
    
    status = {}
    for stage in stages:
        questions = database_tools.get_questions_by_stage(
            pipeline_stage=stage,
            topic=topic,
            sub_topic=sub_topic
        )
        status[stage] = len(questions) if questions else 0
    
    # Also get counts from training data tables
    # This would require additional database queries
    
    return {
        "status": "success",
        "stages": status,
        "topic": topic,
        "sub_topic": sub_topic
    }
