"""InletScene: Qt graphics items for a Picture (scene units are mm; scene y = -model y)."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPen, QPolygonF, QTransform
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsPathItem, QGraphicsPolygonItem, QGraphicsRectItem, QGraphicsScene,
    QGraphicsSimpleTextItem,
)

from inletdesign import units as _units

from .. import theme
from ..theme import tokens
from ..views import format as fmt

LAYERS = ("regions", "walls", "shocks", "streamtube", "dimensions", "annotations", "selection")
TOGGLEABLE = ("shocks", "regions", "dimensions", "grid")
_Z = {name: i for i, name in enumerate(LAYERS)}


def S(p):
    """Model (x, y-up, mm) -> scene point."""
    return QPointF(p[0], -p[1])


def M(qp):
    """Scene point -> model (x, y-up, mm)."""
    return (qp.x(), -qp.y())


def color(name, alpha=None):
    c = QColor(tokens.COLORS[name])
    if alpha is not None:
        c.setAlphaF(alpha)
    return c


def pen(name, width=1.0, style=Qt.PenStyle.SolidLine, alpha=None):
    p = QPen(color(name, alpha), width, style)
    p.setCosmetic(True)               # width in screen px at any zoom
    p.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return p


def mach_color(M_value, M_max):
    """Linear interpolation along tokens.MACH_RAMP for M in [0, M_max]."""
    stops = [QColor(c) for c in tokens.MACH_RAMP]
    x = min(max(M_value / M_max, 0.0), 1.0) * (len(stops) - 1) if M_max > 0 else 0.0
    i = min(int(x), len(stops) - 2)
    f = x - i
    a, b = stops[i], stops[i + 1]
    c = QColor.fromRgbF(a.redF() + (b.redF() - a.redF()) * f,
                        a.greenF() + (b.greenF() - a.greenF()) * f,
                        a.blueF() + (b.blueF() - a.blueF()) * f)
    c.setAlphaF(tokens.REGION_ALPHA)
    return c


def mach_scale_max(M_inf):
    """Legend range 0 .. ceil(M_inf)."""
    return float(max(1, math.ceil(M_inf - 1e-9)))


def _poly(points):
    return QPolygonF([S(p) for p in points])


def _path(points):
    path = QPainterPath()
    if points:
        path.moveTo(S(points[0]))
        for p in points[1:]:
            path.lineTo(S(p))
    return path


class _Layer(QGraphicsRectItem):
    """Invisible parent: visibility and opacity propagate to its children."""

    def __init__(self, z):
        super().__init__(QRectF())
        self.setPen(Qt.PenStyle.NoPen)
        self.setZValue(z)


class Label(QGraphicsSimpleTextItem):
    """Mono label of constant screen size anchored at a scene point (centre by default)."""

    def __init__(self, text="", parent=None, size=tokens.SIZE_LABEL, color_name="text_muted",
                 anchor="center"):
        super().__init__(text, parent)
        self.setFont(theme.mono_font(size))
        self.setBrush(color(color_name))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.anchor = anchor
        self._reanchor()

    def set(self, text, model_pt):
        self.setText(text)
        self.setPos(S(model_pt))
        self._reanchor()

    def _reanchor(self):
        r = self.boundingRect()
        dx = {"center": -r.width() / 2, "left": 0.0, "right": -r.width()}[self.anchor]
        self.setTransform(QTransform.fromTranslate(dx, -r.height() / 2))


class InletScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(color("surface")))
        self.layers = {name: _Layer(_Z[name]) for name in LAYERS}
        for layer in self.layers.values():
            self.addItem(layer)
        self.picture = None
        self.units = "SI"
        self.region_items = []
        self.shock_items = []
        self._dim_items = []
        self._build_static()

    # --- static items ------------------------------------------------------------------
    def _build_static(self):
        walls = self.layers["walls"]
        hatch = QBrush(color("wall"), Qt.BrushStyle.BDiagPattern)   # 45 deg wall hatching
        self.ramp_body = QGraphicsPolygonItem(walls)
        self.ramp_body.setBrush(hatch)
        self.ramp_body.setPen(Qt.PenStyle.NoPen)
        self.ramp_surface = QGraphicsPathItem(walls)
        self.ramp_surface.setPen(pen("wall", 2.0))
        self.cowl_body = QGraphicsPolygonItem(walls)
        self.cowl_body.setBrush(hatch)
        self.cowl_body.setPen(pen("wall", 1.5))

        self.streamtube = QGraphicsPathItem(self.layers["streamtube"])
        self.streamtube.setPen(pen("text_muted", 1.0, Qt.PenStyle.DotLine))

        ann = self.layers["annotations"]
        self.arrow = QGraphicsPathItem(ann)
        self.arrow.setPen(pen("text", 1.5))
        self.arrow.setBrush(QBrush(color("text")))
        self.arrow_label = Label("", ann, size=tokens.SIZE_BASE, color_name="text")

        sel = self.layers["selection"]
        self.selection_item = QGraphicsPathItem(sel)
        self.selection_item.setPen(pen("accent", 2.5))
        self.selection_item.hide()

    # --- update ------------------------------------------------------------------------
    def set_picture(self, pic, units=None):
        """Update every item in place from a Picture (rebuilding lists only on count change)."""
        self.picture = pic
        if units is not None:
            self.units = units
        sk = pic.skeleton
        self.ramp_body.setPolygon(_poly(pic.ramp_body))
        self.ramp_surface.setPath(_path(pic.ramp_surface))
        self.cowl_body.setPolygon(_poly(pic.cowl_body))
        self.streamtube.setPath(_path(pic.streamtube))
        self._set_regions(pic)
        self._set_shocks(pic)
        self._set_arrow(pic)
        self._set_dimensions(pic)
        self.mach_max = mach_scale_max(sk.regions[0].M)

    def _set_regions(self, pic):
        layer = self.layers["regions"]
        while len(self.region_items) < len(pic.regions):
            item = QGraphicsPolygonItem(layer)
            item.setPen(Qt.PenStyle.NoPen)
            self.region_items.append(item)
        while len(self.region_items) > len(pic.regions):
            self.removeItem(self.region_items.pop())
        m_max = mach_scale_max(pic.skeleton.regions[0].M)
        for item, region in zip(self.region_items, pic.regions):
            item.setPolygon(_poly(region.polygon))
            item.setBrush(QBrush(mach_color(region.state.M, m_max)))

    def _set_shocks(self, pic):
        layer = self.layers["shocks"]
        while len(self.shock_items) < len(pic.shocks):
            self.shock_items.append(QGraphicsPathItem(layer))
        while len(self.shock_items) > len(pic.shocks):
            self.removeItem(self.shock_items.pop())
        for item, shock in zip(self.shock_items, pic.shocks):
            style = Qt.PenStyle.DashLine if shock.kind == "normal" else Qt.PenStyle.SolidLine
            item.setPen(pen("shock", 2.0, style))
            item.setPath(_path([shock.start, shock.end]))

    def _set_arrow(self, pic):
        tail, head = pic.arrow
        h = pic.skeleton.h
        size = 0.045 * h
        path = _path([tail, head])
        tip = QPolygonF([S(head), S((head[0] - 1.8 * size, head[1] + 0.7 * size)),
                         S((head[0] - 1.8 * size, head[1] - 0.7 * size))])
        path.addPolygon(tip)
        path.closeSubpath()
        self.arrow.setPath(path)
        label = "M∞ = " + f"{pic.skeleton.mach:.2f}"
        self.arrow_label.set(label, (0.5 * (tail[0] + head[0]), tail[1] + 0.09 * h))

    # --- dimensions --------------------------------------------------------------------
    def _length_text(self, label, metres):
        value = _units.to_display(metres, "length", self.units)
        return f"{label} {fmt.sig(value, 4)} {_units.unit_label('length', self.units)}"

    def _set_dimensions(self, pic):
        layer = self.layers["dimensions"]
        for item in self._dim_items:
            self.removeItem(item)
        self._dim_items = []
        h = pic.skeleton.h
        line_pen = pen("text_muted", 1.0)
        ext_pen = pen("text_muted", 0.8, alpha=0.7)
        tick = 0.03 * h

        def add(item):
            item.setParentItem(layer)
            self._dim_items.append(item)
            return item

        for d in pic.dimensions:
            if d.kind == "linear":
                a, b, d0, d1 = d.points
                ux, uy = d1[0] - d0[0], d1[1] - d0[1]
                L = math.hypot(ux, uy) or 1.0
                ux, uy = ux / L, uy / L
                ext = QPainterPath()
                for p, q in ((a, d0), (b, d1)):
                    vx, vy = q[0] - p[0], q[1] - p[1]
                    vl = math.hypot(vx, vy) or 1.0
                    ext.moveTo(S(p))
                    ext.lineTo(S((q[0] + vx / vl * tick, q[1] + vy / vl * tick)))
                add(QGraphicsPathItem(ext)).setPen(ext_pen)
                dim = _path([d0, d1])
                for p, s in ((d0, 1.0), (d1, -1.0)):       # filled arrowheads, pointing outward
                    nx, ny = -uy, ux
                    dim.addPolygon(QPolygonF([
                        S(p),
                        S((p[0] + s * ux * 2.2 * tick + nx * 0.6 * tick,
                           p[1] + s * uy * 2.2 * tick + ny * 0.6 * tick)),
                        S((p[0] + s * ux * 2.2 * tick - nx * 0.6 * tick,
                           p[1] + s * uy * 2.2 * tick - ny * 0.6 * tick)),
                    ]))
                    dim.closeSubpath()
                item = add(QGraphicsPathItem(dim))
                item.setPen(line_pen)
                item.setBrush(QBrush(color("text_muted")))
                anchor = "right" if d.label == "h_c" else "center"
                add(Label(anchor=anchor)).set(self._length_text(d.label, d.value), d.text_at)
            elif d.kind == "angle":
                c = d.points[0]
                a0, a1 = d.angles
                path = QPainterPath()
                path.moveTo(S(c))
                path.lineTo(S((c[0] + math.cos(math.radians(a0)) * d.radius * 1.35,
                               c[1] + math.sin(math.radians(a0)) * d.radius * 1.35)))
                add(QGraphicsPathItem(path)).setPen(pen("text_muted", 0.8, Qt.PenStyle.DashLine))
                arc = QPainterPath()
                rect = QRectF(c[0] - d.radius, -c[1] - d.radius, 2 * d.radius, 2 * d.radius)
                arc.arcMoveTo(rect, a0)
                arc.arcTo(rect, a0, a1 - a0)
                add(QGraphicsPathItem(arc)).setPen(line_pen)
                add(Label(anchor="left")).set(f"{d.label} {d.value:.2f}°", d.text_at)
            else:  # callout
                p = d.points[0]
                lead = _path([p, d.text_at])
                lead.addEllipse(S(p), 0.012 * h, 0.012 * h)
                add(QGraphicsPathItem(lead)).setPen(line_pen)
                x, y = (_units.to_display(v, "length", self.units) for v in d.extra)
                unit = _units.unit_label("length", self.units)
                add(Label(anchor="right")).set(f"{d.label} ({fmt.sig(x, 4)}, {fmt.sig(y, 4)}) {unit}",
                                               d.text_at)

    # --- visibility / state ------------------------------------------------------------
    def set_layer_visible(self, name, visible):
        if name == "shocks":
            self.layers["shocks"].setVisible(visible)
        elif name in self.layers:
            self.layers[name].setVisible(visible)

    def layer_visible(self, name):
        return self.layers[name].isVisible()

    def set_dimmed(self, dimmed):
        for name in LAYERS:
            if name != "selection":
                self.layers[name].setOpacity(0.4 if dimmed else 1.0)

    def show_selection(self, kind, index):
        pic = self.picture
        if pic is None or kind is None:
            self.selection_item.hide()
            return
        if kind == "region" and index < len(pic.regions):
            path = _path(pic.regions[index].polygon)
            path.closeSubpath()
        elif kind == "shock" and index < len(pic.shocks):
            path = _path([pic.shocks[index].start, pic.shocks[index].end])
        else:
            self.selection_item.hide()
            return
        self.selection_item.setPath(path)
        self.selection_item.show()

    def geometry_rect(self):
        """Scene rect of the drawing (walls, domain and label anchors), without text extents."""
        if self.picture is None:
            return QRectF(-50, -50, 100, 100)
        x0, y0, x1, y1 = self.picture.bounds()
        pts = [d.text_at for d in self.picture.dimensions if d.text_at] if \
            self.layers["dimensions"].isVisible() else []
        for p in pts:
            x0, y0, x1, y1 = min(x0, p[0]), min(y0, p[1]), max(x1, p[0]), max(y1, p[1])
        return QRectF(QPointF(x0, -y1), QPointF(x1, -y0))
