"""
9_dedupe_parent_substrings.py - Dedupe parents using substring matching.

For tasks where a parent name is a substring of the task title,
keeps only that matching parent and strips all others.

This handles cases like:
  Task: "Arlo: Charge side cam battery 2025-12-14"
  Parents: "Arlo: Charge side cam battery", "Home"
  Result: Keep only "Arlo: Charge side cam battery"

Usage:
    python transforms/9_dedupe_parent_substrings.py <input_folder>
    
Example:
    python transforms/9_dedupe_parent_substrings.py 014578
    # Creates output folder: 0145789
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "9"
SCRIPT_NAME = "dedupe_parent_substrings"


def find_substring_parent(task_title: str, parents: list[dict]) -> dict | None:
    """
    Find a parent whose title is a substring of the task title.
    
    Args:
        task_title: The title of the task
        parents: List of parent dictionaries
        
    Returns:
        The matching parent dict, or None if no match
    """
    for parent in parents:
        parent_title = parent.get("title", "")
        if parent_title and parent_title in task_title and parent_title != task_title:
            return parent
    return None


def dedupe_parents(notes: list[Note]) -> list[Note]:
    """
    For tasks with substring-matching parents, keep only the matching one.
    
    Args:
        notes: List of notes to process
        
    Returns:
        List of notes with deduplicated parents
    """
    tasks_modified = 0
    parents_removed = 0
    
    for note in notes:
        # Only process notes with Task tag
        if "Task" not in note.tags:
            continue
        
        # Get current parents
        parents = note.metadata.get("parents", [])
        if len(parents) <= 1:
            continue
        
        # Find parent that is a substring of task title
        matching_parent = find_substring_parent(note.title, parents)
        
        if matching_parent:
            # Keep only the matching parent
            original_count = len(parents)
            note.metadata["parents"] = [matching_parent]
            tasks_modified += 1
            parents_removed += original_count - 1
    
    print(f"  Tasks modified: {tasks_modified}")
    print(f"  Parent entries removed: {parents_removed}")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with substring-matching parents deduplicated
    """
    print("\nDeduping parents using substring matching...")
    return dedupe_parents(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 014578")
        sys.exit(1)
    
    input_folder_name = sys.argv[1]
    input_folder = Path("output") / input_folder_name
    
    if not input_folder.exists():
        print(f"Error: Input folder not found: {input_folder}")
        sys.exit(1)
    
    # Determine output folder name
    output_folder_name = f"{input_folder_name}{SCRIPT_ID}"
    output_folder = Path("output") / output_folder_name
    
    print(f"Loading notes from: {input_folder}")
    notes = load_json(input_folder)
    print(f"Loaded {len(notes)} notes")
    
    notes = transform(notes)
    
    # Validate before saving
    errors = validate_notes(notes)
    if errors:
        print("\nValidation errors:")
        for error in errors[:5]:
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != "y":
            sys.exit(1)
    
    print(f"\nSaving to: {output_folder}")
    save_output(output_folder, notes)
    
    print(f"\nDone! Created output folder: {output_folder_name}")
    print(f"\nNext steps:")
    print(f"  1. Review the output in: {output_folder}")
    print(f"  2. Inspect _notes.json to see deduplicated parent lists")
    print(f"  3. Create the next transform script")


if __name__ == "__main__":
    main()
