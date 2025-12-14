"""
Test workflow functions directly to verify they work.
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator.workflows import generate_synthetic_data
from tools.database_tools import DatabaseTools
from schema.synthetic_data import SyntheticDataSFT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

async def test():
    print("\n" + "="*70)
    print("  Testing Workflow Functions Directly")
    print("="*70 + "\n")
    
    # Test direct workflow call
    print("[Test] Calling generate_synthetic_data() directly...")
    result = await generate_synthetic_data(
        questions=["What is a covalent bond?"],
        topic="chemistry",
        sub_topic="basic concepts",
        training_type="sft",
        max_questions=1
    )
    
    print(f"  Status: {result['status']}")
    print(f"  Approved: {result['summary']['approved']}")
    
    # Verify in database
    if result['summary']['approved'] > 0:
        print("\n[Verify] Checking database...")
        engine = create_engine('sqlite:///db/synthetic_data.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        records = session.query(SyntheticDataSFT).filter(
            SyntheticDataSFT.topic == 'chemistry'
        ).order_by(SyntheticDataSFT.id.desc()).limit(1).all()
        
        if records:
            print(f"  [OK] Found {len(records)} record(s) in database")
            print(f"    ID: {records[0].id}")
            print(f"    Instruction: {records[0].instruction[:60]}...")
        else:
            print(f"  [X] No records found despite approval")
    
    return result['status'] in ['success', 'partial']

if __name__ == "__main__":
    success = asyncio.run(test())
    print(f"\n{'='*70}")
    if success:
        print("  [OK] Workflow functions work correctly!")
    else:
        print("  [X] Workflow functions have issues")
    print("="*70 + "\n")
