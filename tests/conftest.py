from pathlib import Path
import sys
from typing import cast

import pytest


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    """Create a temporary config file"""
    config_file = tmp_path / "config.toml"
    return config_file


@pytest.fixture
def valid_config_content() -> str:
    """Valid TOML config content"""
    configs = cast(
        dict[str, dict[str, str]], tomllib.loads((FIXTURES_DIR / "configs.toml").read_text())
    )
    return configs["valid"]["content"]


@pytest.fixture
def minimal_config_content() -> str:
    """Minimal valid config with just a token"""
    configs = cast(
        dict[str, dict[str, str]], tomllib.loads((FIXTURES_DIR / "configs.toml").read_text())
    )
    return configs["minimal"]["content"]
