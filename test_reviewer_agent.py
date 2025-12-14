"""
Test script for Reviewer Agent workflows.

Tests the validation of synthetic data for all training types.
"""

import asyncio
from src.orchestrator.reviewer_agent.workflows import (
    review_sft_data,
    review_grpo_data,
    review_dpo_data,
    review_qa_data,
    review_ppo_data,
    review_kto_data,
    review_orpo_data,
    review_rlhf_data,
    review_chat_data,
    review_training_data
)
from schema.synthetic_data import TrainingType


async def test_reviewer_workflows():
    """Test all reviewer workflows."""
    print("\n" + "=" * 70)
    print("  Testing Reviewer Agent Workflows")
    print("=" * 70 + "\n")
    
    results = {}
    
    # Test 1: SFT Review
    print("[Test 1/9] Testing SFT review...")
    try:
        sft_data = {
            "instruction": "What is photosynthesis?",
            "response": "Photosynthesis is the process by which plants convert sunlight into energy. It involves chlorophyll capturing light and converting CO2 and water into glucose and oxygen.",
            "topic": "biology",
            "sub_topic": "plant biology"
        }
        ground_truth = "Photosynthesis is a biological process where plants use sunlight to synthesize nutrients."
        
        review = await review_sft_data(sft_data, ground_truth)
        print(f"  [OK] SFT review complete")
        print(f"    Quality score: {review['quality_score']:.2f}")
        print(f"    Status: {review['review_status']}")
        print(f"    Scores: {review['scores']}")
        results['sft'] = 'PASS' if review['quality_score'] > 0 else 'FAIL'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['sft'] = 'FAIL'
    
    # Test 2: GRPO Review
    print("\n[Test 2/9] Testing GRPO review...")
    try:
        grpo_data = {
            "prompt": "Calculate 2 + 2",
            "reasoning": "Step 1: Identify the numbers to add (2 and 2). Step 2: Perform addition. Step 3: The result is 4. Therefore, the answer is 4.",
            "code": "def add(): return 2 + 2",
            "predicted_answer": "4",
            "is_correct": True
        }
        
        review = await review_grpo_data(grpo_data)
        print(f"  [OK] GRPO review complete")
        print(f"    Quality score: {review['quality_score']:.2f}")
        print(f"    Status: {review['review_status']}")
        results['grpo'] = 'PASS' if review['quality_score'] > 0 else 'FAIL'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['grpo'] = 'FAIL'
    
    # Test 3: DPO Review
    print("\n[Test 3/9] Testing DPO review...")
    try:
        dpo_data = {
            "prompt": "Explain gravity",
            "chosen": "Gravity is a fundamental force that attracts objects with mass toward each other. It keeps planets in orbit and gives weight to objects on Earth.",
            "rejected": "Gravity is a thing that makes stuff fall down.",
            "chosen_rating": 5.0,
            "rejected_rating": 2.0
        }
        
        review = await review_dpo_data(dpo_data)
        print(f"  [OK] DPO review complete")
        print(f"    Quality score: {review['quality_score']:.2f}")
        print(f"    Status: {review['review_status']}")
        print(f"    Preference clarity: {review['scores']['preference_clarity']:.2f}")
        results['dpo'] = 'PASS' if review['quality_score'] > 0 else 'FAIL'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['dpo'] = 'FAIL'
    
    # Test 4: QA Review
    print("\n[Test 4/9] Testing QA review...")
    try:
        qa_data = {
            "question": "What is DNA?",
            "answer": "DNA is the molecule that carries genetic information.",
            "reasoning": "DNA stores hereditary information in all living organisms."
        }
        
        review = await review_qa_data(qa_data)
        print(f"  [OK] QA review complete")
        print(f"    Quality score: {review['quality_score']:.2f}")
        print(f"    Status: {review['review_status']}")
        results['qa'] = 'PASS' if review['quality_score'] > 0 else 'FAIL'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['qa'] = 'FAIL'
    
    # Test 5: PPO Review
    print("\n[Test 5/9] Testing PPO review...")
    try:
        ppo_data = {
            "prompt": "Explain quantum physics",
            "response": "Quantum physics studies the behavior of matter and energy at atomic scales.",
            "reward": 0.85,
            "reward_components": {"accuracy": 0.9, "clarity": 0.8}
        }
        
        review = await review_ppo_data(ppo_data)
        print(f"  [OK] PPO review complete")
        print(f"    Quality score: {review['quality_score']:.2f}")
        print(f"    Status: {review['review_status']}")
        results['ppo'] = 'PASS' if review['quality_score'] > 0 else 'FAIL'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['ppo'] = 'FAIL'
    
    # Test 6: KTO Review
    print("\n[Test 6/9] Testing KTO review...")
    try:
        kto_data = {
            "prompt": "What is AI?",
            "response": "AI is artificial intelligence, the simulation of human intelligence by machines.",
            "is_desirable": True,
            "feedback_reason": "Clear and accurate definition"
        }
        
        review = await review_kto_data(kto_data)
        print(f"  [OK] KTO review complete")
        print(f"    Quality score: {review['quality_score']:.2f}")
        print(f"    Status: {review['review_status']}")
        results['kto'] = 'PASS' if review['quality_score'] > 0 else 'FAIL'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['kto'] = 'FAIL'
    
    # Test 7: ORPO Review
    print("\n[Test 7/9] Testing ORPO review...")
    try:
        orpo_data = {
            "prompt": "Explain atoms",
            "chosen": "Atoms are the basic building blocks of matter, consisting of protons, neutrons, and electrons.",
            "rejected": "Atoms are small things."
        }
        
        review = await review_orpo_data(orpo_data)
        print(f"  [OK] ORPO review complete")
        print(f"    Quality score: {review['quality_score']:.2f}")
        print(f"    Status: {review['review_status']}")
        results['orpo'] = 'PASS' if review['quality_score'] > 0 else 'FAIL'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['orpo'] = 'FAIL'
    
    # Test 8: RLHF Review
    print("\n[Test 8/9] Testing RLHF review...")
    try:
        rlhf_data = {
            "prompt": "What is chemistry?",
            "response_a": "Chemistry is the study of matter and its interactions.",
            "response_b": "Chemistry studies chemicals.",
            "preference": "a"
        }
        
        review = await review_rlhf_data(rlhf_data)
        print(f"  [OK] RLHF review complete")
        print(f"    Quality score: {review['quality_score']:.2f}")
        print(f"    Status: {review['review_status']}")
        results['rlhf'] = 'PASS' if review['quality_score'] > 0 else 'FAIL'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['rlhf'] = 'FAIL'
    
    # Test 9: Chat Review
    print("\n[Test 9/9] Testing Chat review...")
    try:
        chat_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help?"},
                {"role": "user", "content": "Tell me about space"},
                {"role": "assistant", "content": "Space is the vast expanse beyond Earth."}
            ],
            "num_turns": 2
        }
        
        review = await review_chat_data(chat_data)
        print(f"  [OK] Chat review complete")
        print(f"    Quality score: {review['quality_score']:.2f}")
        print(f"    Status: {review['review_status']}")
        results['chat'] = 'PASS' if review['quality_score'] > 0 else 'FAIL'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['chat'] = 'FAIL'
    
    # Test 10: Unified interface
    print("\n[Test 10] Testing unified review_training_data() interface...")
    try:
        test_data = {
            "instruction": "What is machine learning?",
            "response": "Machine learning is a subset of AI that enables systems to learn from data."
        }
        
        review = await review_training_data(TrainingType.SFT, test_data)
        print(f"  [OK] Unified interface works")
        print(f"    Quality score: {review['quality_score']:.2f}")
        results['unified'] = 'PASS'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['unified'] = 'FAIL'
    
    # Summary
    print("\n" + "=" * 70)
    print("  Test Results Summary")
    print("=" * 70)
    passed = sum(1 for r in results.values() if r == 'PASS')
    total = len(results)
    print(f"\n  Tests Passed: {passed}/{total}\n")
    
    for test_name, result in results.items():
        status_symbol = "[OK]" if result == "PASS" else "[X]"
        print(f"  {status_symbol} {test_name.upper()}: {result}")
    
    print("\n" + "=" * 70 + "\n")
    
    return passed == total


