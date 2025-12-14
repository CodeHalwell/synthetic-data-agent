"""
Review script to check the test run results.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.database_tools import DatabaseTools
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema.synthetic_data import SyntheticDataSFT

# Check database
db = DatabaseTools()
engine = create_engine('sqlite:///db/synthetic_data.db')
Session = sessionmaker(bind=engine)
session = Session()

# Query for Chemistry Expert Reasoning records
sft_records = session.query(SyntheticDataSFT).filter(
    SyntheticDataSFT.topic == 'Chemistry'
).filter(
    SyntheticDataSFT.sub_topic == 'Expert Reasoning'
).all()

print(f"\n{'='*70}")
print(f"  Test Run Review: Chemistry Expert Reasoning SFT Dataset")
print(f"{'='*70}\n")

print(f"Found {len(sft_records)} records in database\n")

if len(sft_records) == 0:
    print("  [X] NO RECORDS FOUND - Data was not stored!")
    print("\n  This suggests the database agent may not have actually stored the data.")
    print("  The workflow may have completed but the storage step failed.")
else:
    print(f"  [OK] {len(sft_records)} records found\n")
    
    # Check first few records
    for i, record in enumerate(sft_records[:3], 1):
        print(f"  Record {i}:")
        print(f"    ID: {record.id}")
        print(f"    Instruction: {record.instruction[:80]}...")
        print(f"    Response length: {len(record.response)} chars")
        print(f"    Has <think> tag: {'<think>' in record.response}")
        print(f"    Topic: {record.topic}")
        print(f"    Sub-topic: {record.sub_topic}")
        print(f"    Difficulty: {record.difficulty}")
        print(f"    Quality score: {record.quality_score}")
        print(f"    Review status: {record.review_status}")
        print()
    
    # Verify format compliance
    all_have_think_tags = all('<think>' in r.response for r in sft_records)
    all_have_final_answer = all('Final Answer' in r.response or '</think>' in r.response for r in sft_records)
    
    print(f"  Format Compliance:")
    print(f"    All have <think> tags: {all_have_think_tags}")
    print(f"    All have final answers: {all_have_final_answer}")
    
    # Check topic distribution
    topics = {}
    for record in sft_records:
        # Try to identify sub-topics from instruction
        if 'retrosynthesis' in record.instruction.lower() or 'strychnine' in record.instruction.lower():
            topics['Organic Synthesis'] = topics.get('Organic Synthesis', 0) + 1
        elif 'diels-alder' in record.instruction.lower() or 'fmo' in record.instruction.lower():
            topics['Organic Theory'] = topics.get('Organic Theory', 0) + 1
        elif 'heck' in record.instruction.lower() or 'catalytic' in record.instruction.lower():
            topics['Organometallics'] = topics.get('Organometallics', 0) + 1
        elif 'partition' in record.instruction.lower() or 'thermodynamics' in record.instruction.lower():
            topics['Physical Chemistry'] = topics.get('Physical Chemistry', 0) + 1
        elif 'molecular orbital' in record.instruction.lower() or 'o2' in record.instruction.lower():
            topics['MO Theory'] = topics.get('MO Theory', 0) + 1
        elif 'nmr' in record.instruction.lower() or 'structure' in record.instruction.lower():
            topics['Analytical'] = topics.get('Analytical', 0) + 1
        elif 'hplc' in record.instruction.lower() or 'validation' in record.instruction.lower():
            topics['Analytical'] = topics.get('Analytical', 0) + 1
        elif 'crystal field' in record.instruction.lower() or 'co(' in record.instruction.lower():
            topics['Inorganic'] = topics.get('Inorganic', 0) + 1
        elif 'semiconductor' in record.instruction.lower() or 'band gap' in record.instruction.lower():
            topics['Materials'] = topics.get('Materials', 0) + 1
        elif 'michaelis' in record.instruction.lower() or 'enzymatic' in record.instruction.lower():
            topics['Biochemistry'] = topics.get('Biochemistry', 0) + 1
    
    print(f"\n  Topic Distribution:")
    for topic, count in topics.items():
        print(f"    {topic}: {count}")

session.close()
