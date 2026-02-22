"""
Salvage selections from corrupted resolve_multi_parents.md file.
"""

import json
import re
from pathlib import Path

RESOLUTION_FILE = "resolve_multi_parents.md"
JSON_FILE = "output/01457A9BFGHJ/_notes.json"

def extract_selections_from_corrupted_file():
    """Extract note title and selected parent from corrupted format."""
    content = Path(RESOLUTION_FILE).read_text(encoding='utf-8')
    
    selections = {}
    in_complete_section = False
    
    for line in content.split('\n'):
        # Check if we're entering the COMPLETE section
        if '## COMPLETE' in line:
            in_complete_section = True
            continue
        
        # Stop if we hit another divider after complete section
        if in_complete_section and line.startswith('---'):
            break
        
        # Parse complete entries: - **Title** → Parent
        # The corrupted format shows as: - **Title** �+' Parent
        if in_complete_section and line.startswith('- **'):
            # Match: - **Title** garbage Parent
            match = re.match(r'- \*\*(.+?)\*\*\s+.+?\s+(\S.+)', line)
            if match:
                title = match.group(1)
                parent = match.group(2).strip()
                selections[title] = parent
    
    return selections

def load_notes():
    """Load notes from JSON."""
    return json.loads(Path(JSON_FILE).read_text(encoding='utf-8'))

def get_multi_parent_notes(notes):
    """Get notes with multiple parents."""
    return [n for n in notes if len(n.get('metadata', {}).get('parents', [])) > 1]

def apply_selections(notes, selections):
    """Apply salvaged selections to notes."""
    applied = 0
    not_found = []
    
    for note in notes:
        if note['title'] not in selections:
            continue
        
        selected_parent = selections[note['title']]
        parents = note.get('metadata', {}).get('parents', [])
        
        # Find the matching parent
        matching = [p for p in parents if p['title'] == selected_parent]
        
        if matching:
            note['metadata']['parents'] = matching
            applied += 1
        else:
            # Try fuzzy match - maybe parent name got truncated
            # Just log it for now
            not_found.append((note['title'], selected_parent, [p['title'] for p in parents]))
    
    return notes, applied, not_found

def regenerate_resolution_file(notes):
    """Regenerate file with only remaining multi-parent notes."""
    multi = get_multi_parent_notes(notes)
    
    lines = [
        "# Resolve Multi-Parent Notes",
        "",
        f"**{len(multi)} notes still need a parent selected.**",
        "",
        "For each note below, select **EXACTLY ONE** parent by checking its checkbox.",
        "All unselected parents will be removed.",
        "",
        "---",
        "",
    ]
    
    for note in multi:
        lines.append(f"## {note['title']}")
        lines.append("")
        lines.append("Select ONE parent:")
        lines.append("")
        
        for parent in note.get('metadata', {}).get('parents', []):
            lines.append(f"- [ ] {parent['title']}")
        
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "## Instructions",
        "",
        "1. Check exactly ONE checkbox per note above",
        "2. Save this file",
        "3. Run: python transforms/I2_resolve_multi_parents.py 01457A9BFGHJ",
        "",
        "Repeat until all notes are resolved!",
    ])
    
    Path(RESOLUTION_FILE).write_text('\n'.join(lines), encoding='utf-8')
    return len(multi)

def main():
    print("Extracting selections from corrupted file...")
    selections = extract_selections_from_corrupted_file()
    print(f"  Found {len(selections)} selections in file")
    
    print("\nLoading notes from JSON...")
    data = load_notes()
    notes = data['notes']
    multi_before = len(get_multi_parent_notes(notes))
    print(f"  {multi_before} notes with multiple parents")
    
    print("\nApplying salvaged selections...")
    notes, applied, not_found = apply_selections(notes, selections)
    print(f"  Applied: {applied}")
    
    if not_found:
        print(f"  Could not match {len(not_found)} selections (parent name mismatch):")
        for title, selected, available in not_found[:5]:
            print(f"    - {title}: wanted '{selected}', had {available}")
    
    multi_after = len(get_multi_parent_notes(notes))
    print(f"\nAfter applying selections:")
    print(f"  {multi_after} notes still have multiple parents")
    print(f"  {multi_before - multi_after} notes resolved")
    
    if multi_after > 0:
        print(f"\nRegenerating {RESOLUTION_FILE} with remaining {multi_after} notes...")
        regenerate_resolution_file(notes)
        print(f"  Done! Please edit and select parents for the remaining notes.")
    else:
        print("\nAll notes resolved! Saving...")
        Path('output/01457A9BFGHJI2').mkdir(exist_ok=True)
        Path('output/01457A9BFGHJI2/_notes.json').write_text(
            json.dumps({'notes': notes}, indent=2, default=str),
            encoding='utf-8'
        )
        Path(RESOLUTION_FILE).unlink()
        print("  Saved to output/01457A9BFGHJI2/")

if __name__ == "__main__":
    main()
