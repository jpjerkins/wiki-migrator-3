"""
Step 01: Extract tiddlers from TiddlyWiki 5 (single-file HTML).

TW5 stores tiddlers in the HTML file in one of two ways:
1. As JSON in a <script> tag with id="storeArea" (older format)
2. As <div> elements with class="tiddler" containing <pre> with JSON (common)
3. Or as embedded store area with individual tiddler divs
"""

import json
import re
import html
from pathlib import Path
from typing import List, Dict, Any


def extract_tiddlers_from_html(html_content: str) -> List[Dict[str, Any]]:
    """
    Extract tiddlers from TW5 HTML content.
    
    TW5 single-file format stores tiddlers in a storeArea div,
    where each tiddler is a div with class 'tiddler' containing its data.
    """
    tiddlers = []
    
    # Look for the storeArea - this is where TW5 keeps all tiddlers
    store_match = re.search(r'<div id="storeArea"[^>]*>(.*?)</div>\s*</div>\s*</body>', html_content, re.DOTALL | re.IGNORECASE)
    
    if store_match:
        store_content = store_match.group(1)
        
        # Each tiddler is stored as: <div title="TiddlerTitle" ...><pre>{json}</pre></div>
        # or as: <div title="TiddlerTitle" ... attributes>...</div> with text content
        
        # Method 1: Look for divs with title attribute (these are tiddlers)
        tiddler_pattern = r'<div([^>]+)>(.*?)</div>\s*(?=<div|$)'
        
        for match in re.finditer(tiddler_pattern, store_content, re.DOTALL):
            attrs_str = match.group(1)
            content = match.group(2).strip()
            
            # Parse attributes
            attr_pattern = r'(\w+)="([^"]*)"'
            attrs = dict(re.findall(attr_pattern, attrs_str))
            
            if 'title' not in attrs:
                continue
                
            # Build tiddler dict from attributes
            tiddler = {
                'title': html.unescape(attrs['title']),
                'created': attrs.get('created', ''),
                'modified': attrs.get('modified', ''),
                'modifier': attrs.get('modifier', ''),
                'creator': attrs.get('creator', ''),
                'tags': attrs.get('tags', ''),
                'type': attrs.get('type', 'text/vnd.tiddlywiki'),
            }
            
            # Extract text content - usually in a <pre> block
            pre_match = re.search(r'<pre>(.*?)</pre>', content, re.DOTALL)
            if pre_match:
                text = pre_match.group(1)
                # Unescape HTML entities
                text = html.unescape(text)
                tiddler['text'] = text
            else:
                # Some tiddlers might have text directly
                tiddler['text'] = html.unescape(content)
            
            tiddlers.append(tiddler)
    
    return tiddlers


def extract_tiddlers_alternative(html_content: str) -> List[Dict[str, Any]]:
    """
    Alternative extraction method using JSON storeArea format.
    Some TW5 versions store tiddlers as JSON array in a script tag.
    """
    # Try to find storeArea with JSON array
    pattern = r'<script class="tiddlywiki-tiddler-store" type="application/json">(.*?)</script>'
    match = re.search(pattern, html_content, re.DOTALL)
    
    if match:
        try:
            store_json = match.group(1)
            tiddlers = json.loads(store_json)
            return tiddlers if isinstance(tiddlers, list) else []
        except json.JSONDecodeError:
            pass
    
    return []


def main():
    # Paths
    source_path = Path("data/00_source/wiki.html")
    output_path = Path("data/01_extracted/tiddlers.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read HTML
    print(f"Reading {source_path}...")
    html_content = source_path.read_text(encoding='utf-8')
    
    # Try primary extraction method
    print("Extracting tiddlers...")
    tiddlers = extract_tiddlers_from_html(html_content)
    
    # If no tiddlers found, try alternative method
    if not tiddlers:
        print("Primary method found no tiddlers, trying alternative...")
        tiddlers = extract_tiddlers_alternative(html_content)
    
    # Write output
    output_path.write_text(json.dumps(tiddlers, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f"Extracted {len(tiddlers)} tiddlers to {output_path}")
    
    # Print some stats
    if tiddlers:
        print(f"\nSample tiddlers:")
        for t in tiddlers[:3]:
            print(f"  - {t['title'][:60]}{'...' if len(t['title']) > 60 else ''}")
    
    return len(tiddlers)


if __name__ == "__main__":
    main()
