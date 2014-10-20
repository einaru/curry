"""
    Curry - Command-line interface
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Copyright: (c) 2014 Einar Uvsløkk
"""
import os
import sys
import logging
import argparse

from curry import __version__

log = logging.getLogger(__name__)


def parse_command_line(argv):
    """Parses the command line arguments, and setup logging level."""

    parser = argparse.ArgumentParser(prog='curry',
        description='Command-line currency converter.')

    parser.add_argument('from', help='currency to convert from')
    parser.add_argument('to', help='currency to convert to')
    parser.add_argument('amount', nargs='?', type=float, default=1,
                        help='the amount to convert, defaults to 1')

    parser.add_argument('--version', action='version',
                        version='%(prog)s v{}'.format(__version__),
                        help='show the application version and exit')
    parser.add_argument('-v', '--verbose', dest='verbose_count',
                        action='count', default=0,
                        help='increase log verbosity')

    args = parser.parse_args(argv[1:])

    # Set the log level to WARN going more verbose for each -v
    log.setLevel(max(3 - args.verbose_count, 0) * 10)

    return args


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.WARN,
                        format='%(name)s (%(levelname)s): %(message)s')
    try:
        args = parse_command_line(sys.argv)
        log.debug(args)
    finally:
        logging.shutdown()
