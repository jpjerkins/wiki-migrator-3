"""
G_convert_tables.py - Convert TiddlyWiki tables to Markdown tables (UPDATED).

Converts TiddlyWiki table syntax to Markdown tables:
- Headers: |!Cell| → | Cell |
- Data rows: |Cell| → | Cell |
- Alignment: Preserved by padding (Markdown uses :--- for alignment)
- Cell merging (~, <, >): Handled by leaving empty cells
- Special rows (CSS, caption, header, footer markers): Stripped

UPDATED: Ignores notes where type field is "text/markdown" (already markdown).

Usage:
    python transforms/G_convert_tables.py <input_folder>
    
Example:
    python transforms/G_convert_tables.py 01457A9BF
    # Creates output folder: 01457A9BFG
"""

import re
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "G"
SCRIPT_NAME = "convert_tables"


def parse_tw_table(table_lines: list[str]) -> list[list[str]]:
    """
    Parse TiddlyWiki table lines into a 2D array of cells.
    
    Returns list of rows, where each row is a list of cell contents.
    """
    rows = []
    
    for line in table_lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        
        # Split by | and remove empty first/last elements
        cells = [c.strip() for c in line.split("|")[1:-1]]
        
        # Skip special marker rows (CSS classes, caption, header/footer markers)
        if cells and cells[-1] in ('k', 'c', 'h', 'f'):
            continue
        
        rows.append(cells)
    
    return rows


def is_header_row(row: list[str]) -> bool:
    """Check if a row is a header row (cells start with !)."""
    return all(cell.startswith("!") or cell == "" for cell in row if cell)


def clean_cell(cell: str) -> str:
    """
    Clean a cell's content for Markdown:
    - Remove header marker !
    - Remove vertical alignment markers ^ and ,
    - Handle merge markers (~, <, >) by returning empty string
    """
    cell = cell.strip()
    
    # Handle merge markers
    if cell in ('~', '<', '>'):
        return ""
    
    # Remove header marker
    if cell.startswith("!"):
        cell = cell[1:]
    
    # Remove vertical alignment markers
    if cell.startswith("^") or cell.startswith(","):
        cell = cell[1:]
    
    return cell.strip()


def get_alignment_format(cell: str) -> str:
    """
    Determine Markdown alignment format based on content padding.
    
    - Left aligned (content ends with space): :---
    - Right aligned (content starts with space): ---:
    - Center aligned (both): :---:
    - Default: ---
    """
    if not cell:
        return "---"
    
    left_space = cell.startswith(" ")
    right_space = cell.endswith(" ")
    
    if left_space and right_space:
        return ":---:"
    elif left_space:
        return "---:"
    elif right_space:
        return ":---"
    else:
        return "---"


def convert_to_markdown_table(rows: list[list[str]]) -> str:
    """Convert parsed rows to Markdown table format."""
    if not rows:
        return ""
    
    # Find max number of columns
    max_cols = max(len(row) for row in rows)
    
    # Normalize all rows to have same number of columns
    normalized_rows = []
    for row in rows:
        while len(row) < max_cols:
            row.append("")
        normalized_rows.append(row[:max_cols])
    
    # Find header row (first row with header markers, or first row)
    header_idx = 0
    for i, row in enumerate(normalized_rows):
        if is_header_row(row):
            header_idx = i
            break
    
    # Clean all cells
    cleaned_rows = []
    for row in normalized_rows:
        cleaned = [clean_cell(cell) for cell in row]
        cleaned_rows.append(cleaned)
    
    # Build Markdown table
    md_lines = []
    
    for i, row in enumerate(cleaned_rows):
        # Build row line
        md_line = "| " + " | ".join(row) + " |"
        md_lines.append(md_line)
        
        # Add separator after header
        if i == header_idx:
            # Check alignment from original row
            original_row = normalized_rows[i]
            alignments = [get_alignment_format(cell) for cell in original_row]
            sep_line = "|" + "|".join(alignments) + "|"
            md_lines.append(sep_line)
    
    return "\n".join(md_lines)


def convert_tables_in_text(text: str) -> str:
    """Find and convert all TiddlyWiki tables in text to Markdown."""
    lines = text.split("\n")
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is the start of a table (starts with |)
        if line.strip().startswith("|"):
            # Collect all consecutive table lines
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            
            # Parse and convert
            rows = parse_tw_table(table_lines)
            if rows:
                md_table = convert_to_markdown_table(rows)
                if md_table:
                    result.append(md_table)
            else:
                # Not a valid table, keep original lines
                result.extend(table_lines)
        else:
            result.append(line)
            i += 1
    
    return "\n".join(result)


def is_already_markdown(note: Note) -> bool:
    """
    Check if note is already in markdown format.
    
    Returns True if note's type field is "text/markdown".
    """
    return note.metadata.get("type") == "text/markdown"


def transform(notes: list[Note]) -> list[Note]:
    """
    Convert TiddlyWiki tables to Markdown for all notes.
    
    Skips notes that are already markdown (type field = "text/markdown").
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with converted tables
    """
    converted_count = 0
    skipped_count = 0
    
    for note in notes:
        # Skip notes that are already markdown
        if is_already_markdown(note):
            skipped_count += 1
            continue
        
        original_content = note.content
        note.content = convert_tables_in_text(original_content)
        
        if note.content != original_content:
            converted_count += 1
    
    print(f"  Notes with converted tables: {converted_count}")
    print(f"  Notes skipped (already markdown): {skipped_count}")
    
    return notes


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BF")
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
    
    print("\nConverting TiddlyWiki tables to Markdown...")
    print("  (Skipping notes with type='text/markdown')")
    notes = transform(notes)
    
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
    print(f"  2. Check markdown files for converted tables")
    print(f"  3. Create the next transform script")


if __name__ == "__main__":
    main()
