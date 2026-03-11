<a id="changelog-top"></a>

<div align="center">
  <h1>Changelog</h1>

  <h3>All notable changes to ghlang</h3>

</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#v242--bugfix--cleanup">v2.4.2</a></li>
    <li><a href="#v241--tokount">v2.4.1</a></li>
    <li><a href="#v234--faster-github-processing">v2.3.4</a></li>
    <li><a href="#v233--small--fixes">v2.3.3</a></li>
    <li><a href="#v232--community-themes">v2.3.2</a></li>
    <li><a href="#v231--bugfix--theme-support">v2.3.1</a></li>
    <li><a href="#v230--pypi--simplified-config">v2.3.0</a></li>
    <li><a href="#v220--rich-logging--config-validation">v2.2.0</a></li>
    <li><a href="#v210--themes--svg-export">v2.1.0</a></li>
    <li><a href="#v205--reliability--symlinks">v2.0.5</a></li>
    <li><a href="#v204--config-command">v2.0.4</a></li>
    <li><a href="#v203--pipeline-friendly">v2.0.3</a></li>
    <li><a href="#v202--custom-titles--output">v2.0.2</a></li>
    <li><a href="#v201--typer-swap">v2.0.1</a></li>
    <li><a href="#v200--local-mode--big-refactor">v2.0.0</a></li>
    <li><a href="#v100--initial-release">v1.0.0</a></li>
  </ol>
</details>

## v2.4.2 — Bugfix & cleanup

Patch release fixing a crash in `ghlang local` and cleaning up CI.

**Fixed:**

- `ghlang local` crashing with `'int' object has no attribute 'get'` when tokount output includes metadata keys (`gitRepos`, `gitignorePatterns`)

**Changed:**

- Removed automated AUR publishing from CI (now manual)
- Use relative imports for same-package siblings
- Added `.editorconfig` and `.prettierrc` for consistent formatting
- Consolidated all magic constants into `ghlang/constants.py`
- Lazy-load `matplotlib`/`PIL` in CLI to speed up shell tab completion (~3x faster autocomplete path)
- Added `from __future__ import annotations` for Python 3.11–3.13 compatibility
- Added autocomplete tests for `format_autocomplete` and `themes_autocomplete`

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.4.1 — Tokount

