"""
    Curry - Command-line interface
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Copyright: (c) 2014 Einar Uvsløkk
"""
import sys
import logging
import argparse

from curry import prog_name, version, description
from curry.config import Config
from curry.provider import Provider, APIError, list_api_providers

log = logging.getLogger(__name__)


class ListAPIProviders(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        list_api_providers()
        sys.exit(0)


def parse_command_line(argv, **defaults):
    """Parses the command line arguments, and setup logging level."""

    parser = argparse.ArgumentParser(prog=prog_name,
                                     description=description)

    parser.add_argument('_from', metavar='from',
                        help='currency to convert from')
    parser.add_argument('to', help='currency to convert to')
    parser.add_argument('amount', nargs='?', type=float, default=1,
                        help='the amount to convert (default: 1)')

    default_api = defaults.get('api')
    parser.add_argument('-a', '--api', default=default_api,
                        help='get exchange rates from a given API provider')
    parser.add_argument('-k', '--api-key', metavar='KEY',
                        help='use an API-key (required by some API '
                        'providers!)')
    parser.add_argument('-l', '--list', action=ListAPIProviders, nargs=0,
                        help='show a list of available provider API\'s')

    # TODO:2014-10-21:einar: maybe save on default and provide --no-save flag?
    parser.add_argument('-s', '--save', action='store_true',
                        help='save config settings on exit')
    parser.add_argument('--version', action='version',
                        version='%(prog)s v{}'.format(version),
                        help='show the application version and exit')
    parser.add_argument('-v', '--verbose', dest='verbose_count',
                        action='count', default=0,
                        help='increase log verbosity')

    args = parser.parse_args(argv[1:])

    # Set the log level to WARN going more verbose for each -v
    level = max(3 - args.verbose_count, 0) * 10
    logging.basicConfig(stream=sys.stderr, level=level,
                        format='%(name)s (%(levelname)s): %(message)s')

    return args


def main():
    config = Config()
    try:
        # Load config defaults needed for the command-line
        defaults = {
            'api': config.get('api', 'finance.yahoo.com')
        }

        args = parse_command_line(sys.argv, **defaults)

        api, api_key = args.api, args.api_key

        # If no api_key is provided for the given api provider,
        # try to look it up in the config file.
        if api_key is None:
            api_key = config.get('api_key', section=args.api)

        kwargs = {
            'api': api,
            'api_key': api_key
        }

        provider = Provider(**kwargs)
        rate = provider.get_exchange_rate(args._from, args.to)

        # TODO:2014-10-21:einar: better feedback on error?
        if rate <= 0:
            log.info('Got negative exchange rate: {}'.format(rate))
            return 1

        print('{:.2f}'.format(rate * args.amount))

        if args.save:
            config.set('api', api)
            config.set('api_key', api_key, section=api)
            config.save()

    except APIError as ae:
        log.error(ae)
    finally:
        logging.shutdown()
