# Roadmap

Small, focused releases. Suggestions are welcome in [issues](https://github.com/nicoleyangcoding/todo-age/issues).

## 0.2
- [ ] `--by-author`: a summary table of marker counts and median age per person
- [x] `--exclude` option for paths like `vendor/` or generated code
- [ ] Optional config in `pyproject.toml` (`[tool.todo-age]`) for tags and excludes

## 0.3
- [ ] Monthly GitHub Action recipe that opens or updates an issue with the oldest markers
- [ ] Badge endpoint showing the median TODO age
- [ ] Show the issue number when a marker references one, like `TODO(#123)`

## Later
- [ ] `--since <commit>`: only markers added after a given commit, for pull request checks
- [ ] Publish to PyPI so `pipx install todo-age` works
