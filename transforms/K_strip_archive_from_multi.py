"""
J_strip_archive_from_multi.py - Remove Archive parent from multi-parent notes.

For any note with multiple parents, removes "Archive" from the parents list.
This simplifies the hierarchy by keeping only the meaningful parent(s).

Usage:
    python transforms/J_strip_archive_from_multi.py <input_folder>
    
Example:
    python transforms/J_strip_archive_from_multi.py 01457A9BFGH
    # Creates output folder: 01457A9BFGHJ
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "J"
SCRIPT_NAME = "strip_archive_from_multi"


def strip_archive_from_multi(notes: list[Note]) -> list[Note]:
    """
    Remove Archive parent from notes that have multiple parents.
    
    Args:
        notes: List of notes to process
        
    Returns:
        List of notes with Archive removed from multi-parent notes
    """
    modified_count = 0
    archive_removed_count = 0
    
    for note in notes:
        parents = note.metadata.get("parents", [])
        
        # Only process notes with multiple parents
        if len(parents) <= 1:
            continue
        
        # Check if Archive is in the parents
        has_archive = any(p.get("title") == "Archive" for p in parents)
        
        if has_archive:
            # Remove Archive from parents
            new_parents = [p for p in parents if p.get("title") != "Archive"]
            note.metadata["parents"] = new_parents
            modified_count += 1
            archive_removed_count += 1
    
    print(f"  Notes modified: {modified_count}")
    print(f"  Archive parents removed: {archive_removed_count}")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with Archive stripped from multi-parent notes
    """
    print("\nStripping Archive parent from multi-parent notes...")
    return strip_archive_from_multi(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGH")
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
    print(f"  2. Inspect _notes.json to see updated parent lists")
    print(f"  3. Create the next transform script")


if __name__ == "__main__":
    main()
