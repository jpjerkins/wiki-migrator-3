"""
Template for creating new transform scripts.

Copy this file and rename it with the next available ID.
Example: 1_clean_names.py, 2_inline_tasks.py, A_normalize_tags.py
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

# Configuration - update these for your transform
SCRIPT_ID = "X"  # Replace with next available ID (0-9, A-Z)
SCRIPT_NAME = "template"  # Brief description of what this transform does


def transform(notes: list[Note]) -> list[Note]:
    """
    Apply transformation to the list of notes.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Transformed list of notes
    """
    # TODO: Implement your transformation logic here
    for note in notes:
        # Example: Add a tag to all notes
        # note.tags.append("migrated")
        pass
    
    return notes


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
    
    print("Applying transformation...")
    notes = transform(notes)
    
    # Validate before saving
    errors = validate_notes(notes)
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    print(f"Saving to: {output_folder}")
    save_output(output_folder, notes)
    
    print(f"Done! Created output folder: {output_folder_name}")


if __name__ == "__main__":
    main()
