
from __future__ import annotations
from dataclasses import dataclass
import fnmatch
import logging
import os
from pathlib import Path
import time
from typing import Iterable, Optional, Sequence

logger = logging.getLogger("filedeletemanager")
logger.addHandler(logging.NullHandler())

@dataclass
class DeleteOptions:
    '''
    Options for deleting files and directories.
        dry_run: If True, simulate deletions without actually deleting files.
        recursive: If True, delete files in subdirectories recursively.
        include_pattern: List of glob patterns to include for deletion.
        exclude_pattern: List of glob patterns to exclude from deletion.
        min_size_bytes: Minimum file size in bytes to consider for deletion.
        max_size_bytes: Maximum file size in bytes to consider for deletion.
        follow_symlinks: If True, follow symbolic links when deleting files.
        delete_empty_dirs: If True, delete directories that become empty after file deletions.    
    '''
    dry_run: bool = False
    recursive: bool = True
    include_pattern: Optional[Sequence[str]] = None # e.g., ['*.tmp', '*.log']
    exclude_pattern: Optional[Sequence[str]] = None # e.g., ['important.log']
    min_size_bytes: Optional[int] = None
    max_size_bytes: Optional[int] = None
    follow_symlinks: bool = False
    delete_empty_dirs: bool = False
    # sort key used by some rules (mtime|ctime|size|name)
    sort_key: str = 'mtime'
    # Backwards-compatible aliases used by tests and older callers
    include_patterns: Optional[Sequence[str]] = None
    exclude_patterns: Optional[Sequence[str]] = None

    def __post_init__(self):
        # Normalize alias fields to the canonical names used in the code
        if self.include_pattern is None and self.include_patterns is not None:
            object.__setattr__(self, 'include_pattern', self.include_patterns)
        if self.exclude_pattern is None and self.exclude_patterns is not None:
            object.__setattr__(self, 'exclude_pattern', self.exclude_patterns)


def _iter_files(root: Path, recursive: bool, follow_symlinks: bool) -> Iterable[Path]:
    '''
    Helper function to iterate over files in a directory.
    Args:
        root: The root directory to start searching from.
        recursive: If True, search subdirectories recursively.
        follow_symlinks: If True, follow symbolic links.
    '''
    if recursive:
        for dirpath, _, filenames in os.walk(root, followlinks=follow_symlinks):
            for filename in filenames:
                yield Path(dirpath) / filename
    else:
        for entry in os.scandir(root):
            if entry.is_file(follow_symlinks=follow_symlinks):
                yield Path(entry.path)


def _match_patterns(name: str, patterns: Optional[Sequence[str]]) -> bool:
    '''
    Check if a filename matches any of the given glob patterns.
    Args:
        name: The filename to check.
        patterns: A list of glob patterns.
    Returns:
        True if the filename matches any pattern, False otherwise.
    '''
    if not patterns:
        return True
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def _passes_filters(p: Path, opt: DeleteOptions) -> bool:
    '''
    Check if a file passes the size and pattern filters.
    Args:
        p: The file path to check.
        opt: The deletion options containing filters.
    '''
    if opt.include_pattern and not _match_patterns(p.name, opt.include_pattern):
        return False
    if opt.exclude_pattern and _match_patterns(p.name, opt.exclude_pattern):
        return False
    try:
        stat = p.stat().st_size
    except FileNotFoundError:
        return False
    if opt.min_size_bytes is not None and stat < opt.min_size_bytes:
        return False
    if opt.max_size_bytes is not None and stat > opt.max_size_bytes:
        return False
    return True

def _delete(p: Path, opt: DeleteOptions):
    '''
    Delete a file or directory based on the options.
    Args:
        p: The path to delete.
        opt: The deletion options.
    '''
    if opt.dry_run:
        logger.info(f"[Dry Run] Deleting: {p}")
        # In dry-run we do not actually delete; indicate no real deletion occurred
        return False
    try:
        if p.is_file() or p.is_symlink():
            p.unlink(missing_ok=True)
            logger.info(f"Deleted file: {p}")
            return True
        elif p.is_dir():
            p.rmdir()
            logger.info(f"Deleted directory: {p}")
            return True
    except Exception as e:
        logger.error(f"Error deleting {p}: {e}")
    return False


