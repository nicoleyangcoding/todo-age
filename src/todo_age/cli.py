"""todo-age command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, report
from .scan import DEFAULT_TAGS, GitError, scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo-age",
        description="List every TODO, FIXME and HACK in a git repo, oldest first.",
        epilog="Examples:\n  todo-age\n  todo-age --older-than 1y\n  todo-age src --format markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="*", help="limit the search to these files or folders")
    parser.add_argument("--older-than", metavar="AGE", help="only show markers older than AGE (90d, 6m, 1y)")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PATH",
        help="skip files or folders matching PATH, like vendor/ or '*.min.js' (repeatable)",
    )
    parser.add_argument("--author", help="only show markers whose author name or email contains this text")
    parser.add_argument(
        "--tags",
        default=",".join(DEFAULT_TAGS),
        help=f"comma-separated markers to look for (default: {','.join(DEFAULT_TAGS)})",
    )
    parser.add_argument("--format", choices=["table", "markdown", "json", "csv"], default="table")
    parser.add_argument("--limit", type=int, metavar="N", help="show at most N markers")
    parser.add_argument("--newest-first", action="store_true", help="reverse the sort order")
    parser.add_argument(
        "--fail-if-older-than",
        metavar="AGE",
        help="exit with status 1 if any marker is older than AGE (for CI)",
    )
    parser.add_argument(
        "--repo-url", help="link locations in Markdown output, e.g. https://github.com/you/repo"
    )
    parser.add_argument("-C", dest="directory", default=".", help="run as if started in this directory")
    parser.add_argument("--version", action="version", version=f"todo-age {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        min_age = report.parse_age(args.older_than) if args.older_than else None
        fail_age = report.parse_age(args.fail_if_older_than) if args.fail_if_older_than else None
    except ValueError as exc:
        parser.error(str(exc))
    tags = tuple(t.strip() for t in args.tags.split(",") if t.strip())
    if not tags:
        parser.error("--tags needs at least one marker")

    try:
        pathspecs = tuple(args.paths) + tuple(f":(exclude){p}" for p in args.exclude)
        items = scan(Path(args.directory), tags, pathspecs)
    except GitError as exc:
        print(f"todo-age: {exc}", file=sys.stderr)
        return 2

    now = report.now()
    if args.author:
        needle = args.author.lower()
        items = [i for i in items if needle in i.author.lower() or needle in i.email.lower()]
    if min_age is not None:
        items = [i for i in items if report.age_days(i, now) >= min_age]

    items.sort(key=lambda i: (report.age_days(i, now), i.path, i.line), reverse=not args.newest_first)
    stale = fail_age is not None and any(report.age_days(i, now) >= fail_age for i in items)
    shown = items[: args.limit] if args.limit else items

    if args.format == "json":
        print(report.as_json(shown, now))
    elif args.format == "csv":
        sys.stdout.write(report.as_csv(shown, now))
    elif args.format == "markdown":
        print(report.markdown(shown, now, args.repo_url))
    else:
        if shown:
            print(report.table(shown, now))
            print()
        print(report.summary(items, now))
        if args.limit and len(items) > len(shown):
            print(f"Showing the {len(shown)} oldest. Remove --limit to see all.")

    if stale:
        print(f"todo-age: found markers older than {args.fail_if_older_than}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
