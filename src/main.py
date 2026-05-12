from __future__ import print_function
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pdfplumber
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import SEMESTER_START, SEMESTER_END, TIMEZONE, MY_COURSES, PDF_PATH, YEAR
from src.parse import year_isolation, collect_weekdays_unprocessed, process_weekdays
from src.calendar_client import get_calendar_service, insert_weekly_event, PASTEL_COLOR_IDS

DAY_OFFSET = {
    "monday":    0,
    "tuesday":   1,
    "wednesday": 2,
    "thursday":  3,
    "friday":    4,
}


def build_rrule(end_date) -> str:
    until = end_date.strftime("%Y%m%dT000000Z")
    return f"RRULE:FREQ=WEEKLY;UNTIL={until}"


def parse_time_component(t: str) -> tuple[int, int]:
    h, m = t.split(":")
    return int(h), int(m)


def make_aware_datetime(base_monday, day: str, time_str: str, tz) -> datetime:
    target_date = base_monday + timedelta(days=DAY_OFFSET[day])
    h, m = parse_time_component(time_str)
    return datetime(target_date.year, target_date.month, target_date.day, h, m, tzinfo=tz)


def assign_colors(course_codes: list) -> dict[str, int]:
    """
    Cycles through PASTEL_COLOR_IDS and assigns one colorId per course code.
    The assignment is stable: same list order → same colors every run.
    """
    return {
        code: PASTEL_COLOR_IDS[i % len(PASTEL_COLOR_IDS)]
        for i, code in enumerate(course_codes)
    }


def main():
    if not MY_COURSES:
        print("MY_COURSES is empty in config.py. Add your course codes and re-run.")
        return

    tz           = ZoneInfo(TIMEZONE)
    rrule        = build_rrule(SEMESTER_END)
    color_map    = assign_colors(MY_COURSES)

    print(f"Parsing {PDF_PATH} for year {YEAR}…")
    with pdfplumber.open(PDF_PATH) as pdf:
        year_schedule   = year_isolation(pdf, YEAR)
        day_unprocessed = collect_weekdays_unprocessed(year_schedule)
        schedule        = process_weekdays(day_unprocessed)
    print(f"Found {len(schedule)} courses in the timetable.\n")

    service  = get_calendar_service()
    inserted = 0
    skipped  = 0

    for code in MY_COURSES:
        if code not in schedule:
            print(f"[WARN] '{code}' not found in timetable — skipping.")
            skipped += 1
            continue

        entry    = schedule[code]
        room     = entry["room"] or "TBA"
        name     = entry["name"]
        summary  = f"{code}: {name}"
        color_id = color_map[code]

        print(f"Adding '{summary}' | colorId={color_id} ({len(entry['dayvector'])} session(s)/week)…")

        for day, time_slot in entry["dayvector"]:
            start_str, end_str = time_slot.split("-")
            start_dt = make_aware_datetime(SEMESTER_START, day, start_str, tz)
            end_dt   = make_aware_datetime(SEMESTER_START, day, end_str,   tz)

            event = insert_weekly_event(
                service,
                summary=summary,
                location=room,
                start_dt=start_dt,
                end_dt=end_dt,
                rrule=rrule,
                timezone=TIMEZONE,
                color_id=color_id,
            )

            if event:
                print(f"  ✓ {day.capitalize()} {time_slot} | {room}")
                inserted += 1

    print(f"\nDone. {inserted} event(s) created, {skipped} course(s) skipped.")


if __name__ == "__main__":
    main()
