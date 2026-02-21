"""
0_extract.py - Extract notes from TiddlyWiki.

This is the starting point of the migration pipeline.
It extracts all tiddlers from a TiddlyWiki HTML file and creates the initial output folder '0'.

Usage:
    python transforms/0_extract.py [path/to/tiddlywiki.html]

If no path is provided, defaults to C:/Users/PhilJ/Dropbox/phil-home.html
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for importing lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, Task, Attachment, save_output, validate_notes

SCRIPT_ID = "0"
SCRIPT_NAME = "extract"
DEFAULT_SOURCE = "C:/Users/PhilJ/Dropbox/phil-home.html"


def parse_tiddler_date(date_str: str | None) -> datetime:
    """
    Parse a TiddlyWiki date string to datetime.
    
    TiddlyWiki dates are in format: YYYYMMDDHHMMSSmmm (e.g., 20240101120000000)
    """
    if not date_str or len(date_str) < 14:
        return datetime.now()
    
    try:
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(date_str[8:10])
        minute = int(date_str[10:12])
        second = int(date_str[12:14])
        return datetime(year, month, day, hour, minute, second)
    except (ValueError, IndexError):
        return datetime.now()


def extract_tiddlers(html_content: str) -> list[dict]:
    """
    Extract tiddlers from TiddlyWiki HTML content.
    
    TiddlyWiki stores tiddlers as JSON in script tags with class "tiddlywiki-tiddler-store".
    """
    tiddlers = []
    
    # Find the store area (TiddlyWiki 5.x format)
    store_match = re.search(
        r'<script class="tiddlywiki-tiddler-store" type="application/json">(.*?)</script>',
        html_content,
        re.DOTALL | re.IGNORECASE
    )
    
    if store_match:
        # TiddlyWiki 5.x format
        store_json = store_match.group(1)
        try:
            store_data = json.loads(store_json)
            tiddlers = store_data if isinstance(store_data, list) else store_data.get("tiddlers", [])
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse tiddler store JSON: {e}")
    else:
        # Try TiddlyWiki classic format or alternative locations
        # Look for tiddlers in the storeArea div
        store_area_match = re.search(
            r'<div id="storeArea"[^>]*>(.*?)</div>\s*</body>',
            html_content,
            re.DOTALL | re.IGNORECASE
        )
        if store_area_match:
            store_area = store_area_match.group(1)
            # Extract individual tiddler divs
            tiddler_matches = re.finditer(
                r'<div tiddler="([^"]*)"[^>]*>(.*?)</div>',
                store_area,
                re.DOTALL
            )
            for match in tiddler_matches:
                title = match.group(1)
                content = match.group(2)
                tiddlers.append({
                    "title": title,
                    "text": content,
                    "created": None,
                    "modified": None,
                    "tags": [],
                })
    
    return tiddlers


def parse_tiddlywiki_tags(tags_str: str | list) -> list[str]:
    """
    Parse TiddlyWiki tags, handling space-separated and [[multi-word tags]].
    
    TiddlyWiki formats:
    - Simple tags: space-separated (tag1 tag2 tag3)
    - Multi-word tags: wrapped in [[...]] ([[multi word tag]] simpletag)
    """
    if isinstance(tags_str, list):
        return tags_str
    
    if not isinstance(tags_str, str) or not tags_str.strip():
        return []
    
    tags = []
    remaining = tags_str.strip()
    
    while remaining:
        remaining = remaining.strip()
        if not remaining:
            break
        
        if remaining.startswith("[["):
            # Multi-word tag: find closing ]]
            end = remaining.find("]]")
            if end == -1:
                # Malformed - take rest as tag
                tags.append(remaining[2:])
                break
            tag = remaining[2:end]
            tags.append(tag)
            remaining = remaining[end + 2:]
        else:
            # Simple tag: find next space or end
            space = remaining.find(" ")
            if space == -1:
                tags.append(remaining)
                break
            tag = remaining[:space]
            if tag:
                tags.append(tag)
            remaining = remaining[space + 1:]
    
    return tags


def tiddler_to_note(tiddler: dict) -> Note:
    """
    Convert a TiddlyWiki tiddler to our Note model.
    """
    title = tiddler.get("title", "Untitled")
    
    # Parse tags - handle both simple and [[multi-word]] formats
    tags = []
    if "tags" in tiddler:
        tags = parse_tiddlywiki_tags(tiddler["tags"])
    
    # Build metadata from tiddler fields
    metadata = {}
    reserved_fields = {"title", "text", "tags", "created", "modified", "type"}
    for key, value in tiddler.items():
        if key not in reserved_fields and not key.startswith("_"):
            metadata[key] = value
    
    # Determine file path
    safe_title = sanitize_title_for_path(title)
    path = f"{safe_title}.md"
    
    return Note(
        id=tiddler.get("title", ""),  # Use tiddler title as ID
        title=title,
        content=tiddler.get("text", ""),
        path=path,
        created=parse_tiddler_date(tiddler.get("created")),
        modified=parse_tiddler_date(tiddler.get("modified")),
        tags=tags,
        tasks=[],  # Tasks will be extracted in later transforms
        attachments=[],  # Attachments handled separately
        metadata=metadata,
    )


def sanitize_title_for_path(title: str) -> str:
    """
    Sanitize a tiddler title for use as a file path.
    
    Removes characters that are problematic in file systems.
    """
    # Replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    safe = re.sub(invalid_chars, "_", title)
    # Remove leading/trailing periods and spaces
    safe = safe.strip(". ")
    # Limit length
    if len(safe) > 100:
        safe = safe[:100].strip(". ")
    return safe if safe else "untitled"


def extract_from_source(source_path: Path) -> list[Note]:
    """
    Extract notes from a TiddlyWiki HTML file.
    
    Args:
        source_path: Path to the TiddlyWiki HTML file
        
    Returns:
        List of Note objects
    """
    print(f"Reading TiddlyWiki: {source_path}")
    
    if not source_path.exists():
        raise FileNotFoundError(f"TiddlyWiki file not found: {source_path}")
    
    html_content = source_path.read_text(encoding="utf-8")
    
    print("Extracting tiddlers...")
    tiddlers = extract_tiddlers(html_content)
    print(f"Found {len(tiddlers)} tiddlers")
    
    # Filter out system tiddlers (unless needed)
    system_tiddlers = [t for t in tiddlers if t.get("title", "").startswith("$:/")]
    user_tiddlers = [t for t in tiddlers if not t.get("title", "").startswith("$:/")]
    
    print(f"  User tiddlers: {len(user_tiddlers)}")
    print(f"  System tiddlers (excluded): {len(system_tiddlers)}")
    
    # Convert to notes
    notes = [tiddler_to_note(t) for t in user_tiddlers]
    
    # Sort by title for consistent output
    notes.sort(key=lambda n: n.title.lower())
    
    return notes


def main() -> None:
    """Main entry point for the extract script."""
    # Get source path from command line or use default
    if len(sys.argv) >= 2:
        source_path = Path(sys.argv[1])
    else:
        source_path = Path(DEFAULT_SOURCE)
    
    output_folder_name = SCRIPT_ID
    output_folder = Path("output") / output_folder_name
    
    if output_folder.exists():
        print(f"Warning: Output folder already exists: {output_folder}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(0)
    
    try:
        notes = extract_from_source(source_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"\nUsage: python {SCRIPT_ID}_{SCRIPT_NAME}.py [path/to/tiddlywiki.html]")
        print(f"Default: {DEFAULT_SOURCE}")
        sys.exit(1)
    except Exception as e:
        print(f"Error extracting from TiddlyWiki: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    if not notes:
        print("No notes extracted. Check that the TiddlyWiki file contains tiddlers.")
        sys.exit(1)
    
    # Validate before saving
    errors = validate_notes(notes)
    if errors:
        print("Validation errors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != "y":
            sys.exit(1)
    
    print(f"\nSaving to: {output_folder}")
    save_output(output_folder, notes)
    
    print(f"\nDone! Created output folder: {output_folder_name}")
    print(f"  - notes.json: {output_folder / 'notes.json'}")
    print(f"  - Markdown files: {len(list(output_folder.glob('**/*.md')))}")
    print(f"\nNext steps:")
    print(f"  1. Review the output in: {output_folder}")
    print(f"  2. Open as an Obsidian vault to inspect the markdown files")
    print(f"  3. Create transform script '1' to continue migration")


if __name__ == "__main__":
    main()
