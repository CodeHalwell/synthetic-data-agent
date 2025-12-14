"""
Test suite for Orchestrator workflows.

Tests the complete pipeline coordination and workflow integration.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from src.orchestrator.workflows import (
    generate_synthetic_data,
    process_pending_questions,
    resume_failed_questions,
    get_pipeline_status,
    PipelineProgress
)
from tools.database_tools import DatabaseTools


async def test_generate_synthetic_data():
    """Test the main generate_synthetic_data workflow."""
    print("\n" + "=" * 70)
    print("  Testing generate_synthetic_data() Workflow")
    print("=" * 70 + "\n")
    
    db_tools = DatabaseTools()
    
    try:
        # Test with a small batch
        questions = [
            "What is a molecule?",
            "What is an atom?"
        ]
        
        print("[Test] Generating synthetic data for 2 chemistry questions...")
        result = await generate_synthetic_data(
            questions=questions,
            topic="chemistry",
            sub_topic="basic concepts",
            training_type="sft",
            database_tools=db_tools,
            max_questions=2
        )
        
        print(f"  Status: {result['status']}")
        print(f"  Progress: {result['progress']}")
        print(f"  Summary: {result['summary']}")
        
        # Verify structure
        assert "status" in result
        assert "progress" in result
        assert "results" in result
        assert "summary" in result
        
        # Verify progress structure
        progress = result["progress"]
        assert "total" in progress
        assert "stages" in progress
        assert "completion_percentage" in progress
        
        # Verify summary structure
        summary = result["summary"]
        assert "total_questions" in summary
        assert "researched" in summary
        assert "generated" in summary
        assert "reviewed" in summary
        assert "approved" in summary
        assert "success_rate" in summary
        
        print(f"  [OK] Workflow structure validated")
        print(f"  [OK] Processed {summary['total_questions']} questions")
        print(f"  [OK] Approved {summary['approved']} items")
        print(f"  [OK] Success rate: {summary['success_rate']:.1f}%")
        
        return result["status"] in ["success", "partial"]
        
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_process_pending_questions():
    """Test processing pending questions from database."""
    print("\n[Test] Testing process_pending_questions()...")
    
    db_tools = DatabaseTools()
    
    try:
        # First, add some questions
        add_result = db_tools.add_questions_to_database(
            questions=[
                "What is DNA?",
                "What is RNA?"
            ],
            topic="biology",
            sub_topic="molecular biology",
            training_type="sft"
        )
        
        if add_result.get("status") != "success":
            print(f"  [X] Failed to add questions: {add_result.get('error')}")
            return False
        
        print(f"  [OK] Added {len(add_result['question_ids'])} questions")
        
        # Process pending questions
        result = await process_pending_questions(
            topic="biology",
            sub_topic="molecular biology",
            training_type="sft",
            database_tools=db_tools,
            limit=2
        )
        
        print(f"  Status: {result['status']}")
        if "summary" in result:
            print(f"  Summary: {result['summary']}")
        
        assert "status" in result
        print(f"  [OK] Processed pending questions")
        
        return result["status"] in ["success", "partial"]
        
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_pipeline_status():
    """Test getting pipeline status."""
    print("\n[Test] Testing get_pipeline_status()...")
    
    db_tools = DatabaseTools()
    
    try:
        status = await get_pipeline_status(
            topic="chemistry",
            sub_topic="basic concepts",
            database_tools=db_tools
        )
        
        print(f"  Status: {status['status']}")
        print(f"  Stages: {status['stages']}")
        
        assert "status" in status
        assert "stages" in status
        assert "pending" in status["stages"]
        assert "ready_for_generation" in status["stages"]
        
        print(f"  [OK] Pipeline status retrieved")
        print(f"    Pending: {status['stages']['pending']}")
        print(f"    Ready for generation: {status['stages']['ready_for_generation']}")
        
        return True
        
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_pipeline_progress():
    """Test PipelineProgress tracking."""
    print("\n[Test] Testing PipelineProgress...")
    
    try:
        progress = PipelineProgress(total_questions=5)
        
        # Simulate progress
        progress.update("questions_added", 5)
        progress.update("researched", 4)
        progress.update("generated", 4)
        progress.update("reviewed", 3)
        progress.update("approved", 2)
        progress.add_error(1, "generation", "Test error")
        
        summary = progress.get_summary()
        
        print(f"  Total: {summary['total']}")
        print(f"  Stages: {summary['stages']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Completion: {summary['completion_percentage']:.1f}%")
        
        assert summary["total"] == 5
        assert summary["stages"]["questions_added"] == 5
        assert summary["stages"]["approved"] == 2
        assert summary["errors"] == 1
        assert len(progress.errors) == 1
        
        print(f"  [OK] Progress tracking validated")
        
        return True
        
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_complete_pipeline_integration():
    """Test complete pipeline end-to-end."""
    print("\n" + "=" * 70)
    print("  Testing Complete Pipeline Integration")
    print("=" * 70 + "\n")
    
    db_tools = DatabaseTools()
    
    try:
        # Test complete workflow
        questions = [
            "What is photosynthesis?",
            "How does photosynthesis work?"
        ]
        
        print("[Test] Running complete pipeline...")
        result = await generate_synthetic_data(
            questions=questions,
            topic="biology",
            sub_topic="plant biology",
            training_type="sft",
            database_tools=db_tools,
            max_questions=2
        )
        
        print(f"\n  Pipeline Results:")
        print(f"    Status: {result['status']}")
        print(f"    Total questions: {result['summary']['total_questions']}")
        print(f"    Researched: {result['summary']['researched']}")
        print(f"    Generated: {result['summary']['generated']}")
        print(f"    Reviewed: {result['summary']['reviewed']}")
        print(f"    Approved: {result['summary']['approved']}")
        print(f"    Success rate: {result['summary']['success_rate']:.1f}%")
        
        # Verify pipeline completed
        assert result["status"] in ["success", "partial"]
        assert result["summary"]["researched"] > 0
        assert result["summary"]["generated"] > 0
        assert result["summary"]["reviewed"] > 0
        
        # Check individual results
        if result["results"]:
            for res in result["results"]:
                if res.get("status") == "success":
                    print(f"\n  [OK] Question {res['question_id']}:")
                    print(f"    Generated ID: {res.get('generated_id')}")
                    print(f"    Quality score: {res.get('quality_score', 0):.2f}")
                    print(f"    Review status: {res.get('review_status')}")
        
        print(f"\n  [OK] Complete pipeline test passed")
        
        return True
        
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test error handling in workflows."""
    print("\n[Test] Testing error handling...")
    
    db_tools = DatabaseTools()
    
    try:
        # Test with invalid input
        result = await generate_synthetic_data(
            questions=[],  # Empty list
            topic="test",
            sub_topic="test",
            training_type="sft",
            database_tools=db_tools
        )
        
        # Should handle gracefully
        assert "status" in result
        print(f"  [OK] Empty questions handled: {result['status']}")
        
        # Test with invalid training type (should be caught by database)
        result2 = await generate_synthetic_data(
            questions=["Test question"],
            topic="test",
            sub_topic="test",
            training_type="invalid_type",
            database_tools=db_tools
        )
        
        # Should handle gracefully
        assert "status" in result2
        print(f"  [OK] Invalid training type handled: {result2['status']}")
        
        return True
        
    except Exception as e:
        print(f"  [X] Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all orchestrator workflow tests."""
    print("\n" + "=" * 70)
    print("  Orchestrator Workflows Test Suite")
    print("=" * 70 + "\n")
    
    results = {}
    
    try:
        results["generate_synthetic_data"] = await test_generate_synthetic_data()
    except Exception as e:
        print(f"\n[ERROR] test_generate_synthetic_data failed: {str(e)}")
        results["generate_synthetic_data"] = False
    
    try:
        results["process_pending"] = await test_process_pending_questions()
    except Exception as e:
        print(f"\n[ERROR] test_process_pending_questions failed: {str(e)}")
        results["process_pending"] = False
    
    try:
        results["pipeline_status"] = await test_get_pipeline_status()
    except Exception as e:
        print(f"\n[ERROR] test_get_pipeline_status failed: {str(e)}")
        results["pipeline_status"] = False
    
    try:
        results["progress_tracking"] = await test_pipeline_progress()
    except Exception as e:
        print(f"\n[ERROR] test_pipeline_progress failed: {str(e)}")
        results["progress_tracking"] = False
    
    try:
        results["complete_pipeline"] = await test_complete_pipeline_integration()
    except Exception as e:
        print(f"\n[ERROR] test_complete_pipeline_integration failed: {str(e)}")
        results["complete_pipeline"] = False
    
    try:
        results["error_handling"] = await test_error_handling()
    except Exception as e:
        print(f"\n[ERROR] test_error_handling failed: {str(e)}")
        results["error_handling"] = False
    
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
        print("  [OK] ALL TESTS PASSED - Orchestrator workflows are working correctly!\n")
    else:
        print("  [X] SOME TESTS FAILED - Review output above\n")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_all_tests())
