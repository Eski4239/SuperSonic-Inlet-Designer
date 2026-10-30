"""Inlet canvas (M3) GUI tests, offscreen."""
import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt  # noqa: E402

from busemann.canvas import picture as P  # noqa: E402
from busemann.canvas.scene import S  # noqa: E402
from inletdesign import api  # noqa: E402

pytestmark = pytest.mark.gui


def _set(qtbot, win, **changes):
    with qtbot.waitSignal(win.state.design_ready, timeout=5000):
        win.state.update(**changes)
    qtbot.waitUntil(lambda: not win.canvas.is_animating(), timeout=2000)


def _view_pos(canvas, model_pt):
    return canvas.mapFromScene(S(model_pt))


def _hover(qtbot, canvas, model_pt):
    qtbot.mouseMove(canvas.viewport(), _view_pos(canvas, model_pt))
    qtbot.waitUntil(lambda: canvas.hover_card.isVisible(), timeout=2000)


@pytest.mark.parametrize("n", range(5))
def test_canvas_builds_for_each_ramp_count(qtbot, window, n):
    if window.state.inputs.n_ramps != n:
        _set(qtbot, window, n_ramps=n)
    scene = window.canvas.inlet_scene
    assert len(scene.region_items) == n + 2
    assert len(scene.shock_items) == n + 1
    assert not window.canvas.overlay.isVisible()


def test_hover_region_shows_api_mach(qtbot, window):
    canvas = window.canvas
    region = canvas.inlet_scene.picture.regions[1]
    _hover(qtbot, canvas, P.polygon_centroid(region.polygon))
    assert canvas.hovered == ("region", 1)
    expected = api.design(3.0, 2).regions[1].M
    assert canvas.hover_card.values["M"] == pytest.approx(expected, abs=1e-6)
    assert "p" in canvas.hover_card.values and "T" in canvas.hover_card.values


def test_hover_shock_shows_shock_angle(qtbot, window):
    canvas = window.canvas
    shock = canvas.inlet_scene.picture.shocks[1]
    mid = (0.5 * (shock.start[0] + shock.end[0]), 0.5 * (shock.start[1] + shock.end[1]))
    _hover(qtbot, canvas, mid)
    assert canvas.hovered == ("shock", 1)
    d = api.design(3.0, 2)
    assert canvas.hover_card.values["beta"] == pytest.approx(d.betas_deg[1], abs=1e-6)
    assert canvas.hover_card.values["Mn1"] == pytest.approx(d.shock_states[1].Mn1, abs=1e-6)


def test_click_selects_region_and_fills_results_panel(qtbot, window):
    canvas = window.canvas
    region = canvas.inlet_scene.picture.regions[2]
    pos = _view_pos(canvas, P.polygon_centroid(region.polygon))
    with qtbot.waitSignal(canvas.selection_changed, timeout=2000) as blocker:
        qtbot.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    assert blocker.args[:2] == ["region", 2]
    assert canvas.inlet_scene.selection_item.isVisible()
    assert window.results_panel.selection_values["M"] == pytest.approx(region.state.M)
    # clicking outside the drawing clears the selection
    qtbot.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(3, 3))
    assert canvas.selection == (None, None)
    assert not canvas.inlet_scene.selection_item.isVisible()


def test_fit_contains_all_geometry(qtbot, window):
    canvas = window.canvas
    canvas.zoom(8.0)
    canvas.fit()
    visible = canvas.mapToScene(canvas.viewport().rect()).boundingRect()
    geometry = QRectF()
    for item in canvas.inlet_scene.region_items + canvas.inlet_scene.shock_items + [
            canvas.inlet_scene.ramp_body, canvas.inlet_scene.cowl_body]:
        geometry = geometry.united(item.sceneBoundingRect())
    assert visible.contains(geometry)


def test_wheel_zoom_and_f_key_fit(qtbot, window):
    canvas = window.canvas
    canvas.fit()
    s0 = canvas.scale_factor()
    canvas.zoom(1.5)
    assert canvas.scale_factor() == pytest.approx(1.5 * s0)
    canvas.setFocus()
    qtbot.keyClick(canvas, Qt.Key.Key_F)
    assert canvas.scale_factor() == pytest.approx(s0)


