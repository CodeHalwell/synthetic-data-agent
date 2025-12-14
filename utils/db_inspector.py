"""
Database Inspector Utility

Provides functions to print and inspect database table contents.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from schema.synthetic_data import (
    Base,
    QUESTIONS_TABLE,
    SyntheticDataSFT,
    SyntheticDataDPO,
    SyntheticDataPPO,
    SyntheticDataGRPO,
    SyntheticDataRLHF,
    SyntheticDataKTO,
    SyntheticDataORPO,
    SyntheticDataChat,
    SyntheticDataQA,
)

# Database connection
db_dir = Path(__file__).parent.parent / "db"
db_dir.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{(db_dir / 'synthetic_data.db').as_posix()}"

# All table classes
ALL_TABLES = {
    "questions": QUESTIONS_TABLE,
    "synthetic_data_sft": SyntheticDataSFT,
    "synthetic_data_dpo": SyntheticDataDPO,
    "synthetic_data_ppo": SyntheticDataPPO,
    "synthetic_data_grpo": SyntheticDataGRPO,
    "synthetic_data_rlhf": SyntheticDataRLHF,
    "synthetic_data_kto": SyntheticDataKTO,
    "synthetic_data_orpo": SyntheticDataORPO,
    "synthetic_data_chat": SyntheticDataChat,
    "synthetic_data_qa": SyntheticDataQA,
}


def format_value(value: Any, max_length: int = 100) -> str:
    """Format a value for display, truncating long text."""
    if value is None:
        return "None"
    
    if isinstance(value, (dict, list)):
        # Format JSON as compact string
        json_str = json.dumps(value, indent=2)
        if len(json_str) > max_length:
            return json_str[:max_length] + "..."
        return json_str
    
    if isinstance(value, datetime):
        return value.isoformat()
    
    value_str = str(value)
    if len(value_str) > max_length:
        return value_str[:max_length] + "..."
    
    return value_str


def print_table_contents(
    table_name: str,
    table_class,
    limit: Optional[int] = None,
    show_all_columns: bool = False
) -> int:
    """
    Print contents of a database table.
    
    Args:
        table_name: Name of the table
        table_class: SQLAlchemy model class
        limit: Optional limit on number of records to show
        show_all_columns: If True, show all columns even if empty
        
    Returns:
        Number of records found
    """
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Query all records
        query = session.query(table_class)
        if limit:
            query = query.limit(limit)
        
        records = query.all()
        count = len(records)
        
        if count == 0:
            print(f"  [Empty] No records found")
            return 0
        
        # Get column names
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        # Filter out timestamp columns if not showing all
        if not show_all_columns:
            columns = [c for c in columns if c not in ['created_at', 'updated_at']]
        
        print(f"\n  {'='*70}")
        print(f"  Table: {table_name}")
        print(f"  Records: {count}" + (f" (showing {limit})" if limit else ""))
        print(f"  {'='*70}")
        
        for i, record in enumerate(records, 1):
            print(f"\n  Record {i} (ID: {getattr(record, 'id', 'N/A')}):")
            print(f"  {'-'*70}")
            
            for col in columns:
                value = getattr(record, col, None)
                
                # Skip None values unless show_all_columns
                if value is None and not show_all_columns:
                    continue
                
                # Format the value
                formatted = format_value(value, max_length=150)
                
                # Truncate column name if too long
                col_display = col[:30] + "..." if len(col) > 30 else col
                
                print(f"    {col_display:35} : {formatted}")
        
        print(f"\n  {'='*70}\n")
        
        return count
        
    except Exception as e:
        print(f"  [ERROR] Failed to read table {table_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        session.close()
        engine.dispose()


def print_all_tables(
    limit_per_table: Optional[int] = None,
    show_all_columns: bool = False,
    table_filter: Optional[List[str]] = None
) -> Dict[str, int]:
    """
    Print contents of all database tables.
    
    Args:
        limit_per_table: Optional limit on records per table
        show_all_columns: If True, show all columns including empty ones
        table_filter: Optional list of table names to include (None = all)
        
    Returns:
        Dictionary mapping table names to record counts
    """
    print("\n" + "="*70)
    print("  DATABASE CONTENTS - ALL TABLES")
    print("="*70)
    
    results = {}
    
    # Filter tables if specified
    tables_to_print = ALL_TABLES
    if table_filter:
        tables_to_print = {k: v for k, v in ALL_TABLES.items() if k in table_filter}
    
    for table_name, table_class in tables_to_print.items():
        count = print_table_contents(
            table_name,
            table_class,
            limit=limit_per_table,
            show_all_columns=show_all_columns
        )
        results[table_name] = count
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    total_records = sum(results.values())
    print(f"  Total records across all tables: {total_records}")
    print("\n  Records per table:")
    for table_name, count in results.items():
        status = "[OK]" if count > 0 else "[Empty]"
        print(f"    {status} {table_name:30} : {count:4} records")
    print("="*70 + "\n")
    
    return results


def print_table_summary() -> Dict[str, Dict[str, Any]]:
    """
    Print a summary of all tables (counts only, no full contents).
    
    Returns:
        Dictionary with table summaries
    """
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    summaries = {}
    
    print("\n" + "="*70)
    print("  DATABASE SUMMARY")
    print("="*70 + "\n")
    
    for table_name, table_class in ALL_TABLES.items():
        try:
            count = session.query(table_class).count()
            
            # Get sample record to show structure
            sample = session.query(table_class).first()
            columns = []
            if sample:
                inspector = inspect(engine)
                columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            summaries[table_name] = {
                "count": count,
                "columns": columns,
                "column_count": len(columns)
            }
            
            status = "[OK]" if count > 0 else "[Empty]"
            print(f"  {status} {table_name:30} : {count:4} records, {len(columns):2} columns")
            
        except Exception as e:
            print(f"  [ERROR] {table_name:30} : Error - {str(e)}")
            summaries[table_name] = {"error": str(e)}
    
    session.close()
    engine.dispose()
    
    print("="*70 + "\n")
    
    return summaries


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Print database table contents")
    parser.add_argument(
        "--table",
        type=str,
        help="Specific table to print (default: all tables)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of records per table"
    )
    parser.add_argument(
        "--all-columns",
        action="store_true",
        help="Show all columns including empty ones"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary only (counts, no full contents)"
    )
    
    args = parser.parse_args()
    
    if args.summary:
        print_table_summary()
    elif args.table:
        if args.table in ALL_TABLES:
            print_table_contents(
                args.table,
                ALL_TABLES[args.table],
                limit=args.limit,
                show_all_columns=args.all_columns
            )
        else:
            print(f"Error: Table '{args.table}' not found.")
            print(f"Available tables: {', '.join(ALL_TABLES.keys())}")
    else:
        print_all_tables(
            limit_per_table=args.limit,
            show_all_columns=args.all_columns
        )
