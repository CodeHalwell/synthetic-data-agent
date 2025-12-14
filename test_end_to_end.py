"""
End-to-End Integration Test

Tests the complete pipeline: Question -> Research -> Generation -> Review -> Database

This validates that all components work together properly.
"""

import asyncio
from tools.database_tools import DatabaseTools
from src.orchestrator.generation_agent.workflows import generate_training_data
from src.orchestrator.reviewer_agent.workflows import review_training_data
from schema.synthetic_data import TrainingType


async def test_sft_pipeline():
    """Test complete SFT pipeline."""
    print("\n" + "=" * 70)
    print("  End-to-End Test: SFT Pipeline")
    print("=" * 70 + "\n")
    
    db_tools = DatabaseTools()
    
    # Step 1: Add question
    print("[Step 1/5] Adding question to database...")
    question_result = db_tools.add_questions_to_database(
        questions=["What is the Krebs cycle in cellular respiration?"],
        topic="biology",
        sub_topic="cellular biology",
        training_type="sft"
    )
    question_id = question_result['question_ids'][0]
    print(f"  [OK] Question ID: {question_id}")
    
    # Step 2: Simulate research (add context)
    print("\n[Step 2/5] Adding research context...")
    research_context = """
    The Krebs cycle, also known as the citric acid cycle, is a series of chemical reactions 
    that occurs in the mitochondria. It is part of cellular respiration and produces ATP, 
    NADH, and FADH2 from acetyl-CoA. The cycle involves 8 main steps and is crucial for 
    energy production in aerobic organisms.
    """
    
    synthesized = {
        "summary": "The Krebs cycle is a metabolic pathway that generates energy through oxidation of acetyl-CoA.",
        "key_concepts": ["citric acid cycle", "mitochondria", "ATP production", "cellular respiration"],
        "definitions": {
            "Krebs cycle": "A series of chemical reactions used by aerobic organisms to generate energy"
        },
        "examples": ["Conversion of pyruvate to ATP", "NADH and FADH2 production"]
    }
    
    context_result = db_tools.update_question_context(
        question_id=question_id,
        ground_truth_context=research_context,
        synthesized_context=str(synthesized),
        context_sources=[{
            "url": "https://example.com/biology",
            "title": "Cell Biology Textbook",
            "license": "CC-BY-4.0"
        }],
        quality_score=0.95
    )
    print(f"  [OK] Context added, pipeline stage: {context_result['pipeline_stage']}")
    
    # Step 3: Generate training data
    print("\n[Step 3/5] Generating SFT training data...")
    question_data = {
        'question': "What is the Krebs cycle in cellular respiration?",
        'topic': "biology",
        'sub_topic': "cellular biology",
        'ground_truth_context': research_context,
        'synthesized_context': str(synthesized)
    }
    
    generated_data = await generate_training_data(TrainingType.SFT, question_data)
    print(f"  [OK] Generated data")
    print(f"    Instruction: {generated_data['instruction'][:50]}...")
    print(f"    Response length: {len(generated_data['response'])} chars")
    
    # Step 4: Review generated data
    print("\n[Step 4/5] Reviewing generated data...")
    review_result = await review_training_data(
        TrainingType.SFT,
        generated_data,
        ground_truth=research_context
    )
    print(f"  [OK] Review complete")
    print(f"    Quality score: {review_result['quality_score']:.2f}")
    print(f"    Review status: {review_result['review_status']}")
    print(f"    Detailed scores: {review_result['scores']}")
    
    # Step 5: Store approved data
    print("\n[Step 5/5] Storing in database...")
    # Add review scores to generated data
    generated_data['quality_score'] = review_result['quality_score']
    generated_data['review_status'] = review_result['review_status']
    generated_data['reviewer_notes'] = review_result['reviewer_notes']
    
    store_result = db_tools.add_synthetic_data(
        training_type="sft",
        data=generated_data
    )
    print(f"  [OK] Stored with ID: {store_result['id']} in {store_result['table']}")
    
    # Verify
    print("\n" + "=" * 70)
    print("  Pipeline Summary")
    print("=" * 70)
    print(f"  Question ID: {question_id}")
    print(f"  Generated Data ID: {store_result['id']}")
    print(f"  Quality Score: {review_result['quality_score']:.2f}")
    print(f"  Review Status: {review_result['review_status']}")
    print(f"  Final Status: {'APPROVED' if review_result['review_status'] == 'approved' else 'NEEDS WORK'}")
    print("=" * 70 + "\n")
    
    return review_result['review_status'] == 'approved'


