"""
Y_inline_tasks_with_recurring.py - Inline tasks with Obsidian Tasks plugin recurring support.

Converts task notes into Obsidian Tasks plugin format:
- Regular tasks: Inlined as checkboxes in parent notes (like Transform L)
- RepeatedTasks: DELETED (they're replaced by Tasks plugin auto-recurrence)
- RepeatingTasks: Kept as notes with 🔁 recurrence syntax added

Usage:
    python transforms/Y_inline_tasks_with_recurring.py <input_folder>
    
Example:
    python transforms/Y_inline_tasks_with_recurring.py 01457A9BFGHJK
    # Creates output folder: 01457A9BFGHJKY
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "Y"
SCRIPT_NAME = "inline_tasks_with_recurring"


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
    
    Format: - [ ] Task title 🔁 every week 📅 YYYY-MM-DD
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
    Process all tasks:
    - RepeatedTasks: Delete them (don't keep, don't inline)
    - RepeatingTasks: Keep as notes with 🔁 formatting added to content
    - Regular Tasks: Inline as checkboxes in parent notes
    """
    # Separate task types
    repeating_tasks = [n for n in notes if "RepeatingTask" in n.tags]
    repeated_tasks = [n for n in notes if "RepeatedTask" in n.tags]
    regular_tasks = [n for n in notes if "Task" in n.tags 
                     and "RepeatingTask" not in n.tags 
                     and "RepeatedTask" not in n.tags]
    non_tasks = [n for n in notes if "Task" not in n.tags]
    
    print(f"  Found {len(repeating_tasks)} RepeatingTasks")
    print(f"  Found {len(repeated_tasks)} RepeatedTasks (will be deleted)")
    print(f"  Found {len(regular_tasks)} regular tasks")
    
    # Track statistics
    tasks_inlined = 0
    tasks_orphaned = 0
    repeating_formatted = 0
    repeated_deleted = len(repeated_tasks)
    
    # Index non-task notes by title for quick lookup
    notes_by_title = {n.title: n for n in non_tasks}
    # Also include RepeatingTasks in the index (they can be parents)
    for rt in repeating_tasks:
        notes_by_title[rt.title] = rt
    
    # Step 1: Process RepeatingTasks - add 🔁 formatting to their content
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
    # Keep: non_tasks + repeating_tasks (now with 🔁 formatting)
    # Drop: regular_tasks (inlined) + repeated_tasks (deleted)
    result = non_tasks + repeating_tasks
    
    print(f"  RepeatingTasks formatted with recurrence: {repeating_formatted}")
    print(f"  RepeatedTasks deleted: {repeated_deleted}")
    print(f"  Regular tasks inlined: {tasks_inlined}")
    print(f"  Regular tasks kept (orphaned): {tasks_orphaned}")
    
    return result


def transform(notes: list[Note]) -> list[Note]:
    """
    Main transform function.
    """
    print("\nProcessing tasks with Obsidian Tasks plugin support...")
    print("  - RepeatedTasks: DELETED (replaced by auto-recurrence)")
    print("  - RepeatingTasks: [recurrence] formatting added")
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
    print(f"  2. Check RepeatingTasks for recurrence formatting")
    print(f"  3. Verify RepeatedTasks were deleted")


if __name__ == "__main__":
    main()
