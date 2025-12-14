# Database Inspection Guide

## Overview

The system includes comprehensive database inspection utilities to view all table contents. This is useful for:
- Verifying data was stored correctly
- Debugging pipeline issues
- Reviewing generated synthetic data
- Understanding database state

## Quick Start

### Method 1: Using DatabaseTools (Recommended)

```python
from tools.database_tools import DatabaseTools

db = DatabaseTools()

# Print all tables with default settings (5 records per table)
result = db.print_all_tables()

# Print with custom limit
result = db.print_all_tables(limit_per_table=10)

# Show all columns including empty ones
result = db.print_all_tables(show_all_columns=True)
```

### Method 2: Using Direct Utility

```python
from utils.db_inspector import print_all_tables, print_table_summary

# Print summary (counts only, no full contents)
print_table_summary()

# Print all tables
result = print_all_tables(limit_per_table=5)
```

### Method 3: Using Command Line Script

```bash
# Show summary only
uv run python inspect_database.py --summary

# Show all tables (5 records each)
uv run python inspect_database.py

# Show more records
uv run python inspect_database.py --limit 10

# Show all columns including timestamps
uv run python inspect_database.py --all-columns
```

## Available Functions

### `DatabaseTools.print_all_tables()`

**Parameters:**
- `limit_per_table` (Optional[int]): Limit number of records per table (default: None = all)
- `show_all_columns` (bool): Show all columns including empty ones and timestamps (default: False)

**Returns:**
- Dictionary mapping table names to record counts

**Example:**
```python
db = DatabaseTools()
result = db.print_all_tables(limit_per_table=3)
# Returns: {'questions': 10, 'synthetic_data_sft': 5, ...}
```

### `print_all_tables()` (Direct Utility)

Same as above, but called directly from `utils.db_inspector`.

### `print_table_summary()`

Prints a summary of all tables showing only counts and column information (no full contents).

**Example:**
```python
from utils.db_inspector import print_table_summary

summary = print_table_summary()
# Prints counts and column info for all tables
```

### `print_table_contents()`

Print contents of a specific table.

**Parameters:**
- `table_name` (str): Name of the table
- `table_class`: SQLAlchemy model class
- `limit` (Optional[int]): Limit number of records
- `show_all_columns` (bool): Show all columns

**Example:**
```python
from utils.db_inspector import print_table_contents, ALL_TABLES

print_table_contents(
    "synthetic_data_sft",
    ALL_TABLES["synthetic_data_sft"],
    limit=5
)
```

## Output Format

The inspector prints:
- Table name and record count
- Each record with ID
- All non-empty columns (unless `show_all_columns=True`)
- Formatted values (JSON, dates, truncated long text)
- Summary with total records per table

**Example Output:**
```
======================================================================
  Table: synthetic_data_sft
  Records: 5
======================================================================

  Record 1 (ID: 1):
  ----------------------------------------------------------------------
    id                                  : 1
    instruction                         : What is photosynthesis?
    response                            : Photosynthesis is the process...
    topic                               : biology
    sub_topic                           : plant biology
    quality_score                       : 0.95
    review_status                       : approved
```

## Tables Inspected

The inspector shows all 10 tables:

1. **questions** - Questions waiting to be processed
2. **synthetic_data_sft** - Supervised Fine-Tuning data
3. **synthetic_data_dpo** - Direct Preference Optimization data
4. **synthetic_data_ppo** - Proximal Policy Optimization data
5. **synthetic_data_grpo** - Group Relative Policy Optimization data
6. **synthetic_data_rlhf** - Reinforcement Learning from Human Feedback data
7. **synthetic_data_kto** - Kahneman-Tversky Optimization data
8. **synthetic_data_orpo** - Odds Ratio Preference Optimization data
9. **synthetic_data_chat** - Multi-turn conversation data
10. **synthetic_data_qa** - Question-Answer pairs

## Use Cases

### Verify Data Storage
```python
# After generating data, verify it was stored
db = DatabaseTools()
result = db.print_all_tables(limit_per_table=1)

if result['synthetic_data_sft'] > 0:
    print("SFT data stored successfully!")
```

### Debug Pipeline Issues
```python
# Check questions at each pipeline stage
from utils.db_inspector import print_table_contents, ALL_TABLES

# Check pending questions
print_table_contents("questions", ALL_TABLES["questions"])
```

### Review Generated Data
```python
# Review recently generated data
db = DatabaseTools()
db.print_all_tables(limit_per_table=10, show_all_columns=False)
```

## Tips

1. **Use `--summary` for quick overview** - Faster when you just need counts
2. **Use `limit_per_table` for large databases** - Prevents overwhelming output
3. **Use `show_all_columns=True` for debugging** - Shows all fields including timestamps
4. **Check specific tables** - Use `print_table_contents()` for focused inspection

## Notes

- Long text fields are truncated to 150 characters by default
- JSON fields are formatted with indentation
- Timestamps are shown in ISO format
- Empty tables show "[Empty] No records found"
- Errors are caught and displayed with traceback