Introducing [`tokount`](https://github.com/MihaiStreames/tokount), a small Rust tool that counts lines of code.

**New stuff:**

- `tokount`, providing a nice 42x speedup in line counting
- Automated AUR publishing on release

**Improved:**

- Refactored most of the Python code (especially `cli`)
- Extracted duplicated code out of `github` / `local`
- Centralized setting up cli environment & error handling
- Better exception handling via `tokount`, errors are propagated via JSON

**Changed:**

- Replaced `cloc_client` with `tokount_client`
- `config` uses `tokount` instead of `cloc`, deprecation warning added
- Swapped `build` with `hatchling` as it's more modern

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.3.4 — Faster GitHub processing

GitHub language data now fetches way faster using concurrent requests.

**Improved:**

- Added concurrent processing for GitHub repository language data (~10x speedup using `ThreadPoolExecutor` with 10 workers)

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.3.3 — Small fixes

**Fixed:**

- Skip cloc `_summary` entries when merging multi-path stats
- Avoid malformed or colliding JSON filenames for local multi-path output
- Configure logging before config load so config messages aren't lost
- Validate repo names and improve GitHub API error handling

**New stuff:**

- Analyze specific GitHub repos by passing `owner/repo` arguments (#12 and #11)
- Analyze multiple local paths in a single command (#8)

**Improved:**

- Reduced chart saving duplication with a shared save helper
- Refactored `local()` and `get_all_language_stats()` to reduce complexity

**Changed:**

- Dependency updates: `pillow`, `rich`, `typer`

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.3.2 — Community themes

Community theme system is now fully functional. Monokai moved from built-in to community theme.

**Changed:**

- Moved `monokai` theme from built-in to community (fetched from GitHub manifest)
- Charts now automatically load built-in + remote + custom themes
- Only `light` and `dark` remain as built-in themes

**New stuff:**

- Created `themes/manifest.json` for community themes
- Community themes auto-fetch with 1-day cache
- Added contribution guide in `themes/README.md`

**Improved:**

- Simplified theme system architecture
- Themes can now be added without releasing new versions

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.3.1 — Bugfix & theme support

Critical bugfix for `ghlang config show` and basic *community* theme system support.

**Fixed:**

- **Critical:** Removed references to deleted config fields (`save_json`, `save_repos`, `top_n_languages`) in `config show` command that would cause errors

**New stuff:**

- Theme autocomplete in CLI
- Community theme manifest support (auto-cached, 1-day TTL)
- Custom themes via `~/.config/ghlang/custom_themes.json`

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.3.0 — PyPI & simplified config

Now available on [PyPI](https://pypi.org/project/ghlang/)! Install with `pipx install ghlang` or `pip install ghlang`. Simplified config and added GitHub automation.

**New stuff:**

- Published to PyPI, no more installing from source
- `--save-json` flag to control JSON file generation (replaces config options)
- GitHub Actions workflow for automated PyPI releases on tags
- GitHub issue templates for bug reports and feature requests

**Changed:**

- Removed `save_json`, `save_repos`, and `top_n_languages` from config file
- These settings are now CLI flags only (`--save-json`, `--top-n`)
- Simplified config structure
- Clean script now removes `dist/` directory

**Improved:**

- Easier installation experience via package managers
- More flexible per-command control vs global config

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.2.0 — Rich logging & config validation

Replaced loguru with [Rich](https://github.com/Textualize/rich) for better progress bars and unified console output. Added config validation with helpful suggestions for typos.

**New stuff:**

- Progress bars for GitHub repo fetching and processing
- Spinner for cloc analysis
- Progress bar for chart generation
- Config validation warns about unknown keys with fuzzy matching ("did you mean...?")
- `monokai` chart theme
- Syntax highlighting for `ghlang config --raw`

**Changed:**

- Replaced loguru with Rich for all logging and progress display
- Logging now uses text-only style with colored level labels (INFO, SUCCESS, WARNING, ERROR)
- `--quiet` suppresses all output except errors
- `--stdout` outputs clean JSON only (no progress bars)
- `-v` enables debug messages

**Improved:**

- Better visual feedback during long-running operations
- Friendlier config error messages with typo suggestions

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.1.0 — Themes & SVG export

Theme support and SVG output for better customization.

**New stuff:**

- `--theme` flag to choose chart color schemes
  - Built-in themes: `light` (default), `dark`
  - Configurable via `preferences.theme` in config
- `--format` / `-f` flag for output format
  - Support for PNG (default) and SVG
  - Priority: `--format` > `--output` extension > default png
- Rounded corners on PNG charts
- Theme-aware fallback colors for languages without GitHub linguist equivalents

**Changed:**

- Pillow used for adding rounded corners to PNGs
- Refactored static data: `lang_mapping.py` now uses Python dicts instead of JSON
- All chart styling constants moved to top of `visualizers.py` for easy customization
- Language normalization: languages without linguist mapping now use original name with fallback color instead of being excluded

**Improved:**

- Cleaner constant organization for maintainability
- User-friendly warnings for invalid themes and unsupported formats

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.0.5 — Reliability & symlinks

Better rate limit handling and symlink support for local mode.

**New stuff:**

- `--follow-links` flag for local mode to follow symlinks (unix only)
- Rate limit info shown in verbose mode (`Rate limit: X/Y remaining`)
- Dev dependencies for type checking (`types-requests`, `types-PyYAML`)

**Improved:**

- GitHub API rate limiting now uses exponential backoff for 429/5xx errors
- Retries up to 5 times with increasing delays before failing
- Internal code cleanup: private attributes/methods where appropriate

**Fixed:**

- Various mypy type errors resolved

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.0.4 — Config command

New `ghlang config` command for managing your config file.

**New stuff:**

- `ghlang config` opens config in your default editor
- `ghlang config --show` prints config as a formatted table
- `ghlang config --path` prints the config file path
- `ghlang config --raw` prints raw TOML contents

**Changed:**

- CLI refactored into `ghlang/cli/` package for better organization

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.0.3 — Pipeline friendly

New flags for scripting and CI/CD workflows.

**New stuff:**

- `--json-only` flag to skip chart generation and just output JSON
- `--stdout` flag to output stats to stdout (perfect for piping to jq)
- `--quiet` / `-q` flag to suppress log output

**Notes:**

- `--stdout` implies both `--json-only` and `--quiet`
- Great for CI pipelines, scripts, and custom visualizations

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.0.2 — Custom titles & output

New CLI flags for more control over your charts.

**New stuff:**

- `--title` / `-t` flag to set a custom chart title
- `--output` / `-o` flag to specify custom output filename (creates `_pie` and `_bar` variants)
- Dynamic chart titles: GitHub mode shows "GitHub Language Stats", local mode shows "Local: {folder}"

**Changed:**

- `--output-dir` no longer has `-o` shorthand (now used by `--output`)

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.0.1 — Typer swap

Swapped Click for [Typer](https://typer.tiangolo.com/). Same functionality, but now with:

- Built-in shell completion (`ghlang --install-completion`)
- Nicer help output with colors and tables

**New stuff:**

- GitHub Actions workflow for automatic releases

**Changed:**

- Dropped `click` as a direct dependency (Typer uses it internally anyway)

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v2.0.0 — Local mode & big refactor

Big update. You can now analyze local files, not just GitHub repos.

**New stuff:**

- `ghlang local` command using [cloc](https://github.com/AlDanial/cloc)
- Ignore repos with patterns (`org/*`, full URLs)
- Ignore directories in local mode
- Default config bundled in the package

**Changed:**

- CLI now uses Click groups (`github`, `local` subcommands)
- Config system overhauled: `Config` dataclass, platform-specific paths
- Visualizers cleaned up: better legends, layout fixes
- README completely rewritten

**Fixed:**

- Console script entry point works with pipx now

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

## v1.0.0 — Initial release

First version. GitHub-only.

- `GitHubClient` to fetch repos and aggregate language stats
- Pie and bar charts with GitHub's linguist colors
- Config via `config.toml`
- Filter by repo affiliation and visibility
- MIT License

<p align="right">(<a href="#changelog-top">back to top</a>)</p>

---

<div align="center">
  <p>Back to <a href="README.md">README</a>?</p>
</div>
