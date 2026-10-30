"""Design tokens (spec section 5). The only place colours, spacing and type sizes are defined."""

COLORS = {
    "bg": "#F6F7F9",          # window background
    "surface": "#FFFFFF",     # panels, canvas
    "border": "#E2E5EA",      # 1 px dividers
    "text": "#111827",        # primary text
    "text_muted": "#6B7280",  # labels, units
    "accent": "#2563EB",      # selection, sliders, active tab, links
    "shock": "#D97706",       # shock lines
    "wall": "#374151",        # ramps / cowl
    "ok": "#059669",
    "warn": "#D97706",
    "error": "#DC2626",
}

SPACING = 8          # px grid unit
RADIUS = 6           # px, maximum corner radius
BORDER = 1           # px

FONT_UI = "Inter"
FONT_MONO = "JetBrains Mono"
FONT_UI_FALLBACK = "Segoe UI"
FONT_MONO_FALLBACK = "Consolas"

SIZE_BASE = 13       # px
SIZE_LABEL = 11      # px, small caps
SIZE_KPI = 22        # px

LEFT_PANEL_WIDTH = 300
RIGHT_PANEL_WIDTH = 320
MIN_WINDOW = (1280, 800)

DEBOUNCE_MS = 30


def space(n=1):
    """n grid units in px."""
    return n * SPACING
