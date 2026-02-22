"""
E_convert_high_priority.py - Convert high priority TiddlyWiki markup to Markdown.

Handles:
- Block quotes: <<<...>>> or <<quoted text>> → > blockquote
- Inline code: `code` → `code` (same, but ensure proper escaping)
- Code blocks: {{{ code }}} → ```code```
- Strikethrough: ~~text~~ → ~~text~~ (same syntax)
- Horizontal rules: --- or ---- → ---
- Images: [img[filename]] or [img[filename|tooltip]] → ![tooltip](filename)

Usage:
    python transforms/E_convert_high_priority.py <input_folder>
    
Example:
    python transforms/E_convert_high_priority.py 01457A9BCD
    # Creates output folder: 01457A9BCDE
"""

import re
import sys
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, load_json, save_output, validate_notes

SCRIPT_ID = "E"
SCRIPT_NAME = "convert_high_priority"


def convert_blockquotes(text: str) -> str:
    """
    Convert TiddlyWiki blockquotes to Markdown.
    
    TiddlyWiki:
    <<<.author
    Quoted text
    <<<
    
    or <<quoted text>>
    
    Markdown:
    > Quoted text
    > — author
    """
    # Handle multi-line blockquotes: <<<.author\ntext\n<<<
    def replace_multiline_blockquote(match):
        content = match.group(1).strip()
        lines = content.split("\n")
        
        # Check for author prefix (lines starting with .)
        author = None
        if lines and lines[0].startswith("."):
            author = lines[0][1:].strip()
            lines = lines[1:]
        
        # Quote all lines
        quoted = "\n".join("> " + line for line in lines if line.strip())
        
        if author:
            quoted += f"\n> — {author}"
        
        return quoted
    
    # Multi-line blockquotes
    text = re.sub(
        r"<<<\s*\n?(.*?)\s*<<<",
        replace_multiline_blockquote,
        text,
        flags=re.DOTALL
    )
    
    # Inline blockquotes: <<quoted text>>
    text = re.sub(
        r"<<([^<\n]{10,}?)>>",
        r"> \1",
        text
    )
    
    return text


def convert_code_blocks(text: str) -> str:
    """
    Convert TiddlyWiki code blocks to Markdown.
    
    TiddlyWiki inline: `code` (same as Markdown)
    TiddlyWiki block: {{{ code }}} or {{{\ncode\n}}}
    
    Markdown block: ```\ncode\n```
    """
    # Handle block code: {{{\ncode\n}}}
    def replace_code_block(match):
        code = match.group(1)
        # Remove leading/trailing newlines but preserve internal formatting
        code = code.strip("\n")
        return f"```\n{code}\n```"
    
    text = re.sub(
        r"\{\{\{\s*\n(.*?)\n\s*\}\}\}",
        replace_code_block,
        text,
        flags=re.DOTALL
    )
    
    # Handle inline code blocks on single line: {{{code}}}
    text = re.sub(
        r"\{\{\{([^\n]*?)\}\}\}",
        r"`\1`",
        text
    )
    
    return text


def convert_strikethrough(text: str) -> str:
    """
    Convert TiddlyWiki strikethrough to Markdown.
    
    TiddlyWiki: ~~text~~
    Markdown: ~~text~~ (same syntax!)
    
    Note: We just need to ensure it's properly formatted.
    """
    # TiddlyWiki and Markdown use same syntax, but let's ensure consistency
    # Handle any spacing issues
    text = re.sub(
        r"~~\s*([^~]+?)\s*~~",
        r"~~\1~~",
        text
    )
    return text


def convert_horizontal_rules(text: str) -> str:
    """
    Convert TiddlyWiki horizontal rules to Markdown.
    
    TiddlyWiki: ---- or ---
    Markdown: ---
    """
    # Convert 4+ dashes on their own line to ---
    text = re.sub(
        r"^\s*----\s*$",
        "---",
        text,
        flags=re.MULTILINE
    )
    return text


def convert_images(text: str) -> str:
    """
    Convert TiddlyWiki images to Markdown.
    
    TiddlyWiki:
    - [img[filename.png]]
    - [img[filename.png|tooltip text]]
    - [img[filename.png|tooltip|link]] (with link)
    
    Markdown:
    - ![alt](filename.png "tooltip")
    - [![alt](filename.png)](link) (with link)
    """
    def replace_image(match):
        content = match.group(1)
        parts = content.split("|")
        
        filename = parts[0].strip()
        tooltip = parts[1].strip() if len(parts) > 1 else ""
        link = parts[2].strip() if len(parts) > 2 else ""
        
        # Use filename (without extension) as alt text
        alt = Path(filename).stem
        
        if link:
            # Linked image: [![alt](image)](link)
            return f"[![{alt}]({filename})]({link})"
        elif tooltip:
            # Image with tooltip: ![alt](image "tooltip")
            return f"![{alt}]({filename} \"{tooltip}\")"
        else:
            # Simple image: ![alt](image)
            return f"![{alt}]({filename})"
    
    text = re.sub(
        r"\[img\[(.*?)\]\]",
        replace_image,
        text
    )
    
    return text


def convert_high_priority(text: str) -> str:
    """Apply all high priority conversions."""
    # Order matters - do code blocks first to avoid conflicts
    text = convert_code_blocks(text)
    text = convert_blockquotes(text)
    text = convert_images(text)
    text = convert_horizontal_rules(text)
    text = convert_strikethrough(text)
    
    return text


def transform(notes: list[Note]) -> list[Note]:
    """
    Convert high priority TiddlyWiki markup to Markdown for all notes.
    
    Args:
        notes: List of notes from the previous step
        
    Returns:
        Notes with converted content
    """
    converted_count = 0
    
    for note in notes:
        original_content = note.content
        note.content = convert_high_priority(original_content)
        
        if note.content != original_content:
            converted_count += 1
    
    print(f"  Notes with converted high priority markup: {converted_count}")
    
    return notes


def main() -> None:
    """Main entry point for the transform script."""
    if len(sys.argv) != 2:
        print(f"Usage: python {SCRIPT_ID}_{SCRIPT_NAME}.py <input_folder>")
        print(f"Example: python {SCRIPT_ID}_{SCRIPT_NAME}.py 01457A9BCD")
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
    
    print("\nConverting high priority TiddlyWiki markup to Markdown...")
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
    print(f"  2. Check markdown files for converted high priority markup")
    print(f"  3. Create the next transform script")


if __name__ == "__main__":
    main()
