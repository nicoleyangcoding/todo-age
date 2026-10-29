"""Find marker comments with git grep and date them with git blame."""

from __future__ import annotations

import os
import re
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TAGS = ("TODO", "FIXME", "HACK", "XXX")
UNCOMMITTED = "0" * 40


class GitError(Exception):
    pass


@dataclass(frozen=True)
class Item:
    path: str
    line: int
    tag: str
    text: str
    author: str
    email: str
    timestamp: int  # unix seconds; 0 when the line is not committed yet
    commit: str

    @property
    def committed(self) -> bool:
        return self.commit != UNCOMMITTED


def git(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            check=False,
            env={**os.environ, "GIT_PAGER": "cat", "LC_ALL": "C"},
        )
    except FileNotFoundError:
        raise GitError("git is not installed or not on PATH") from None
    if result.returncode not in (0, 1):  # git grep exits 1 when nothing matches
        message = result.stderr.decode("utf-8", "replace").strip()
        raise GitError(message or f"git {args[0]} failed")
    return result.stdout.decode("utf-8", "replace")


def repo_root(path: Path) -> Path:
    out = git(path, "rev-parse", "--show-toplevel").strip()
    if not out:
        raise GitError(f"{path} is not inside a git repository")
    return Path(out)


def tag_pattern(tags: tuple[str, ...]) -> re.Pattern[str]:
    alternatives = "|".join(re.escape(tag) for tag in tags)
    return re.compile(rf"(?<![A-Za-z0-9_])({alternatives})(?![A-Za-z0-9_])")


def grep(
    root: Path, tags: tuple[str, ...], pathspecs: tuple[str, ...] = ()
) -> list[tuple[str, int, str, str]]:
    """Return (path, line, tag, text) for every tracked line that mentions a tag."""
    args = ["grep", "-z", "-n", "-I", "--untracked", "-F"]
    for tag in tags:
        args += ["-e", tag]
    args += ["--", *pathspecs] if pathspecs else []
    out = git(root, *args)
    pattern = tag_pattern(tags)
    hits = []
    # With -z each record is "path\0line\0content\n".
    for record in out.split("\n"):
        parts = record.split("\0", 2)
        if len(parts) != 3:
            continue
        path, line, content = parts
        match = pattern.search(content)
        if not match:
            continue
        text = content[match.start() :].strip()
        text = re.sub(r"\s*(\*/|-->|#}|%>)\s*$", "", text)
        hits.append((path, int(line), match.group(1), text))
    return hits


def blame(root: Path, path: str, lines: list[int]) -> dict[int, tuple[str, str, int, str]]:
    """Map line number -> (author, email, timestamp, commit) for the given lines of one file."""
    args = ["blame", "--line-porcelain", "-w"]
    for line in sorted(set(lines)):
        args += ["-L", f"{line},{line}"]
    try:
        out = git(root, *args, "--", path)
    except GitError:
        return {}  # untracked or otherwise unblameable file
    result: dict[int, tuple[str, str, int, str]] = {}
    commit, final, author, email, stamp = "", 0, "", "", 0
    for row in out.split("\n"):
        if row.startswith("\t"):
            result[final] = (author, email, stamp, commit)
            continue
        head, _, rest = row.partition(" ")
        if len(head) == 40 and all(c in "0123456789abcdef" for c in head):
            commit, final = head, int(rest.split()[1])
        elif head == "author":
            author = rest
        elif head == "author-mail":
            email = rest.strip("<>")
        elif head == "author-time":
            stamp = int(rest)
    return result


def scan(path: Path, tags: tuple[str, ...] = DEFAULT_TAGS, pathspecs: tuple[str, ...] = ()) -> list[Item]:
    root = repo_root(path)
    hits = grep(root, tags, pathspecs)
    by_file: dict[str, list[int]] = defaultdict(list)
    for file, line, _, _ in hits:
        by_file[file].append(line)

    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
        blames = dict(zip(by_file, pool.map(lambda f: blame(root, f, by_file[f]), by_file)))

    items = []
    for file, line, tag, text in hits:
        author, email, stamp, commit = blames.get(file, {}).get(line, ("", "", 0, UNCOMMITTED))
        if commit == UNCOMMITTED:
            author, email, stamp = "(uncommitted)", "", 0
        items.append(Item(file, line, tag, text, author, email, stamp, commit))
    return items
