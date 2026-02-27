"""
0A_fix_parked_leaves.py - Fix Parked project leaves placement.

Fix for Transform U Step 3 bug:
- Transform U Step 3 overwrites output_path for leaf notes
- Parked project leaves get assigned to "Projects" instead of "Projects/z_Parked"
- This transform runs AFTER U to correct the paths

Usage:
    python transforms/0A_fix_parked_leaves.py <input_folder>
    
Example:
    python transforms/0A_fix_parked_leaves.py 01457A9BFGHJKZMU
    # Creates output folder: 01457A9BFGHJKZMU0A
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "0A"
SCRIPT_NAME = "fix_parked_leaves"


def fix_parked_leaves(notes: list[Note]) -> list[Note]:
    """
    Fix Parked project leaves that were incorrectly placed in Projects root.
    
    Identifies notes that:
    - Have 'Parked' and 'Project' tags
    - Have output_path containing 'Projects' but not 'z_Parked'
    - Are leaf notes (not referenced as parents)
    
    Moves them to 'Projects/z_Parked'.
    """
    # Build set of all note titles referenced as parents
    referenced_parents = set()
    for note in notes:
        parents = note.metadata.get("parents", [])
        for parent in parents:
            referenced_parents.add(parent["title"])
    
    fixed_count = 0
    
    for note in notes:
        # Check if this is a Parked project
        if "Parked" not in note.tags or "Project" not in note.tags:
            continue
        
        # Check if it's a leaf note (not referenced as parent)
        if note.title in referenced_parents:
            continue
        
        # Check current path
        current_path = note.metadata.get("output_path", "")
        
        # If already in z_Parked, skip
        if "z_Parked" in current_path:
            continue
        
        # If in Projects (but not z_Parked), move to z_Parked
        if "Projects" in current_path:
            # Replace "Projects" with "Projects/z_Parked" in the path
            new_path = current_path.replace("Projects", "Projects/z_Parked", 1)
            note.metadata["output_path"] = new_path
            fixed_count += 1
    
    print(f"  Fixed {fixed_count} Parked project leaves")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    """
    print("\nFixing Parked project leaves placement...")
    print("  Moving Parked project leaves from Projects to Projects/z_Parked")
    return fix_parked_leaves(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGHJKZMU")
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
