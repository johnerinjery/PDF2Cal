# PDF2Cal

A small utility that reads the IISER Pune course timetable PDF and populates your Google Calendar with weekly recurring events for your courses.

Pair it with [CalClear](https://github.com/johnerinjery/CalClear) (which wipes your existing weekly events) for a clean slate at the start of every semester. Because automation is awesome.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Google API credentials

- Go to the [Google Cloud Console](https://console.cloud.google.com/)
- Create a project → enable the **Google Calendar API**
- Create an **OAuth 2.0 Client ID** (Desktop app) → download as `credentials.json`
- Place `credentials.json` in the project root

<br>

> If you already have `credentials.json` and `token.json` from CalClear, copy them straight into this directory. The OAuth scope is identical.

### 3. Place the timetable PDF

Put the IISER timetable PDF in the project root and name it `schedule.pdf`.

## Configuration

Everything you need to change lives in **`config.py`**:

```python
SEMESTER_START = date(2025, 8, 4)   # Must be the Monday of your first teaching week
SEMESTER_END   = date(2025, 11, 28) # Last day of the semester (events stop recurring here)
TIMEZONE       = "Asia/Kolkata"

MY_COURSES = [
    "PH3234",
    "MT4123",
    # add your course codes here, exactly as they appear in the PDF
]

YEAR = 3   # your current BS-MS year as an integer
```

---

## Usage

### Dry run (just testing)

Before touching your calendar, run `parse.py` standalone to confirm your course codes are being read correctly:

```bash
python src/parse.py
```

This prints the full parsed schedule as JSON - no calendar writes happen.

### Push to calendar

```bash
python src/main.py
```

On the first run, a browser window will open for Google OAuth consent. After you authorise, a `token.json` is cached and subsequent runs skip the browser step.

Terminal output looks like:

```
Parsing schedule.pdf for year 3…
Found 47 courses in the timetable.

Adding 'PH3234: Statistical Mechanics I' | colorId=1 (2 session(s)/week)…
  ✓ Wednesday 11:00-11:55 | LHC 103
  ✓ Thursday 11:00-11:55 | LHC 103
Adding 'MA4123: Complex Analysis' | colorId=2 (2 session(s)/week)…
  ✓ Monday 10:00-10:55 | LHC 301
  ✓ Friday 10:00-10:55 | LHC 301

Done. 6 event(s) created, 0 course(s) skipped.
```


## Footnotes

**`SEMESTER_START` must be a Monday.**
The date arithmetic anchors every slot to an offset from that Monday (`wednesday` = Monday + 2, etc.). If you set a non-Monday date, all events will land on the wrong days.

**Run CalClear before PDF2Cal.**
PDF2Cal only adds events; it does not check for duplicates. Running it twice will create duplicate recurring events. Use CalClear to wipe first, then PDF2Cal to repopulate.
