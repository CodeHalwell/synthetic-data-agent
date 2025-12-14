"""
Test script for Research Agent workflows.

Tests research functionality, context synthesis, and database integration.
"""

import asyncio
import json
from src.orchestrator.research_agent.workflows import (
    research_question,
    research_question_and_store,
    research_questions_batch
)
from tools.database_tools import DatabaseTools
from tools.web_tools import WebTools


async def test_research_question():
    """Test basic research_question function."""
    print("\n" + "=" * 70)
    print("  Testing Research Question Function")
    print("=" * 70 + "\n")
    
    print("[Test 1] Researching a chemistry question...")
    try:
        result = await research_question(
            question="What is a covalent bond?",
            topic="chemistry",
            sub_topic="chemical bonding",
            training_type="sft"
        )
        
        print(f"  [OK] Research complete")
        print(f"    Quality score: {result['quality_score']:.2f}")
        print(f"    Key concepts: {result['key_concepts_count']}")
        print(f"    Examples: {result['examples_count']}")
        print(f"    Sources: {len(result['context_sources'])}")
        print(f"    Ground truth length: {len(result['ground_truth_context'])} chars")
        print(f"    Synthesized context length: {len(result['synthesized_context'])} chars")
        
        # Verify structure
        assert "ground_truth_context" in result
        assert "synthesized_context" in result
        assert "context_sources" in result
        assert "quality_score" in result
        assert 0.0 <= result["quality_score"] <= 1.0
        
        # Parse synthesized context
        synthesized = json.loads(result["synthesized_context"])
        assert "summary" in synthesized
        assert "key_concepts" in synthesized
        assert "definitions" in synthesized
        
        print("  [OK] Structure validation passed")
        return True
        
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_research_different_types():
    """Test research for different question types."""
    print("\n[Test 2] Testing different question types...")
    
    test_cases = [
        {
            "question": "What is photosynthesis?",
            "topic": "biology",
            "sub_topic": "plant biology",
            "type": "definition"
        },
        {
            "question": "How does the Krebs cycle work?",
            "topic": "biology",
            "sub_topic": "cellular biology",
            "type": "process"
        },
        {
            "question": "Why is DNA double-stranded?",
            "topic": "biology",
            "sub_topic": "molecular biology",
            "type": "explanation"
        }
    ]
    
    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        try:
            result = await research_question(
                question=test_case["question"],
                topic=test_case["topic"],
                sub_topic=test_case["sub_topic"]
            )
            
            synthesized = json.loads(result["synthesized_context"])
            question_type = synthesized.get("question_type", "")
            
            print(f"  [OK] Test {i}: {test_case['type']} -> detected as {question_type}")
            assert result["quality_score"] > 0
            passed += 1
            
        except Exception as e:
            print(f"  [X] Test {i} failed: {str(e)}")
    
    print(f"\n  Results: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


async def test_research_and_store():
    """Test research_question_and_store workflow."""
    print("\n[Test 3] Testing research and store workflow...")
    
    db_tools = DatabaseTools()
    
    try:
        # Step 1: Add a question to database
        print("  Step 1: Adding question to database...")
        add_result = db_tools.add_questions_to_database(
            questions=["What is a polymer?"],
            topic="chemistry",
            sub_topic="organic chemistry",
            training_type="sft"
        )
        
        question_id = add_result["question_ids"][0]
        print(f"    [OK] Question ID: {question_id}")
        
        # Step 2: Research and store
        print("  Step 2: Researching and storing...")
        research_result = await research_question_and_store(
            question_id=question_id,
            question="What is a polymer?",
            topic="chemistry",
            sub_topic="organic chemistry",
            training_type="sft"
        )
        
        if research_result["status"] == "success":
            print(f"    [OK] Research stored successfully")
            print(f"    Pipeline stage: {research_result['pipeline_stage']}")
            print(f"    Quality score: {research_result['research']['quality_score']:.2f}")
            
            # Step 3: Verify in database
            print("  Step 3: Verifying in database...")
            question_data = db_tools.get_question_by_id(question_id)
            
            assert question_data is not None
            assert question_data["status"] == "researched"
            assert question_data["pipeline_stage"] == "ready_for_generation"
            assert question_data["ground_truth_context"] is not None
            assert question_data["synthesized_context"] is not None
            assert question_data["context_sources"] is not None
            assert question_data["context_quality_score"] is not None
            
            print(f"    [OK] Database verification passed")
            print(f"    Status: {question_data['status']}")
            print(f"    Pipeline stage: {question_data['pipeline_stage']}")
            print(f"    Quality score: {question_data['context_quality_score']:.2f}")
            
            return True
        else:
            print(f"    [X] Research failed: {research_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_batch_research():
    """Test batch research workflow."""
    print("\n[Test 4] Testing batch research workflow...")
    
    db_tools = DatabaseTools()
    
    try:
        # Step 1: Add multiple questions
        print("  Step 1: Adding questions to database...")
        add_result = db_tools.add_questions_to_database(
            questions=[
                "What is an enzyme?",
                "What is a catalyst?",
                "How do enzymes work?"
            ],
            topic="biology",
            sub_topic="biochemistry",
            training_type="sft"
        )
        
        question_ids = add_result["question_ids"]
        print(f"    [OK] Added {len(question_ids)} questions: {question_ids}")
        
        # Step 2: Research batch
        print("  Step 2: Researching batch...")
        batch_result = await research_questions_batch(
            question_ids=question_ids,
            database_tools=db_tools
        )
        
        print(f"    [OK] Batch research complete")
        print(f"    Total: {batch_result['total']}")
        print(f"    Researched: {batch_result['researched']}")
        print(f"    Failed: {batch_result['failed']}")
        
        # Step 3: Verify all were researched
        print("  Step 3: Verifying results...")
        for result in batch_result["results"]:
            if result["status"] == "success":
                question_data = db_tools.get_question_by_id(result["question_id"])
                assert question_data["status"] == "researched"
                assert question_data["pipeline_stage"] == "ready_for_generation"
                print(f"    [OK] Question {result['question_id']}: researched")
            else:
                print(f"    [X] Question {result.get('question_id')}: {result.get('error')}")
        
        success_count = sum(1 for r in batch_result["results"] if r.get("status") == "success")
        print(f"\n  Results: {success_count}/{batch_result['total']} successfully researched")
        
        return success_count == batch_result["total"]
        
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_context_synthesis():
    """Test context synthesis quality."""
    print("\n[Test 5] Testing context synthesis quality...")
    
    try:
        result = await research_question(
            question="What is quantum entanglement?",
            topic="physics",
            sub_topic="quantum mechanics",
            training_type="grpo"
        )
        
        synthesized = json.loads(result["synthesized_context"])
        
        # Check required fields
        required_fields = ["summary", "key_concepts", "definitions", "examples", "training_guidance"]
        missing = [f for f in required_fields if f not in synthesized]
        
        if missing:
            print(f"  [X] Missing fields: {missing}")
            return False
        
        print(f"  [OK] All required fields present")
        print(f"    Summary: {len(synthesized['summary'])} chars")
        print(f"    Key concepts: {len(synthesized['key_concepts'])}")
        print(f"    Definitions: {len(synthesized['definitions'])}")
        print(f"    Examples: {len(synthesized['examples'])}")
        print(f"    Training type: {synthesized.get('training_guidance', {}).get('training_type')}")
        
        # Check training guidance
        guidance = synthesized.get("training_guidance", {})
        if guidance.get("training_type") == "grpo":
            assert "focus_areas" in guidance
            assert "quality_criteria" in guidance
            print(f"  [OK] Training guidance present for GRPO")
        
        return True
        
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_source_tracking():
    """Test source tracking and license compliance."""
    print("\n[Test 6] Testing source tracking...")
    
    try:
        result = await research_question(
            question="What is machine learning?",
            topic="computer science",
            sub_topic="artificial intelligence"
        )
        
        sources = result["context_sources"]
        
        print(f"  [OK] Found {len(sources)} sources")
        
        # Check source structure
        for i, source in enumerate(sources, 1):
            required_fields = ["url", "title", "license", "type"]
            missing = [f for f in required_fields if f not in source]
            
            if missing:
                print(f"  [X] Source {i} missing fields: {missing}")
                return False
            
            print(f"    Source {i}: {source['title']} ({source['license']})")
        
        # Check license compliance
        licenses = [s.get("license") for s in sources]
        print(f"  [OK] Licenses tracked: {set(licenses)}")
        
        return True
        
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_quality_scoring():
    """Test quality score calculation."""
    print("\n[Test 7] Testing quality score calculation...")
    
    test_cases = [
        {
            "question": "What is DNA?",
            "topic": "biology",
            "sub_topic": "genetics",
            "expected_min": 0.5
        },
        {
            "question": "Explain photosynthesis in detail with examples",
            "topic": "biology",
            "sub_topic": "plant biology",
            "expected_min": 0.6
        }
    ]
    
    passed = 0
    for i, test_case in enumerate(test_cases, 1):
        try:
            result = await research_question(
                question=test_case["question"],
                topic=test_case["topic"],
                sub_topic=test_case["sub_topic"]
            )
            
            score = result["quality_score"]
            expected_min = test_case["expected_min"]
            
            if score >= expected_min:
                print(f"  [OK] Test {i}: Score {score:.2f} >= {expected_min}")
                passed += 1
            else:
                print(f"  [X] Test {i}: Score {score:.2f} < {expected_min}")
                
        except Exception as e:
            print(f"  [X] Test {i} failed: {str(e)}")
    
    print(f"\n  Results: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


async def run_all_tests():
    """Run all research agent tests."""
    print("\n" + "=" * 70)
    print("  Research Agent Test Suite")
    print("=" * 70 + "\n")
    
    results = {}
    
    # Run all tests
    try:
        results["research_question"] = await test_research_question()
    except Exception as e:
        print(f"\n[ERROR] test_research_question failed: {str(e)}")
        results["research_question"] = False
    
    try:
        results["different_types"] = await test_research_different_types()
    except Exception as e:
        print(f"\n[ERROR] test_research_different_types failed: {str(e)}")
        results["different_types"] = False
    
    try:
        results["research_and_store"] = await test_research_and_store()
    except Exception as e:
        print(f"\n[ERROR] test_research_and_store failed: {str(e)}")
        results["research_and_store"] = False
    
    try:
        results["batch_research"] = await test_batch_research()
    except Exception as e:
        print(f"\n[ERROR] test_batch_research failed: {str(e)}")
        results["batch_research"] = False
    
    try:
        results["context_synthesis"] = await test_context_synthesis()
    except Exception as e:
        print(f"\n[ERROR] test_context_synthesis failed: {str(e)}")
        results["context_synthesis"] = False
    
    try:
        results["source_tracking"] = await test_source_tracking()
    except Exception as e:
        print(f"\n[ERROR] test_source_tracking failed: {str(e)}")
        results["source_tracking"] = False
    
    try:
        results["quality_scoring"] = await test_quality_scoring()
    except Exception as e:
        print(f"\n[ERROR] test_quality_scoring failed: {str(e)}")
        results["quality_scoring"] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("  Test Results Summary")
    print("=" * 70)
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\n  Tests Passed: {passed}/{total}\n")
    
    for test_name, result in results.items():
        status_symbol = "[OK]" if result else "[X]"
        print(f"  {status_symbol} {test_name}: {'PASS' if result else 'FAIL'}")
    
    print("\n" + "=" * 70 + "\n")
    
    if passed == total:
        print("  [OK] ALL TESTS PASSED - Research Agent is working correctly!\n")
    else:
        print("  [X] SOME TESTS FAILED - Review output above\n")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_all_tests())