async def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 70)
    print("  Testing Edge Cases")
    print("=" * 70 + "\n")
    
    results = {}
    
    # Test: Missing required fields
    print("[Edge 1] Testing missing required fields...")
    try:
        bad_sft = {"instruction": "test"}  # Missing response
        review = await review_sft_data(bad_sft)
        if review['review_status'] == 'rejected' and review['quality_score'] == 0.0:
            print("  [OK] Correctly rejected incomplete data")
            results['missing_fields'] = 'PASS'
        else:
            print("  [X] Failed to reject incomplete data")
            results['missing_fields'] = 'FAIL'
    except Exception as e:
        print(f"  [X] Exception: {str(e)}")
        results['missing_fields'] = 'FAIL'
    
    # Test: Identical chosen/rejected
    print("\n[Edge 2] Testing identical chosen/rejected...")
    try:
        bad_dpo = {
            "prompt": "test",
            "chosen": "same response",
            "rejected": "same response"
        }
        review = await review_dpo_data(bad_dpo)
        if review['review_status'] == 'rejected':
            print("  [OK] Correctly rejected identical responses")
            results['identical_responses'] = 'PASS'
        else:
            print("  [X] Failed to reject identical responses")
            results['identical_responses'] = 'FAIL'
    except Exception as e:
        print(f"  [X] Exception: {str(e)}")
        results['identical_responses'] = 'FAIL'
    
    # Test: Invalid reward range
    print("\n[Edge 3] Testing invalid reward range...")
    try:
        bad_ppo = {
            "prompt": "test",
            "response": "test response",
            "reward": 999.0  # Way out of range
        }
        review = await review_ppo_data(bad_ppo)
        if review['scores']['reward_validity'] < 0.5:
            print("  [OK] Detected invalid reward range")
            results['invalid_reward'] = 'PASS'
        else:
            print("  [X] Failed to detect invalid reward")
            results['invalid_reward'] = 'FAIL'
    except Exception as e:
        print(f"  [X] Exception: {str(e)}")
        results['invalid_reward'] = 'FAIL'
    
    # Summary
    print("\n" + "=" * 70)
    print("  Edge Case Results")
    print("=" * 70)
    passed = sum(1 for r in results.values() if r == 'PASS')
    total = len(results)
    print(f"\n  Tests Passed: {passed}/{total}\n")
    
    for test_name, result in results.items():
        status_symbol = "[OK]" if result == "PASS" else "[X]"
        print(f"  {status_symbol} {test_name}: {result}")
    
    print("\n" + "=" * 70 + "\n")
    
    return passed == total


