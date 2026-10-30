"""Drawing model of the inlet: pure Python (no Qt), built from api results, in mm with y up.

Two stages so transitions can animate:
- skeleton_from(design, off): the few numbers that define the drawing (corners, lip, shock
  angles, streamline). Skeletons with the same topology interpolate linearly.
- build(skeleton): walls, flow regions (the flow domain split by the shock lines),
  clipped shock segments, the capture streamtube and dimension annotations.

Drawing-only proportions (duct length, cowl wedge, margins) are illustrative and are not
part of the physics model.
"""
import math
from dataclasses import dataclass, field, replace

MM = 1000.0              # api lengths are metres
LEFT_MARGIN = 0.6        # x of the left edge of the drawing, in capture heights
DUCT_LENGTH = 1.0        # drawn duct length, in capture heights
COWL_WEDGE_DEG = 6.0     # drawn cowl wedge angle
WALL_THICKNESS = 0.07    # drawn wall hatch band, in capture heights
_EPS = 1e-9


# --- small vector helpers ---------------------------------------------------------------

def _dir(angle_deg):
    a = math.radians(angle_deg)
    return (math.cos(a), math.sin(a))


def _add(p, v, s=1.0):
    return (p[0] + s * v[0], p[1] + s * v[1])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp_pt(a, b, t):
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t))


def polygon_area(poly):
    """Shoelace area (positive for counter-clockwise)."""
    n = len(poly)
    return 0.5 * sum(_cross(poly[i], poly[(i + 1) % n]) for i in range(n))


def polygon_centroid(poly):
    a = polygon_area(poly)
    if abs(a) < 1e-12:
        xs, ys = zip(*poly)
        return (sum(xs) / len(xs), sum(ys) / len(ys))
    cx = cy = 0.0
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        c = _cross(p, q)
        cx += (p[0] + q[0]) * c
        cy += (p[1] + q[1]) * c
    return (cx / (6.0 * a), cy / (6.0 * a))


def point_in_polygon(pt, poly):
    inside = False
    x, y = pt
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xc > x:
                inside = not inside
    return inside


def clip_half_plane(poly, origin, normal, keep_positive):
    """Sutherland-Hodgman clip of a polygon by the half-plane sign((X - origin).normal)."""
    sign = 1.0 if keep_positive else -1.0

    def f(p):
        return sign * ((p[0] - origin[0]) * normal[0] + (p[1] - origin[1]) * normal[1])

    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = f(p), f(q)
        if fp >= -_EPS:
            out.append(p)
        if (fp >= -_EPS) != (fq >= -_EPS):
            t = fp / (fp - fq)
            out.append(_lerp_pt(p, q, t))
    return _dedupe(out)


def _dedupe(points, tol=1e-9):
    out = []
    for p in points:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > tol:
            out.append(p)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= tol:
        out.pop()
    return out


def ray_exit(origin, direction, boundary, segments_extra=()):
    """Smallest t > 0 at which origin + t*direction meets a polygon edge or an extra segment."""
    best = math.inf
    edges = [(boundary[i], boundary[(i + 1) % len(boundary)]) for i in range(len(boundary))]
    for a, b in list(edges) + list(segments_extra):
        e = _sub(b, a)
        den = _cross(direction, e)
        if abs(den) < 1e-14:
            continue
        w = _sub(a, origin)
        t = _cross(w, e) / den
        u = _cross(w, direction) / den
        if t > 1e-7 and -1e-9 <= u <= 1.0 + 1e-9:
            best = min(best, t)
    return best


# --- skeleton -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Skeleton:
    h: float                 # capture height, mm
    corners: tuple           # ramp corner points (leading edge first), mm
    foot: tuple              # terminal-shock foot on the ramp side, mm
    lip: tuple               # cowl lip, mm
    phi_n: float             # duct / cowl direction, deg
    shock_angles: tuple      # absolute direction of each ramp shock, deg
    streamline: tuple        # capture streamline points (upstream first, ends at lip), mm
    has_terminal: bool
    mach: float
    off_design: bool
    ramp_angles: tuple       # incremental, deg
    flow_angles: tuple       # cumulative, deg (freestream first)
    regions: tuple           # RegionState x (n + 2); duct reuses the last state if subsonic
    shocks: tuple            # ShockState per ramp shock (+ terminal)
    mass_capture: float

    @property
    def n(self):
        return len(self.shock_angles)

    @property
    def x_left(self):
        return -LEFT_MARGIN * self.h


def _mm(p):
    return (p[0] * MM, p[1] * MM)


