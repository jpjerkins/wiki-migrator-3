"""
I2_resolve_multi_parents.py - Interactive multi-parent resolver (ITERATIVE).

Workflow:
1. If resolution file doesn't exist:
   - Generate it with all multi-parent notes
   - Tell user to select ONE parent per note
   - EXIT

2. If resolution file exists:
   - Parse selections
   - If ALL notes have exactly one parent selected:
     * Apply selections (remove unselected parents)
     * Clean up file
     * EXIT
   - If SOME notes need work:
     * Move incomplete notes to top
     * Move complete notes below divider
     * Tell user how many need work
     * EXIT

Usage:
    python transforms/I2_resolve_multi_parents.py <input_folder>
    
Example:
    python transforms/I2_resolve_multi_parents.py 01457A9BFGHJ
    # Creates output folder: 01457A9BFGHJI2
"""

import re
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "I2"
SCRIPT_NAME = "resolve_multi_parents"

RESOLUTION_FILE = "resolve_multi_parents.md"


def get_multi_parent_notes(notes: list[Note]) -> list[Note]:
    """Get all notes with more than one parent."""
    return [n for n in notes if len(n.metadata.get("parents", [])) > 1]


def generate_resolution_file(notes: list[Note]) -> int:
    """Generate the markdown file with checkboxes for multi-parent notes."""
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
        f"3. Run: python transforms/{SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>",
        "",
        "Repeat until all notes are resolved!",
    ])
    
    output_path = Path(RESOLUTION_FILE)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    
    return len(multi_notes)


def parse_resolution_file() -> dict[str, list[str]]:
    """
    Parse the resolution file and return all selections.
    
    Returns dict mapping note title -> list of selected parent titles
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
        
        # Check for checked parent (both [x] and [X])
        if current_note and (line.startswith("- [x] ") or line.startswith("- [X] ")):
            parent_title = line[6:].strip()
            if current_note in selections:
                selections[current_note].append(parent_title)
    
    return selections


def categorize_selections(selections: dict[str, list[str]]) -> tuple[dict[str, str], list[str]]:
    """
    Categorize selections into complete and incomplete.
    
    Returns (complete_dict, incomplete_list) where:
    - complete_dict: note_title -> selected_parent (exactly one selected)
    - incomplete_list: note_titles that need work (0 or 2+ selected)
    """
    complete = {}
    incomplete = []
    
    for note_title, parents in selections.items():
        if len(parents) == 1:
            complete[note_title] = parents[0]
        else:
            incomplete.append(note_title)
    
    return complete, incomplete


def get_note_by_title(notes: list[Note], title: str) -> Note | None:
    """Find a note by its title."""
    for note in notes:
        if note.title == title:
            return note
    return None


def rewrite_resolution_file(notes: list[Note], complete: dict[str, str], incomplete: list[str]) -> None:
    """
    Rewrite resolution file with incomplete notes at top, complete below divider.
    """
    lines = [
        "# Resolve Multi-Parent Notes",
        "",
        f"**{len(incomplete)} notes still need a parent selected.**",
        f"**{len(complete)} notes are complete.**",
        "",
        "For each incomplete note below, select **EXACTLY ONE** parent.",
        "",
        "---",
        "",
        "## INCOMPLETE - Needs Work",
        "",
    ]
    
    # Add incomplete notes first
    for note_title in incomplete:
        note = get_note_by_title(notes, note_title)
        if not note:
            continue
        
        lines.append(f"### {note_title}")
        lines.append("")
        lines.append("Select ONE parent:")
        lines.append("")
        
        for parent in note.metadata.get("parents", []):
            lines.append(f"- [ ] {parent['title']}")
        
        lines.append("")
    
    # Add divider and complete notes
    lines.extend([
        "---",
        "",
        "## COMPLETE - Already Selected",
        "",
        "These notes already have exactly one parent selected:",
        "",
    ])
    
    for note_title, selected_parent in complete.items():
        lines.append(f"- **{note_title}** → {selected_parent}")
    
    lines.extend([
        "",
        "---",
        "",
        "## Instructions",
        "",
        "1. Check exactly ONE checkbox for each INCOMPLETE note above",
        "2. Save this file",
        f"3. Run: python transforms/{SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>",
        "",
        "Repeat until all notes are resolved!",
    ])
    
    output_path = Path(RESOLUTION_FILE)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def apply_selections(notes: list[Note], selections: dict[str, str]) -> list[Note]:
    """Apply parent selections to notes."""
    for note in notes:
        if note.title not in selections:
            continue
        
        selected_parent = selections[note.title]
        parents = note.metadata.get("parents", [])
        
        # Keep only the selected parent
        new_parents = [p for p in parents if p["title"] == selected_parent]
        note.metadata["parents"] = new_parents
    
    return notes


def transform(notes: list[Note]) -> list[Note]:
    """Interactive transform to resolve multi-parent notes."""
    resolution_path = Path(RESOLUTION_FILE)
    
    # CASE 1: File doesn't exist - generate it
    if not resolution_path.exists():
        multi_count = len(get_multi_parent_notes(notes))
        
        if multi_count == 0:
            print("  No multi-parent notes found. Nothing to resolve.")
            return notes
        
        print(f"\nGenerating resolution file: {RESOLUTION_FILE}")
        generate_resolution_file(notes)
        print(f"  {multi_count} notes with multiple parents listed")
        print(f"\n>>> Please edit {RESOLUTION_FILE} and select ONE parent per note.")
        print(f">>> Then run: python transforms/{SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        return notes  # Exit without saving output
    
    # CASE 2: File exists - parse and process
    selections = parse_resolution_file()
    complete, incomplete = categorize_selections(selections)
    
    # CASE 2a: All complete - apply and finish
    if not incomplete:
        print(f"\nAll {len(complete)} notes have exactly one parent selected!")
        print("  Applying selections...")
        notes = apply_selections(notes, complete)
        resolution_path.unlink()
        print(f"  Cleaned up {RESOLUTION_FILE}")
        return notes
    
    # CASE 2b: Some incomplete - reorganize file
    print(f"\n{len(incomplete)} notes still need a parent selected.")
    print(f"  {len(complete)} notes are complete.")
    
    # Rewrite file with incomplete at top
    rewrite_resolution_file(notes, complete, incomplete)
    print(f"\n>>> Updated {RESOLUTION_FILE}")
    print(f">>> Incomplete notes moved to top, complete notes moved to bottom.")
    print(f">>> Please select ONE parent for each incomplete note.")
    print(f">>> Then run: python transforms/{SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
    
    return notes  # Exit without saving output (user needs to finish)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGHJ")
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
    
    # Check if we should save (only if resolution file doesn't exist or all resolved)
    resolution_path = Path(RESOLUTION_FILE)
    if resolution_path.exists():
        print("\nResolution not complete. Output NOT saved.")
        print("Please finish selecting parents and run again.")
        sys.exit(0)
    
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
    print(f"  2. Create the next transform script")


if __name__ == "__main__":
    main()
