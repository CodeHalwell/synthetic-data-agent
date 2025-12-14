"""
Test script for Generation Agent workflows.

Tests the generation of synthetic data for all training types.
"""

import asyncio
from src.orchestrator.generation_agent.workflows import (
    generate_sft_data,
    generate_grpo_data,
    generate_dpo_data,
    generate_qa_data,
    generate_ppo_data,
    generate_kto_data,
    generate_orpo_data,
    generate_rlhf_data,
    generate_chat_data,
    generate_training_data
)
from schema.synthetic_data import TrainingType


# Sample test data
TEST_QUESTION = "What is the mechanism of SN2 reactions in organic chemistry?"
TEST_TOPIC = "chemistry"
TEST_SUB_TOPIC = "organic chemistry"
TEST_GROUND_TRUTH = """
The SN2 mechanism proceeds through a single concerted step where the nucleophile 
attacks the electrophile from the backside, causing inversion of configuration at 
the chiral center. This mechanism is second-order, depending on both the concentration 
of the substrate and the nucleophile. The rate of SN2 reactions is affected by steric 
hindrance, with primary alkyl halides reacting fastest and tertiary alkyl halides 
reacting slowest or not at all.
"""
TEST_SYNTHESIZED = """{
    "summary": "The SN2 mechanism is a nucleophilic substitution reaction that occurs in a single concerted step with backside attack.",
    "key_concepts": ["backside attack", "inversion of configuration", "bimolecular", "steric hindrance"],
    "definitions": {
        "SN2": "Substitution Nucleophilic Bimolecular - a reaction mechanism with a single transition state",
        "inversion": "Walden inversion - stereochemical flip at the reaction center"
    },
    "examples": [
        "Reaction of methyl bromide with hydroxide ion",
        "Formation of alcohols from alkyl halides using aqueous hydroxide"
    ]
}"""


async def test_generation_workflows():
    """Test all generation workflows."""
    print("\n" + "=" * 70)
    print("  Testing Generation Agent Workflows")
    print("=" * 70 + "\n")
    
    results = {}
    
    # Test 1: SFT
    print("[Test 1/9] Testing SFT generation...")
    try:
        sft_data = await generate_sft_data(
            TEST_QUESTION, TEST_TOPIC, TEST_SUB_TOPIC,
            TEST_GROUND_TRUTH, TEST_SYNTHESIZED
        )
        print(f"  [OK] Generated SFT data with {len(sft_data['response'])} character response")
        print(f"    Fields: {list(sft_data.keys())}")
        results['sft'] = 'PASS'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['sft'] = 'FAIL'
    
    # Test 2: GRPO
    print("\n[Test 2/9] Testing GRPO generation...")
    try:
        grpo_data = await generate_grpo_data(
            TEST_QUESTION, TEST_TOPIC, TEST_SUB_TOPIC,
            TEST_GROUND_TRUTH, TEST_SYNTHESIZED
        )
        print(f"  [OK] Generated GRPO data with reasoning and code")
        print(f"    Has reasoning: {bool(grpo_data.get('reasoning'))}")
        print(f"    Has code: {bool(grpo_data.get('code'))}")
        print(f"    Is correct: {grpo_data.get('is_correct')}")
        results['grpo'] = 'PASS'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['grpo'] = 'FAIL'
    
    # Test 3: DPO
    print("\n[Test 3/9] Testing DPO generation...")
    try:
        dpo_data = await generate_dpo_data(
            TEST_QUESTION, TEST_TOPIC, TEST_SUB_TOPIC,
            TEST_GROUND_TRUTH, TEST_SYNTHESIZED
        )
        print(f"  [OK] Generated DPO preference pair")
        print(f"    Chosen length: {len(dpo_data['chosen'])} chars")
        print(f"    Rejected length: {len(dpo_data['rejected'])} chars")
        print(f"    Chosen rating: {dpo_data['chosen_rating']}")
        print(f"    Rejected rating: {dpo_data['rejected_rating']}")
        results['dpo'] = 'PASS'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['dpo'] = 'FAIL'
    
    # Test 4: QA
    print("\n[Test 4/9] Testing QA generation...")
    try:
        qa_data = await generate_qa_data(
            TEST_QUESTION, TEST_TOPIC, TEST_SUB_TOPIC,
            TEST_GROUND_TRUTH, TEST_SYNTHESIZED
        )
        print(f"  [OK] Generated QA pair")
        print(f"    Question: {qa_data['question'][:50]}...")
        print(f"    Answer length: {len(qa_data['answer'])} chars")
        results['qa'] = 'PASS'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['qa'] = 'FAIL'
    
    # Test 5: PPO
    print("\n[Test 5/9] Testing PPO generation...")
    try:
        ppo_data = await generate_ppo_data(
            TEST_QUESTION, TEST_TOPIC, TEST_SUB_TOPIC,
            TEST_GROUND_TRUTH, TEST_SYNTHESIZED
        )
        print(f"  [OK] Generated PPO data with reward signal")
        print(f"    Reward: {ppo_data['reward']:.3f}")
        print(f"    Components: {list(ppo_data['reward_components'].keys())}")
        results['ppo'] = 'PASS'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['ppo'] = 'FAIL'
    
    # Test 6: KTO
    print("\n[Test 6/9] Testing KTO generation...")
    try:
        kto_data = await generate_kto_data(
            TEST_QUESTION, TEST_TOPIC, TEST_SUB_TOPIC,
            TEST_GROUND_TRUTH, TEST_SYNTHESIZED
        )
        print(f"  [OK] Generated KTO binary feedback")
        print(f"    Is desirable: {kto_data['is_desirable']}")
        print(f"    Feedback: {kto_data['feedback_reason'][:60]}...")
        results['kto'] = 'PASS'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['kto'] = 'FAIL'
    
    # Test 7: ORPO
    print("\n[Test 7/9] Testing ORPO generation...")
    try:
        orpo_data = await generate_orpo_data(
            TEST_QUESTION, TEST_TOPIC, TEST_SUB_TOPIC,
            TEST_GROUND_TRUTH, TEST_SYNTHESIZED
        )
        print(f"  [OK] Generated ORPO combined data")
        print(f"    Has chosen: {bool(orpo_data.get('chosen'))}")
        print(f"    Has rejected: {bool(orpo_data.get('rejected'))}")
        results['orpo'] = 'PASS'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['orpo'] = 'FAIL'
    
    # Test 8: RLHF
    print("\n[Test 8/9] Testing RLHF generation...")
    try:
        rlhf_data = await generate_rlhf_data(
            TEST_QUESTION, TEST_TOPIC, TEST_SUB_TOPIC,
            TEST_GROUND_TRUTH, TEST_SYNTHESIZED
        )
        print(f"  [OK] Generated RLHF comparison pair")
        print(f"    Preference: {rlhf_data['preference']}")
        print(f"    Helpfulness: {rlhf_data['helpfulness']}")
        results['rlhf'] = 'PASS'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['rlhf'] = 'FAIL'
    
    # Test 9: Chat
    print("\n[Test 9/9] Testing Chat generation...")
    try:
        chat_data = await generate_chat_data(
            TEST_QUESTION, TEST_TOPIC, TEST_SUB_TOPIC,
            TEST_GROUND_TRUTH, TEST_SYNTHESIZED
        )
        print(f"  [OK] Generated multi-turn conversation")
        print(f"    Number of turns: {chat_data['num_turns']}")
        print(f"    Number of messages: {len(chat_data['messages'])}")
        results['chat'] = 'PASS'
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        results['chat'] = 'FAIL'
    
    # Test 10: Unified interface
    print("\n[Test 10] Testing unified generate_training_data() interface...")
    try:
        question_data = {
            'question': TEST_QUESTION,
            'topic': TEST_TOPIC,
            'sub_topic': TEST_SUB_TOPIC,
            'ground_truth_context': TEST_GROUND_TRUTH,
            'synthesized_context': TEST_SYNTHESIZED
        }
        
        unified_sft = await generate_training_data(TrainingType.SFT, question_data)
        print(f"  [OK] Unified interface works for SFT")
        
        unified_dpo = await generate_training_data(TrainingType.DPO, question_data)
        print(f"  [OK] Unified interface works for DPO")
        
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


