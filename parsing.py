from __future__ import annotations

import re
from datetime import datetime

FRACTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*$")
PERCENT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*%\s*$")
NUMBER_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*$")


def parse_mmdd_to_datetime(date_mmdd: str, time_hhmm_24: str) -> datetime:
    year = datetime.now().year
    return datetime.strptime(f"{year} {date_mmdd} {time_hhmm_24}", "%Y %m/%d %H:%M")





def parse_planner_datetime(date_mmdd: str, time_hhmm_24: str) -> datetime:
    date_text = (date_mmdd or "").strip()
    time_text = (time_hhmm_24 or "").strip()
    if not date_text:
        raise ValueError("TODO date is required.")
    if not time_text:
        raise ValueError("TODO time is required.")
    return parse_mmdd_to_datetime(date_text, time_text)

def format_percent(pct: float) -> str:
    if abs(pct - round(pct)) < 1e-9:
        return f"{int(round(pct))}%"
    s = f"{pct:.1f}".rstrip("0").rstrip(".")
    return f"{s}%"


def normalize_number_string(x: float) -> str:
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s


def fraction_denominator_if_present(text: str) -> str | None:
    if text is None:
        return None
    t = str(text).strip()
    m = FRACTION_RE.match(t)
    if not m:
        return None
    return t.split("/", 1)[1].strip()


def _parse_maxpoints_text(max_points_text: str) -> float | None:
    mp = (max_points_text or "").strip()
    if mp == "":
        return None
    try:
        return float(mp)
    except Exception:
        return None


def _score_string(earned: float, maxp: float) -> str:
    return f"{normalize_number_string(earned)}/{normalize_number_string(maxp)}"


def compute_displays_from_inputs(
    grade_text: str,
    score_text: str,
    max_points_text: str
) -> tuple[str, str, str]:
    """
    Returns (grade_display, score_display, max_points_display)

    grade_display: "90%"
    score_display: "18/20"
    max_points_display: "20"

    You can:
    - Enter Score as "18/20" -> computes Grade + Max Points
    - Enter Score as "18" + Max Points -> computes Grade + Score
    - Enter Grade as "90%" + Max Points -> computes Score
    - Enter Grade as "18/20" -> computes Score + Grade + Max Points
    - Enter Grade as "18" + Max Points -> computes Score + Grade
    - Enter Grade as "90" without Max Points -> treated as percent
    """
    g = (grade_text or "").strip()
    s = (score_text or "").strip()
    mp_float = _parse_maxpoints_text(max_points_text)
    maxp_display = "" if mp_float is None else normalize_number_string(mp_float)

    # ---- Score provided (highest priority) ----
    if s != "":
        m = FRACTION_RE.match(s)
        if m:
            earned = float(m.group(1))
            maxp = float(m.group(2))
            if maxp <= 0:
                raise ValueError("Max Points must be greater than 0.")
            pct = (earned / maxp) * 100.0
            return (format_percent(pct), _score_string(earned, maxp), normalize_number_string(maxp))

        m = PERCENT_RE.match(s)
        if m:
            pct = float(m.group(1))
            grade_display = format_percent(pct)
            if mp_float is not None and mp_float > 0:
                earned = (pct / 100.0) * mp_float
                return (grade_display, _score_string(earned, mp_float), normalize_number_string(mp_float))
            return (grade_display, "", maxp_display)

        m = NUMBER_RE.match(s)
        if m and mp_float is not None:
            earned = float(m.group(1))
            if mp_float <= 0:
                raise ValueError("Max Points must be greater than 0.")
            pct = (earned / mp_float) * 100.0
            return (format_percent(pct), _score_string(earned, mp_float), normalize_number_string(mp_float))

        if m and mp_float is None:
            return ("", s, "")

        return ("", s, maxp_display)

    # ---- Grade provided ----
    if g != "":
        m = FRACTION_RE.match(g)
        if m:
            earned = float(m.group(1))
            maxp = float(m.group(2))
            if maxp <= 0:
                raise ValueError("Max Points must be greater than 0.")
            pct = (earned / maxp) * 100.0
            return (format_percent(pct), _score_string(earned, maxp), normalize_number_string(maxp))

        m = PERCENT_RE.match(g)
        if m:
            pct = float(m.group(1))
            grade_display = format_percent(pct)
            if mp_float is not None and mp_float > 0:
                earned = (pct / 100.0) * mp_float
                return (grade_display, _score_string(earned, mp_float), normalize_number_string(mp_float))
            return (grade_display, "", maxp_display)

        m = NUMBER_RE.match(g)
        if m:
            num = float(m.group(1))
            if mp_float is not None and mp_float > 0:
                pct = (num / mp_float) * 100.0
                return (format_percent(pct), _score_string(num, mp_float), normalize_number_string(mp_float))

            # treat as percent
            pct = num
            grade_display = format_percent(pct)
            if mp_float is not None and mp_float > 0:
                earned = (pct / 100.0) * mp_float
                return (grade_display, _score_string(earned, mp_float), normalize_number_string(mp_float))
            return (grade_display, "", maxp_display)

    return ("", "", maxp_display)
