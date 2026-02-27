#!/usr/bin/env python3
"""
run_migration_1.py - TiddlyWiki to Obsidian migration pipeline (Part 1).

Runs transforms from extraction through the first interactive multi-parent resolution.
Ends with transform J, which requires user interaction to resolve multi-parent notes.

After this completes, manually resolve any multi-parent issues, then run run_migration_2.py.

Usage:
    python run_migration_1.py <path_to_wiki_html_file>

Example:
    python run_migration_1.py "C:/Users/PhilJ/Dropbox/phil-work.html"
    python run_migration_1.py "~/Dropbox/phil-home.html"
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Transform pipeline in execution order (Part 1: up to and including J)
# Each tuple: (transform_id, script_name, description)
TRANSFORM_PIPELINE = [
    # Phase 1: Extraction and Initial Filtering
    ("0", "0_extract.py", "Extract notes from TiddlyWiki HTML"),
    ("1", "1_filter_done_tasks.py", "Filter out completed tasks"),

    # Phase 2: PARA Assignment and Parent Identification
    ("4", "4_assign_para_folder.py", "Assign PARA folders"),
    ("5", "5_identify_para_parents.py", "Identify PARA parents"),

    # Phase 3: Parent Cleaning
    ("7", "7_strip_task_from_projects.py", "Strip Task tag from projects"),
    ("A", "A_strip_task_parents.py", "Clean task parent references"),

    # Phase 4: Parent Deduplication
    ("9", "9_dedupe_parent_substrings.py", "Deduplicate parent substrings"),

    # Phase 5: Orphan Task Collection
    ("B", "B_assign_orphan_tasks.py", "Assign orphan tasks to collector"),

    # Phase 6: WikiText Conversion
    ("F", "F_wikitext_to_markdown.py", "Convert WikiText to Markdown"),
    ("G", "G_convert_tables.py", "Convert tables to Markdown"),
    ("H", "H_convert_high_priority.py", "Convert high priority markers"),

    # Phase 7: Multi-Parent Resolution (interactive)
    ("J", "J_resolve_multi_parents.py", "Resolve multi-parent notes (interactive)"),
]


def run_transform(transform_id: str, script_name: str, input_folder: str, output_base: Path) -> str:
    """
    Run a single transform and return the output folder name.

    Args:
        transform_id: The ID character(s) for this transform
        script_name: The Python script filename
        input_folder: The input folder name (or wiki path for transform 0)
        output_base: Base path for output folders

    Returns:
        The output folder name
    """
    script_path = Path("transforms") / script_name

    if not script_path.exists():
        print(f"  ERROR: Script not found: {script_path}")
        return None

    # Determine output folder name
    if transform_id == "0":
        # Transform 0 outputs to folder "0"
        output_folder = "0"
    else:
        # Subsequent transforms append their ID
        output_folder = f"{input_folder}{transform_id}"

    # Build command
    cmd = [sys.executable, str(script_path), input_folder]

    print(f"  Input:  {input_folder}")
    print(f"  Output: {output_folder}")

    # Run the transform
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per transform
            check=True
        )

        # Print relevant output
        lines = result.stdout.split('\n')
        for line in lines:
            if any(key in line for key in ['Loaded', 'Final', 'Done!', 'Error', 'Moved', 'Fixed', 'Created', 'PASS', 'FAIL']):
                print(f"    {line}")

        if result.stderr:
            # Filter stderr for relevant warnings
            stderr_lines = result.stderr.split('\n')
            for line in stderr_lines:
                if 'warning' in line.lower() or 'error' in line.lower():
                    print(f"    WARNING: {line}")

        return output_folder

    except subprocess.TimeoutExpired:
        print(f"  ERROR: Transform timed out after 5 minutes")
        return None
    except subprocess.CalledProcessError as e:
        print(f"  ERROR: Transform failed with exit code {e.returncode}")
        print(f"    stdout: {e.stdout[-500:] if e.stdout else 'None'}")  # Last 500 chars
        print(f"    stderr: {e.stderr[-500:] if e.stderr else 'None'}")
        return None


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python run_migration_1.py <path_to_wiki_html_file>")
        print("Example: python run_migration_1.py 'C:/Users/PhilJ/Dropbox/phil-work.html'")
        sys.exit(1)

    wiki_path = sys.argv[1]
    wiki_file = Path(wiki_path)

    if not wiki_file.exists():
        print(f"Error: Wiki file not found: {wiki_path}")
        sys.exit(1)

    # Ensure output directory exists
    output_base = Path("output")
    output_base.mkdir(exist_ok=True)

    print("=" * 70)
    print("TiddlyWiki to Obsidian Migration Pipeline - Part 1")
    print("=" * 70)
    print(f"\nWiki file: {wiki_file.absolute()}")
    print(f"Output directory: {output_base.absolute()}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Track current input folder
    current_input = str(wiki_file)
    folder_chain = ""

    successful_transforms = 0
    failed_transform = None

    try:
        for idx, (transform_id, script_name, description) in enumerate(TRANSFORM_PIPELINE, 1):
            print(f"\n[{idx}/{len(TRANSFORM_PIPELINE)}] Transform {transform_id}: {description}")
            print("-" * 50)

            output_folder = run_transform(transform_id, script_name, current_input, output_base)

            if output_folder is None:
                failed_transform = transform_id
                print(f"\nTransform {transform_id} failed. Pipeline halted.")
                break

            successful_transforms += 1
            folder_chain += transform_id

            # Update input for next transform
            if transform_id == "0":
                current_input = "0"
            else:
                current_input = output_folder

        print("\n" + "=" * 70)

        if failed_transform:
            print(f"MIGRATION PART 1 INCOMPLETE - Failed at Transform {failed_transform}")
            print(f"Successfully completed: {successful_transforms}/{len(TRANSFORM_PIPELINE)} transforms")
            print(f"Last successful output: output/{current_input}")
            sys.exit(1)
        else:
            print("MIGRATION PART 1 COMPLETE!")
            print(f"Completed: {successful_transforms}/{len(TRANSFORM_PIPELINE)} transforms")
            print(f"Output folder: output/{current_input}")
            print(f"Folder chain: {folder_chain}")
            print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\nNext steps:")
            print(f"  1. Review multi-parent notes in: output/{current_input}")
            print(f"  2. Manually resolve any multi-parent conflicts if needed")
            print(f"  3. Run: python run_migration_2.py {current_input}")

    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        print(f"Last successful output: output/{current_input}")
        sys.exit(1)


if __name__ == "__main__":
    main()
