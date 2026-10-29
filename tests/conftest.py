from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

DAY = 86400


class Repo:
    def __init__(self, path: Path):
        self.path = path
        self.run("init", "-q", "-b", "main")
        self.run("config", "user.name", "Test")
        self.run("config", "user.email", "test@example.com")
        self.run("config", "commit.gpgsign", "false")

    def run(self, *args: str, env: dict | None = None) -> str:
        return subprocess.run(
            ["git", *args], cwd=self.path, check=True, capture_output=True, text=True, env=env
        ).stdout

    def write(self, name: str, text: str) -> None:
        target = self.path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def commit(self, days_ago: int, author: str = "Test", email: str = "test@example.com") -> None:
        stamp = f"{int(time.time()) - days_ago * DAY} +0000"
        env = {
            **os.environ,
            "GIT_AUTHOR_DATE": stamp,
            "GIT_COMMITTER_DATE": stamp,
            "GIT_AUTHOR_NAME": author,
            "GIT_AUTHOR_EMAIL": email,
        }
        self.run("add", "-A")
        self.run("commit", "-q", "-m", f"commit {days_ago}", env=env)


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    return Repo(tmp_path)
