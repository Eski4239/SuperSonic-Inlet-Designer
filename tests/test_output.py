import matplotlib

matplotlib.use("Agg")

import ezdxf
import pytest
from matplotlib.lines import Line2D

from inletdesign import geometry as geo
from inletdesign.export import export_dxf
from inletdesign.plotting import plot_inlet, save_inlet_plot


def _geometry_for(M_inf, n_ramps):
    return geo.design_inlet(M_inf, n_ramps)


@pytest.fixture(params=[0, 1, 2, 3])
def geom(request):
    return _geometry_for(3.0, request.param)


def test_plot_inlet_returns_figure(geom):
    fig, ax = plot_inlet(geom)
    assert fig is not None
    assert ax is not None


def test_save_png_and_svg_nonempty(geom, tmp_path):
    png_path = tmp_path / "x.png"
    svg_path = tmp_path / "x.svg"
    save_inlet_plot(geom, png_path)
    save_inlet_plot(geom, svg_path)
    assert png_path.stat().st_size > 0
    assert svg_path.stat().st_size > 0


def test_plot_line_counts(geom):
    fig, ax = plot_inlet(geom)
    lines = [artist for artist in ax.get_lines() if isinstance(artist, Line2D)]

    ramp_lines = [line for line in lines if line.get_gid() == "ramp"]
    cowl_lines = [line for line in lines if line.get_gid() == "cowl"]
    shock_lines = [line for line in lines if line.get_gid() and line.get_gid().startswith("shock_")]

    assert len(ramp_lines) == 1
    assert len(cowl_lines) == 1
    assert len(shock_lines) == len(geom.shocks)


def test_dxf_layers_and_units(geom, tmp_path):
    path = tmp_path / "x.dxf"
    export_dxf(geom, str(path))
    doc = ezdxf.readfile(str(path))

    layer_names = {layer.dxf.name for layer in doc.layers}
    assert "RAMP" in layer_names
    assert "COWL" in layer_names
    assert "SHOCKS" in layer_names
    assert doc.header["$INSUNITS"] == 4


def test_dxf_ramp_vertices_match_geometry(geom, tmp_path):
    path = tmp_path / "x.dxf"
    export_dxf(geom, str(path))
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()

    polylines = [e for e in msp if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "RAMP"]
    assert len(polylines) == 1
    vertices = [(p[0], p[1]) for p in polylines[0].get_points()]

    expected = [(x * 1000.0, y * 1000.0) for x, y in geom.ramp_points]
    assert len(vertices) == len(expected)
    for (vx, vy), (ex, ey) in zip(vertices, expected):
        assert vx == pytest.approx(ex, abs=1e-6)
        assert vy == pytest.approx(ey, abs=1e-6)


def test_dxf_include_shocks_false(geom, tmp_path):
    path = tmp_path / "x.dxf"
    export_dxf(geom, str(path), include_shocks=False)
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()

    shock_entities = [e for e in msp if getattr(e.dxf, "layer", None) == "SHOCKS"]
    assert len(shock_entities) == 0


def test_mach_labels_outside_ramp_body_and_distinct(geom):
    fig, ax = plot_inlet(geom, units="hc")
    h_c = 1.0  # units="hc" normalizes capture_height to 1.0 in display coordinates

    mach_labels = [t for t in ax.texts if t.get_gid() and t.get_gid().startswith("mach_label_")]
    assert len(mach_labels) > 0

    divisor = geom.capture_height
    ramp_disp = [(p[0] / divisor, p[1] / divisor) for p in geom.ramp_points]
    ramp_xs = [p[0] for p in ramp_disp]
    ramp_ys = [p[1] for p in ramp_disp]

    def ramp_height_at(x):
        if x < ramp_xs[0] or x > ramp_xs[-1]:
            return None
        for i in range(len(ramp_xs) - 1):
            x0, x1 = ramp_xs[i], ramp_xs[i + 1]
            if x0 <= x <= x1:
                if x1 == x0:
                    return ramp_ys[i]
                frac = (x - x0) / (x1 - x0)
                return ramp_ys[i] + frac * (ramp_ys[i + 1] - ramp_ys[i])
        return None

    positions = [t.get_position() for t in mach_labels]
    for x, y in positions:
        ramp_y = ramp_height_at(x)
        if ramp_y is not None:
            assert y > ramp_y

    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            dx = positions[i][0] - positions[j][0]
            dy = positions[i][1] - positions[j][1]
            dist = (dx**2 + dy**2) ** 0.5
            assert dist >= 0.05 * h_c
