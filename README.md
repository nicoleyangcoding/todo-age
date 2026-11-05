# todo-age

Find every TODO, FIXME and HACK in a git repo and see how old each one is, oldest first.

A list of 400 TODOs is noise. The 20 that have sat untouched for three years are a to-do list. `todo-age` uses `git blame` to date every marker, so you can see which ones are real debt.

```
$ todo-age --limit 5
AGE   AUTHOR  LOCATION                   TEXT
4.2y  Dana    src/billing/refunds.py:88  TODO: handle partial refunds
3.1y  Lee     api/routes.js:201          FIXME race condition when two saves overlap
2.7y  Dana    src/billing/tax.py:14      HACK: hardcoded rate until the tax API is ready
14mo  Sam     web/cart.tsx:56            TODO: remove after the checkout redesign
45d   Priya   scripts/deploy.sh:9        XXX check exit code

37 markers, median age 1.4y, oldest 4.2y
Showing the 5 oldest. Remove --limit to see all.
```

## Quick start

Requires Python 3.9 or newer and git.

```bash
pipx install git+https://github.com/nicoleyangcoding/todo-age
cd your-repo
todo-age
```

No dependencies, no configuration. It runs in well under a second on most repos.

## Common uses

```bash
todo-age --older-than 1y            # only the ones older than a year
todo-age --author dana              # one person's markers (matches name or email)
todo-age src/billing                # one folder
todo-age --exclude vendor/          # skip a folder (repeat for more)
todo-age --tags TODO,FIXME,BUG      # your own set of markers
todo-age --format markdown > TODOS.md
todo-age --format json | jq '.items[0]'
```

| Option | What it does |
| --- | --- |
| `--older-than AGE` | Hide markers newer than `AGE`. Ages look like `90d`, `6m`, `2y`. |
| `--exclude PATH` | Skip files or folders matching `PATH` (a folder like `vendor/` or a pattern like `*.min.js`). Repeat it for more. |
| `--author TEXT` | Only markers whose blamed author name or email contains `TEXT`. |
| `--tags LIST` | Markers to look for. Default: `TODO,FIXME,HACK,XXX`. |
| `--format` | `table` (default), `markdown`, `json` or `csv`. |
| `--limit N` | Show the N oldest. |
| `--newest-first` | Reverse the order. |
| `--fail-if-older-than AGE` | Exit with status 1 if anything is older than `AGE`. Useful in CI. |
| `--repo-url URL` | In Markdown output, link each location to its line on GitHub. |
| `-C DIR` | Run in another directory. |

## How it works

1. `git grep` finds lines containing a marker in tracked and untracked files. It skips binary files and anything in `.gitignore`.
2. A marker must be a whole word in uppercase, so `todo_list` and `TODOS` don't count.
3. `git blame` runs once per file, only on the matching lines, to get each line's author and date. Whitespace-only changes are ignored, so reformatting doesn't reset a TODO's age.
4. Lines you haven't committed yet show as `new` with the author `(uncommitted)`.

Nothing leaves your machine. `todo-age` only reads your local repository.

## Use it in GitHub Actions

Add a summary of the oldest markers to every run, and optionally fail the build when something gets too old:

```yaml
- uses: actions/checkout@v7
  with:
    fetch-depth: 0            # full history, so the ages are correct
- uses: nicoleyangcoding/todo-age@v0
  with:
    limit: 20
    fail-if-older-than: 2y    # optional
```

The report appears on the workflow run's summary page.

## Contributing

Bug reports and small pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [roadmap](ROADMAP.md).

## License

[MIT](LICENSE)
