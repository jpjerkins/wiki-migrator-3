"""
R_folder_notes_plugin.py - Create folder notes compatible with Folder Notes plugin.

Creates proper folder notes where the note for a folder is INSIDE that folder
with the same name as the folder. Compatible with Obsidian's Folder Notes plugin.

Example:
- Folder: Projects/OpenClaw Setup/
- Folder Note: Projects/OpenClaw Setup/OpenClaw Setup.md

Usage:
    python transforms/R_folder_notes_plugin.py <input_folder>
    
Example:
    python transforms/R_folder_notes_plugin.py 01457A9BFGHJKLMP
    # Creates final output in: output/O/
"""

import json
import shutil
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, validate_notes

SCRIPT_ID = "R"
SCRIPT_NAME = "folder_notes_plugin"

# Output directory will be set in main() based on input folder name


def get_unique_folder_names(notes: list[Note]) -> set[str]:
    """Extract all unique individual folder names from hierarchical paths."""
    folder_names = set()
    
    for note in notes:
        output_path = note.metadata.get("output_path", ".")
        if output_path != ".":
            parts = output_path.split("/")
            for part in parts:
                if part:
                    folder_names.add(part)
    
    return folder_names


def find_child_items(folder_name: str, notes: list[Note]) -> tuple[set[str], set[str]]:
    """
    Find all child items (subfolders and notes) of a given folder.
    
    Returns (subfolders, child_notes) where:
    - subfolders: folder names that are direct children
    - child_notes: note titles that are direct children
    """
    subfolders = set()
    child_notes = set()
    
    for note in notes:
        output_path = note.metadata.get("output_path", ".")
        if output_path == ".":
            continue
        
        parts = output_path.split("/")
        
        # Check if this path goes through our folder
        for i, part in enumerate(parts):
            if part == folder_name:
                # If there's another level after this, it's a subfolder
                if i < len(parts) - 1:
                    subfolders.add(parts[i + 1])
                break
        
        # Check if this note is directly in this folder
        # (its immediate parent matches folder_name)
        parents = note.metadata.get("parents", [])
        if parents and parents[0]["title"] == folder_name:
            child_notes.add(note.title)
    
    return subfolders, child_notes


def create_folder_note(folder_name: str, notes: list[Note]) -> Note:
    """
    Create a folder note for Folder Notes plugin compatibility.
    
    The note is placed INSIDE the folder with matching name.
    """
    subfolders, child_notes = find_child_items(folder_name, notes)
    
    all_children = sorted(subfolders) + sorted(child_notes)
    
    # Build content
    content_lines = [
        f"# {folder_name}",
        "",
        f"This folder contains {len(subfolders)} subfolder(s) and {len(child_notes)} note(s).",
        "",
    ]
    
    if subfolders:
        content_lines.append("## Subfolders")
        content_lines.append("")
        for subfolder in sorted(subfolders):
            content_lines.append(f"- [[{subfolder}]]")
        content_lines.append("")
    
    if child_notes:
        content_lines.append("## Notes")
        content_lines.append("")
        for child in sorted(child_notes):
            content_lines.append(f"- [[{child}]]")
        content_lines.append("")
    
    content = "\n".join(content_lines)
    
    # Check if there's already a note with this title
    existing = next((n for n in notes if n.title == folder_name), None)
    
    if existing:
        # Update existing note
        existing.content = content
        existing.metadata["is_folder_note"] = True
        existing.metadata["folder_note_path"] = f"{folder_name}/{folder_name}.md"
        return existing
    else:
        # Create new folder note
        from datetime import datetime
        now = datetime.now()
        
        return Note(
            id=f"folder-{folder_name.lower().replace(' ', '-').replace('/', '-')}",
            title=folder_name,
            content=content,
            path=f"{folder_name}/{folder_name}.md",
            created=now,
            modified=now,
            tags=["Folder"],
            tasks=[],
            attachments=[],
            metadata={
                "is_folder_note": True,
                "folder_note_path": f"{folder_name}/{folder_name}.md",
            },
        )


