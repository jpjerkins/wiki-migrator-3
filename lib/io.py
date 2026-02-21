"""
I/O operations for transform scripts.

Handles loading JSON data and saving output (JSON + Markdown).
"""

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Note


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Removes or replaces characters that are invalid in file paths.
    """
    # Replace invalid characters with underscore
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove control characters
    name = re.sub(r'[\x00-\x1f]', '', name)
    # Trim whitespace and periods (Windows doesn't like trailing periods)
    name = name.strip('. ')
    # Ensure not empty
    if not name:
        name = "untitled"
    return name


def load_json(folder: Path | str) -> list["Note"]:
    """
    Load notes from a JSON file in the given folder.
    
    Args:
        folder: Path to the input folder containing notes.json
        
    Returns:
        List of Note objects
    """
    from .models import Note
    
    folder = Path(folder)
    json_path = folder / "_notes.json"
    
    if not json_path.exists():
        raise FileNotFoundError(f"_notes.json not found in {folder}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, dict) and "notes" in data:
        notes_data = data["notes"]
    else:
        notes_data = data
    
    return [Note.model_validate(note) for note in notes_data]


def save_output(folder: Path | str, notes: list["Note"]) -> None:
    """
    Save notes to JSON and Markdown export in the given folder.
    
    Args:
        folder: Path to the output folder to create
        notes: List of Note objects to save
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    _save_json(folder, notes)
    
    # Save Markdown files
    _save_markdown(folder, notes)


def _save_json(folder: Path, notes: list["Note"]) -> None:
    """Save notes as JSON."""
    json_path = folder / "_notes.json"
    
    data = {
        "notes": [note.model_dump(mode="json") for note in notes],
        "count": len(notes),
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def _save_markdown(folder: Path, notes: list["Note"]) -> None:
    """Save notes as individual Markdown files."""
    for note in notes:
        # Create subdirectory if needed
        note_path = folder / note.path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build markdown content
        md_content = _build_markdown(note)
        
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(md_content)


def _build_markdown(note: "Note") -> str:
    """Build markdown content from a Note."""
    lines = []
    
    # Frontmatter
    lines.append("---")
    lines.append(f"id: {note.id}")
    lines.append(f"title: {note.title}")
    lines.append(f"created: {note.created.isoformat()}")
    lines.append(f"modified: {note.modified.isoformat()}")
    if note.tags:
        lines.append(f"tags: [{', '.join(note.tags)}]")
    if note.metadata:
        for key, value in note.metadata.items():
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    
    # Title
    lines.append(f"# {note.title}")
    lines.append("")
    
    # Content
    lines.append(note.content)
    lines.append("")
    
    # Tasks section
    if note.tasks:
        lines.append("## Tasks")
        lines.append("")
        for task in note.tasks:
            checkbox = "[x]" if task.completed else "[ ]"
            priority = f" !{task.priority}" if task.priority else ""
            due = f" 📅 {task.due_date.date()}" if task.due_date else ""
            lines.append(f"- {checkbox} {task.content}{priority}{due}")
        lines.append("")
    
    # Attachments section
    if note.attachments:
        lines.append("## Attachments")
        lines.append("")
        for att in note.attachments:
            lines.append(f"- [{att.filename}]({att.path or att.filename})")
        lines.append("")
    
    return "\n".join(lines)
