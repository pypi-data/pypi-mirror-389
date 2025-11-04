from __future__ import annotations
from pathlib import Path
from typing import Optional
import shutil
import logging

from .core import DeleteOptions, _iter_files, _passes_filters, _delete

logger = logging.getLogger("filedeletemanager")


def delete_if_over_size(directory: str | Path, max_total_bytes: int, options: Optional[DeleteOptions] = None, sort_key: Optional[str] = None) -> int:
    '''
    Delete files in the specified directory if the total size exceeds max_total_bytes.
    Start to delete the oldest files first until the total size is under the limit.
    Args:
        directory: The target directory to monitor and delete files from.
        max_total_bytes: The maximum allowed total size in bytes.
        options: Additional deletion options.
    Returns:
        Number of files deleted.
    '''
    opt = options or DeleteOptions()
    root = Path(directory)

    files = [p for p in _iter_files(root, opt.recursive, opt.follow_symlinks) if _passes_filters(p, opt)]

    # Determine effective sort key: explicit param wins over options
    effective_sort = sort_key or opt.sort_key or 'mtime'

    # Sort files so the correct candidates are removed first:
    # - mtime/ctime: oldest first (ascending)
    # - size: largest first (descending) when we want to remove biggest items first
    if effective_sort == "mtime":
        files.sort(key=lambda p: p.stat().st_mtime)
    elif effective_sort == "ctime":
        try:
            files.sort(key=lambda p: p.stat().st_birthtime)
        except AttributeError:
            files.sort(key=lambda p: p.stat().st_ctime)
    elif effective_sort == "size":
        files.sort(key=lambda p: p.stat().st_size, reverse=True)
    else:
        files.sort(key=lambda p: p.stat().st_mtime)

    total = sum(p.stat().st_size for p in files)
    deleted = 0
    for p in files:
        if total <= max_total_bytes:
            break
        try:
            size = p.stat().st_size
        except FileNotFoundError:
            continue
        if _delete(p, opt):
            total -= size
            deleted += 1

    if opt.delete_empty_dirs and not opt.dry_run:
        from .core import _delete_empty_dirs
        _delete_empty_dirs(root)

    return deleted


def move_to_trash(path: str | Path, trash_dir: str | Path, options: Optional[DeleteOptions] = None) -> int:
    '''
    Move a file or directory to a specified trash directory.
    Args:
        path: The file or directory to move.
        trash_dir: The directory to move the file or directory to.
        options: Additional deletion options.
    Returns:
        Number of items moved.
    '''
    opt = options or DeleteOptions()
    src = Path(path)
    dst = Path(trash_dir)
    dst.mkdir(parents=True, exist_ok=True)

    moved = 0

    # If src is a file, move it directly
    if src.is_file():
        target_path = dst / src.name
        if opt.dry_run:
            logger.info(f"[Dry Run] Moving {src} to {target_path}")
            # dry-run should not count as moved
            return 0
        try:
            shutil.move(str(src), str(target_path))
            logger.info(f"Moved {src} to {target_path}")
            return 1
        except Exception as e:
            logger.error(f"Error moving {src} to {target_path}: {e}")
            return 0

    # Otherwise assume directory: preserve relative paths to avoid name collisions
    for p in _iter_files(src, opt.recursive, opt.follow_symlinks):
        if not _passes_filters(p, opt):
            continue
        try:
            rel = p.relative_to(src)
        except Exception:
            rel = Path(p.name)
        target_path = dst / rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if opt.dry_run:
            logger.info(f"[Dry Run] Moving {p} to {target_path}")
            # In dry-run we do not actually move; do not count
            continue
        try:
            shutil.move(str(p), str(target_path))
            logger.info(f"Moved {p} to {target_path}")
            moved += 1
        except Exception as e:
            logger.error(f"Error moving {p} to {target_path}: {e}")

    return moved
