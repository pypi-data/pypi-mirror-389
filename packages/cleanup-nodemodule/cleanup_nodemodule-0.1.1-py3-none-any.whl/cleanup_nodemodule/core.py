"""Core logic for finding and removing target folders.

This is a refactor of the original script to be importable and testable.
"""
from pathlib import Path
import os
import shutil
from typing import Iterable, Optional, Union

DEFAULT_TARGETS = ["node_modules", ".next", "dist"]


def delete_folder_recursive(folder_path: Union[str, Path], dry_run: bool = True) -> None:
    """Recursively delete a folder and all its contents.

    When dry_run is True this prints what would be deleted instead of removing.
    """
    folder_path = Path(folder_path)
    if not folder_path.exists():
        return

    try:
        if dry_run:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    print(f"Would delete file: {file_path}")
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    print(f"Would remove directory: {dir_path}")
            print(f"Would remove directory: {folder_path}")
        else:
            shutil.rmtree(folder_path)
    except Exception as e:
        print(f"Error deleting {folder_path}: {e}")


def find_and_delete_targets(start_path: Union[str, Path] = "./", min_depth: int = 0,
                            dry_run: bool = True,
                            targets: Optional[Iterable[str]] = None) -> None:
    """Recursively find and delete target directories at or below min_depth.

    Parameters
    - start_path: root path to start scanning (string or Path)
    - min_depth: minimum depth before deletion is allowed (0 = all levels)
    - dry_run: if True, do not delete, only print actions
    - targets: iterable of directory names to target; defaults to DEFAULT_TARGETS
    """
    if targets is None:
        targets = DEFAULT_TARGETS

    start = Path(start_path)
    if not start.exists():
        print(f"Start path does not exist: {start}")
        return

    def _recurse(path: Path, current_depth: int) -> None:
        try:
            for entry in path.iterdir():
                if entry.is_dir():
                    if current_depth >= min_depth and entry.name in targets:
                        action = 'Would delete:' if dry_run else 'Deleting:'
                        print(f"{action} {entry}")
                        delete_folder_recursive(entry, dry_run=dry_run)
                    else:
                        _recurse(entry, current_depth + 1)
        except PermissionError:
            print(f"Permission denied: {path}")
            return

    _recurse(start, 0)
