"""
O_write_final_structure.py - Create final folder structure and write all notes.

This is the FINAL transform that:
1. Creates the folder structure in output/O/
2. Creates folder notes for parent notes (notes that have children)
3. Writes all notes to their assigned folders
4. Updates note paths to reflect final location

Usage:
    python transforms/O_write_final_structure.py <input_folder>
    
Example:
    python transforms/O_write_final_structure.py 01457A9BFGHJKLMN
    # Creates final output in: output/O/
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "O"
SCRIPT_NAME = "write_final_structure"

# FINAL_OUTPUT_DIR will be set based on input folder name in main()


def get_folder_notes(notes: list[Note]) -> set[str]:
    """
    Identify which notes are "folder notes" (have children).
    
    Returns set of folder names that need folder notes created.
    """
    folder_names = set()
    
    for note in notes:
        output_path = note.metadata.get("output_path", ".")
        if output_path != ".":
            folder_names.add(output_path)
    
    return folder_names


def create_folder_note(folder_name: str, notes: list[Note]) -> Note:
    """
    Create a folder note for a folder.
    
    The folder note is named after the folder and contains:
    - List of child notes
    - Links to child notes
    """
    # Find all notes in this folder
    child_notes = [
        n for n in notes 
        if n.metadata.get("output_path") == folder_name and n.title != folder_name
    ]
    
    # Build content
    content_lines = [
        f"# {folder_name}",
        "",
        f"This folder contains {len(child_notes)} note(s).",
        "",
        "## Contents",
        "",
    ]
    
    for child in sorted(child_notes, key=lambda n: n.title):
        content_lines.append(f"- [[{child.title}]]")
    
    content = "\n".join(content_lines)
    
    # Check if there's already a note with this title
    existing = next((n for n in notes if n.title == folder_name), None)
    
    if existing:
        # Use existing note but update its content and path
        existing.content = content
        existing.path = f"{folder_name}/{folder_name}.md"
        existing.metadata["is_folder_note"] = True
        return existing
    else:
        # Create new folder note
        from datetime import datetime
        now = datetime.now()
        
        return Note(
            id=f"folder-{folder_name.lower().replace(' ', '-')}",
            title=folder_name,
            content=content,
            path=f"{folder_name}/{folder_name}.md",
            created=now,
            modified=now,
            tags=["Folder"],
            tasks=[],
            attachments=[],
            metadata={
                "output_path": folder_name,
                "is_folder_note": True,
            },
        )


def write_notes_to_folders(notes: list[Note], output_dir: Path) -> tuple[int, int]:
    """
    Write all notes to their assigned folders.
    
    Returns (notes_written, folders_created)
    """
    # Clear/create final output directory
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    # Track folders created
    folders_created = set()
    notes_written = 0
    
    # Create folder structure
    folder_names = get_folder_notes(notes)
    print(f"  Creating {len(folder_names)} folders...")
    
    for folder_name in folder_names:
        folder_path = output_dir / folder_name
        # Use parents=True to create nested directories
        folder_path.mkdir(parents=True, exist_ok=True)
        folders_created.add(folder_name)
    
    # Create folder notes
    print(f"  Creating folder notes...")
    folder_notes = []
    for folder_name in folder_names:
        folder_note = create_folder_note(folder_name, notes)
        folder_notes.append(folder_note)
    
    # Combine all notes
    all_notes = notes + [fn for fn in folder_notes if fn not in notes]
    
    # Write each note
    print(f"  Writing notes...")
    for note in all_notes:
        output_path = note.metadata.get("output_path", ".")
        
        # Determine file path
        if output_path == ".":
            file_path = FINAL_OUTPUT_DIR / f"{note.title}.md"
        else:
            file_path = FINAL_OUTPUT_DIR / output_path / f"{note.title}.md"
        
        # Sanitize filename
        safe_filename = sanitize_filename(note.title) + ".md"
        if output_path == ".":
            file_path = output_dir / safe_filename
        else:
            file_path = output_dir / output_path / safe_filename
        
        # Write note content
        content = build_note_content(note)
        file_path.write_text(content, encoding="utf-8")
        notes_written += 1
    
    return notes_written, len(folders_created)


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


def transform(notes: list[Note], output_dir: Path) -> list[Note]:
    """
    Main transform function.
    """
    print(f"\nCreating final output structure in: {output_dir}")
    
    notes_written, folders_created = write_notes_to_folders(notes, output_dir)
    
    print(f"  Notes written: {notes_written}")
    print(f"  Folders created: {folders_created}")
    
    return notes


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGHJKLMN")
        sys.exit(1)
    
    input_folder_name = sys.argv[1]
    input_folder = Path("output") / input_folder_name
    
    if not input_folder.exists():
        print(f"Error: Input folder not found: {input_folder}")
        sys.exit(1)
    
    print(f"Loading notes from: {input_folder}")
    notes = load_json(input_folder)
    print(f"Loaded {len(notes)} notes")
    
    notes = transform(notes, output_folder)
    
    print(f"\n{'='*50}")
    print("MIGRATION COMPLETE!")
    print(f"{'='*50}")
    print(f"\nFinal output location: {output_folder}")
    print(f"\nYou can now:")
    print(f"  1. Open {output_folder} as an Obsidian vault")
    print(f"  2. Review the folder structure")
    print(f"  3. Move/copy to your final destination")


if __name__ == "__main__":
    main()
