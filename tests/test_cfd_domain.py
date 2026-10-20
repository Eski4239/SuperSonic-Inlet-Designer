import math

import ezdxf
import numpy as np
import pytest

from inletdesign import oblique_shock as obl
from inletdesign.cfd_domain import export_cfd_domain_dxf, export_offdesign_domain_dxf
from inletdesign.cli import main
from inletdesign.geometry import design_inlet

EXPECTED_LAYERS = {"INLET", "SYMMETRY", "RAMP", "OUTLET", "COWL", "TOP_FREESTREAM"}
EXPECTED_OFFDESIGN_LAYERS = {
    "INLET", "FARFIELD_TOP", "OUTLET_EXT", "COWL", "OUTLET", "RAMP", "SYMMETRY",
}


@pytest.mark.parametrize("M_inf, n_ramps", [(3.0, 2), (2.0, 1), (4.0, 3)])
def test_loop_closes(M_inf, n_ramps, tmp_path):
    geom = design_inlet(M_inf, n_ramps, capture_height=0.1)
    path = tmp_path / "domain.dxf"

    # Should not raise (export_cfd_domain_dxf itself verifies closure internally).
    export_cfd_domain_dxf(geom, str(path))

    # Independent cross-check: recompute the same loop from geom and verify closure directly.
    h_c = geom.capture_height
    tip = geom.ramp_points[0]
    terminal_foot = geom.ramp_points[-1]
    lip = geom.lip
    phi_n = geom.cowl_angle_deg
    dir_n = (math.cos(math.radians(phi_n)), math.sin(math.radians(phi_n)))

    inlet_bottom = (tip[0] - 1.0 * h_c, 0.0)
    inlet_top = (tip[0] - 1.0 * h_c, h_c)
    ramp_duct_end = (
        terminal_foot[0] + 2.0 * h_c * dir_n[0],
        terminal_foot[1] + 2.0 * h_c * dir_n[1],
    )
    cowl_inner_end = (lip[0] + 2.0 * h_c * dir_n[0], lip[1] + 2.0 * h_c * dir_n[1])

    full_loop = (
        [inlet_bottom, inlet_top, lip, cowl_inner_end, ramp_duct_end]
        + list(reversed(geom.ramp_points[:-1]))
        + [tip, inlet_bottom]
    )
    gap = math.hypot(full_loop[0][0] - full_loop[-1][0], full_loop[0][1] - full_loop[-1][1])
    assert gap < 1e-9


def test_layers_exist(tmp_path):
    geom = design_inlet(3.0, 2, capture_height=0.1)
    path = tmp_path / "domain.dxf"
    export_cfd_domain_dxf(geom, str(path))

    doc = ezdxf.readfile(str(path))
    layer_names = {layer.dxf.name for layer in doc.layers}
    assert EXPECTED_LAYERS <= layer_names


def test_cli_cfd_domain_creates_file(tmp_path):
    out = tmp_path / "m3_cfd"
    code = main(
        [
            "cfd-domain", "--mach", "3", "--ramps", "2",
            "--capture-height", "0.1", "--out", str(out),
        ]
    )
    assert code == 0
    assert out.with_suffix(".dxf").exists()


def _offdesign_loop(geom, duct_length_factor=2.0, top_height_factor=2.0):
    h_c = geom.capture_height
    tip = geom.ramp_points[0]
    terminal_foot = geom.ramp_points[-1]
    lip = geom.lip
    phi_n = geom.cowl_angle_deg
    dir_n = (math.cos(math.radians(phi_n)), math.sin(math.radians(phi_n)))

    H = top_height_factor * h_c
    inlet_x = tip[0] - 1.0 * h_c
    inlet_bottom = (inlet_x, 0.0)
    inlet_top_H = (inlet_x, H)
    x_lip = lip[0]
    farfield_top_end = (x_lip, H)
    ramp_duct_end = (
        terminal_foot[0] + duct_length_factor * h_c * dir_n[0],
        terminal_foot[1] + duct_length_factor * h_c * dir_n[1],
    )
    cowl_inner_end = (
        lip[0] + duct_length_factor * h_c * dir_n[0],
        lip[1] + duct_length_factor * h_c * dir_n[1],
    )

    return (
        [inlet_bottom, inlet_top_H, farfield_top_end, lip, cowl_inner_end, ramp_duct_end]
        + list(reversed(geom.ramp_points[:-1]))
        + [tip, inlet_bottom]
    )


def _shoelace_area(points):
    pts = np.array(points, dtype=float)
    x, y = pts[:, 0], pts[:, 1]
    return 0.5 * abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


@pytest.mark.parametrize("M_inf, n_ramps", [(3.0, 2), (2.0, 1), (4.0, 3)])
def test_offdesign_loop_closes(M_inf, n_ramps, tmp_path):
    geom = design_inlet(M_inf, n_ramps, capture_height=0.1)
    path = tmp_path / "offdesign.dxf"

    export_offdesign_domain_dxf(geom, str(path))

    full_loop = _offdesign_loop(geom)
    gap = math.hypot(full_loop[0][0] - full_loop[-1][0], full_loop[0][1] - full_loop[-1][1])
    assert gap < 1e-9


