"""
C_wikitext_to_markdown.py - Convert TiddlyWiki wikitext to Markdown.

Converts common TiddlyWiki markup to Markdown:
- Bold: ''text'' → **text**
- Italics: //text// → *text*
- Internal links: [[Link|Text]] → [[Text|Link]] (Obsidian format)
- External links: [[URL|Text]] → [Text](URL)
- Bullet lists: * Item → - Item
- Numbered lists: # Item → 1. Item
- Headings: ! Heading → # Heading

Usage:
    python transforms/C_wikitext_to_markdown.py <input_folder>
    
Example:
    python transforms/C_wikitext_to_markdown.py 01457A9B
    # Creates output folder: 01457A9BC
"""

import re
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "C"
SCRIPT_NAME = "wikitext_to_markdown"


def convert_bold(text: str) -> str:
    """Convert TiddlyWiki bold ''text'' to Markdown **text**."""
    # Handle bold: ''text'' → **text**
    # Need to avoid matching single quotes in contractions
    return re.sub(r"''([^']+?)''", r"**\1**", text)


def convert_italics(text: str) -> str:
    """Convert TiddlyWiki italics //text// to Markdown *text*."""
    return re.sub(r"//(.+?)//", r"*\1*", text)


def convert_headings(text: str) -> str:
    """Convert TiddlyWiki headings !Heading to Markdown # Heading."""
    lines = text.split("\n")
    result = []
    
    for line in lines:
        # Match headings: ! Heading, !! Heading, !!! Heading, etc.
        match = re.match(r"^(!{1,6})\s*(.+)$", line)
        if match:
            level = len(match.group(1))
            heading_text = match.group(2)
            result.append(f"{'#' * level} {heading_text}")
        else:
            result.append(line)
    
    return "\n".join(result)


def convert_internal_links(text: str) -> str:
    """
    Convert TiddlyWiki internal links to Obsidian format.
    
    TiddlyWiki: [[Title]] or [[Title|Display Text]]
    Obsidian: [[Title]] or [[Display Text|Title]]
    """
    def replace_link(match):
        content = match.group(1)
        if "|" in content:
            # [[Title|Display]] → [[Display|Title]]
            parts = content.split("|", 1)
            title = parts[0].strip()
            display = parts[1].strip()
            return f"[[{display}|{title}]]"
        else:
            # [[Title]] stays [[Title]]
            return f"[[{content}]]"
    
    # Match [[...]] but not preceded by http (external links handled separately)
    return re.sub(r"(?<![\[])\[\[([^\]]+)\]\](?![\]])", replace_link, text)


def convert_external_links(text: str) -> str:
    """
    Convert TiddlyWiki external links to Markdown format.
    
    TiddlyWiki: [[URL|Display Text]] or [ext[URL|Display Text]]
    Markdown: [Display Text](URL)
    """
    # Handle [ext[URL]] format
    text = re.sub(r"\[ext\[(https?://[^\]|]+)\|([^\]]+)\]\]", r"[\2](\1)", text)
    text = re.sub(r"\[ext\[(https?://[^\]]+)\]\]", r"[\1](\1)", text)
    
    # Handle [[URL|Text]] where URL starts with http
    def replace_external(match):
        content = match.group(1)
        if "|" in content:
            parts = content.split("|", 1)
            url = parts[0].strip()
            display = parts[1].strip()
            if url.startswith(("http://", "https://")):
                return f"[{display}]({url})"
        return f"[[{content}]]"
    
    return re.sub(r"\[\[(https?://[^\]]+)\]\]", replace_external, text)


def convert_lists(text: str) -> str:
    """
    Convert TiddlyWiki lists to Markdown lists.
    
    TiddlyWiki: * Item (bullet), # Item (numbered)
    Markdown: - Item, 1. Item
    """
    lines = text.split("\n")
    result = []
    
    for line in lines:
        # Convert bullet lists: * Item → - Item
        if re.match(r"^\*\s+", line):
            line = re.sub(r"^(\*+)\s+", lambda m: "  " * (len(m.group(1)) - 1) + "- ", line)
        # Convert numbered lists: # Item → 1. Item
        elif re.match(r"^#\s+", line):
            line = re.sub(r"^(#+)\s+", lambda m: "  " * (len(m.group(1)) - 1) + "1. ", line)
        
        result.append(line)
    
    return "\n".join(result)


def convert_note_content(content: str) -> str:
    """Apply all wikitext to markdown conversions."""
    # Order matters - do headings first to avoid conflicts
    content = convert_headings(content)
    content = convert_lists(content)
    content = convert_external_links(content)
    content = convert_internal_links(content)
    content = convert_bold(content)
    content = convert_italics(content)
    
    return content


def transform(notes: list[Note]) -> list[Note]:
    """
    Convert TiddlyWiki wikitext to Markdown for all notes.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with converted Markdown content
    """
    converted_count = 0
    
    for note in notes:
        original_content = note.content
        note.content = convert_note_content(original_content)
        
        if note.content != original_content:
            converted_count += 1
    
    print(f"  Notes with converted content: {converted_count}")
    
    return notes


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9B")
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
    
    print("\nConverting TiddlyWiki wikitext to Markdown...")
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
    print(f"  2. Check markdown files for converted wikitext")
    print(f"  3. Create the next transform script")


if __name__ == "__main__":
    main()
