import sys

from inletdesign.cli import main


def test_gui_subcommand_without_app_gives_clear_error(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "busemann.app", None)  # makes the import fail
    assert main(["gui"]) == 2
    assert "pip install -e .[app]" in capsys.readouterr().err
