"""
Validation utilities for transform scripts.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Note


def validate_notes(notes: list["Note"]) -> list[str]:
    """
    Validate a list of notes and return any errors found.
    
    Args:
        notes: List of Note objects to validate
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors = []
    seen_ids = set()
    seen_paths = set()
    
    for i, note in enumerate(notes):
        prefix = f"Note[{i}]"
        
        # Required fields
        if not note.id:
            errors.append(f"{prefix}: Missing id")
        elif note.id in seen_ids:
            errors.append(f"{prefix}: Duplicate id '{note.id}'")
        else:
            seen_ids.add(note.id)
        
        if not note.title:
            errors.append(f"{prefix} ({note.id}): Missing title")
        
        if not note.path:
            errors.append(f"{prefix} ({note.id}): Missing path")
        elif note.path in seen_paths:
            errors.append(f"{prefix} ({note.id}): Duplicate path '{note.path}'")
        else:
            seen_paths.add(note.path)
        
        # Validate tasks
        for j, task in enumerate(note.tasks):
            if not task.id:
                errors.append(f"{prefix} ({note.id}): Task[{j}] missing id")
            if not task.content:
                errors.append(f"{prefix} ({note.id}): Task[{j}] missing content")
    
    return errors


def assert_valid(notes: list["Note"]) -> None:
    """
    Assert that notes are valid, raising an error if not.
    
    Args:
        notes: List of Note objects to validate
        
    Raises:
        ValueError: If any validation errors are found
    """
    errors = validate_notes(notes)
    if errors:
        raise ValueError(f"Validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
