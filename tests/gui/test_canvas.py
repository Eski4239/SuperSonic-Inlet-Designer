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


# --- M3.1 ----------------------------------------------------------------------------

def test_region_colours_diverge_at_sonic(qtbot, window):
    scene = window.canvas.inlet_scene
    duct = scene.region_fill(len(scene.region_items) - 1)          # subsonic: warm sand
    free = scene.region_fill(0)                                     # supersonic: blue
    assert duct.red() > duct.blue() and free.blue() > free.red()
    assert 1.0 in scene.mach_edges and scene.mach_edges[-1] == pytest.approx(3.0)
    item = scene.region_items[0]
    assert item.pen().color().lightness() < item.brush().color().lightness()   # darker border


def test_legend_card_top_right(window):
    canvas = window.canvas
    card = canvas.legend_rect()
    vp = canvas.viewport().rect()
    assert card.top() == 16 and vp.width() - card.right() == pytest.approx(16)
    assert canvas.available_rect().right() < card.left()


def test_fit_fills_85_percent_of_limiting_dimension(qtbot, window):
    canvas = window.canvas
    canvas.fit()
    avail = canvas.available_rect()
    drawn = canvas.mapFromScene(canvas.inlet_scene.geometry_rect()).boundingRect()
    fill = max(drawn.width() / avail.width(), drawn.height() / avail.height())
    assert fill == pytest.approx(0.85, abs=0.01)
    assert drawn.center().x() == pytest.approx(avail.center().x(), abs=2)
    assert drawn.center().y() == pytest.approx(avail.center().y(), abs=2)


def test_dimension_labels_do_not_collide_and_fit_includes_them(qtbot, window):
    from busemann.canvas import picture as Pm

    window.layer_actions["dimensions"].setChecked(True)
    canvas = window.canvas
    scene = canvas.inlet_scene
    rects = scene.label_rects
    assert len(rects) == len(scene.dim_labels) + 1                 # + the M∞ label
    polygons, segments = scene.obstacles()
    for i, r in enumerate(rects):
        assert not any(Pm.rect_hits_polygon(r, p) for p in polygons)
        assert not any(Pm.rect_hits_segment(r, a, b) for a, b in segments)
        assert not any(Pm._rect_overlaps_rect(r, o) for o in rects[i + 1:])
    visible = canvas.mapToScene(canvas.viewport().rect()).boundingRect()
    assert visible.contains(scene.geometry_rect(include_labels=True))
    texts = [lab.text() for lab in scene.dim_labels]
    assert any(t.startswith("h_c ") and t.endswith("100.0 mm") for t in texts)
    window.state.update(units="Imperial")
    assert any(t.text().startswith("h_c ") and t.text().endswith("3.94 in")
               for t in scene.dim_labels)


def test_x15_four_ramp_shows_detached_cowl(qtbot, window):
    with qtbot.waitSignal(window.state.design_ready, timeout=5000):
        window.state.update(mach=6.7, altitude_m=31000.0, n_ramps=4)
    qtbot.waitUntil(lambda: not window.canvas.is_animating(), timeout=2000)
    scene = window.canvas.inlet_scene
    assert scene.bow_shock.isVisible()
    assert "Illustrative only" in scene.bow_shock.toolTip()
    assert "error" in window.results_panel.warning_levels()
    assert any(t.startswith("External cowl shock detached")
               for t in window.results_panel.warning_texts())
    assert window.results_panel.warnings_box.property("level") == "error"


def test_max_cowl_angle_constrains_design(qtbot, window):
    panel = window.design_panel
    panel.advanced.toggle.setChecked(True)
    assert not window.state.inputs.max_cowl_enabled
    with qtbot.waitSignal(window.state.design_ready, timeout=5000):
        panel.max_cowl_check.setChecked(True)
    d = window.state.design
    assert d.constrained and d.cowl_angle_deg <= 30.0 + 1e-9
    badge = window.results_panel.cards["recovery_total"].badge
    assert badge.isVisible() and badge.text() == "CONSTRAINED"
    with qtbot.waitSignal(window.state.design_ready, timeout=5000):
        panel.max_cowl_check.setChecked(False)
    assert not window.state.design.constrained and not badge.isVisible()


def test_ramp_table_replaces_angle_lists(window):
    table = window.design_panel.ramp_table
    d = window.state.design
    assert len(table.rows) == 2
    assert table.text(0, 1) == f"{d.ramp_angles_deg[0]:.2f}"
    assert table.text(1, 2) == f"{d.betas_deg[1]:.2f}"
    assert table.text(1, 3) == f"{d.regions[2].M:.3f}"
    assert window.design_panel.readout.text("margin") == f"{d.cowl_margin_deg:+.2f}"


def test_error_card_wraps_with_non_breaking_spaces(qtbot, window):
    with qtbot.waitSignal(window.state.design_ready, timeout=5000):
        window.state.update(method="custom", custom_angles=(12.0, 40.0))
    overlay = window.canvas.overlay
    assert "M = " in overlay.text() and " deg" in overlay.text()
    assert overlay.width() <= 480
    assert overlay.height() >= overlay.heightForWidth(overlay.width())
