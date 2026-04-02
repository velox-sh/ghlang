<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<div align="center">

[![Stars](https://img.shields.io/github/stars/velox-sh/ghlang?style=social)](https://github.com/velox-sh/ghlang/stargazers)
[![PyPI](https://img.shields.io/pypi/v/ghlang?label=PyPI)](https://pypi.org/project/ghlang/)
[![AUR Version](https://img.shields.io/aur/version/python-ghlang?label=AUR)](https://aur.archlinux.org/packages/python-ghlang)
[![Python Version](https://img.shields.io/pypi/pyversions/ghlang?label=Python)](https://pypi.org/project/ghlang/)
[![codecov](https://codecov.io/gh/velox-sh/ghlang/graph/badge.svg)](https://codecov.io/gh/velox-sh/ghlang)
[![Downloads](https://img.shields.io/pypi/dm/ghlang?label=Downloads)](https://pypi.org/project/ghlang/)
[![License](https://img.shields.io/github/license/velox-sh/ghlang?label=License)](LICENSE)

</div>

<!-- PROJECT LOGO -->
<div align="center">
  <img src="assets/ghlang-icon.svg" alt="ghlang logo" width="120" />

  <h1>ghlang</h1>

  <h3 align="center">Visualize your GitHub language stats, blazingly fast. </h3>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#shell-completion">Shell Completion</a></li>
    <li><a href="#configuration">Configuration</a></li>
    <li><a href="#output">Output</a></li>
    <li><a href="#themes">Themes</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project

Ever wondered what languages you actually use? **ghlang** makes pretty charts to show you:

<div align="center">
  <img src="https://raw.githubusercontent.com/velox-sh/ghlang/master/assets/example_pixel.png" alt="Pixel chart example" width="40%" />
  <p><i>isometric pixel tower - the default style</i></p>
</div>

<div align="center">
  <img src="https://raw.githubusercontent.com/velox-sh/ghlang/master/assets/example_pie.png" alt="Pie chart example" width="50%" />
  <img src="https://raw.githubusercontent.com/velox-sh/ghlang/master/assets/example_bar.png" alt="Bar chart example" width="50%" />
  <p><i>pie and bar styles - all from my actual GitHub repos</i></p>
</div>

- **GitHub mode**: Pulls stats from all your repos via the API (counts bytes)
- **Local mode**: Analyzes files on your machine using [tokount](https://github.com/velox-sh/tokount) (counts lines)

### Why ghlang?

Unlike tools like [github-readme-stats](https://github.com/anuraghazra/github-readme-stats) (which generate SVG cards for your README), ghlang is a **CLI tool** that:

- Runs locally on your machine (Python-based)
- Analyzes local files, not just GitHub repos
- Generates downloadable charts (PNG/SVG) you can use anywhere
- Exports raw JSON data for further analysis
- Works offline for local analysis
- Gives you full control over the data

If you want embedded GitHub stats for your README, use github-readme-stats. If you want to analyze your actual codebase and generate charts you can save, share, or customize, use ghlang.

(that said, ghlang does support SVG output with `--format svg`, so you can totally embed your charts in READMEs too - would be cool to see people do that!)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

- [Python](https://www.python.org/)
- [Typer](https://typer.tiangolo.com/)
- [Matplotlib](https://matplotlib.org/)
- [Pillow](https://python-pillow.org/)
- [Requests](https://requests.readthedocs.io/)
- [Rich](https://github.com/Textualize/rich)
- [tokount](https://github.com/velox-sh/tokount) (for local analysis)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

Getting this running is pretty straightforward.

### Prerequisites

- Python 3.10+
- For GitHub mode: a GitHub token
- For local mode: [`tokount`](https://github.com/velox-sh/tokount)

### Installation

```bash
# with pipx (recommended)
pipx install ghlang

# or with pip
pip install ghlang

# or with yay (AUR)
yay -S python-ghlang

# or with paru (AUR)
paru -S python-ghlang

# or install from source
pip install git+https://github.com/velox-sh/ghlang.git
```

For local mode, you'll also need [`tokount`](https://github.com/velox-sh/tokount):

```bash
# with cargo
cargo install tokount

# or with yay (AUR)
yay -S tokount

# or with paru (AUR)
paru -S tokount
```

### Setting Up GitHub Mode

1. **Get a token** from [GitHub Settings](https://github.com/settings/tokens)

   - Pick `repo` for private repos, or just `public_repo` for public only

2. **Run it once** to create the config file:

   ```bash
   ghlang github
   ```

   Config lives at `~/.config/ghlang/config.toml` (or `%LOCALAPPDATA%\ghlang\config.toml` on Windows)

3. **Add your token** to the config:

   ```toml
   [github]
   token = "ghp_your_token_here"
   ```

4. **Run it again** and you're good:

   ```bash
   ghlang github
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

## Usage

### All the Flags

Both `github` and `local` commands share the same options:

| Flag           | Short | What it does                                                |
| -------------- | ----- | ----------------------------------------------------------- |
| `--config`     |       | use a different config file                                 |
| `--output-dir` |       | where to save the charts (directory)                        |
| `--output`     | `-o`  | custom output filename (creates `_<style>` variant)         |
| `--title`      | `-t`  | custom chart title                                          |
| `--style`      | `-s`  | chart style: `pixel` (default), `pie`, or `bar`             |
| `--top-n`      |       | how many languages to show (default: 6)                     |
| `--save-json`  |       | save raw stats as JSON files                                |
| `--theme`      |       | chart color theme (default: light)                          |
| `--json-only`  |       | output JSON only, skip chart generation                     |
| `--stdout`     |       | output stats to stdout (implies `--json-only --quiet`)      |
| `--quiet`      | `-q`  | suppress log output (only show errors)                      |
| `--verbose`    | `-v`  | show more details                                           |

The `local` command also takes an optional `[PATH]` argument (defaults to `.`) and has one extra flag:

| Flag             | Short | What it does                               |
| ---------------- | ----- | ------------------------------------------ |
| `--follow-links` | `-L`  | follow symlinks when analyzing (unix only) |

The `config` command has its own options:

| Flag     | What it does                    |
| -------- | ------------------------------- |
| `--show` | print config as formatted table |
| `--path` | print config file path          |
| `--raw`  | print raw TOML contents         |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- SHELL COMPLETION -->

## Shell Completion

ghlang has built-in shell completion. To enable it:

```bash
# install completion for your shell
ghlang --install-completion

# or just view the completion script
ghlang --show-completion
```

After installing, restart your shell or source your config file.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- OUTPUT -->

## What You Get

Charts end up in your output directory as `.png`:

| File                    | What it is                                               |
| ----------------------- | -------------------------------------------------------- |
| `language_pixel.png`    | pixel tower chart (default style)                        |
| `language_pie.png`      | pie chart with all languages (`--style pie`)             |
| `language_bar.png`      | bar chart with top N languages (`--style bar`)           |
| `language_stats.json`   | raw stats (with `--save-json`)                           |
| `tokount_stats.json`    | detailed tokount output (local mode, with `--save-json`) |
| `repositories.json`     | list of repos analyzed (GitHub mode, with `--save-json`) |
| `github_colors.json`    | language colors from GitHub (with `--save-json`)         |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONFIGURATION -->

## Config Options

Everything lives in `config.toml`:

### `[github]`

| Option          | Default                                    | What it does                                                     |
| --------------- | ------------------------------------------ | ---------------------------------------------------------------- |
| `token`         | -                                          | your GitHub token                                                |
| `affiliation`   | `"owner,collaborator,organization_member"` | which repos to include                                           |
| `visibility`    | `"all"`                                    | `all`, `public`, or `private`                                    |
| `ignored_repos` | `[]`                                       | repos to skip (e.g. `"org/*"`, `"https://github.com/user/repo"`) |

### `[tokount]`

| Option         | Default                           | What it does        |
| -------------- | --------------------------------- | ------------------- |
| `ignored_dirs` | `["node_modules", "vendor", ...]` | directories to skip |

### `[output]`

| Option      | Default                      | What it does         |
| ----------- | ---------------------------- | -------------------- |
| `directory` | `"~/Documents/ghlang-stats"` | where to save charts |

### `[preferences]`

| Option    | Default   | What it does      |
| --------- | --------- | ----------------- |
| `verbose` | `false`   | more logging      |
| `theme`   | `"light"` | chart color theme |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- THEMES -->

## Themes

ghlang comes with built-in themes and supports community themes:

| Theme     | Preview                                                                                             | Source    |
| --------- | --------------------------------------------------------------------------------------------------- | --------- |
| `light`   | ![light](https://raw.githubusercontent.com/velox-sh/ghlang/master/assets/themes/light.png)          | built-in  |
| `dark`    | ![dark](https://raw.githubusercontent.com/velox-sh/ghlang/master/assets/themes/dark.png)            | built-in  |
| `monokai` | ![monokai](https://raw.githubusercontent.com/velox-sh/ghlang/master/assets/themes/monokai.png)      | community |

**Using themes:**

```bash
# use a theme
ghlang github --theme dark

# combine with a style
ghlang github --theme dark --style pie
```

**Set default in `config.toml`:**

```toml
[preferences]
theme = "dark"
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->

## License

MIT. Do whatever you want with it. See [LICENSE](LICENSE) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<div align="center">

Made with ❤️

</div>
