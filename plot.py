import matplotlib.pyplot as plt
import numpy as np
import argparse
import io
import csv
import sys

RANKINGS_PATH = 'data/rankings.csv'
PLAYERS_PATH = 'data/players.csv'

DEFAULT_START_YEAR = 1967
DEFAULT_END_YEAR = 2023

DEFAULT_MAX_RANK = 25

MAX_RATING = 2900
MIN_RATING = 2500

START_DATE = 5

NO_RATING = float('-inf')
NO_RANK = float('inf')

def load_players():
    players_table = []
    with open(PLAYERS_PATH) as f:
        rdr = csv.reader(f)
        for row in rdr:
            players_table.append(row[0])
    return players_table

def load_rankings():
    with open(RANKINGS_PATH) as f:
        return list(csv.reader(f))

def read_names(names_path, players_table):
    names = []

    if names_path:
        # read in names from a file
        with open(names_path) as f:
            lines = f.read().splitlines()

        for line in lines:
            user_input = line.strip()
            if user_input == '':
                continue
            name = parse_name(user_input, players_table, require_exact=True)

            if not name:
                print(f'No exact match for {user_input}. Skipping.')
            elif name in names:
                print(f'Ignoring duplicate: {name}')
            else:
                names.append(name)
    else:
        # read in names from the command line
        while True:
            num = str(len(names) + 1)
            user_input = input(f'Player {num}: ').strip()
            if user_input == '':
                break

            name = parse_name(user_input, players_table)

            if name:
                if name in names:
                    print(f'Ignoring duplicate: {name}')
                else:
                    names.append(name)

    return names

def parse_name(name, players_table, require_exact=False):

    if name in players_table:
        return name

    if require_exact:
        return None

    matches = []

    for player in players_table:
        if player.lower().startswith(name.lower()):
            matches.append(player)

    if not matches:
        print('No matches found for \"{}\"'.format(name)) 
        return None
    if len(matches) == 1:
        player = matches[0]
        print('Match found for \"{}\": {}'.format(name, player))
        return player
    elif len(matches) <= 10:
        print('Multiple matches found for \"{}\":'.format(name))

        for match in matches:
            print(match)

        while True:
            s = input('Pick one: ').strip()

            if s == '':
                print('None selected.')
                return None

            choices = []
            
            for match in matches:
                if match.lower().startswith(s.lower()):
                    choices.append(match)
            
            if len(choices) == 1:
                choice = choices[0]
                print('Your choice: {}'.format(choice))
                return choice

            print('Try again.')
    else:
        print('Too many matches to display. Refine your search.')
        return None

def plot(names, args, rankings_table):
    setup_plot(args.start, args.end, args.rank)

    for name in names:
        date = START_DATE

        X = []
        Y = []

        # query rankings table for player
        for row in rankings_table:
            curr_date = int(row[0])
            curr_rank = int(row[1])
            curr_name = row[2]
            curr_rating = int(row[3])

            if curr_date != date:
                if len(X) == 0 or X[-1] != date:
                    X.append(date)
                    Y.append(NO_RANK if args.rank else NO_RATING)
                date = curr_date

            if curr_name == name:
                X.append(date)
                Y.append(curr_rank if args.rank else curr_rating)

        # convert x-axis units
        X = np.array(X, dtype=np.float64)
        X /= 12
        X += DEFAULT_START_YEAR
        
        # plot player
        if args.rank:
            plt.step(X, Y, label=name, where='post')
        else:
            plt.plot(X, Y, label=name)
    
    if not args.hide_legend:
        plt.legend()

    plt.show()

def setup_plot(year1, year2, rank_mode):
    start_year = DEFAULT_START_YEAR
    end_year = DEFAULT_END_YEAR
    max_rank = DEFAULT_MAX_RANK

    if year1 and start_year <= year1 and year1 <= end_year:
        start_year = year1
        
    if year2 and start_year <= year2 and year2 <= end_year:
        end_year = year2

    title = 'Chess Rankings' if rank_mode else 'Chess Ratings'
    label = 'World Rank' if rank_mode else 'FIDE Rating'

    plt.title(title)
    plt.xlabel('Year')
    plt.ylabel(label)

    xmin = start_year
    xmax = end_year + 1

    ymin = 0 if rank_mode else MIN_RATING
    ymax = max_rank if rank_mode else MAX_RATING
    
    plt.axis([xmin, xmax, ymin, ymax])
    plt.ticklabel_format(style='plain', useOffset=False)
    
    if (rank_mode):
        plt.yticks(np.arange(1, ymax + 1, 1.0))
        plt.grid(axis='y')

def main(args):
    players_table = load_players()
    rankings_table = load_rankings()

    names = read_names(args.file, players_table)

    if len(names) > 0:
        plot(names, args, rankings_table)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage='%(prog)s [options]')

    parser.add_argument('--rank', action='store_true', help='plot ranks instead of ratings')
    parser.add_argument('--hide-legend', action='store_true', help='don\'t display legend')
    parser.add_argument('-s', dest='start', type=int, help='specify start year')
    parser.add_argument('-e', dest='end', type=int, help='specify end year')
    parser.add_argument('-n', dest='file', help='provide text file with list of names')

    args = parser.parse_args()
    main(args)
