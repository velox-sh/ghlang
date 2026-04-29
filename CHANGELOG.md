# Changelog

All notable changes to this project.

## [2.5.5] - 2026-04-09

### Fixed

- Thread-safe HTTP connections via per-thread `HTTPSConnection` reuse (`threading.local`); concurrent language fetches were failing with `Request-sent` errors under a shared connection
- Request timeout lowered from 30s to 10s so throttled requests fail fast
- Pie chart percentage label threshold lowered from 5.0% to 2.0%

## [2.5.4] - 2026-04-09

### Fixed

- `ghlang github` returning 403 after the `requests` → `http.client` swap in v2.5.2; missing `User-Agent` header restored

## [2.5.3] - 2026-04-07

### Changed

- Replaced `pyyaml` with a targeted regex parser for linguist YAML (85x faster, 457ms → 5ms)

### Security

- Pygments bumped to 2.20.0 (ReDoS vulnerability in `AdlLexer`)

## [2.5.2] - 2026-04-07

### Added

- `net/` package: `client.py` (HTTP with connection reuse), `github.py` (API client), `linguist.py` (color fetch)
- `ghlang/utils.py` for shared utilities (`save_json`, `get_config_dir`, `get_active_theme`, `load_themes_by_source`)

### Changed

- Replaced `requests` with stdlib `urllib` / `http.client`; one fewer dependency
- `http.client` connection reuse in `Session` (2x faster than `requests` per request)
- Orchestration (threading, progress bars, JSON saving) moved from network layer to `cli/github.py`
- Merged `languages.py` + `static/lang_mapping.py` into `static/languages.py`
- Split `cli/utils.py`: general utilities to `ghlang/utils.py`, CLI-specific helpers stay

### Removed

- Retry / rate-limit / backoff logic in HTTP client (overkill for a CLI)
- `save_json_stats` wrapper (callers use `utils.save_json` directly)

## [2.5.1] - 2026-04-06

### Changed

- Lazy `requests` import in `github_client`, `colors`, `themes` (-141 ms)
- Lazy `rich.console` and `rich.progress` in `log.py` (-14 ms)
- Lazy command registration via `LazyGroup`; command modules only imported when invoked
- Pre-existing in-function imports moved to module level (`LazyGroup` defers the entire module)
- Startup: 480 ms → 183 ms (`--version`), 103 ms bare import cost

### Fixed

- Redundant `# noqa: PLC0415` inline suppressions removed (rule already globally disabled)

## [2.5.0] - 2026-04-02

### Added

- `--style` / `-s` flag on `github` and `local` commands; choose between `pixel` (default), `pie`, and `bar`
- `pixel` chart style: isometric tower chart with Cozette bitmap font, per-language color blocks, segment connectors
- Style registry: each style is self-contained and discovered dynamically via `get_style_registry()`
- Shell autocomplete for `--style`
- Benchmark scripts (`scripts/benchmark.sh`) for import profiling, startup timing, chart generation

### Changed

- Module restructure: `styles/` for chart rendering, `display/` for Rich console output, `cli/charts.py` for chart orchestration
- Extracted `colors.py` (linguist color loading), `languages.py` (tokount name normalization); `get_theme()` moved to `themes.py`
- `styles/` is now a pure rendering layer; no network IO, no config dependencies
- Adopted Google/Django module-import convention; all internal imports are module imports
- Renamed `logging.py` to `log.py` to avoid stdlib collision
- NumPy-style docstrings on all public functions and classes
- `build_display_segments()` shared utility; `top_n` and hide threshold applied consistently across all styles
- "Other" aggregate now uses theme fallback color in all styles (was inconsistent between pie/bar)
- Pie chart shows all languages regardless of `top_n`; only hides percentage label text below threshold

## [2.4.6] - 2026-04-01

### Changed

- Minimum Python lowered from 3.11 to 3.10
- Added `tomli` backport for `tomllib` on Python 3.10

## [2.4.5] - 2026-04-01

### Added