async def test_with_database():
    """Test generation with actual database insertion."""
    print("\n" + "=" * 70)
    print("  Testing Generation Agent with Database")
    print("=" * 70 + "\n")
    
    from tools.database_tools import DatabaseTools
    db_tools = DatabaseTools()
    
    # Add a test question
    print("[1] Adding test question to database...")
    result = db_tools.add_questions_to_database(
        questions=[TEST_QUESTION],
        topic=TEST_TOPIC,
        sub_topic=TEST_SUB_TOPIC,
        training_type="sft"
    )
    question_id = result['question_ids'][0]
    print(f"  [OK] Question added with ID: {question_id}")
    
    # Simulate research completion
    print("\n[2] Simulating research completion...")
    db_tools.update_question_context(
        question_id=question_id,
        ground_truth_context=TEST_GROUND_TRUTH,
        synthesized_context=TEST_SYNTHESIZED,
        context_sources=[{
            "url": "https://example.com/organic-chemistry",
            "title": "Organic Chemistry Textbook",
            "license": "CC-BY-4.0"
        }],
        quality_score=0.92
    )
    print(f"  [OK] Research context added")
    
    # Generate SFT data
    print("\n[3] Generating SFT training data...")
    question_data = {
        'question': TEST_QUESTION,
        'topic': TEST_TOPIC,
        'sub_topic': TEST_SUB_TOPIC,
        'ground_truth_context': TEST_GROUND_TRUTH,
        'synthesized_context': TEST_SYNTHESIZED
    }
    
    sft_data = await generate_training_data(TrainingType.SFT, question_data)
    print(f"  [OK] Generated SFT data")
    
    # Store in database
    print("\n[4] Storing in database...")
    store_result = db_tools.add_synthetic_data(
        training_type="sft",
        data=sft_data
    )
    print(f"  [OK] Stored in {store_result['table']} with ID: {store_result['id']}")
    
    print("\n" + "=" * 70)
    print("  Database Integration Test: PASS [OK]")
    print("=" * 70 + "\n")
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  Generation Agent Test Suite")
    print("=" * 70 + "\n")
    
    # Run workflow tests
    try:
        workflows_pass = asyncio.run(test_generation_workflows())
    except Exception as e:
        print(f"\n[ERROR] Workflow tests failed: {str(e)}")
        workflows_pass = False
    
    # Run database integration test
    try:
        db_pass = asyncio.run(test_with_database())
    except Exception as e:
        print(f"\n[ERROR] Database test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        db_pass = False
    
    # Final summary
    print("\n" + "=" * 70)
    print("  Final Results")
    print("=" * 70)
    if workflows_pass and db_pass:
        print("\n  [OK] ALL TESTS PASSED - Generation Agent is working correctly!\n")
    else:
        print("\n  [X] SOME TESTS FAILED - Review output above\n")
        if not workflows_pass:
            print("    - Workflow generation tests failed")
        if not db_pass:
            print("    - Database integration test failed")
        print()

