"""
N_assign_output_paths.py - Determine final folder structure and assign output paths.

For each note, determines where it should be placed in the final output:
1. If note has a parent: place in folder named after the parent
2. If note has no parent but has PARA folder: place in PARA folder root
3. If note has neither: place in root

Assigns the path to note.metadata['output_path'] for later use.
Does NOT create folders or write files yet.

Usage:
    python transforms/N_assign_output_paths.py <input_folder>
    
Example:
    python transforms/N_assign_output_paths.py 01457A9BFGHJKLM
    # Creates output folder: 01457A9BFGHJKLMN
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "N"
SCRIPT_NAME = "assign_output_paths"


def sanitize_folder_name(name: str) -> str:
    """
    Sanitize a name for use as a folder name.
    Removes/replaces characters problematic in file systems.
    """
    # Characters not allowed in Windows folder names
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Remove trailing spaces and periods
    name = name.rstrip('. ')
    
    # Ensure not empty
    if not name:
        name = "untitled"
    
    return name


def assign_output_paths(notes: list[Note]) -> list[Note]:
    """
    Determine output folder path for each note.
    
    Priority:
    1. Parent folder (if parent exists)
    2. PARA folder (if no parent but PARA assigned)
    3. Root (if neither)
    
    Args:
        notes: List of notes
        
    Returns:
        List of notes with output_path assigned
    """
    # Count statistics
    stats = {
        "by_parent": 0,
        "by_para": 0,
        "to_root": 0,
    }
    
    for note in notes:
        parents = note.metadata.get("parents", [])
        para_folder = note.metadata.get("para_folder")
        
        # Priority 1: Has a parent -> place in parent folder
        if parents:
            parent_title = parents[0]["title"]
            folder_name = sanitize_folder_name(parent_title)
            note.metadata["output_path"] = folder_name
            stats["by_parent"] += 1
        
        # Priority 2: No parent but has PARA folder
        elif para_folder:
            folder_name = sanitize_folder_name(para_folder)
            note.metadata["output_path"] = folder_name
            stats["by_para"] += 1
        
        # Priority 3: Neither -> root
        else:
            note.metadata["output_path"] = "."
            stats["to_root"] += 1
    
    print(f"  Assigned by parent: {stats['by_parent']}")
    print(f"  Assigned by PARA folder: {stats['by_para']}")
    print(f"  Assigned to root: {stats['to_root']}")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with output_path assigned
    """
    print("\nAssigning output paths to notes...")
    return assign_output_paths(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGHJKLM")
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
    
    # Show sample assignments
    print("\nSample output path assignments:")
    for note in notes[:5]:
        path = note.metadata.get("output_path", "NOT ASSIGNED")
        parent_info = note.metadata.get("parents", [{}])[0].get("title", "none") if note.metadata.get("parents") else "none"
        para_info = note.metadata.get("para_folder", "none")
        print(f"  - {note.title}")
        print(f"    -> output_path: {path}")
        print(f"    (parent: {parent_info}, para: {para_info})")
    
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
    print(f"  2. Inspect _notes.json to see output_path assignments")
    print(f"  3. Create the next transform script to actually create the folder structure")


if __name__ == "__main__":
    main()
