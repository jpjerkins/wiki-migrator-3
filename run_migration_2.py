#!/usr/bin/env python3
"""
run_migration_2.py - TiddlyWiki to Obsidian migration pipeline (Part 2).

Runs transforms from the interactive multi-parent resolution through final output.
Starts with transform J (which can be re-run if needed).

This should be run after run_migration_1.py completes and you've manually
resolved any multi-parent conflicts.

Usage:
    python run_migration_2.py <input_folder>

Example:
    python run_migration_2.py 01457A9BFGHJ
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Transform pipeline in execution order (Part 2: starting from J)
# Each tuple: (transform_id, script_name, description)
TRANSFORM_PIPELINE = [
    # Phase 7: Multi-Parent Resolution (interactive - can be re-run)
    ("J", "J_resolve_multi_parents.py", "Resolve multi-parent notes (interactive)"),
    ("K", "K_strip_archive_from_multi.py", "Strip Archive from multi-parent notes"),
    ("L", "L_resolve_multi_parents.py", "Resolve remaining multi-parent notes"),

    # Phase 8: Task Processing with Protected Parents
    ("0A", "0A_inline_tasks_protected_parents.py", "Inline tasks (protected parents)"),

    # Phase 9: Archive Cleanup
    ("N", "N_remove_archive_with_parent.py", "Remove Archive from notes with parents"),

    # Phase 10: Path Assignment
    ("V", "V_path_assignment_with_ordinals.py", "Assign paths with PARA ordinals"),

    # Phase 11: Fixes for Parked/Done Project Leaves
    ("0B", "0B_fix_parked_leaves.py", "Fix Parked project leaves placement"),
    ("0C", "0C_fix_done_leaves.py", "Fix Done project leaves placement"),

    # Phase 12: Final Output
    ("Y", "Y_folder_notes_with_metadata.py", "Create final folder structure"),
]


def run_transform(transform_id: str, script_name: str, input_folder: str, output_base: Path) -> str:
    """
    Run a single transform and return the output folder name.

    Args:
        transform_id: The ID character(s) for this transform
        script_name: The Python script filename
        input_folder: The input folder name
        output_base: Base path for output folders

    Returns:
        The output folder name
    """
    script_path = Path("transforms") / script_name

    if not script_path.exists():
        print(f"  ERROR: Script not found: {script_path}")
        return None

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
        print("Usage: python run_migration_2.py <input_folder>")
        print("Example: python run_migration_2.py 01457A9BFGHJ")
        print("\nNote: Run run_migration_1.py first to generate the input folder")
        sys.exit(1)

    input_folder = sys.argv[1]

    # Ensure output directory exists
    output_base = Path("output")
    if not output_base.exists():
        print(f"Error: Output directory not found: {output_base}")
        sys.exit(1)

    # Check if input folder exists
    input_path = output_base / input_folder
    if not input_path.exists():
        print(f"Error: Input folder not found: {input_path}")
        print("\nAvailable folders:")
        for folder in sorted(output_base.iterdir()):
            if folder.is_dir():
                print(f"  {folder.name}")
        sys.exit(1)

    print("=" * 70)
    print("TiddlyWiki to Obsidian Migration Pipeline - Part 2")
    print("=" * 70)
    print(f"\nInput folder: {input_path.absolute()}")
    print(f"Output directory: {output_base.absolute()}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Track current input folder
    current_input = input_folder
    folder_chain = input_folder

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
            current_input = output_folder

        print("\n" + "=" * 70)

        if failed_transform:
            print(f"MIGRATION PART 2 INCOMPLETE - Failed at Transform {failed_transform}")
            print(f"Successfully completed: {successful_transforms}/{len(TRANSFORM_PIPELINE)} transforms")
            print(f"Last successful output: output/{current_input}")
            sys.exit(1)
        else:
            print("MIGRATION COMPLETE!")
            print(f"Completed: {successful_transforms}/{len(TRANSFORM_PIPELINE)} transforms")
            print(f"Final output folder: output/{current_input}")
            print(f"Complete folder chain: {folder_chain}")
            print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\nNext steps:")
            print(f"  1. Review the output in: output/{current_input}")
            print(f"  2. Copy the markdown files to your Obsidian vault")
            print(f"  3. Install the Obsidian Tasks plugin for recurring task support")

    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        print(f"Last successful output: output/{current_input}")
        sys.exit(1)


if __name__ == "__main__":
    main()
