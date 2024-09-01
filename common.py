import csv

RANKINGS_PATH = 'data/rankings.csv'
PLAYERS_PATH = 'data/players.csv'

MONTHS = [
    'january',
    'february',
    'march',
    'april',
    'may',
    'june',
    'july',
    'august',
    'september',
    'october',
    'november',
    'december',
]


def load_table_from_csv(path):
    with open(path) as f:
        return list(csv.reader(f))


def load_rankings():
    return load_table_from_csv(RANKINGS_PATH)


def load_players():
    return load_table_from_csv(PLAYERS_PATH)


def date_to_month_year(date):
    month = MONTHS[int(date) % 12]
    year = str(1967 + int(date) // 12)
    return month, year


def month_year_to_date(month, year):
    return str((int(year) - 1967) * 12 + MONTHS.index(month.lower()))
