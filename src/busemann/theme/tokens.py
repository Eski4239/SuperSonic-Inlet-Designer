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
SIZE_LABEL = 11      # px, uppercase labels
LABEL_TRACKING_EM = 0.06
SIZE_KPI = 22        # px

LEFT_PANEL_WIDTH = 300
RIGHT_PANEL_WIDTH = 320
MIN_WINDOW = (1280, 800)

DEBOUNCE_MS = 30


def space(n=1):
    """n grid units in px."""
    return n * SPACING


# --- inlet canvas ---------------------------------------------------------------------
# Sequential Mach tint, light (low M) -> darker blue (high M); low saturation so that the
# drawing stays readable on top. Interpolated linearly between the stops.
MACH_RAMP = ("#F7F9FC", "#EBF1F8", "#DDE7F3", "#CEDCEE", "#BFD1E8", "#AFC5E2", "#9FB9DB")
REGION_ALPHA = 0.9
CANVAS_ANIM_MS = 150
HOVER_PICK_PX = 6        # shock pick distance, screen px
CANVAS_FIT_MARGIN_PX = 56
SHADOW_ALPHA = 28        # hover card shadow (0-255), subtle
