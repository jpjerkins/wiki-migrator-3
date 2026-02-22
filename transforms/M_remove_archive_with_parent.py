"""
M_remove_archive_with_parent.py - Remove Archive PARA folder when note has a parent.

For notes that:
- Have para_folder = "Archive"
- Have at least one parent identified

Removes the Archive assignment, effectively making the note only exist under its parent.

Usage:
    python transforms/M_remove_archive_with_parent.py <input_folder>
    
Example:
    python transforms/M_remove_archive_with_parent.py 01457A9BFGHJKL
    # Creates output folder: 01457A9BFGHJKLM
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "M"
SCRIPT_NAME = "remove_archive_with_parent"


def remove_archive_with_parent(notes: list[Note]) -> list[Note]:
    """
    Remove Archive PARA folder from notes that have a parent.
    
    Args:
        notes: List of notes to process
        
    Returns:
        List of notes with Archive removed where appropriate
    """
    modified_count = 0
    
    for note in notes:
        # Check if note has Archive as PARA folder
        if note.metadata.get("para_folder") != "Archive":
            continue
        
        # Check if note has a parent
        parents = note.metadata.get("parents", [])
        if not parents:
            continue
        
        # Remove Archive assignment
        del note.metadata["para_folder"]
        modified_count += 1
    
    print(f"  Notes modified (Archive removed): {modified_count}")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with Archive stripped where parent exists
    """
    print("\nRemoving Archive PARA folder from notes with parents...")
    return remove_archive_with_parent(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGHJKL")
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
    print(f"  2. Inspect _notes.json to see updated PARA assignments")
    print(f"  3. Create the next transform script")


if __name__ == "__main__":
    main()
