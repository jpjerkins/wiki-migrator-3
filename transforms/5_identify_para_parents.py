"""
5_identify_para_parents.py - Identify parents including PARA folders.

Analyzes all notes and their tags to identify parent relationships.
Additionally, adds the assigned PARA folder as a parent for each note.

This combines the parent identification from script 2 with PARA folder awareness.

Usage:
    python transforms/5_identify_para_parents.py <input_folder>
    
Example:
    python transforms/5_identify_para_parents.py 014
    # Creates output folder: 0145
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "5"
SCRIPT_NAME = "identify_para_parents"

# PARA folder titles (virtual parents)
PARA_FOLDERS = ["Projects", "Areas", "Resources", "Archive"]


def build_title_index(notes: list[Note]) -> dict[str, Note]:
    """
    Build a lookup index of notes by their title.
    
    Returns:
        Dictionary mapping title -> Note
    """
    return {note.title: note for note in notes}


def identify_parents_with_para(notes: list[Note]) -> list[Note]:
    """
    Identify parent relationships for all notes, including PARA folders.
    
    If note B has note A's title in its tags, then A is a parent of B.
    Additionally, each note's assigned PARA folder is added as a parent.
    
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
        "notes_with_para_parent": 0,
    }
    
    for note in notes:
        parents = []
        parent_ids = set()  # Track to avoid duplicates
        
        # First, add the PARA folder as a parent (if assigned)
        para_folder = note.metadata.get("para_folder")
        if para_folder:
            parents.append({
                "id": para_folder,
                "title": para_folder,
                "type": "para_folder",
            })
            parent_ids.add(para_folder)
            stats["notes_with_para_parent"] += 1
        
        # Then check tags for other note parents
        for tag in note.tags:
            if tag in title_index:
                parent_note = title_index[tag]
                # Avoid duplicates (e.g., if PARA folder happens to match a note title)
                if parent_note.title not in parent_ids:
                    parents.append({
                        "id": parent_note.id,
                        "title": parent_note.title,
                        "type": "note",
                    })
                    parent_ids.add(parent_note.title)
        
        # Store parents in metadata
        if parents:
            note.metadata["parents"] = parents
            stats["notes_with_parents"] += 1
            stats["total_parent_relationships"] += len(parents)
            
            if len(parents) > 1:
                stats["notes_with_multiple_parents"] += 1
            
            stats["max_parents"] = max(stats["max_parents"], len(parents))
    
    # Print statistics
    print(f"  Notes with PARA folder parent: {stats['notes_with_para_parent']}")
    print(f"  Notes with additional note parents: {stats['notes_with_parents'] - stats['notes_with_para_parent']}")
    print(f"  Total notes with parents: {stats['notes_with_parents']}")
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
        Notes with parent relationships identified (including PARA folders)
    """
    print("\nAnalyzing parent-child relationships (including PARA folders)...")
    return identify_parents_with_para(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 014")
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
    print(f"  2. Inspect _notes.json to see parent relationships with PARA folders")
    print(f"  3. Create the next transform script (6_*.py)")


if __name__ == "__main__":
    main()
