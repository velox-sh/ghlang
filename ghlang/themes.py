from datetime import datetime
import json
from pathlib import Path
from typing import cast

import requests

from .constants import REQUEST_TIMEOUT
from .constants import THEME_CACHE_TTL
from .constants import THEME_MANIFEST_URL
from .logging import logger
from .static.themes import THEMES


def _fetch_remote_themes(cache_path: Path, force: bool = False) -> dict[str, dict[str, str]]:
    """Fetch community themes from manifest"""
    cache_meta = cache_path.with_suffix(".json.meta")

    if not force and cache_path.exists() and cache_meta.exists():
        try:
            meta = json.loads(cache_meta.read_text())
            cached_time = datetime.fromisoformat(meta["timestamp"])

            if datetime.now() - cached_time < THEME_CACHE_TTL:
                return cast(dict[str, dict[str, str]], json.loads(cache_path.read_text()))

        except Exception:
            pass

    try:
        r = requests.get(THEME_MANIFEST_URL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        themes = cast(dict[str, dict[str, str]], r.json())

        cache_path.write_text(json.dumps(themes, indent=2))
        cache_meta.write_text(
            json.dumps(
                {
                    "timestamp": datetime.now().isoformat(),
                    "url": THEME_MANIFEST_URL,
                }
            )
        )

        return themes

    except Exception as e:
        logger.warning(f"Couldn't fetch remote themes: {e}")
        return {}


def load_all_themes(config_dir: Path, force_refresh: bool = False) -> dict[str, dict[str, str]]:
    """Load: built-in + remote + custom"""
    themes = THEMES.copy()

    remote_path = config_dir / "themes.json"
    remote = _fetch_remote_themes(remote_path, force=force_refresh)
    themes.update(remote)

    custom_path = config_dir / "custom_themes.json"
    if custom_path.exists():
        try:
            custom = json.loads(custom_path.read_text())
            themes.update(custom)

        except Exception as e:
            logger.warning(f"Couldn't load custom themes: {e}")

    return themes
