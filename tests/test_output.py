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
