"""
Q_fix_folder_notes.py - Fix folder note naming for hierarchical paths.

Fixes the issue where folder notes were named after full paths like 
"Projects_OpenClaw Setup" instead of just "OpenClaw Setup".

Correctly identifies individual folder names from hierarchical paths and
creates properly named folder notes for each.

Usage:
    python transforms/Q_fix_folder_notes.py <input_folder>
    
Example:
    python transforms/Q_fix_folder_notes.py 01457A9BFGHJKLMP
    # Creates output folder: 01457A9BFGHJKLMPQ
"""

import json
import shutil
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "Q"
SCRIPT_NAME = "fix_folder_notes"

# Output directory will be set in main() based on input folder name


def get_unique_folder_names(notes: list[Note]) -> set[str]:
    """
    Extract all unique individual folder names from hierarchical paths.
    
    For paths like "Projects/OpenClaw Setup", extracts both "Projects" and "OpenClaw Setup".
    For paths like "Resources/Learn AI", extracts both "Resources" and "Learn AI".
    """
    folder_names = set()
    
    for note in notes:
        output_path = note.metadata.get("output_path", ".")
        if output_path != ".":
            # Split hierarchical path and add each component
            parts = output_path.split("/")
            for part in parts:
                if part:
                    folder_names.add(part)
    
    return folder_names


def create_folder_note(folder_name: str, notes: list[Note]) -> Note:
    """
    Create a folder note for a specific folder name.
    
    Finds all notes that are direct children of this folder.
    """
    # Find notes that are direct children of this folder
    child_notes = []
    
    for note in notes:
        output_path = note.metadata.get("output_path", ".")
        if output_path == ".":
            continue
        
        # Split the path
        parts = output_path.split("/")
        
        # Check if this note's immediate parent is the folder_name
        # (i.e., path ends with folder_name/note or is folder_name for top-level)
        if len(parts) >= 1 and parts[-1] == folder_name:
            # This note IS in this folder (as the last component)
            # But we want notes that have this as their immediate parent
            pass
        
        # Find notes that are DIRECTLY in this folder
        # Path is like "Projects/OpenClaw Setup" - notes in OpenClaw Setup have this as path
        # We want notes where folder_name is the LAST component of their path
        if parts and parts[-1] == folder_name:
            # This note is the folder itself or a note directly in it
            # Actually, we want notes that have this folder as their output_path
            pass
    
    # Better approach: find notes where this folder is the immediate container
    # A note is in folder "X" if its output_path ends with "/X" or equals "X"
    direct_children = []
    
    for note in notes:
        output_path = note.metadata.get("output_path", ".")
        if output_path == ".":
            continue
        
        parts = output_path.split("/")
        
        # Check if this note's path contains this folder as a component
        # and find notes that are at this level
        for i, part in enumerate(parts):
            if part == folder_name and i < len(parts) - 1:
                # There's a child folder/note after this one
                child_folder = parts[i + 1]
                # We want to list the child folders/notes
                pass
    
    # Simpler approach: Find all notes that have this exact folder in their parent chain
    # and group by immediate parent
    immediate_children = set()
    
    for note in notes:
        output_path = note.metadata.get("output_path", ".")
        if output_path == ".":
            continue
        
        parts = output_path.split("/")
        
        # Check if folder_name appears in the path
        for i, part in enumerate(parts):
            if part == folder_name:
                # If there's something after this in the path, it's a child
                if i < len(parts) - 1:
                    immediate_children.add(parts[i + 1])
                # Also check if any note has this exact path (meaning it's a note IN this folder)
                break
    
    # Also find notes that are directly assigned to this folder
    for note in notes:
        path = note.metadata.get("output_path", "")
        parent = note.metadata.get("parents", [{}])[0].get("title", "") if note.metadata.get("parents") else ""
        
        # If this note's parent matches folder_name, it's a direct child
        if parent == folder_name:
            immediate_children.add(note.title)
    
    # Build content
    content_lines = [
        f"# {folder_name}",
        "",
        f"This folder contains {len(immediate_children)} item(s).",
        "",
        "## Contents",
        "",
    ]
    
    for child in sorted(immediate_children):
        content_lines.append(f"- [[{child}]]")
    
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
                "output_path": folder_name,
                "is_folder_note": True,
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


def write_notes_to_folders(notes: list[Note], output_dir: Path) -> tuple[int, int]:
    """
    Write all notes to their assigned folders with proper hierarchy.
    """
    # Clear/create final output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    # Collect all unique folder names (individual components, not full paths)
    folder_names = get_unique_folder_names(notes)
    
    # Create all folder directories
    print(f"  Creating {len(folder_names)} unique folders...")
    folders_created = set()
    
    for note in notes:
        output_path = note.metadata.get("output_path", ".")
        if output_path != ".":
            # Create the full hierarchical path
            folder_path = output_dir / output_path
            folder_path.mkdir(parents=True, exist_ok=True)
            folders_created.add(output_path)
    
    # Create folder notes for each unique folder name
    print(f"  Creating folder notes...")
    folder_notes = []
    for folder_name in folder_names:
        folder_note = create_folder_note(folder_name, notes)
        folder_notes.append(folder_note)
    
    # Combine all notes
    all_notes = notes + [fn for fn in folder_notes if fn not in notes]
    
    # Write each note
    print(f"  Writing notes...")
    notes_written = 0
    
    for note in all_notes:
        output_path = note.metadata.get("output_path", ".")
        is_folder_note = note.metadata.get("is_folder_note", False)
        
        # Determine file path
        safe_filename = sanitize_filename(note.title) + ".md"
        
        if is_folder_note:
            # Folder notes go in their own folder
            file_path = output_dir / output_path / safe_filename
        elif output_path == ".":
            # Root-level notes
            file_path = output_dir / safe_filename
        else:
            # Regular notes in their assigned folder
            file_path = output_dir / output_path / safe_filename
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write note content
        content = build_note_content(note)
        file_path.write_text(content, encoding="utf-8")
        notes_written += 1
    
    return notes_written, len(folders_created)


def transform(notes: list[Note], output_dir: Path) -> list[Note]:
    """Main transform function."""
    print(f"\nCreating final output structure in: {output_dir}")
    
    notes_written, folders_created = write_notes_to_folders(notes, output_dir)
    
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
    print(f"\nYou can now:")
    print(f"  1. Open {output_folder} as an Obsidian vault")
    print(f"  2. Review the folder structure")
    print(f"  3. Move/copy to your final destination")


if __name__ == "__main__":
    main()
