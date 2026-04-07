import json
from pathlib import Path
import re

from ghlang import constants
from ghlang import exceptions
from ghlang import log

from . import client


# linguist YAML structure: language at column 0, color on indented line
_LANG_RE = re.compile(r"^([A-Za-z0-9][\w\s\+\#\-\.\'/\*\(\)]*):$", re.MULTILINE)
_COLOR_RE = re.compile(r'^\s+color:\s*"(#[0-9A-Fa-f]{6})"', re.MULTILINE)


def _parse_linguist_yaml(text: str) -> dict[str, str]:
    """Extract language -> color mappings from linguist YAML text"""
    colors: dict[str, str] = {}
    current_lang: str | None = None

    for line in text.splitlines():
        lang_match = _LANG_RE.match(line)
        if lang_match:
            current_lang = lang_match.group(1)
            continue

        if current_lang:
            color_match = _COLOR_RE.match(line)
            if color_match:
                colors[current_lang] = color_match.group(1)
                current_lang = None
            elif not line.startswith(" ") and not line.startswith("#") and line.strip():
                # new top-level key without color found
                current_lang = None

    return colors


def load_github_colors(output_file: Path | None = None) -> dict[str, str]:
    """Fetch GitHub's language colors from the linguist YAML.

    Parameters
    ----------
    output_file : Path | None
        If given, write the color map to this path as JSON.

    Returns
    -------
    dict[str, str]
        Mapping of language name to hex color string (e.g. ``"#3572A5"``).
        Empty dict on network failure.
    """
    log.logger.info("Grabbing language colors from GitHub")

    try:
        r = client.get(constants.LINGUIST_URL, timeout=constants.REQUEST_TIMEOUT)
        r.raise_for_status()

        colors = _parse_linguist_yaml(r.text)
        log.logger.success(f"Loaded {len(colors)} language colors")

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open("w") as f:
                json.dump(colors, f, indent=2)
            log.logger.debug(f"Saved color data to {output_file}")

        return colors

    except (exceptions.RequestError, exceptions.HTTPError, OSError) as e:
        log.logger.warning(f"Couldn't load GitHub colors: {e}")
        return {}
