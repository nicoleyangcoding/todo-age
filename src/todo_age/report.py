"""Format scan results as a table, Markdown, JSON or CSV."""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import statistics
import time

from .scan import Item

DAY = 86400
_AGE = re.compile(r"^\s*(\d+)\s*(d|w|m|mo|y)\s*$", re.IGNORECASE)
_UNIT_DAYS = {"d": 1, "w": 7, "m": 30, "mo": 30, "y": 365}


def parse_age(text: str) -> int:
    """'90d', '6m', '2y' -> days."""
    match = _AGE.match(text)
    if not match:
        raise ValueError(f"'{text}' is not an age. Use a number with d, w, m or y, like 90d or 1y.")
    return int(match.group(1)) * _UNIT_DAYS[match.group(2).lower()]


def age_days(item: Item, now: float) -> int:
    return 0 if not item.committed else max(0, int((now - item.timestamp) // DAY))


def human_age(days: int) -> str:
    if days < 1:
        return "new"
    if days < 60:
        return f"{days}d"
    if days < 730:
        return f"{days // 30}mo"
    return f"{days / 365:.1f}y"


def summary(items: list[Item], now: float) -> str:
    if not items:
        return "No TODOs found."
    ages = [age_days(i, now) for i in items]
    noun = "marker" if len(items) == 1 else "markers"
    return (
        f"{len(items)} {noun}, median age {human_age(int(statistics.median(ages)))}, "
        f"oldest {human_age(max(ages))}"
    )


def _rows(items: list[Item], now: float) -> list[dict[str, object]]:
    return [
        {
            "age_days": age_days(i, now),
            "age": human_age(age_days(i, now)),
            "author": i.author,
            "email": i.email,
            "file": i.path,
            "line": i.line,
            "tag": i.tag,
            "text": i.text,
            "commit": i.commit if i.committed else None,
        }
        for i in items
    ]


def _clip(text: str, width: int) -> str:
    return text if len(text) <= width else text[: max(1, width - 3)] + "..."


def table(items: list[Item], now: float, width: int | None = None) -> str:
    width = width or shutil.get_terminal_size((120, 20)).columns
    rows = [(human_age(age_days(i, now)), i.author, f"{i.path}:{i.line}", i.text) for i in items]
    head = ("AGE", "AUTHOR", "LOCATION", "TEXT")
    w_age = max(len(head[0]), *(len(r[0]) for r in rows)) if rows else 3
    w_author = min(18, max(len(head[1]), *(len(r[1]) for r in rows))) if rows else 6
    w_loc = min(48, max(len(head[2]), *(len(r[2]) for r in rows))) if rows else 8
    w_text = max(20, width - w_age - w_author - w_loc - 6)
    lines = []
    for age, author, loc, text in (head, *rows):
        lines.append(
            f"{age:<{w_age}}  {_clip(author, w_author):<{w_author}}  "
            f"{_clip(loc, w_loc):<{w_loc}}  {_clip(text, w_text)}".rstrip()
        )
    return "\n".join(lines)


def markdown(items: list[Item], now: float, repo_url: str | None = None) -> str:
    out = [
        f"**{summary(items, now)}**",
        "",
        "| Age | Author | Location | Text |",
        "| --- | --- | --- | --- |",
    ]
    for row in _rows(items, now):
        loc = f"{row['file']}:{row['line']}"
        if repo_url and row["commit"]:
            loc = f"[{loc}]({repo_url}/blob/{row['commit']}/{row['file']}#L{row['line']})"
        text = str(row["text"]).replace("|", "\\|")
        out.append(f"| {row['age']} | {row['author']} | {loc} | {text} |")
    return "\n".join(out)


def as_json(items: list[Item], now: float) -> str:
    return json.dumps({"summary": summary(items, now), "items": _rows(items, now)}, indent=2)


def as_csv(items: list[Item], now: float) -> str:
    buffer = io.StringIO()
    fields = ["age_days", "author", "email", "file", "line", "tag", "text", "commit"]
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(_rows(items, now))
    return buffer.getvalue()


def now() -> float:
    return time.time()
