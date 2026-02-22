"""
Diagnostic script for I2 transform issues.
"""

import json
import re
from pathlib import Path

RESOLUTION_FILE = "resolve_multi_parents.md"

def get_multi_parent_notes(data):
    """Get notes with multiple parents from JSON."""
    return [n for n in data['notes'] if len(n.get('metadata', {}).get('parents', [])) > 1]

def parse_resolution_file():
    """Parse the resolution file."""
    resolution_path = Path(RESOLUTION_FILE)
    if not resolution_path.exists():
        print(f"ERROR: {RESOLUTION_FILE} not found!")
        return {}
    
    content = resolution_path.read_text(encoding='utf-8')
    
    selections = {}
    current_note = None
    
    for line in content.split("\n"):
        # Check for note header (both ## and ###)
        note_match = re.match(r"^###? (.+)$", line)
        if note_match:
            current_note = note_match.group(1).strip()
            selections[current_note] = []
            continue
        
        # Check for checked parent
        if current_note and (line.startswith("- [x] ") or line.startswith("- [X] ")):
            parent_title = line[6:].strip()
            if current_note in selections:
                selections[current_note].append(parent_title)
    
    return selections

def main():
    # Load JSON
    json_path = Path("output/01457A9BFGHJ/_notes.json")
    if not json_path.exists():
        print(f"JSON not found at {json_path}")
        return
    
    data = json.loads(json_path.read_text(encoding='utf-8'))
    multi_notes = get_multi_parent_notes(data)
    
    print(f"Notes with multiple parents in JSON: {len(multi_notes)}")
    print()
    
    # Parse resolution file
    selections = parse_resolution_file()
    print(f"Notes found in {RESOLUTION_FILE}: {len(selections)}")
    print()
    
    # Find discrepancies
    json_titles = {n['title'] for n in multi_notes}
    md_titles = set(selections.keys())
    
    # Notes in JSON but not in markdown
    missing_from_md = json_titles - md_titles
    if missing_from_md:
        print(f"ERROR: {len(missing_from_md)} notes in JSON but NOT in markdown:")
        for title in sorted(missing_from_md):
            print(f"  - {title}")
        print()
    
    # Notes in markdown but not in JSON (shouldn't happen)
    extra_in_md = md_titles - json_titles
    if extra_in_md:
        print(f"WARNING: {len(extra_in_md)} notes in markdown but NOT in JSON:")
        for title in sorted(extra_in_md):
            print(f"  - {title}")
        print()
    
    # Check selection counts
    print("Selection counts per note:")
    zero_selections = []
    one_selection = []
    multiple_selections = []
    
    for title, parents in selections.items():
        count = len(parents)
        if count == 0:
            zero_selections.append(title)
        elif count == 1:
            one_selection.append(title)
        else:
            multiple_selections.append((title, count))
    
    print(f"  0 selections: {len(zero_selections)} notes")
    print(f"  1 selection:  {len(one_selection)} notes")
    print(f"  2+ selections: {len(multiple_selections)} notes")
    print()
    
    if zero_selections:
        print("Notes with ZERO selections:")
        for title in sorted(zero_selections):
            print(f"  - {title}")
        print()
    
    if multiple_selections:
        print("Notes with MULTIPLE selections:")
        for title, count in sorted(multiple_selections):
            print(f"  - {title} ({count} selected)")
        print()
    
    # Show a sample comparison
    if multi_notes and selections:
        sample_note = multi_notes[0]
        sample_title = sample_note['title']
        print(f"Sample check - Note: '{sample_title}'")
        print(f"  JSON parents: {[p['title'] for p in sample_note.get('metadata', {}).get('parents', [])]}")
        if sample_title in selections:
            print(f"  MD selections: {selections[sample_title]}")
        else:
            print(f"  NOT FOUND in markdown!")

if __name__ == "__main__":
    main()
