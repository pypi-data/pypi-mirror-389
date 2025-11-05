# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]
 Planned improvements for next release:

- Update and refine more docstrings
- Additional examples in README
- Possible bump to release 0.1.0

---

## [0.0.4] - 2025-11-05

- Fixed bug: auto inverted boolean field did not change value when source-field
             was modified to a new value
- Fixed bug: examples/demo-files -> show_vars() -> inspect_vars()
- Fixed bug: Config.from_dict() raised error during validation in case of min/max
             validation. The method starts now a transaction/commit to postpone
             validations.
- Added and updates docstrings
- Added more pytests
- 100% test coverage (219 passed)
- Modified pyproject.toml to point correct location of this file

---

## [0.0.3] - 2025-10-25
- Many internal improvements, tests, high coverage
- API stable
- Docs not yet updated

### Added
- Unit tests expanded to ~200 tests with 99% coverage
- Core API in `konvigius/core/` for processing data
- `get_changelog()` function to access changelog programmatically
- Unit tests with coverage
- Linting setup with `black`, `ruff`, and `pyright`

### Fixed
- N/A

### Changed
- Internal logic and implementation updated, but API remains unchanged

### Notes
- API interface remains fully compatible with 0.0.1
- Docstrings are still not fully updated; full documentation update planned for next release

---

## [0.0.1] - 2025-10-22
Initial release.

### Added
- Initial release of `konvigius` package

### Fixed
- N/A for first release

### Changed
- N/A for first release
