# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [0.4.0] - 2026-11-19

### Added
- `--by-author` prints one row per person with their marker count, median age and oldest marker, most markers first. It works with every output format and with the usual filters, and `--limit` caps the number of authors.

## [0.3.0] - 2026-11-15

### Added
- Issue references right after a marker, like `TODO(#123)`, `FIXME(dana, #45)` or `TODO #123:`, are picked up. JSON and CSV output get an `issue` field (a new last column in CSV), and Markdown output links the number to the issue when `--repo-url` is set.

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
