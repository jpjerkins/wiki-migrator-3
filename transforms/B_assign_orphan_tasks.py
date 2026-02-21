"""
B_assign_orphan_tasks.py - Assign orphan tasks to a new "Orphan Tasks" note.

Creates a new note called "Orphan Tasks" with Organization as its parent.
Adds "Orphan Tasks" as the parent for all tasks that have no parents.

Usage:
    python transforms/B_assign_orphan_tasks.py <input_folder>
    
Example:
    python transforms/B_assign_orphan_tasks.py 01457A9
    # Creates output folder: 01457A9B
"""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, Task, Attachment, load_json, save_output, validate_notes

SCRIPT_ID = "B"
SCRIPT_NAME = "assign_orphan_tasks"


def create_orphan_tasks_note() -> Note:
    """
    Create the "Orphan Tasks" note that will parent all orphan tasks.
    
    Returns:
        The new Orphan Tasks note
    """
    now = datetime.now()
    
    return Note(
        id="orphan-tasks",
        title="Orphan Tasks",
        content="# Orphan Tasks\n\nThis note contains all tasks that were not assigned to any parent during migration.",
        path="Orphan Tasks.md",
        created=now,
        modified=now,
        tags=["Task"],
        tasks=[],
        attachments=[],
        metadata={
            "parents": [{"id": "Organization", "title": "Organization", "type": "note"}],
            "para_folder": "Archive",
        },
    )


def assign_orphans(notes: list[Note]) -> list[Note]:
    """
    Assign "Orphan Tasks" as parent to all tasks with no parents.
    
    Args:
        notes: List of notes to process
        
    Returns:
        List of notes with orphan tasks assigned
    """
    orphan_tasks_note = create_orphan_tasks_note()
    orphan_parent_ref = {
        "id": orphan_tasks_note.id,
        "title": orphan_tasks_note.title,
        "type": "orphan_collector",
    }
    
    orphans_assigned = 0
    
    for note in notes:
        # Only process notes with Task tag
        if "Task" not in note.tags:
            continue
        
        # Check if task has no parents
        parents = note.metadata.get("parents", [])
        if not parents:
            note.metadata["parents"] = [orphan_parent_ref]
            orphans_assigned += 1
    
    # Add the orphan tasks note to the list
    notes.append(orphan_tasks_note)
    
    print(f"  Orphan tasks assigned: {orphans_assigned}")
    print(f"  Created 'Orphan Tasks' note with Organization as parent")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with orphan tasks assigned to "Orphan Tasks"
    """
    print("\nAssigning orphan tasks to 'Orphan Tasks' note...")
    return assign_orphans(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9")
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
    print(f"  2. Check 'Orphan Tasks.md' for the new note")
    print(f"  3. Create the next transform script")


if __name__ == "__main__":
    main()
