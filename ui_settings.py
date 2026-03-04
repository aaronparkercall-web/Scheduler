from __future__ import annotations

from typing import Any, Callable

import tkinter as tk
from tkinter import colorchooser
import ttkbootstrap as ttk

from state import DEFAULT_SETTINGS, AppState
from storage import save_settings
from ui_tables import apply_treeview_selection_style, configure_tags


def build_settings_tab(
    tab_settings: ttk.Frame,
    state: AppState,
    style: ttk.Style,
    get_all_treeviews: Callable[[], list[ttk.Treeview]],
    refresh_tables: Callable[[], None],
) -> None:
    frame = ttk.Frame(tab_settings)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    ttk.Label(frame, text="Row Highlight Colors", font=("TkDefaultFont", 14, "bold")).grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 10)
    )
    ttk.Label(frame, text="Selection (Selected Row) Colors", font=("TkDefaultFont", 14, "bold")).grid(
        row=6, column=0, columnspan=3, sticky="w", pady=(25, 10)
    )

    preview_labels: dict[str, tk.Label] = {}

    def set_preview(key: str, color: str) -> None:
        lbl = preview_labels.get(key)
        if lbl:
            lbl.configure(background=color)

    def pick_color(initial: str) -> str | None:
        c = colorchooser.askcolor(color=initial, title="Choose color")
        if not c or not c[1]:
            return None
        return c[1]

    def apply_visual_settings() -> None:
        apply_treeview_selection_style(style, state.settings)
        for tv in get_all_treeviews():
            configure_tags(tv, state.settings)
        refresh_tables()

    def choose_and_apply(section: str, key: str, preview_key: str) -> None:
        current = state.settings[section][key]
        chosen = pick_color(current)
        if not chosen:
            return
        state.settings[section][key] = chosen
        set_preview(preview_key, chosen)
        save_settings(state.settings)
        apply_visual_settings()

    def reset_to_defaults() -> None:
        import copy
        state.settings = copy.deepcopy(DEFAULT_SETTINGS)
        save_settings(state.settings)

        set_preview("flagged", state.settings["colors"]["flagged"])
        set_preview("complete", state.settings["colors"]["complete"])
        set_preview("overdue", state.settings["colors"]["overdue"])
        set_preview("soon", state.settings["colors"]["soon"])
        set_preview("sel_bg", state.settings["selection"]["background"])
        set_preview("sel_fg", state.settings["selection"]["foreground"])

        apply_visual_settings()

    def make_color_row(row: int, title: str, section: str, key: str, preview_key: str) -> None:
        ttk.Label(frame, text=title, width=18).grid(row=row, column=0, sticky="w", pady=6)

        preview = tk.Label(frame, width=12, relief="solid", bd=1)
        preview.grid(row=row, column=1, sticky="w", padx=(10, 10))
        preview_labels[preview_key] = preview
        set_preview(preview_key, state.settings[section][key])

        ttk.Button(
            frame,
            text="Choose…",
            command=lambda: choose_and_apply(section, key, preview_key),
            bootstyle="info"
        ).grid(row=row, column=2, sticky="w")

    make_color_row(1, "Flagged", "colors", "flagged", "flagged")
    make_color_row(2, "Complete", "colors", "complete", "complete")
    make_color_row(3, "Overdue", "colors", "overdue", "overdue")
    make_color_row(4, "Due Soon", "colors", "soon", "soon")

    make_color_row(7, "Selection BG", "selection", "background", "sel_bg")
    make_color_row(8, "Selection Text", "selection", "foreground", "sel_fg")

    ttk.Button(
        frame,
        text="Reset to Defaults",
        command=reset_to_defaults,
        bootstyle="warning"
    ).grid(row=10, column=0, columnspan=3, sticky="w", pady=(30, 0))
