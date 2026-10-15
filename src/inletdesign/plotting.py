"""Technical line-drawing rendering of an InletGeometry via matplotlib.

Never calls plt.show() -- the caller decides whether to show or save the
returned figure. This module (and export.py) are the only places in the
package that import matplotlib; physics and geometry modules stay free of it.
"""
import math

import matplotlib.pyplot as plt

from . import inlet as _inlet

_RAMP_COLOR = "#1a1a1a"
_SHOCK_COLOR = "#E4572E"
_BG_COLOR = "#FAFAFA"


def plot_inlet(geom, ax=None, annotate=True):
    """Render an InletGeometry as a technical line drawing. Returns (fig, ax)."""
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    fig.patch.set_facecolor(_BG_COLOR)
    ax.set_facecolor(_BG_COLOR)

    ramp_xs = [p[0] for p in geom.ramp_points]
    ramp_ys = [p[1] for p in geom.ramp_points]
    ax.plot(ramp_xs, ramp_ys, color=_RAMP_COLOR, linewidth=1.2, label="ramp", gid="ramp")

    cowl_len = 0.4 * geom.capture_height
    cowl_end = (
        geom.lip[0] + cowl_len * math.cos(math.radians(geom.cowl_angle_deg)),
        geom.lip[1] + cowl_len * math.sin(math.radians(geom.cowl_angle_deg)),
    )
    ax.plot(
        [geom.lip[0], cowl_end[0]], [geom.lip[1], cowl_end[1]],
        color=_RAMP_COLOR, linewidth=1.2, label="cowl", gid="cowl",
    )

    n_shocks = len(geom.shocks)
    for i, (p0, p1) in enumerate(geom.shocks):
        is_terminal = i == n_shocks - 1
        ax.plot(
            [p0[0], p1[0]], [p0[1], p1[1]],
            color=_SHOCK_COLOR, linewidth=1.0,
            linestyle="--" if is_terminal else "-",
            label="shock", gid=f"shock_{i}",
        )

    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)

    if annotate:
        states = _inlet.compress(geom.M_inf, geom.ramp_angles_deg, gamma=1.4)

        ax.text(
            ramp_xs[0], ramp_ys[0] - 0.05 * geom.capture_height,
            f"M={geom.M_inf:.3f}", family="monospace", fontsize=8, ha="left", va="top",
        )
        for i, state in enumerate(states):
            region_point = geom.shocks[i][0]
            ax.text(
                region_point[0], region_point[1] - 0.05 * geom.capture_height,
                f"M={state.M:.3f}", family="monospace", fontsize=8, ha="left", va="top",
            )
        for i, theta in enumerate(geom.ramp_angles_deg):
            corner = geom.ramp_points[i]
            ax.text(
                corner[0], corner[1] + 0.05 * geom.capture_height,
                f"{theta:.2f} deg", family="monospace", fontsize=8, ha="left", va="bottom",
            )

        recovery = states[-1].p0_ratio if states else 1.0
        ax.set_title(
            f"M_inf={geom.M_inf:.2f}  ramps={len(geom.ramp_angles_deg)}  recovery={recovery:.4f}",
            family="monospace",
        )

    return fig, ax


def save_inlet_plot(geom, path, annotate=True):
    """Builds the plot and saves it as PNG or SVG based on path's extension, dpi=200."""
    fig, _ = plot_inlet(geom, annotate=annotate)
    fig.savefig(path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path
