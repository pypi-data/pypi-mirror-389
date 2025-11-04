"""AnyWidget bindings for the file drop widget."""

from __future__ import annotations

from pathlib import Path

import anywidget
import traitlets

__all__ = ["FileDropWidget"]

_STATIC_DIR = Path(__file__).parent / "static"


class FileDropWidget(anywidget.AnyWidget):
    """File drop zone widget for notebooks."""

    # AnyWidget expects module references pointing at the built assets on disk.
    _esm = _STATIC_DIR / "index.js"
    _css = _STATIC_DIR / "style.css"

    files = traitlets.Unicode("[]").tag(sync=True)
    file_count = traitlets.Int(0).tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)
    max_files = traitlets.Int(5, min=1).tag(sync=True)
    selected_config = traitlets.Unicode("").tag(sync=True)
