"""
Example: Print Database Contents

This script demonstrates how to print the contents of database tables.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.database_tools import DatabaseTools
from utils.db_inspector import print_all_tables, print_table_contents, print_table_summary

# Option 1: Using DatabaseTools method
print("\n" + "="*70)
print("  Option 1: Using DatabaseTools.print_all_tables()")
print("="*70)
db = DatabaseTools()
db.print_all_tables(limit_per_table=2)

# Option 2: Using db_inspector directly
print("\n" + "="*70)
print("  Option 2: Using db_inspector.print_table_summary()")
print("="*70)
print_table_summary()

# Option 3: Print specific table
print("\n" + "="*70)
print("  Option 3: Print specific table (questions)")
print("="*70)
from schema.synthetic_data import Questions
print_table_contents("questions", Questions, limit=3)

print("\n" + "="*70)
print("  Done!")
print("="*70 + "\n")
