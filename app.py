from __future__ import annotations

"""
Assignment Dashboard (ttkbootstrap + Treeview) - with Score support

Run:
    python app.py
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from state import AppState
from storage import load_data, load_settings, load_planner_items
from ui_tables import build_main_tables, build_planner_table, apply_treeview_selection_style, configure_tags, refresh_tables
from ui_actions import ActionHandlers
from ui_settings import build_settings_tab


def main() -> None:
    app = ttk.Window(themename="darkly")
    app.title("Assignment Dashboard")
    app.geometry("1320x700")
    app.minsize(1100, 500)
    app.option_add("*Font", "{Segoe UI} 10")

    style = ttk.Style()
    style.configure("Treeview", rowheight=30, borderwidth=1, relief="solid")
    style.configure("Treeview.Heading", borderwidth=1, relief="solid")
    style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
    style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
    style.configure("BoldLabel.TLabel", font=("Segoe UI", 9, "bold"))

    # State
    state = AppState()
    state.settings = load_settings()
    state.data = load_data()
    state.planner_items = load_planner_items()

    apply_treeview_selection_style(style, state.settings)

    # Header
    header_frame = ttk.Frame(app, padding=(20, 16, 20, 8))
    header_frame.pack(fill="x")
    ttk.Label(header_frame, text="Assignment Dashboard", style="Title.TLabel").pack(anchor="w")
    ttk.Label(
        header_frame,
        text="Track assignments, grades, and flags by class in one place.",
        style="Subtitle.TLabel",
    ).pack(anchor="w", pady=(3, 0))

    # Inputs
    input_card = ttk.Labelframe(app, text="Assignment Details", padding=(14, 12))
    input_card.pack(fill="x", padx=20, pady=(0, 10))

    input_frame = ttk.Frame(input_card)
    input_frame.pack(fill="x")

    date_var = ttk.StringVar()
    time_var = ttk.StringVar()
    class_var = ttk.StringVar()
    assignment_var = ttk.StringVar()
    score_var = ttk.StringVar()
    grade_var = ttk.StringVar()
    max_points_var = ttk.StringVar()
    planner_assignment_var = ttk.StringVar()
    planner_todo_date_var = ttk.StringVar()
    planner_todo_time_var = ttk.StringVar()
    planner_event_title_var = ttk.StringVar()
    planner_event_class_var = ttk.StringVar()

    ttk.Label(input_frame, text="Date (MM/DD)", style="BoldLabel.TLabel").grid(row=0, column=0, padx=5, sticky="w")
    ttk.Entry(input_frame, width=10, textvariable=date_var).grid(row=1, column=0, padx=5, pady=(3, 0), sticky="ew")

    ttk.Label(input_frame, text="Time (HH:MM 24hr)", style="BoldLabel.TLabel").grid(row=0, column=1, padx=5, sticky="w")
    ttk.Entry(input_frame, width=10, textvariable=time_var).grid(row=1, column=1, padx=5, pady=(3, 0), sticky="ew")

    ttk.Label(input_frame, text="Class", style="BoldLabel.TLabel").grid(row=0, column=2, padx=5, sticky="w")
    ttk.Entry(input_frame, width=15, textvariable=class_var).grid(row=1, column=2, padx=5, pady=(3, 0), sticky="ew")

    ttk.Label(input_frame, text="Assignment", style="BoldLabel.TLabel").grid(row=0, column=3, padx=5, sticky="w")
    ttk.Entry(input_frame, width=22, textvariable=assignment_var).grid(row=1, column=3, padx=5, pady=(3, 0), sticky="ew")

    ttk.Label(input_frame, text="Score (optional)", style="BoldLabel.TLabel").grid(row=0, column=4, padx=5, sticky="w")
    ttk.Entry(input_frame, width=14, textvariable=score_var).grid(row=1, column=4, padx=5, pady=(3, 0), sticky="ew")

    ttk.Label(input_frame, text="Grade (optional)", style="BoldLabel.TLabel").grid(row=0, column=5, padx=5, sticky="w")
    ttk.Entry(input_frame, width=14, textvariable=grade_var).grid(row=1, column=5, padx=5, pady=(3, 0), sticky="ew")

    ttk.Label(input_frame, text="Max Points (optional)", style="BoldLabel.TLabel").grid(row=0, column=6, padx=5, sticky="w")
    ttk.Entry(input_frame, width=12, textvariable=max_points_var).grid(row=1, column=6, padx=5, pady=(3, 0), sticky="ew")

    for col in range(8):
        input_frame.columnconfigure(col, weight=1)

    # Tabs
    notebook = ttk.Notebook(app)
    notebook.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    tab_all = ttk.Frame(notebook)
    tab_flagged = ttk.Frame(notebook)
    tab_planner = ttk.Frame(notebook)
    tab_settings = ttk.Frame(notebook)

    notebook.add(tab_all, text="All Assignments")
    notebook.add(tab_flagged, text="Flagged")
    notebook.add(tab_planner, text="Planner")
    notebook.add(tab_settings, text="Settings")

    # Tables
    table_all, table_flagged = build_main_tables(tab_all, tab_flagged, state.settings)

    planner_controls = ttk.Labelframe(tab_planner, text="Planner Actions", padding=(10, 10))
    planner_controls.pack(fill="x", padx=8, pady=(8, 6))

    ttk.Label(planner_controls, text="Assignment", style="BoldLabel.TLabel").grid(row=0, column=0, sticky="w", padx=4)
    planner_assignment_combo = ttk.Combobox(planner_controls, textvariable=planner_assignment_var, state="readonly", width=50)
    planner_assignment_combo.grid(row=1, column=0, padx=4, pady=(3, 0), sticky="ew")

    ttk.Label(planner_controls, text="TODO Date (MM/DD)", style="BoldLabel.TLabel").grid(row=0, column=1, sticky="w", padx=4)
    ttk.Entry(planner_controls, textvariable=planner_todo_date_var, width=14).grid(row=1, column=1, padx=4, pady=(3, 0), sticky="ew")

    ttk.Label(planner_controls, text="TODO Time (HH:MM 24hr)", style="BoldLabel.TLabel").grid(row=0, column=2, sticky="w", padx=4)
    ttk.Entry(planner_controls, textvariable=planner_todo_time_var, width=14).grid(row=1, column=2, padx=4, pady=(3, 0), sticky="ew")

    add_planner_assignment_btn = ttk.Button(planner_controls, text="Add Assignment to TODO", bootstyle="primary")
    add_planner_assignment_btn.grid(row=1, column=3, padx=4, pady=(3, 0), sticky="ew")

    ttk.Label(planner_controls, text="Event Title", style="BoldLabel.TLabel").grid(row=2, column=0, sticky="w", padx=4, pady=(10, 0))
    ttk.Entry(planner_controls, textvariable=planner_event_title_var).grid(row=3, column=0, padx=4, pady=(3, 0), sticky="ew")

    ttk.Label(planner_controls, text="Event Class (optional)", style="BoldLabel.TLabel").grid(row=2, column=1, sticky="w", padx=4, pady=(10, 0))
    ttk.Entry(planner_controls, textvariable=planner_event_class_var, width=16).grid(row=3, column=1, padx=4, pady=(3, 0), sticky="ew")

    add_planner_event_btn = ttk.Button(planner_controls, text="Add Event", bootstyle="success")
    add_planner_event_btn.grid(row=3, column=3, padx=4, pady=(3, 0), sticky="ew")

    for col in range(4):
        planner_controls.columnconfigure(col, weight=1)

    table_planner = build_planner_table(tab_planner)

    # Handlers
    handlers = ActionHandlers(
        app=app,
        notebook=notebook,
        tab_all=tab_all,
        tab_flagged=tab_flagged,
        tab_settings=tab_settings,
        tab_planner=tab_planner,
        table_all=table_all,
        table_flagged=table_flagged,
        table_planner=table_planner,
        style=style,
        state=state,
        date_var=date_var,
        time_var=time_var,
        class_var=class_var,
        assignment_var=assignment_var,
        score_var=score_var,
        grade_var=grade_var,
        max_points_var=max_points_var,
        planner_assignment_var=planner_assignment_var,
        planner_todo_date_var=planner_todo_date_var,
        planner_todo_time_var=planner_todo_time_var,
        planner_event_title_var=planner_event_title_var,
        planner_event_class_var=planner_event_class_var,
    )

    planner_assignment_combo.configure(values=handlers.planner_assignment_options())
    add_planner_assignment_btn.configure(command=handlers.add_assignment_to_planner_from_dropdown)
    add_planner_event_btn.configure(command=handlers.add_event_to_planner)

    ttk.Button(input_frame, text="Clear", command=handlers.clear_inputs, bootstyle="secondary").grid(
        row=1,
        column=7,
        padx=(10, 0),
        pady=(3, 0),
        sticky="e",
    )

    # Bind selection + context menus
    table_all.bind("<<TreeviewSelect>>", lambda e: handlers.capture_selection(table_all))
    table_all.bind("<Button-3>", lambda e: handlers.on_right_click_any(table_all, e))
    table_all.bind("<Button-2>", lambda e: handlers.on_right_click_any(table_all, e))

    table_flagged.bind("<<TreeviewSelect>>", lambda e: handlers.capture_selection(table_flagged))
    table_flagged.bind("<Button-3>", lambda e: handlers.on_right_click_any(table_flagged, e))
    table_flagged.bind("<Button-2>", lambda e: handlers.on_right_click_any(table_flagged, e))
    table_flagged.bind("<Double-1>", handlers.on_double_click_flagged)

    table_planner.bind("<<TreeviewSelect>>", lambda e: handlers.capture_selection(table_planner))

    # Ctrl+Z undo
    app.bind_all("<Control-z>", lambda e: handlers.undo_last_action())
    app.bind_all("<Control-Z>", lambda e: handlers.undo_last_action())
    app.bind_all("<Delete>", lambda e: handlers.delete_selected())

    # Buttons
    button_frame = ttk.Labelframe(app, text="Actions", padding=(12, 10))
    button_frame.pack(fill="x", padx=20, pady=(0, 10))

    ttk.Button(button_frame, text="Add Assignment", command=handlers.add_assignment, bootstyle="success").pack(side="left", padx=4)
    ttk.Button(button_frame, text="Edit Selected", command=handlers.load_selected, bootstyle="info").pack(side="left", padx=4)
    ttk.Button(button_frame, text="Update Assignment", command=handlers.update_assignment, bootstyle="warning").pack(side="left", padx=4)
    ttk.Button(button_frame, text="Delete Selected", command=handlers.delete_selected, bootstyle="danger").pack(side="left", padx=4)
    ttk.Button(button_frame, text="Toggle Complete", command=handlers.toggle_complete, bootstyle="primary").pack(side="left", padx=4)
    ttk.Button(
        button_frame,
        text="Download All Assignments",
        command=handlers.download_all_assignments_spreadsheet,
        bootstyle="light",
    ).pack(side="left", padx=4)
    ttk.Button(button_frame, text="Undo (Ctrl+Z)", command=handlers.undo_last_action, bootstyle="secondary").pack(side="left", padx=4)

    # Settings tab
    build_settings_tab(
        tab_settings=tab_settings,
        state=state,
        style=style,
        get_all_treeviews=handlers.get_all_treeviews,
        refresh_tables=lambda: handlers.refresh_tables(),
    )

    configure_tags(table_all, state.settings)
    configure_tags(table_flagged, state.settings)
    configure_tags(table_planner, state.settings)

    # Initial load/refresh incl class tabs
    handlers.refresh_tables(jump=True)
    planner_assignment_combo.configure(values=handlers.planner_assignment_options())

    notebook.bind("<<NotebookTabChanged>>", lambda e: planner_assignment_combo.configure(values=handlers.planner_assignment_options()))

    app.mainloop()


if __name__ == "__main__":
    main()
