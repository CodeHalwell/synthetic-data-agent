"""Script to print a directory tree, excluding specified directories."""

from pathlib import Path


def print_tree(
    directory: str = ".",
    prefix: str = "",
    exclude_dirs: set[str] = None
) -> None:
    """
    Print a directory tree structure.
    
    Args:
        directory: The root directory to start from.
        prefix: The prefix for the current level (used for recursion).
        exclude_dirs: Set of directory names to exclude.
    """
    if exclude_dirs is None:
        exclude_dirs = {".venv", "__pycache__", ".git", ".adk"}
    
    path = Path(directory)
    
    if not path.exists():
        print(f"Error: Directory '{directory}' does not exist.")
        return
    
    # Get all items, filter out excluded directories
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    items = [item for item in items if item.name not in exclude_dirs]
    
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "+-- " if is_last else "|-- "
        
        print(f"{prefix}{connector}{item.name}")
        
        if item.is_dir():
            extension = "    " if is_last else "|   "
            print_tree(item, prefix + extension, exclude_dirs)


if __name__ == "__main__":
    print(".")
    print_tree()
