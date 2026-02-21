"""
Render intermediate data into human-readable markdown documentation.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter


def render_step_01_extraction_summary():
    """Generate documentation for Step 01: Extraction"""
    
    # Load extracted tiddlers
    tiddlers_path = Path("data/01_extracted/tiddlers.json")
    tiddlers = json.loads(tiddlers_path.read_text(encoding='utf-8'))
    
    # Calculate statistics
    total = len(tiddlers)
    
    # Field coverage
    fields = ['created', 'modified', 'tags', 'type', 'text', 'modifier', 'creator']
    field_coverage = {}
    for field in fields:
        count = sum(1 for t in tiddlers if t.get(field))
        field_coverage[field] = (count, count / total * 100)
    
    # Content types
    type_counter = Counter(t.get('type', 'text/vnd.tiddlywiki') for t in tiddlers)
    
    # Tag statistics
    all_tags = []
    for t in tiddlers:
        tags_str = t.get('tags', '')
        if tags_str:
            # Tags in TW5 are space-separated, but can be quoted
            # Simple split for now
            tags = tags_str.split()
            all_tags.extend(tags)
    
    tag_counter = Counter(all_tags)
    
    # Title statistics
    title_lengths = [len(t['title']) for t in tiddlers]
    avg_title_len = sum(title_lengths) / len(title_lengths) if title_lengths else 0
    max_title_len = max(title_lengths) if title_lengths else 0
    
    # Text size statistics
    text_sizes = [len(t.get('text', '')) for t in tiddlers]
    avg_text_size = sum(text_sizes) / len(text_sizes) if text_sizes else 0
    max_text_size = max(text_sizes) if text_sizes else 0
    
    # Sample tiddlers (first 10)
    samples = tiddlers[:10]
    
    # Generate markdown
    lines = [
        "# Step 01: Extraction Summary",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Source:** `data/00_source/wiki.html`",
        "",
        "## Overview",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Tiddlers | {total:,} |",
        f"| Tiddlers with Tags | {field_coverage['tags'][0]:,} ({field_coverage['tags'][1]:.1f}%) |",
        f"| Tiddlers with Text | {field_coverage['text'][0]:,} ({field_coverage['text'][1]:.1f}%) |",
        f"| Avg Title Length | {avg_title_len:.1f} chars |",
        f"| Max Title Length | {max_title_len} chars |",
        f"| Avg Text Size | {avg_text_size:,.0f} chars |",
        f"| Max Text Size | {max_text_size:,} chars |",
        "",
        "## Field Coverage",
        "",
        "| Field | Present | Coverage |",
        "|-------|---------|----------|",
    ]
    
    for field, (count, pct) in field_coverage.items():
        lines.append(f"| {field} | {count:,} | {pct:.1f}% |")
    
    lines.extend([
        "",
        "## Content Types",
        "",
        "| Type | Count | Percentage |",
        "|------|-------|------------|",
    ])
    
    for content_type, count in type_counter.most_common(10):
        pct = count / total * 100
        display_type = content_type[:50] + '...' if len(content_type) > 50 else content_type
        lines.append(f"| {display_type} | {count:,} | {pct:.1f}% |")
    
    if len(type_counter) > 10:
        lines.append(f"| ... and {len(type_counter) - 10} more | | |")
    
    lines.extend([
        "",
        "## Top 30 Tags",
        "",
        "| Tag | Count |",
        "|-----|-------|",
    ])
    
    for tag, count in tag_counter.most_common(30):
        # Clean up tag for display (unescape HTML entities)
        display_tag = tag.replace('&quot;', '"').replace('&apos;', "'")
        display_tag = display_tag[:60] + '...' if len(display_tag) > 60 else display_tag
        lines.append(f"| {display_tag} | {count:,} |")
    
    lines.extend([
        "",
        f"**Total unique tags:** {len(tag_counter)}",
        "",
        "## Sample Tiddlers",
        "",
        "| # | Title | Type | Has Tags | Text Length |",
        "|---|-------|------|----------|-------------|",
    ])
    
    for i, t in enumerate(samples, 1):
        title = t['title'][:50] + '...' if len(t['title']) > 50 else t['title']
        title = title.replace('|', '\\|')  # Escape pipe in markdown
        has_tags = '✓' if t.get('tags') else '✗'
        text_len = len(t.get('text', ''))
        content_type = t.get('type', 'text/vnd.tiddlywiki').split('/')[-1][:20]
        lines.append(f"| {i} | {title} | {content_type} | {has_tags} | {text_len:,} |")
    
    lines.extend([
        "",
        "## Representative Full Examples",
        "",
    ])
    
    # Show 3 complete examples of different types
    example_indices = [0, min(10, total//10), min(100, total//3)]
    for idx in example_indices:
        if idx < len(tiddlers):
            t = tiddlers[idx]
            title = t['title']
            lines.extend([
                f"### Example: `{title}`",
                "",
                "```json",
                json.dumps(t, indent=2, ensure_ascii=False)[:2000],
                "```",
                "",
            ])
    
    lines.extend([
        "",
        "## Observations & Questions",
        "",
        "### Immediate Observations",
        f"- Total of **{len(tag_counter)} unique tags** suggests heavy tag usage as expected",
        f"- **{field_coverage['tags'][0]:,} tiddlers ({field_coverage['tags'][1]:.1f}%)** have tags — this is the primary organization mechanism",
        "",
        "### Open Questions for Next Step",
        "",
        "1. **Tag Structure**: Are there hierarchical patterns like `Project/Active`?",
        "2. **System Tags**: Which tags are TW5 system tags vs. content tags?",
        "3. **MOCs**: Are there tags or titles indicating Map of Contents?",
        "4. **Journal Tiddlers**: Are there date-based tiddlers with `Journal` or date tags?",
        "5. **Special Types**: The non-default content types may need special handling",
        "",
        "## Recommended Next Step",
        "",
        "**Step 02: Tag Analysis** — Deep dive into the tag taxonomy to understand:",
        "- Hierarchical patterns",
        "- System vs. content tags",
        "- Tag co-occurrence (which tags appear together)",
        "- Structural tags that might drive folder organization",
    ])
    
    # Write output
    output_path = Path("docs/migration_log/01_extraction_summary.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    
    print(f"Rendered documentation to {output_path}")
    return total, len(tag_counter)


if __name__ == "__main__":
    render_step_01_extraction_summary()
