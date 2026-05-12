import pdfplumber

cap_alpha = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]
roman = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
time_table_template = ["", "9:00-9:55", "rooms",  "10:00-10:55", "rooms", "11:00-11:55", "rooms", "12:00-12:55", "rooms", "14:00-14:55", "rooms", "15:00-15:55", "rooms", "16:00-16:55", "rooms", "17:00-17:55", "rooms"]

def year_isolation(pdf:pdfplumber.pdf.PDF, year:int) -> list:
    """
    :param pdf: pdfplumber PDF object
    :param year: the year to isolate
    :return: unprocessed nested list of the schedule containing the specified year

    This function picks out the lists containing the schedule for the specified year. The raw nested list is messy, years are not page seperated or anything, this function looks for the year title and outputs all lists until the next year title is reached.
    """

    def search_for_year(year:str, rows:list) -> int:
        """
        Helper function
        """
        for row in rows:
            if (f := row[0]) is not None and "Year" in f:
                f_comps = f.strip().split()

                if year in f_comps:
                    return rows.index(row)
                
    rows = [
    row
    for page in pdf.pages
    for table in page.extract_tables()
    if table
    for row in table
    ]

    end_year = roman[year + 1] # This will break in your 5th year, congrats my guy. Add another entry in the roman dictionary to fix it.
    start_year = roman[year]

    start_index = search_for_year(start_year, rows)
    end_index = search_for_year(end_year, rows)

    if start_index == end_index:
        end_index = search_for_year(roman[year + 2], rows)
    
    return rows[start_index:end_index]

def collect_weekdays_unprocessed(year_schedule:list) -> list:
    """
    :param year_schedule: unprocessed nested list of the schedule containing the specified year
    :return: list of lists with weekdays as keys and lists of course codes and timings as values

    This function takes the unprocessed nested list of the schedule for a specific year and organizes it into a list with weekdays that may be unprocessed.
    """
    def mostly_true(lst):
        return sum(lst) > len(lst) / 2
    
    day_unprocessed = []
    for day in year_schedule:
        if day[0].strip().lower() in weekdays:
            if not mostly_true(list((i in (cap_alpha + ['']) for i in day[1:]))): # this gets rid of the row with the group names and stuff
                day_unprocessed.append(day[:9] + day[10:])
    return day_unprocessed

def process_weekdays(day_up:list) -> dict:
    """
    :param day_unprocessed: list of lists with weekdays as keys and lists of course codes and timings as values
    :return: dictionary with weekdays as keys and lists of course codes and timings as values

    This function takes the unprocessed list of weekdays and processes it into a more usable format, a dictionary with weekdays as keys and lists of course codes and timings as values.
    """
    schedule = {day: [] for day in weekdays}
    for day in day_up:
        day_name = day[0].strip().lower()
        for i in range(1, len(day), 2):
            if day[i] is not None and day[i].strip() != "":
                course_code = day[i].split(":")[0]
                if day[i+1] is not None and day[i].strip() != "":
                    pass
            else:
                schedule[day_name].append((time_table_template[i-1], None))
    return schedule

with pdfplumber.open("schedule.pdf") as pdf:
    year_schedule = year_isolation(pdf, 3)
    day_unprocessed = collect_weekdays_unprocessed(year_schedule)
    schedule = process_weekdays(day_unprocessed)
    print(schedule)