import re
import subprocess
import sys

import ghlang


def test_version_string() -> None:
    """Version is a non-empty string with a recognisable shape."""
    v = ghlang.version()
    assert isinstance(v, str)
    assert len(v) > 0
    assert re.match(r"\d+\.\d+", v) is not None


def test_dunder_version_matches() -> None:
    """``__version__`` matches ``version()``."""
    assert ghlang.__version__ == ghlang.version()


def test_module_entry_prints_version() -> None:
    """``python -m ghlang`` prints the version to stdout."""
    result = subprocess.run(
        [sys.executable, "-m", "ghlang"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ghlang.version()
