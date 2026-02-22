"""
I_resolve_multi_parents.py - Interactively resolve multi-parent notes.

This is an INTERACTIVE transform that:
1. Generates a markdown file with checkboxes for all multi-parent notes
2. Waits for user to select ONE parent per note
3. Applies selections and validates
4. Loops until all notes have exactly one parent

Usage:
    python transforms/I_resolve_multi_parents.py <input_folder>
    
Example:
    python transforms/I_resolve_multi_parents.py 01457A9BFGH
    # Creates output folder: 01457A9BFGHI
"""

import re
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "I"
SCRIPT_NAME = "resolve_multi_parents"

RESOLUTION_FILE = "resolve_multi_parents.md"


def get_multi_parent_notes(notes: list[Note]) -> list[Note]:
    """Get all notes with more than one parent."""
    return [n for n in notes if len(n.metadata.get("parents", [])) > 1]


def generate_resolution_file(notes: list[Note]) -> int:
    """
    Generate the markdown file with checkboxes for multi-parent notes.
    
    Returns the number of multi-parent notes.
    """
    multi_notes = get_multi_parent_notes(notes)
    
    lines = [
        "# Resolve Multi-Parent Notes",
        "",
        f"**{len(multi_notes)} notes have multiple parents.**",
        "",
        "For each note below, select **EXACTLY ONE** parent by checking its checkbox.",
        "All unselected parents will be removed.",
        "",
        "---",
        "",
    ]
    
    for note in multi_notes:
        lines.append(f"## {note.title}")
        lines.append("")
        lines.append("Select ONE parent:")
        lines.append("")
        
        for parent in note.metadata.get("parents", []):
            lines.append(f"- [ ] {parent['title']}")
        
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "## Instructions",
        "",
        "1. Check exactly ONE checkbox per note above",
        "2. Save this file",
        "3. Return to the terminal and press ENTER",
        "",
        "If you don't select exactly one parent for a note, you'll be asked to fix it.",
    ])
    
    # Write to current directory (project root)
    output_path = Path(RESOLUTION_FILE)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    
    return len(multi_notes)


def parse_resolution_file(notes: list[Note]) -> dict[str, str]:
    """
    Parse the resolution file and return selected parents.
    
    Returns dict mapping note title -> selected parent title
    """
    resolution_path = Path(RESOLUTION_FILE)
    if not resolution_path.exists():
        return {}
    
    content = resolution_path.read_text(encoding="utf-8")
    
    selections = {}
    current_note = None
    
    for line in content.split("\n"):
        # Check for note header
        note_match = re.match(r"^## (.+)$", line)
        if note_match:
            current_note = note_match.group(1)
            selections[current_note] = []
            continue
        
        # Check for checked parent
        if current_note and line.startswith("- [x] ") or line.startswith("- [X] "):
            parent_title = line[6:].strip()
            if current_note in selections:
                selections[current_note].append(parent_title)
    
    # Convert to single selection per note (or empty if multiple/none selected)
    result = {}
    for note_title, parents in selections.items():
        if len(parents) == 1:
            result[note_title] = parents[0]
        else:
            result[note_title] = None  # Invalid selection
    
    return result


def apply_selections(notes: list[Note], selections: dict[str, str]) -> tuple[list[Note], list[str]]:
    """
    Apply parent selections to notes.
    
    Returns (updated_notes, list of notes with invalid selections)
    """
    invalid_notes = []
    
    for note in notes:
        if note.title not in selections:
            continue
        
        selected_parent = selections[note.title]
        
        if selected_parent is None:
            invalid_notes.append(note.title)
            continue
        
        # Find and keep only the selected parent
        parents = note.metadata.get("parents", [])
        new_parents = [p for p in parents if p["title"] == selected_parent]
        
        if len(new_parents) == 1:
            note.metadata["parents"] = new_parents
        else:
            invalid_notes.append(note.title)
    
    return notes, invalid_notes


def transform(notes: list[Note]) -> list[Note]:
    """
    Interactive transform to resolve multi-parent notes.
    """
    multi_count = len(get_multi_parent_notes(notes))
    
    if multi_count == 0:
        print("  No multi-parent notes found. Nothing to resolve.")
        return notes
    
    # Generate resolution file
    print(f"\nGenerating resolution file: {RESOLUTION_FILE}")
    generate_resolution_file(notes)
    print(f"  {multi_count} notes with multiple parents listed")
    
    # Wait for user
    input(f"\nPlease edit {RESOLUTION_FILE} and select ONE parent per note.\nPress ENTER when ready...")
    
    # Loop until all valid
    while True:
        selections = parse_resolution_file(notes)
        notes, invalid = apply_selections(notes, selections)
        
        if not invalid:
            print(f"  All {multi_count} multi-parent notes resolved!")
            break
        
        print(f"\n  WARNING: {len(invalid)} note(s) need fixing:")
        for title in invalid:
            print(f"    - {title}")
        print(f"\n  Please ensure exactly ONE parent is selected for each note in {RESOLUTION_FILE}")
        input("  Press ENTER when ready...")
    
    return notes


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGH")
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
    
    # Clean up resolution file
    resolution_path = Path(RESOLUTION_FILE)
    if resolution_path.exists():
        resolution_path.unlink()
        print(f"  Cleaned up {RESOLUTION_FILE}")
    
    print(f"\nDone! Created output folder: {output_folder_name}")
    print(f"\nNext steps:")
    print(f"  1. Review the output in: {output_folder}")
    print(f"  2. Create the next transform script")


if __name__ == "__main__":
    main()
