import pdfplumber
weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
roman = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}

def year_isolation(pdf:pdfplumber.pdf.PDF, year:int) -> list:
    """
    :param pdf: pdfplumber PDF object
    :param year: the year to isolate
    :return: unprocessed nested list of the schedule containing the specified year

    This function picks out the lists containing the schedule for the specified year. The raw nested list is messy, years are not page seperated or anything, this function looks for the year title and outputs all lists until the next year title is reached.
    """

    def search_for_year(year:str) -> int:
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

    start_index = search_for_year(start_year)
    end_index = search_for_year(end_year)

    if start_index == end_index:
        end_index = search_for_year(roman[year + 2])
    print(end_index)
    return rows[start_index:end_index]
