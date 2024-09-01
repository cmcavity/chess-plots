import csv
from tabulate import tabulate

from common import date_to_month_year, month_year_to_date, load_rankings


def get_rating_gaps(rankings):
    cur_date = None
    gaps = []
    for i, entry in enumerate(rankings):
        date = entry[0]
        rank = entry[1]
        if date == cur_date:
            continue
        if rank == '1':
            second_entry = rankings[i + 1]
            player1 = entry[2]
            player2 = second_entry[2]
            gap = int(entry[3]) - int(second_entry[3])
            month, year = date_to_month_year(date)
            month, year = month.capitalize(), year.capitalize()
            gaps.append((player1, player2, gap, month, year))
        cur_date = date
    return gaps


def average_gaps(gaps, player):
    rankings = load_rankings()
    gaps = get_rating_gaps(rankings)
    nums = []
    for gap in gaps:
        if gap[0] == player:
            nums.append(gap[2])
    avg = sum(nums) / len(nums)
    print(f'{player} had an average gap of {avg}')


def largest_gaps(args):
    rankings = load_rankings()
    gaps = get_rating_gaps(rankings)
    if args.player != None:
        gaps = [entry for entry in gaps if entry[0] == args.player]
    gaps.sort(key=lambda x: -x[2])
    gaps = gaps[:args.number]
    header = ['First place', 'Second place', 'Gap', 'Month', 'Year']
    print(tabulate(gaps, headers=header, tablefmt='plain'))


def second_place_players(args):
    rankings = load_rankings()
    gaps = get_rating_gaps(rankings)

    periods = []

    def previous_month(month, year):
        date = month_year_to_date(month, year)
        prev_date = str(int(date) - 1)
        month, year = date_to_month_year(prev_date)
        return month.capitalize(), year.capitalize()

    def num_months(start_month, start_year, end_month, end_year):
        start_date = int(month_year_to_date(start_month, start_year))
        end_date = int(month_year_to_date(end_month, end_year))
        return end_date - start_date + 1

    initial = gaps[0]
    rest = gaps[1:]

    first = initial[0]
    second = initial[1]
    start_month = initial[3]
    start_year = initial[4]

    for i, entry in enumerate(rest):
        cur_first = entry[0]
        cur_second = entry[1]
        cur_month = entry[3]
        cur_year = entry[4]

        if cur_first != first or cur_second != second:
            # finalize and append old period
            end_month, end_year = previous_month(cur_month, cur_year)
            months = num_months(start_month, start_year, end_month, end_year)
            period = [
                first,
                second,
                months,
                start_month,
                start_year,
                end_month,
                end_year,
            ]
            periods.append(period)

            # initialize new period
            first = cur_first
            second = cur_second
            start_month = cur_month
            start_year = cur_year

        if i == len(rest) - 1:
            months = num_months(start_month, start_year, cur_month, cur_year)
            period = [
                first,
                second,
                months,
                start_month,
                start_year,
                cur_month,
                cur_year,
            ]
            periods.append(period)

    header = ['First', 'Second', 'Months', 'SM', 'SY', 'EM', 'EY']
    print(tabulate(periods, headers=header, tablefmt='plain'))


def list_top_players(args):
    rankings = load_rankings()
    n = args.n
    if n < 1 or n > 100:
        raise ValueError('n must be between 1 and 100')
    date = month_year_to_date(args.month, args.year)
    rankings = list(filter(lambda x: x[0] == date, rankings))
    print(tabulate(rankings[:n]))
