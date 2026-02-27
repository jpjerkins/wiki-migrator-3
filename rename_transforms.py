#!/usr/bin/env python3
"""
Script to reorganize transforms and output folders.
Shifts J-0B up by one ID and inserts I2 as J.
"""

import os
import shutil
from pathlib import Path

# Mapping for transform renames (applied in reverse order)
TRANSFORM_RENAMES = [
    ("0B_fix_done_leaves.py", "0C_fix_done_leaves.py"),
    ("0A_fix_parked_leaves.py", "0B_fix_parked_leaves.py"),
    ("Z_inline_tasks_protected_parents.py", "0A_inline_tasks_protected_parents.py"),
    ("Y_inline_tasks_with_recurring.py", "Z_inline_tasks_with_recurring.py"),
    ("X_folder_notes_with_metadata.py", "Y_folder_notes_with_metadata.py"),
    ("W_folder_notes_in_folders.py", "X_folder_notes_in_folders.py"),
    ("V_folder_notes_minimal.py", "W_folder_notes_minimal.py"),
    ("U_path_assignment_with_ordinals.py", "V_path_assignment_with_ordinals.py"),
    ("T_path_assignment_ordered.py", "U_path_assignment_ordered.py"),
    ("S_reorganize_projects.py", "T_reorganize_projects.py"),
    ("R_folder_notes_plugin.py", "S_folder_notes_plugin.py"),
    ("Q_fix_folder_notes.py", "R_fix_folder_notes.py"),
    ("P_path_assignment_hierarchical.py", "Q_path_assignment_hierarchical.py"),
    ("O_write_final_structure.py", "P_write_final_structure.py"),
    ("N_assign_output_paths.py", "O_assign_output_paths.py"),
    ("M_remove_archive_with_parent.py", "N_remove_archive_with_parent.py"),
    ("L_inline_tasks.py", "M_inline_tasks.py"),
    ("K_resolve_multi_parents.py", "L_resolve_multi_parents.py"),
    ("J_strip_archive_from_multi.py", "K_strip_archive_from_multi.py"),
    ("I2_resolve_multi_parents.py", "J_resolve_multi_parents.py"),
]

# Character mapping for folder renames
CHAR_MAP = {
    'J': 'K',
    'K': 'L',
    'L': 'M',
    'M': 'N',
    'N': 'O',
    'O': 'P',
    'P': 'Q',
    'Q': 'R',
    'R': 'S',
    'S': 'T',
    'T': 'U',
    'U': 'V',
    'V': 'W',
    'W': 'X',
    'X': 'Y',
    'Y': 'Z',
    'Z': '0A',
}

def rename_transforms():
    """Rename transform files."""
    transforms_dir = Path("transforms")
    print("=" * 70)
    print("STEP 1: Renaming transform files")
    print("=" * 70)

    for old_name, new_name in TRANSFORM_RENAMES:
        old_path = transforms_dir / old_name
        new_path = transforms_dir / new_name

        if old_path.exists():
            print(f"  {old_name} -> {new_name}")
            shutil.move(str(old_path), str(new_path))
        else:
            print(f"  SKIP {old_name} (not found)")
    print()

def rename_folder(old_name: str) -> str:
    """
    Rename a folder by replacing characters according to CHAR_MAP.
    Handle multi-character IDs like 0A, 0B properly.
    """
    new_name = ""
    i = 0
    while i < len(old_name):
        # Check for two-character IDs starting with 0
        if i < len(old_name) - 1 and old_name[i] == '0' and old_name[i+1] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            two_char = old_name[i:i+2]
            # Special handling for 0A → 0B and 0B → 0C
            if two_char == '0A':
                new_name += '0B'
                i += 2
                continue
            elif two_char == '0B':
                new_name += '0C'
                i += 2
                continue

        # Single character mapping
        char = old_name[i]
        if char == 'Z':
            new_name += '0A'
        elif char in CHAR_MAP:
            new_name += CHAR_MAP[char]
        else:
            new_name += char
        i += 1

    return new_name

def insert_j_before_k(folder_name: str) -> str:
    """Insert J before the first occurrence of K in the folder name."""
    if 'K' in folder_name:
        # Find first K and insert J before it
        k_index = folder_name.index('K')
        return folder_name[:k_index] + 'J' + folder_name[k_index:]
    return folder_name

def rename_output_folders():
    """Rename output folders and insert J before K."""
    output_dir = Path("output")

    print("=" * 70)
    print("STEP 2: Renaming output folders")
    print("=" * 70)

    # Get all folders and sort in reverse order to avoid conflicts
    folders = sorted([f for f in output_dir.iterdir() if f.is_dir()], reverse=True)

    renames = []
    for folder in folders:
        if folder.name == '.gitkeep':
            continue

        old_name = folder.name
        # Apply character mappings
        new_name = rename_folder(old_name)

        if old_name != new_name:
            renames.append((old_name, new_name))

    # Execute renames
    for old_name, new_name in renames:
        old_path = output_dir / old_name
        new_path = output_dir / new_name
        print(f"  {old_name} -> {new_name}")
        shutil.move(str(old_path), str(new_path))

    print()

    print("=" * 70)
    print("STEP 3: Inserting J before K in output folders")
    print("=" * 70)

    # Now insert J before K in folders that have K
    folders = sorted([f for f in output_dir.iterdir() if f.is_dir()], reverse=True)

    for folder in folders:
        if folder.name == '.gitkeep':
            continue

        old_name = folder.name
        if 'K' in old_name:
            new_name = insert_j_before_k(old_name)
            if old_name != new_name:
                old_path = output_dir / old_name
                new_path = output_dir / new_name
                print(f"  {old_name} -> {new_name}")
                shutil.move(str(old_path), str(new_path))

    print()

def main():
    # Step 1: Rename transform files
    rename_transforms()

    # Step 2 & 3: Rename output folders and insert J
    rename_output_folders()

    print("=" * 70)
    print("All renames complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
