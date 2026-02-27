"""
P_assign_full_paths.py - Determine full hierarchical output paths for all notes.

Builds the complete folder path by traversing up through all parent relationships.
Example: If "Spec Kit Insights" has parent "Learn AI", and "Learn AI" has parent "Resources",
         the full path becomes "Resources/Learn AI"

Usage:
    python transforms/P_assign_full_paths.py <input_folder>
    
Example:
    python transforms/P_assign_full_paths.py 01457A9BFGHJKLM
    # Creates output folder: 01457A9BFGHJKLMP
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "P"
SCRIPT_NAME = "assign_full_paths"


def sanitize_folder_name(name: str) -> str:
    """Sanitize a name for use as a folder name."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    name = name.rstrip('. ')
    if not name:
        name = "untitled"
    return name


def build_parent_tree(notes: list[Note]) -> dict[str, str]:
    """
    Build a lookup of note title -> its parent title.
    
    Returns dict mapping note title -> parent title (or None if no parent)
    """
    parent_map = {}
    
    for note in notes:
        parents = note.metadata.get("parents", [])
        if parents:
            # Use first parent
            parent_map[note.title] = parents[0]["title"]
        else:
            parent_map[note.title] = None
    
    return parent_map


def get_full_path(note_title: str, parent_map: dict[str, str], para_map: dict[str, str], visited: set = None) -> str:
    """
    Recursively build the full path for a note by traversing up through parents.
    
    Args:
        note_title: The title of the note
        parent_map: Dict mapping note title -> parent title
        para_map: Dict mapping note title -> PARA folder
        visited: Set of visited titles (to prevent infinite loops)
        
    Returns:
        Full path like "Resources/Learn AI" or "Projects/ArchWork"
    """
    if visited is None:
        visited = set()
    
    # Prevent infinite loops
    if note_title in visited:
        return sanitize_folder_name(note_title)
    visited.add(note_title)
    
    # Get this note's parent
    parent_title = parent_map.get(note_title)
    
    if parent_title is None:
        # No parent - use PARA folder if available, or root
        para_folder = para_map.get(note_title)
        if para_folder:
            return sanitize_folder_name(para_folder)
        return "."
    
    # Check if parent is a top-level PARA folder
    if parent_title in ("Projects", "Areas", "Resources", "Archive"):
        return sanitize_folder_name(parent_title)
    
    # Recursively get parent's path
    parent_path = get_full_path(parent_title, parent_map, para_map, visited.copy())
    
    if parent_path == ".":
        # Parent is at root
        return sanitize_folder_name(parent_title)
    
    # Combine parent path with this note's parent
    return f"{parent_path}/{sanitize_folder_name(parent_title)}"


def assign_full_paths(notes: list[Note]) -> list[Note]:
    """
    Determine and assign full hierarchical paths for all notes.
    
    Args:
        notes: List of notes
        
    Returns:
        List of notes with full output_path assigned
    """
    # Build lookup maps
    parent_map = build_parent_tree(notes)
    para_map = {n.title: n.metadata.get("para_folder") for n in notes}
    
    # Track depth statistics
    depth_counts = {}
    
    for note in notes:
        full_path = get_full_path(note.title, parent_map, para_map)
        note.metadata["output_path"] = full_path
        
        # Track depth
        depth = full_path.count("/") + 1 if full_path != "." else 0
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    
    print("  Path depth distribution:")
    for depth in sorted(depth_counts.keys()):
        level_name = ["Root", "Top-level folder", "2 levels deep", "3 levels deep", "4+ levels deep"][min(depth, 4)]
        print(f"    {level_name}: {depth_counts[depth]} notes")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """Main transform function."""
    print("\nAssigning full hierarchical paths to notes...")
    return assign_full_paths(notes)


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
    print("\nSample full path assignments:")
    samples = [n for n in notes if "/" in n.metadata.get("output_path", "")][:5]
    for note in samples:
        print(f"  - {note.title}")
        print(f"    -> {note.metadata['output_path']}")
    
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
    print(f"  2. Run transform O to create the final folder structure")


if __name__ == "__main__":
    main()
