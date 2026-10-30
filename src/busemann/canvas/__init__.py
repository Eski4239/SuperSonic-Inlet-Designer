"""Inlet canvas (spec 4.3): pure drawing model (picture), Qt scene items, interactive view.

`picture` has no Qt dependency; InletCanvas is imported lazily so the drawing model can be
used (and tested) without PySide6.
"""
__all__ = ["InletCanvas"]


def __getattr__(name):
    if name == "InletCanvas":
        from .view import InletCanvas
        return InletCanvas
    raise AttributeError(name)
