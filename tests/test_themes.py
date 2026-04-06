import json
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import typer

from ghlang.cli.theme import theme
from ghlang.static.themes import THEMES
from ghlang.themes import load_all_themes
from ghlang.utils import load_themes_by_source


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Empty config directory"""
    return tmp_path


@pytest.fixture
def config_dir_with_remote(tmp_path: Path) -> Path:
    """Config dir with cached remote themes from fixture file"""
    data = (FIXTURES_DIR / "remote_themes.json").read_text()
    (tmp_path / "themes.json").write_text(data)
    (tmp_path / "themes.json.meta").write_text(json.dumps({"timestamp": "2099-01-01T00:00:00"}))
    return tmp_path


@pytest.fixture
def config_dir_with_custom(tmp_path: Path) -> Path:
    """Config dir with custom themes from fixture file"""
    data = (FIXTURES_DIR / "custom_themes.json").read_text()
    (tmp_path / "custom_themes.json").write_text(data)
    return tmp_path


@pytest.fixture
def theme_env(monkeypatch: pytest.MonkeyPatch, config_dir: Path) -> None:
    """Patch theme module to use test config dir with 'light' active"""
    monkeypatch.setattr("ghlang.utils.get_config_dir", lambda: config_dir)
    monkeypatch.setattr("ghlang.utils.get_active_theme", lambda: "light")
    monkeypatch.setattr("ghlang.utils.load_themes_by_source", load_themes_by_source)


@pytest.fixture
def theme_env_dark(monkeypatch: pytest.MonkeyPatch, config_dir: Path) -> None:
    """Patch theme module to use test config dir with 'dark' active"""
    monkeypatch.setattr("ghlang.utils.get_config_dir", lambda: config_dir)
    monkeypatch.setattr("ghlang.utils.get_active_theme", lambda: "dark")
    monkeypatch.setattr("ghlang.utils.load_themes_by_source", load_themes_by_source)


@pytest.fixture
def theme_env_remote(monkeypatch: pytest.MonkeyPatch, config_dir_with_remote: Path) -> None:
    """Patch theme module to use config dir with remote themes"""
    monkeypatch.setattr("ghlang.utils.get_config_dir", lambda: config_dir_with_remote)
    monkeypatch.setattr("ghlang.utils.get_active_theme", lambda: "light")
    monkeypatch.setattr("ghlang.utils.load_themes_by_source", load_themes_by_source)


@pytest.fixture
def theme_env_refresh(monkeypatch: pytest.MonkeyPatch, config_dir: Path) -> list[bool]:
    """Patch theme module for refresh test with fake load_all_themes"""
    monkeypatch.setattr("ghlang.utils.get_config_dir", lambda: config_dir)
    calls: list[bool] = []

    def fake_load(_d: Path, force_refresh: bool = False) -> dict:
        calls.append(force_refresh)
        return {**THEMES, "monokai": {}}

    monkeypatch.setattr("ghlang.themes.load_all_themes", fake_load)
    return calls


class TestLoadAllThemes:
    """Tests for theme loading pipeline"""

    def test_returns_builtin_themes(self, config_dir: Path) -> None:
        """Should always include built-in themes"""
        themes = load_all_themes(config_dir)

        for name in THEMES:
            assert name in themes

    def test_merges_remote_themes(self, config_dir_with_remote: Path) -> None:
        """Should merge cached remote themes"""
        themes = load_all_themes(config_dir_with_remote)

        assert "nord" in themes
        assert themes["nord"]["background"] == "#2e3440"

    def test_merges_custom_themes(self, config_dir_with_custom: Path) -> None:
        """Should merge custom themes"""
        themes = load_all_themes(config_dir_with_custom)

        assert "solarized" in themes

    def test_custom_overrides_remote(self, tmp_path: Path) -> None:
        """Custom themes should override remote themes with same name"""
        (tmp_path / "themes.json").write_text(json.dumps({"shared": {"background": "#111111"}}))
        (tmp_path / "themes.json.meta").write_text(json.dumps({"timestamp": "2099-01-01T00:00:00"}))
        (tmp_path / "custom_themes.json").write_text(
            json.dumps({"shared": {"background": "#222222"}})
        )

        themes = load_all_themes(tmp_path)

        assert themes["shared"]["background"] == "#222222"

    def test_handles_corrupt_custom_file(self, tmp_path: Path) -> None:
        """Should gracefully handle corrupt custom themes file"""
        (tmp_path / "custom_themes.json").write_text("not json")

        themes = load_all_themes(tmp_path)

        assert len(themes) >= len(THEMES)

    def test_force_refresh(self, config_dir: Path) -> None:
        """Should bypass cache when force_refresh=True"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"dracula": {"background": "#282a36"}}
        mock_response.raise_for_status = MagicMock()

        with patch("ghlang.net.client.get", return_value=mock_response):
            themes = load_all_themes(config_dir, force_refresh=True)

        assert "dracula" in themes

    def test_network_error_returns_builtin_only(self, config_dir: Path) -> None:
        """Should return built-in themes when remote fetch fails"""
        with patch("ghlang.net.client.get", side_effect=OSError("network error")):
            themes = load_all_themes(config_dir, force_refresh=True)

        assert set(themes.keys()) == set(THEMES.keys())


class TestLoadBySource:
    """Tests for load_themes_by_source helper"""

    def test_empty_config_dir(self, config_dir: Path) -> None:
        """Should return only built-in when no remote/custom files exist"""
        built_in, remote, custom = load_themes_by_source(config_dir)

        assert built_in == THEMES
        assert remote == {}
        assert custom == {}

    def test_separates_sources(self, tmp_path: Path) -> None:
        """Should keep remote and custom sources separate from built-in"""
        (tmp_path / "themes.json").write_text(json.dumps({"nord": {"background": "#2e3440"}}))
        (tmp_path / "custom_themes.json").write_text(
            json.dumps({"solarized": {"background": "#002b36"}})
        )

        built_in, remote, custom = load_themes_by_source(tmp_path)

        assert "nord" in remote
        assert "solarized" in custom
        assert "nord" not in built_in
        assert "solarized" not in built_in


class TestThemeCommands:
    """Tests for theme CLI commands"""

    # typer.Option defaults are OptionInfo objects (truthy), not actual values,
    # so all params must be passed explicitly when calling theme() directly

    @pytest.mark.usefixtures("theme_env")
    def test_list(self) -> None:
        """Should list themes without error"""
        theme(list_themes=True, refresh=False, info=None)

    @pytest.mark.usefixtures("theme_env_dark")
    def test_list_marks_active(self) -> None:
        """Active theme should be marked in the list"""
        theme(list_themes=True, refresh=False, info=None)

    @pytest.mark.usefixtures("theme_env")
    def test_info_builtin(self) -> None:
        """Should print info for a valid built-in theme"""
        theme(list_themes=False, refresh=False, info="light")

    @pytest.mark.usefixtures("theme_env_remote")
    def test_info_remote(self) -> None:
        """Should print info for a remote theme"""
        theme(list_themes=False, refresh=False, info="nord")

    @pytest.mark.usefixtures("theme_env")
    def test_info_unknown_exits(self) -> None:
        """Should exit with error for unknown theme"""
        with pytest.raises(typer.Exit):
            theme(list_themes=False, refresh=False, info="nonexistent")

    def test_refresh_calls_load(self, theme_env_refresh: list[bool]) -> None:
        """Should call load_all_themes with force_refresh=True"""
        theme(list_themes=False, refresh=True, info=None)

        assert theme_env_refresh == [True]
