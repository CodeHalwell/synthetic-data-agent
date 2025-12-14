"""
Orchestrator workflows for coordinating the complete synthetic data generation pipeline.

This module provides high-level workflow functions that coordinate all agents
to generate synthetic training data from questions to final approved datasets.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from tools.database_tools import DatabaseTools
from src.orchestrator.research_agent.workflows import (
    research_question_and_store,
    research_questions_batch
)
from src.orchestrator.generation_agent.workflows import generate_training_data
from src.orchestrator.reviewer_agent.workflows import review_training_data
from schema.synthetic_data import TrainingType


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
    auto_approve: bool = False
) -> Dict[str, Any]:
    """
    Complete workflow: Question -> Research -> Generation -> Review -> Database.
    
    This is the main entry point for generating synthetic training data.
    It coordinates all agents to:
    1. Add questions to database
    2. Research each question
    3. Generate training data
    4. Review quality
    5. Store approved data
    
    Args:
        questions: List of questions to process
        topic: Main topic (e.g., "chemistry", "biology")
        sub_topic: Sub-topic (e.g., "organic", "cellular biology")
        training_type: Training type (e.g., "sft", "dpo", "grpo")
        database_tools: Optional DatabaseTools instance
        max_questions: Optional limit on number of questions to process
        auto_approve: If True, store data even if review status is "needs_revision"
        
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
        # Step 1: Add questions to database
        print(f"\n[Step 1/5] Adding {len(questions)} questions to database...")
        add_result = database_tools.add_questions_to_database(
            questions=questions,
            topic=topic,
            sub_topic=sub_topic,
            training_type=training_type
        )
        
        if add_result.get("status") != "success":
            return {
                "status": "error",
                "error": f"Failed to add questions: {add_result.get('error')}",
                "progress": progress.get_summary()
            }
        
        question_ids = add_result["question_ids"]
        progress.update("questions_added", len(question_ids))
        print(f"  [OK] Added {len(question_ids)} questions")
        
        # Step 2: Research all questions
        print(f"\n[Step 2/5] Researching {len(question_ids)} questions...")
        research_results = await research_questions_batch(
            question_ids=question_ids,
            database_tools=database_tools
        )
        
        researched_count = research_results["researched"]
        progress.update("researched", researched_count)
        print(f"  [OK] Researched {researched_count}/{len(question_ids)} questions")
        
        if researched_count == 0:
            return {
                "status": "error",
                "error": "No questions were successfully researched",
                "progress": progress.get_summary(),
                "research_results": research_results
            }
        
        # Step 3: Generate training data for each researched question
        print(f"\n[Step 3/5] Generating training data...")
        training_type_enum = TrainingType(training_type.lower())
        
        for research_result in research_results["results"]:
            if research_result.get("status") != "success":
                progress.add_error(
                    research_result.get("question_id", 0),
                    "research",
                    research_result.get("error", "Unknown error")
                )
                continue
            
            question_id = research_result["question_id"]
            
            try:
                # Get question data
                question_data = database_tools.get_question_by_id(question_id)
                if not question_data or "error" in question_data:
                    progress.add_error(question_id, "generation", "Failed to retrieve question")
                    continue
                
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
                
                progress.update("generated")
                
                # Step 4: Review generated data
                review_result = await review_training_data(
                    training_type_enum,
                    generated_data,
                    ground_truth=question_data.get("ground_truth_context", "")
                )
                
                progress.update("reviewed")
                
                # Step 5: Store if approved (or if auto_approve and needs_revision)
                should_store = (
                    review_result["review_status"] == "approved" or
                    (auto_approve and review_result["review_status"] == "needs_revision")
                )
                
                if should_store:
                    # Add review metadata
                    generated_data['quality_score'] = review_result['quality_score']
                    generated_data['review_status'] = review_result['review_status']
                    generated_data['reviewer_notes'] = review_result.get('reviewer_notes', '')
                    
                    # Store in database
                    store_result = database_tools.add_synthetic_data(
                        training_type,
                        generated_data
                    )
                    
                    if store_result.get("status") == "success":
                        progress.update("approved")
                        results.append({
                            "question_id": question_id,
                            "status": "success",
                            "generated_id": store_result.get("id"),
                            "quality_score": review_result["quality_score"],
                            "review_status": review_result["review_status"]
                        })
                    else:
                        progress.add_error(
                            question_id,
                            "storage",
                            store_result.get("error", "Storage failed")
                        )
                else:
                    results.append({
                        "question_id": question_id,
                        "status": "rejected",
                        "quality_score": review_result["quality_score"],
                        "review_status": review_result["review_status"],
                        "reason": "Quality below threshold"
                    })
                    
            except Exception as e:
                progress.add_error(question_id, "generation", str(e))
                results.append({
                    "question_id": question_id,
                    "status": "error",
                    "error": str(e)
                })
        
        print(f"  [OK] Generated and reviewed {progress.stages['reviewed']} items")
        print(f"  [OK] Approved and stored {progress.stages['approved']} items")
        
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
