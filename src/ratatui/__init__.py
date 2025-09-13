"""
Compatibility shim package for `import ratatui`.

This re-exports the public API from the original `ratatui_py` package so that
users can `import ratatui` when installing the distribution named `ratatui`.
"""

from ratatui_py import *  # noqa: F401,F403
# Propagate the public API list for tools relying on __all__
try:
    from ratatui_py import __all__ as __all__  # type: ignore  # noqa: F401,F403
except Exception:  # pragma: no cover
    pass

# Optionally expose a version if available via importlib.metadata.
try:  # pragma: no cover
    from importlib.metadata import version as _pkg_version  # type: ignore

    __version__ = _pkg_version("ratatui")
except Exception:  # pragma: no cover
    __version__ = "0"