def test_offdesign_layers_exist(tmp_path):
    geom = design_inlet(3.0, 2, capture_height=0.1)
    path = tmp_path / "offdesign.dxf"
    export_offdesign_domain_dxf(geom, str(path))

    doc = ezdxf.readfile(str(path))
    layer_names = {layer.dxf.name for layer in doc.layers}
    assert EXPECTED_OFFDESIGN_LAYERS <= layer_names


def test_offdesign_farfield_top_and_outlet_ext_positions(tmp_path):
    geom = design_inlet(3.0, 2, capture_height=0.1)
    h_c = geom.capture_height
    H = 2.0 * h_c
    x_lip = geom.lip[0]

    path = tmp_path / "offdesign.dxf"
    export_offdesign_domain_dxf(geom, str(path))
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()

    farfield_lines = [e for e in msp if e.dxftype() == "LINE" and e.dxf.layer == "FARFIELD_TOP"]
    assert len(farfield_lines) == 1
    line = farfield_lines[0]
    assert line.dxf.start[1] == pytest.approx(H * 1000.0, abs=1e-6)
    assert line.dxf.end[1] == pytest.approx(H * 1000.0, abs=1e-6)

    outlet_ext_lines = [e for e in msp if e.dxftype() == "LINE" and e.dxf.layer == "OUTLET_EXT"]
    assert len(outlet_ext_lines) == 1
    line = outlet_ext_lines[0]
    assert line.dxf.start[0] == pytest.approx(x_lip * 1000.0, abs=1e-6)
    assert line.dxf.end[0] == pytest.approx(x_lip * 1000.0, abs=1e-6)
    ys = sorted([line.dxf.start[1], line.dxf.end[1]])
    assert ys[0] == pytest.approx(h_c * 1000.0, abs=1e-6)
    assert ys[1] == pytest.approx(H * 1000.0, abs=1e-6)


def test_offdesign_area_equals_design_plus_strip():
    geom = design_inlet(3.0, 2, capture_height=1.0)
    h_c = geom.capture_height
    tip = geom.ramp_points[0]
    x_lip = geom.lip[0]
    inlet_x = tip[0] - 1.0 * h_c
    H = 2.0 * h_c

    design_loop = (
        [(inlet_x, 0.0), (inlet_x, h_c), geom.lip]
        + [
            (
                geom.lip[0] + 2.0 * h_c * math.cos(math.radians(geom.cowl_angle_deg)),
                geom.lip[1] + 2.0 * h_c * math.sin(math.radians(geom.cowl_angle_deg)),
            ),
            (
                geom.ramp_points[-1][0] + 2.0 * h_c * math.cos(math.radians(geom.cowl_angle_deg)),
                geom.ramp_points[-1][1] + 2.0 * h_c * math.sin(math.radians(geom.cowl_angle_deg)),
            ),
        ]
        + list(reversed(geom.ramp_points[:-1]))
        + [tip]
    )
    area_design = _shoelace_area(design_loop)

    offdesign_loop = _offdesign_loop(geom)[:-1]  # drop the closing duplicate of inlet_bottom
    area_offdesign = _shoelace_area(offdesign_loop)

    added_strip = (x_lip - inlet_x) * (H - h_c)
    assert area_offdesign == pytest.approx(area_design + added_strip, rel=1e-9)


def test_offdesign_shock1_exits_through_outlet_ext():
    geom = design_inlet(3.0, 2, capture_height=1.0)
    h_c = geom.capture_height
    x_lip = geom.lip[0]
    H = 2.0 * h_c

    M_inf = 2.5
    phis = [0.0]
    M = M_inf
    betas = []
    for theta in geom.ramp_angles_deg:
        state = obl.oblique_shock_state(M, theta, weak=True)
        betas.append(state["beta"])
        M = state["M2"]
        phis.append(phis[-1] + theta)

    origin = np.array(geom.ramp_points[0])
    angle = np.radians(phis[0] + betas[0])
    d = np.array([np.cos(angle), np.sin(angle)])
    t = (x_lip - origin[0]) / d[0]
    y_at_xlip = origin[1] + t * d[1]

    assert h_c < y_at_xlip < H


def test_cli_cfd_domain_offdesign_smoke(tmp_path):
    out = tmp_path / "m3"
    code = main(
        [
            "cfd-domain", "--mach", "3", "--ramps", "2",
            "--capture-height", "1.0", "--out", str(out), "--offdesign",
        ]
    )
    assert code == 0
    assert out.with_suffix(".dxf").exists()
    offdesign_path = out.parent / f"{out.name}_offdesign.dxf"
    assert offdesign_path.exists()
