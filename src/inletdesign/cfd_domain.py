"""CFD fluid-domain outline export for Phase 3 meshing (SpaceClaim/Fluent import).

Design-point domain only: the captured streamtube at the shock-on-lip design
condition, extended downstream by a straight constant-area duct. Off-design
operation (spillage, an external flow region ahead of the cowl) is not
modeled here; that would require a farfield boundary and an external cowl
surface, deferred to a later Phase 3 step.
"""
import math

import ezdxf


def _to_mm(point):
    return (point[0] * 1000.0, point[1] * 1000.0)


def export_cfd_domain_dxf(geom, path, duct_length_factor=2.0):
    """Write a closed 2D fluid-domain outline (mm, DXF R2010) with one layer per boundary.

    Layers: INLET, SYMMETRY, RAMP, OUTLET, COWL, TOP_FREESTREAM. The outline is
    one closed loop: INLET -> TOP_FREESTREAM -> COWL -> OUTLET -> RAMP ->
    SYMMETRY -> back to INLET's start.

    Raises:
        ValueError: if the resulting loop does not close (start and end
            points differ by more than 1e-9, in geometry units).
    """
    h_c = geom.capture_height
    tip = geom.ramp_points[0]
    terminal_foot = geom.ramp_points[-1]
    lip = geom.lip
    phi_n = geom.cowl_angle_deg
    dir_n = (math.cos(math.radians(phi_n)), math.sin(math.radians(phi_n)))

    inlet_bottom = (tip[0] - 1.0 * h_c, 0.0)
    inlet_top = (tip[0] - 1.0 * h_c, h_c)
    ramp_duct_end = (
        terminal_foot[0] + duct_length_factor * h_c * dir_n[0],
        terminal_foot[1] + duct_length_factor * h_c * dir_n[1],
    )
    cowl_inner_end = (
        lip[0] + duct_length_factor * h_c * dir_n[0],
        lip[1] + duct_length_factor * h_c * dir_n[1],
    )

    ramp_polyline = list(geom.ramp_points) + [ramp_duct_end]

    full_loop = (
        [inlet_bottom, inlet_top, lip, cowl_inner_end, ramp_duct_end]
        + list(reversed(geom.ramp_points[:-1]))
        + [tip, inlet_bottom]
    )
    closure_gap = math.hypot(
        full_loop[0][0] - full_loop[-1][0], full_loop[0][1] - full_loop[-1][1]
    )
    if closure_gap > 1e-9:
        raise ValueError(f"CFD domain outline does not close (gap={closure_gap})")

    boundaries = [
        ("INLET", [inlet_bottom, inlet_top]),
        ("TOP_FREESTREAM", [lip, inlet_top]),
        ("COWL", [cowl_inner_end, lip]),
        ("OUTLET", [ramp_duct_end, cowl_inner_end]),
        ("RAMP", ramp_polyline),
        ("SYMMETRY", [inlet_bottom, tip]),
    ]

    doc = ezdxf.new(dxfversion="R2010")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()

    layer_colors = {
        "INLET": 1,
        "SYMMETRY": 2,
        "RAMP": 7,
        "OUTLET": 3,
        "COWL": 5,
        "TOP_FREESTREAM": 6,
    }
    for name, color in layer_colors.items():
        doc.layers.add(name, color=color)

    for layer_name, points in boundaries:
        points_mm = [_to_mm(p) for p in points]
        if len(points_mm) == 2:
            msp.add_line(points_mm[0], points_mm[1], dxfattribs={"layer": layer_name})
        else:
            msp.add_lwpolyline(points_mm, dxfattribs={"layer": layer_name})

    doc.saveas(path)
    return path
