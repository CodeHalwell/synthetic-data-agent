"""
Main entry point for Synthetic Data Generation Agent.

This script demonstrates how to use the orchestrator workflows to generate
synthetic training data for LLM post-training.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator.workflows import generate_synthetic_data, get_pipeline_status
from tools.database_tools import DatabaseTools


async def main():
    """Main function demonstrating the synthetic data generation pipeline."""
    print("\n" + "=" * 70)
    print("  Synthetic Data Generation Agent - Demo")
    print("=" * 70 + "\n")
    
    # Example: Generate synthetic data for chemistry questions
    questions = [
        "What is a covalent bond?",
        "What is an ionic bond?",
        "How do chemical reactions work?"
    ]
    
    print("Generating synthetic training data for chemistry questions...")
    print(f"  Topic: chemistry")
    print(f"  Sub-topic: chemical bonding")
    print(f"  Training type: SFT (Supervised Fine-Tuning)")
    print(f"  Questions: {len(questions)}")
    print()
    
    # Run the complete pipeline
    result = await generate_synthetic_data(
        questions=questions,
        topic="chemistry",
        sub_topic="chemical bonding",
        training_type="sft",
        max_questions=3
    )
    
    # Display results
    print("\n" + "=" * 70)
    print("  Pipeline Results")
    print("=" * 70)
    print(f"  Status: {result['status']}")
    print(f"  Total questions: {result['summary']['total_questions']}")
    print(f"  Researched: {result['summary']['researched']}")
    print(f"  Generated: {result['summary']['generated']}")
    print(f"  Reviewed: {result['summary']['reviewed']}")
    print(f"  Approved: {result['summary']['approved']}")
    print(f"  Success rate: {result['summary']['success_rate']:.1f}%")
    
    if result['summary']['approved'] > 0:
        print(f"\n  [OK] Successfully generated {result['summary']['approved']} approved training examples!")
        print(f"\n  Individual Results:")
        for res in result['results']:
            if res.get('status') == 'success':
                print(f"    Question {res['question_id']}:")
                print(f"      Generated ID: {res.get('generated_id')}")
                print(f"      Quality score: {res.get('quality_score', 0):.2f}")
                print(f"      Review status: {res.get('review_status')}")
    else:
        print(f"\n  [!] No data was approved. Check errors for details.")
        if result.get('errors'):
            print(f"  Errors: {len(result['errors'])}")
    
    # Check pipeline status
    print("\n" + "=" * 70)
    print("  Pipeline Status")
    print("=" * 70)
    status = await get_pipeline_status(
        topic="chemistry",
        sub_topic="chemical bonding"
    )
    print(f"  Pending: {status['stages']['pending']}")
    print(f"  Ready for generation: {status['stages']['ready_for_generation']}")
    print(f"  Approved: {status['stages'].get('approved', 0)}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