def skeleton_from(design, off=None):
    """Skeleton of a DesignResult, or of its frozen geometry at an OffDesignResult's Mach."""
    g = design.geometry
    n = design.inputs.n_ramps
    pts = [_mm(p) for p in g.ramp_points]
    corners = tuple(pts[:n]) if n else ()
    foot = pts[-1]
    lip = _mm(g.lip)
    flow = tuple(design.flow_angles_deg)
    src = off if off is not None else design
    betas = tuple(src.betas_deg)
    regions = tuple(src.regions)
    shocks = tuple(src.shock_states)
    has_terminal = any(s.kind == "normal" for s in shocks)
    if not has_terminal:        # subsonic behind the last ramp: the duct carries that state
        regions = regions + (replace(regions[-1], name="duct (subsonic, no terminal shock)"),)
    if off is not None and off.capture_streamline:
        streamline = tuple(_mm(p) for p in off.capture_streamline)
    else:
        streamline = (lip,)
    return Skeleton(
        h=design.inputs.capture_height * MM, corners=corners, foot=foot, lip=lip,
        phi_n=flow[-1], shock_angles=tuple(flow[i] + betas[i] for i in range(n)),
        streamline=streamline, has_terminal=has_terminal,
        mach=float(src.M_inf if off is not None else design.inputs.M),
        off_design=off is not None, ramp_angles=tuple(design.ramp_angles_deg),
        flow_angles=flow, regions=regions, shocks=shocks,
        mass_capture=float(off.mass_capture_ratio) if off is not None else 1.0,
    )


def same_topology(a, b):
    return a is not None and b is not None and a.n == b.n and a.has_terminal == b.has_terminal


def interpolate(a, b, t):
    """Skeleton between a (t=0) and b (t=1); numbers shown are always b's. b if topologies differ."""
    if t >= 1.0 or not same_topology(a, b):
        return b
    sa, sb = a.streamline, b.streamline
    if len(sa) != len(sb):      # pad the shorter one with its upstream point
        m = max(len(sa), len(sb))
        sa = (sa[0],) * (m - len(sa)) + sa
        sb = (sb[0],) * (m - len(sb)) + sb
    return replace(
        b,
        h=_lerp(a.h, b.h, t),
        corners=tuple(_lerp_pt(p, q, t) for p, q in zip(a.corners, b.corners)),
        foot=_lerp_pt(a.foot, b.foot, t), lip=_lerp_pt(a.lip, b.lip, t),
        phi_n=_lerp(a.phi_n, b.phi_n, t),
        shock_angles=tuple(_lerp(p, q, t) for p, q in zip(a.shock_angles, b.shock_angles)),
        streamline=tuple(_lerp_pt(p, q, t) for p, q in zip(sa, sb)),
    )


# --- picture ------------------------------------------------------------------------------

@dataclass
class Region:
    index: int
    name: str
    polygon: list
    state: object            # api.RegionState


@dataclass
class Shock:
    index: int
    kind: str                # "oblique" | "normal"
    start: tuple
    end: tuple
    state: object            # api.ShockState


@dataclass
class Dimension:
    kind: str                # "linear" | "angle" | "callout"
    label: str               # prefix, e.g. "h_c" or "θ1"
    value: float             # metres for lengths, degrees for angles; None for callouts
    points: tuple            # linear: (a, b, d0, d1); angle: (centre,); callout: (point, text_at)
    radius: float = 0.0      # angle only
    angles: tuple = ()       # angle only: (start, end) deg
    extra: tuple = ()        # callout only: values (x, y) in metres
    text_at: tuple = None


@dataclass
class Picture:
    skeleton: Skeleton
    domain: list
    ramp_surface: list       # wall line on the flow side, leading edge to duct exit
    ramp_body: list          # hatched band below the ramp surface
    cowl_body: list          # hatched wedge
    cowl_inner: list
    cowl_outer: list
    regions: list = field(default_factory=list)
    shocks: list = field(default_factory=list)
    streamtube: list = field(default_factory=list)
    dimensions: list = field(default_factory=list)
    arrow: tuple = ()        # (tail, head)

    def bounds(self):
        pts = list(self.domain) + list(self.ramp_body) + list(self.cowl_body)
        xs, ys = zip(*pts)
        return min(xs), min(ys), max(xs), max(ys)


def _normal_downstream(angle_deg):
    """Unit normal of a shock line pointing to its downstream side."""
    a = math.radians(angle_deg)
    return (math.sin(a), -math.cos(a))


