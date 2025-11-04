"""Compatibility package that re-exports the public API from ``whisperx``.

This allows downstream code to import ``whisperx_legen_fork`` while the
implementation continues to live under the original ``whisperx`` package.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

_SOURCE_PACKAGE = "whisperx"
_source_module = importlib.import_module(_SOURCE_PACKAGE)

__doc__ = _source_module.__doc__
__path__ = _source_module.__path__

_exported_names = {
    name: getattr(_source_module, name)
    for name in dir(_source_module)
    if not name.startswith("_")
}

globals().update(_exported_names)
__all__ = sorted(_exported_names)

def __getattr__(name: str) -> Any:
    """Lazy-load attributes and submodules from the original package."""
    if name in _exported_names:
        return _exported_names[name]

    try:
        attr = getattr(_source_module, name)
    except AttributeError:
        try:
            submodule = importlib.import_module(f"{_SOURCE_PACKAGE}.{name}")
        except ModuleNotFoundError as exc:  # pragma: no cover - mirrors stdlib behaviour
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
        sys.modules.setdefault(f"{_SOURCE_PACKAGE}.{name}", submodule)
        sys.modules[f"{__name__}.{name}"] = submodule
        _exported_names[name] = submodule
        globals()[name] = submodule
        return submodule

    _exported_names[name] = attr
    globals()[name] = attr
    return attr

def __dir__() -> list[str]:
    """Expose combined attributes for interactive environments."""
    names = set(__all__)
    names.update(globals())
    names.update(dir(_source_module))
    return sorted(names)
