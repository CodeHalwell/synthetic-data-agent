"""
End-to-End Integration Test: Research -> Generation -> Review

Tests the complete pipeline with Research Agent integrated.
"""

import asyncio
from tools.database_tools import DatabaseTools
from src.orchestrator.research_agent.workflows import research_question_and_store
from src.orchestrator.generation_agent.workflows import generate_training_data
from src.orchestrator.reviewer_agent.workflows import review_training_data
from schema.synthetic_data import TrainingType


async def test_complete_pipeline():
    """Test complete pipeline: Question -> Research -> Generation -> Review."""
    print("\n" + "=" * 70)
    print("  Complete Pipeline Test: Research -> Generation -> Review")
    print("=" * 70 + "\n")
    
    db_tools = DatabaseTools()
    
    # Step 1: Add question
    print("[Step 1/6] Adding question to database...")
    add_result = db_tools.add_questions_to_database(
        questions=["What is the structure of DNA?"],
        topic="biology",
        sub_topic="molecular biology",
        training_type="sft"
    )
    question_id = add_result["question_ids"][0]
    print(f"  [OK] Question ID: {question_id}")
    
    # Step 2: Research
    print("\n[Step 2/6] Researching question...")
    research_result = await research_question_and_store(
        question_id=question_id,
        question="What is the structure of DNA?",
        topic="biology",
        sub_topic="molecular biology",
        training_type="sft"
    )
    
    if research_result["status"] != "success":
        print(f"  [X] Research failed: {research_result.get('error')}")
        return False
    
    print(f"  [OK] Research complete")
    print(f"    Quality score: {research_result['research']['quality_score']:.2f}")
    print(f"    Key concepts: {research_result['research']['key_concepts_count']}")
    print(f"    Sources: {len(research_result['research']['context_sources'])}")
    
    # Step 3: Verify research stored
    print("\n[Step 3/6] Verifying research in database...")
    question_data = db_tools.get_question_by_id(question_id)
    assert question_data["status"] == "researched"
    assert question_data["pipeline_stage"] == "ready_for_generation"
    print(f"  [OK] Research verified")
    print(f"    Status: {question_data['status']}")
    print(f"    Pipeline stage: {question_data['pipeline_stage']}")
    
    # Step 4: Generate training data
    print("\n[Step 4/6] Generating SFT training data...")
    generated_data = await generate_training_data(
        TrainingType.SFT,
        {
            'question': question_data["question"],
            'topic': question_data["topic"],
            'sub_topic': question_data["sub_topic"],
            'ground_truth_context': question_data["ground_truth_context"],
            'synthesized_context': question_data["synthesized_context"]
        }
    )
    print(f"  [OK] Data generated")
    print(f"    Instruction: {generated_data['instruction'][:60]}...")
    print(f"    Response length: {len(generated_data['response'])} chars")
    
    # Step 5: Review generated data
    print("\n[Step 5/6] Reviewing generated data...")
    review_result = await review_training_data(
        TrainingType.SFT,
        generated_data,
        ground_truth=question_data["ground_truth_context"]
    )
    print(f"  [OK] Review complete")
    print(f"    Quality score: {review_result['quality_score']:.2f}")
    print(f"    Review status: {review_result['review_status']}")
    print(f"    Detailed scores: {review_result['scores']}")
    
    # Step 6: Store approved data
    print("\n[Step 6/6] Storing approved data...")
    if review_result['review_status'] == 'approved':
        generated_data['quality_score'] = review_result['quality_score']
        generated_data['review_status'] = review_result['review_status']
        generated_data['reviewer_notes'] = review_result['reviewer_notes']
        
        store_result = db_tools.add_synthetic_data('sft', generated_data)
        print(f"  [OK] Stored with ID: {store_result['id']} in {store_result['table']}")
    else:
        print(f"  [!] Data not approved (status: {review_result['review_status']})")
    
    # Summary
    print("\n" + "=" * 70)
    print("  Pipeline Summary")
    print("=" * 70)
    print(f"  Question ID: {question_id}")
    print(f"  Research Quality: {research_result['research']['quality_score']:.2f}")
    print(f"  Generation: SUCCESS")
    print(f"  Review Quality: {review_result['quality_score']:.2f}")
    print(f"  Review Status: {review_result['review_status']}")
    print(f"  Final Status: {'APPROVED' if review_result['review_status'] == 'approved' else 'NEEDS WORK'}")
    print("=" * 70 + "\n")
    
    return review_result['review_status'] == 'approved'


