"""Top-level package proxying to apps/api/src."""

from __future__ import annotations

import pathlib

_api_src = pathlib.Path(__file__).resolve().parent.parent / "apps" / "api" / "src"

# Treat apps/api/src as the package contents for `src`
__path__ = [str(_api_src)]
