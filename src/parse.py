import pdfplumber

# ── Constants ──────────────────────────────────────────────────────────────────
cap_alpha = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
weekdays  = ["monday", "tuesday", "wednesday", "thursday", "friday"]
roman     = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}

time_table_template = [
    "",
    "9:00-9:55",   "rooms",
    "10:00-10:55", "rooms",
    "11:00-11:55", "rooms",
    "12:00-12:55", "rooms",
    "14:00-14:55", "rooms",
    "15:00-15:55", "rooms",
    "16:00-16:55", "rooms",
    "17:00-17:55", "rooms",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def year_isolation(pdf: pdfplumber.pdf.PDF, year: int) -> list:
    """
    Extracts all table rows belonging to the given year from the PDF.
    Scans for year title rows (e.g. 'II Year') as delimiters.
    """
    def search_for_year(label: str, rows: list):
        for row in rows:
            if (f := row[0]) is not None and "Year" in f:
                if label in f.strip().split():
                    return rows.index(row)

    rows = [
        row
        for page in pdf.pages
        for table in page.extract_tables()
        if table
        for row in table
    ]

    start_label = roman[year]
    end_label   = roman[year + 1]

    start_idx = search_for_year(start_label, rows)
    end_idx   = search_for_year(end_label, rows)

    # Edge case: back-to-back years on the same page share a title row
    if start_idx == end_idx:
        end_idx = search_for_year(roman[year + 2], rows)

    return rows[start_idx:end_idx]


def collect_weekdays_unprocessed(year_schedule: list) -> list:
    """
    Filters out header rows (group labels like A, B, C…) and keeps only
    rows that represent actual course slots for a weekday.
    Also drops the spurious 10th column that appears in some PDF exports.
    """
    def mostly_true(lst):
        return sum(lst) > len(lst) / 2

    day_unprocessed = []
    for row in year_schedule:
        if row[0] is None:
            continue
        if row[0].strip().lower() not in weekdays:
            continue
        # Discard rows where the payload is mostly group-letter labels
        if mostly_true([i in (cap_alpha + [""]) for i in row[1:]]):
            continue
        day_unprocessed.append(row[:9] + row[10:])  # drop column index 9

    return day_unprocessed


def process_weekdays(unprocessed_weekdays: list) -> dict:
    """
    Converts the flat weekday rows into a course-keyed dictionary:

        {
            "PH3234": {
                "dayvector": [("wednesday", "11:00-11:55"), ...],
                "room": "LHC 103",
                "name": "Statistical Mechanics I",
            },
            ...
        }

    Each (day, time) pair in dayvector is one weekly class session.
    If a course appears in multiple rooms (rare), the first room wins.
    """
    time_slots = time_table_template[1::2]  # every odd entry is a time string
    courses: dict = {}

    for day_row in unprocessed_weekdays:
        day_name = day_row[0].strip().lower()

        for slot_idx, time_slot in enumerate(time_slots):
            course_idx = 2 * slot_idx + 1
            room_idx   = course_idx + 1

            course = day_row[course_idx] if course_idx < len(day_row) else None
            room   = day_row[room_idx]   if room_idx   < len(day_row) else None

            if course:
                course = course.replace("\n", " ").strip()
            if room:
                room = room.replace("\n", " ").strip()

            if not course:
                continue

            # "PH3234:Statistical Mechanics I" → code="PH3234", name="Statistical Mechanics I"
            parts = course.split(":", 1)
            code  = parts[0].strip()
            name  = parts[1].strip() if len(parts) > 1 else code

            if code not in courses:
                courses[code] = {"dayvector": [], "room": room, "name": name}

            courses[code]["dayvector"].append((day_name, time_slot))

    return courses


# ── Entry point for standalone testing ────────────────────────────────────────
if __name__ == "__main__":
    import json
    from config import PDF_PATH, YEAR

    with pdfplumber.open(PDF_PATH) as pdf:
        year_schedule   = year_isolation(pdf, YEAR)
        day_unprocessed = collect_weekdays_unprocessed(year_schedule)
        schedule        = process_weekdays(day_unprocessed)

    print(json.dumps(schedule, indent=2))