async def test_quality_thresholds():
    """Test quality score thresholds."""
    print("\n" + "=" * 70)
    print("  Testing Quality Thresholds")
    print("=" * 70 + "\n")
    
    # Test high quality (should be approved)
    print("[Threshold 1] Testing high quality data (expect approved)...")
    high_quality = {
        "instruction": "Explain the water cycle",
        "response": "The water cycle is the continuous movement of water on, above, and below the Earth's surface. It involves evaporation, condensation, precipitation, and collection. Water evaporates from bodies of water, forms clouds, falls as rain or snow, and returns to water bodies."
    }
    review = await review_sft_data(high_quality)
    print(f"  Score: {review['quality_score']:.2f}, Status: {review['review_status']}")
    
    # Test medium quality (should need revision)
    print("\n[Threshold 2] Testing medium quality data (expect needs_revision)...")
    medium_quality = {
        "instruction": "What is a cloud?",
        "response": "A cloud is water vapor in the sky."
    }
    review = await review_sft_data(medium_quality)
    print(f"  Score: {review['quality_score']:.2f}, Status: {review['review_status']}")
    
    # Test low quality (should be rejected)
    print("\n[Threshold 3] Testing low quality data (expect rejected)...")
    low_quality = {
        "instruction": "Explain physics",
        "response": "Physics."
    }
    review = await review_sft_data(low_quality)
    print(f"  Score: {review['quality_score']:.2f}, Status: {review['review_status']}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  Reviewer Agent Test Suite")
    print("=" * 70 + "\n")
    
    # Run workflow tests
    try:
        workflows_pass = asyncio.run(test_reviewer_workflows())
    except Exception as e:
        print(f"\n[ERROR] Workflow tests failed: {str(e)}")
        import traceback
        traceback.print_exc()
        workflows_pass = False
    
    # Run edge case tests
    try:
        edge_cases_pass = asyncio.run(test_edge_cases())
    except Exception as e:
        print(f"\n[ERROR] Edge case tests failed: {str(e)}")
        edge_cases_pass = False
    
    # Run threshold tests
    try:
        asyncio.run(test_quality_thresholds())
        threshold_pass = True
    except Exception as e:
        print(f"\n[ERROR] Threshold tests failed: {str(e)}")
        threshold_pass = False
    
    # Final summary
    print("\n" + "=" * 70)
    print("  Final Results")
    print("=" * 70)
    if workflows_pass and edge_cases_pass and threshold_pass:
        print("\n  [OK] ALL TESTS PASSED - Reviewer Agent is working correctly!\n")
    else:
        print("\n  [X] SOME TESTS FAILED - Review output above\n")
        if not workflows_pass:
            print("    - Workflow tests failed")
        if not edge_cases_pass:
            print("    - Edge case tests failed")
        if not threshold_pass:
            print("    - Threshold tests failed")
        print()
