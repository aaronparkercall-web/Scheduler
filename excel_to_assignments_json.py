"""
excel_to_assignments_json.py

Reads an Excel file (your semester sheet) and writes assignments.json
in the exact format your dashboard app expects, PLUS a "Score" field.

Run:
    python excel_to_assignments_json.py "Winter 2026 Semester.xlsx"
"""

import sys
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

DEFAULT_EXCEL = "Winter 2026 Semester.xlsx"
OUTPUT_JSON = "assignments.json"

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())

def find_column(df: pd.DataFrame, keywords: list[str]) -> str | None:
    cols = list(df.columns)
    norm_cols = {c: norm(c) for c in cols}
    for kw in keywords:
        kw = kw.lower()
        for c, nc in norm_cols.items():
            if kw in nc:
                return c
    return None

FRACTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*$")
PERCENT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*%\s*$")
NUMBER_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*$")

def format_percent(pct: float) -> str:
    if abs(pct - round(pct)) < 1e-9:
        return f"{int(round(pct))}%"
    s = f"{pct:.1f}".rstrip("0").rstrip(".")
    return f"{s}%"

def normalize_number(x: float) -> str:
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s

def parse_complete(val) -> bool:
    if pd.isna(val):
        return False
    s = str(val).strip().lower()
    return s in {"true", "t", "yes", "y", "1", "done", "complete", "completed"}

def parse_date_time(due_date_val, time_val=None) -> datetime | None:
    if pd.isna(due_date_val):
        return None
    try:
        dt = pd.to_datetime(due_date_val)
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
    except Exception:
        return None

    if time_val is not None and not pd.isna(time_val):
        try:
            t = pd.to_datetime(str(time_val)).time()
            dt = dt.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
            return dt
        except Exception:
            pass

    if dt.hour == 0 and dt.minute == 0:
        dt = dt.replace(hour=23, minute=59, second=0, microsecond=0)
    return dt

def parse_grade_score_maxpoints(grade_val, maxpoints_val=None) -> tuple[str, str, str]:
    score_display = ""
    grade_display = ""
    max_points_display = "" if pd.isna(maxpoints_val) else str(maxpoints_val).strip()

    if pd.isna(grade_val) or str(grade_val).strip() == "":
        return ("", "" if max_points_display in {"nan", "None"} else max_points_display, "")

    g = str(grade_val).strip()

    m = FRACTION_RE.match(g)
    if m:
        earned = float(m.group(1))
        maxp = float(m.group(2))
        score_display = f"{normalize_number(earned)}/{normalize_number(maxp)}"
        max_points_display = normalize_number(maxp)
        if maxp > 0:
            grade_display = format_percent((earned / maxp) * 100.0)
        return (score_display, max_points_display, grade_display)

    m = PERCENT_RE.match(g)
    if m:
        pct = float(m.group(1))
        grade_display = format_percent(pct)
        if max_points_display in {"nan", "None"}:
            max_points_display = ""
        return ("", max_points_display, grade_display)

    m = NUMBER_RE.match(g)
    if m:
        num = float(m.group(1))
        if max_points_display not in {"", "nan", "None"}:
            try:
                maxp = float(max_points_display)
                if maxp > 0:
                    score_display = f"{normalize_number(num)}/{normalize_number(maxp)}"
                    grade_display = format_percent((num / maxp) * 100.0)
                    max_points_display = normalize_number(maxp)
                    return (score_display, max_points_display, grade_display)
            except Exception:
                pass
        grade_display = format_percent(num)
        if max_points_display in {"nan", "None"}:
            max_points_display = ""
        return ("", max_points_display, grade_display)

    if max_points_display in {"nan", "None"}:
        max_points_display = ""
    return ("", max_points_display, "")

def main():
    excel_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(DEFAULT_EXCEL)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    df = pd.read_excel(excel_path)

    col_due = find_column(df, ["due date", "due", "date"])
    col_time = find_column(df, ["time"])
    col_class = find_column(df, ["class"])
    col_assignment = find_column(df, ["assignment", "task", "name"])
    col_grade = find_column(df, ["grade", "score", "points"])
    col_max = find_column(df, ["max points", "max", "possible", "out of"])
    col_done = find_column(df, ["done", "complete", "completed"])

    if col_due is None:
        raise ValueError("Could not find a due-date column. Rename it to include 'Due' or 'Date'.")

    out = []

    for _, row in df.iterrows():
        dt = parse_date_time(row[col_due], row[col_time] if col_time else None)
        if dt is None:
            continue

        score_display, max_points_display, grade_display = parse_grade_score_maxpoints(
            row[col_grade] if col_grade else "",
            row[col_max] if col_max else None
        )

        out.append({
            "datetime": dt.strftime("%Y/%m/%d %H:%M"),
            "Date": dt.strftime("%m/%d"),
            "Time": dt.strftime("%I:%M %p"),
            "Class": "" if col_class is None or pd.isna(row[col_class]) else str(row[col_class]).strip(),
            "Assignment": "" if col_assignment is None or pd.isna(row[col_assignment]) else str(row[col_assignment]).strip(),
            "Score": "" if score_display in {"nan", "None"} else score_display,
            "MaxPoints": "" if max_points_display in {"nan", "None"} else max_points_display,
            "Grade": grade_display,
            "Complete": parse_complete(row[col_done]) if col_done else False,
            "Flagged": False,
            "Note": ""
        })

    out.sort(key=lambda x: datetime.strptime(x["datetime"], "%Y/%m/%d %H:%M"))

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=4)

    print(f"Wrote {len(out)} rows to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
