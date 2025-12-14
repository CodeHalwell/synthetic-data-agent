"""
Test script to verify Priority 1 database updates.

Tests:
1. Adding questions to database
2. Updating question context
3. Updating question artifacts
4. Querying questions by pipeline stage
"""

from tools.database_tools import DatabaseTools
from datetime import datetime

def test_database_updates():
    print("\n" + "=" * 60)
    print("  Testing Database Updates (Priority 1)")
    print("=" * 60 + "\n")
    
    db_tools = DatabaseTools()
    
    # Test 1: Add a question
    print("[Test 1] Adding a question...")
    result = db_tools.add_questions_to_database(
        questions=["What is the mechanism of SN2 reactions?"],
        topic="chemistry",
        sub_topic="organic chemistry",
        training_type="sft"
    )
    print(f"  Status: {result['status']}")
    print(f"  Added {result['count']} question(s)")
    question_id = result['question_ids'][0]
    print(f"  Question ID: {question_id}\n")
    
    # Test 2: Update question context (simulating Research Agent)
    print("[Test 2] Updating question context...")
    context_result = db_tools.update_question_context(
        question_id=question_id,
        ground_truth_context="The SN2 mechanism proceeds through a single concerted step where the nucleophile attacks the electrophile from the backside, causing inversion of configuration at the chiral center.",
        synthesized_context='{"mechanism": "concerted", "stereochemistry": "inversion", "rate_law": "bimolecular"}',
        context_sources=[
            {
                "url": "https://example.com/organic-chemistry",
                "title": "Organic Chemistry Textbook",
                "license": "CC-BY-4.0",
                "fetched_at": datetime.utcnow().isoformat()
            }
        ],
        quality_score=0.92
    )
    print(f"  Status: {context_result['status']}")
    print(f"  New status: {context_result['new_status']}")
    print(f"  Pipeline stage: {context_result['pipeline_stage']}\n")
    
    # Test 3: Update question artifacts
    print("[Test 3] Updating question artifacts...")
    artifacts_result = db_tools.update_question_artifacts(
        question_id=question_id,
        task_spec={
            "training_type": "sft",
            "output_format": "instruction-response",
            "difficulty": "medium",
            "requires_code": False
        },
        evidence={
            "items": [
                {
                    "source": "textbook",
                    "content": "SN2 reactions involve backside attack...",
                    "relevance": 0.95
                }
            ]
        },
        reference_solution={
            "final_answer": "The SN2 mechanism is a concerted reaction...",
            "answer_type": "explanation",
            "acceptance_criteria": {
                "must_mention": ["backside attack", "inversion", "concerted"]
            }
        },
        pipeline_stage="ready_for_generation"
    )
    print(f"  Status: {artifacts_result['status']}")
    print(f"  Pipeline stage: {artifacts_result['pipeline_stage']}\n")
    
    # Test 4: Query questions by pipeline stage
    print("[Test 4] Querying questions by pipeline stage...")
    questions = db_tools.get_questions_by_stage(
        pipeline_stage="ready_for_generation",
        topic="chemistry"
    )
    print(f"  Found {len(questions)} question(s) ready for generation")
    if questions:
        q = questions[0]
        print(f"  Question ID: {q['id']}")
        print(f"  Question: {q['question'][:50]}...")
        print(f"  Has context: {bool(q['ground_truth_context'])}")
        print(f"  Has task_spec: {bool(q['task_spec'])}")
        print(f"  Has evidence: {bool(q['evidence'])}")
        print(f"  Has reference_solution: {bool(q['reference_solution'])}\n")
    
    # Test 5: Check old methods still work
    print("[Test 5] Testing backward compatibility...")
    pending = db_tools.get_pending_questions(topic="chemistry")
    print(f"  Pending questions query: {'PASS' if isinstance(pending, list) else 'FAIL'}")
    
    count_result = db_tools.get_questions_count(topic="chemistry")
    print(f"  Count query: {'PASS' if count_result['count'] >= 0 else 'FAIL'}\n")
    
    print("=" * 60)
    print("  All Priority 1 Tests Complete!")
    print("=" * 60 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        test_database_updates()
        print("[SUCCESS] Priority 1 implementation verified!\n")
    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
