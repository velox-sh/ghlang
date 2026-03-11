from dataclasses import dataclass
from dataclasses import field
from difflib import get_close_matches
from importlib import resources
from pathlib import Path
import sys
import tomllib

from .constants import DEFAULT_IGNORED_DIRS
from .constants import DEFAULT_OUTPUT_DIR
from .exceptions import ConfigError
from .exceptions import MissingTokenError
from .logging import logger


VALID_KEYS: dict[str, set[str]] = {
    "github": {"token", "affiliation", "visibility", "ignored_repos"},
    "tokount": {"ignored_dirs"},
    "output": {"directory"},
    "preferences": {"verbose", "theme"},
}


@dataclass
class Config:
    """Configuration for the language stats"""

    # GitHub settings
    token: str = ""
    affiliation: str = "owner,collaborator,organization_member"
    visibility: str = "all"
    ignored_repos: list[str] = field(default_factory=list)

    # Tokount settings
    ignored_dirs: list[str] = field(default_factory=DEFAULT_IGNORED_DIRS.copy)

    # Output settings
    output_dir: Path = field(default_factory=lambda: Path(DEFAULT_OUTPUT_DIR))

    # Preferences
    verbose: bool = False
    theme: str = "light"


def _validate_config(data: dict) -> None:
    """Warn about unknown config keys with fuzzy suggestions"""
    for section, keys in data.items():
        section_name = section
        if section == "cloc":
            logger.warning("Config section 'cloc' is deprecated, use 'tokount' instead")
            section_name = "tokount"

        if section_name not in VALID_KEYS:
            suggestions = get_close_matches(section_name, VALID_KEYS.keys(), n=1, cutoff=0.6)

            if suggestions:
                logger.warning(
                    f"Unknown config section '{section}' - did you mean '{suggestions[0]}'?"
                )
            else:
                logger.warning(f"Unknown config section '{section}'")
            continue

        if not isinstance(keys, dict):
            continue

        valid = VALID_KEYS[section_name]
        for key in keys:
            if key not in valid:
                suggestions = get_close_matches(key, valid, n=1, cutoff=0.6)

                if suggestions:
                    logger.warning(
                        f"Unknown key '{section}.{key}' - did you mean '{suggestions[0]}'?"
                    )
                else:
                    logger.warning(f"Unknown config key '{section}.{key}'")


def get_config_path() -> Path:
    """Get the platform-specific config file path"""
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local"
    else:
        base = Path.home() / ".config"
    return base / "ghlang" / "config.toml"


def create_default_config(config_path: Path) -> None:
    """Create a default config file from template"""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    default_content = resources.files("ghlang.static").joinpath("default_config.toml").read_text()
    config_path.write_text(default_content)
    logger.debug(f"Created default config at: {config_path}")


def load_config(
    config_path: Path | None = None,
    cli_overrides: dict | None = None,
    require_token: bool = True,
) -> Config:
    """Load config from TOML file with optional CLI overrides"""
    if config_path is None:
        config_path = get_config_path()

    if not config_path.exists():
        create_default_config(config_path)

        if require_token:
            raise MissingTokenError(str(config_path))

        logger.debug(f"Config file created at: {config_path}")

    try:
        with config_path.open("rb") as f:
            data = tomllib.load(f)

    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML in config file: {e}") from e

    _validate_config(data)

    github = data.get("github", {})
    tokount = data.get("tokount")
    if tokount is None:
        tokount = data.get("cloc", {})

    output = data.get("output", {})
    preferences = data.get("preferences", {})

    token = github.get("token", "")

    if require_token and (not token or token == "YOUR_TOKEN_HERE"):
        raise MissingTokenError()

    config = Config(
        token=token if token != "YOUR_TOKEN_HERE" else "",
        affiliation=github.get("affiliation", Config.affiliation),
        visibility=github.get("visibility", Config.visibility),
        ignored_repos=github.get("ignored_repos", []),
        ignored_dirs=tokount.get("ignored_dirs", DEFAULT_IGNORED_DIRS.copy()),
        output_dir=Path(output.get("directory", DEFAULT_OUTPUT_DIR)).expanduser(),
        verbose=preferences.get("verbose", Config.verbose),
        theme=preferences.get("theme", Config.theme),
    )

    if cli_overrides:
        for key, value in cli_overrides.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)

    return config
