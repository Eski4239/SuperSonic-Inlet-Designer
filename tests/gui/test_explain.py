"""Explain drawer (M5): toggle and slide, content follows the selection, numbers are api
values, equations render."""
import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from busemann.views.explain_drawer import DRAWER_W, SLIDE_MS  # noqa: E402
from inletdesign import api  # noqa: E402

pytestmark = pytest.mark.gui


def _open(qtbot, window):
    drawer = window.explain_drawer
    window.explain_action.setChecked(True)
    qtbot.waitUntil(lambda: drawer._anim.state() != drawer._anim.State.Running, timeout=2000)
    return drawer


def test_toggle_slides_drawer_in_over_results_panel(qtbot, window):
    drawer = window.explain_drawer
    assert not drawer.isVisible() and not drawer.is_open
    assert drawer._anim.duration() == SLIDE_MS == 200
    _open(qtbot, window)
    central = window.centralWidget().geometry()
    assert drawer.isVisible() and drawer.width() == DRAWER_W == 420
    assert drawer.geometry().right() == central.right()
    assert drawer.geometry().top() == central.top() and drawer.height() == central.height()
    assert drawer.x() <= window.right_panel.mapTo(window, window.right_panel.rect().topLeft()).x()
    window.explain_action.setChecked(False)
    qtbot.waitUntil(lambda: not drawer.isVisible(), timeout=2000)


def test_nothing_selected_shows_design_method(qtbot, window):
    drawer = _open(qtbot, window)
    assert window.canvas.selection == (None, None)
    assert drawer.entry_name == "method"
    assert drawer.rendered.title.startswith("Design method")


@pytest.mark.parametrize("kind, index, entry", [
    ("shock", 0, "oblique_shock"), ("shock", 2, "normal_shock"), ("region", 0, "freestream"),
    ("region", 1, "region"), ("region", 3, "duct"), ("cowl", 0, "cowl_design")])
def test_canvas_selection_switches_content(qtbot, window, kind, index, entry):
    drawer = _open(qtbot, window)
    with qtbot.waitSignal(drawer.content_changed, timeout=2000):
        window.canvas.select(kind, index)
    assert drawer.entry_name == entry
    assert drawer.images and all(not img.isNull() for img in drawer.images.values())


def test_table_row_switches_content(qtbot, window):
    drawer = _open(qtbot, window)
    table = window.results_panel.station_table
    with qtbot.waitSignal(drawer.content_changed, timeout=2000):
        table.selectRow(2)
    assert drawer.entry_name == "region" and drawer.rendered.title == "Region 2 (behind ramp shock 2)"


def test_shock_numbers_are_api_values(qtbot, window):
    drawer = _open(qtbot, window)
    window.canvas.select("shock", 1)
    s = api.design(3.0, 2).shock_states[1]
    shown = {sub.path: sub.text for sub in drawer.rendered.substitutions}
    assert shown["sel.Mn1"] == f"{s.Mn1:.4f}" and shown["sel.beta_deg"] == f"{s.beta_deg:.2f}"
    assert shown["sel.M2"] == f"{s.M2:.4f}" and shown["sel.p0_ratio"] == f"{s.p0_ratio:.4f}"
    assert f"{s.Mn1:.4f}" in drawer.body.toPlainText()          # plain-words paragraph


def test_cowl_on_off_design_tab_uses_local_rule(qtbot, window):
    with qtbot.waitSignal(window.state.design_ready, timeout=5000):
        window.state.update(cowl_wedge_deg=6.0)
    window.tabs.setCurrentWidget(window.offdesign_tab)
    with qtbot.waitSignal(window.state.off_design_ready, timeout=5000):
        window.state.update(off_design_mach=2.55)
    drawer = _open(qtbot, window)
    with qtbot.waitSignal(drawer.content_changed, timeout=2000):
        window.offdesign_tab.canvas.select("cowl", 0)
    assert drawer.entry_name == "cowl_offdesign"
    off = window.state.off_design
    shown = {sub.path: sub.text for sub in drawer.rendered.substitutions}
    assert shown["off.cowl_margin_deg"] == f"{off.cowl_margin_deg:+.2f}"
    assert shown["off.cowl_required_turn_deg"] == "6.00"


def test_topic_links(qtbot, window):
    drawer = _open(qtbot, window)
    drawer.topics.linkActivated.emit("offdesign")
    assert drawer.entry_name == "offdesign"
    window.canvas.select("shock", 0)
    drawer.topics.linkActivated.emit("method")
    assert drawer.entry_name == "method"
    drawer.topics.linkActivated.emit("selection")
    assert drawer.entry_name == "oblique_shock"
