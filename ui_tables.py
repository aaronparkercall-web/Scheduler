from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import ttkbootstrap as ttk

from state import AppState, COLUMNS_ALL, COLUMNS_FLAGGED


def apply_treeview_selection_style(style: ttk.Style, settings: dict[str, Any]) -> None:
    sel_bg = settings["selection"]["background"]
    sel_fg = settings["selection"]["foreground"]
    style.map(
        "Treeview",
        background=[("selected", sel_bg)],
        foreground=[("selected", sel_fg)],
    )


def configure_tags(tv: ttk.Treeview, settings: dict[str, Any]) -> None:
    tv.tag_configure("even", background=settings["colors"]["even"])
    tv.tag_configure("odd", background=settings["colors"]["odd"])

    tv.tag_configure("flagged", background=settings["colors"]["flagged"])
    tv.tag_configure("complete", background=settings["colors"]["complete"])
    tv.tag_configure("overdue", background=settings["colors"]["overdue"])
    tv.tag_configure("soon", background=settings["colors"]["soon"])


def get_row_tag(item: dict[str, Any], stripe_tag: str) -> str:
    if item.get("Flagged"):
        return "flagged"
    if item.get("Complete"):
        return "complete"

    today = datetime.now().date()
    due = item["datetime"].date()
    delta_days = (due - today).days

    if due < today:
        return "overdue"
    if 0 <= delta_days <= 5:
        return "soon"
    return stripe_tag


def normalized_class_name(s: str) -> str:
    return (s or "").strip()


def get_all_classes(state: AppState) -> list[str]:
    classes = sorted({
        normalized_class_name(item.get("Class", ""))
        for item in state.data
        if normalized_class_name(item.get("Class", ""))
    })
    return classes


def build_main_tables(
    tab_all: ttk.Frame,
    tab_flagged: ttk.Frame,
    settings: dict[str, Any],
) -> tuple[ttk.Treeview, ttk.Treeview]:
    table_all = ttk.Treeview(tab_all, columns=COLUMNS_ALL, show="headings", selectmode="extended")
    for col in COLUMNS_ALL:
        table_all.heading(col, text=col, anchor="w")
        w = 150
        if col == "Assignment":
            w = 240
        if col in ("Date", "Time"):
            w = 110
        if col in ("Flag", "Complete"):
            w = 90
        if col in ("Score", "Max Points", "Grade"):
            w = 120
        anchor = "center" if col in ("Flag", "Complete") else "w"
        table_all.column(col, anchor=anchor, width=w)
    configure_tags(table_all, settings)
    table_all.pack(fill="both", expand=True)

    table_flagged = ttk.Treeview(tab_flagged, columns=COLUMNS_FLAGGED, show="headings", selectmode="extended")
    for col in COLUMNS_FLAGGED:
        table_flagged.heading(col, text=col, anchor="w")
        if col == "Note":
            table_flagged.column(col, anchor="w", width=560)
        else:
            table_flagged.column(col, anchor="w", width=170)
    configure_tags(table_flagged, settings)
    table_flagged.pack(fill="both", expand=True)

    return table_all, table_flagged


def rebuild_class_tabs_if_needed(
    state: AppState,
    notebook: ttk.Notebook,
    settings: dict[str, Any],
    on_right_click_any: Callable[[ttk.Treeview, Any], None],
    on_select: Callable[[ttk.Treeview], None],
) -> None:
    current_classes = get_all_classes(state)
    if current_classes == state.class_order:
        return

    for cls in list(state.class_tabs.keys()):
        notebook.forget(state.class_tabs[cls]["tab"])
    state.class_tabs.clear()
    state.class_order = current_classes

    insert_at = 1
    for cls in state.class_order:
        tab = ttk.Frame(notebook)
        notebook.insert(insert_at, tab, text=cls)
        insert_at += 1

        tv = ttk.Treeview(tab, columns=COLUMNS_ALL, show="headings", selectmode="extended")
        for col in COLUMNS_ALL:
            tv.heading(col, text=col, anchor="w")
            w = 150
            if col == "Assignment":
                w = 240
            if col in ("Date", "Time"):
                w = 110
            if col in ("Flag", "Complete"):
                w = 90
            if col in ("Score", "Max Points", "Grade"):
                w = 120
            anchor = "center" if col in ("Flag", "Complete") else "w"
            tv.column(col, anchor=anchor, width=w)
        configure_tags(tv, settings)
        tv.pack(fill="both", expand=True)

        state.class_tabs[cls] = {"tab": tab, "tree": tv}

        tv.bind("<Button-3>", lambda e, tree=tv: on_right_click_any(tree, e))
        tv.bind("<Button-2>", lambda e, tree=tv: on_right_click_any(tree, e))
        tv.bind("<<TreeviewSelect>>", lambda e, tree=tv: on_select(tree))


