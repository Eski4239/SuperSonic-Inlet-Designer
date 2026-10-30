"""Bundled app resources resolve to real files, from source and under PyInstaller."""
import sys

import pytest

# busemann.theme imports Qt at package level, so this module needs PySide6 installed.
pytest.importorskip("PySide6")

from busemann import paths  # noqa: E402
from busemann.theme import tokens  # noqa: E402


def test_chevron_resolves_to_existing_file():
    path = paths.resource_path("icons", "chevron-down-muted.svg")
    assert path.is_file()
    assert path.parent.parent == paths.resource_root()


def test_pretinted_chevron_matches_token():
    svg = paths.resource_path("icons", "chevron-down-muted.svg").read_text(encoding="utf-8")
    assert f'stroke="{tokens.COLORS["text_muted"]}"' in svg
    assert "currentColor" not in svg


def test_missing_resource_raises():
    with pytest.raises(FileNotFoundError):
        paths.resource_path("icons", "does-not-exist.svg")


def test_frozen_bundle_uses_meipass(tmp_path, monkeypatch):
    icon = tmp_path / "busemann" / "resources" / "icons" / "chevron-down-muted.svg"
    icon.parent.mkdir(parents=True)
    icon.write_text("<svg/>", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert paths.resource_path("icons", "chevron-down-muted.svg") == icon


def test_pyproject_ships_icons_and_fonts():
    """package-data must include every resource kind the app loads by path."""
    import tomllib
    from pathlib import Path

    data = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text("utf-8"))
    patterns = data["tool"]["setuptools"]["package-data"]["busemann"]
    assert "resources/icons/*.svg" in patterns
    assert "resources/fonts/*.ttf" in patterns
