"""
T_assign_all_paths.py - Assign full paths to all notes in correct order.

Does the following in order:
1. Assign paths to parent notes (folders) using transform P rules
2. Apply transform S rules (Parked -> Projects/z_Parked, Done -> Archive)
3. Assign leaf notes to paths based on their parent's assigned path

Usage:
    python transforms/T_assign_all_paths.py <input_folder>
    
Example:
    python transforms/T_assign_all_paths.py 01457A9BFGHJKLM
    # Creates output folder: 01457A9BFGHJKLMT
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "T"
SCRIPT_NAME = "assign_all_paths"


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
    """Build lookup of note title -> parent title."""
    parent_map = {}
    for note in notes:
        parents = note.metadata.get("parents", [])
        if parents:
            parent_map[note.title] = parents[0]["title"]
        else:
            parent_map[note.title] = None
    return parent_map


def get_full_path(note_title: str, parent_map: dict[str, str], para_map: dict[str, str], visited: set = None) -> str:
    """Recursively build full path by traversing up through parents."""
    if visited is None:
        visited = set()
    
    if note_title in visited:
        return sanitize_folder_name(note_title)
    visited.add(note_title)
    
    parent_title = parent_map.get(note_title)
    
    if parent_title is None:
        para_folder = para_map.get(note_title)
        if para_folder:
            return sanitize_folder_name(para_folder)
        return "."
    
    if parent_title in ("Projects", "Areas", "Resources", "Archive"):
        return sanitize_folder_name(parent_title)
    
    parent_path = get_full_path(parent_title, parent_map, para_map, visited.copy())
    
    if parent_path == ".":
        return sanitize_folder_name(parent_title)
    
    return f"{parent_path}/{sanitize_folder_name(parent_title)}"


def step1_assign_parent_paths(notes: list[Note]) -> list[Note]:
    """
    Step 1: Assign paths to notes that are parents (have children).
    Uses transform P logic.
    """
    # Build maps
    parent_map = build_parent_tree(notes)
    para_map = {n.title: n.metadata.get("para_folder") for n in notes}
    
    # Find all notes that are parents (have children)
    all_parents = set()
    for note in notes:
        if note.title in parent_map.values():
            all_parents.add(note.title)
    
    print(f"  Found {len(all_parents)} notes that are parents")
    
    # Assign paths to parents
    for note in notes:
        if note.title in all_parents:
            full_path = get_full_path(note.title, parent_map, para_map)
            note.metadata["output_path"] = full_path
    
    return notes, all_parents


def step2_apply_project_reorganization(notes: list[Note]) -> list[Note]:
    """
    Step 2: Apply transform S rules.
    Parked projects in Projects -> Projects/z_Parked
    Done projects in Projects -> Archive
    """
    moved_parked = 0
    moved_done = 0
    
    for note in notes:
        if "Project" not in note.tags:
            continue
        
        current_path = note.metadata.get("output_path", "")
        
        # Only process if in Projects (root level)
        if current_path != "Projects":
            continue
        
        if "Parked" in note.tags:
            note.metadata["output_path"] = "Projects/z_Parked"
            note.metadata["para_folder"] = "Projects"
            moved_parked += 1
        elif "Done" in note.tags:
            note.metadata["output_path"] = "Archive"
            note.metadata["para_folder"] = "Archive"
            moved_done += 1
    
    print(f"  Moved {moved_parked} parked projects to Projects/z_Parked")
    print(f"  Moved {moved_done} done projects to Archive")
    
    return notes


def step3_assign_leaf_paths(notes: list[Note], all_parents: set) -> list[Note]:
    """
    Step 3: Assign paths to leaf notes based on their parent's assigned path.
    """
    leaf_count = 0
    
    for note in notes:
        # Skip if already has path (is a parent)
        if note.title in all_parents:
            continue
        
        parents = note.metadata.get("parents", [])
        if not parents:
            # No parent - use PARA folder or root
            para = note.metadata.get("para_folder")
            if para:
                note.metadata["output_path"] = sanitize_folder_name(para)
            else:
                note.metadata["output_path"] = "."
            leaf_count += 1
            continue
        
        # Get parent's assigned path
        parent_title = parents[0]["title"]
        parent_note = next((n for n in notes if n.title == parent_title), None)
        
        if parent_note and parent_note.metadata.get("output_path"):
            parent_path = parent_note.metadata["output_path"]
            # Leaf goes inside parent's folder
            note.metadata["output_path"] = f"{parent_path}/{sanitize_folder_name(parent_title)}"
        else:
            # Parent not found or no path - use PARA
            para = note.metadata.get("para_folder")
            if para:
                note.metadata["output_path"] = sanitize_folder_name(para)
            else:
                note.metadata["output_path"] = "."
        
        leaf_count += 1
    
    print(f"  Assigned paths to {leaf_count} leaf notes")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """Main transform function."""
    print("\nStep 1: Assigning paths to parent notes...")
    notes, all_parents = step1_assign_parent_paths(notes)
    
    print("\nStep 2: Reorganizing projects (Parked/Done)...")
    notes = step2_apply_project_reorganization(notes)
    
    print("\nStep 3: Assigning paths to leaf notes...")
    notes = step3_assign_leaf_paths(notes, all_parents)
    
    # Show statistics
    print("\nPath depth distribution:")
    depth_counts = {}
    for note in notes:
        path = note.metadata.get("output_path", ".")
        depth = path.count("/") + 1 if path != "." else 0
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    
    for depth in sorted(depth_counts.keys()):
        level_name = ["Root", "Top-level", "2 levels", "3 levels", "4+ levels"][min(depth, 4)]
        print(f"    {level_name}: {depth_counts[depth]} notes")
    
    return notes


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
    
    output_folder_name = f"{input_folder_name}{SCRIPT_ID}"
    output_folder = Path("output") / output_folder_name
    
    print(f"Loading notes from: {input_folder}")
    notes = load_json(input_folder)
    print(f"Loaded {len(notes)} notes")
    
    notes = transform(notes)
    
    # Show samples
    print("\nSample path assignments:")
    samples = [
        ("Projects", lambda n: n.metadata.get("output_path") == "Projects" and "Project" in n.tags),
        ("Projects/z_Parked", lambda n: n.metadata.get("output_path") == "Projects/z_Parked"),
        ("Archive (Done projects)", lambda n: n.metadata.get("output_path") == "Archive" and "Done" in n.tags),
        ("Deep path", lambda n: "/" in n.metadata.get("output_path", "") and n.metadata.get("output_path", "").count("/") >= 2),
    ]
    
    for label, predicate in samples:
        matches = [n for n in notes if predicate(n)]
        if matches:
            print(f"\n  {label}:")
            for note in matches[:2]:
                print(f"    - {note.title}")
                print(f"      -> {note.metadata['output_path']}")
    
    # Validate
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
