"""
0B_fix_done_leaves.py - Fix Done project leaves placement.

Fix for Transform U Step 2/3 bug:
- Transform U Step 2 only moves Done projects that already have output_path == "Projects"
- But leaf projects don't get their output_path until Step 3
- This transform runs AFTER U to correct the paths for Done projects

Usage:
    python transforms/0B_fix_done_leaves.py <input_folder>
    
Example:
    python transforms/0B_fix_done_leaves.py 01457A9BFGHJKZMU0A
    # Creates output folder: 01457A9BFGHJKZMU0A0B
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "0B"
SCRIPT_NAME = "fix_done_leaves"


def fix_done_leaves(notes: list[Note]) -> list[Note]:
    """
    Fix Done project leaves that were incorrectly left in Projects.
    
    Identifies notes that:
    - Have 'Done' and 'Project' tags
    - Have output_path containing 'Projects' (but not already in Archive)
    - Are leaf notes (not referenced as parents)
    
    Moves them to 'Archive'.
    """
    # Build set of all note titles referenced as parents
    referenced_parents = set()
    for note in notes:
        parents = note.metadata.get("parents", [])
        for parent in parents:
            referenced_parents.add(parent["title"])
    
    fixed_count = 0
    
    for note in notes:
        # Check if this is a Done project
        if "Done" not in note.tags or "Project" not in note.tags:
            continue
        
        # Check if it's a leaf note (not referenced as parent)
        if note.title in referenced_parents:
            continue
        
        # Check current path
        current_path = note.metadata.get("output_path", "")
        
        # If already in Archive, skip
        if "Archive" in current_path:
            continue
        
        # If in Projects, move to Archive (use ordinal prefix since U already ran)
        if "Projects" in current_path:
            note.metadata["output_path"] = "4 Archive"
            note.metadata["para_folder"] = "Archive"
            fixed_count += 1
    
    print(f"  Fixed {fixed_count} Done project leaves")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    """
    print("\nFixing Done project leaves placement...")
    print("  Moving Done project leaves from Projects to Archive")
    return fix_done_leaves(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGHJKZMU0A")
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
    
    print(f"\nFinal note count: {len(notes)}")
    
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
    print(f"  2. Run X transform to create final output")


if __name__ == "__main__":
    main()