def fill_all_table(state: AppState, table_all: ttk.Treeview) -> None:
    for row in table_all.get_children():
        table_all.delete(row)

    sorted_data = sorted(enumerate(state.data), key=lambda x: x[1]["datetime"])
    for i, (idx, item) in enumerate(sorted_data):
        stripe = "even" if i % 2 == 0 else "odd"
        tag = get_row_tag(item, stripe)
        checkmark = "✔" if item.get("Complete") else ""
        flag_icon = "🚩" if item.get("Flagged") else ""
        table_all.insert(
            "", "end", iid=str(idx),
            values=(
                item.get("Date", ""),
                item.get("Time", ""),
                item.get("Class", ""),
                item.get("Assignment", ""),
                item.get("Score", ""),
                item.get("MaxPoints", ""),
                item.get("Grade", ""),
                flag_icon,
                checkmark
            ),
            tags=(tag,)
        )


def fill_class_table(state: AppState, cls: str, tv: ttk.Treeview) -> None:
    for row in tv.get_children():
        tv.delete(row)

    filtered = [(i, item) for i, item in enumerate(state.data) if normalized_class_name(item.get("Class", "")) == cls]
    filtered.sort(key=lambda x: x[1]["datetime"])

    for j, (idx, item) in enumerate(filtered):
        stripe = "even" if j % 2 == 0 else "odd"
        tag = get_row_tag(item, stripe)
        checkmark = "✔" if item.get("Complete") else ""
        flag_icon = "🚩" if item.get("Flagged") else ""
        tv.insert(
            "", "end", iid=str(idx),
            values=(
                item.get("Date", ""),
                item.get("Time", ""),
                item.get("Class", ""),
                item.get("Assignment", ""),
                item.get("Score", ""),
                item.get("MaxPoints", ""),
                item.get("Grade", ""),
                flag_icon,
                checkmark
            ),
            tags=(tag,)
        )


def fill_flagged_table(state: AppState, table_flagged: ttk.Treeview) -> None:
    for row in table_flagged.get_children():
        table_flagged.delete(row)

    flagged = [(i, item) for i, item in enumerate(state.data) if item.get("Flagged")]
    flagged.sort(key=lambda x: x[1]["datetime"])

    for j, (idx, item) in enumerate(flagged):
        stripe = "even" if j % 2 == 0 else "odd"
        tag = get_row_tag(item, stripe)
        checkmark = "✔" if item.get("Complete") else ""
        table_flagged.insert(
            "", "end", iid=str(idx),
            values=(item.get("Date", ""), item.get("Time", ""), item.get("Class", ""), item.get("Assignment", ""),
                    item.get("Note", ""), checkmark),
            tags=(tag,)
        )


def refresh_tables(
    state: AppState,
    notebook: ttk.Notebook,
    table_all: ttk.Treeview,
    table_flagged: ttk.Treeview,
    settings: dict[str, Any],
    on_right_click_any: Callable[[ttk.Treeview, Any], None],
    on_select: Callable[[ttk.Treeview], None],
    jump: bool = False,
) -> None:
    rebuild_class_tabs_if_needed(
        state=state,
        notebook=notebook,
        settings=settings,
        on_right_click_any=on_right_click_any,
        on_select=on_select,
    )

    fill_all_table(state, table_all)

    for cls, obj in state.class_tabs.items():
        fill_class_table(state, cls, obj["tree"])

    fill_flagged_table(state, table_flagged)

    if jump:
        jump_to_today(state, table_all)


def jump_to_today(state: AppState, table_all: ttk.Treeview) -> None:
    if not state.data:
        return

    today = datetime.now().date()
    children = table_all.get_children()
    if not children:
        return

    target_iid = None
    for iid in children:
        idx = int(iid)
        if state.data[idx]["datetime"].date() >= today:
            target_iid = iid
            break

    if target_iid is None:
        target_iid = children[-1]

    table_all.selection_set(target_iid)
    table_all.focus(target_iid)
    table_all.see(target_iid)
