"""
File validation utilities for the Partcl CLI.
"""

from pathlib import Path
from typing import Union


def validate_file(filepath: Union[str, Path], expected_extension: str) -> None:
    """
    Validate that a file exists and has the expected extension.

    Args:
        filepath: Path to the file to validate
        expected_extension: Expected file extension (e.g., ".v", ".lib", ".sdc")

    Raises:
        ValueError: If the file doesn't exist or has wrong extension
    """
    path = Path(filepath)

    # Check if file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Check if it's a file (not directory)
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    # Check extension
    if not path.suffix.lower() == expected_extension.lower():
        raise ValueError(
            f"Invalid file extension for {path.name}. "
            f"Expected {expected_extension}, got {path.suffix}"
        )

    # Check if file is readable
    if not path.stat().st_size > 0:
        raise ValueError(f"File is empty: {path}")


def get_file_info(filepath: Union[str, Path]) -> dict:
    """
    Get information about a file.

    Args:
        filepath: Path to the file

    Returns:
        Dictionary with file information (name, size, lines)
    """
    path = Path(filepath)

    if not path.exists():
        return {"name": str(path), "exists": False}

    size = path.stat().st_size

    # Try to count lines
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = sum(1 for _ in f)
    except:
        lines = None

    return {
        "name": path.name,
        "path": str(path.absolute()),
        "exists": True,
        "size": size,
        "size_human": format_size(size),
        "lines": lines,
    }


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"