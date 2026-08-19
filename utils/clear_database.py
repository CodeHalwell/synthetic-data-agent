"""
Clear all data from database tables.

This script deletes all records from all tables in the database.
Use with caution!
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import sessionmaker

from schema.synthetic_data import QUESTIONS_TABLE, SCHEMA_REGISTRY
from utils.db import create_db_engine

# All table classes (questions plus one table per training type)
ALL_TABLES = {
    "questions": QUESTIONS_TABLE,
    **{cls.__tablename__: cls for cls in SCHEMA_REGISTRY.values()},
}


def clear_all_tables(confirm: bool = False) -> dict[str, int]:
    """
    Clear all data from all database tables.

    Args:
        confirm: If True, proceed with deletion. If False, only show what would be deleted.

    Returns:
        Dictionary mapping table names to number of records deleted
    """
    engine = create_db_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    results = {}

    print("\n" + "=" * 70)
    if confirm:
        print("  CLEARING ALL DATABASE TABLES")
    else:
        print("  DRY RUN: Would clear the following tables")
    print("=" * 70 + "\n")

    try:
        for table_name, table_class in ALL_TABLES.items():
            # Count records before deletion
            count = session.query(table_class).count()
            results[table_name] = count

            if confirm:
                if count > 0:
                    # Delete all records
                    session.query(table_class).delete()
                    print(f"  [OK] {table_name:30} : Deleted {count:4} records")
                else:
                    print(f"  [Empty] {table_name:30} : No records to delete")
            else:
                if count > 0:
                    print(f"  [Would delete] {table_name:30} : {count:4} records")
                else:
                    print(f"  [Empty] {table_name:30} : 0 records")

        if confirm:
            session.commit()
            print("\n" + "=" * 70)
            print("  All tables cleared successfully!")
            print("=" * 70 + "\n")
        else:
            print("\n" + "=" * 70)
            print("  DRY RUN COMPLETE - No data was deleted")
            print("  Run with --confirm to actually delete the data")
            print("=" * 70 + "\n")

        return results

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Failed to clear tables: {e!s}")
        import traceback

        traceback.print_exc()
        return results
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Clear all data from database tables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (show what would be deleted)
  python clear_database.py

  # Actually delete all data
  python clear_database.py --confirm
        """,
    )
    parser.add_argument(
        "--confirm", action="store_true", help="Actually delete the data (required for deletion)"
    )

    args = parser.parse_args()

    if not args.confirm:
        print("\n[WARNING] This is a DRY RUN. No data will be deleted.")
        print("Add --confirm flag to actually delete all data.\n")

    results = clear_all_tables(confirm=args.confirm)

    total = sum(results.values())
    if args.confirm:
        print(f"Total records deleted: {total}")
    else:
        print(f"Total records that would be deleted: {total}")
