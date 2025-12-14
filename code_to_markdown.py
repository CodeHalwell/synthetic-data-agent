"""Script to recursively save all Python files from src directory to a markdown file."""

import os
from pathlib import Path


def collect_python_files_to_markdown(src_dir: str = ".", output_file: str = "docs/codebase.md") -> None:
    """
    Recursively walk through src directory and save all Python file contents to a markdown file.
    
    Args:
        src_dir: The source directory to scan for Python files.
        output_file: The output markdown file name.
    """
    src_path = Path(src_dir)
    
    if not src_path.exists():
        print(f"Error: Directory '{src_dir}' does not exist.")
        return
    
    # Collect all Python files recursively, excluding .venv directory
    python_files = sorted(
        py_file for py_file in src_path.rglob("*.py")
        if ".venv" not in py_file.parts
    )
    
    if not python_files:
        print(f"No Python files found in '{src_dir}'.")
        return
    
    with open(output_file, "w", encoding="utf-8") as md_file:
        md_file.write("# Codebase\n\n")
        md_file.write(f"This file contains the contents of all Python files in the `{src_dir}` directory.\n\n")
        md_file.write("---\n\n")
        
        for py_file in python_files:
            # Get relative path from src directory for the heading
            relative_path = py_file.relative_to(src_path.parent)
            
            print(f"Processing: {relative_path}")
            
            # Write the heading with the file path
            md_file.write(f"## {relative_path}\n\n")
            
            # Read and write the file contents in a code block
            try:
                content = py_file.read_text(encoding="utf-8")
                md_file.write("```python\n")
                md_file.write(content)
                # Ensure there's a newline before closing the code block
                if not content.endswith("\n"):
                    md_file.write("\n")
                md_file.write("```\n\n")
            except Exception as e:
                md_file.write(f"*Error reading file: {e}*\n\n")
    
    print(f"\nSuccessfully saved {len(python_files)} Python files to '{output_file}'")


if __name__ == "__main__":
    collect_python_files_to_markdown()
