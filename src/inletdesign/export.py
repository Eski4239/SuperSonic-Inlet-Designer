"""DXF export of an InletGeometry via ezdxf.

This module (and plotting.py) are the only places in the package that import
ezdxf; physics and geometry modules stay free of output-format dependencies.
"""
import math

import ezdxf


def _to_mm(point):
    return (point[0] * 1000.0, point[1] * 1000.0)


def export_dxf(geom, path, units="mm", include_shocks=True):
    """Export an InletGeometry as a DXF (R2010, millimetres). Returns path."""
    doc = ezdxf.new(dxfversion="R2010")
    doc.header["$INSUNITS"] = 4  # mm

    doc.layers.add("RAMP", color=7)
    doc.layers.add("COWL", color=5)
    if include_shocks:
        doc.layers.add("SHOCKS", color=1)

    msp = doc.modelspace()

    ramp_pts_mm = [_to_mm(p) for p in geom.ramp_points]
    msp.add_lwpolyline(ramp_pts_mm, dxfattribs={"layer": "RAMP"})

    cowl_len = 0.4 * geom.capture_height
    cowl_end = (
        geom.lip[0] + cowl_len * math.cos(math.radians(geom.cowl_angle_deg)),
        geom.lip[1] + cowl_len * math.sin(math.radians(geom.cowl_angle_deg)),
    )
    msp.add_line(_to_mm(geom.lip), _to_mm(cowl_end), dxfattribs={"layer": "COWL"})

    if include_shocks:
        for p0, p1 in geom.shocks:
            msp.add_line(_to_mm(p0), _to_mm(p1), dxfattribs={"layer": "SHOCKS"})

    doc.saveas(path)
    return path
