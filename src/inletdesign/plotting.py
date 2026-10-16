"""Technical line-drawing rendering of an InletGeometry via matplotlib.

Never calls plt.show() -- the caller decides whether to show or save the
returned figure. This module (and export.py) are the only places in the
package that import matplotlib; physics and geometry modules stay free of it.
"""
import math

import matplotlib.pyplot as plt
from matplotlib.patches import Arc

from . import inlet as _inlet

_RAMP_COLOR = "#1a1a1a"
_SHOCK_COLOR = "#E4572E"
_BG_COLOR = "#FAFAFA"

_UNIT_LABELS = {
    "hc": ("x / h_c", "y / h_c"),
    "m": ("x (m)", "y (m)"),
    "mm": ("x (mm)", "y (mm)"),
}


def _display_divisor(geom, units):
    if units == "hc":
        return geom.capture_height
    if units == "mm":
        return 1.0 / 1000.0
    if units == "m":
        return 1.0
    raise ValueError(f"unknown units {units!r}; expected 'hc', 'm', or 'mm'")


def _to_display(point, divisor):
    return (point[0] / divisor, point[1] / divisor)


def plot_inlet(geom, ax=None, annotate=True, units="hc"):
    """Render an InletGeometry as a technical line drawing. Returns (fig, ax)."""
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    divisor = _display_divisor(geom, units)
    h_c = geom.capture_height / divisor
    xlabel, ylabel = _UNIT_LABELS[units]

    fig.patch.set_facecolor(_BG_COLOR)
    ax.set_facecolor(_BG_COLOR)

    ramp_disp = [_to_display(p, divisor) for p in geom.ramp_points]
    ramp_xs = [p[0] for p in ramp_disp]
    ramp_ys = [p[1] for p in ramp_disp]
    ax.plot(ramp_xs, ramp_ys, color=_RAMP_COLOR, linewidth=1.2, label="ramp", gid="ramp")

    lip_disp = _to_display(geom.lip, divisor)
    cowl_len = 0.4 * h_c
    cowl_end_disp = (
        lip_disp[0] + cowl_len * math.cos(math.radians(geom.cowl_angle_deg)),
        lip_disp[1] + cowl_len * math.sin(math.radians(geom.cowl_angle_deg)),
    )
    ax.plot(
        [lip_disp[0], cowl_end_disp[0]], [lip_disp[1], cowl_end_disp[1]],
        color=_RAMP_COLOR, linewidth=1.2, label="cowl", gid="cowl",
    )

    n_shocks = len(geom.shocks)
    for i, (p0, p1) in enumerate(geom.shocks):
        p0d, p1d = _to_display(p0, divisor), _to_display(p1, divisor)
        is_terminal = i == n_shocks - 1
        ax.plot(
            [p0d[0], p1d[0]], [p0d[1], p1d[1]],
            color=_SHOCK_COLOR, linewidth=1.0,
            linestyle="--" if is_terminal else "-",
            label="shock", gid=f"shock_{i}",
        )

    # Ramp body fill (hatched, below the ramp surface).
    fill_bottom = min(ramp_ys) - 0.3 * h_c
    ax.fill_between(
        ramp_xs, ramp_ys, y2=fill_bottom,
        color="lightgrey", hatch="//", alpha=0.5, zorder=0, edgecolor="grey",
    )

    # Thin filled cowl body above the cowl line.
    cowl_thickness = 0.03 * h_c
    perp_angle = math.radians(geom.cowl_angle_deg + 90.0)
    offset = (cowl_thickness * math.cos(perp_angle), cowl_thickness * math.sin(perp_angle))
    cowl_quad_x = [
        lip_disp[0], cowl_end_disp[0],
        cowl_end_disp[0] + offset[0], lip_disp[0] + offset[0],
    ]
    cowl_quad_y = [
        lip_disp[1], cowl_end_disp[1],
        cowl_end_disp[1] + offset[1], lip_disp[1] + offset[1],
    ]
    ax.fill(cowl_quad_x, cowl_quad_y, color=_RAMP_COLOR, alpha=0.8, zorder=1)

    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    phis = [0.0]
    for theta in geom.ramp_angles_deg:
        phis.append(phis[-1] + theta)

    n_ramps = len(geom.ramp_angles_deg)

    if annotate:
        states = _inlet.compress(geom.M_inf, geom.ramp_angles_deg, gamma=1.4)

        # Freestream label: upstream of shock 1, roughly mid-height.
        freestream_point = (geom.ramp_points[0][0] - 0.15 * geom.capture_height,
                             geom.ramp_points[0][1] + 0.5 * geom.capture_height)
        label_points = [freestream_point]

        # Post-ramp-shock region centroids: triangle [corner_i, next_corner, lip].
        for i in range(1, n_ramps + 1):
            corner_i = geom.ramp_points[i - 1]
            next_corner = geom.ramp_points[i]
            centroid = (
                (corner_i[0] + next_corner[0] + geom.lip[0]) / 3.0,
                (corner_i[1] + next_corner[1] + geom.lip[1]) / 3.0,
            )
            label_points.append(centroid)

        # Post-terminal-shock region: midpoint of (terminal_foot, lip), nudged downstream.
        terminal_foot = geom.ramp_points[-1]
        post_terminal = (
            (terminal_foot[0] + geom.lip[0]) / 2.0 + 0.1 * geom.capture_height,
            (terminal_foot[1] + geom.lip[1]) / 2.0,
        )
        label_points.append(post_terminal)

        machs = [geom.M_inf] + [s.M for s in states]
        for i, (point, M) in enumerate(zip(label_points, machs)):
            disp = _to_display(point, divisor)
            ax.text(
                disp[0], disp[1], f"M={M:.3f}",
                family="monospace", fontsize=8, ha="center", va="center",
                gid=f"mach_label_{i}",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.75, edgecolor="none"),
            )

        # Angle arcs + labels at each turning corner (geom.ramp_points[0..n_ramps-1]).
        arc_radius = 0.08 * h_c
        label_radius = 0.12 * h_c
        for i in range(n_ramps):
            corner_disp = _to_display(geom.ramp_points[i], divisor)
            theta1, theta2 = phis[i], phis[i + 1]
            ax.add_patch(
                Arc(
                    corner_disp, width=2 * arc_radius, height=2 * arc_radius,
                    theta1=theta1, theta2=theta2, color=_RAMP_COLOR, linewidth=0.8,
                )
            )
            bisector = math.radians((theta1 + theta2) / 2.0)
            label_pos = (
                corner_disp[0] + label_radius * math.cos(bisector),
                corner_disp[1] + label_radius * math.sin(bisector),
            )
            ax.text(
                label_pos[0], label_pos[1], f"{geom.ramp_angles_deg[i]:.2f}°",
                family="monospace", fontsize=7, ha="center", va="center",
            )

        recovery = states[-1].p0_ratio if states else 1.0
        ax.set_title(
            f"{n_ramps}-ramp external-compression inlet, M∞ = {geom.M_inf:.2f}\n"
            f"$\\pi_d$ = p02/p01 = {recovery:.3f}  ·  shock-on-lip",
            family="monospace",
        )

    # Freestream arrow, drawn in the left margin, ending at the ramp tip.
    ramp_tip_disp = ramp_disp[0]
    arrow_len = 0.25 * h_c
    arrow_start = (ramp_tip_disp[0] - arrow_len, ramp_tip_disp[1])
    ax.annotate(
        "", xy=ramp_tip_disp, xytext=arrow_start,
        arrowprops=dict(arrowstyle="->", color=_RAMP_COLOR, linewidth=1.0),
    )
    ax.text(
        arrow_start[0], arrow_start[1] + 0.05 * h_c,
        f"M∞ = {geom.M_inf:.2f}", family="monospace", fontsize=8, ha="left", va="bottom",
    )

    # Margins: 0.3*h_c upstream of the ramp tip, 0.2*h_c around everything else.
    all_xs = ramp_xs + [cowl_end_disp[0], lip_disp[0], arrow_start[0]]
    all_ys = ramp_ys + [cowl_end_disp[1], lip_disp[1]]
    x_min, x_max = min(all_xs), max(all_xs)
    y_min, y_max = min(all_ys), max(all_ys)
    ax.set_xlim(min(x_min, ramp_tip_disp[0] - 0.3 * h_c) - 0.2 * h_c, x_max + 0.2 * h_c)
    ax.set_ylim(y_min - 0.2 * h_c, y_max + 0.2 * h_c)

    return fig, ax


def save_inlet_plot(geom, path, annotate=True, units="hc"):
    """Builds the plot and saves it as PNG or SVG based on path's extension, dpi=200."""
    fig, _ = plot_inlet(geom, annotate=annotate, units=units)
    fig.savefig(path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path