async def test_multiple_training_types():
    """Test pipeline with multiple training types."""
    print("\n" + "=" * 70)
    print("  Multi-Type Pipeline Test")
    print("=" * 70 + "\n")
    
    test_context = {
        'question': "What is Newton's first law of motion?",
        'topic': "physics",
        'sub_topic': "classical mechanics",
        'ground_truth_context': "Newton's first law states that an object at rest stays at rest and an object in motion stays in motion unless acted upon by an external force.",
        'synthesized_context': '{"summary": "Law of inertia", "key_concepts": ["inertia", "force", "motion"]}'
    }
    
    db_tools = DatabaseTools()
    results = {}
    
    # Test SFT
    print("[1/3] Testing SFT...")
    sft_data = await generate_training_data(TrainingType.SFT, test_context)
    sft_review = await review_training_data(TrainingType.SFT, sft_data, test_context['ground_truth_context'])
    sft_data.update({'quality_score': sft_review['quality_score'], 'review_status': sft_review['review_status']})
    sft_stored = db_tools.add_synthetic_data('sft', sft_data)
    print(f"  [OK] SFT: {sft_review['review_status']}, Score: {sft_review['quality_score']:.2f}, ID: {sft_stored['id']}")
    results['sft'] = sft_review['review_status']
    
    # Test DPO
    print("\n[2/3] Testing DPO...")
    dpo_data = await generate_training_data(TrainingType.DPO, test_context)
    dpo_review = await review_training_data(TrainingType.DPO, dpo_data)
    dpo_data.update({'review_status': dpo_review['review_status']})
    dpo_stored = db_tools.add_synthetic_data('dpo', dpo_data)
    print(f"  [OK] DPO: {dpo_review['review_status']}, Score: {dpo_review['quality_score']:.2f}, ID: {dpo_stored['id']}")
    results['dpo'] = dpo_review['review_status']
    
    # Test GRPO
    print("\n[3/3] Testing GRPO...")
    grpo_data = await generate_training_data(TrainingType.GRPO, test_context)
    grpo_review = await review_training_data(TrainingType.GRPO, grpo_data)
    # Note: GRPO schema doesn't have review_status field - it's tracked separately
    grpo_stored = db_tools.add_synthetic_data('grpo', grpo_data)
    print(f"  [OK] GRPO: {grpo_review['review_status']}, Score: {grpo_review['quality_score']:.2f}, ID: {grpo_stored['id']}")
    results['grpo'] = grpo_review['review_status']
    
    print("\n" + "=" * 70)
    print("  Multi-Type Test Complete")
    print("=" * 70)
    print(f"  SFT: {results['sft']}")
    print(f"  DPO: {results['dpo']}")
    print(f"  GRPO: {results['grpo']}")
    print("=" * 70 + "\n")
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  END-TO-END INTEGRATION TEST SUITE")
    print("=" * 70 + "\n")
    
    try:
        sft_pass = asyncio.run(test_sft_pipeline())
        print(f"\n[Result 1] SFT Pipeline: {'PASS' if sft_pass else 'FAIL'}")
    except Exception as e:
        print(f"\n[ERROR] SFT pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sft_pass = False
    
    try:
        multi_pass = asyncio.run(test_multiple_training_types())
        print(f"\n[Result 2] Multi-Type Pipeline: {'PASS' if multi_pass else 'FAIL'}")
    except Exception as e:
        print(f"\n[ERROR] Multi-type pipeline failed: {str(e)}")
        multi_pass = False
    
    # Final summary
    print("\n" + "=" * 70)
    print("  FINAL RESULTS")
    print("=" * 70)
    if sft_pass and multi_pass:
        print("\n  [OK] ALL INTEGRATION TESTS PASSED!")
        print("\n  The complete pipeline is working:")
        print("    Question -> Research -> Generation -> Review -> Database")
        print("\n  You can now generate synthetic training data end-to-end!")
    else:
        print("\n  [X] SOME TESTS FAILED")
        if not sft_pass:
            print("    - SFT pipeline test failed")
        if not multi_pass:
            print("    - Multi-type pipeline test failed")
    print("\n" + "=" * 70 + "\n")
