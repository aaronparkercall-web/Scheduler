from __future__ import annotations

import json
import os
import copy
from datetime import datetime
from typing import Any

from state import JSON_FILE, SETTINGS_FILE, DEFAULT_SETTINGS, PLANNER_FILE


def save_data(data: list[dict[str, Any]], json_file: str = JSON_FILE) -> None:
    serializable_data = []
    for item in data:
        serializable_data.append({
            "datetime": item["datetime"].strftime("%Y/%m/%d %H:%M"),
            "Date": item.get("Date", ""),
            "Time": item.get("Time", ""),
            "Class": item.get("Class", ""),
            "Assignment": item.get("Assignment", ""),
            "Score": item.get("Score", ""),
            "MaxPoints": item.get("MaxPoints", ""),
            "Grade": item.get("Grade", ""),
            "Complete": bool(item.get("Complete", False)),
            "Flagged": bool(item.get("Flagged", False)),
            "Note": item.get("Note", ""),
        })
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(serializable_data, f, indent=4)


def load_data(json_file: str = JSON_FILE) -> list[dict[str, Any]]:
    if not os.path.exists(json_file):
        return []
    with open(json_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    out: list[dict[str, Any]] = []
    for item in loaded:
        dt = datetime.strptime(item["datetime"], "%Y/%m/%d %H:%M")
        out.append({
            "datetime": dt,
            "Date": item.get("Date", ""),
            "Time": item.get("Time", ""),
            "Class": item.get("Class", ""),
            "Assignment": item.get("Assignment", ""),
            "Score": item.get("Score", ""),
            "MaxPoints": item.get("MaxPoints", ""),
            "Grade": item.get("Grade", ""),
            "Complete": bool(item.get("Complete", False)),
            "Flagged": bool(item.get("Flagged", False)),
            "Note": item.get("Note", ""),
        })
    return out


def save_planner_items(planner_items: list[dict[str, Any]], planner_file: str = PLANNER_FILE) -> None:
    with open(planner_file, "w", encoding="utf-8") as f:
        json.dump(planner_items, f, indent=4)


def load_planner_items(planner_file: str = PLANNER_FILE) -> list[dict[str, Any]]:
    if not os.path.exists(planner_file):
        return []
    with open(planner_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    out: list[dict[str, Any]] = []
    for item in loaded:
        out.append({
            "Type": item.get("Type", "Assignment"),
            "TodoDate": item.get("TodoDate", ""),
            "Class": item.get("Class", ""),
            "Title": item.get("Title", ""),
        })
    return out


def load_settings(settings_file: str = SETTINGS_FILE) -> dict[str, Any]:
    if not os.path.exists(settings_file):
        return copy.deepcopy(DEFAULT_SETTINGS)
    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        merged = copy.deepcopy(DEFAULT_SETTINGS)
        merged["colors"].update(loaded.get("colors", {}))
        merged["selection"].update(loaded.get("selection", {}))
        return merged
    except Exception:
        return copy.deepcopy(DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any], settings_file: str = SETTINGS_FILE) -> None:
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