def build(sk):
    h = sk.h
    duct = _dir(sk.phi_n)
    le = sk.corners[0] if sk.corners else sk.foot
    floor_end = _add(sk.foot, duct, DUCT_LENGTH * h)
    cowl_end = _add(sk.lip, duct, DUCT_LENGTH * h)

    ramp_surface = _dedupe([le, *sk.corners[1:], sk.foot, floor_end])
    domain = _dedupe([(sk.x_left, 0.0), (min(0.0, le[0]), 0.0), *ramp_surface,
                      cowl_end, sk.lip, (sk.x_left, h)])

    t = WALL_THICKNESS * h
    lower = [(p[0], p[1] - t) for p in ramp_surface[1:]]
    ramp_body = ramp_surface + lower[::-1] + [(le[0] + 2.5 * t, le[1] - t)]

    wedge_len = DUCT_LENGTH * h / math.cos(math.radians(COWL_WEDGE_DEG))
    cowl_outer_end = _add(sk.lip, _dir(sk.phi_n + COWL_WEDGE_DEG), wedge_len)
    cowl_body = [sk.lip, cowl_end, cowl_outer_end]

    pic = Picture(skeleton=sk, domain=domain, ramp_surface=ramp_surface, ramp_body=ramp_body,
                  cowl_body=cowl_body, cowl_inner=[sk.lip, cowl_end],
                  cowl_outer=[sk.lip, cowl_outer_end])

    # Shock lines: (origin, absolute angle). Terminal shock spans foot -> lip.
    terminal_angle = sk.phi_n + 90.0
    terminal_seg = (sk.foot, sk.lip)
    lines = [(sk.corners[i], sk.shock_angles[i]) for i in range(sk.n)]

    for i, (origin, angle) in enumerate(lines):
        d = _dir(angle)
        t_end = ray_exit(origin, d, domain, [terminal_seg])
        end = _add(origin, d, t_end) if math.isfinite(t_end) else origin
        if not sk.off_design:
            end = sk.lip          # shock-on-lip by construction
        pic.shocks.append(Shock(i, "oblique", origin, end, sk.shocks[i]))
    if sk.has_terminal:
        pic.shocks.append(Shock(sk.n, "normal", sk.foot, sk.lip, sk.shocks[sk.n]))

    # Regions: the domain split by half-planes of the shock lines and the terminal line.
    t_normal = _normal_downstream(terminal_angle)
    upstream_of_terminal = clip_half_plane(domain, sk.foot, t_normal, keep_positive=False)
    for k in range(sk.n + 1):
        poly = upstream_of_terminal
        for i in range(k):
            o, a = lines[i]
            poly = clip_half_plane(poly, o, _normal_downstream(a), keep_positive=True)
        if k < sk.n:
            o, a = lines[k]
            poly = clip_half_plane(poly, o, _normal_downstream(a), keep_positive=False)
        pic.regions.append(Region(k, sk.regions[k].name, poly, sk.regions[k]))
    duct_poly = clip_half_plane(domain, sk.foot, t_normal, keep_positive=True)
    pic.regions.append(Region(sk.n + 1, sk.regions[sk.n + 1].name, duct_poly,
                              sk.regions[sk.n + 1]))

    first = sk.streamline[0]
    pic.streamtube = [(sk.x_left, first[1]), *sk.streamline]
    y_arrow = 0.62 * h
    pic.arrow = ((sk.x_left + 0.08 * h, y_arrow), (sk.x_left + 0.42 * h, y_arrow))
    pic.dimensions = _dimensions(sk, ramp_surface)
    return pic


def _dimensions(sk, ramp_surface):
    h = sk.h
    dims = []
    # Ramp angles: arc at each corner between the incoming and outgoing wall directions.
    for i in range(sk.n):
        c = sk.corners[i]
        a0, a1 = sk.flow_angles[i], sk.flow_angles[i + 1]
        r = 0.32 * h
        label_at = _add(c, _dir(a1 + 6.0), r * 1.45)      # just above the outgoing wall
        dims.append(Dimension("angle", f"θ{i + 1}", sk.ramp_angles[i], (c,), radius=r,
                              angles=(a0, a1), text_at=label_at))
    # Ramp lengths: offset dimension below each ramp segment.
    ends = list(sk.corners) + [sk.foot]
    for i in range(sk.n):
        a, b = ends[i], ends[i + 1]
        nrm = _normal_downstream(sk.flow_angles[i] + 0.0)   # points below the wall
        off = 0.24 * h
        d0, d1 = _add(a, nrm, off), _add(b, nrm, off)
        length = math.hypot(b[0] - a[0], b[1] - a[1]) / MM
        dims.append(Dimension("linear", f"L{i + 1}", length, (a, b, d0, d1),
                              text_at=_add(_lerp_pt(d0, d1, 0.5), nrm, 0.08 * h)))
    # Capture height: vertical dimension left of the drawn flow domain.
    x = sk.x_left - 0.12 * h
    dims.append(Dimension("linear", "h_c", sk.h / MM,
                          ((sk.x_left, 0.0), (sk.x_left, h), (x, 0.0), (x, h)),
                          text_at=(x - 0.04 * h, 0.5 * h)))
    # Duct entry (throat) height along the terminal line, offset into the duct.
    duct = _dir(sk.phi_n)
    off = 0.35 * h
    d0, d1 = _add(sk.foot, duct, off), _add(sk.lip, duct, off)
    throat = math.hypot(sk.lip[0] - sk.foot[0], sk.lip[1] - sk.foot[1]) / MM
    dims.append(Dimension("linear", "h_t", throat, (sk.foot, sk.lip, d0, d1),
                          text_at=_add(_lerp_pt(d0, d1, 0.5), duct, 0.08 * h)))
    # Lip position callout.
    dims.append(Dimension("callout", "lip", None, (sk.lip,),
                          extra=(sk.lip[0] / MM, sk.lip[1] / MM),
                          text_at=_add(sk.lip, (-0.15 * h, 0.22 * h))))
    return dims
