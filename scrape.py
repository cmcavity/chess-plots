from datetime import datetime
import csv
import json
import os

from bs4 import BeautifulSoup
import requests

RANKINGS_PATH = "data/rankings.csv"
PLAYERS_PATH = "data/players.csv"
SUBSTITUTIONS_PATH = "resources/substitutions.json"
OLIMPBASE_PATH = "resources/olimpbase.txt"

OLIMPBASE_URL = "http://www.olimpbase.org"
FIDE_URL = "https://ratings.fide.com/toparc.phtml"

MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


def load_substitutions():
    substitutions = {}
    with open(SUBSTITUTIONS_PATH) as f:
        data = json.load(f)
        for target, names in data.items():
            for name in names:
                assert name not in substitutions
                substitutions[name] = target
        return substitutions


def load_players():
    players = []
    with open(PLAYERS_PATH) as f:
        rdr = csv.reader(f)
        for row in rdr:
            players.append(row[0])
    return players


def load_start_month():
    with open(RANKINGS_PATH) as f:
        rdr = csv.reader(f)
        last_row = list(rdr)[-1]
        date = last_row[0]
        month, year = date_to_month_year(date)
        month_idx = MONTHS.index(month)
        if month_idx == len(MONTHS) - 1:
            month = MONTHS[0]
            year = str(int(year) + 1)
        else:
            month = MONTHS[month_idx + 1]
        return month, int(year)


def add_list_to_database(rankings):
    with open(RANKINGS_PATH, "a") as f:
        wtr = csv.writer(f)
        for row in rankings:
            wtr.writerow(row)


def add_new_players_to_database(players, new_players):
    with open(PLAYERS_PATH, "w") as f:
        wtr = csv.writer(f)
        players += new_players
        players.sort()
        for name in players:
            wtr.writerow([name])


def get(url, params=None):
    res = requests.get(url, params)
    assert res.status_code == 200
    return res.text


def confirm(prompt):
    s = input(f"{prompt} [Y/n] ").strip().capitalize()
    return s in ["Y", "Yes"]


def month_year_to_fide_list_code(month, year):
    month = month.lower()
    month_idx = MONTHS.index(month)

    # starting july 2001, FIDE publishes a new rating list every 3 months
    case1 = (
        (year == 2000 and month_idx >= MONTHS.index("july"))
        or (2000 < year and year < 2009)
        or (year == 2009 and month_idx < MONTHS.index("july"))
    )

    # starting july 2009, FIDE publishes a new rating list every 2 months
    case2 = (
        (year == 2009 and month_idx >= MONTHS.index("july"))
        or (2009 < year and year < 2012)
        or (year == 2012 and month_idx < MONTHS.index("july"))
    )

    # starting july 2012, FIDE publishes a new rating list every month
    case3 = (year == 2012 and month_idx >= MONTHS.index("july")) or (year > 2012)

    start_month = "july"
    code_gap = 4  # lists for women, juniors, and girls are also provided, consecutively
    start_year = None
    months_gap = None
    start_code = None

    if case1:
        start_year = "2000"
        months_gap = 3
        start_code = 1
    elif case2:
        start_year = "2009"
        months_gap = 2
        start_code = 145
    elif case3:
        start_year = "2012"
        months_gap = 1
        start_code = 217
    else:
        return None

    start_date = month_year_to_date(start_month, start_year)
    date = month_year_to_date(month, str(year))
    months_diff = int(date) - int(start_date)
    if months_diff % months_gap != 0:
        return None
    else:
        code = start_code + code_gap * (months_diff / months_gap)
        return code


def month_year_to_date(month, year):
    return str((int(year) - 1967) * 12 + MONTHS.index(month.lower()))


