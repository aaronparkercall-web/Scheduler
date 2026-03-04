from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import copy as _copy

JSON_FILE = "assignments.json"
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    "colors": {
        "flagged": "#4b1f5c",   # purple
        "complete": "#1f5c2a",  # green
        "overdue": "#5c1e1e",   # red
        "soon": "#6b5a16",      # yellow-ish
        "even": "#2b2b2b",
        "odd": "#242424",
    },
    "selection": {
        "background": "#3a3a3a",  # selected row background (replaces grey)
        "foreground": "#ffffff",  # selected row text
    },
}

# Score is before Max Points (per your request)
COLUMNS_ALL = ["Date", "Time", "Class", "Assignment", "Score", "Max Points", "Grade", "Flag", "Complete"]
COLUMNS_FLAGGED = ["Date", "Time", "Class", "Assignment", "Note", "Complete"]


@dataclass
class AppState:
    data: list[dict[str, Any]] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=lambda: _copy.deepcopy(DEFAULT_SETTINGS))

    undo_stack: list[list[dict[str, Any]]] = field(default_factory=list)
    undo_max: int = 50

    selected_index: int | None = None
    selected_indices_multi: list[int] = field(default_factory=list)

    class_tabs: dict[str, dict[str, Any]] = field(default_factory=dict)  # cls -> {"tab": frame, "tree": treeview}
    class_order: list[str] = field(default_factory=list)
