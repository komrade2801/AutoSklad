#!/usr/bin/env python3
"""
AutoSklad Database Cleanup Script

Cleans up database and command queue files from both client and server directories.

Usage:
    python cleanup_databases.py [--project-root PATH] [--force]

Options:
    --project-root PATH    Absolute path to AutoSklad project root (auto-detects if not provided)
    --force               Force deletion without confirmation
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

def print_error(message):
    """Print error message."""
    print(f"ERROR: {message}", file=sys.stderr)

def print_success(message):
    """Print success message."""
    print(f"SUCCESS: {message}")

def print_info(message):
    """Print info message."""
    print(f"INFO: {message}")

def print_warning(message):
    """Print warning message."""
    print(f"WARNING: {message}")

def find_project_root():
    """Find the AutoSklad project root directory."""
    try:
        # Try using git to find the project root
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        project_root = result.stdout.strip()
        if project_root and Path(project_root).exists():
            print_info(f"Found project root via git: {project_root}")
            return Path(project_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback: search for .git directory walking up
    print_warning("Git not available or not in repository, searching manually...")
    current_path = Path.cwd()

    while current_path != current_path.parent:  # Stop at root
        git_dir = current_path / ".git"
        if git_dir.exists():
            print_info(f"Found project root via .git search: {current_path}")
            return current_path
        current_path = current_path.parent

    return None

def main():
    parser = argparse.ArgumentParser(
        description="Clean up database and command queue files from AutoSklad project"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        help="Absolute path to AutoSklad project root (optional, auto-detects if not provided)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force deletion without confirmation"
    )

    args = parser.parse_args()

    # 1. Find project root
    if args.project_root:
        project_root = Path(args.project_root)
        if not project_root.exists():
            print_error(f"Project root path does not exist: {project_root}")
            return 1
    else:
        project_root = find_project_root()
        if not project_root:
            print_error("Could not find AutoSklad project root. Please provide --project-root parameter.")
            return 1

    # Verify it looks like AutoSklad (check for .git)
    if not (project_root / ".git").exists():
        print_warning(f"Project root doesn't appear to be a git repository: {project_root}")
        print_warning("Proceeding anyway, but please verify this is the correct AutoSklad directory.")

    # Define files to delete (relative to project root)
    files_to_delete = [
        "server/dbSync/Model/sync.db",
        "client/dbSync/Model/sync.db",
        "server/command_queue.json",
        "client/command_queue.json",
        "server/DB/Data/web_vending.db",
        "client/DB/Data/vending.db"
    ]

    # 2. Show what we're about to do
    print_info("")
    print_info("AutoSklad Database Cleanup Script")
    print_info("==================================")
    print_info(f"Project root: {project_root}")
    print_info("")
    print_info("Files to delete:")
    for relative_path in files_to_delete:
        full_path = project_root / relative_path
        status = "FOUND" if full_path.exists() else "NOT FOUND"
        marker = "*"
        print(f"  {status}: {relative_path}")
    print_info("")

    # 3. Ask for confirmation unless forced
    if not args.force:
        try:
            confirmation = input("Do you want to delete these files? (y/N) ").strip().lower()
            if confirmation not in ("y", "yes"):
                print_info("Operation cancelled.")
                return 0
        except KeyboardInterrupt:
            print_info("")
            print_info("Operation cancelled.")
            return 0

    print_info("")
    print_info("Starting deletion...")
    print_info("")

    deleted_count = 0
    not_found_count = 0

    # 4. Delete each file
    for relative_path in files_to_delete:
        full_path = project_root / relative_path

        try:
            if full_path.exists():
                if full_path.is_file():
                    full_path.unlink()
                elif full_path.is_dir():
                    shutil.rmtree(full_path)
                print_success(f"Deleted: {relative_path}")
                deleted_count += 1
            else:
                print_warning(f"Not found: {relative_path}")
                not_found_count += 1
        except Exception as e:
            print_error(f"Failed to delete {relative_path}: {e}")

    # 5. Summary
    print_info("")
    print_info("Cleanup Summary:")
    print_info(f"- Files successfully deleted: {deleted_count}")
    print_info(f"- Files not found: {not_found_count}")

    if deleted_count == len(files_to_delete):
        print_success("All database files have been cleaned up!")
    elif deleted_count > 0:
        print_success("Cleanup partially complete. Some files were deleted.")
    else:
        print_warning("No files were deleted. They were either not found or deletion failed.")

    print_info("")
    print_info("You may need to restart the client/server for changes to take effect.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
