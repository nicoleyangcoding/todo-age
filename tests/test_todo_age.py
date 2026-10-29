import json
import time

import pytest

from todo_age import report
from todo_age.cli import main
from todo_age.scan import GitError, scan, tag_pattern


def _setup(repo):
    repo.write("old.py", "x = 1\n# TODO: handle refunds\n")
    repo.commit(days_ago=900, author="Dana", email="dana@example.com")
    repo.write("api/routes.js", "// FIXME race condition\nconst a = 1;\n/* HACK: temporary */\n")
    repo.commit(days_ago=100, author="Lee", email="lee@example.com")
    repo.write("old.py", "x = 1\n# TODO: handle refunds\n# TODO add tests\n")
    repo.commit(days_ago=5, author="Sam", email="sam@example.com")


def test_tag_pattern_needs_word_boundaries():
    pattern = tag_pattern(("TODO", "FIXME"))
    assert pattern.search("# TODO: x")
    assert pattern.search("//TODO(dana)")
    assert not pattern.search("todo_list = []")
    assert not pattern.search("TODOS = 3")
    assert not pattern.search("MYTODO")


def test_scan_dates_each_line(repo):
    _setup(repo)
    items = {(i.path, i.line): i for i in scan(repo.path)}
    assert set(items) == {("old.py", 2), ("old.py", 3), ("api/routes.js", 1), ("api/routes.js", 3)}
    assert items[("old.py", 2)].author == "Dana"  # untouched line keeps its original author
    assert items[("old.py", 3)].author == "Sam"
    assert items[("api/routes.js", 3)].text == "HACK: temporary"
    now = time.time()
    assert 899 <= report.age_days(items[("old.py", 2)], now) <= 901


def test_uncommitted_and_untracked_lines(repo):
    _setup(repo)
    repo.write("new.py", "# TODO brand new\n")
    repo.write("old.py", "x = 1\n# TODO: handle refunds\n# TODO add tests\n# FIXME not committed\n")
    items = {(i.path, i.line): i for i in scan(repo.path)}
    assert items[("new.py", 1)].author == "(uncommitted)"
    assert items[("old.py", 4)].author == "(uncommitted)"
    assert not items[("old.py", 4)].committed


def test_ignores_binary_and_gitignored(repo):
    repo.write(".gitignore", "build/\n")
    repo.write("build/out.py", "# TODO ignored\n")
    (repo.path / "blob.bin").write_bytes(b"\x00\x01TODO\x00")
    repo.write("a.py", "# TODO keep\n")
    repo.commit(days_ago=1)
    assert [i.path for i in scan(repo.path)] == ["a.py"]


def test_not_a_repo(tmp_path):
    with pytest.raises(GitError):
        scan(tmp_path)
    assert main(["-C", str(tmp_path)]) == 2


def test_cli_filters_and_sorting(repo, capsys):
    _setup(repo)
    assert main(["-C", str(repo.path), "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    ages = [row["age_days"] for row in data["items"]]
    assert ages == sorted(ages, reverse=True)
    assert data["summary"].startswith("4 markers")

    main(["-C", str(repo.path), "--older-than", "1y", "--format", "json"])
    assert [r["author"] for r in json.loads(capsys.readouterr().out)["items"]] == ["Dana"]

    main(["-C", str(repo.path), "--author", "lee@", "--format", "json"])
    assert {r["author"] for r in json.loads(capsys.readouterr().out)["items"]} == {"Lee"}

    main(["-C", str(repo.path), "--tags", "HACK", "--format", "json"])
    assert [r["tag"] for r in json.loads(capsys.readouterr().out)["items"]] == ["HACK"]

    main(["-C", str(repo.path), "api", "--format", "json"])
    assert {r["file"] for r in json.loads(capsys.readouterr().out)["items"]} == {"api/routes.js"}


def test_cli_fail_gate(repo, capsys):
    _setup(repo)
    assert main(["-C", str(repo.path), "--fail-if-older-than", "2y"]) == 1
    assert main(["-C", str(repo.path), "--fail-if-older-than", "3y"]) == 0


def test_table_and_limit(repo, capsys):
    _setup(repo)
    assert main(["-C", str(repo.path), "--limit", "1"]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("AGE")
    assert "old.py:2" in out and "Showing the 1 oldest" in out


def test_markdown_links(repo, capsys):
    _setup(repo)
    main(["-C", str(repo.path), "--format", "markdown", "--repo-url", "https://github.com/x/y"])
    out = capsys.readouterr().out
    assert "| Age | Author | Location | Text |" in out
    assert "](https://github.com/x/y/blob/" in out


def test_csv(repo, capsys):
    _setup(repo)
    main(["-C", str(repo.path), "--format", "csv"])
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "age_days,author,email,file,line,tag,text,commit"
    assert len(lines) == 5


def test_empty_repo(repo, capsys):
    repo.write("a.py", "x = 1\n")
    repo.commit(days_ago=1)
    assert main(["-C", str(repo.path)]) == 0
    assert "No TODOs found." in capsys.readouterr().out


@pytest.mark.parametrize(("text", "days"), [("90d", 90), ("2w", 14), ("6m", 180), ("1y", 365), ("3mo", 90)])
def test_parse_age(text, days):
    assert report.parse_age(text) == days


def test_parse_age_rejects_garbage():
    with pytest.raises(ValueError):
        report.parse_age("old")


def test_human_age():
    assert report.human_age(0) == "new"
    assert report.human_age(45) == "45d"
    assert report.human_age(400) == "13mo"
    assert report.human_age(1000) == "2.7y"


def test_file_names_with_spaces(repo):
    repo.write("my notes/plan v2.md", "- TODO: write intro\n")
    repo.commit(days_ago=3)
    (item,) = scan(repo.path)
    assert item.path == "my notes/plan v2.md" and item.author == "Test"
