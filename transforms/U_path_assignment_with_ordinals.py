"""
U_assign_paths_with_ordinals.py - Assign paths with numbered PARA folders.

Like transform T but with fixes:
1. Correctly handles notes whose parent is a PARA folder (not a note)
2. Prepends ordinals to PARA folder names (1 Projects, 2 Areas, 3 Resources, 4 Archive)

Usage:
    python transforms/U_assign_paths_with_ordinals.py <input_folder>
    
Example:
    python transforms/U_assign_paths_with_ordinals.py 01457A9BFGHJKLM
    # Creates output folder: 01457A9BFGHJKLMU
"""

import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "U"
SCRIPT_NAME = "assign_paths_with_ordinals"

# PARA folder ordering with ordinals
PARA_ORDINALS = {
    "Projects": "1 Projects",
    "Areas": "2 Areas",
    "Resources": "3 Resources",
    "Archive": "4 Archive",
}

PARA_FOLDERS = {"Projects", "Areas", "Resources", "Archive"}


def sanitize_folder_name(name: str) -> str:
    """Sanitize a name for use as a folder name."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    name = name.rstrip('. ')
    if not name:
        name = "untitled"
    return name


def get_ordinal_path(path: str) -> str:
    """Replace PARA folder names with their ordinal versions."""
    if not path or path == ".":
        return path
    
    parts = path.split("/")
    # Replace first part if it's a PARA folder
    if parts[0] in PARA_ORDINALS:
        parts[0] = PARA_ORDINALS[parts[0]]
    
    return "/".join(parts)


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


def get_full_path_for_parent(note_title: str, parent_map: dict[str, str], para_map: dict[str, str], visited: set = None) -> str:
    """Recursively build full path for a parent note."""
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
    
    if parent_title in PARA_FOLDERS:
        return sanitize_folder_name(parent_title)
    
    parent_path = get_full_path_for_parent(parent_title, parent_map, para_map, visited.copy())
    
    if parent_path == ".":
        return sanitize_folder_name(parent_title)
    
    return f"{parent_path}/{sanitize_folder_name(parent_title)}"


def step1_assign_parent_paths(notes: list[Note]) -> tuple[list[Note], set[str]]:
    """Step 1: Assign paths to parent notes (those with children)."""
    parent_map = build_parent_tree(notes)
    para_map = {n.title: n.metadata.get("para_folder") for n in notes}
    
    # Find all notes that are parents
    all_parents = set()
    for note in notes:
        if note.title in parent_map.values():
            all_parents.add(note.title)
    
    print(f"  Found {len(all_parents)} notes that are parents")
    
    # Assign paths to parents
    for note in notes:
        if note.title in all_parents:
            full_path = get_full_path_for_parent(note.title, parent_map, para_map)
            note.metadata["output_path"] = full_path
    
    return notes, all_parents


def step2_apply_project_reorganization(notes: list[Note]) -> list[Note]:
    """Step 2: Move Parked projects to z_Parked, Done projects to Archive."""
    moved_parked = 0
    moved_done = 0
    
    for note in notes:
        if "Project" not in note.tags:
            continue
        
        current_path = note.metadata.get("output_path", "")
        
        # Only process if in Projects root
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
    Step 3: Assign paths to leaf notes based on their parent's path.
    
    FIX: Handle PARA folder parents correctly.
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
        
        parent_title = parents[0]["title"]
        
        # FIX: Check if parent is a PARA folder directly
        if parent_title in PARA_FOLDERS:
            # Parent is a PARA folder - use it directly
            note.metadata["output_path"] = sanitize_folder_name(parent_title)
            leaf_count += 1
            continue
        
        # Get parent's assigned path
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


def step4_apply_ordinals(notes: list[Note]) -> list[Note]:
    """Step 4: Replace PARA folder names with ordinal versions."""
    updated = 0
    
    for note in notes:
        path = note.metadata.get("output_path", ".")
        if path != ".":
            new_path = get_ordinal_path(path)
            if new_path != path:
                note.metadata["output_path"] = new_path
                updated += 1
    
    print(f"  Applied ordinals to {updated} notes")
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """Main transform function."""
    print("\nStep 1: Assigning paths to parent notes...")
    notes, all_parents = step1_assign_parent_paths(notes)
    
    print("\nStep 2: Reorganizing projects (Parked/Done)...")
    notes = step2_apply_project_reorganization(notes)
    
    print("\nStep 3: Assigning paths to leaf notes...")
    notes = step3_assign_leaf_paths(notes, all_parents)
    
    print("\nStep 4: Applying PARA folder ordinals...")
    notes = step4_apply_ordinals(notes)
    
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
    """Main entry point."""
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
        ("Daily Score in Archive", lambda n: "Daily Score" in n.title and "4 Archive" in n.metadata.get("output_path", "")),
        ("Active Projects", lambda n: n.metadata.get("output_path") == "1 Projects" and "Project" in n.tags and "Parked" not in n.tags and "Done" not in n.tags),
        ("z_Parked", lambda n: "z_Parked" in n.metadata.get("output_path", "")),
        ("Ordinal folders", lambda n: n.metadata.get("output_path", "").startswith(("1 ", "2 ", "3 ", "4 "))),
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


if __name__ == "__main__":
    main()
