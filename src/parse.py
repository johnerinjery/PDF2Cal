import pdfplumber

weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]
roman    = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}

# Column layout of the new-format tables (26 columns wide, consistent across
# the "Year I", "Year II" and "Year III & IV" blocks):
#   col 0            -> day name
#   cols 1-3         -> slot 1  (Course, Course Name, Room)
#   cols 4-6         -> slot 2
#   cols 7-9         -> slot 3
#   cols 10-12       -> slot 4
#   col 13           -> lunch-break marker column ("13:00"), no data
#   cols 14-16       -> slot 5
#   cols 17-19       -> slot 6
#   cols 20-22       -> slot 7
#   cols 23-25       -> slot 8
# Each 3-wide slot is (course_code, course_name, room).

COLUMN_SLOTS = [
    (1,  "9:00-10:00"),
    (4,  "10:00-11:00"),
    (7,  "11:00-12:00"),
    (10, "12:00-13:00"),
    (14, "14:00-15:00"),
    (17, "15:00-16:00"),
    (20, "16:00-17:00"),
    (23, "17:00-18:00"),
]


def year_isolation(pdf: pdfplumber.pdf.PDF, year: int) -> list:
    """
    Extracts all table rows belonging to the given year from the PDF.

    The new format labels sections "Year I", "Year II", "Year III & IV"
    (3rd and 4th years share one combined section). A section header's
    remainder (everything after "Year") is tokenized on whitespace/"&" to
    get the roman numerals it covers, e.g. "III & IV" -> ["III", "IV"].
    We isolate the block whose tokens contain the roman numeral for the
    requested year.
    """
    rows = [
        row
        for page in pdf.pages
        for table in page.extract_tables()
        if table
        for row in table
    ]

    headers = []  # (row_index, [roman tokens])
    for idx, row in enumerate(rows):
        cell = row[0]
        if cell and cell.strip().startswith("Year"):
            remainder = cell.strip()[len("Year"):]
            tokens = [t for t in remainder.replace("&", " ").split() if t]
            headers.append((idx, tokens))

    target = roman.get(year)
    start_idx = None
    for i, (idx, tokens) in enumerate(headers):
        if target in tokens:
            start_idx = idx
            end_idx = headers[i + 1][0] if i + 1 < len(headers) else len(rows)
            break

    if start_idx is None:
        return []

    return rows[start_idx:end_idx]


def collect_weekdays_unprocessed(year_schedule: list) -> list:
    """
    Keeps only the real per-day data rows, dropping:
      - the "Year X" / "Day" / column-header rows (day cell is empty)
      - each day's group-letter row (e.g. "Monday | A | B | E | ...")

    Each weekday's FIRST appearance in the section is its group-letter row
    (this holds for both the single-data-row-per-day old-style block and the
    multi-row-per-day new-style block, since a blank label/header row always
    separates the group-letter row from the data rows that follow). Every
    later row with that same day name is real course data.
    """
    seen_days = set()
    day_rows = []

    for row in year_schedule:
        cell = row[0]
        if not cell:
            continue
        day = cell.strip().lower()
        if day not in weekdays:
            continue

        if day not in seen_days:
            seen_days.add(day)
            continue  # this is the group-letter row, skip it

        day_rows.append(row)

    return day_rows


def _clean(cell) -> str:
    return (cell or "").replace("\n", " ").strip()


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

    Handles two course-cell shapes seen in the new tables:
      - normal: separate (code, name, room) columns
      - cross-listed: "CODE1/CODE2" in the code column, registered under
        each alt code so lookups by either code succeed
      - merged multi-course cells (comma-separated "CODE:Name, CODE:Name"),
        as still appear in some lab/tutorial blocks
    """
    courses: dict = {}

    def register(code, name, room, day_name, time_slot):
        code = code.strip()
        if not code:
            return
        if code not in courses:
            courses[code] = {"dayvector": [], "room": room or "TBA", "name": name}
        courses[code]["dayvector"].append((day_name, time_slot))

    for row in unprocessed_weekdays:
        day_name = row[0].strip().lower()

        for start, time_slot in COLUMN_SLOTS:
            if start >= len(row):
                continue
            # course codes never legitimately contain a newline; that shows
            # up when pdfplumber splits a code across a line wrap
            raw_code = (row[start] or "").replace("\n", "").strip()
            name_cell = _clean(row[start + 1]) if start + 1 < len(row) else ""
            room_cell = _clean(row[start + 2]) if start + 2 < len(row) else ""

            if not raw_code:
                continue

            if "," in raw_code and ":" in raw_code:
                # merged cell: "CODE1:Name1, CODE2:Name2, ..."
                for piece in raw_code.split(","):
                    piece = piece.strip()
                    if ":" not in piece:
                        continue
                    code, name = piece.split(":", 1)
                    register(code, name.strip(), room_cell, day_name, time_slot)
            elif "/" in raw_code:
                # cross-listed course, e.g. "BI3134/DS3114"
                for alt_code in raw_code.split("/"):
                    register(alt_code, name_cell, room_cell, day_name, time_slot)
            else:
                register(raw_code, name_cell, room_cell, day_name, time_slot)

    return courses


# testing
if __name__ == "__main__":
    import json
    from config import PDF_PATH, YEAR

    with pdfplumber.open(PDF_PATH) as pdf:
        year_schedule   = year_isolation(pdf, YEAR)
        day_unprocessed = collect_weekdays_unprocessed(year_schedule)
        schedule        = process_weekdays(day_unprocessed)

    print(json.dumps(schedule, indent=2))