def sanitize_filename(name: str) -> str:
    """Sanitize a name for use as a filename."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    name = name.rstrip('. ')
    if not name:
        name = "untitled"
    return name


def build_note_content(note: Note) -> str:
    """Build the final markdown content for a note."""
    lines = []
    
    # Frontmatter
    lines.append("---")
    lines.append(f"id: {note.id}")
    if note.metadata.get("is_folder_note"):
        lines.append("type: folder")
    if note.tags:
        lines.append(f"tags: [{', '.join(note.tags)}]")
    lines.append("---")
    lines.append("")
    
    # Content
    lines.append(note.content)
    
    # Add backlinks to parent if exists
    parents = note.metadata.get("parents", [])
    if parents and not note.metadata.get("is_folder_note"):
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"**Parent:** [[{parents[0]['title']}]]")
    
    return "\n".join(lines)


def write_final_structure(notes: list[Note], output_dir: Path) -> tuple[int, int]:
    """
    Create final folder structure with proper folder notes.
    """
    # Clear/create final output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    # Get all unique folder names
    folder_names = get_unique_folder_names(notes)
    print(f"  Creating {len(folder_names)} unique folders...")
    
    # Create all directories first
    folders_created = set()
    for note in notes:
        output_path = note.metadata.get("output_path", ".")
        if output_path != ".":
            folder_path = output_dir / output_path
            folder_path.mkdir(parents=True, exist_ok=True)
            folders_created.add(output_path)
    
    # Create folder notes for each unique folder
    print(f"  Creating folder notes...")
    folder_notes = []
    for folder_name in folder_names:
        folder_note = create_folder_note(folder_name, notes)
        folder_notes.append(folder_note)
    
    # Write all regular notes
    print(f"  Writing regular notes...")
    notes_written = 0
    
    for note in notes:
        if note.metadata.get("is_folder_note"):
            continue  # Skip folder notes for now
        
        output_path = note.metadata.get("output_path", ".")
        safe_filename = sanitize_filename(note.title) + ".md"
        
        if output_path == ".":
            file_path = output_dir / safe_filename
        else:
            file_path = output_dir / output_path / safe_filename
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = build_note_content(note)
        file_path.write_text(content, encoding="utf-8")
        notes_written += 1
    
    # Write folder notes (inside their respective folders)
    print(f"  Writing folder notes...")
    for folder_note in folder_notes:
        folder_name = folder_note.title
        safe_filename = sanitize_filename(folder_name) + ".md"
        
        # Folder note goes INSIDE the folder with matching name
        # Find where this folder appears in the hierarchy
        # It could be at top level or nested
        
        # Find all paths that contain this folder
        folder_paths = set()
        for note in notes:
            path = note.metadata.get("output_path", ".")
            if path != "." and folder_name in path.split("/"):
                parts = path.split("/")
                for i, part in enumerate(parts):
                    if part == folder_name:
                        # This is the path to this folder
                        folder_path = "/".join(parts[:i+1])
                        folder_paths.add(folder_path)
        
        # If folder is not in any path, it might be a top-level folder
        if not folder_paths:
            folder_paths = {folder_name}
        
        # Write folder note to each location it appears
        # (usually just one, but could be multiple if same name appears in different branches)
        for folder_path in folder_paths:
            file_path = output_dir / folder_path / safe_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            content = build_note_content(folder_note)
            file_path.write_text(content, encoding="utf-8")
            notes_written += 1
    
    return notes_written, len(folders_created)


def transform(notes: list[Note], output_dir: Path) -> list[Note]:
    """Main transform function."""
    print(f"\nCreating final output with Folder Notes plugin compatibility...")
    print(f"Output location: {output_dir}")
    
    notes_written, folders_created = write_final_structure(notes, output_dir)
    
    print(f"  Notes written: {notes_written}")
    print(f"  Folders created: {folders_created}")
    
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
    
    notes = transform(notes, output_folder)
    
    # Save JSON
    json_path = output_folder / "_notes.json"
    output_folder.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps({"notes": [n.model_dump(mode="json") for n in notes]}, indent=2, default=str),
        encoding="utf-8"
    )
    
    print(f"\n{'='*50}")
    print("MIGRATION COMPLETE!")
    print(f"{'='*50}")
    print(f"\nFinal output location: {output_folder}")
    print(f"\nFolder Notes plugin compatible structure created!")
    print(f"Each folder contains a note with the same name as the folder.")


if __name__ == "__main__":
    main()
