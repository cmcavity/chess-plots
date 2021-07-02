from bs4 import BeautifulSoup
import requests
import argparse
import csv
import json
import os

RANKINGS_PATH = 'data/rankings.csv'
PLAYERS_PATH = 'data/players.csv'

SUBSTITUTIONS_PATH = 'resources/substitutions.json'
OLIMPBASE_PATH = 'resources/olimpbase.txt'

OLIMPBASE_URL = 'http://www.olimpbase.org'
FIDE_URL = 'https://ratings.fide.com/toplist.phtml'
FIDE_FORM_URL = 'https://ratings.fide.com/toparc.phtml'

MONTHS = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
]

def month_year_to_date(month, year):
    return str((int(year) - 1967) * 12 + MONTHS.index(month))

def date_to_month_year(date):
    month = MONTHS[int(date) % 12]
    year = str(1967 + int(date) // 12)
    return month, year

def download(url, params=None):
    res = requests.get(url, params)
    assert res.status_code == 200
    return res.text

def confirmation(prompt):
    s = input(f'{prompt} [Y/n] ').strip().capitalize()
    return s in ['Y', 'Yes']

def load_dates():
    dates = set() 

    with open(RANKINGS_PATH) as f:
        rdr = csv.reader(f)
        for row in rdr:
            date = row[0]
            if date not in dates:
                dates.add(date)
    
    return dates

def load_substitutions():
    subs = {}

    with open(SUBSTITUTIONS_PATH) as f:
        data = json.load(f) 

    for target, names in data.items():
        for name in names: 
            subs[name] = target

    return subs

def load_players():
    players = []
    with open(PLAYERS_PATH) as f:
        rdr = csv.reader(f)
        for row in rdr:
            players.append(row[0])
    return players

def write_list(l):
    with open(RANKINGS_PATH, 'a') as f:
        wtr = csv.writer(f)
        for row in l:
            wtr.writerow(row)

def write_new_players(new_players):
    with open(PLAYERS_PATH, 'a') as f:
        wtr = csv.writer(f)
        for name in new_players:
            wtr.writerow([name])

def add_new_players(players, new_players, l):
    for row in l:
        name = row[2]
        if name not in players:
            new_players.add(name)

def parse_fide_list(text, substitutions):
    text = text.replace('&nbsp;', '')
    
    soup = BeautifulSoup(text, 'lxml')

    title = soup.title.string.split()

    month = str(title[3]) 
    year = str(title[4])
    date = month_year_to_date(month, year)

    table = soup.find_all('table')[4]
    rows = table.find_all('tr')

    rankings = []
    
    for row in rows[1:]:
        columns = row.find_all('td')
        
        if len(columns) != 7:
            raise Exception('Error parsing file: missing column.')
        
        rank = str(columns[0].get_text())
        name = str(columns[1].get_text())
        rating = str(columns[4].get_text())

        if name in substitutions:
            print('Substitution: \"{}\" --> \"{}\"'.format(name, substitutions[name]))
            name = substitutions[name]

        rankings.append([date, rank, name, rating])

    return rankings

def parse_olimpbase_list(text, substitutions):
    soup = BeautifulSoup(text, 'lxml')

    title = soup.title.string.split()

    if str(title[3]) == '1969':
        month = 'January'
        year = '1969'
    elif str(title[3]) == '1970':
        month = 'January'
        year = '1970'
    else:
        month = str(title[3])
        year = str(title[4])
    
    date = month_year_to_date(month, year)
    
    # header of the table
    i = text.find('<span style="font-weight: bold; background-color: #EEEECC;">')

    if i == -1:
        raise Exception('Error parsing file: can\'t find table.')

    lines = text[i:].splitlines()

    rankings = []

    for i in range(1, 101):
        line = lines[i]

        # reached end of table
        if line.find('<a href') == -1:
            break

        chunks = line.split()

        rank = int(chunks[0].strip('='))

        assert 1 <= rank and rank <= 100

        chunks.reverse()

        rating = 0

        for chunk in chunks:
            if len(chunk) == 4 and chunk[0] == '2':
                rating = int(chunk)
                break

        assert rating > 2400

        mark1 = 'blank\">'
        mark2 = '</a>'

        start = line.find(mark1) + len(mark1)
        end = line.find(mark2)
        
        assert start != -1 and end != -1 and start < end

        name = str(line[start:end])
        rank = str(rank)
        rating = str(rating)

        if name in substitutions:
            print('Substitution: \"{}\" --> \"{}\"'.format(name, substitutions[name]))
            name = substitutions[name]
        rankings.append([date, rank, name, rating])

    return rankings


def add_olimpbase_lists(substitutions):
    with open(OLIMPBASE_PATH, 'r') as f:
        names = f.read().splitlines()

    if confirmation('Add all lists from olimpbase.org?'):
        print('Adding lists ...')

        with open(RANKINGS_PATH, 'a') as f:
            wtr = csv.writer(f)

            for name in names:
                url = f'{OLIMPBASE_URL}/Elo/Elo{name}'
                text = download(url)
                ls = parse_olimpbase_list(text, substitutions)
                write_list(ls)

        print('Done.')

def add_new_fide_lists(substitutions, players):
    print('Checking fide.com for new rating lists ...')

    text = download(FIDE_URL)
    soup = BeautifulSoup(text, 'lxml')
    form = soup.find_all('form')[0]
    options = form.find_all('option')

    dates = load_dates()
    new_dates = []

    # look at each date
    for option in options:
        tokens = option.text.split()
        month = tokens[3]
        year = tokens[4]
        date = month_year_to_date(month, year)

        # new rating list
        if date not in dates:
            code = option['value'] 
            new_dates.append((month, year, code))

    count = len(new_dates)

    if count == 0:
        print('No new rating lists found.')
    else:
        if confirmation(f'Found {count} new rating list(s). Display all?'):
            for date in new_dates:
                print(f'{date[0]} {date[1]}')
        
        if confirmation('Add lists to database?'):
            print('Adding lists ...')

            new_players = set()

            for date in new_dates:
                params = {'cod': date[2]}
                text = download(FIDE_FORM_URL, params)
                ls = parse_fide_list(text, substitutions)
                add_new_players(players, new_players, ls)
                write_list(ls)
            
            write_new_players(new_players)
                
            print(f'Done.')

            for player in new_players:
                print(f'New player: {player}')

def main():
    substitutions = load_substitutions()
    players = load_players()

    if not os.path.exists(RANKINGS_PATH):
        add_olimpbase_lists(substitutions)

    add_new_fide_lists(substitutions, players)

if __name__ == '__main__':
    main()