- `ghlang theme` command with `--list`, `--refresh`, `--info <name>` (#20)

### Fixed

- `tokount` CLI flags updated for v2.1.6 compat (`-o json`, `-e`)
- Various mypy type errors

## [2.4.4] - 2026-03-12

### Changed

- `tokount_client`: pass `--json` flag explicitly (tokount now outputs a human-readable table by default)
- `tokount_client`: excluded dirs passed as `--excluded <DIRS>` named flag (was positional)
- `local`: `--follow-links` now has `-L` short alias; blocked on Windows

## [2.4.3] - 2026-03-11

### Fixed

- Include `tests/**` in the sdist via `pyproject.toml`

## [2.4.2] - 2026-03-11

### Fixed

- `ghlang local` crashing with `'int' object has no attribute 'get'` when tokount output includes metadata keys (`gitRepos`, `gitignorePatterns`)

### Changed

- Relative imports for same-package siblings
- All magic constants consolidated into `ghlang/constants.py`
- Lazy-load `matplotlib` / `PIL` in CLI so shell tab completion is ~3x faster
- `from __future__ import annotations` added for Python 3.11-3.13 compatibility
- Autocomplete tests for `format_autocomplete` and `themes_autocomplete`

## [2.4.1] - 2026-01-15

### Added

- [`tokount`](https://github.com/MihaiStreames/tokount) integration; ~42x speedup in line counting
- Centralized CLI environment setup and error handling
- Structured error propagation from tokount via JSON

### Changed

- Replaced `cloc_client` with `tokount_client`
- `config` uses `tokount` instead of `cloc` (deprecation warning added)
- Swapped `build` for `hatchling`

## [2.3.4] - 2026-01-11

### Changed

- Concurrent GitHub repository language fetching via `ThreadPoolExecutor` (10 workers, ~10x speedup)

## [2.3.3] - 2026-01-11

### Added

- Analyze specific GitHub repos by passing `owner/repo` arguments (#11, #12)
- Analyze multiple local paths in a single command (#8)

### Fixed

- Skip cloc `_summary` entries when merging multi-path stats
- Avoid malformed or colliding JSON filenames for local multi-path output
- Configure logging before config load so config messages aren't lost
- Validate repo names; better GitHub API error handling

### Changed

- Shared save helper reduces chart-saving duplication
- `local()` and `get_all_language_stats()` refactored for lower complexity
- Dependency updates: `pillow`, `rich`, `typer`

## [2.3.2] - 2025-12-31

### Added

- `themes/manifest.json` for community themes
- Community themes auto-fetch with 1-day cache
- Theme contribution guide in `themes/README.md`

### Changed

- `monokai` moved from built-in to community (fetched from GitHub manifest)
- Charts load built-in + remote + custom themes automatically
- Only `light` and `dark` remain as built-in themes
- Themes can be added without releasing new versions

## [2.3.1] - 2025-12-31

### Added

- Theme autocomplete in CLI
- Community theme manifest support (auto-cached, 1-day TTL)
- Custom themes via `~/.config/ghlang/custom_themes.json`

### Fixed

- `config show` crashing on references to deleted fields (`save_json`, `save_repos`, `top_n_languages`)

## [2.3.0] - 2025-12-30

### Added

- `--save-json` flag to control JSON file generation (replaces config options)
- Published to [PyPI](https://pypi.org/project/ghlang/); `pipx install ghlang` / `pip install ghlang`

### Changed

- `save_json`, `save_repos`, `top_n_languages` removed from config file; now CLI flags only (`--save-json`, `--top-n`)
- Clean script removes `dist/` directory

## [2.2.0] - 2025-12-30

### Added

- Progress bars for GitHub repo fetching and processing
- Spinner for cloc analysis
- Progress bar for chart generation
- Config validation warns about unknown keys with fuzzy matching ("did you mean…?")
- `monokai` chart theme
- Syntax highlighting for `ghlang config --raw`

### Changed

- Replaced `loguru` with [Rich](https://github.com/Textualize/rich) for all logging and progress display
- Logging uses text-only style with colored level labels (INFO, SUCCESS, WARNING, ERROR)
- `--quiet` suppresses all output except errors
- `--stdout` outputs clean JSON only (no progress bars)
- `-v` enables debug messages

## [2.1.0] - 2025-12-30

### Added

- `--theme` flag for chart color schemes; built-in `light` (default) and `dark`; configurable via `preferences.theme`
- `--format` / `-f` flag for output format; PNG (default) and SVG; priority `--format` > `--output` extension > default PNG
- Rounded corners on PNG charts (via Pillow)
- Theme-aware fallback colors for languages without GitHub linguist equivalents

### Changed

- `lang_mapping.py` uses Python dicts instead of JSON
- All chart styling constants moved to top of `visualizers.py`
- Languages without linguist mapping now use original name with fallback color instead of being excluded

## [2.0.5] - 2025-12-30

### Added

- `--follow-links` flag for local mode to follow symlinks (unix only)
- Rate limit info in verbose mode (`Rate limit: X/Y remaining`)
- Dev dependencies `types-requests`, `types-PyYAML`

### Changed

- GitHub API rate limiting uses exponential backoff for 429/5xx; retries up to 5 times
- Private attributes/methods where appropriate

### Fixed

- Various mypy type errors

## [2.0.4] - 2025-12-30

### Added

- `ghlang config` command; opens config in `$EDITOR`
- `ghlang config --show` prints config as a formatted table
- `ghlang config --path` prints the config file path
- `ghlang config --raw` prints raw TOML contents

### Changed

- CLI refactored into `ghlang/cli/` package

## [2.0.3] - 2025-12-30

### Added

- `--json-only` flag to skip chart generation and just output JSON
- `--stdout` flag to output stats to stdout (implies `--json-only --quiet`)
- `--quiet` / `-q` flag to suppress log output

## [2.0.2] - 2025-12-30

### Added

- `--title` / `-t` flag for custom chart title
- `--output` / `-o` flag for custom output filename (creates `_pie` and `_bar` variants)
- Dynamic chart titles: GitHub mode shows "GitHub Language Stats", local mode shows "Local: {folder}"

### Changed

- `--output-dir` no longer has `-o` shorthand (now used by `--output`)

## [2.0.1] - 2025-12-30

### Added

- Built-in shell completion (`ghlang --install-completion`)
- GitHub Actions workflow for automatic releases

### Changed

- Swapped Click for [Typer](https://typer.tiangolo.com/); nicer help output with colors and tables
- Dropped `click` as a direct dependency (Typer uses it internally)

## [2.0.0] - 2025-12-29

### Added

- `ghlang local` command using [cloc](https://github.com/AlDanial/cloc)
- Ignore repos with patterns (`org/*`, full URLs)
- Ignore directories in local mode
- Default config bundled in the package

### Changed

- CLI uses Click groups (`github`, `local` subcommands)
- Config system overhauled: `Config` dataclass, platform-specific paths
- Visualizers cleaned up: better legends, layout fixes
- README completely rewritten

### Fixed

- Console script entry point works with pipx

## [1.0.0] - 2025-12-19

First version. GitHub-only.

### Added

- `GitHubClient` to fetch repos and aggregate language stats
- Pie and bar charts with GitHub linguist colors
- Config via `config.toml`
- Filter by repo affiliation and visibility
