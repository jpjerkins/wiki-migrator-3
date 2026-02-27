"""
Z_inline_tasks_protected_parents.py - Inline tasks with protected parent notes.

Enhancement of Transform Y that protects notes referenced as parents:
- Identifies all notes referenced as parents by other notes
- Excludes referenced parents from task classification (even if they have Task tags)
- RepeatingTasks: Kept as notes with 🔁 recurrence formatting
- RepeatedTasks: DELETED (replaced by Tasks plugin auto-recurrence)
- Regular tasks: Inlined as checkboxes in parent notes

Usage:
    python transforms/Z_inline_tasks_protected_parents.py <input_folder>
    
Example:
    python transforms/Z_inline_tasks_protected_parents.py 01457A9BFGHJK
    # Creates output folder: 01457A9BFGHJKZ
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "Z"
SCRIPT_NAME = "inline_tasks_protected_parents"


def get_referenced_parents(notes: list[Note]) -> set[str]:
    """
    Build a set of all note titles that are referenced as parents.
    These notes should be protected from task classification.
    """
    referenced = set()
    for note in notes:
        parents = note.metadata.get("parents", [])
        for parent in parents:
            referenced.add(parent["title"])
    return referenced


def detect_recurrence_rule(task: Note) -> str:
    """
    Detect recurrence rule from task tags and title.
    Returns Tasks plugin format: 'every day', 'every week', etc.
    """
    tags = [t.lower() for t in task.tags]
    title_lower = task.title.lower()
    
    # Check for specific interval tags
    if 'daily' in tags or 'dailyfocus' in tags:
        return "every day"
    if 'weekly' in tags:
        return "every week"
    if 'biweekly' in tags or 'bi-weekly' in tags:
        return "every 2 weeks"
    if 'monthly' in tags:
        return "every month"
    if 'quarterly' in tags:
        return "every 3 months"
    if 'yearly' in tags or 'annual' in tags:
        return "every year"
    
    # Check title for clues
    if 'daily' in title_lower or 'every day' in title_lower:
        return "every day"
    if 'weekly' in title_lower or 'every week' in title_lower:
        return "every week"
    if 'monthly' in title_lower or 'every month' in title_lower:
        return "every month"
    if 'biweekly' in title_lower or 'bi-weekly' in title_lower:
        return "every 2 weeks"
    
    # Default to weekly for most repeating tasks
    return "every week"


def find_due_date(task: Note) -> str | None:
    """
    Try to find a due date for the task from metadata or tags.
    Returns YYYY-MM-DD string or None.
    """
    # Check for date in tags (sometimes dates are embedded)
    for tag in task.tags:
        # Look for date patterns like 2026-02-21
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', tag)
        if date_match:
            return tag[date_match.start():date_match.end()]
    
    return None


def format_recurring_task(task: Note) -> str:
    """
    Format a RepeatingTask as an Obsidian Tasks plugin recurring task.
    
    Format: - [ ] Task title [RECUR] every week [DUE] YYYY-MM-DD
    (emojis replaced for display; actual output uses proper characters)
    """
    recurrence = detect_recurrence_rule(task)
    
    # Use emoji directly in the task format
    checkbox = f"- [ ] {task.title} 🔁 {recurrence}"
    
    # Try to find a due date, otherwise use today + 7 days as default
    due_date = find_due_date(task)
    if not due_date:
        # Default to one week from today
        future = datetime.now() + timedelta(days=7)
        due_date = future.strftime('%Y-%m-%d')
    
    checkbox += f" 📅 {due_date}"
    
    return checkbox


def find_or_create_next_actions_section(content: str) -> str:
    """
    Find or create a '## Next Actions' section in the content.
    """
    if "## Next Actions" in content:
        return content
    
    if not content.endswith("\n"):
        content += "\n"
    
    content += "\n## Next Actions\n\n"
    return content


def format_regular_task(task: Note) -> str:
    """
    Convert a regular task note to a checkbox format.
    """
    checkbox = f"- [ ] {task.title}"
    
    if task.content and task.content.strip():
        lines = [l.strip() for l in task.content.split("\n") if l.strip()]
        if lines and lines[0] != task.title:
            checkbox += f"\n  - {lines[0][:100]}"
    
    return checkbox


def process_tasks(notes: list[Note]) -> list[Note]:
    """
    Process all tasks with protected parent notes.
    """
    # Step 0: Identify all notes referenced as parents
    referenced_parents = get_referenced_parents(notes)
    print(f"  Found {len(referenced_parents)} notes referenced as parents")
    
    # Log some examples of protected notes
    protected_examples = [t for t in referenced_parents if t in ['Orphan Tasks', 'I grow assets', 'I lead teams to success']]
    if protected_examples:
        print(f"  Protected examples: {', '.join(protected_examples)}")
    
    # Separate task types
    # KEY FIX: Exclude referenced parents from ALL task classifications
    repeating_tasks = [n for n in notes 
                       if "RepeatingTask" in n.tags 
                       and n.title not in referenced_parents]
    repeated_tasks = [n for n in notes 
                      if "RepeatedTask" in n.tags]
    regular_tasks = [n for n in notes 
                     if "Task" in n.tags 
                     and "RepeatingTask" not in n.tags 
                     and "RepeatedTask" not in n.tags
                     and n.title not in referenced_parents]  # KEY FIX
    
    # Notes that are protected (referenced as parents) - keep them all
    protected_notes = [n for n in notes if n.title in referenced_parents]
    
    # Non-task notes (no Task tag and not referenced)
    non_tasks = [n for n in notes 
                 if "Task" not in n.tags 
                 and n.title not in referenced_parents]
    
    print(f"  Found {len(repeating_tasks)} RepeatingTasks")
    print(f"  Found {len(repeated_tasks)} RepeatedTasks (will be deleted)")
    print(f"  Found {len(regular_tasks)} regular tasks")
    print(f"  Found {len(protected_notes)} protected parent notes")
    
    # Track statistics
    tasks_inlined = 0
    tasks_orphaned = 0
    repeating_formatted = 0
    repeated_deleted = len(repeated_tasks)
    
    # Index for parent lookups (includes protected notes)
    notes_by_title = {n.title: n for n in non_tasks}
    for pn in protected_notes:
        notes_by_title[pn.title] = pn
    for rt in repeating_tasks:
        notes_by_title[rt.title] = rt
    
    # Step 1: Process RepeatingTasks - add recurrence formatting to their content
    for task in repeating_tasks:
        checkbox = format_recurring_task(task)
        
        # Add to content
        if not task.content.endswith("\n"):
            task.content += "\n"
        task.content += f"\n{checkbox}\n"
        
        # Also add to Next Actions section if there's a parent
        parents = task.metadata.get("parents", [])
        if parents:
            parent_title = parents[0]["title"]
            parent_note = notes_by_title.get(parent_title)
            if parent_note:
                parent_note.content = find_or_create_next_actions_section(parent_note.content)
                if not parent_note.content.endswith("\n"):
                    parent_note.content += "\n"
                parent_note.content += checkbox + "\n"
        
        repeating_formatted += 1
    
    # Step 2: Process regular tasks - inline as checkboxes
    for task in regular_tasks:
        parents = task.metadata.get("parents", [])
        
        if not parents:
            # Task has no parent - keep it as a separate note
            non_tasks.append(task)
            tasks_orphaned += 1
            continue
        
        parent_title = parents[0]["title"]
        parent_note = notes_by_title.get(parent_title)
        
        if not parent_note:
            # Parent not found - keep task as separate note
            non_tasks.append(task)
            tasks_orphaned += 1
            continue
        
        # Format task as checkbox and add to parent
        checkbox = format_regular_task(task)
        parent_note.content = find_or_create_next_actions_section(parent_note.content)
        
        if not parent_note.content.endswith("\n"):
            parent_note.content += "\n"
        parent_note.content += checkbox + "\n"
        
        tasks_inlined += 1
    
    # Step 3: Combine results
    # Keep: non_tasks + protected_notes + repeating_tasks (now with recurrence formatting)
    # Drop: regular_tasks (inlined) + repeated_tasks (deleted)
    result = non_tasks + protected_notes + repeating_tasks
    
    print(f"  RepeatingTasks formatted: {repeating_formatted}")
    print(f"  RepeatedTasks deleted: {repeated_deleted}")
    print(f"  Regular tasks inlined: {tasks_inlined}")
    print(f"  Regular tasks kept (orphaned): {tasks_orphaned}")
    print(f"  Protected parent notes preserved: {len(protected_notes)}")
    
    return result


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    """
    print("\nProcessing tasks with protected parent notes...")
    print("  - Protected parents: Excluded from task classification")
    print("  - RepeatedTasks: DELETED (replaced by auto-recurrence)")
    print("  - RepeatingTasks: Recurrence formatting added")
    print("  - Regular tasks: Inlined as checkboxes")
    return process_tasks(notes)


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
    print(f"  2. Check protected parent notes are preserved")
    print(f"  3. Verify RepeatedTasks were deleted")


if __name__ == "__main__":
    main()
