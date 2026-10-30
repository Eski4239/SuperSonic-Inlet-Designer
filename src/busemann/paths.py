"""Filesystem paths of bundled resources, valid both from source and in a PyInstaller bundle.

Most resources are read as bytes through importlib.resources. Qt stylesheets need a real file
path for url(), so this helper returns a pathlib.Path:
- frozen (PyInstaller): <sys._MEIPASS>/busemann/resources/...
- otherwise: the installed/editable package directory busemann/resources/...
"""
import sys
from importlib import resources
from pathlib import Path


def resource_root():
    bundle = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and bundle:
        return Path(bundle) / "busemann" / "resources"
    return Path(str(resources.files("busemann"))) / "resources"


def resource_path(*parts):
    """Path to busemann/resources/<parts...>. Raises FileNotFoundError if it does not exist."""
    path = resource_root().joinpath(*parts)
    if not path.exists():
        raise FileNotFoundError(f"bundled resource missing: {path}")
    return path
