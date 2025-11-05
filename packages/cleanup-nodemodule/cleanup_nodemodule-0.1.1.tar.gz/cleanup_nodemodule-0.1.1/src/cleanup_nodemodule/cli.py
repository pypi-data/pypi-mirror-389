"""Command-line interface for cleanup_nodemodule."""
from __future__ import annotations
import argparse
from .core import find_and_delete_targets


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="cleanup-nodemodule",
        description="Find and remove common build folders (node_modules, .next, dist)."
    )

    parser.add_argument('-p', '--path', default='.', help='Root path to start scanning (default: current directory)')
    parser.add_argument('-d', '--min-depth', type=int, default=0, help='Minimum depth before deletion is allowed (default: 0)')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dry-run', dest='dry_run', action='store_true', help='Show what would be deleted (default)')
    group.add_argument('--no-dry-run', dest='dry_run', action='store_false', help='Actually delete found directories')
    parser.set_defaults(dry_run=True)

    parser.add_argument('--targets', nargs='*', help='List of directory names to target (overrides defaults)')

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    targets = args.targets if args.targets else None
    find_and_delete_targets(args.path, args.min_depth, dry_run=args.dry_run, targets=targets)


if __name__ == '__main__':
    main()
