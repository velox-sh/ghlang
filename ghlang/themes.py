from datetime import datetime
import json
from pathlib import Path
from typing import cast

from . import config
from . import constants
from . import exceptions
from . import log
from .net import client as net_client
from .static import themes as static_themes


def _fetch_remote_themes(cache_path: Path, force: bool = False) -> dict[str, dict[str, str]]:
    """Fetch remote theme manifest with local cache"""
    cache_meta = cache_path.with_suffix(".json.meta")

    if not force and cache_path.exists() and cache_meta.exists():
        try:
            meta = json.loads(cache_meta.read_text())
            cached_time = datetime.fromisoformat(meta["timestamp"])

            if datetime.now() - cached_time < constants.THEME_CACHE_TTL:
                return cast(dict[str, dict[str, str]], json.loads(cache_path.read_text()))

        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            pass

    try:
        r = net_client.get(constants.MANIFEST_URL, timeout=constants.REQUEST_TIMEOUT)
        r.raise_for_status()
        themes = cast(dict[str, dict[str, str]], r.json())

        cache_path.write_text(json.dumps(themes, indent=2))
        cache_meta.write_text(
            json.dumps(
                {
                    "timestamp": datetime.now().isoformat(),
                    "url": constants.MANIFEST_URL,
                }
            )
        )

        return themes

    except (exceptions.RequestError, exceptions.HTTPError, json.JSONDecodeError, OSError) as e:
        log.logger.warning(f"Couldn't fetch remote themes: {e}")
        return {}


def load_all_themes(config_dir: Path, force_refresh: bool = False) -> dict[str, dict[str, str]]:
    """Load all themes: built-in, remote, and custom.

    Parameters
    ----------
    config_dir : Path
        Config directory containing ``themes.json`` and ``custom_themes.json``.
    force_refresh : bool
        Bypass the remote theme cache TTL.

    Returns
    -------
    dict[str, dict[str, str]]
        Merged theme registry keyed by theme name.
    """
    themes = static_themes.THEMES.copy()

    remote_path = config_dir / "themes.json"
    remote = _fetch_remote_themes(remote_path, force=force_refresh)
    themes.update(remote)

    custom_path = config_dir / "custom_themes.json"
    if custom_path.exists():
        try:
            custom = json.loads(custom_path.read_text())
            themes.update(custom)

        except (json.JSONDecodeError, OSError) as e:
            log.logger.warning(f"Couldn't load custom themes: {e}")

    return themes


def get_theme(theme: str) -> dict[str, str]:
    """Look up a theme by name, falling back to light if not found.

    Parameters
    ----------
    theme : str
        Theme name to look up.

    Returns
    -------
    dict[str, str]
        Color key to hex value mapping for the resolved theme.
    """
    config_dir = config.get_config_path().parent

    all_themes = load_all_themes(config_dir)
    if theme not in all_themes:
        log.logger.warning(f"No '{theme}' theme exists, using light instead")
        return static_themes.THEMES["light"]

    return all_themes[theme]