async def test_research_for_multiple_types():
    """Test research workflow for different training types."""
    print("\n" + "=" * 70)
    print("  Multi-Type Research Test")
    print("=" * 70 + "\n")
    
    db_tools = DatabaseTools()
    test_cases = [
        {
            "question": "What is a covalent bond?",
            "topic": "chemistry",
            "sub_topic": "chemical bonding",
            "training_type": "dpo"
        },
        {
            "question": "How does photosynthesis work?",
            "topic": "biology",
            "sub_topic": "plant biology",
            "training_type": "grpo"
        }
    ]
    
    results = {}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"[Test {i}/{len(test_cases)}] Researching for {test_case['training_type'].upper()}...")
        
        # Add question
        add_result = db_tools.add_questions_to_database(
            questions=[test_case["question"]],
            topic=test_case["topic"],
            sub_topic=test_case["sub_topic"],
            training_type=test_case["training_type"]
        )
        question_id = add_result["question_ids"][0]
        
        # Research
        research_result = await research_question_and_store(
            question_id=question_id,
            question=test_case["question"],
            topic=test_case["topic"],
            sub_topic=test_case["sub_topic"],
            training_type=test_case["training_type"]
        )
        
        if research_result["status"] == "success":
            # Check training guidance
            import json
            synthesized = json.loads(research_result["research"]["synthesized_context"])
            guidance = synthesized.get("training_guidance", {})
            
            print(f"  [OK] Research complete for {test_case['training_type']}")
            print(f"    Quality: {research_result['research']['quality_score']:.2f}")
            print(f"    Training type: {guidance.get('training_type')}")
            print(f"    Focus areas: {guidance.get('focus_areas', [])}")
            
            results[test_case["training_type"]] = "success"
        else:
            print(f"  [X] Research failed: {research_result.get('error')}")
            results[test_case["training_type"]] = "failed"
    
    print("\n" + "=" * 70)
    print("  Multi-Type Results")
    print("=" * 70)
    for training_type, result in results.items():
        status = "[OK]" if result == "success" else "[X]"
        print(f"  {status} {training_type.upper()}: {result}")
    print("=" * 70 + "\n")
    
    return all(r == "success" for r in results.values())


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  RESEARCH INTEGRATION TEST SUITE")
    print("=" * 70 + "\n")
    
    try:
        pipeline_pass = asyncio.run(test_complete_pipeline())
        print(f"\n[Result 1] Complete Pipeline: {'PASS' if pipeline_pass else 'FAIL'}")
    except Exception as e:
        print(f"\n[ERROR] Complete pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        pipeline_pass = False
    
    try:
        multi_type_pass = asyncio.run(test_research_for_multiple_types())
        print(f"\n[Result 2] Multi-Type Research: {'PASS' if multi_type_pass else 'FAIL'}")
    except Exception as e:
        print(f"\n[ERROR] Multi-type research test failed: {str(e)}")
        multi_type_pass = False
    
    # Final summary
    print("\n" + "=" * 70)
    print("  FINAL RESULTS")
    print("=" * 70)
    if pipeline_pass and multi_type_pass:
        print("\n  [OK] ALL INTEGRATION TESTS PASSED!")
        print("\n  The complete pipeline with Research Agent is working:")
        print("    Question -> Research -> Generation -> Review -> Database")
        print("\n  Research Agent successfully integrated!")
    else:
        print("\n  [X] SOME TESTS FAILED")
        if not pipeline_pass:
            print("    - Complete pipeline test failed")
        if not multi_type_pass:
            print("    - Multi-type research test failed")
    print("\n" + "=" * 70 + "\n")
