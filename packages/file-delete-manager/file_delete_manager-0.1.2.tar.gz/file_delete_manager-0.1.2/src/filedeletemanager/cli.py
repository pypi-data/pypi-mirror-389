import argparse
import logging
import os, inspect
import sys
import filedeletemanager
import filedeletemanager.core as core
from .core import DeleteOptions, delete_by_age, delete_by_count
from .rules import delete_if_over_size, move_to_trash


def _common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--recursive', dest='recursive', action='store_true', help='Recursively process directories.')
    parser.add_argument('--no-recursive', dest='recursive', action='store_false', help='Do not process directories recursively.')
    parser.set_defaults(recursive=True)
    parser.add_argument('--follow-symlinks', action='store_true', help='Follow symbolic links.')
    parser.add_argument('--dry-run', action='store_true', help='Simulate deletions without making changes.')
    parser.add_argument('--delete-empty-dirs', action='store_true', help='Delete empty directories after file deletions.')
    parser.add_argument('--log-level', default='INFO', help='Set the logging level (DEBUG, INFO, WARNING, ERROR).')
    parser.add_argument('--sort-key', choices=['mtime', 'ctime', 'size', 'name'], default='mtime', help='Attribute to sort files by.')
    parser.add_argument('directory', help='Target directory to process.')
    parser.add_argument('--include-pattern', action='append', dest='include_pattern', help='Include only files matching this pattern (can be used multiple times).')
    parser.add_argument('--exclude-pattern', action='append', dest='exclude_pattern', help='Exclude files matching this pattern (can be used multiple times).')
    parser.add_argument('--min-size', type=int, dest='min_size', help='Minimum file size in bytes to consider.')
    parser.add_argument('--max-size', type=int, dest='max_size', help='Maximum file size in bytes to consider.')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output.')


def _build_options(args) -> DeleteOptions:
    return DeleteOptions(
        dry_run=bool(getattr(args, 'dry_run', False)),
        recursive=bool(getattr(args, 'recursive', True)),
        include_pattern=getattr(args, 'include_pattern', None),
        exclude_pattern=getattr(args, 'exclude_pattern', None),
        min_size_bytes=getattr(args, 'min_size', None),
        max_size_bytes=getattr(args, 'max_size', None),
        follow_symlinks=bool(getattr(args, 'follow_symlinks', False)),
        delete_empty_dirs=bool(getattr(args, 'delete_empty_dirs', False)),
        sort_key=getattr(args, 'sort_key', 'mtime'),
    )


def main():
    if os.getenv("FILEDELETEMANAGER_DEBUG") == "1":
        print(f"[DEBUG] sys.path[0]: {sys.path[0]}")
        print(f"[DEBUG] filedeletemanager: {inspect.getfile(filedeletemanager)}")
        print(f"[DEBUG] core:        {inspect.getfile(core)}")
        
    parser = argparse.ArgumentParser(prog='filedeletemanager', description='File management utility.')
    sub = parser.add_subparsers(dest='command', required=True)

    p_age = sub.add_parser('delete-by-age', aliases=['age'], help='Delete files older than a specified age.')
    _common_options(p_age)
    p_age.add_argument('--older-than', type=str, required=True, help='Delete files older than this duration. Examples: 7d, 30m, 3600s')
    p_age.set_defaults(func=lambda args: delete_by_age(args.directory, args.older_than, _build_options(args)))

    p_count = sub.add_parser('delete-by-count', aliases=['count'], help='Delete files to maintain a maximum count.')
    _common_options(p_count)
    p_count.add_argument('--keep-last', '--max-count', dest='keep_last', type=int, required=True, help='Number of most recent files to keep.')
    p_count.set_defaults(func=lambda args: delete_by_count(args.directory, args.keep_last, _build_options(args), sort_key=args.sort_key))

    p_size = sub.add_parser('delete-by-size', aliases=['sizecap'], help='Delete files if total size exceeds a limit.')
    _common_options(p_size)
    p_size.add_argument('--max-total-bytes', type=int, required=True, help='Maximum total size in bytes to keep.')
    p_size.set_defaults(func=lambda args: delete_if_over_size(args.directory, args.max_total_bytes, _build_options(args)))

    p_trash = sub.add_parser('move-to-trash', aliases=['trash'], help='Move files to a trash directory.')
    _common_options(p_trash)
    p_trash.add_argument('--trash-dir', required=True, help='Directory to move files to as trash.')
    p_trash.set_defaults(func=lambda args: move_to_trash(args.directory, args.trash_dir, _build_options(args)))

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    result = args.func(args)

    print(f"Operation completed. Result: {result}")

if __name__ == "__main__":
    main()