def date_to_month_year(date):
    month = MONTHS[int(date) % 12]
    year = str(1967 + int(date) // 12)
    return month, year


def parse_olimpbase_list(text, substitutions):
    soup = BeautifulSoup(text, "lxml")

    title = soup.title.string.split()

    if str(title[3]) == "1969":
        month = "January"
        year = "1969"
    elif str(title[3]) == "1970":
        month = "January"
        year = "1970"
    else:
        month = str(title[3])
        year = str(title[4])

    date = month_year_to_date(month, year)

    # header of the table
    i = text.find('<span style="font-weight: bold; background-color: #EEEECC;">')

    if i == -1:
        raise Exception("Error parsing file: can't find table.")

    lines = text[i:].splitlines()

    rankings = []

    for i in range(1, 101):
        line = lines[i]

        # reached end of table
        if line.find("<a href") == -1:
            break

        chunks = line.split()

        rank = int(chunks[0].strip("="))

        assert 1 <= rank and rank <= 100

        chunks.reverse()

        rating = 0

        for chunk in chunks:
            if len(chunk) == 4 and chunk[0] == "2":
                rating = int(chunk)
                break

        assert rating > 2400

        mark1 = 'blank">'
        mark2 = "</a>"

        start = line.find(mark1) + len(mark1)
        end = line.find(mark2)

        assert start != -1 and end != -1 and start < end

        name = str(line[start:end])
        rank = str(rank)
        rating = str(rating)

        if name in substitutions:
            new_name = substitutions[name]
            name = new_name
        rankings.append([date, rank, name, rating])

    return rankings


def extract_new_players(players, new_players, rankings):
    for row in rankings:
        name = row[2]
        if name not in players:
            new_players.add(name)


def parse_fide_list(text, substitutions, expected_month, expected_year):
    text = text.replace("&nbsp;", "")

    soup = BeautifulSoup(text, "lxml")

    title = soup.title.string.split()

    month = str(title[3])
    year = int(title[4])
    assert month.lower() == expected_month.lower()
    assert year == expected_year

    date = month_year_to_date(month, year)

    table = soup.find_all("table")[4]
    rows = table.find_all("tr")

    rankings = []

    for row in rows[1:]:
        columns = row.find_all("td")

        if len(columns) != 7:
            raise Exception("Error parsing file: missing column.")

        rank = str(columns[0].get_text())
        name = str(columns[1].get_text())
        rating = str(columns[4].get_text())

        if name in substitutions:
            new_name = substitutions[name]
            name = new_name

        rankings.append([date, rank, name, rating])

    return rankings


def get_new_fide_lists_and_players(substitutions, players):
    current_month_idx = datetime.now().month - 1
    current_year = datetime.now().year

    new_lists = []
    new_players = set()
    month, year = load_start_month()
    while (
        year < current_year
        or year == current_year
        and MONTHS.index(month) <= current_month_idx
    ):
        code = month_year_to_fide_list_code(month, year)
        if code is not None:
            params = {"cod": code}
            text = get(FIDE_URL, params)
            rankings = parse_fide_list(text, substitutions, month, year)
            extract_new_players(players, new_players, rankings)
            new_lists.append(rankings)

            print(f"Found new list: {month.capitalize()} {year}")

        # Increment (month, year)
        month_idx = MONTHS.index(month)
        month, year = (
            (MONTHS[month_idx + 1], year) if month_idx < 11 else ("january", year + 1)
        )

    return new_lists, new_players


def add_olimpbase_lists(substitutions):
    """Adds all the rating lists from olimpbase.org to the database.

    OlimpBase is a site that hosts archival rating lists dating from 1967-2001.
    """

    print("Adding lists from olimpbase.org ...")

    with open(OLIMPBASE_PATH, "r") as f:
        names = f.read().splitlines()
        for name in names:
            url = f"{OLIMPBASE_URL}/Elo/Elo{name}"
            text = get(url)
            rankings = parse_olimpbase_list(text, substitutions)
            add_list_to_database(rankings)

    print("Done.")


def add_new_fide_lists(substitutions, players):
    """Adds new rating lists from ratings.fide.com to the database.

    FIDE is the international chess federation. They post a new rating list of
    the top 100 players every month, and host past rating lists dating back to
    July 2000.
    """

    print("Checking ratings.fide.com for new rating lists.")

    new_lists, new_players = get_new_fide_lists_and_players(substitutions, players)
    count_new_lists = len(new_lists)

    if count_new_lists == 0:
        print("No new rating lists found.")
    elif confirm(f"Found {count_new_lists} new rating list(s). Update database?"):
        print("Updating database ...")

        for rankings in new_lists:
            add_list_to_database(rankings)

        count_new_players = len(new_players)
        if count_new_players > 0:
            print(f"Found {count_new_players} new players:")
            for player in new_players:
                print(f"{player}")
            add_new_players_to_database(players, new_players)

        print("Database is up to date.")


def main():
    substitutions = load_substitutions()
    players = load_players()

    if not os.path.exists(RANKINGS_PATH):
        print("No rankings database found at `data/rankings.csv`.")
        if not confirm("Do you want to rebuild the database from scratch?"):
            return
        add_olimpbase_lists(substitutions)

    add_new_fide_lists(substitutions, players)


if __name__ == "__main__":
    main()
