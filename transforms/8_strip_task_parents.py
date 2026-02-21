"""
8_strip_task_parents.py - Strip needless parent entries from tasks (UPDATED).

Removes system/systematic parents from tasks to simplify their hierarchy:
- Parked
- Today
- TodayCandidate
- Archive
- Task
- WhileOut (NEW)

Usage:
    python transforms/8_strip_task_parents.py <input_folder>
    
Example:
    python transforms/8_strip_task_parents.py 01457
    # Creates output folder: 014578
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "8"
SCRIPT_NAME = "strip_task_parents"

# Parents to strip from tasks (UPDATED: added WhileOut)
PARENTS_TO_STRIP = {"Parked", "Today", "TodayCandidate", "Archive", "Task", "WhileOut"}


def strip_task_parents(notes: list[Note]) -> list[Note]:
    """
    Remove needless parent entries from all tasks.
    
    Args:
        notes: List of notes to process
        
    Returns:
        List of notes with cleaned parent lists
    """
    tasks_modified = 0
    parents_removed = 0
    
    for note in notes:
        # Only process notes with Task tag
        if "Task" not in note.tags:
            continue
        
        # Get current parents
        parents = note.metadata.get("parents", [])
        if not parents:
            continue
        
        # Filter out needless parents
        original_count = len(parents)
        cleaned_parents = [
            p for p in parents 
            if p.get("title") not in PARENTS_TO_STRIP
        ]
        
        removed = original_count - len(cleaned_parents)
        if removed > 0:
            note.metadata["parents"] = cleaned_parents
            tasks_modified += 1
            parents_removed += removed
    
    print(f"  Tasks modified: {tasks_modified}")
    print(f"  Parent entries removed: {parents_removed}")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with needless parents stripped from tasks
    """
    print("\nStripping needless parents from tasks...")
    print(f"  (Including: {', '.join(sorted(PARENTS_TO_STRIP))})")
    return strip_task_parents(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457")
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
    print(f"  2. Inspect _notes.json to see cleaned parent lists")
    print(f"  3. Create the next transform script")


if __name__ == "__main__":
    main()