def _parse_time_string(time_str: str | int) -> int:
    '''
    Parse a time string with units into seconds.
    Args:
        time_str: Time value as string with unit (e.g., "5d", "30m", "3600s") or integer (seconds).
    Returns:
        Time in seconds as integer.
    Raises:
        ValueError: If the time string format is invalid.
    '''
    if isinstance(time_str, int):
        return time_str
    
    if isinstance(time_str, str):
        time_str = time_str.strip().lower()
        
        # If it's just a number without unit, assume seconds
        if time_str.isdigit():
            return int(time_str)
        
        # Parse time with unit
        if len(time_str) < 2:
            raise ValueError(f"Invalid time format: {time_str}")
        
        unit = time_str[-1]
        try:
            value = float(time_str[:-1])
        except ValueError:
            raise ValueError(f"Invalid numeric value in time string: {time_str}")
        
        if unit == 's':  # seconds
            return int(value)
        elif unit == 'm':  # minutes
            return int(value * 60)
        elif unit == 'd':  # days
            return int(value * 86400)  # 24 * 60 * 60
        else:
            raise ValueError(f"Unsupported time unit: {unit}. Use 's' (seconds), 'm' (minutes), or 'd' (days)")
    
    raise ValueError(f"Invalid time format: {time_str}")


def delete_by_age(directory: str | Path, older_than: str | int, options: Optional[DeleteOptions] = None) -> int:
    '''
    Delete files older than a specified age.
    Args:
        directory: The root directory to search for files.
        older_than: Age threshold. Can be:
                    - Integer: seconds
                    - String with unit: "5d" (days), "30m" (minutes), "3600s" (seconds)
        options: Deletion options.
    Returns:
        Number of files deleted.
    '''
    opt = options or DeleteOptions()
    root = Path(directory)
    now = time.time()
    deleted_count = 0
    
    # Convert time to seconds
    older_than_seconds = _parse_time_string(older_than)

    for p in _iter_files(root, opt.recursive, opt.follow_symlinks):
        if not _passes_filters(p, opt):
            continue
        try:
            mtime = p.stat().st_mtime
        except FileNotFoundError:
            continue
        if now - mtime > older_than_seconds:
            if _delete(p, opt):
                deleted_count += 1

    # Optionally delete empty directories after removing files
    if opt.delete_empty_dirs and not opt.dry_run:
        _delete_empty_dirs(root)
    
    return deleted_count

def delete_by_count(directory: str | Path, keep_last: int, options: Optional[DeleteOptions] = None, sort_key: str = 'mtime') -> int:
    '''
    Delete files to keep only the last N files based on a sort key.
    Args:
        directory: The root directory to search for files.
        keep_last: Number of most recent files to keep.
        options: Deletion options.
        sort_key: Attribute to sort by ('mtime' for modification time, 'ctime' for creation time).
    Returns:
        Number of files deleted.
    '''
    opt = options or DeleteOptions()
    root = Path(directory)
    deleted_count = 0
    
    # Gather files that pass filters
    files = [p for p in _iter_files(root, opt.recursive, opt.follow_symlinks) if _passes_filters(p, opt)]
    
    # Sort files based on the specified key
    if sort_key == 'mtime':
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    elif sort_key == 'ctime':
        # Try to use st_birthtime if is not present use st_ctime which is available cross-platform.
        try:
            files.sort(key=lambda p: p.stat().st_birthtime, reverse=True)
        except AttributeError:
            files.sort(key=lambda p: p.stat().st_ctime, reverse=True)
    elif sort_key == "size":
        files.sort(key=lambda p: p.stat().st_size, reverse=True)
    elif sort_key == "name":
        files.sort(key=lambda p: p.name, reverse=True)
    else:
        raise ValueError(f"Unsupported sort_key: {sort_key}. Use mtime|ctime|size|name")
    
    survivors = set(files[:max(keep_last, 0)])
    victims = [p for p in files if p not in survivors]
   
    # Delete files beyond the keep_last count
    for p in victims:
        if _delete(p, opt):
            deleted_count += 1

    if opt.delete_empty_dirs and not opt.dry_run:
        _delete_empty_dirs(root)

    return deleted_count

def _delete_empty_dirs(root: Path) -> int:
    '''
    Delete empty directories under the given root.
    Args:
        root: The root directory to start searching from.
    Returns:
        Number of directories deleted.
    '''
    deleted_count = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        dir_path = Path(dirpath)
        if not dirnames and not filenames:
            try:
                dir_path.rmdir()
                logger.info(f"Deleted empty directory: {dir_path}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting directory {dir_path}: {e}")
    return deleted_count