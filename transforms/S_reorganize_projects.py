"""
S_reorganize_projects.py - Reorganize projects based on status tags.

Changes folder assignments for projects:
1. Projects with 'Parked' tag in 'Projects' → 'Projects/z_Parked'
2. Projects with 'Done' tag in 'Projects' → 'Archive'

Usage:
    python transforms/S_reorganize_projects.py <input_folder>
    
Example:
    python transforms/S_reorganize_projects.py 01457A9BFGHJKLMP
    # Creates output folder: 01457A9BFGHJKLMPS
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "S"
SCRIPT_NAME = "reorganize_projects"


def reorganize_projects(notes: list[Note]) -> tuple[list[Note], dict]:
    """
    Reorganize projects based on Parked and Done tags.
    
    Args:
        notes: List of notes
        
    Returns:
        Tuple of (updated notes, statistics dict)
    """
    stats = {
        "parked_moved": 0,
        "done_moved": 0,
        "unchanged": 0,
    }
    
    for note in notes:
        # Only process projects
        if "Project" not in note.tags:
            stats["unchanged"] += 1
            continue
        
        # Check current assignment
        current_path = note.metadata.get("output_path", "")
        
        # Only process if currently in Projects (but not already in a subfolder)
        if not (current_path == "Projects" or current_path.startswith("Projects/") and "/" not in current_path.replace("Projects/", "")):
            stats["unchanged"] += 1
            continue
        
        # Case 1: Parked projects → Projects/z_Parked
        if "Parked" in note.tags:
            note.metadata["output_path"] = "Projects/z_Parked"
            note.metadata["para_folder"] = "Projects"  # Keep para_folder as Projects
            stats["parked_moved"] += 1
        
        # Case 2: Done projects → Archive
        elif "Done" in note.tags:
            note.metadata["output_path"] = "Archive"
            note.metadata["para_folder"] = "Archive"
            stats["done_moved"] += 1
        
        else:
            stats["unchanged"] += 1
    
    return notes, stats


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with reorganized project assignments
    """
    print("\nReorganizing projects based on status tags...")
    notes, stats = reorganize_projects(notes)
    
    print(f"  Projects moved to z_Parked: {stats['parked_moved']}")
    print(f"  Projects moved to Archive: {stats['done_moved']}")
    print(f"  Projects unchanged: {stats['unchanged']}")
    
    return notes


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGHJKLMP")
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
    
    # Count projects before
    projects_before = len([n for n in notes if "Project" in n.tags])
    parked_before = len([n for n in notes if "Project" in n.tags and "Parked" in n.tags])
    done_before = len([n for n in notes if "Project" in n.tags and "Done" in n.tags])
    print(f"\nBefore reorganization:")
    print(f"  Total projects: {projects_before}")
    print(f"  Parked projects: {parked_before}")
    print(f"  Done projects: {done_before}")
    
    notes = transform(notes)
    
    # Show sample moved projects
    print("\nSample moved projects:")
    parked_sample = [n for n in notes if "Project" in n.tags and "Parked" in n.tags and n.metadata.get("output_path") == "Projects/z_Parked"][:3]
    done_sample = [n for n in notes if "Project" in n.tags and "Done" in n.tags and n.metadata.get("output_path") == "Archive"][:3]
    
    if parked_sample:
        print("  Parked -> Projects/z_Parked:")
        for note in parked_sample:
            print(f"    - {note.title}")
    
    if done_sample:
        print("  Done -> Archive:")
        for note in done_sample:
            print(f"    - {note.title}")
    
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
    print(f"  2. Run transform R to create the final folder structure")


if __name__ == "__main__":
    main()
