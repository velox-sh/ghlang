from dataclasses import dataclass
from dataclasses import field
from difflib import get_close_matches
from importlib import resources
from pathlib import Path
import sys


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from . import constants
from . import exceptions
from . import log


VALID_KEYS: dict[str, set[str]] = {
    "github": {"token", "affiliation", "visibility", "ignored_repos"},
    "tokount": {"ignored_dirs"},
    "output": {"directory"},
    "preferences": {"verbose", "theme"},
}


@dataclass
class Config:
    """Configuration for the language stats.

    Attributes
    ----------
    token : str
        GitHub personal access token.
    affiliation : str
        Comma-separated repo affiliations (owner, collaborator, organization_member).
    visibility : str
        Repo visibility filter (all, public, private).
    ignored_repos : list[str]
        Glob patterns for repos to skip.
    ignored_dirs : list[str]
        Directory names tokount should skip.
    output_dir : Path
        Directory where charts and JSON files are written.
    verbose : bool
        Enable debug-level log output.
    theme : str
        Name of the chart color theme.
    """

    # GitHub settings
    token: str = ""
    affiliation: str = "owner,collaborator,organization_member"
    visibility: str = "all"
    ignored_repos: list[str] = field(default_factory=list)

    # Tokount settings
    ignored_dirs: list[str] = field(default_factory=lambda: list(constants.DEFAULT_IGNORED_DIRS))

    # Output settings
    output_dir: Path = field(default_factory=lambda: Path(constants.DEFAULT_OUTPUT_DIR))

    # Preferences
    verbose: bool = False
    theme: str = "light"


def _validate_config(data: dict) -> None:
    for section, keys in data.items():
        section_name = section
        if section == "cloc":
            log.logger.warning("Config section 'cloc' is deprecated, use 'tokount' instead")
            section_name = "tokount"

        if section_name not in VALID_KEYS:
            suggestions = get_close_matches(section_name, VALID_KEYS.keys(), n=1, cutoff=0.6)

            if suggestions:
                log.logger.warning(
                    f"Unknown config section '{section}' - did you mean '{suggestions[0]}'?"
                )
            else:
                log.logger.warning(f"Unknown config section '{section}'")
            continue

        if not isinstance(keys, dict):
            continue

        valid = VALID_KEYS[section_name]
        for key in keys:
            if key not in valid:
                suggestions = get_close_matches(key, valid, n=1, cutoff=0.6)

                if suggestions:
                    log.logger.warning(
                        f"Unknown key '{section}.{key}' - did you mean '{suggestions[0]}'?"
                    )
                else:
                    log.logger.warning(f"Unknown config key '{section}.{key}'")


def get_config_path() -> Path:
    """Return the platform-specific config file path.

    Returns
    -------
    Path
        ``~/.config/ghlang/config.toml`` on Unix,
        ``~/AppData/Local/ghlang/config.toml`` on Windows.
    """
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local"
    else:
        base = Path.home() / ".config"
    return base / "ghlang" / "config.toml"


def create_default_config(config_path: Path) -> None:
    """Create a default config file from the bundled template.

    Parameters
    ----------
    config_path : Path
        Destination path. Parent directories are created if needed.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    default_content = resources.files("ghlang.static").joinpath("default_config.toml").read_text()
    config_path.write_text(default_content)
    log.logger.debug(f"Created default config at: {config_path}")


def load_config(
    config_path: Path | None = None,
    cli_overrides: dict | None = None,
    require_token: bool = True,
) -> Config:
    """Load config from TOML file with optional CLI overrides.

    Parameters
    ----------
    config_path : Path | None
        Explicit path to the TOML file. Uses the platform default when *None*.
    cli_overrides : dict | None
        Key-value pairs that override values read from the file.
    require_token : bool
        Raise ``MissingTokenError`` when the GitHub token is empty.

    Returns
    -------
    Config
        Populated configuration dataclass.

    Raises
    ------
    MissingTokenError
        If *require_token* is True and no valid token is found.
    ConfigError
        If the TOML file cannot be parsed.
    """
    if config_path is None:
        config_path = get_config_path()

    if not config_path.exists():
        create_default_config(config_path)

        if require_token:
            raise exceptions.MissingTokenError(str(config_path))

        log.logger.debug(f"Config file created at: {config_path}")

    try:
        with config_path.open("rb") as f:
            data = tomllib.load(f)

    except tomllib.TOMLDecodeError as e:
        raise exceptions.ConfigError(f"Invalid TOML in config file: {e}") from e

    _validate_config(data)

    github = data.get("github", {})
    tokount = data.get("tokount")
    if tokount is None:
        tokount = data.get("cloc", {})

    output = data.get("output", {})
    preferences = data.get("preferences", {})

    token = github.get("token", "")

    if require_token and (not token or token == "YOUR_TOKEN_HERE"):
        raise exceptions.MissingTokenError()

    config = Config(
        token=token if token != "YOUR_TOKEN_HERE" else "",
        affiliation=github.get("affiliation", Config.affiliation),
        visibility=github.get("visibility", Config.visibility),
        ignored_repos=github.get("ignored_repos", []),
        ignored_dirs=tokount.get("ignored_dirs", list(constants.DEFAULT_IGNORED_DIRS)),
        output_dir=Path(output.get("directory", constants.DEFAULT_OUTPUT_DIR)).expanduser(),
        verbose=preferences.get("verbose", Config.verbose),
        theme=preferences.get("theme", Config.theme),
    )

    if cli_overrides:
        for key, value in cli_overrides.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)

    return config
