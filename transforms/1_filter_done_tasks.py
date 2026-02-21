"""
1_filter_done_tasks.py - Filter out completed tasks.

Removes notes that have both 'Task' and 'Done' tags, as these represent
tasks that have been completed and don't need to be migrated.

Usage:
    python transforms/1_filter_done_tasks.py <input_folder>
    
Example:
    python transforms/1_filter_done_tasks.py 0
    # Creates output folder: 01
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "1"
SCRIPT_NAME = "filter_done_tasks"


def transform(notes: list[Note]) -> list[Note]:
    """
    Filter out notes with both 'Task' and 'Done' tags.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Filtered list of notes (completed tasks removed)
    """
    filtered = []
    removed_count = 0
    
    for note in notes:
        # Check if note has both 'Task' and 'Done' tags
        has_task_tag = "Task" in note.tags
        has_done_tag = "Done" in note.tags
        
        if has_task_tag and has_done_tag:
            # Skip this note - it's a completed task
            removed_count += 1
            continue
        
        filtered.append(note)
    
    print(f"  Removed {removed_count} completed task(s)")
    print(f"  Kept {len(filtered)} note(s)")
    
    return filtered


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 0")
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
    
    print("\nFiltering out completed tasks...")
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
    print(f"  2. Compare with previous: {input_folder}")
    print(f"  3. Create the next transform script (2_*.py)")


if __name__ == "__main__":
    main()
