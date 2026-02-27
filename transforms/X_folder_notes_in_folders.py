"""
W_folder_notes_in_folders.py - Put parent notes in their own folders, preserve content.

Combines best of R and V:
1. Puts parent notes inside their own folders (like R)
2. Preserves existing note content exactly (like V)
3. Creates minimal folder notes only for folders without existing notes

Usage:
    python transforms/W_folder_notes_in_folders.py <input_folder>
    
Example:
    python transforms/W_folder_notes_in_folders.py 01457A9BFGHJKLMU
    # Creates final output in: output/01457A9BFGHJKLMUW/
"""

import json
import shutil
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, validate_notes

SCRIPT_ID = "W"
SCRIPT_NAME = "folder_notes_in_folders"


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
    
    # Content (preserved as-is)
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
    Create final folder structure with parent notes in their own folders.
    """
    # Clear/create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    # Collect all folder paths from output_path
    folder_paths = set()
    for note in notes:
        path = note.metadata.get("output_path", ".")
        if path != ".":
            folder_paths.add(path)
            # Add parent paths
            parts = path.split("/")
            for i in range(1, len(parts)):
                folder_paths.add("/".join(parts[:i]))
    
    print(f"  Creating {len(folder_paths)} folders...")
    
    # Create all directories
    for folder_path in folder_paths:
        (output_dir / folder_path).mkdir(parents=True, exist_ok=True)
    
    # Identify which notes are "parent notes" (have children)
    # These need to be put in their own subfolder
    all_parents = set()
    for note in notes:
        parents = note.metadata.get("parents", [])
        if parents:
            all_parents.add(parents[0]["title"])
    
    # Find folder names (last part of each path)
    folder_names = set()
    for fp in folder_paths:
        folder_names.add(fp.split("/")[-1])
    
    # Notes that are folder notes (exist and match a folder name)
    existing_folder_notes = []
    # Folders needing new minimal notes
    folders_needing_notes = set(folder_names)
    
    for note in notes:
        if note.title in folder_names:
            existing_folder_notes.append(note)
            folders_needing_notes.discard(note.title)
    
    print(f"  {len(existing_folder_notes)} existing notes will become folder notes")
    print(f"  {len(folders_needing_notes)} folders need new minimal notes")
    
    # Write all notes
    notes_written = 0
    
    # First, write existing notes (including folder notes)
    for note in notes:
        output_path = note.metadata.get("output_path", ".")
        safe_filename = sanitize_filename(note.title) + ".md"
        
        # Check if this note is a folder note (its title matches a folder name)
        is_folder_note = note.title in folder_names
        
        if is_folder_note:
            # Put in its own subfolder
            # Path is: output_dir / output_path / note_title / note_title.md
            file_path = output_dir / output_path / note.title / safe_filename
            note.metadata["is_folder_note"] = True
        elif output_path == ".":
            file_path = output_dir / safe_filename
        else:
            file_path = output_dir / output_path / safe_filename
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = build_note_content(note)
        file_path.write_text(content, encoding="utf-8")
        notes_written += 1
    
    # Create minimal folder notes for folders without existing notes
    from datetime import datetime
    now = datetime.now()
    
    for folder_name in folders_needing_notes:
        # Find the full path for this folder
        folder_full_path = None
        for fp in folder_paths:
            if fp.endswith(folder_name) and (len(fp) == len(folder_name) or fp[-len(folder_name)-1] == "/"):
                folder_full_path = fp
                break
        
        if not folder_full_path:
            continue
        
        # Create minimal folder note
        folder_note = Note(
            id=f"folder-{folder_name.lower().replace(' ', '-').replace('/', '-')}",
            title=folder_name,
            content=f"# {folder_name}\n",
            path=f"{folder_full_path}/{folder_name}.md",
            created=now,
            modified=now,
            tags=["Folder"],
            tasks=[],
            attachments=[],
            metadata={
                "output_path": folder_full_path,
                "is_folder_note": True,
            },
        )
        
        safe_filename = sanitize_filename(folder_name) + ".md"
        file_path = output_dir / folder_full_path / folder_name / safe_filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = build_note_content(folder_note)
        file_path.write_text(content, encoding="utf-8")
        notes_written += 1
    
    return notes_written, len(folder_paths)


def transform(notes: list[Note], output_dir: Path) -> list[Note]:
    """Main transform function."""
    print(f"\nCreating folder structure with notes in their own folders...")
    print(f"Output location: {output_dir}")
    
    notes_written, folders_created = write_final_structure(notes, output_dir)
    
    print(f"  Notes written: {notes_written}")
    print(f"  Folders created: {folders_created}")
    
    return notes


def main() -> None:
    """Main entry point."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGHJKLMU")
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
    
    notes = transform(notes, output_folder)
    
    # Save JSON
    json_path = output_folder / "_notes.json"
    json_path.write_text(
        json.dumps({"notes": [n.model_dump(mode="json") for n in notes]}, indent=2, default=str),
        encoding="utf-8"
    )
    
    print(f"\n{'='*50}")
    print("MIGRATION COMPLETE!")
    print(f"{'='*50}")
    print(f"\nFinal output location: {output_folder}")
    print(f"\nParent notes are in their own folders.")
    print(f"Original content preserved.")


if __name__ == "__main__":
    main()