@pytest.mark.parametrize("layer", ["shocks", "regions", "dimensions"])
def test_layer_toggles_hide_items(qtbot, window, layer):
    canvas = window.canvas
    action = window.layer_actions[layer]
    action.setChecked(True)
    assert canvas.inlet_scene.layers[layer].isVisible()
    action.setChecked(False)
    assert not canvas.inlet_scene.layers[layer].isVisible()
    items = canvas.inlet_scene.layers[layer].childItems()
    assert items and all(not item.isVisible() for item in items)


def test_grid_toggle(qtbot, window):
    window.layer_actions["grid"].setChecked(True)
    assert window.canvas.layer_visible("grid")
    window.layer_actions["grid"].setChecked(False)
    assert not window.canvas.layer_visible("grid")


def test_hidden_shocks_are_not_pickable(qtbot, window):
    canvas = window.canvas
    shock = canvas.inlet_scene.picture.shocks[0]
    mid = (0.5 * (shock.start[0] + shock.end[0]), 0.5 * (shock.start[1] + shock.end[1]))
    assert canvas.pick(_view_pos(canvas, mid))[0] == "shock"
    window.layer_actions["shocks"].setChecked(False)
    assert canvas.pick(_view_pos(canvas, mid))[0] == "region"


def test_error_state_keeps_previous_geometry(qtbot, window):
    canvas = window.canvas
    before = canvas.inlet_scene.picture
    polygon = [tuple(p) for p in before.regions[1].polygon]
    _set(qtbot, window, method="custom", custom_angles=(12.0, 45.0))
    assert window.state.design is None
    assert canvas.inlet_scene.picture is before
    assert [tuple(p) for p in canvas.inlet_scene.picture.regions[1].polygon] == polygon
    assert canvas.is_dimmed()
    assert canvas.inlet_scene.layers["regions"].opacity() == pytest.approx(0.4)
    assert canvas.overlay.isVisible() and "detachment" in canvas.overlay.text()
    _set(qtbot, window, custom_angles=(12.0, 14.0))
    assert not canvas.is_dimmed() and not canvas.overlay.isVisible()


def test_animation_snaps_when_new_result_arrives(qtbot, window):
    canvas = window.canvas
    a = canvas._shown
    b = P.skeleton_from(api.design(3.3, 2))
    c = P.skeleton_from(api.design(3.6, 2))
    canvas.show_skeleton(b)
    assert canvas.is_animating()
    canvas.show_skeleton(c)             # mid-animation: snap straight to c
    assert not canvas.is_animating()
    assert canvas._shown is c and a is not c


def test_animation_disabled_while_slider_dragged(qtbot, window):
    slider = window.flight_panel.mach.slider
    slider.sliderPressed.emit()
    assert not window.canvas.animations_enabled
    slider.sliderReleased.emit()
    assert window.canvas.animations_enabled


def test_off_design_mach_moves_shocks(qtbot, window):
    canvas = window.canvas
    _set(qtbot, window, off_design_mach=2.5)
    pic = canvas.inlet_scene.picture
    assert pic.skeleton.off_design
    assert pic.shocks[0].end[0] < pic.skeleton.lip[0]          # spillage ahead of the lip
    assert pic.regions[1].state.M == pytest.approx(window.state.off_design.regions[1].M)
    _set(qtbot, window, off_design_mach=None)
    assert canvas.inlet_scene.picture.shocks[0].end == pytest.approx(pic.skeleton.lip)


def test_units_switch_relabels_dimensions(qtbot, window):
    window.layer_actions["dimensions"].setChecked(True)
    window.state.update(units="Imperial")
    texts = [i.text() for i in window.canvas.inlet_scene.layers["dimensions"].childItems()
             if hasattr(i, "text")]
    assert any(t.startswith("h_c") and t.endswith(" in") for t in texts)


def test_section_labels_are_uppercase_with_tracking(window):
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QLabel

    titles = [w for w in window.findChildren(QLabel) if w.objectName() == "sectionTitle"]
    assert titles and all(t.text() == t.text().upper() for t in titles)
    font = titles[0].font()
    assert font.capitalization() != QFont.Capitalization.SmallCaps
    assert font.letterSpacing() == pytest.approx(0.06 * 11, abs=1 / 64)   # Qt uses 1/64 px
    symbol = [w for w in window.findChildren(QLabel) if w.text() == "p∞"]
    assert symbol, "symbol labels keep their case"
