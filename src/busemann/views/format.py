"""Number formatting for read-outs (mono font, tabular)."""
import math

_SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def sig(value, digits=4):
    """Significant-figure formatting; large/small magnitudes as m × 10ⁿ."""
    if value is None or not math.isfinite(value):
        return "—"
    if value == 0:
        return "0"
    exponent = math.floor(math.log10(abs(value)))
    if -3 <= exponent < 6:
        decimals = max(0, digits - 1 - exponent)
        return f"{value:.{decimals}f}"
    mantissa = value / 10**exponent
    return f"{mantissa:.{digits - 1}f} × 10{str(exponent).translate(_SUPERSCRIPT)}"


def angles(values, decimals=2):
    return ", ".join(f"{v:.{decimals}f}" for v in values) if values else "—"


_NBSP = " "


def nbsp(text):
    """Keep "M = 2.406", "28.75 kPa", "θ = 14.98°" etc. on one line (non-breaking spaces)."""
    if not text:
        return text
    import re

    text = re.sub(r"(\b[A-Za-z_∞0]+) = (-?\d)", lambda m: f"{m.group(1)}{_NBSP}={_NBSP}{m.group(2)}", text)
    return re.sub(r"(\d) (deg|K|kPa|Pa|m|mm|in|%)\b", lambda m: f"{m.group(1)}{_NBSP}{m.group(2)}", text)
