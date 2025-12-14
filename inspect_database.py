"""
Database Inspector Script

Simple script to print all database table contents.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.database_tools import DatabaseTools
from utils.db_inspector import print_all_tables, print_table_summary

def main():
    """Main function to inspect database."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Inspect database table contents")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary only (counts, no full contents)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Limit number of records per table (default: 5)"
    )
    parser.add_argument(
        "--all-columns",
        action="store_true",
        help="Show all columns including empty ones and timestamps"
    )
    parser.add_argument(
        "--method",
        choices=["tool", "direct"],
        default="tool",
        help="Use DatabaseTools method or direct utility (default: tool)"
    )
    
    args = parser.parse_args()
    
    if args.summary:
        print_table_summary()
    elif args.method == "tool":
        # Use DatabaseTools method
        db = DatabaseTools()
        result = db.print_all_tables(
            limit_per_table=args.limit,
            show_all_columns=args.all_columns
        )
        print(f"\nReturned record counts: {result}")
    else:
        # Use direct utility function
        result = print_all_tables(
            limit_per_table=args.limit,
            show_all_columns=args.all_columns
        )
        print(f"\nReturned record counts: {result}")


if __name__ == "__main__":
    main()
