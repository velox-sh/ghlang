from pathlib import Path

from ghlang.utils import load_themes_by_source


class TestLoadThemesBySource:
    """Tests for load_themes_by_source utility"""

    def test_empty_dir(self, tmp_path: Path) -> None:
        """Should return only built-in themes for empty config dir."""
        built_in, remote, custom = load_themes_by_source(tmp_path)

        assert len(built_in) > 0
        assert remote == {}
        assert custom == {}

    def test_corrupt_remote_file(self, tmp_path: Path) -> None:
        """Should handle corrupt remote themes file gracefully."""
        (tmp_path / "themes.json").write_text("not json")

        _, remote, _ = load_themes_by_source(tmp_path)
        assert remote == {}

    def test_corrupt_custom_file(self, tmp_path: Path) -> None:
        """Should handle corrupt custom themes file gracefully."""
        (tmp_path / "custom_themes.json").write_text("{broken")

        _, _, custom = load_themes_by_source(tmp_path)
        assert custom == {}
