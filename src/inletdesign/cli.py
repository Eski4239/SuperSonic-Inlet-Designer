"""Command-line interface for supersonic-inlet-designer.

Thin argparse layer over the existing library: no shock-relation or
optimization formulas live here.
"""
import argparse
import csv
import json
import os
import sys
from importlib.metadata import PackageNotFoundError, version

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import inlet as _inlet
from .cfd_domain import export_cfd_domain_dxf
from .export import export_dxf
from .geometry import design_inlet
from .optimize import optimize_equal_strength
from .plotting import _BG_COLOR, _RAMP_COLOR, save_inlet_plot


class CliError(Exception):
    """Raised for invalid user input; caught once in main() for a clean exit."""


def _package_version():
    try:
        return version("supersonic-inlet-designer")
    except PackageNotFoundError:
        return "0.1.0"


def _cumulative_angles(ramp_angles_deg):
    phis = [0.0]
    for theta in ramp_angles_deg:
        phis.append(phis[-1] + theta)
    return phis[1:]


def _handle_design(args):
    if args.mach <= 1:
        raise CliError("mach must be > 1")
    if args.ramps < 0:
        raise CliError("ramps must be >= 0")

    geom = design_inlet(args.mach, args.ramps, capture_height=args.capture_height)
    states = _inlet.compress(args.mach, geom.ramp_angles_deg)
    cumulative = _cumulative_angles(geom.ramp_angles_deg)

    machs = [args.mach] + [s.M for s in states]
    p0_ratios = [1.0] + [s.p0_ratio for s in states]
    recovery = states[-1].p0_ratio if states else 1.0

    print(f"Design: M_inf={args.mach:.3f}  ramps={args.ramps}")
    print(f"{'ramp':>6} {'incr deg':>10} {'cumul deg':>10} {'beta deg':>10}")
    for i in range(args.ramps):
        beta = geom.betas_deg[i]
        print(
            f"{i + 1:>6} {geom.ramp_angles_deg[i]:>10.4f} {cumulative[i]:>10.4f} {beta:>10.4f}"
        )
    print()
    print(f"{'region':>8} {'Mach':>10} {'p0/p0_inf':>12}")
    print(f"{'inf':>8} {machs[0]:>10.4f} {p0_ratios[0]:>12.4f}")
    for i in range(1, len(machs)):
        label = f"shock{i}" if i < len(machs) - 1 else "terminal"
        print(f"{label:>8} {machs[i]:>10.4f} {p0_ratios[i]:>12.4f}")
    print()
    print(f"total recovery (pi_d): {recovery:.4f}")
    print(f"capture height: {geom.capture_height:.4f}")
    print(f"throat height:  {geom.throat_height:.4f}")
    print(f"lip position:   ({geom.lip[0]:.4f}, {geom.lip[1]:.4f})")

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    png_path = f"{args.out}.png"
    dxf_path = f"{args.out}.dxf"
    json_path = f"{args.out}.json"

    save_inlet_plot(geom, png_path, units=args.units)
    export_dxf(geom, dxf_path, include_shocks=not args.no_shocks_in_dxf)

    result = {
        "inputs": {
            "mach": args.mach,
            "ramps": args.ramps,
            "capture_height": args.capture_height,
            "units": args.units,
        },
        "ramp_angles_deg": geom.ramp_angles_deg,
        "cumulative_angles_deg": cumulative,
        "beta_angles_deg": geom.betas_deg,
        "region_mach": machs,
        "region_p0_ratio": p0_ratios,
        "recovery": recovery,
        "capture_height": geom.capture_height,
        "throat_height": geom.throat_height,
        "lip": list(geom.lip),
        "package_version": _package_version(),
    }
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)

    return 0


def _handle_curve(args):
    for n in args.ramps:
        if n < 0:
            raise CliError("ramps must be >= 0")
    if args.mach_min >= args.mach_max:
        raise CliError("mach-min must be < mach-max")
    if args.step <= 0:
        raise CliError("step must be > 0")

    mach_values = np.arange(args.mach_min, args.mach_max + args.step / 2.0, args.step)

    rows = []
    skipped = 0
    for n_ramps in args.ramps:
        for M in mach_values:
            try:
                result = optimize_equal_strength(float(M), n_ramps)
            except ValueError:
                skipped += 1
                continue
            rows.append((float(M), n_ramps, result["recovery"], result["ramps"]))

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    csv_path = f"{args.out}.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["M_inf", "n_ramps", "recovery", "ramp_angles_deg"])
        for M, n_ramps, recovery, ramps in rows:
            ramps_str = ";".join(f"{a:.6f}" for a in ramps)
            writer.writerow([f"{M:.6f}", n_ramps, f"{recovery:.6f}", ramps_str])

    fig, ax = plt.subplots()
    fig.patch.set_facecolor(_BG_COLOR)
    ax.set_facecolor(_BG_COLOR)
    for n_ramps in args.ramps:
        xs = [r[0] for r in rows if r[1] == n_ramps]
        ys = [r[2] for r in rows if r[1] == n_ramps]
        ax.plot(xs, ys, label=f"{n_ramps} ramps", linewidth=1.2)
    ax.set_xlabel("M∞")
    ax.set_ylabel("$\\pi_d$ = p02/p01")
    ax.grid(True, alpha=0.3)
    ax.legend()
    png_path = f"{args.out}.png"
    fig.savefig(png_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)

    print(f"skipped {skipped} infeasible combinations", file=sys.stderr)

    return 0


def _handle_cfd_domain(args):
    if args.mach <= 1:
        raise CliError("mach must be > 1")
    if args.ramps < 0:
        raise CliError("ramps must be >= 0")

    geom = design_inlet(args.mach, args.ramps, capture_height=args.capture_height)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    dxf_path = f"{args.out}.dxf"
    export_cfd_domain_dxf(geom, dxf_path)
    print(f"wrote {dxf_path}")

    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="inletdesign")
    subparsers = parser.add_subparsers(dest="command", required=True)

    design_parser = subparsers.add_parser("design", help="design a single inlet")
    design_parser.add_argument("--mach", type=float, required=True)
    design_parser.add_argument("--ramps", type=int, required=True)
    design_parser.add_argument("--capture-height", type=float, default=1.0)
    design_parser.add_argument("--out", type=str, default="results/design")
    design_parser.add_argument("--units", choices=["hc", "m", "mm"], default="hc")
    design_parser.add_argument("--no-shocks-in-dxf", action="store_true")
    design_parser.set_defaults(handler=_handle_design)

    curve_parser = subparsers.add_parser("curve", help="sweep recovery vs Mach")
    curve_parser.add_argument("--ramps", type=int, nargs="+", required=True)
    curve_parser.add_argument("--mach-min", type=float, required=True)
    curve_parser.add_argument("--mach-max", type=float, required=True)
    curve_parser.add_argument("--step", type=float, required=True)
    curve_parser.add_argument("--out", type=str, default="results/curve")
    curve_parser.set_defaults(handler=_handle_curve)

    cfd_domain_parser = subparsers.add_parser(
        "cfd-domain", help="export a closed CFD fluid-domain outline (DXF)"
    )
    cfd_domain_parser.add_argument("--mach", type=float, required=True)
    cfd_domain_parser.add_argument("--ramps", type=int, required=True)
    cfd_domain_parser.add_argument("--capture-height", type=float, default=1.0)
    cfd_domain_parser.add_argument("--out", type=str, default="results/cfd_domain")
    cfd_domain_parser.set_defaults(handler=_handle_cfd_domain)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
