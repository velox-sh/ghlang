import contextlib
import json
from pathlib import Path

from . import config
from . import exceptions
from . import log
from .static import themes as static_themes


def save_json(data: object, path: Path) -> None:
    """Write data as JSON, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w") as f:
        json.dump(data, f, indent=2)

    log.logger.debug(f"Saved to {path}")


def get_config_dir() -> Path:
    """Get the config directory path."""
    return config.get_config_path().parent


def get_active_theme() -> str:
    """Get the currently active theme name."""
    try:
        return config.load_config(require_token=False).theme
    except exceptions.ConfigError:
        return "light"


def load_themes_by_source(
    config_dir: Path,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Load themes split by origin for display purposes.

    Parameters
    ----------
    config_dir : Path
        Config directory containing cached theme files.

    Returns
    -------
    tuple[dict, dict, dict]
        Three dicts: (built-in, remote, custom) theme registries.
    """
    built_in: dict[str, dict[str, str]] = dict(static_themes.THEMES)

    remote: dict[str, dict[str, str]] = {}
    remote_path = config_dir / "themes.json"
    if remote_path.exists():
        with contextlib.suppress(json.JSONDecodeError, OSError):
            remote = json.loads(remote_path.read_text())

    custom: dict[str, dict[str, str]] = {}
    custom_path = config_dir / "custom_themes.json"
    if custom_path.exists():
        with contextlib.suppress(json.JSONDecodeError, OSError):
            custom = json.loads(custom_path.read_text())

    return built_in, remote, custom
