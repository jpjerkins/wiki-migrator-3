"""
3B_assign_para_folder.py - Assign notes to PARA folders based on tags (FIXED).

Identifies which PARA folder each note belongs to:
- Projects: notes tagged with "Project"
- Areas: notes tagged with "Area"  
- Resources: notes tagged with "ResourceTopic" (FIXED: was "Resource")
- Archive: notes without any PARA tag (orphans)

Note: The tag names are singular or specific but folder names are plural.

Usage:
    python transforms/3B_assign_para_folder.py <input_folder>
    
Example:
    python transforms/3B_assign_para_folder.py 01
    # Creates output folder: 013B
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "4"
SCRIPT_NAME = "assign_para_folder"

# PARA tag to folder mapping
# FIXED: Resources now uses "ResourceTopic" tag instead of "Resource"
PARA_TAGS = {
    "Project": "Projects",
    "Area": "Areas", 
    "ResourceTopic": "Resources",
}
FALLBACK_FOLDER = "Archive"


def assign_para_folder(note: Note) -> str:
    """
    Determine which PARA folder a note belongs to.
    
    Priority: Project > Area > ResourceTopic > Archive (fallback)
    
    Args:
        note: The note to analyze
        
    Returns:
        PARA folder name (Projects, Areas, Resources, or Archive)
    """
    # Check for PARA tags in priority order
    for tag, folder in PARA_TAGS.items():
        if tag in note.tags:
            return folder
    
    # No PARA tag found - assign to Archive
    return FALLBACK_FOLDER


def transform(notes: list[Note]) -> list[Note]:
    """
    Assign PARA folders to all notes.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with para_folder added to metadata
    """
    # Track statistics
    stats = {folder: 0 for folder in list(PARA_TAGS.values()) + [FALLBACK_FOLDER]}
    
    for note in notes:
        folder = assign_para_folder(note)
        note.metadata["para_folder"] = folder
        stats[folder] += 1
    
    # Print statistics
    print("\nPARA folder assignments:")
    for folder, count in stats.items():
        print(f"  {folder}: {count} notes")
    
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
    print(f"  2. Inspect _notes.json to see para_folder assignments")
    print(f"  3. Re-run script 2 on this output to identify parents within PARA context")


if __name__ == "__main__":
    main()
