# Wiki Migrator 3: Architecture and Approach

> **Project Goal:** Migrate a TiddlyWiki (TW5, single-file) to an Obsidian vault of markdown files.
>
> **Core Challenge:** The conversion rules cannot be fully specified in advance due to heavy and varied tag usage. We need an evolutionary, collaborative approach.

---

## Guiding Principles

1. **Evolutionary Development** — We discover and refine transforms together, one step at a time
2. **Human-in-the-Loop** — Pause after each step to review, discuss, and decide on next steps
3. **Reversibility** — Each step is checkpointed in git; we can always step back
4. **Reproducibility** — The final configuration can be replayed on other wikis
5. **Living Documentation** — Each step generates human-readable markdown reports for review

---

## Architecture: Checkpoint Pipeline

The migration follows a **pipeline** architecture where data flows through discrete, reversible stages:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Source     │────→│  Extracted   │────→│ Transformed  │────→│    Final     │
│  TW5.html    │     │   (JSON)     │     │   (JSON)     │     │ Obsidian MD  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                            │                   │
                            ↓                   ↓
                   ┌─────────────────┐  ┌─────────────────┐
                   │ 01_extraction   │  │ 02_tag_analysis │
                   │    _summary.md  │  │      .md        │
                   └─────────────────┘  └─────────────────┘
```

### Directory Structure

```
wiki-migrator-3/
├── data/
│   ├── 00_source/           # TiddlyWiki.html (gitignored)
│   ├── 01_extracted/        # Step 1: Raw JSON extraction
│   ├── 02_transformed/      # Step N: After each transform
│   └── 99_final/            # Ready-to-import Obsidian vault
├── transforms/
│   ├── __init__.py
│   ├── 01_extract.py        # TW5 → JSON
│   ├── 02_analyze.py        # Tag/structure analysis
│   └── ...                  # Added incrementally
├── docs/
│   ├── Architecture and Approach.md   # This file
│   └── migration_log/       # Generated reports at each step
│       ├── 01_extraction_summary.md
│       ├── 02_tag_analysis.md
│       └── ...
├── render_docs.py           # Generates markdown visualizations
└── migrate.py               # Orchestrates the pipeline
```

---

## The "Review Render" Workflow

Each step produces **three artifacts**:

| Artifact | Location | Purpose |
|----------|----------|---------|
| **Data** | `data/XX_name/` | Machine-readable intermediate state |
| **Documentation** | `docs/migration_log/XX_name.md` | Human-readable summary and samples |
| **Git Commit** | Git history | Reversible checkpoint with context |

### Cycle per Step

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Write/Edit │───→│  Run Step    │───→│   Review    │───→│   Decide     │
│  Transform  │    │  (extract/   │    │  Rendered   │    │   Next Step  │
│             │    │  transform)  │    │    Docs     │    │              │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                                          │
                          ┌────────────────────────────────┘
                          ↓
                   ┌──────────────┐
                   │ Git Commit   │
                   │ "step XX:    │
                   │ description" │
                   └──────────────┘
```

1. **Write/Edit** — I write or modify a transform script
2. **Run** — Execute the step, generating JSON and markdown
3. **Review** — You read `docs/migration_log/XX_*.md` to understand results
4. **Decide** — We discuss edge cases, patterns, and next steps
5. **Commit** — Checkpoint with descriptive message

---

## Git Strategy: One Commit Per Step

Each commit represents a complete, reviewable unit of work.

### Commit Message Format

```
step XX: brief description of what was done

- Key statistics (e.g., "1,203 tiddlers extracted")
- Key findings (e.g., "47 broken links flagged")
- Decisions made (e.g., "Using [[target|display]] for wiki links")
- Open questions for next step
```

### Example Commit History

```
step 04: convert wiki links to obsidian format
step 03: analyze tag taxonomy and hierarchies  
step 02: identify tiddler types by tag patterns
step 01: extract 1,247 tiddlers from TW5
```

This creates a **reversible narrative** — we can `git checkout` to any point and replay from there with different decisions.

---

## Handling Tag Complexity

Since the wiki uses tags heavily for structure, we'll discover the taxonomy before converting:

### Phase 1: Discovery (Steps 01-03)

1. **Extraction** — Get raw tiddler data
2. **Tag Inventory** — What tags exist? Frequencies?
3. **Pattern Analysis** — Hierarchical tags (`Project/Active`)? MOC markers? System tags?

### Phase 2: Structure Mapping (Steps 04-06)

4. **Folder Strategy** — Which tags imply folder placement?
5. **MOC Generation** — Which tags become Map of Contents?
6. **Frontmatter Design** — Which metadata becomes YAML frontmatter?

### Phase 3: Content Conversion (Steps 07+)

7. **Link Conversion** — WikiLinks → Obsidian format
8. **Transclusion Handling** — `{{tiddler}}` → `![[tiddler]]`
9. **Custom Macros** — Any `<<macros>>` needing special handling
10. **HTML Cleanup** — TiddlyWiki widgets → Markdown equivalents

---

## The Render System

`render_docs.py` generates human-readable reports from intermediate JSON data.

### Report Contents

Each `docs/migration_log/XX_*.md` includes:

- **Summary Statistics** — Counts, distributions, coverage
- **Representative Samples** — Before/after for key tiddlers
- **Edge Case Spotlights** — Unusual patterns needing attention
- **Decision Points** — Explicit questions for your input
- **Next Step Recommendations** — Proposed transforms based on findings

### Example Report Structure

```markdown
# Step 02: Tag Analysis

## Overview
- Total tiddlers: 1,247
- Unique tags: 89
- Tiddlers with no tags: 23

## Top Tags
| Tag | Count | Notes |
|-----|-------|-------|
| Journal | 342 | Date-based entries |
| Project/Active | 28 | Hierarchical tag |
| MOC-Philosophy | 3 | MOC marker pattern |

## Tag Co-occurrence
- `Project/Active` + `Area/Work` → 24 tiddlers (strong correlation)
- `Person` + `MOC-Network` → 15 tiddlers (biographical MOCs?)

## Open Questions
1. Should `Project/*` tags become folders or stay as tags?
2. Are `MOC-*` tags intentional MOC markers?

## Recommended Next Step
Analyze tiddler types by tag combination to inform folder structure.
```

---

## Obsidian Output Considerations

### Folder Structure (TBD)

Candidate approaches:

| Approach | Pros | Cons |
|----------|------|------|
| **PARA** (`Projects/`, `Areas/`, `Resources/`, `Archive/`) | Matches PARA system | May not map cleanly to tag taxonomy |
| **Tag-Derived Folders** | Preserves wiki organization | May create too many folders |
| **Hybrid** (PARA base + tag MOCs) | Best of both | More complex to configure |
| **Flat + Heavy Frontmatter** | Simple structure | Loses folder-based navigation |

### Plugins to Support

- **Breadcrumbs** — For hierarchical navigation
- **Folder Notes** — For MOC-per-folder
- **Dataview** — For querying frontmatter
- **Templater** — For consistent note structure

These considerations will be decided during Phase 2 (Structure Mapping).

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- A TW5 single-file wiki to migrate

### First Steps

1. Place your `wiki.html` in `data/00_source/`
2. Run Step 01 (extraction) → review `docs/migration_log/01_extraction_summary.md`
3. Discuss findings → proceed to Step 02

---

## Evolution of This Document

This architecture is a starting hypothesis. As we discover the actual structure and complexity of your wiki, we may:

- Add new phases to the pipeline
- Modify the render system for better visualization
- Adjust git commit granularity
- Evolve the documentation format

Changes to the approach will be documented here with dated revision notes.
