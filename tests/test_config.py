from pathlib import Path

import pytest

from ghlang.config import Config
from ghlang.config import load_config
from ghlang.constants import DEFAULT_IGNORED_DIRS
from ghlang.exceptions import ConfigError
from ghlang.exceptions import MissingTokenError


class TestConfigDataclass:
    """Tests for Config dataclass defaults"""

    def test_default_values(self) -> None:
        """Config should have sensible defaults"""
        config = Config()

        assert config.token == ""
        assert config.affiliation == "owner,collaborator,organization_member"
        assert config.visibility == "all"
        assert config.ignored_repos == []
        assert config.ignored_dirs == list(DEFAULT_IGNORED_DIRS)
        assert config.verbose is False
        assert config.theme == "light"

    def test_ignored_dirs_independent_copies(self) -> None:
        """Each Config instance should have independent ignored_dirs list"""
        config1 = Config()
        config2 = Config()

        config1.ignored_dirs.append("custom_dir")

        assert "custom_dir" in config1.ignored_dirs
        assert "custom_dir" not in config2.ignored_dirs


class TestLoadConfig:
    """Tests for config file loading"""

    def test_load_valid_config(self, tmp_config: Path, valid_config_content: str) -> None:
        """Should load a valid config file correctly"""
        tmp_config.write_text(valid_config_content)

        config = load_config(config_path=tmp_config)

        assert config.token == "ghp_test_token_12345"
        assert config.affiliation == "owner"
        assert config.visibility == "public"
        assert config.ignored_repos == ["test-repo", "another-repo"]
        assert config.ignored_dirs == ["node_modules", ".git"]
        assert config.verbose is True
        assert config.theme == "dark"

    def test_load_minimal_config(self, tmp_config: Path, minimal_config_content: str) -> None:
        """Should load config with only required fields, using defaults for rest"""
        tmp_config.write_text(minimal_config_content)

        config = load_config(config_path=tmp_config)

        assert config.token == "ghp_test_token_12345"
        assert config.affiliation == "owner,collaborator,organization_member"
        assert config.visibility == "all"
        assert config.ignored_repos == []
        assert config.ignored_dirs == list(DEFAULT_IGNORED_DIRS)

    def test_missing_token_raises_error(self, tmp_config: Path) -> None:
        """Should raise MissingTokenError when token is missing"""
        tmp_config.write_text("[github]\n")

        with pytest.raises(MissingTokenError):
            load_config(config_path=tmp_config, require_token=True)

    def test_placeholder_token_raises_error(self, tmp_config: Path) -> None:
        """Should raise MissingTokenError when token is placeholder"""
        tmp_config.write_text('[github]\ntoken = "YOUR_TOKEN_HERE"\n')

        with pytest.raises(MissingTokenError):
            load_config(config_path=tmp_config, require_token=True)

    def test_missing_token_allowed_when_not_required(self, tmp_config: Path) -> None:
        """Should allow missing token when require_token=False"""
        tmp_config.write_text("[github]\n")

        config = load_config(config_path=tmp_config, require_token=False)

        assert config.token == ""

    def test_invalid_toml_raises_config_error(self, tmp_config: Path) -> None:
        """Should raise ConfigError for invalid TOML"""
        tmp_config.write_text("this is not valid toml [[[")

        with pytest.raises(ConfigError, match="Invalid TOML"):
            load_config(config_path=tmp_config, require_token=False)

    def test_cli_overrides_applied(self, tmp_config: Path, minimal_config_content: str) -> None:
        """CLI overrides should take precedence over config file"""
        tmp_config.write_text(minimal_config_content)

        config = load_config(
            config_path=tmp_config,
            cli_overrides={
                "verbose": True,
                "theme": "dark",
                "output_dir": Path("/custom/path"),
            },
        )

        assert config.verbose is True
        assert config.theme == "dark"
        assert config.output_dir == Path("/custom/path")

    def test_cli_overrides_none_values_ignored(
        self, tmp_config: Path, valid_config_content: str
    ) -> None:
        """None values in CLI overrides should not override config"""
        tmp_config.write_text(valid_config_content)

        config = load_config(
            config_path=tmp_config,
            cli_overrides={"verbose": None, "theme": None},
        )

        assert config.verbose is True
        assert config.theme == "dark"

    def test_creates_default_config_when_missing(self, tmp_path: Path) -> None:
        """Should create default config when file doesn't exist"""
        config_path = tmp_path / "new_config" / "config.toml"

        with pytest.raises(MissingTokenError):
            load_config(config_path=config_path, require_token=True)

        assert config_path.exists()

    def test_output_dir_expanded(self, tmp_config: Path) -> None:
        """Output directory with ~ should be expanded"""
        tmp_config.write_text(
            """
        [github]
        token = "test_token"

        [output]
        directory = "~/my-output"
        """
        )

        config = load_config(config_path=tmp_config)

        assert "~" not in str(config.output_dir)
        assert config.output_dir.is_absolute()
