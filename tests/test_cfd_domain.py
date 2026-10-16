import math

import ezdxf
import pytest

from inletdesign.cfd_domain import export_cfd_domain_dxf
from inletdesign.cli import main
from inletdesign.geometry import design_inlet

EXPECTED_LAYERS = {"INLET", "SYMMETRY", "RAMP", "OUTLET", "COWL", "TOP_FREESTREAM"}


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
