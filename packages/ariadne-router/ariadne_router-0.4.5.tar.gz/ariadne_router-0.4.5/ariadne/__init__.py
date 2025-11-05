"""Shim package to expose src/ariadne without installation."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "ariadne"
_SPEC = importlib.util.spec_from_file_location(
    __name__, _SRC_PACKAGE / "__init__.py", submodule_search_locations=[str(_SRC_PACKAGE)]
)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - defensive programming
    raise ImportError("Unable to load Ariadne package from src directory")

_MODULE = importlib.util.module_from_spec(_SPEC)
_MODULE.__path__ = [str(_SRC_PACKAGE)]
sys.modules[__name__] = _MODULE
_SPEC.loader.exec_module(_MODULE)

# Re-export public attributes for introspection tools
globals().update(_MODULE.__dict__)
