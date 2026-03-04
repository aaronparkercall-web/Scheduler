from __future__ import annotations

import copy
from typing import Any

import tkinter as tk
from tkinter import simpledialog
import ttkbootstrap as ttk

from state import AppState
from parsing import parse_mmdd_to_datetime, compute_displays_from_inputs, fraction_denominator_if_present
from storage import save_data
from ui_tables import refresh_tables as refresh_tables_full


class ActionHandlers:
    def __init__(
        self,
        app: ttk.Window,
        notebook: ttk.Notebook,
        tab_all: ttk.Frame,
        tab_flagged: ttk.Frame,
        tab_settings: ttk.Frame,
        table_all: ttk.Treeview,
        table_flagged: ttk.Treeview,
        style: ttk.Style,
        state: AppState,
        # inputs:
        date_var: ttk.StringVar,
        time_var: ttk.StringVar,
        class_var: ttk.StringVar,
        assignment_var: ttk.StringVar,
        score_var: ttk.StringVar,
        grade_var: ttk.StringVar,
        max_points_var: ttk.StringVar,
    ) -> None:
        self.app = app
        self.notebook = notebook
        self.tab_all = tab_all
        self.tab_flagged = tab_flagged
        self.tab_settings = tab_settings
        self.table_all = table_all
        self.table_flagged = table_flagged
        self.style = style
        self.state = state

        self.date_var = date_var
        self.time_var = time_var
        self.class_var = class_var
        self.assignment_var = assignment_var
        self.score_var = score_var
        self.grade_var = grade_var
        self.max_points_var = max_points_var

        self.menu = tk.Menu(app, tearoff=0)
        self.menu.add_command(label="Flag", command=lambda: self.set_flag_for_selection(True, self.active_treeview()))
        self.menu.add_command(label="Unflag", command=lambda: self.set_flag_for_selection(False, self.active_treeview()))
        self.menu.add_separator()
        self.menu.add_command(label="Add/Edit Note…", command=lambda: self.edit_note_for_selection(self.active_treeview()))
        self.menu.add_command(label="Clear Note", command=lambda: self.clear_note_for_selection(self.active_treeview()))

        self._wire_autofill_denominators()

    # -------------------------
    # Undo
    # -------------------------
    def push_undo_state(self) -> None:
        self.state.undo_stack.append(copy.deepcopy(self.state.data))
        if len(self.state.undo_stack) > self.state.undo_max:
            self.state.undo_stack.pop(0)

    def undo_last_action(self) -> None:
        if not self.state.undo_stack:
            return
        self.state.data = self.state.undo_stack.pop()
        self.state.selected_index = None
        self.state.selected_indices_multi = []
        self.clear_inputs()
        self.refresh_tables(jump=True)
        save_data(self.state.data)

    # -------------------------
    # Helpers
    # -------------------------
    def clear_inputs(self) -> None:
        self.date_var.set("")
        self.time_var.set("")
        self.class_var.set("")
        self.assignment_var.set("")
        self.score_var.set("")
        self.grade_var.set("")
        self.max_points_var.set("")

    def refresh_tables(self, jump: bool = False) -> None:
        refresh_tables_full(
            state=self.state,
            notebook=self.notebook,
            table_all=self.table_all,
            table_flagged=self.table_flagged,
            settings=self.state.settings,
            on_right_click_any=self.on_right_click_any,
            on_select=self.capture_selection,
            jump=jump,
        )

    def get_all_treeviews(self) -> list[ttk.Treeview]:
        trees = [self.table_all, self.table_flagged]
        for _, obj in self.state.class_tabs.items():
            trees.append(obj["tree"])
        return trees

    def active_treeview(self) -> ttk.Treeview:
        current_tab = self.notebook.select()
        # tabs are: All, class tabs..., Flagged, Settings
        if current_tab == str(self.tab_all):
            return self.table_all
        if current_tab == str(self.tab_flagged):
            return self.table_flagged
        if current_tab == str(self.tab_settings):
            return self.table_all
        for _, obj in self.state.class_tabs.items():
            if current_tab == str(obj["tab"]):
                return obj["tree"]
        return self.table_all

    def capture_selection(self, tree: ttk.Treeview) -> None:
        sel = tree.selection()
        if not sel:
            self.state.selected_index = None
            self.state.selected_indices_multi = []
            return

        indices = [int(iid) for iid in sel]
        if len(indices) == 1:
            self.state.selected_index = indices[0]
            self.state.selected_indices_multi = []
        else:
            self.state.selected_index = None
            self.state.selected_indices_multi = indices
            self.clear_inputs()

    def ensure_row_selected(self, tree: ttk.Treeview, iid: str) -> None:
        if iid not in tree.selection():
            tree.selection_set(iid)
            tree.focus(iid)

    # -------------------------
    # Auto-fill MaxPoints from fractions (Score or Grade)
    # -------------------------
    def _wire_autofill_denominators(self) -> None:
        def on_change(*_args: Any) -> None:
            denom = fraction_denominator_if_present(self.score_var.get())
            if denom is None:
                denom = fraction_denominator_if_present(self.grade_var.get())
            if denom is None:
                return
            if self.max_points_var.get().strip() != denom:
                self.max_points_var.set(denom)

        self.score_var.trace_add("write", on_change)
        self.grade_var.trace_add("write", on_change)

    # -------------------------
    # Core actions
    # -------------------------
    def add_assignment(self) -> None:
        try:
            dt = parse_mmdd_to_datetime(self.date_var.get(), self.time_var.get())
            grade_display, score_display, max_points_display = compute_displays_from_inputs(
                grade_text=self.grade_var.get(),
                score_text=self.score_var.get(),
                max_points_text=self.max_points_var.get(),
            )

            self.push_undo_state()

            self.state.data.append({
                "datetime": dt,
                "Date": dt.strftime("%m/%d"),
                "Time": dt.strftime("%I:%M %p"),
                "Class": self.class_var.get(),
                "Assignment": self.assignment_var.get(),
                "Score": score_display,
                "MaxPoints": max_points_display,
                "Grade": grade_display,
                "Complete": False,
                "Flagged": False,
                "Note": "",
            })

            self.refresh_tables()
            save_data(self.state.data)

        except ValueError as e:
            print(f"Invalid input: {e}")

    def load_selected(self) -> None:
        tree = self.active_treeview()
        self.capture_selection(tree)

        if self.state.selected_index is None:
            return

        item = self.state.data[self.state.selected_index]
        dt = item["datetime"]

        self.clear_inputs()
        self.date_var.set(dt.strftime("%m/%d"))
        self.time_var.set(dt.strftime("%H:%M"))
        self.class_var.set(item.get("Class", ""))
        self.assignment_var.set(item.get("Assignment", ""))
        self.score_var.set(item.get("Score", ""))
        self.max_points_var.set(item.get("MaxPoints", ""))
        self.grade_var.set(item.get("Grade", ""))

    def update_assignment(self) -> None:
        tree = self.active_treeview()
        self.capture_selection(tree)

        # MULTI update: apply only non-blank inputs (blank means "leave as-is")
        if self.state.selected_indices_multi:
            date_text = self.date_var.get().strip()
            time_text = self.time_var.get().strip()
            class_text = self.class_var.get().strip()
            assignment_text = self.assignment_var.get().strip()
            score_text = self.score_var.get().strip()
            grade_text = self.grade_var.get().strip()
            maxp_text = self.max_points_var.get().strip()

            if not any([date_text, time_text, class_text, assignment_text, score_text, grade_text, maxp_text]):
                return

            self.push_undo_state()

            for idx in self.state.selected_indices_multi:
                item = self.state.data[idx]

                if date_text or time_text:
                    existing_dt = item["datetime"]
                    new_date_mmdd = date_text if date_text else existing_dt.strftime("%m/%d")
                    new_time_hhmm = time_text if time_text else existing_dt.strftime("%H:%M")
                    new_dt = parse_mmdd_to_datetime(new_date_mmdd, new_time_hhmm)
                    item["datetime"] = new_dt
                    item["Date"] = new_dt.strftime("%m/%d")
                    item["Time"] = new_dt.strftime("%I:%M %p")

                if class_text:
                    item["Class"] = class_text
                if assignment_text:
                    item["Assignment"] = assignment_text

                if score_text or grade_text or maxp_text:
                    g_in = grade_text if grade_text else item.get("Grade", "")
                    s_in = score_text if score_text else item.get("Score", "")
                    mp_in = maxp_text if maxp_text else item.get("MaxPoints", "")

                    g_out, s_out, mp_out = compute_displays_from_inputs(g_in, s_in, mp_in)

                    item["Grade"] = g_out
                    item["Score"] = s_out
                    item["MaxPoints"] = mp_out

            self.state.selected_indices_multi = []
            self.clear_inputs()
            self.refresh_tables()
            save_data(self.state.data)
            return

        # SINGLE update
        if self.state.selected_index is None:
            return

        try:
            dt = parse_mmdd_to_datetime(self.date_var.get(), self.time_var.get())
            grade_display, score_display, max_points_display = compute_displays_from_inputs(
                grade_text=self.grade_var.get(),
                score_text=self.score_var.get(),
                max_points_text=self.max_points_var.get(),
            )

            self.push_undo_state()

            item = self.state.data[self.state.selected_index]
            item["datetime"] = dt
            item["Date"] = dt.strftime("%m/%d")
            item["Time"] = dt.strftime("%I:%M %p")
            item["Class"] = self.class_var.get()
            item["Assignment"] = self.assignment_var.get()
            item["Score"] = score_display
            item["MaxPoints"] = max_points_display
            item["Grade"] = grade_display

            self.state.selected_index = None
            self.refresh_tables()
            save_data(self.state.data)

        except ValueError as e:
            print(f"Invalid input: {e}")

    def toggle_complete(self) -> None:
        tree = self.active_treeview()
        sel = tree.selection()
        if not sel:
            return

        self.push_undo_state()
        for iid in sel:
            idx = int(iid)
            self.state.data[idx]["Complete"] = not self.state.data[idx].get("Complete", False)

        self.refresh_tables()
        save_data(self.state.data)

    def delete_selected(self) -> None:
        tree = self.active_treeview()
        sel = tree.selection()
        if not sel:
            return

        self.push_undo_state()
        indices = sorted([int(iid) for iid in sel], reverse=True)
        for idx in indices:
            self.state.data.pop(idx)

        self.state.selected_index = None
        self.state.selected_indices_multi = []
        self.clear_inputs()
        self.refresh_tables(jump=True)
        save_data(self.state.data)

    # -------------------------
    # Right-click menu actions
    # -------------------------
    def set_flag_for_selection(self, flag_value: bool, tree: ttk.Treeview) -> None:
        sel = tree.selection()
        if not sel:
            return
        self.push_undo_state()
        for iid in sel:
            idx = int(iid)
            self.state.data[idx]["Flagged"] = flag_value
        self.refresh_tables()
        save_data(self.state.data)

    def edit_note_for_selection(self, tree: ttk.Treeview) -> None:
        sel = tree.selection()
        if not sel:
            return

        idx0 = int(sel[0])
        current_note = self.state.data[idx0].get("Note", "")

        note = simpledialog.askstring("Note", "Enter note for selected assignment(s):", initialvalue=current_note)
        if note is None:
            return

        self.push_undo_state()
        for iid in sel:
            idx = int(iid)
            self.state.data[idx]["Note"] = note
            self.state.data[idx]["Flagged"] = True

        self.refresh_tables()
        save_data(self.state.data)

    def clear_note_for_selection(self, tree: ttk.Treeview) -> None:
        sel = tree.selection()
        if not sel:
            return
        self.push_undo_state()
        for iid in sel:
            idx = int(iid)
            self.state.data[idx]["Note"] = ""
        self.refresh_tables()
        save_data(self.state.data)

    def on_right_click_any(self, tree: ttk.Treeview, event: Any) -> None:
        iid = tree.identify_row(event.y)
        if not iid:
            return
        self.ensure_row_selected(tree, iid)
        self.menu.tk_popup(event.x_root, event.y_root)

    def on_double_click_flagged(self, event: Any) -> None:
        iid = self.table_flagged.identify_row(event.y)
        if not iid:
            return
        self.notebook.select(self.tab_all)
        self.table_all.selection_set(iid)
        self.table_all.focus(iid)
        self.table_all.see(iid)
