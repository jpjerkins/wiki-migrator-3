"""
2_identify_parents.py - Identify parent-child relationships from tags.

Analyzes all notes and their tags to identify parent relationships.
If note B has note A's title in its tags, then A is a parent of B.

This handles the case where multiple notes can be parents of a single note.

Usage:
    python transforms/2_identify_parents.py <input_folder>
    
Example:
    python transforms/2_identify_parents.py 01
    # Creates output folder: 012
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "2"
SCRIPT_NAME = "identify_parents"


def build_title_index(notes: list[Note]) -> dict[str, Note]:
    """
    Build a lookup index of notes by their title.
    
    Returns:
        Dictionary mapping title -> Note
    """
    return {note.title: note for note in notes}


def identify_parents(notes: list[Note]) -> list[Note]:
    """
    Identify parent relationships for all notes based on tags.
    
    If note B has note A's title in its tags, then A is a parent of B.
    
    Args:
        notes: List of notes to analyze
        
    Returns:
        List of notes with parent information added to metadata
    """
    # Build title index for quick lookup
    title_index = build_title_index(notes)
    
    # Track statistics
    stats = {
        "notes_with_parents": 0,
        "total_parent_relationships": 0,
        "notes_with_multiple_parents": 0,
        "max_parents": 0,
    }
    
    for note in notes:
        parents = []
        
        # Check each tag to see if it matches another note's title
        for tag in note.tags:
            if tag in title_index:
                # This tag is the title of another note -> that note is a parent
                parent_note = title_index[tag]
                parents.append({
                    "id": parent_note.id,
                    "title": parent_note.title,
                })
        
        # Store parents in metadata
        if parents:
            note.metadata["parents"] = parents
            stats["notes_with_parents"] += 1
            stats["total_parent_relationships"] += len(parents)
            
            if len(parents) > 1:
                stats["notes_with_multiple_parents"] += 1
            
            stats["max_parents"] = max(stats["max_parents"], len(parents))
    
    # Print statistics
    print(f"  Notes with parents: {stats['notes_with_parents']}")
    print(f"  Total parent relationships: {stats['total_parent_relationships']}")
    print(f"  Notes with multiple parents: {stats['notes_with_multiple_parents']}")
    print(f"  Max parents for a single note: {stats['max_parents']}")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with parent relationships identified
    """
    print("\nAnalyzing parent-child relationships...")
    return identify_parents(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01")
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
    print(f"  2. Inspect _notes.json to see parent relationships")
    print(f"  3. Create the next transform script (3_*.py)")


if __name__ == "__main__":
    main()
