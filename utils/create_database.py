"""
Database Initialization Script

Creates and initializes the synthetic data database with all required tables.

Run this script once before using the system:
    python create_database.py

This will:
1. Create the database directory if it doesn't exist
2. Create all tables defined in schema/synthetic_data.py
3. Display a summary of created tables
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect

from utils.db import create_db_engine, get_database_url


def create_database():
    """Create all tables in the database."""
    print("\n" + "=" * 60)
    print("  Synthetic Data Generation - Database Initialization")
    print("=" * 60 + "\n")

    print(f"[Database] Location: {get_database_url()}\n")

    print("[Creating] Tables...")
    engine = create_db_engine()

    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("\n[Success] Database created successfully!")
    print(f"\n[Tables] Created ({len(tables)} total):\n")

    # Group tables by type
    training_tables = [t for t in tables if t.startswith("synthetic_data_")]
    other_tables = [t for t in tables if not t.startswith("synthetic_data_")]

    if training_tables:
        print("   Training Type Tables:")
        for table in sorted(training_tables):
            training_type = table.replace("synthetic_data_", "").upper()
            print(f"   - {table:<30} ({training_type})")

    if other_tables:
        print("\n   Pipeline Tables:")
        for table in sorted(other_tables):
            print(f"   - {table}")

    print("\n" + "=" * 60)
    print("  Database is ready to use!")
    print("=" * 60 + "\n")

    return engine


if __name__ == "__main__":
    create_database()
