"""Compatibility package so `import src.*` resolves to this codebase."""

from __future__ import annotations

import pathlib

_parent = pathlib.Path(__file__).resolve().parent.parent
__path__ = [str(_parent)]
