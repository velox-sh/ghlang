# ghlang

ghlang generates pretty charts for your GitHub language stats from either the GitHub API (bytes) or local files via [`tokount`](https://github.com/MihaiStreames/tokount) (lines). Ships as a Python CLI with a few chart styles (`pixel`, `pie`, `bar`), community themes, PNG/SVG output, and raw JSON export.

[![ghlang](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/MihaiStreames/ghlang/master/assets/badge.json)](https://github.com/MihaiStreames/ghlang)
[![PyPI](https://img.shields.io/pypi/v/ghlang?label=pypi)](https://pypi.org/project/ghlang/)
[![AUR](https://img.shields.io/aur/version/python-ghlang?label=AUR)](https://aur.archlinux.org/packages/python-ghlang)
[![CI](https://github.com/MihaiStreames/ghlang/actions/workflows/ci.yml/badge.svg)](https://github.com/MihaiStreames/ghlang/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/MihaiStreames/ghlang)](LICENSE)

<p align="center">
  <img src="https://raw.githubusercontent.com/MihaiStreames/ghlang/master/assets/example_pixel.png" height="360" alt="pixel style" />
  <img src="https://raw.githubusercontent.com/MihaiStreames/ghlang/master/assets/example_pie.png" height="360" alt="pie style" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/MihaiStreames/ghlang/master/assets/example_bar.png" width="75%" alt="bar style" />
</p>

<p align="center">
  <i>My language stats across all my repos.</i>
</p>

## About

Originally a small `matplotlib` script to learn how [`github-readme-stats`](https://github.com/anuraghazra/github-readme-stats) worked. A friend asked for local mode, so I added it (first with `cloc`, then with my own line counter, [`tokount`](https://github.com/MihaiStreames/tokount)). (`tokount` ended up taking over most of my time, and now ghlang is back on the bench haha)

Unlike github-readme-stats (serverless SVG cards) or [`github-stats`](https://github.com/jstrieb/github-stats) (Actions-generated SVGs), ghlang runs locally and gives you both: downloadable PNGs you can save/share, and `--format svg` for embedding.

## Table of contents

- [Install](#install)
- [Setup](#setup)
- [Usage](#usage)
- [Shell completion](#shell-completion)
- [Output](#output)
- [Config](#config)
- [Themes](#themes)
- [License](#license)

## Install

### pipx (recommended)

```sh
pipx install ghlang
```

### pip

```sh
pip install ghlang
```

### AUR

```sh
yay -S python-ghlang
paru -S python-ghlang
```

### From source

```sh
pip install git+https://github.com/MihaiStreames/ghlang.git
```

For `ghlang local`, install [tokount](https://github.com/MihaiStreames/tokount):

```sh
cargo install tokount
yay -S tokount
```

## Setup

GitHub mode needs a token. Get one from [GitHub Settings](https://github.com/settings/tokens) with `repo` (private) or `public_repo` (public only).

Run `ghlang github` once to create the config at `~/.config/ghlang/config.toml` (or `%LOCALAPPDATA%\ghlang\config.toml` on Windows), then add your token:

```toml
[github]
token = "ghp_your_token_here"
```

Run `ghlang github` again. That's it.

## Usage

```sh
ghlang github                         # chart from GitHub API
ghlang local                          # chart from current directory
ghlang local src/ tests/              # multiple paths
ghlang github --style pie             # pie chart
ghlang local --theme dark             # dark theme
ghlang github --save-json             # also dump raw JSON
ghlang github --stdout                # pipe JSON to jq
ghlang config                         # open config in $EDITOR
ghlang theme --list                   # list themes
```

Both `github` and `local` share the same flags:

| Flag           | Short | Description                                     |
| -------------- | ----- | ----------------------------------------------- |
| `--config`     |       | use a different config file                     |
| `--output-dir` |       | where to save charts                            |
| `--output`     | `-o`  | custom output filename (adds `_<style>` suffix) |
| `--title`      | `-t`  | custom chart title                              |
| `--style`      | `-s`  | `pixel` (default), `pie`, `bar`                 |
| `--top-n`      |       | languages to show (default: 6)                  |
| `--save-json`  |       | save raw stats as JSON                          |
| `--theme`      |       | chart color theme (default: `light`)            |
| `--json-only`  |       | output JSON only, skip charts                   |
| `--stdout`     |       | JSON to stdout (implies `--json-only --quiet`)  |
| `--quiet`      | `-q`  | suppress log output                             |
| `--verbose`    | `-v`  | show debug details                              |

`local` also accepts a `[PATH]` argument (default `.`) and:

| Flag             | Short | Description                 |
| ---------------- | ----- | --------------------------- |
| `--follow-links` | `-L`  | follow symlinks (unix only) |

`config` subcommand:

| Flag     | Description             |
| -------- | ----------------------- |
| `--show` | print config as table   |
| `--path` | print config file path  |
| `--raw`  | print raw TOML contents |

Running `ghlang config` with no flags opens the file in `$EDITOR`.

`theme` subcommand:

| Flag        | Description                                |
| ----------- | ------------------------------------------ |
| `--list`    | list available themes                      |
| `--info`    | show details for a specific theme          |
| `--refresh` | force-refresh remote themes (bypass cache) |

## Shell completion

```sh
ghlang --install-completion     # install for current shell
ghlang --show-completion        # print completion script
```

## Output

Charts land in `output-dir` as `.png` (or `.svg`):

| File                  | Description                                          |
| --------------------- | ---------------------------------------------------- |
| `language_pixel.png`  | isometric pixel-tower chart (default style)          |
| `language_pie.png`    | pie chart (`--style pie`)                            |
| `language_bar.png`    | bar chart, top N (`--style bar`)                     |
| `language_stats.json` | raw stats (with `--save-json`)                       |
| `tokount_stats.json`  | detailed tokount output (local mode, `--save-json`)  |
| `repositories.json`   | list of repos analyzed (GitHub mode, `--save-json`)  |
| `github_colors.json`  | language colors from GitHub linguist (`--save-json`) |

## Config

Everything lives in `config.toml`:

### `[github]`

| Option          | Default                                    | Description                                                      |
| --------------- | ------------------------------------------ | ---------------------------------------------------------------- |
| `token`         | -                                          | GitHub token                                                     |
| `affiliation`   | `"owner,collaborator,organization_member"` | which repos to include                                           |
| `visibility`    | `"all"`                                    | `all`, `public`, `private`                                       |
| `ignored_repos` | `[]`                                       | repos to skip (e.g. `"org/*"`, `"https://github.com/user/repo"`) |

### `[tokount]`

| Option         | Default                           | Description         |
| -------------- | --------------------------------- | ------------------- |
| `ignored_dirs` | `["node_modules", "vendor", ...]` | directories to skip |

### `[output]`

| Option      | Default                      | Description          |
| ----------- | ---------------------------- | -------------------- |
| `directory` | `"~/Documents/ghlang-stats"` | where to save charts |

### `[preferences]`

| Option    | Default   | Description       |
| --------- | --------- | ----------------- |
| `verbose` | `false`   | more logging      |
| `theme`   | `"light"` | chart color theme |

## Themes

Built-in: `light`, `dark`. Community themes auto-fetch from `themes/manifest.json` (1-day cache). Custom themes via `~/.config/ghlang/custom_themes.json`.

| Theme     | Preview                                                                                             | Source    |
| --------- | --------------------------------------------------------------------------------------------------- | --------- |
| `light`   | ![light](https://raw.githubusercontent.com/MihaiStreames/ghlang/master/assets/themes/light.png)     | built-in  |
| `dark`    | ![dark](https://raw.githubusercontent.com/MihaiStreames/ghlang/master/assets/themes/dark.png)       | built-in  |
| `monokai` | ![monokai](https://raw.githubusercontent.com/MihaiStreames/ghlang/master/assets/themes/monokai.png) | community |

Contributing a theme: see [`themes/README.md`](themes/README.md).

## License

MIT. See [LICENSE](LICENSE).

<div align="center">
  Made with ❤️
</div>
