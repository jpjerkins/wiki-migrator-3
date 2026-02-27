"""
V_folder_notes_minimal.py - Create folder notes without modifying parent content.

Like transform R but:
1. Preserves existing parent note content exactly as-is
2. Does not add child note listings (Obsidian UI shows them)
3. Creates minimal folder notes only for folders without existing notes

Usage:
    python transforms/V_folder_notes_minimal.py <input_folder>
    
Example:
    python transforms/V_folder_notes_minimal.py 01457A9BFGHJKLMU
    # Creates final output in: output/01457A9BFGHJKLMUV/
"""

import json
import shutil
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, validate_notes

SCRIPT_ID = "V"
SCRIPT_NAME = "folder_notes_minimal"


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
    
    # Content (preserved as-is for existing notes)
    lines.append(note.content)
    
    # Add backlinks to parent if exists (for non-folder notes)
    parents = note.metadata.get("parents", [])
    if parents and not note.metadata.get("is_folder_note"):
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"**Parent:** [[{parents[0]['title']}]]")
    
    return "\n".join(lines)


def write_final_structure(notes: list[Note], output_dir: Path) -> tuple[int, int]:
    """
    Create final folder structure.
    
    For existing notes: preserve content, just move to correct folder.
    For new folder notes: create minimal note with just title.
    """
    # Clear/create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    # Collect all unique folder paths
    folder_paths = set()
    for note in notes:
        path = note.metadata.get("output_path", ".")
        if path != ".":
            folder_paths.add(path)
            # Also add parent paths
            parts = path.split("/")
            for i in range(1, len(parts)):
                folder_paths.add("/".join(parts[:i]))
    
    print(f"  Creating {len(folder_paths)} folders...")
    
    # Create all directories
    for folder_path in folder_paths:
        (output_dir / folder_path).mkdir(parents=True, exist_ok=True)
    
    # Find which notes are "folder notes" (have same name as their containing folder)
    folder_note_titles = set()
    for folder_path in folder_paths:
        folder_name = folder_path.split("/")[-1]
        folder_note_titles.add(folder_name)
    
    # Separate existing notes from folders needing new notes
    existing_notes = []  # Notes that exist and should be preserved
    folders_needing_notes = set(folder_note_titles)  # Folders that need a note created
    
    for note in notes:
        if note.title in folders_needing_notes:
            # This note will become a folder note
            folders_needing_notes.discard(note.title)
            existing_notes.append(note)
        else:
            existing_notes.append(note)
    
    print(f"  Preserving {len(existing_notes)} existing notes...")
    print(f"  Creating {len(folders_needing_notes)} minimal folder notes...")
    
    # Write all existing notes
    notes_written = 0
    for note in existing_notes:
        output_path = note.metadata.get("output_path", ".")
        safe_filename = sanitize_filename(note.title) + ".md"
        
        # Check if this is a folder note (title matches last part of path)
        is_folder_note = False
        if output_path != ".":
            path_last_part = output_path.split("/")[-1]
            if note.title == path_last_part:
                is_folder_note = True
                note.metadata["is_folder_note"] = True
        
        if output_path == ".":
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
        # Find the path for this folder
        folder_path = None
        for fp in folder_paths:
            if fp.endswith(folder_name) or fp == folder_name:
                folder_path = fp
                break
        
        if not folder_path:
            continue
        
        # Create minimal folder note
        folder_note = Note(
            id=f"folder-{folder_name.lower().replace(' ', '-').replace('/', '-')}",
            title=folder_name,
            content=f"# {folder_name}\n",
            path=f"{folder_path}/{folder_name}.md",
            created=now,
            modified=now,
            tags=["Folder"],
            tasks=[],
            attachments=[],
            metadata={
                "output_path": folder_path,
                "is_folder_note": True,
            },
        )
        
        safe_filename = sanitize_filename(folder_name) + ".md"
        file_path = output_dir / folder_path / safe_filename
        content = build_note_content(folder_note)
        file_path.write_text(content, encoding="utf-8")
        notes_written += 1
    
    return notes_written, len(folder_paths)


def transform(notes: list[Note], output_dir: Path) -> list[Note]:
    """Main transform function."""
    print(f"\nCreating folder structure with minimal folder notes...")
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
    
    # Output follows naming convention: {input}V
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
    print(f"\nParent note content preserved.")
    print(f"Folder Notes plugin compatible structure created.")


if __name__ == "__main__":
    main()
