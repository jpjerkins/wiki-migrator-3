"""
L_inline_tasks.py - Inline tasks into their parent notes as checkboxes.

Converts task notes into checkboxes within their parent notes:
- Finds all notes with "Task" tag
- For each task, locates its parent note
- Converts task content to checkbox format: "- [ ] Task title"
- Adds to "## Next Actions" section in parent note
- Removes the separate task note

Usage:
    python transforms/L_inline_tasks.py <input_folder>
    
Example:
    python transforms/L_inline_tasks.py 01457A9BFGHJK
    # Creates output folder: 01457A9BFGHJKL
"""

import re
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "L"
SCRIPT_NAME = "inline_tasks"


def get_parent_note(notes: list[Note], parent_title: str) -> Note | None:
    """Find a note by its title."""
    for note in notes:
        if note.title == parent_title:
            return note
    return None


def find_or_create_next_actions_section(content: str) -> str:
    """
    Find or create a '## Next Actions' section in the content.
    
    Returns updated content with the section ready for appending tasks.
    """
    # Check if Next Actions section exists
    if "## Next Actions" in content:
        return content
    
    # Add Next Actions section at the end
    if not content.endswith("\n"):
        content += "\n"
    
    content += "\n## Next Actions\n\n"
    return content


def format_task_as_checkbox(task: Note) -> str:
    """
    Convert a task note to a checkbox format.
    
    Format: - [ ] Task title (or first line of content)
    """
    # Use title as the checkbox text
    checkbox = f"- [ ] {task.title}"
    
    # If task has content, add it as indented text below
    if task.content and task.content.strip():
        # Get first non-empty line of content as details
        lines = [l.strip() for l in task.content.split("\n") if l.strip()]
        if lines and lines[0] != task.title:
            # Add first line as indented detail
            checkbox += f"\n  - {lines[0][:100]}"  # Limit to 100 chars
    
    return checkbox


def inline_tasks(notes: list[Note]) -> list[Note]:
    """
    Inline all task notes into their parent notes.
    
    Args:
        notes: List of all notes
        
    Returns:
        List of notes with tasks inlined (task notes removed)
    """
    # Separate tasks from non-tasks
    tasks = [n for n in notes if "Task" in n.tags]
    non_tasks = [n for n in notes if "Task" not in n.tags]
    
    # Index non-task notes by title for quick lookup
    notes_by_title = {n.title: n for n in non_tasks}
    
    tasks_inlined = 0
    tasks_orphaned = 0
    
    for task in tasks:
        # Get the task's parent
        parents = task.metadata.get("parents", [])
        
        if not parents:
            # Task has no parent - keep it as a separate note for now
            non_tasks.append(task)
            tasks_orphaned += 1
            continue
        
        # Use the first (and should be only) parent
        parent_title = parents[0]["title"]
        parent_note = notes_by_title.get(parent_title)
        
        if not parent_note:
            # Parent not found - keep task as separate note
            non_tasks.append(task)
            tasks_orphaned += 1
            continue
        
        # Format task as checkbox and add to parent
        checkbox = format_task_as_checkbox(task)
        
        # Ensure parent has Next Actions section
        parent_note.content = find_or_create_next_actions_section(parent_note.content)
        
        # Append checkbox to content
        if not parent_note.content.endswith("\n"):
            parent_note.content += "\n"
        parent_note.content += checkbox + "\n"
        
        tasks_inlined += 1
    
    print(f"  Tasks inlined: {tasks_inlined}")
    print(f"  Tasks kept separate (orphaned): {tasks_orphaned}")
    
    return non_tasks


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with tasks inlined into parents
    """
    print("\nInlining tasks into parent notes...")
    return inline_tasks(notes)


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BFGHJK")
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
    
    print(f"\nFinal note count: {len(notes)}")
    
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
    print(f"  2. Check parent notes for '## Next Actions' sections")
    print(f"  3. Create the next transform script")


if __name__ == "__main__":
    main()
