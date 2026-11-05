# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-11-05

### Added
- `--exclude PATH` skips files or folders, like `vendor/` or `*.min.js`. Repeat it to exclude several.

## [0.1.0] - 2026-10-29

### Added
- Find TODO, FIXME, HACK and XXX markers with `git grep`, and date each line with `git blame`
- Filters: `--older-than`, `--author`, `--tags`, paths, `--limit`
- Output formats: table, Markdown (with GitHub links), JSON, CSV
- `--fail-if-older-than` for CI
- GitHub Action that writes a report to the job summary
