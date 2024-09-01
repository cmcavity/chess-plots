import argparse

from analyze import largest_gaps, second_place_players, list_top_players
from plot import plot_players
from scrape import scrape_rating_data


def main(args):
    args.func(args)


def parse_args():
    parser = argparse.ArgumentParser(usage='%(prog)s [options]')
    subparsers = parser.add_subparsers(required=True)

    scrape_parser = subparsers.add_parser('scrape')
    scrape_parser.set_defaults(func=scrape_rating_data)

    plot_parser = subparsers.add_parser('plot')
    plot_parser.add_argument(
        '--rank', action='store_true', help='plot ranks instead of ratings'
    )
    plot_parser.add_argument(
        '--hide-legend', action='store_true', help='don\'t display legend'
    )
    plot_parser.add_argument(
        '--start', '-s', dest='start', type=int, help='specify start year'
    )
    plot_parser.add_argument(
        '--end', '-e', dest='end', type=int, help='specify end year'
    )
    plot_parser.add_argument(
        '--file', '-f', dest='file', help='provide text file with list of names'
    )
    plot_parser.set_defaults(func=plot_players)

    gap_parser = subparsers.add_parser('gap')
    gap_parser.add_argument('--number', '-n', type=int, default=20)
    gap_parser.add_argument('--player', '-p')
    gap_parser.set_defaults(func=largest_gaps)

    second_place_parser = subparsers.add_parser('second-place')
    second_place_parser.set_defaults(func=second_place_players)

    list_top_parser = subparsers.add_parser('list-top')
    list_top_parser.add_argument('month', type=str)
    list_top_parser.add_argument('year', type=int)
    list_top_parser.add_argument(
        '-n', type=int, default=10, help='number of players to display (1-100)'
    )
    list_top_parser.set_defaults(func=list_top_players)

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    main(args)
